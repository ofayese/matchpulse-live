#!/usr/bin/env python3
"""Discover and audition eligible ElevenLabs stock voices without rendering a final video."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = "eleven_multilingual_v2"
STABLE_MODEL_IDS = frozenset({"eleven_multilingual_v2", "eleven_flash_v2_5"})
REQUEST_OPTIONS = {"timeout_in_seconds": 30, "max_retries": 0}
MAX_API_ATTEMPTS = 2
MAX_INITIAL_AUDITIONS = 10
MAX_VOICE_PAGES = 20
TARGET_SAMPLE_RATE = 48_000
TARGET_CHANNELS = 2
TARGET_LOUDNESS_LUFS = -16.0
TARGET_TRUE_PEAK_DBTP = -1.5
AUDITION_TEXT = (
    "Here’s MatchPulse Live. It turns synthetic football events into clear, "
    "evidence-grounded stories for fans, analysts, and broadcasters.\n\n"
    "Northbridge City leads Harbor United by two goals to one.\n\n"
    "If the same event arrives twice, the score stays exactly the same. And if "
    "something arrives out of order, MatchPulse rejects it cleanly, without "
    "changing the match.\n\n"
    "For this deployment, Foundry is switched off, so every result follows the "
    "deterministic fallback path, with zero model calls."
)
PRONUNCIATION_TEXT = (
    "MatchPulse. Azure Container Apps. Northbridge City. Harbor United. "
    "Analyst. Broadcaster. Deterministic fallback. Foundry."
)
TERMS_URLS = (
    "https://elevenlabs.io/pricing",
    "https://elevenlabs.io/terms",
    "https://elevenlabs.io/use-policy",
    "https://elevenlabs.io/service-specific-terms",
    "https://elevenlabs.io/bsa",
    "https://elevenlabs.io/docs/help-center/legal/can-i-publish-the-content-i-generate-on-the-platform",
)
ROLE_TERMS = {
    "calm polished narrator": {
        "calm", "soothing", "gentle", "narration", "narrator", "narrative", "storyteller",
        "documentary", "measured", "polished",
    },
    "conversational presenter": {
        "conversational", "conversation", "natural", "friendly", "approachable", "presenter",
    },
    "technical explainer": {
        "technical", "explainer", "informative", "educational", "training", "clear", "professional",
    },
    "slightly energetic sports-technology": {
        "energetic", "upbeat", "dynamic", "sports", "sport", "presenter", "broadcaster",
        "broadcast", "enthusiastic", "promotional",
    },
    "warmer or lower alternative": {
        "warm", "deep", "low", "rich", "resonant", "mature", "grounded",
    },
}
INCOMPATIBLE_RESTRICTION = re.compile(
    r"\b(?:non[- ]commercial|personal use only|not for commercial use|"
    r"no commercial use|not for public distribution|no public distribution|"
    r"commercial use prohibited)\b",
    re.IGNORECASE,
)


class ElevenLabsError(RuntimeError):
    """A sanitized integration error that never includes credentials or SDK bodies."""


@dataclass(frozen=True)
class VoiceCandidate:
    voice_id: str
    name: str
    category: str
    labels: dict[str, str]
    description: str
    available_for_tiers: tuple[str, ...]
    compatible_model_ids: tuple[str, ...]
    roles: tuple[str, ...]
    tier_access_note: str
    restriction_note: str


@dataclass(frozen=True)
class Preflight:
    tier: str
    status: str
    remaining_characters: int
    required_characters: int
    model_id: str
    supports_style: bool
    supports_speaker_boost: bool


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _retryable(exc: Exception) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError)):
        return True
    status = _field(exc, "status_code")
    return status == 429 or isinstance(status, int) and status >= 500


def _bounded_api_call(
    call: Callable[[], Any],
    *,
    operation: str,
    max_attempts: int = MAX_API_ATTEMPTS,
    sleeper: Callable[[float], None] = time.sleep,
) -> tuple[Any, int]:
    if not 1 <= max_attempts <= MAX_API_ATTEMPTS:
        raise ValueError("API retry bound is invalid")
    for attempt in range(1, max_attempts + 1):
        try:
            return call(), attempt
        except Exception as exc:
            if attempt < max_attempts and _retryable(exc):
                sleeper(0.25 * attempt)
                continue
            raise ElevenLabsError(f"{operation} failed; SDK details were withheld") from None
    raise ElevenLabsError(f"{operation} failed; SDK details were withheld")


def create_client(api_key: str | None = None) -> Any:
    key = api_key if api_key is not None else os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise ElevenLabsError("ELEVENLABS_API_KEY is missing from the process environment")
    try:
        from elevenlabs import ElevenLabs
    except ImportError:
        raise ElevenLabsError('Install the optional narration extra with: pip install -e ".[narration]"') from None
    try:
        return ElevenLabs(api_key=key, timeout=REQUEST_OPTIONS["timeout_in_seconds"])
    except Exception:
        raise ElevenLabsError("ElevenLabs client initialization failed; details were withheld") from None


def _load_local_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        raise ElevenLabsError('Install the optional narration extra with: pip install -e ".[narration]"') from None
    load_dotenv(ROOT / ".env", override=False)


def _clean_labels(raw: Any) -> dict[str, str]:
    if not isinstance(raw, Mapping):
        return {}
    return {
        str(key).strip().lower(): str(value).strip()
        for key, value in raw.items()
        if value is not None and str(value).strip()
    }


def _is_english(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in {"en", "english"} or normalized.startswith(("en-", "english "))


def _is_british(value: str) -> bool:
    return bool(re.search(r"\bbritish\b|\bunited kingdom\b|\buk\b", value, re.IGNORECASE))


def _role_matches(labels: Mapping[str, str], description: str) -> tuple[str, ...]:
    searchable = " ".join([description, *labels.values()]).lower()
    words = set(re.findall(r"[a-z]+", searchable))
    return tuple(
        role for role, terms in ROLE_TERMS.items()
        if any(term in words or term.replace("-", " ") in searchable for term in terms)
    )


def _voice_candidate(voice: Any, *, starter_verified: bool = False) -> VoiceCandidate | None:
    category = str(_field(voice, "category", "") or "").strip().lower()
    if category != "premade":
        return None

    tiers_raw = _field(voice, "available_for_tiers")
    tiers = (
        tuple(sorted(str(tier).strip().lower() for tier in tiers_raw))
        if isinstance(tiers_raw, (list, tuple, set))
        else ()
    )
    if tiers and "starter" not in tiers or not tiers and not starter_verified:
        return None

    labels = _clean_labels(_field(voice, "labels", {}))
    verified = _field(voice, "verified_languages", ()) or ()
    verified_languages: list[str] = []
    verified_accents: list[str] = []
    compatible_models: set[str] = set()
    for language in verified:
        lang_name = str(_field(language, "language", "") or "")
        lang_code = str(_field(language, "language_code", "") or "")
        accent = str(_field(language, "accent", "") or "")
        verified_languages.extend((lang_name, lang_code))
        verified_accents.append(accent)
        if (
            (_is_english(lang_name) or _is_english(lang_code))
            and _is_british(accent)
            and _field(language, "model_id")
        ):
            compatible_models.add(str(_field(language, "model_id")))

    language_values = [labels.get("language", ""), *verified_languages]
    accent_values = [labels.get("accent", ""), *verified_accents]
    if not any(_is_english(value) for value in language_values):
        return None
    if not any(_is_british(value) for value in accent_values):
        return None
    if MODEL_ID not in compatible_models:
        return None

    name = str(_field(voice, "name", "") or "").strip()
    voice_id = str(_field(voice, "voice_id", "") or "").strip()
    if not name or not voice_id:
        return None

    description = re.sub(r"\s+", " ", str(_field(voice, "description", "") or "")).strip()
    sharing = _field(voice, "sharing")
    sharing_terms = str(_field(sharing, "terms", "") or "").strip() if sharing else ""
    restriction_text = " ".join((description, sharing_terms, *labels.values()))
    if INCOMPATIBLE_RESTRICTION.search(restriction_text):
        return None
    note = (
        "No voice-specific incompatible use restriction was present in the returned metadata; "
        "the account terms and public-use rights still require human review."
    )
    if sharing_terms:
        note = f"Voice sharing terms were returned and require human review: {sharing_terms[:240]}"

    return VoiceCandidate(
        voice_id=voice_id,
        name=name,
        category=category,
        labels=labels,
        description=description[:500],
        available_for_tiers=tiers,
        compatible_model_ids=tuple(sorted(compatible_models)),
        roles=_role_matches(labels, description),
        tier_access_note=(
            "The authenticated voice-search endpoint listed this voice while the active Starter plan was verified; "
            "the API omitted an explicit tier list."
            if not tiers
            else "The voice metadata explicitly lists Starter availability."
        ),
        restriction_note=note,
    )


def discover_voices(client: Any, *, starter_verified: bool = False) -> list[VoiceCandidate]:
    if not starter_verified:
        raise ElevenLabsError("Verify the active Starter subscription before voice discovery")
    voices: list[Any] = []
    token: str | None = None
    seen_tokens: set[str] = set()
    for _ in range(MAX_VOICE_PAGES):
        params: dict[str, Any] = {
            "category": "premade",
            "voice_type": "default",
            "language": "en",
            "page_size": 100,
            "include_total_count": False,
            "request_options": REQUEST_OPTIONS,
        }
        if token:
            params["next_page_token"] = token
        response, _ = _bounded_api_call(
            lambda params=params: client.voices.search(**params),
            operation="Voice discovery",
        )
        page = _field(response, "voices")
        if not isinstance(page, (list, tuple)):
            raise ElevenLabsError("Voice discovery returned an invalid response")
        voices.extend(page)
        if not _field(response, "has_more", False):
            break
        token = _field(response, "next_page_token")
        if not isinstance(token, str) or not token or token in seen_tokens:
            raise ElevenLabsError("Voice discovery pagination was invalid")
        seen_tokens.add(token)
    else:
        raise ElevenLabsError("Voice discovery exceeded the bounded page limit")

    candidates = {
        candidate.voice_id: candidate
        for voice in voices
        if (candidate := _voice_candidate(voice, starter_verified=starter_verified)) is not None
    }
    return sorted(candidates.values(), key=lambda candidate: candidate.name.casefold())


def shortlist_voices(candidates: list[VoiceCandidate], count: int = 3) -> list[VoiceCandidate]:
    if not 3 <= count <= 5:
        raise ElevenLabsError("The British stock-voice shortlist must contain three to five voices")
    if len(candidates) < count:
        raise ElevenLabsError(
            f"Only {len(candidates)} eligible Starter British premade voices were verified; at least {count} are required"
        )

    chosen: list[VoiceCandidate] = []
    uncovered = set(ROLE_TERMS)
    remaining = list(candidates)
    while remaining and len(chosen) < count:
        best = max(
            remaining,
            key=lambda voice: (
                len(uncovered.intersection(voice.roles)),
                len(voice.roles),
                voice.name.casefold(),
            ),
        )
        chosen.append(best)
        uncovered.difference_update(best.roles)
        remaining.remove(best)
    return chosen


def _model_record(models: list[Any], model_id: str) -> Any | None:
    return next((model for model in models if _field(model, "model_id") == model_id), None)


def _validate_model(model: Any) -> bool:
    if (
        _field(model, "model_id") not in STABLE_MODEL_IDS
        or not _field(model, "can_do_text_to_speech", False)
        or _field(model, "requires_alpha_access", False)
    ):
        return False
    languages = _field(model, "languages", ()) or ()
    language_names = " ".join(
        f"{_field(language, 'language_id', '')} {_field(language, 'name', '')}"
        for language in languages
    )
    return not languages or "english" in language_names.casefold() or bool(re.search(r"\ben\b", language_names))


def _script_character_count(path: Path) -> int:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        units = payload["units"]
        if len(units) != 10 or any(not str(unit["revised_spoken_text"]).strip() for unit in units):
            raise ValueError
        return sum(len(str(unit["revised_spoken_text"])) for unit in units)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        raise ElevenLabsError("The approved ten-unit narration script could not be validated") from None


def _required_characters(script_characters: int, voice_count: int = 3) -> int:
    variants = voice_count * 2
    pronunciations = voice_count
    audition_chars = variants * len(AUDITION_TEXT) + pronunciations * len(PRONUNCIATION_TEXT)
    retry_reserve = audition_chars
    full_render_reserve = 2 * script_characters + pronunciations * len(PRONUNCIATION_TEXT)
    return math.ceil((retry_reserve + audition_chars + full_render_reserve) * 1.10)


def verify_model_and_subscription(client: Any, voice_count: int = 3) -> Preflight:
    models, _ = _bounded_api_call(
        lambda: client.models.list(request_options=REQUEST_OPTIONS),
        operation="Model discovery",
    )
    if not isinstance(models, (list, tuple)):
        raise ElevenLabsError("Model discovery returned an invalid response")
    model = _model_record(list(models), MODEL_ID)
    if model is None or not _validate_model(model):
        raise ElevenLabsError("The approved stable, non-Beta speech model is not available")

    subscription, _ = _bounded_api_call(
        lambda: client.user.subscription.get(request_options=REQUEST_OPTIONS),
        operation="Subscription verification",
    )
    tier = str(_field(subscription, "tier", "") or "").strip().lower()
    status = str(_field(subscription, "status", "") or "").strip().lower()
    try:
        used = int(_field(subscription, "character_count"))
        limit = int(_field(subscription, "character_limit"))
    except (TypeError, ValueError):
        raise ElevenLabsError("Subscription character availability could not be verified") from None
    if tier != "starter" or status != "active":
        raise ElevenLabsError("An active paid Starter subscription was not verified")
    remaining = max(limit - used, 0)
    script_characters = _script_character_count(
        ROOT / "submission" / "final-support" / "MATCHPULSE_NARRATION_CONVERSATIONAL_V2.json"
    )
    required = _required_characters(script_characters, voice_count)
    if remaining < required:
        raise ElevenLabsError(
            f"Insufficient remaining Starter characters for bounded auditions and the reserved full-render plan "
            f"(available={remaining}, required={required})"
        )
    return Preflight(
        tier=tier,
        status=status,
        remaining_characters=remaining,
        required_characters=required,
        model_id=MODEL_ID,
        supports_style=bool(_field(model, "can_use_style", False)),
        supports_speaker_boost=bool(_field(model, "can_use_speaker_boost", False)),
    )


def _validate_settings(settings: Mapping[str, Any]) -> dict[str, Any]:
    required = {"stability", "similarity_boost", "speed", "use_speaker_boost"}
    if not required.issubset(settings):
        raise ElevenLabsError("Voice settings are incomplete")
    try:
        stability = float(settings["stability"])
        similarity = float(settings["similarity_boost"])
        speed = float(settings["speed"])
        style = float(settings.get("style", 0.0))
    except (TypeError, ValueError):
        raise ElevenLabsError("Voice settings are invalid") from None
    if not 0 <= stability <= 1 or not 0 <= similarity <= 1 or not 0 <= style <= 1 or not 0.7 <= speed <= 1.2:
        raise ElevenLabsError("Voice settings are outside supported bounds")
    if not isinstance(settings["use_speaker_boost"], bool):
        raise ElevenLabsError("Speaker boost must be an explicit boolean")
    return dict(settings)


def _approved_output_path(path: Path, suffix: str) -> Path:
    requested_dir = Path(tempfile.gettempdir()) / "matchpulse-elevenlabs-auditions"
    if requested_dir.is_symlink() or getattr(requested_dir, "is_junction", lambda: False)():
        raise ElevenLabsError("The temporary audition directory may not be redirected")
    approved_dir = requested_dir.resolve()
    if approved_dir.parent != Path(tempfile.gettempdir()).resolve():
        raise ElevenLabsError("The temporary audition directory is outside the system temp root")
    try:
        output = path.resolve(strict=False)
    except OSError:
        raise ElevenLabsError("The requested output path could not be resolved") from None
    if output.parent != approved_dir or output.suffix.lower() != suffix:
        raise ElevenLabsError("Audio outputs are restricted to the approved temporary audition directory")
    return output


def _collect_audio(stream: Any) -> bytes:
    if stream is None or isinstance(stream, (str, bytes, bytearray, Mapping)):
        raise ElevenLabsError("Text-to-speech returned an invalid response type")
    try:
        chunks = list(stream)
    except Exception:
        raise ElevenLabsError("Text-to-speech response streaming failed; SDK details were withheld") from None
    if not chunks or any(not isinstance(chunk, (bytes, bytearray)) for chunk in chunks):
        raise ElevenLabsError("Text-to-speech returned empty or invalid audio")
    audio = b"".join(chunks)
    if not audio:
        raise ElevenLabsError("Text-to-speech returned empty audio")
    if not (audio.startswith(b"ID3") or len(audio) >= 2 and audio[0] == 0xFF and audio[1] & 0xE0 == 0xE0):
        raise ElevenLabsError("Text-to-speech response did not match the requested MP3 format")
    return audio


def _write_exclusive(path: Path, content: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError:
        raise ElevenLabsError("Output collision detected; refusing to overwrite an existing file") from None
    try:
        with os.fdopen(descriptor, "wb") as target:
            target.write(content)
    except Exception:
        path.unlink(missing_ok=True)
        raise ElevenLabsError("Could not safely write the temporary audio output") from None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _ffprobe(path: Path) -> dict[str, Any]:
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration,format_name:stream=codec_name,sample_rate,channels",
                "-of", "json", str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        payload = json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        raise ElevenLabsError("FFprobe could not validate the generated audio") from None
    streams = payload.get("streams", [])
    if not streams or not payload.get("format", {}).get("duration"):
        raise ElevenLabsError("Generated audio metadata was incomplete")
    return payload


def _measure_loudness(path: Path) -> dict[str, float]:
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-nostats", "-nostdin", "-i", str(path),
                "-af", f"loudnorm=I={TARGET_LOUDNESS_LUFS}:TP={TARGET_TRUE_PEAK_DBTP}:LRA=9:print_format=json",
                "-f", "null", "-",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=90,
        )
    except (OSError, subprocess.SubprocessError):
        raise ElevenLabsError("FFmpeg could not measure audition loudness") from None
    matches = re.findall(r"\{[^{}]*\}", result.stderr, re.DOTALL)
    if not matches:
        raise ElevenLabsError("FFmpeg returned no loudness measurement")
    try:
        stats = json.loads(matches[-1])
        measured = {
            "integrated_lufs": float(stats["input_i"]),
            "true_peak_dbtp": float(stats["input_tp"]),
            "lra_lu": float(stats["input_lra"]),
            "threshold_lufs": float(stats["input_thresh"]),
            "target_offset_lu": float(stats["target_offset"]),
        }
        if any(not math.isfinite(value) for value in measured.values()):
            raise ValueError
        return measured
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        raise ElevenLabsError("FFmpeg returned invalid loudness measurements") from None


def _normalized_record(path: Path) -> dict[str, Any]:
    output = _approved_output_path(path, ".wav")
    if not output.is_file():
        raise ElevenLabsError("Normalized review audio is missing")
    measured = _measure_loudness(output)
    probe = _ffprobe(output)
    audio_stream = next((stream for stream in probe["streams"] if stream.get("codec_name") == "pcm_s16le"), None)
    if (
        audio_stream is None
        or audio_stream.get("sample_rate") != str(TARGET_SAMPLE_RATE)
        or audio_stream.get("channels") != TARGET_CHANNELS
        or abs(measured["integrated_lufs"] - TARGET_LOUDNESS_LUFS) > 0.15
        or measured["true_peak_dbtp"] > TARGET_TRUE_PEAK_DBTP + 0.1
    ):
        raise ElevenLabsError("Normalized review audio did not meet the required format or loudness targets")
    return {
        "path": output,
        "sha256": _sha256(output),
        "duration_seconds": float(probe["format"]["duration"]),
        "sample_rate": TARGET_SAMPLE_RATE,
        "channels": TARGET_CHANNELS,
        "integrated_lufs": measured["integrated_lufs"],
        "true_peak_dbtp": measured["true_peak_dbtp"],
    }


def normalize_audio(source: Path, destination: Path) -> dict[str, Any]:
    output = _approved_output_path(destination, ".wav")
    if output.exists():
        raise ElevenLabsError("Normalized output collision detected; refusing to overwrite")
    measured = _measure_loudness(source)
    loudnorm = (
        f"loudnorm=I={TARGET_LOUDNESS_LUFS}:TP={TARGET_TRUE_PEAK_DBTP}:LRA=9:"
        f"measured_I={measured['integrated_lufs']}:measured_TP={measured['true_peak_dbtp']}:"
        f"measured_LRA={measured['lra_lu']}:measured_thresh={measured['threshold_lufs']}:"
        f"offset={measured['target_offset_lu']}:linear=true"
    )
    approved_dir = output.parent
    try:
        with tempfile.TemporaryDirectory(prefix="normalize-", dir=approved_dir) as work_dir:
            intermediate = Path(work_dir) / "pass1.wav"
            subprocess.run(
                [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostats", "-nostdin",
                    "-i", str(source), "-af", loudnorm, "-ar", str(TARGET_SAMPLE_RATE),
                    "-ac", str(TARGET_CHANNELS), "-c:a", "pcm_s16le", "-f", "wav", "-n", str(intermediate),
                ],
                capture_output=True,
                check=True,
                timeout=120,
            )
            after_pass = _measure_loudness(intermediate)
            correction_db = TARGET_LOUDNESS_LUFS - after_pass["integrated_lufs"]
            if after_pass["true_peak_dbtp"] + correction_db > TARGET_TRUE_PEAK_DBTP + 0.05:
                raise ElevenLabsError("Loudness correction would exceed the true-peak ceiling")
            subprocess.run(
                [
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostats", "-nostdin",
                    "-i", str(intermediate), "-af", f"volume={correction_db:.4f}dB",
                    "-ar", str(TARGET_SAMPLE_RATE), "-ac", str(TARGET_CHANNELS),
                    "-c:a", "pcm_s16le", "-f", "wav", "-n", str(output),
                ],
                capture_output=True,
                check=True,
                timeout=120,
            )
    except ElevenLabsError:
        if output.exists():
            output.unlink()
        raise
    except (OSError, subprocess.SubprocessError):
        if output.exists():
            output.unlink()
        raise ElevenLabsError("FFmpeg could not create the normalized review copy") from None
    normalized = _normalized_record(output)
    normalized["analysis_loudness"] = measured["integrated_lufs"]
    return normalized


def synthesize_audio(
    client: Any,
    *,
    text: str,
    voice_id: str,
    model_id: str,
    settings: Mapping[str, Any],
    output_path: Path,
    eligible_voices: Mapping[str, VoiceCandidate],
    available_stable_models: set[str],
) -> dict[str, Any]:
    if not text.strip():
        raise ElevenLabsError("Synthesis text must not be empty")
    voice = eligible_voices.get(voice_id)
    if (
        voice is None
        or voice.category != "premade"
        or ("starter" not in voice.available_for_tiers and "active Starter plan" not in voice.tier_access_note)
        or model_id not in voice.compatible_model_ids
    ):
        raise ElevenLabsError("Synthesis requires a verified Starter-eligible premade British voice")
    if model_id not in STABLE_MODEL_IDS or model_id not in available_stable_models:
        raise ElevenLabsError("Synthesis requires a verified stable non-Beta model")
    request_settings = _validate_settings(settings)
    output = _approved_output_path(output_path, ".mp3")
    if output.exists():
        raise ElevenLabsError("Raw output collision detected; refusing to overwrite")

    def request_audio() -> bytes:
        stream = client.text_to_speech.convert(
            voice_id,
            text=text,
            model_id=model_id,
            output_format="mp3_44100_128",
            voice_settings=request_settings,
            enable_logging=False,
            request_options=REQUEST_OPTIONS,
        )
        return _collect_audio(stream)

    audio, attempts = _bounded_api_call(request_audio, operation="Speech generation")
    _write_exclusive(output, audio)
    probe = _ffprobe(output)
    audio_stream = next((stream for stream in probe["streams"] if stream.get("codec_name") == "mp3"), None)
    if audio_stream is None or "mp3" not in probe["format"].get("format_name", ""):
        output.unlink(missing_ok=True)
        raise ElevenLabsError("Generated audio did not decode as MP3")
    return {
        "path": output,
        "sha256": _sha256(output),
        "duration_seconds": float(probe["format"]["duration"]),
        "requested_characters": len(text),
        "api_attempts": attempts,
        "generation_utc": _utc_now(),
        "generation_timestamp_basis": "ElevenLabs response completion time",
        "sample_rate": audio_stream.get("sample_rate"),
        "channels": audio_stream.get("channels"),
    }


def _existing_raw_record(path: Path, text: str) -> dict[str, Any]:
    output = _approved_output_path(path, ".mp3")
    probe = _ffprobe(output)
    audio_stream = next((stream for stream in probe["streams"] if stream.get("codec_name") == "mp3"), None)
    if audio_stream is None or "mp3" not in probe["format"].get("format_name", ""):
        raise ElevenLabsError("A prior raw audition file did not validate as MP3")
    generated = datetime.fromtimestamp(output.stat().st_mtime, UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    return {
        "path": output,
        "sha256": _sha256(output),
        "duration_seconds": float(probe["format"]["duration"]),
        "requested_characters": len(text),
        "api_attempts": "not persisted by the interrupted first run",
        "generation_utc": generated,
        "generation_timestamp_basis": "temporary-file modification time",
        "sample_rate": audio_stream.get("sample_rate"),
        "channels": audio_stream.get("channels"),
    }


def _variant_settings(variant: str, preflight: Preflight) -> dict[str, Any]:
    if variant == "MEASURED_CONVERSATIONAL":
        settings = {
            "stability": 0.62,
            "similarity_boost": 0.78,
            "speed": 0.98,
            "use_speaker_boost": False,
        }
        if preflight.supports_style:
            settings["style"] = 0.12
    elif variant == "ENERGETIC_EXPLAINER":
        settings = {
            "stability": 0.52,
            "similarity_boost": 0.78,
            "speed": 1.03,
            "use_speaker_boost": False,
        }
        if preflight.supports_style:
            settings["style"] = 0.25
    else:
        raise ElevenLabsError("Unknown audition variant")
    if not preflight.supports_speaker_boost:
        settings["use_speaker_boost"] = False
    return settings


def _safe_stem_part(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return result[:48] or "voice"


def _sample_stem(number: int, voice: VoiceCandidate, variant: str) -> str:
    name = _safe_stem_part(voice.name)
    suffix = re.sub(r"[^a-zA-Z0-9]", "", voice.voice_id)[-6:].lower() or "voiceid"
    return f"{number:02d}_{name}_{suffix}_{variant}"


def _unique_stem(directory: Path, number: int, voice: VoiceCandidate, variant: str) -> str:
    while True:
        stem = _sample_stem(number, voice, variant)
        if not (directory / f"{stem}.mp3").exists() and not (directory / f"{stem}.wav").exists():
            return stem
        number += 1


def _voice_summary(voice: VoiceCandidate, model_id: str) -> str:
    labels = ", ".join(f"{key}={value}" for key, value in sorted(voice.labels.items()))
    roles = ", ".join(voice.roles) or "metadata does not identify a narrower style"
    description = voice.description or "No description returned."
    return (
        f"- **{voice.name}** (`{voice.voice_id}`): category `{voice.category}`; "
        f"accent `{voice.labels.get('accent', 'verified-language metadata')}`; "
        f"style/use-case metadata: {labels or 'none returned'}; "
        f"compatible stable models: {', '.join(voice.compatible_model_ids)}. "
        f"Starter access: {voice.tier_access_note} "
        f"Why shortlisted: metadata suggests {roles}. Description: {description} "
        f"Restriction note: {voice.restriction_note}"
    )


def _settings_summary(settings: Mapping[str, Any]) -> str:
    keys = ("stability", "similarity_boost", "style", "speed", "use_speaker_boost")
    return ", ".join(f"{key}={settings[key]}" for key in keys if key in settings)


def _format_result(label: str, voice: VoiceCandidate, settings: Mapping[str, Any], raw: dict[str, Any], normalized: dict[str, Any]) -> str:
    return (
        f"### {label}: {voice.name} (`{voice.voice_id}`)\n"
        f"- Category: `{voice.category}`; accent metadata: `{voice.labels.get('accent', 'verified British')}`\n"
        f"- Model: `{MODEL_ID}`; settings: `{_settings_summary(settings)}`\n"
        f"- Duration: {normalized['duration_seconds']:.2f} s\n"
        f"- Loudness: {normalized['integrated_lufs']:.2f} LUFS; true peak: "
        f"{normalized['true_peak_dbtp']:.2f} dBTP\n"
        f"- Raw format: MP3, {raw['sample_rate']} Hz, {raw['channels']} channels; "
        f"normalized format: WAV, {normalized['sample_rate']} Hz, {normalized['channels']} channels\n"
        f"- Raw MP3 SHA-256: `{raw['sha256']}`; normalized WAV SHA-256: `{normalized['sha256']}`\n"
        f"- Generated UTC: `{raw['generation_utc']}`\n"
        f"- Timestamp basis: {raw['generation_timestamp_basis']}\n"
        f"- Request usage estimate: {raw['requested_characters']} text characters; "
        f"attempts: {raw['api_attempts']}. Account billing headers were not logged.\n"
        f"- Terms/restriction note: {voice.restriction_note}\n"
        f"- Terms to review: {', '.join(TERMS_URLS)}\n"
        f"{'- Normalization note: ' + normalized['normalization_note'] + chr(10) if normalized.get('normalization_note') else ''}"
        "- Human notes: _Add listening notes here._\n"
        f"- Raw file: `{raw['path'].name}`; review file: `{normalized['path'].name}`\n"
    )


def run_auditions(client: Any, voices: list[VoiceCandidate], preflight: Preflight) -> Path:
    if len(voices) != 3:
        raise ElevenLabsError("The bounded audition plan requires exactly three shortlisted voices")
    requested_dir = Path(tempfile.gettempdir()) / "matchpulse-elevenlabs-auditions"
    if requested_dir.is_symlink() or getattr(requested_dir, "is_junction", lambda: False)():
        raise ElevenLabsError("The temporary audition directory may not be redirected")
    requested_dir.mkdir(parents=True, exist_ok=True)
    directory = requested_dir.resolve()
    if directory.parent != Path(tempfile.gettempdir()).resolve():
        raise ElevenLabsError("The temporary audition directory resolved outside the system temp root")
    if len(voices) * 3 > MAX_INITIAL_AUDITIONS:
        raise ElevenLabsError("The bounded plan would exceed the initial generation limit")
    summary_path = directory / "AUDITION_SUMMARY.md"
    if summary_path.exists():
        raise ElevenLabsError("The audition summary already exists; refusing to overwrite prior review evidence")
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise ElevenLabsError("FFmpeg and FFprobe are required before voice generation")

    lines = [
        "# ElevenLabs British stock-voice audition summary",
        "",
        f"- Generated at (UTC): `{_utc_now()}`",
        f"- Plan: `{preflight.tier.upper()}`; status: `{preflight.status.upper()}`",
        f"- Model: `{preflight.model_id}` (stable, non-Beta, TTS-capable)",
        f"- Character headroom before generation: {preflight.remaining_characters}; conservative reserve: "
        f"{preflight.required_characters}.",
        f"- Planned initial generations: {len(voices) * 2} audition variants plus {len(voices)} pronunciation checks "
        f"({len(voices) * 3} total; cap {MAX_INITIAL_AUDITIONS}).",
        "- Voice cloning: `NO`; community voices: `EXCLUDED`",
        "- Full narration: `NOT GENERATED`; replacement MP4: `NOT CREATED`",
        "- Output location: local temporary directory only; nothing uploaded.",
        "",
        "## Shortlist",
        "",
    ]
    for voice in voices:
        lines.append(_voice_summary(voice, preflight.model_id))
        lines.append("")

    results: list[str] = []
    sample_number = 1
    correction_number = MAX_INITIAL_AUDITIONS + 1
    eligible_voices = {voice.voice_id: voice for voice in voices}
    for voice in voices:
        samples = [
            ("MEASURED_CONVERSATIONAL", AUDITION_TEXT),
            ("ENERGETIC_EXPLAINER", AUDITION_TEXT),
            ("PRONUNCIATION", PRONUNCIATION_TEXT),
        ]
        for variant, text in samples:
            stem = _sample_stem(sample_number, voice, variant)
            raw_path = directory / f"{stem}.mp3"
            settings_variant = "MEASURED_CONVERSATIONAL" if variant == "PRONUNCIATION" else variant
            settings = _variant_settings(settings_variant, preflight)
            if raw_path.exists():
                raw = _existing_raw_record(raw_path, text)
            else:
                stem = _unique_stem(directory, sample_number, voice, variant)
                raw_path = directory / f"{stem}.mp3"
                raw = synthesize_audio(
                    client,
                    text=text,
                    voice_id=voice.voice_id,
                    model_id=preflight.model_id,
                    settings=settings,
                    output_path=raw_path,
                    eligible_voices=eligible_voices,
                    available_stable_models={preflight.model_id},
                )
            normalized_path = directory / f"{stem}.wav"
            normalization_note = None
            try:
                if normalized_path.exists():
                    normalized = _normalized_record(normalized_path)
                else:
                    normalized = normalize_audio(raw["path"], normalized_path)
            except ElevenLabsError:
                if not normalized_path.exists():
                    raise
                normalization_note = "An earlier review copy failed validation and was preserved; this corrected copy is separate."
                corrected_stem = _unique_stem(directory, correction_number, voice, variant)
                correction_number = int(corrected_stem.split("_", 1)[0]) + 1
                normalized = normalize_audio(raw["path"], directory / f"{corrected_stem}.wav")
                normalized["normalization_note"] = normalization_note
            results.append(_format_result(variant, voice, settings, raw, normalized))
            sample_number += 1

    lines.extend(["## Audition and pronunciation samples", ""])
    lines.extend(results)
    lines.extend(
        [
            "## Human decision required",
            "",
            "Do not generate full narration until a human selects one option:",
            "",
            "`SELECT_ELEVENLABS_VOICE=<VOICE_ID>` with `SELECT_ELEVENLABS_VARIANT=MEASURED_CONVERSATIONAL`",
            "",
            "`SELECT_ELEVENLABS_VOICE=<VOICE_ID>` with `SELECT_ELEVENLABS_VARIANT=ENERGETIC_EXPLAINER`",
            "",
            "`AUDITION_MORE_BRITISH_VOICES`",
            "",
            "`NO_ELEVENLABS_VOICE_APPROVED`",
            "",
            "No winner was selected automatically.",
            "",
        ]
    )
    try:
        with summary_path.open("x", encoding="utf-8", newline="\n") as summary:
            summary.write("\n".join(lines))
    except FileExistsError:
        raise ElevenLabsError("The audition summary already exists; refusing to overwrite prior review evidence") from None
    except OSError:
        raise ElevenLabsError("Could not safely write the audition summary") from None
    return summary_path


def discover_only(client: Any) -> tuple[Preflight, list[VoiceCandidate]]:
    preflight = verify_model_and_subscription(client, voice_count=3)
    candidates = discover_voices(client, starter_verified=preflight.tier == "starter" and preflight.status == "active")
    shortlist = shortlist_voices(candidates, 3)
    return preflight, shortlist


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("discover", "audition"))
    args = parser.parse_args(argv)
    try:
        _load_local_env()
        client = create_client()
        preflight, shortlist = discover_only(client)
        safe_result = {
            "plan": preflight.tier,
            "status": preflight.status,
            "remaining_characters": preflight.remaining_characters,
            "reserved_characters": preflight.required_characters,
            "stable_model": preflight.model_id,
            "supports_style": preflight.supports_style,
            "shortlist": [
                {
                    "name": voice.name,
                    "voice_id": voice.voice_id,
                    "category": voice.category,
                    "labels": voice.labels,
                    "available_for_tiers": voice.available_for_tiers,
                    "compatible_model_ids": voice.compatible_model_ids,
                    "roles": voice.roles,
                    "description": voice.description,
                    "tier_access_note": voice.tier_access_note,
                    "restriction_note": voice.restriction_note,
                }
                for voice in shortlist
            ],
        }
        print(json.dumps(safe_result, indent=2, ensure_ascii=False))
        if args.command == "audition":
            summary_path = run_auditions(client, shortlist, preflight)
            print(f"AUDITION_SUMMARY={summary_path}")
    except ElevenLabsError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    finally:
        os.environ.pop("ELEVENLABS_API_KEY", None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
