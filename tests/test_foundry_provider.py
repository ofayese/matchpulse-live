# cspell:ignore caplog delenv unconfigured
"""Guarded Foundry provider tests.

These cover the optional enrichment path only. The deterministic pipeline stays
authoritative and is never allowed to depend on a model response.
"""

from __future__ import annotations

import asyncio
import json
import logging

import httpx
import pytest

from matchpulse.foundry import (
    AUTH_MANAGED_IDENTITY,
    DEFAULT_CALL_BUDGET,
    DEFAULT_MAX_CONCURRENCY,
    DEFAULT_TIMEOUT_SECONDS,
    MAX_OUTPUT_TOKENS,
    MAX_PROMPT_PAYLOAD_BYTES,
    RETRY_COUNT,
    STATE_CONFIGURED_UNVERIFIED,
    STATE_DEGRADED_FALLBACK,
    STATE_DISABLED,
    STATE_VERIFIED,
    ApiKeyCredentialProvider,
    FoundryCredentialError,
    FoundryNarrativeClient,
    FoundrySettings,
    ManagedIdentityCredentialProvider,
)
from matchpulse.models import Evidence, Persona, PersonalizedInsight

SECRET = "super-secret-foundry-key"


def item() -> PersonalizedInsight:
    return PersonalizedInsight(
        insight_id="i",
        match_id="m",
        profile_id="fan",
        locale="en",
        persona=Persona.FAN,
        priority=0.8,
        title="Shot",
        body="A shot reached 101 km/h.",
        overlay_text="101 km/h shot",
        clock_ms=1,
        sequence=1,
        severity="notable",
        evidence=Evidence(
            event_ids=["e1"],
            inputs={"speed": 101},
            formula="measured speed",
            confidence=0.9,
        ),
        stats={"speed_kmh": 101},
        expires_in_ms=12000,
    )


def _completion(content: str) -> httpx.Response:
    return httpx.Response(
        200, json={"choices": [{"message": {"content": content}}]}
    )


def _client(handler) -> tuple[FoundryNarrativeClient, httpx.AsyncClient]:
    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport)
    settings = FoundrySettings("https://example.test", "model", SECRET)
    return FoundryNarrativeClient(settings, http_client=http), http


def _run(
    client: FoundryNarrativeClient, source: PersonalizedInsight | None = None
):
    return asyncio.run(client.rewrite(source or item()))


def test_valid_guarded_foundry_response_is_applied():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["headers"] = dict(request.headers)
        return _completion(
            json.dumps(
                {
                    "title": "Faster shot",
                    "body": "A shot reached 101 km/h.",
                    "overlay_text": "101 km/h",
                }
            )
        )

    client, http = _client(handler)
    try:
        output, warning = _run(client)
    finally:
        asyncio.run(http.aclose())
    assert warning is None
    assert output.title == "Faster shot"
    assert output.body == "A shot reached 101 km/h."
    assert output.overlay_text == "101 km/h"
    assert seen["headers"]["api-key"] == SECRET
    assert client.state == STATE_VERIFIED


def test_model_request_has_bounded_completion_tokens():
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(json.loads(request.content))
        return _completion(
            json.dumps(
                {
                    "title": "Faster shot",
                    "body": "A shot reached 101 km/h.",
                    "overlay_text": "101 km/h",
                }
            )
        )

    client, http = _client(handler)
    try:
        _run(client)
    finally:
        asyncio.run(http.aclose())
    assert seen["max_tokens"] == 128


def test_oversized_prompt_falls_back_without_sending_or_spending_call_budget():
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return _completion(
            json.dumps(
                {
                    "title": "Faster shot",
                    "body": "A shot reached 101 km/h.",
                    "overlay_text": "101 km/h",
                }
            )
        )

    source = item().model_copy(
        update={
            "evidence": Evidence(
                event_ids=["e1"],
                inputs={"speed": 101},
                formula="x" * 5000,
                confidence=0.9,
            ),
        }
    )
    settings = FoundrySettings(
        "https://example.test", "model", SECRET, call_budget=1
    )
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = FoundryNarrativeClient(settings, http_client=http)
    try:
        output, warning = _run(client, source)
        remaining = client.remaining_calls
    finally:
        asyncio.run(http.aclose())
    assert output == source
    assert warning is not None
    assert "prompt-budget-exceeded" in warning
    assert calls == 0
    assert remaining == 1


