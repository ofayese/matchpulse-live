from __future__ import annotations

import abc
import asyncio
import contextvars
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Any

import httpx

from .models import PersonalizedInsight

log = logging.getLogger(__name__)

DEFAULT_API_VERSION = "2024-10-21"
DEFAULT_TIMEOUT_SECONDS = 1.4
DEFAULT_SCOPE = "https://cognitiveservices.azure.com/.default"
DEFAULT_MAX_CONCURRENCY = 1
DEFAULT_CALL_BUDGET = 20
MAX_PROMPT_PAYLOAD_BYTES = 4096
MAX_OUTPUT_TOKENS = 128
RETRY_COUNT = 0

_IN_REWRITE: contextvars.ContextVar[bool] = contextvars.ContextVar("_IN_REWRITE", default=False)

AUTH_API_KEY = "api_key"
AUTH_MANAGED_IDENTITY = "managed_identity"
SUPPORTED_AUTH_MODES = (AUTH_API_KEY, AUTH_MANAGED_IDENTITY)

STATE_DISABLED = "disabled"
STATE_CONFIGURED_UNVERIFIED = "configured-unverified"
STATE_VERIFIED = "verified"
STATE_DEGRADED_FALLBACK = "degraded-fallback"

MAX_TITLE_LENGTH = 140
MAX_BODY_LENGTH = 800
MAX_OVERLAY_LENGTH = 90

# Team identifiers look like "Northbridge-FC"; player identifiers look like "NB-9".
_TEAM_LIKE_RE = re.compile(r"\b[A-Z][A-Za-z]+-[A-Z][A-Za-z]+\b")
_PLAYER_LIKE_RE = re.compile(r"\b[A-Z]{2}-\d+\b")
_UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
# Two consecutive capitalised words are treated as a proper name unless both
# words already appear in the deterministic source text.
_PROPER_NAME_RE = re.compile(r"\b([A-Z][A-Za-z'’-]{2,})\s+([A-Z][A-Za-z'’-]{2,})\b")
_MARKUP_RE = re.compile(r"<\s*/?\s*[a-zA-Z][^>]{0,200}>")
_EVENT_HANDLER_RE = re.compile(r"\bon[a-zA-Z]{3,20}\s*=")
_CAUSAL_PHRASES = (
    "because", "because of", "caused by", "due to", "thanks to", "as a result of",
    "led to", "resulted in", "so that", "owing to", "thanks to the", "means that",
    "por culpa de", "a causa de", "gracias a", "porque", "por lo tanto",
    "à cause de", "grâce à", "parce que", "donc",
)
_NUMBER_RE = re.compile(r"(?<![A-Za-z])\d+(?:\.\d+)?")


class FoundryError(RuntimeError):
    """Base error for the optional Microsoft Foundry enrichment path."""


class FoundryCredentialError(FoundryError):
    """Raised when no usable Foundry credential could be produced."""


