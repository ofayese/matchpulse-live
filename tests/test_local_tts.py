from __future__ import annotations

import hashlib
import importlib
import io
import shutil
import sys
import tempfile
import wave
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

local_tts = importlib.import_module("matchpulse_local_tts")
recorder = importlib.import_module("record_matchpulse_demo")
hosted = importlib.import_module("record_matchpulse_hosted_submission")
LocalDockerTTS = local_tts.LocalDockerTTS
LocalTTSError = local_tts.LocalTTSError
plan_segment_window = local_tts.plan_segment_window
validate_loopback_url = local_tts.validate_loopback_url


def make_wav(seconds: float = 0.5, sample: int = 900) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(48_000)
        frame = int(sample).to_bytes(2, "little", signed=True) * 2
        output.writeframes(frame * round(seconds * 48_000))
    return buffer.getvalue()


def test_hosted_caption_layouts_keep_captions_in_safe_zones() -> None:
    base = recorder.Image.new("RGB", (recorder.VIDEO_WIDTH, recorder.VIDEO_HEIGHT), (20, 40, 60))
    lines = ("Readable caption", "Second line")
    font = recorder._load_fonts()["caption_large"]
    bounds = [recorder.ImageDraw.Draw(base).textbbox((0, 0), line, font=font) for line in lines]
    height = sum(box[3] - box[1] for box in bounds) + 8
    box_height = height + 36

    for layout, center_y in (("opening-card", 820), ("application-safe", 1022)):
        frame = recorder.draw_frame_overlays(
            base,
            cursor_xy=(100, 100),
            elapsed_sec=12,
            total_sec=115,
            caption_lines=lines,
            caption_layout=layout,
            timecode_y=1048,
        )
        panel_y = center_y - (box_height // 2 if layout == "opening-card" else box_height)
        assert frame.getpixel((200, panel_y + 4)) == (5, 16, 26)

    with pytest.raises(recorder.RecordingError, match="at most two lines"):
        recorder.draw_frame_overlays(
            base,
            cursor_xy=(100, 100),
            elapsed_sec=12,
            total_sec=115,
            caption_lines=("one", "two", "three"),
            caption_layout="application-safe",
        )


def create_adapter(tmp_path: Path, handler, *, retries: int = 2) -> LocalDockerTTS:
    return LocalDockerTTS(
        "http://127.0.0.1:8765",
        approved_output_dirs=(tmp_path, Path(tempfile.gettempdir())),
        retries=retries,
        transport=httpx.MockTransport(handler),
    )


def test_loopback_urls_are_accepted_and_non_loopback_urls_rejected() -> None:
    assert validate_loopback_url("http://127.0.0.1:7788") == "http://127.0.0.1:7788"
    assert validate_loopback_url("http://localhost:7788/") == "http://localhost:7788"
    assert validate_loopback_url("http://[::1]:7788") == "http://[::1]:7788"
    for url in (
        "https://127.0.0.1:7788",
        "http://example.com:7788",
        "http://192.168.1.40:7788",
        "http://10.0.0.2:7788",
        "http://0.0.0.0:7788",
        "http://user:pass@127.0.0.1:7788",
    ):
        with pytest.raises(LocalTTSError):
            validate_loopback_url(url)


def test_hosted_url_requires_an_explicit_matching_azure_host() -> None:
    host = "demo.example.azurecontainerapps.io"
    assert hosted.validate_url(f"https://{host}", host) == (f"https://{host}", host)
    for allowed_host in ("", "other.example.azurecontainerapps.io", "example.com"):
        with pytest.raises(ValueError, match="explicitly allowed"):
            hosted.validate_url(f"https://{host}", allowed_host)


def test_recorder_workspace_allowlist_is_explicit_and_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo_root = tmp_path / "matchpulse"
    repo_root.mkdir()
    (tmp_path / "private-sibling").mkdir()

    monkeypatch.delenv("MATCHPULSE_ALLOWED_WORKSPACE_SIBLINGS", raising=False)
    with pytest.raises(recorder.RecordingError) as exc_info:
        recorder.verify_workspace_root(repo_root)
    assert "private-sibling" not in str(exc_info.value)

    monkeypatch.setenv("MATCHPULSE_ALLOWED_WORKSPACE_SIBLINGS", "../private")
    with pytest.raises(recorder.RecordingError, match="directory names only"):
        recorder.verify_workspace_root(repo_root)

    monkeypatch.setenv("MATCHPULSE_ALLOWED_WORKSPACE_SIBLINGS", "private-sibling")
    assert recorder.verify_workspace_root(repo_root) == 2

    (tmp_path / "workspace-file.txt").touch()
    with pytest.raises(recorder.RecordingError, match="explicit sibling allowlist"):
        recorder.verify_workspace_root(repo_root)


def test_missing_service_fails_closed(tmp_path: Path) -> None:
    def unavailable(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("service is unavailable", request=request)

    with create_adapter(tmp_path, unavailable) as adapter:
        with pytest.raises(LocalTTSError, match="health check failed"):
            adapter.health_check()


def test_health_voice_discovery_and_segment_result(tmp_path: Path) -> None:
    audio = make_wav(0.25)
    calls = []

    def service(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        if request.url.path == "/v1/voices":
            return httpx.Response(200, json={"voices": [{"voice_id": "bf_emma"}]})
        return httpx.Response(200, headers={"content-type": "audio/wav; charset=binary"}, content=audio)

    with create_adapter(tmp_path, service) as adapter:
        assert adapter.health_check()["status"] == "ok"
        assert adapter.discover_voices() == ["bf_emma"]
        result = adapter.synthesize_segment(text="Secret narration", output_path=tmp_path / "one.wav")
    request = calls[-1]
    body = __import__("json").loads(request.content)
    assert body == {
        "model": "kokoro-v1.0",
        "input": "Secret narration",
        "voice": "bf_emma",
        "speed": 0.95,
        "response_format": "wav",
    }
    assert result.path.read_bytes() == audio
    assert result.duration == pytest.approx(0.25)
    assert result.sha256 == hashlib.sha256(audio).hexdigest()
    assert result.sample_rate == 48_000 and result.channels == 2 and result.attempts == 1


@pytest.mark.parametrize(
    ("content_type", "audio", "message"),
    [
        ("application/json", make_wav(), "Content-Type"),
        ("audio/wav", b"", "invalid or empty WAV"),
        ("audio/wav", b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * 32, "unparseable WAV"),
    ],
    ids=["wrong-content-type", "empty-wave", "invalid-wave"],
)
def test_rejects_invalid_audio_responses(tmp_path: Path, content_type: str, audio: bytes, message: str) -> None:
    def service(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": content_type}, content=audio)

    with create_adapter(tmp_path, service) as adapter:
        with pytest.raises(LocalTTSError, match=message):
            adapter.synthesize_segment(text="No output", output_path=tmp_path / "bad.wav")
    assert not (tmp_path / "bad.wav").exists()


def test_output_must_be_in_approved_directory(tmp_path: Path) -> None:
    def service(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "audio/wav"}, content=make_wav())

    outside = ROOT / "tests" / "unapproved-local-tts.wav"
    with create_adapter(tmp_path, service) as adapter:
        with pytest.raises(LocalTTSError, match="approved"):
            adapter.synthesize_segment(text="x", output_path=outside)
    assert not outside.exists()


def test_segment_timing_reserves_lead_in_and_trailing_silence() -> None:
    cue = recorder.SrtCue(index=4, start_ms=1000, end_ms=5000, lines=("Words",))
    window = plan_segment_window(cue)
    assert window.speech_start_ms == 1100
    assert window.speech_end_ms == 4900
    assert window.max_duration == pytest.approx(3.8)
    with pytest.raises(LocalTTSError, match="lead-in"):
        plan_segment_window(cue, lead_in_ms=20)


def test_speed_is_bounded_and_increases_only_when_cue_needs_it(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    speeds = []

    def service(request: httpx.Request) -> httpx.Response:
        speed = __import__("json").loads(request.content)["speed"]
        speeds.append(speed)
        seconds = 1.9 * 0.95 / speed
        return httpx.Response(200, headers={"content-type": "audio/wav"}, content=make_wav(seconds))

    monkeypatch.setattr(local_tts, "_run_ffmpeg", lambda _ffmpeg, source, target: shutil.copyfile(source, target))
    cue = recorder.SrtCue(index=1, start_ms=0, end_ms=2000, lines=("A manageable line",))
    with create_adapter(tmp_path, service) as adapter:
        result = local_tts.synthesize_timeline(
            adapter=adapter, cues=[cue], total_duration_seconds=2,
            output_path=tmp_path / "speed.wav", manifest_path=tmp_path / "speed.json",
        )
    assert speeds[0] == 0.95 and len(speeds) == 2
    assert 0.90 <= speeds[-1] <= 1.05 and speeds[-1] > speeds[0]
    assert result["segments"][0]["speed"] == speeds[-1]


def test_speed_limit_failure_names_segment_and_never_exceeds_105(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    speeds = []

    def service(request: httpx.Request) -> httpx.Response:
        speeds.append(__import__("json").loads(request.content)["speed"])
        return httpx.Response(200, headers={"content-type": "audio/wav"}, content=make_wav(3.0))

    monkeypatch.setattr(local_tts, "_run_ffmpeg", lambda _ffmpeg, source, target: shutil.copyfile(source, target))
    cue = recorder.SrtCue(index=7, start_ms=0, end_ms=2000, lines=("Too long",))
    with create_adapter(tmp_path, service) as adapter:
        with pytest.raises(LocalTTSError, match="segment 7.*shorten its wording"):
            local_tts.synthesize_timeline(
                adapter=adapter, cues=[cue], total_duration_seconds=2,
                output_path=tmp_path / "too-long.wav", manifest_path=tmp_path / "too-long.json",
            )
    assert speeds and max(speeds) <= 1.05
    assert not (tmp_path / "too-long.wav").exists()
    assert not (tmp_path / "too-long.json").exists()


def _render_deterministic_timeline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    audio = make_wav(0.5, sample=800)

    def service(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "audio/wav"}, content=audio)

    monkeypatch.setattr(local_tts, "_run_ffmpeg", lambda _ffmpeg, source, target: shutil.copyfile(source, target))
    cue = recorder.SrtCue(index=1, start_ms=1000, end_ms=3000, lines=("Private narrated sentence",))
    with create_adapter(tmp_path, service) as adapter:
        manifest = local_tts.synthesize_timeline(
            adapter=adapter, cues=[cue], total_duration_seconds=3,
            output_path=tmp_path / "final.wav", manifest_path=tmp_path / "final.json",
        )
    return manifest


def test_timeline_has_silence_padding_and_deterministic_text_free_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    first_dir, second_dir = tmp_path / "first", tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    first = _render_deterministic_timeline(first_dir, monkeypatch)
    second = _render_deterministic_timeline(second_dir, monkeypatch)
    assert first == second
    serialized = (first_dir / "final.json").read_text(encoding="utf-8")
    assert "Private narrated sentence" not in serialized
    segment = first["segments"][0]
    assert segment["text_sha256"] == hashlib.sha256(b"Private narrated sentence").hexdigest()
    assert len(segment["sha256"]) == 64
    with wave.open(str(first_dir / "final.wav"), "rb") as output:
        assert output.getnframes() == 3 * 48_000
        pcm = output.readframes(output.getnframes())
    frame_size = 4
    assert set(pcm[: int(1.1 * 48_000) * frame_size]) == {0}
    assert any(pcm[int(1.1 * 48_000) * frame_size : int(1.6 * 48_000) * frame_size])
    assert set(pcm[int(1.6 * 48_000) * frame_size :]) == {0}


def _prepared_submission(tmp_path: Path) -> Path:
    submission = tmp_path / "submission"
    submission.mkdir()
    for name in (*hosted.ORIGINAL_VIDEO_NAMES, hosted.CANDIDATE_NAME):
        (submission / name).write_bytes(name.encode())
    (submission / "MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt").write_text(
        "1\n00:00:00,000 --> 00:00:05,000\nA short line.\n", encoding="utf-8"
    )
    return submission


@pytest.mark.parametrize(
    "output_name",
    [hosted.LOCAL_TTS_AUDIO_NAME, hosted.LOCAL_TTS_MANIFEST_NAME, hosted.LOCAL_TTS_CANDIDATE_NAME],
)
def test_local_narration_preflight_refuses_new_output_collisions_before_health(
    tmp_path: Path, output_name: str,
) -> None:
    submission = _prepared_submission(tmp_path)
    (submission / output_name).write_bytes(b"existing")
    with pytest.raises(ValueError, match="refusing overwrite"):
        hosted.narration_preflight(tmp_path, tts_url="http://127.0.0.1:1")


def test_local_narration_preflight_allows_existing_hosted_source_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepared_submission(tmp_path)

    class ReadyTTS:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def health_check(self):
            return {"status": "ok"}

        def discover_voices(self):
            return ["bf_emma"]

    monkeypatch.setattr(hosted, "LocalDockerTTS", ReadyTTS)
    result = hosted.narration_preflight(tmp_path, tts_url="http://127.0.0.1:1")
    assert result["candidate_collision_check"] == "PASS"
    assert hosted.CANDIDATE_NAME not in result["outputs"]
    assert result["outputs"] == [
        hosted.LOCAL_TTS_AUDIO_NAME,
        hosted.LOCAL_TTS_MANIFEST_NAME,
        hosted.LOCAL_TTS_CANDIDATE_NAME,
    ]


def test_original_video_hash_protection_detects_changes(tmp_path: Path) -> None:
    submission = _prepared_submission(tmp_path)
    before = hosted._protected_video_hashes(submission)
    (submission / hosted.CANDIDATE_NAME).write_bytes(b"changed")
    with pytest.raises(recorder.RecordingError, match="video changed"):
        hosted._verify_protected_video_hashes(submission, before)


def test_local_provider_fails_before_sapi_or_hosted_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    submission = tmp_path / "submission"
    submission.mkdir()
    (submission / "MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt").write_text("placeholder", encoding="utf-8")
    cue = recorder.SrtCue(index=1, start_ms=0, end_ms=5000, lines=("No fallback",))
    monkeypatch.setattr(recorder, "verify_required_tools", lambda: {"ffmpeg_bin": "ffmpeg"})
    monkeypatch.setattr(recorder, "parse_srt", lambda *_args, **_kwargs: [cue])
    monkeypatch.setattr(
        recorder,
        "synthesize_narration_wav_bytes",
        lambda *_args, **_kwargs: pytest.fail("System.Speech fallback was called"),
    )
    monkeypatch.setattr(recorder, "wait_for_health", lambda *_args: pytest.fail("Hosted endpoint was contacted"))

    class FailingLocalTTS:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        def health_check(self):
            raise LocalTTSError("mock local service missing")

    monkeypatch.setattr(hosted, "LocalDockerTTS", FailingLocalTTS)
    now = datetime.now(UTC)
    with pytest.raises(LocalTTSError, match="mock local service missing"):
        hosted.record_candidate(
            tmp_path,
            "https://demo.example.azurecontainerapps.io",
            now - timedelta(seconds=1),
            now + timedelta(minutes=2),
            hosted.CANDIDATE_NAME,
            allowed_host="demo.example.azurecontainerapps.io",
            tts_provider="local-docker",
            tts_url="http://127.0.0.1:8765",
        )


def test_adapter_does_not_log_narration_text(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    secret_text = "UNIQUE_PRIVATE_NARRATION_9f38"

    def service(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "audio/wav"}, content=make_wav())

    with create_adapter(tmp_path, service) as adapter:
        adapter.synthesize_segment(text=secret_text, output_path=tmp_path / "private.wav")
    assert secret_text not in caplog.text