def test_timeout_falls_back_to_deterministic_text():
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out")

    client, http = _client(handler)
    try:
        source = item()
        output, warning = _run(client, source)
    finally:
        asyncio.run(http.aclose())
    assert output == source
    assert warning is not None
    assert "TimeoutException" in warning
    assert client.state == STATE_DEGRADED_FALLBACK


def test_connection_failure_falls_back_to_deterministic_text():
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    client, http = _client(handler)
    try:
        source = item()
        output, warning = _run(client, source)
    finally:
        asyncio.run(http.aclose())
    assert output == source
    assert warning is not None
    assert "ConnectError" in warning


@pytest.mark.parametrize("status", [401, 403, 429, 500, 503])
def test_http_error_statuses_fall_back_to_deterministic_text(status):
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"error": "nope"})

    client, http = _client(handler)
    try:
        source = item()
        output, warning = _run(client, source)
    finally:
        asyncio.run(http.aclose())
    assert output == source
    assert warning is not None
    assert "HTTPStatusError" in warning


def test_invalid_json_falls_back_to_deterministic_text():
    client, http = _client(lambda _request: _completion("this is not json"))
    try:
        source = item()
        output, warning = _run(client, source)
    finally:
        asyncio.run(http.aclose())
    assert output == source
    assert warning is not None
    assert "malformed-json" in warning


def test_missing_key_falls_back_to_deterministic_text():
    client, http = _client(
        lambda _request: _completion(json.dumps({"title": "Only a title"}))
    )
    try:
        source = item()
        output, warning = _run(client, source)
    finally:
        asyncio.run(http.aclose())
    assert output == source
    assert warning is not None
    assert "unexpected-keys" in warning


def test_unexpected_key_falls_back_to_deterministic_text():
    payload = {
        "title": "T",
        "body": "A shot reached 101 km/h.",
        "overlay_text": "101 km/h",
        "extra": 1,
    }
    client, http = _client(lambda _request: _completion(json.dumps(payload)))
    try:
        source = item()
        output, warning = _run(client, source)
    finally:
        asyncio.run(http.aclose())
    assert output == source
    assert warning is not None
    assert "unexpected-keys" in warning


def test_empty_output_falls_back_to_deterministic_text():
    payload = {
        "title": "  ",
        "body": "A shot reached 101 km/h.",
        "overlay_text": "101 km/h",
    }
    client, http = _client(lambda _request: _completion(json.dumps(payload)))
    try:
        source = item()
        output, warning = _run(client, source)
    finally:
        asyncio.run(http.aclose())
    assert output == source
    assert warning is not None
    assert "empty-output" in warning


def test_oversized_output_falls_back_to_deterministic_text():
    payload = {
        "title": "T",
        "body": "A shot reached 101 km/h. " + "x" * 900,
        "overlay_text": "101 km/h",
    }
    client, http = _client(lambda _request: _completion(json.dumps(payload)))
    try:
        source = item()
        output, warning = _run(client, source)
    finally:
        asyncio.run(http.aclose())
    assert output == source
    assert warning is not None
    assert "oversized-output" in warning


def test_new_number_falls_back_to_deterministic_text():
    payload = {
        "title": "T",
        "body": "A shot reached 102 km/h.",
        "overlay_text": "102 km/h",
    }
    client, http = _client(lambda _request: _completion(json.dumps(payload)))
    try:
        source = item()
        output, warning = _run(client, source)
    finally:
        asyncio.run(http.aclose())
    assert output == source
    assert warning is not None
    assert "unsupported-number" in warning


def test_changed_number_falls_back_to_deterministic_text():
    payload = {
        "title": "T",
        "body": "A shot reached 99 km/h.",
        "overlay_text": "99 km/h",
    }
    client, http = _client(lambda _request: _completion(json.dumps(payload)))
    try:
        source = item()
        output, warning = _run(client, source)
    finally:
        asyncio.run(http.aclose())
    assert output == source
    assert warning is not None
    assert "unsupported-number" in warning