class FoundryRewriteRejected(FoundryError):
    """Raised when a model response is not a safe rewrite of the source text."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class FoundrySettings:
    """Non-secret configuration for the optional narrative rewrite.

    Only ``api_key`` can hold a secret, and it is supplied through the runtime
    environment. Every other field is a public identifier.
    """

    endpoint: str
    deployment: str
    api_key: str = ""
    api_version: str = DEFAULT_API_VERSION
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    auth_mode: str = AUTH_API_KEY
    scope: str = DEFAULT_SCOPE
    max_concurrency: int = DEFAULT_MAX_CONCURRENCY
    call_budget: int = DEFAULT_CALL_BUDGET

    @property
    def configured(self) -> bool:
        if self.auth_mode == AUTH_MANAGED_IDENTITY:
            return True
        return bool(self.api_key)

    @classmethod
    def from_env(cls) -> FoundrySettings | None:
        """Build settings from the environment, or ``None`` when not configured.

        The deterministic pipeline is authoritative, so an unconfigured or
        partially configured environment simply disables the optional rewrite.
        """
        endpoint = os.getenv("FOUNDRY_ENDPOINT", "").strip().rstrip("/")
        deployment = os.getenv("FOUNDRY_DEPLOYMENT", "").strip()
        api_key = os.getenv("FOUNDRY_API_KEY", "").strip()
        if not (endpoint and deployment):
            return None

        requested = os.getenv("FOUNDRY_AUTH_MODE", "").strip().lower()
        if requested not in SUPPORTED_AUTH_MODES:
            requested = AUTH_API_KEY if api_key else ""
        if requested == AUTH_API_KEY and not api_key:
            requested = ""

        if not requested:
            return None

        try:
            timeout_seconds = float(os.getenv("FOUNDRY_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS))
        except ValueError:
            timeout_seconds = DEFAULT_TIMEOUT_SECONDS
        if timeout_seconds <= 0:
            timeout_seconds = DEFAULT_TIMEOUT_SECONDS

        return cls(
            endpoint=endpoint,
            deployment=deployment,
            api_key=api_key,
            api_version=os.getenv("FOUNDRY_API_VERSION", DEFAULT_API_VERSION).strip() or DEFAULT_API_VERSION,
            timeout_seconds=timeout_seconds,
            auth_mode=requested,
            scope=os.getenv("FOUNDRY_AZURE_SCOPE", DEFAULT_SCOPE).strip() or DEFAULT_SCOPE,
            max_concurrency=_positive_int("FOUNDRY_MAX_CONCURRENCY", DEFAULT_MAX_CONCURRENCY),
            call_budget=_positive_int("FOUNDRY_CALL_BUDGET", DEFAULT_CALL_BUDGET),
        )


def _positive_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


class FoundryCredentialProvider(abc.ABC):
    """Strategy that turns configuration into outbound authentication headers."""

    name = "provider"

    @abc.abstractmethod
    def headers(self) -> dict[str, str]:
        """Return authentication headers for a single Foundry request."""


class ApiKeyCredentialProvider(FoundryCredentialProvider):
    """Runtime-supplied API key. The value is never logged or persisted."""

    name = AUTH_API_KEY

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def headers(self) -> dict[str, str]:
        if not self._api_key:
            raise FoundryCredentialError("Foundry API key is not set")
        return {"api-key": self._api_key}


class ManagedIdentityCredentialProvider(FoundryCredentialProvider):
    """Azure managed identity via ``DefaultAzureCredential``.

    This is the preferred production path: it needs no stored secret and no
    committed key. ``azure-identity`` is an optional dependency, so a machine
    without it degrades to the deterministic fallback instead of failing.
    """

    name = AUTH_MANAGED_IDENTITY

    def __init__(self, scope: str = DEFAULT_SCOPE, credential: Any | None = None, refresh_margin_seconds: float = 120.0) -> None:
        self._scope = scope
        self._credential = credential
        self._refresh_margin_seconds = refresh_margin_seconds
        self._token = ""
        self._expires_at = 0.0

    def _ensure_credential(self) -> Any:
        if self._credential is None:
            try:
                from azure.identity import DefaultAzureCredential
            except ImportError as exc:
                raise FoundryCredentialError("azure-identity is not installed") from exc
            self._credential = DefaultAzureCredential()
        return self._credential

    def headers(self) -> dict[str, str]:
        now = time.time()
        if not self._token or now >= (self._expires_at - self._refresh_margin_seconds):
            credential = self._ensure_credential()
            try:
                token = credential.get_token(self._scope)
            except Exception as exc:
                raise FoundryCredentialError(f"managed identity token request failed: {type(exc).__name__}") from exc
            self._token = token.token
            self._expires_at = float(getattr(token, "expires_on", now + 300))
        return {"Authorization": f"Bearer {self._token}"}


class FoundryNarrativeClient:
    """Optional Microsoft Foundry rewrite with deterministic, grounded fallback.

    The core pipeline never depends on model output. Any timeout, invalid JSON,
    new numeric claim, or schema violation returns the original evidence-backed
    text. The client is asynchronous so it never blocks an event-loop request
    path, it bounds its own concurrency and its total number of outbound calls,
    and it reports a truthful state that distinguishes "configured" from
    "actually verified".
    """

    def __init__(
        self,
        settings: FoundrySettings,
        provider: FoundryCredentialProvider | None = None,
        *,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings
        self._provider = provider if provider is not None else self._default_provider(settings)
        self._http_client = http_client
        self._state = STATE_CONFIGURED_UNVERIFIED
        self._remaining_calls = max(0, int(settings.call_budget))
        self._active_requests = 0
        self._attempted = 0
        self._succeeded = 0
        self._fallbacks = 0
        self._rejections = 0

    @staticmethod
    def _default_provider(settings: FoundrySettings) -> FoundryCredentialProvider:
        if settings.auth_mode == AUTH_MANAGED_IDENTITY:
            return ManagedIdentityCredentialProvider(scope=settings.scope)
        return ApiKeyCredentialProvider(settings.api_key)

    @property
    def provider_name(self) -> str:
        return self._provider.name

    @property
    def state(self) -> str:
        """Truthful state: configured alone never implies a verified call."""
        return self._state

    @property
    def remaining_calls(self) -> int:
        return self._remaining_calls

    @property
    def counters(self) -> dict[str, int]:
        return {"attempted": self._attempted, "succeeded": self._succeeded,
                "fallbacks": self._fallbacks, "rejections": self._rejections}

    # ------------------------------------------------------------ public API

    async def rewrite(self, item: PersonalizedInsight) -> tuple[PersonalizedInsight, str | None]:
        if _IN_REWRITE.get():
            self._fallbacks += 1
            self._state = STATE_DEGRADED_FALLBACK
            return item, "Foundry fallback: recursive-call-blocked"
        if self._active_requests >= max(1, self.settings.max_concurrency):
            self._fallbacks += 1
            self._state = STATE_DEGRADED_FALLBACK
            return item, "Foundry fallback: concurrency-limit-exceeded"
        self._active_requests += 1
        token = _IN_REWRITE.set(True)
        try:
            return await self._rewrite_one(item)
        finally:
            _IN_REWRITE.reset(token)
            self._active_requests -= 1

    async def rewrite_many(self, items: list[PersonalizedInsight]) -> tuple[list[PersonalizedInsight], list[str]]:
        """Rewrite several insights with bounded concurrency.

        Every failure degrades to the original deterministic output; the order
        of the returned list always matches the order of the input.
        """
        if not items:
            return [], []
        if _IN_REWRITE.get():
            self._fallbacks += len(items)
            self._state = STATE_DEGRADED_FALLBACK
            return list(items), ["Foundry fallback: recursive-call-blocked"] * len(items)
        semaphore = asyncio.Semaphore(max(1, self.settings.max_concurrency))

        async def guarded(item: PersonalizedInsight) -> tuple[PersonalizedInsight, str | None]:
            async with semaphore:
                return await self.rewrite(item)

        results = await asyncio.gather(*(guarded(item) for item in items), return_exceptions=True)
        outputs: list[PersonalizedInsight] = []
        warnings: list[str] = []
        for item, result in zip(items, results, strict=True):
            if isinstance(result, BaseException):
                self._fallbacks += 1
                self._state = STATE_DEGRADED_FALLBACK
                outputs.append(item)
                warnings.append(f"Foundry fallback: {type(result).__name__}")
            else:
                output, warning = result
                outputs.append(output)
                if warning:
                    warnings.append(warning)
        return outputs, warnings

    # -------------------------------------------------------------- internals

    async def _rewrite_one(self, item: PersonalizedInsight) -> tuple[PersonalizedInsight, str | None]:
        if self._remaining_calls <= 0:
            self._fallbacks += 1
            self._state = STATE_DEGRADED_FALLBACK
            return item, "Foundry fallback: call-budget-exhausted"

        url = (f"{self.settings.endpoint}/openai/deployments/{self.settings.deployment}"
               f"/chat/completions?api-version={self.settings.api_version}")
        payload = {
            "messages": [
                {"role": "system", "content": "You are a grounded football broadcast copy editor."},
                {"role": "user", "content": self._prompt(item)},
            ],
            "temperature": 0.1,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "response_format": {"type": "json_object"},
        }
        payload_bytes = len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        if payload_bytes > MAX_PROMPT_PAYLOAD_BYTES:
            self._fallbacks += 1
            self._state = STATE_DEGRADED_FALLBACK
            return item, "Foundry fallback: prompt-budget-exceeded"

        self._remaining_calls -= 1
        self._attempted += 1
        try:
            headers = {"Content-Type": "application/json"}
            headers.update(self._provider.headers())
            content = await self._post(url, headers, payload)
            rewrite = self._parse(content)
            self._validate(item, rewrite)
        except FoundryRewriteRejected as exc:
            self._rejections += 1
            self._fallbacks += 1
            self._state = STATE_DEGRADED_FALLBACK
            log.warning("Foundry rewrite rejected: %s", exc.reason)
            return item, f"Foundry fallback: {exc.reason}"
        except Exception as exc:
            self._fallbacks += 1
            self._state = STATE_DEGRADED_FALLBACK
            reason = type(exc).__name__
            log.warning("Foundry rewrite fallback: %s", reason)
            return item, f"Foundry fallback: {reason}"

        self._succeeded += 1
        self._state = STATE_VERIFIED
        return self._apply(item, rewrite), None

    async def _post(self, url: str, headers: dict[str, str], payload: dict[str, Any]) -> str:
        if self._http_client is not None:
            response = await self._http_client.post(url, headers=headers, json=payload,
                                                   timeout=self.settings.timeout_seconds)
        else:
            async with httpx.AsyncClient(timeout=self.settings.timeout_seconds) as owned:
                response = await owned.post(url, headers=headers, json=payload,
                                           timeout=self.settings.timeout_seconds)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    @staticmethod
    def _prompt(item: PersonalizedInsight) -> str:
        source = item.model_dump(mode="json")
        return (
            "Rewrite only the title, body, and overlay_text for clarity and the stated audience. "
            "Return strict JSON with exactly those three keys. Do not add facts, numbers, names, "
            "predictions, or causal claims. Keep overlay_text under 90 characters. Input: "
            + json.dumps(source, ensure_ascii=False)
        )

    @staticmethod
    def _parse(content: Any) -> dict[str, Any]:
        if not isinstance(content, str):
            raise FoundryRewriteRejected("non-string-response")
        try:
            rewrite = json.loads(content)
        except json.JSONDecodeError as exc:
            raise FoundryRewriteRejected("malformed-json") from exc
        if not isinstance(rewrite, dict):
            raise FoundryRewriteRejected("malformed-json")
        return rewrite

    # ----------------------------------------------------------- guard rails

    @staticmethod
    def _numbers(text: str) -> list[str]:
        return _NUMBER_RE.findall(text)

    @classmethod
    def _validate(cls, item: PersonalizedInsight, rewrite: dict[str, Any]) -> None:
        """Reject any response that is not a safe rewrite of the source text."""
        if set(rewrite) != {"title", "body", "overlay_text"}:
            raise FoundryRewriteRejected("unexpected-keys")
        for key in ("title", "body", "overlay_text"):
            value = rewrite[key]
            if not isinstance(value, str) or not value.strip():
                raise FoundryRewriteRejected("empty-output")
        if len(rewrite["title"]) > MAX_TITLE_LENGTH:
            raise FoundryRewriteRejected("oversized-output")
        if len(rewrite["body"]) > MAX_BODY_LENGTH:
            raise FoundryRewriteRejected("oversized-output")
        if len(rewrite["overlay_text"]) > MAX_OVERLAY_LENGTH:
            raise FoundryRewriteRejected("oversized-output")

        source_text = f"{item.title}\n{item.body}\n{item.overlay_text}"
        candidate_text = f"{rewrite['title']}\n{rewrite['body']}\n{rewrite['overlay_text']}"

        cls._reject_markup(candidate_text)
        cls._reject_unsupported_identifiers(source_text, candidate_text)
        cls._reject_unsupported_names(source_text, candidate_text)
        cls._reject_unsupported_causality(source_text, candidate_text)
        cls._reject_new_numbers(source_text, candidate_text)

    @staticmethod
    def _reject_markup(text: str) -> None:
        if _MARKUP_RE.search(text) or _EVENT_HANDLER_RE.search(text):
            raise FoundryRewriteRejected("markup-output")
        lowered = text.lower()
        if "javascript:" in lowered or "</script" in lowered or "<script" in lowered:
            raise FoundryRewriteRejected("markup-output")

    @staticmethod
    def _reject_new_numbers(source_text: str, candidate_text: str) -> None:
        """The rewrite may omit numbers but never add, change or reorder them."""
        source_numbers = FoundryNarrativeClient._numbers(source_text)
        candidate_numbers = FoundryNarrativeClient._numbers(candidate_text)
        position = 0
        for number in candidate_numbers:
            while position < len(source_numbers) and source_numbers[position] != number:
                position += 1
            if position >= len(source_numbers):
                raise FoundryRewriteRejected("unsupported-number")
            position += 1

    @staticmethod
    def _reject_unsupported_identifiers(source_text: str, candidate_text: str) -> None:
        if _UUID_RE.search(candidate_text):
            raise FoundryRewriteRejected("unsupported-identifier")
        for pattern in (_TEAM_LIKE_RE, _PLAYER_LIKE_RE):
            for token in pattern.findall(candidate_text):
                if token not in source_text:
                    raise FoundryRewriteRejected("unsupported-identifier")

    @staticmethod
    def _reject_unsupported_names(source_text: str, candidate_text: str) -> None:
        lowered_source = source_text.lower()
        for first, second in _PROPER_NAME_RE.findall(candidate_text):
            if first.lower() not in lowered_source and second.lower() not in lowered_source:
                raise FoundryRewriteRejected("unsupported-name")

    @staticmethod
    def _reject_unsupported_causality(source_text: str, candidate_text: str) -> None:
        lowered_source = source_text.lower()
        lowered_candidate = candidate_text.lower()
        for phrase in _CAUSAL_PHRASES:
            if phrase in lowered_candidate and phrase not in lowered_source:
                raise FoundryRewriteRejected("unsupported-causal-claim")

    @staticmethod
    def _apply(item: PersonalizedInsight, rewrite: dict[str, Any]) -> PersonalizedInsight:
        """Rebuild the insight so pydantic revalidates the rewritten fields."""
        data = item.model_dump(mode="json")
        data.update(rewrite)
        return PersonalizedInsight(**data)
