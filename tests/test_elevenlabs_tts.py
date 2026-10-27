from __future__ import annotations

import ast
import hashlib
import tempfile
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import matchpulse_elevenlabs_tts as tts


def _voice(
    *,
    category: str = "premade",
    tiers: list[str] | None = None,
    language: str = "English",
    verified_language: str | None = None,
    accent: str = "British",
    verified_accent: str | None = None,
    description: str = "A warm, clear conversational narrator.",
) -> SimpleNamespace:
    return SimpleNamespace(
        voice_id="stock-voice-123456",
        name="British Narrator",
        category=category,
        available_for_tiers=tiers if tiers is not None else ["starter"],
        labels={"language": language, "accent": accent, "use_case": "narration"},
        description=description,
        sharing=None,
        verified_languages=[
            SimpleNamespace(
                language=verified_language or ("es" if language == "Spanish" else "en"),
                language_code=verified_language or ("es" if language == "Spanish" else "en"),
                accent=(verified_accent or accent).lower(),
                model_id=tts.MODEL_ID,
                locale="en-GB",
            )
        ],
    )


def test_missing_api_key_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    with pytest.raises(tts.ElevenLabsError, match="missing from the process environment"):
        tts.create_client()


def test_api_key_is_withheld_from_errors_and_logs(caplog: pytest.LogCaptureFixture) -> None:
    secret = "never-print-this-api-key"

    def fail() -> None:
        raise RuntimeError(f"request failed with credential {secret}")

    with pytest.raises(tts.ElevenLabsError) as error:
        tts._bounded_api_call(fail, operation="Test request")
    assert secret not in str(error.value)
    assert secret not in caplog.text
    assert error.value.__cause__ is None


def test_premade_voice_is_accepted_and_non_stock_categories_rejected() -> None:
    candidate = tts._voice_candidate(_voice())
    assert candidate is not None
    assert candidate.category == "premade"
    assert candidate.available_for_tiers == ("starter",)
    assert tts._voice_candidate(_voice(category="cloned")) is None
    assert tts._voice_candidate(_voice(category="community")) is None
    assert tts._voice_candidate(_voice(category="generated")) is None


def test_empty_tier_list_requires_verified_starter_account_listing() -> None:
    voice = _voice(tiers=[])
    assert tts._voice_candidate(voice) is None
    candidate = tts._voice_candidate(voice, starter_verified=True)
    assert candidate is not None
    assert "authenticated voice-search endpoint" in candidate.tier_access_note


def test_voice_requires_starter_and_explicit_british_english_metadata() -> None:
    assert tts._voice_candidate(_voice(tiers=["free"])) is None
    assert tts._voice_candidate(_voice(accent="American", verified_accent="American")) is None
    assert tts._voice_candidate(_voice(language="Spanish", verified_language="es")) is None


def test_stable_model_is_allowlisted_and_beta_models_are_rejected() -> None:
    stable = SimpleNamespace(
        model_id="eleven_multilingual_v2",
        can_do_text_to_speech=True,
        requires_alpha_access=False,
        languages=[SimpleNamespace(language_id="en", name="English")],
    )
    assert tts._validate_model(stable)
    for model_id in ("eleven_v4_beta", "eleven_flash_v3_beta", "unlisted-model"):
        assert not tts._validate_model(
            SimpleNamespace(
                model_id=model_id,
                can_do_text_to_speech=True,
                requires_alpha_access=False,
                languages=[SimpleNamespace(language_id="en", name="English")],
            )
        )
    assert not tts._validate_model(
        SimpleNamespace(
            model_id="eleven_multilingual_v2",
            can_do_text_to_speech=True,
            requires_alpha_access=True,
            languages=[SimpleNamespace(language_id="en", name="English")],
        )
    )