def test_reordered_numbers_fall_back_to_deterministic_text():
    source = PersonalizedInsight(
        insight_id="i",
        match_id="m",
        profile_id="fan",
        locale="en",
        persona=Persona.FAN,
        priority=0.8,
        title="Score",
        body="The score is now 2-1.",
        overlay_text="2-1",
        clock_ms=1,
        sequence=1,
        severity="notable",
        evidence=Evidence(
            event_ids=["e1"],
            inputs={"score": "2-1"},
            formula="aggregate",
            confidence=0.9,
        ),
        stats={"score": "2-1"},
        expires_in_ms=12000,
    )
    payload = {
        "title": "Score",
        "body": "The score is now 1-2.",
        "overlay_text": "1-2",
    }
    client, http = _client(lambda _request: _completion(json.dumps(payload)))
    try:
        output, warning = _run(client, source)
    finally:
        asyncio.run(http.aclose())
    assert output == source
    assert warning is not None
    assert "unsupported-number" in warning


def test_unsupported_identifier_falls_back_to_deterministic_text():
    payload = {
        "title": "T",
        "body": "A shot reached 101 km/h by NB-42.",
        "overlay_text": "101 km/h",
    }
    client, http = _client(lambda _request: _completion(json.dumps(payload)))
    try:
        source = item()
        output, warning = _run(client, source)
    finally:
        asyncio.run(http.aclose())
    assert output == source
    assert warning is not None
    assert "unsupported-identifier" in warning


def test_unsupported_team_identifier_falls_back_to_deterministic_text():
    payload = {
        "title": "T",
        "body": "A shot reached 101 km/h for Arsenal-FC.",
        "overlay_text": "101 km/h",
    }
    client, http = _client(lambda _request: _completion(json.dumps(payload)))
    try:
        source = item()
        output, warning = _run(client, source)
    finally:
        asyncio.run(http.aclose())
    assert output == source
    assert warning is not None
    assert "unsupported-identifier" in warning


def test_unsupported_name_falls_back_to_deterministic_text():
    payload = {
        "title": "T",
        "body": "A shot reached 101 km/h at Wembley Stadium.",
        "overlay_text": "101 km/h",
    }
    client, http = _client(lambda _request: _completion(json.dumps(payload)))
    try:
        source = item()
        output, warning = _run(client, source)
    finally:
        asyncio.run(http.aclose())
    assert output == source
    assert warning is not None
    assert "unsupported-name" in warning


def test_unsupported_causal_claim_falls_back_to_deterministic_text():
    payload = {
        "title": "T",
        "body": "A shot reached 101 km/h because of the wind.",
        "overlay_text": "101 km/h",
    }
    client, http = _client(lambda _request: _completion(json.dumps(payload)))
    try:
        source = item()
        output, warning = _run(client, source)
    finally:
        asyncio.run(http.aclose())
    assert output == source
    assert warning is not None
    assert "unsupported-causal-claim" in warning


def test_html_output_falls_back_to_deterministic_text():
    payload = {
        "title": "<script>alert(1)</script>",
        "body": "A shot reached 101 km/h.",
        "overlay_text": "101 km/h",
    }
    client, http = _client(lambda _request: _completion(json.dumps(payload)))
    try:
        source = item()
        output, warning = _run(client, source)
    finally:
        asyncio.run(http.aclose())
    assert output == source
    assert warning is not None
    assert "markup-output" in warning


def test_secret_never_appears_in_warning_or_logs(caplog):
    def handler(_request: httpx.Request) -> httpx.Response:
        raise RuntimeError(f"transport rejected credential {SECRET}")

    client, http = _client(handler)
    try:
        source = item()
        with caplog.at_level(logging.DEBUG):
            output, warning = _run(client, source)
    finally:
        asyncio.run(http.aclose())
    assert output == source
    assert warning is not None
    assert SECRET not in warning
    assert SECRET not in json.dumps(output.model_dump(mode="json"))
    for record in caplog.records:
        assert SECRET not in record.getMessage()


def test_managed_identity_configuration_needs_no_api_key(monkeypatch):
    monkeypatch.delenv("FOUNDRY_API_KEY", raising=False)
    monkeypatch.setenv("FOUNDRY_ENDPOINT", "https://example.test")
    monkeypatch.setenv("FOUNDRY_DEPLOYMENT", "model")
    monkeypatch.setenv("FOUNDRY_AUTH_MODE", AUTH_MANAGED_IDENTITY)
    settings = FoundrySettings.from_env()
    assert settings is not None
    assert settings.auth_mode == AUTH_MANAGED_IDENTITY
    assert settings.api_key == ""
    assert settings.configured is True
    client = FoundryNarrativeClient(settings)
    assert client.provider_name == AUTH_MANAGED_IDENTITY


def test_unconfigured_environment_disables_the_optional_rewrite(monkeypatch):
    for name in (
        "FOUNDRY_ENDPOINT",
        "FOUNDRY_DEPLOYMENT",
        "FOUNDRY_API_KEY",
        "FOUNDRY_AUTH_MODE",
    ):
        monkeypatch.delenv(name, raising=False)
    assert FoundrySettings.from_env() is None


def test_api_key_mode_without_a_key_stays_unconfigured(monkeypatch):
    monkeypatch.delenv("FOUNDRY_API_KEY", raising=False)
    monkeypatch.setenv("FOUNDRY_ENDPOINT", "https://example.test")
    monkeypatch.setenv("FOUNDRY_DEPLOYMENT", "model")
    monkeypatch.setenv("FOUNDRY_AUTH_MODE", "api_key")
    assert FoundrySettings.from_env() is None


def test_api_key_provider_requires_a_non_empty_value():
    provider = ApiKeyCredentialProvider("")
    with pytest.raises(FoundryCredentialError):
        provider.headers()


def test_managed_identity_provider_uses_a_bearer_token():
    class Token:
        token = "signed-token"
        expires_on = 4_102_444_800.0

    class Credential:
        def __init__(self) -> None:
            self.calls = 0

        def get_token(self, scope, *_args, **_kwargs):
            self.calls += 1
            assert scope == "https://cognitiveservices.azure.com/.default"
            return Token()

    credential = Credential()
    provider = ManagedIdentityCredentialProvider(credential=credential)
    headers = provider.headers()
    assert headers == {"Authorization": "Bearer signed-token"}
    provider.headers()
    assert credential.calls == 1


def test_managed_identity_provider_falls_back_when_identity_is_unavailable():
    class Broken:
        def get_token(self, scope, *_args, **_kwargs):
            raise RuntimeError("no identity")

    provider = ManagedIdentityCredentialProvider(credential=Broken())
    with pytest.raises(FoundryCredentialError):
        provider.headers()


def test_configured_client_reports_unverified_before_any_call():
    client = FoundryNarrativeClient(
        FoundrySettings("https://example.test", "model", SECRET)
    )
    assert client.state == STATE_CONFIGURED_UNVERIFIED
    assert client.state != STATE_VERIFIED
    assert client.state != STATE_DISABLED


def test_call_budget_is_enforced():
    def handler(_request: httpx.Request) -> httpx.Response:
        return _completion(
            json.dumps(
                {
                    "title": "Faster shot",
                    "body": "A shot reached 101 km/h.",
                    "overlay_text": "101 km/h",
                }
            )
        )

    settings = FoundrySettings(
        "https://example.test", "model", SECRET, call_budget=1
    )
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = FoundryNarrativeClient(settings, http_client=http)

    async def scenario():
        first, _ = await client.rewrite(item())
        second, warning = await client.rewrite(item())
        return first, second, warning

    try:
        first, second, warning = asyncio.run(scenario())
    finally:
        asyncio.run(http.aclose())
    assert first.title == "Faster shot"
    assert second.title == "Shot"
    assert warning is not None
    assert "call-budget-exhausted" in warning