def test_output_collision_is_rejected_before_api_call() -> None:
    approved = Path(tempfile.gettempdir()) / "matchpulse-elevenlabs-auditions"
    approved.mkdir(exist_ok=True)
    output = approved / f"collision-test-{uuid.uuid4().hex}.mp3"
    with output.open("xb") as existing:
        existing.write(b"existing")

    class Client:
        class Speech:
            called = False

            def convert(self, *_args: object, **_kwargs: object) -> object:
                self.called = True
                return iter([b"ID3audio"])

        text_to_speech = Speech()

    client = Client()
    try:
        with pytest.raises(tts.ElevenLabsError, match="collision"):
            tts.synthesize_audio(
                client,
                text="test",
                voice_id="stock-voice-123456",
                model_id=tts.MODEL_ID,
                settings={
                    "stability": 0.6,
                    "similarity_boost": 0.75,
                    "speed": 1.0,
                    "use_speaker_boost": False,
                },
                output_path=output,
                eligible_voices={"stock-voice-123456": tts._voice_candidate(_voice())},
                available_stable_models={tts.MODEL_ID},
            )
        assert client.text_to_speech.called is False
    finally:
        output.unlink(missing_ok=True)


def test_invalid_tts_response_type_and_empty_audio_are_rejected() -> None:
    with pytest.raises(tts.ElevenLabsError, match="response type"):
        tts._collect_audio("not-a-stream")
    with pytest.raises(tts.ElevenLabsError, match="empty"):
        tts._collect_audio(iter(()))
    with pytest.raises(tts.ElevenLabsError, match="format"):
        tts._collect_audio(iter([b"not-mp3"]))


def test_synthesis_rejects_non_stock_voice_and_unverified_model() -> None:
    candidate = tts._voice_candidate(_voice())
    assert candidate is not None
    cloned = tts._voice_candidate(_voice(category="cloned"))
    assert cloned is None
    with pytest.raises(tts.ElevenLabsError, match="verified Starter-eligible"):
        tts.synthesize_audio(
            object(),
            text="test",
            voice_id="stock-voice-123456",
            model_id=tts.MODEL_ID,
            settings={
                "stability": 0.6,
                "similarity_boost": 0.75,
                "speed": 1.0,
                "use_speaker_boost": False,
            },
            output_path=Path(tempfile.gettempdir()) / "matchpulse-elevenlabs-auditions" / "unused.mp3",
            eligible_voices={
                "stock-voice-123456": SimpleNamespace(
                    category="cloned",
                    available_for_tiers=("starter",),
                    tier_access_note="active Starter plan",
                    compatible_model_ids=(tts.MODEL_ID,),
                )
            },
            available_stable_models={tts.MODEL_ID},
        )


def test_retry_count_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    sleeps: list[float] = []

    class ServiceUnavailable(RuntimeError):
        status_code = 503

    def fail() -> None:
        nonlocal calls
        calls += 1
        raise ServiceUnavailable("safe to withhold")

    with pytest.raises(tts.ElevenLabsError):
        tts._bounded_api_call(fail, operation="test", sleeper=sleeps.append)
    assert calls == tts.MAX_API_ATTEMPTS == 2
    assert sleeps == [0.25]


def test_timeout_and_retry_options_are_bounded() -> None:
    assert tts.REQUEST_OPTIONS == {"timeout_in_seconds": 30, "max_retries": 0}
    assert tts.MAX_API_ATTEMPTS == 2


def test_output_sha256_is_calculated_for_written_audio() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "audio.mp3"
        audio = b"ID3" + b"test-audio"
        tts._write_exclusive(path, audio)
        assert tts._sha256(path) == hashlib.sha256(audio).hexdigest()


def test_output_directory_is_restricted_to_temp_auditions() -> None:
    approved = Path(tempfile.gettempdir()) / "matchpulse-elevenlabs-auditions" / "one.mp3"
    assert tts._approved_output_path(approved, ".mp3") == approved.resolve()
    with pytest.raises(tts.ElevenLabsError, match="restricted"):
        tts._approved_output_path(Path.cwd() / "not-approved.mp3", ".mp3")
    with pytest.raises(tts.ElevenLabsError, match="restricted"):
        tts._approved_output_path(approved.with_suffix(".wav"), ".mp3")


def test_existing_kokoro_pipeline_is_not_imported_by_adapter() -> None:
    source = Path(tts.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    ] + [
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    ]
    assert not any("kokoro" in name.casefold() or "matchpulse_local_tts" in name for name in imports)


def test_adapter_has_no_browser_tts_upload_or_azure_fallback() -> None:
    source = Path(tts.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    ] + [
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    ]
    calls = [
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))
    ]
    assert not any(name.startswith("azure") for name in imports)
    assert not any("kokoro" in name.casefold() for name in imports)
    assert not any(name.casefold() in {"upload", "upload_file", "put_object"} for name in calls)