def test_rewrite_many_preserves_order_and_falls_back_per_item():
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        text = body["messages"][1]["content"]
        if "Shot" in text and "shot reached 101" in text:
            return _completion(
                json.dumps(
                    {
                        "title": "Faster shot",
                        "body": "A shot reached 101 km/h.",
                        "overlay_text": "101 km/h",
                    }
                )
            )
        raise httpx.TimeoutException("timed out")

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = FoundryNarrativeClient(
        FoundrySettings("https://example.test", "model", SECRET),
        http_client=http,
    )
    items = [item(), item()]
    try:
        outputs, warnings = asyncio.run(client.rewrite_many(items))
    finally:
        asyncio.run(http.aclose())
    assert len(outputs) == 2
    assert all(output.title == "Faster shot" for output in outputs)
    assert warnings == []


def test_rewrite_many_falls_back_for_every_failed_item():
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out")

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = FoundryNarrativeClient(
        FoundrySettings("https://example.test", "model", SECRET),
        http_client=http,
    )
    items = [item(), item()]
    try:
        outputs, warnings = asyncio.run(client.rewrite_many(items))
    finally:
        asyncio.run(http.aclose())
    assert outputs == items
    assert len(warnings) == 2


def test_rewrite_many_bounds_concurrency():
    import threading

    active = 0
    peak = 0
    lock = threading.Lock()

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        try:
            return _completion(
                json.dumps(
                    {
                        "title": "Faster shot",
                        "body": "A shot reached 101 km/h.",
                        "overlay_text": "101 km/h",
                    }
                )
            )
        finally:
            with lock:
                active -= 1

    settings = FoundrySettings(
        "https://example.test", "model", SECRET, max_concurrency=2
    )
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = FoundryNarrativeClient(settings, http_client=http)
    items = [item() for _ in range(6)]
    try:
        asyncio.run(client.rewrite_many(items))
    finally:
        asyncio.run(http.aclose())
    assert peak <= 2


def test_secure_model_control_constants_and_defaults(monkeypatch):
    assert DEFAULT_CALL_BUDGET == 20
    assert DEFAULT_MAX_CONCURRENCY == 1
    assert MAX_PROMPT_PAYLOAD_BYTES == 4096
    assert MAX_OUTPUT_TOKENS == 128
    assert DEFAULT_TIMEOUT_SECONDS == 1.4
    assert RETRY_COUNT == 0

    monkeypatch.setenv("FOUNDRY_ENDPOINT", "https://example.test")
    monkeypatch.setenv("FOUNDRY_DEPLOYMENT", "model")
    monkeypatch.setenv("FOUNDRY_AUTH_MODE", AUTH_MANAGED_IDENTITY)
    monkeypatch.delenv("FOUNDRY_MAX_CONCURRENCY", raising=False)
    monkeypatch.delenv("FOUNDRY_CALL_BUDGET", raising=False)
    monkeypatch.delenv("FOUNDRY_TIMEOUT_SECONDS", raising=False)
    settings = FoundrySettings.from_env()
    assert settings is not None
    assert settings.call_budget == 20
    assert settings.max_concurrency == 1
    assert settings.timeout_seconds == 1.4


def test_calls_1_to_20_are_allowed_and_call_21_falls_back_by_default():
    calls = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return _completion(
            json.dumps(
                {
                    "title": "Faster shot",
                    "body": "A shot reached 101 km/h.",
                    "overlay_text": "101 km/h",
                }
            )
        )

    settings = FoundrySettings("https://example.test", "model", SECRET)
    assert settings.call_budget == 20
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = FoundryNarrativeClient(settings, http_client=http)

    async def scenario():
        return [await client.rewrite(item()) for _ in range(21)]

    try:
        results = asyncio.run(scenario())
    finally:
        asyncio.run(http.aclose())

    assert calls == 20
    assert client.remaining_calls == 0
    assert all(
        warn is None and out.title == "Faster shot"
        for out, warn in results[:20]
    )
    assert results[20][0] == item()
    assert results[20][1] == "Foundry fallback: call-budget-exhausted"


def test_concurrent_request_two_falls_back_under_default_concurrency_one():
    class BlockingTransport(httpx.AsyncBaseTransport):
        def __init__(self) -> None:
            self.entered = asyncio.Event()
            self.release = asyncio.Event()
            self.calls = 0
            self.active = 0
            self.peak = 0

        async def handle_async_request(
            self, request: httpx.Request
        ) -> httpx.Response:
            self.calls += 1
            self.active += 1
            self.peak = max(self.peak, self.active)
            self.entered.set()
            try:
                await self.release.wait()
                return _completion(
                    json.dumps(
                        {
                            "title": "Faster shot",
                            "body": "A shot reached 101 km/h.",
                            "overlay_text": "101 km/h",
                        }
                    )
                )
            finally:
                self.active -= 1

    async def scenario():
        transport = BlockingTransport()
        http = httpx.AsyncClient(transport=transport)
        client = FoundryNarrativeClient(
            FoundrySettings("https://example.test", "model", SECRET),
            http_client=http,
        )
        assert client.settings.max_concurrency == 1
        first_task = asyncio.create_task(client.rewrite(item()))
        await transport.entered.wait()
        second = await client.rewrite(item())
        transport.release.set()
        first = await first_task
        await http.aclose()
        return first, second, transport

    first, second, transport = asyncio.run(scenario())
    assert first[1] is None
    assert first[0].title == "Faster shot"
    assert second[0] == item()
    assert second[1] == "Foundry fallback: concurrency-limit-exceeded"
    assert transport.calls == 1
    assert transport.peak == 1


def test_timeout_is_1_4_seconds_with_zero_retries():
    calls = 0
    observed_timeouts: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        observed_timeouts.append(request.extensions["timeout"]["read"])
        raise httpx.TimeoutException("request timed out")

    settings = FoundrySettings("https://example.test", "model", SECRET)
    assert settings.timeout_seconds == 1.4
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = FoundryNarrativeClient(settings, http_client=http)
    try:
        output, warning = _run(client)
    finally:
        asyncio.run(http.aclose())
    assert output == item()
    assert warning == "Foundry fallback: TimeoutException"
    assert calls == 1
    assert observed_timeouts == [1.4]


def test_recursive_model_calls_cannot_occur():
    calls = 0
    recursive_result: tuple | None = None
    client_ref: list[FoundryNarrativeClient] = []

    class RecursiveTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(
            self, request: httpx.Request
        ) -> httpx.Response:
            nonlocal calls, recursive_result
            calls += 1
            recursive_result = await client_ref[0].rewrite(item())
            return _completion(
                json.dumps(
                    {
                        "title": "Faster shot",
                        "body": "A shot reached 101 km/h.",
                        "overlay_text": "101 km/h",
                    }
                )
            )

    http = httpx.AsyncClient(transport=RecursiveTransport())
    client = FoundryNarrativeClient(
        FoundrySettings(
            "https://example.test", "model", SECRET, max_concurrency=4
        ),
        http_client=http,
    )
    client_ref.append(client)
    try:
        outer_out, outer_warn = _run(client)
    finally:
        asyncio.run(http.aclose())
    assert calls == 1
    assert outer_warn is None
    assert outer_out.title == "Faster shot"
    assert recursive_result is not None
    assert recursive_result[0] == item()
    assert recursive_result[1] == "Foundry fallback: recursive-call-blocked"


def test_prompt_body_is_never_logged_on_failure_or_rejection(caplog):
    prompt_secret_marker = "CONFIDENTIAL_PROMPT_FORMULA_991122"

    def handler(_request: httpx.Request) -> httpx.Response:
        raise RuntimeError(
            f"transport error with {prompt_secret_marker} and {SECRET}"
        )

    source = item().model_copy(
        update={
            "evidence": Evidence(
                event_ids=["e1"],
                inputs={"speed": 101},
                formula=prompt_secret_marker,
                confidence=0.9,
            ),
        }
    )
    client, http = _client(handler)
    try:
        with caplog.at_level(logging.DEBUG):
            output, warning = _run(client, source)
    finally:
        asyncio.run(http.aclose())
    assert output == source
    assert warning == "Foundry fallback: RuntimeError"
    for record in caplog.records:
        msg = record.getMessage()
        assert prompt_secret_marker not in msg
        assert SECRET not in msg
