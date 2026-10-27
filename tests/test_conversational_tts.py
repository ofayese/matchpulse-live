from __future__ import annotations

import hashlib
import importlib
import io
import json
import shutil
import sys
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
conversational = importlib.import_module("matchpulse_conversational_tts")
local_tts = importlib.import_module("matchpulse_local_tts")
hosted = importlib.import_module("record_matchpulse_hosted_submission")
recorder = importlib.import_module("record_matchpulse_demo")


def _cue(index: int, start: int, end: int, text: str) -> SimpleNamespace:
    return SimpleNamespace(index=index, start_ms=start, end_ms=end, lines=(text,))


def _unit(number: int, cue: SimpleNamespace, *, speed: float = 0.95, connected: bool = False) -> dict:
    return {
        "unit": number,
        "visual_start_seconds": cue.start_ms / 1000,
        "visual_end_seconds": cue.end_ms / 1000,
        "available_duration_seconds": (cue.end_ms - cue.start_ms) / 1000,
        "cue_ids": [cue.index],
        "original_captions": [{"cue_id": cue.index, "text": " ".join(cue.lines)}],
        "revised_spoken_text": f"Spoken unit {number}.",
        "delivery_label": "explanatory",
        "preferred_speed": speed,
        "opening_pause_seconds": 0.2,
        "closing_pause_seconds": 0.2,
        "connected_to_next": connected,
        "factual_changes": [],
    }


def _wav(seconds: float = 0.5) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(48_000)
        frame = (1000).to_bytes(2, "little", signed=True) * 2
        output.writeframes(frame * round(seconds * 48_000))
    return buffer.getvalue()


class FakeAdapter:
    approved_output_dirs: tuple[Path, ...]

    def __init__(self, directory: Path, *, seconds: float = 0.5) -> None:
        self.approved_output_dirs = (directory,)
        self.seconds = seconds
        self.calls = 0

    def synthesize_segment(self, *, text: str, output_path: Path, voice: str, speed: float, language: str):
        self.calls += 1
        data = _wav(self.seconds)
        output_path.write_bytes(data)
        return local_tts.SegmentResult(
            path=output_path,
            duration=self.seconds,
            sha256=hashlib.sha256(data).hexdigest(),
            sample_rate=48_000,
            channels=2,
            voice=voice,
            speed=speed,
            attempts=1,
        )


def _render(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, seconds: float = 0.5) -> dict:
    cue = _cue(1, 0, 2000, "Caption one")
    adapter = FakeAdapter(tmp_path, seconds=seconds)
    monkeypatch.setattr(conversational, "_clean_unit", lambda _ffmpeg, source, target: shutil.copyfile(source, target))
    monkeypatch.setattr(
        conversational,
        "_two_pass_loudnorm",
        lambda _ffmpeg, source, target: (shutil.copyfile(source, target), {
            "integrated_lufs": -16.0,
            "true_peak_dbtp": -2.0,
            "lra_lu": 8.0,
            "normalization_type_linear": True,
        })[1],
    )
    manifest = conversational.synthesize_conversational_timeline(
        adapter=adapter,
        cues=[cue],
        units=[_unit(1, cue)],
        total_duration_seconds=2.0,
        output_path=tmp_path / "speech.wav",
        manifest_path=tmp_path / "speech.json",
    )
    return manifest


def test_thought_unit_grouping_and_caption_mapping() -> None:
    cues = [_cue(1, 0, 1000, "First caption"), _cue(2, 1000, 2000, "Second caption")]
    unit = _unit(1, cues[0])
    unit.update({
        "visual_end_seconds": 2.0,
        "available_duration_seconds": 2.0,
        "cue_ids": [1, 2],
        "original_captions": [
            {"cue_id": 1, "text": "First caption"},
            {"cue_id": 2, "text": "Second caption"},
        ],
        "connected_to_next": False,
    })
    result = conversational.validate_thought_units([unit], cues, total_duration_seconds=2.0)
    assert result[0]["_cue_ids"] == [1, 2]


def test_cue_mapping_must_match_srt_verbatim() -> None:
    cue = _cue(1, 0, 2000, "Actual caption")
    unit = _unit(1, cue)
    unit["original_captions"][0]["text"] = "Changed caption"
    with pytest.raises(local_tts.LocalTTSError, match="unchanged SRT"):
        conversational.validate_thought_units([unit], [cue], total_duration_seconds=2.0)


def test_connected_speeds_and_global_speed_bounds() -> None:
    cues = [_cue(1, 0, 1000, "One"), _cue(2, 1000, 2000, "Two")]
    units = [_unit(1, cues[0], speed=0.95, connected=True), _unit(2, cues[1], speed=0.99)]
    with pytest.raises(local_tts.LocalTTSError, match="differ in speed"):
        conversational.validate_thought_units(units, cues, total_duration_seconds=2.0)
    units[0]["preferred_speed"] = 1.02
    with pytest.raises(local_tts.LocalTTSError, match="speed must be between"):
        conversational.validate_thought_units(units, cues, total_duration_seconds=2.0)


def test_pause_and_hard_boundary_safety() -> None:
    cue = _cue(1, 0, 2000, "One")
    unit = _unit(1, cue)
    unit["opening_pause_seconds"] = 0.09
    with pytest.raises(local_tts.LocalTTSError, match="pauses"):
        conversational.validate_thought_units([unit], [cue], total_duration_seconds=2.0)
    unit = _unit(1, cue)
    unit["visual_start_seconds"] = 0.1
    with pytest.raises(local_tts.LocalTTSError, match="visual boundary"):
        conversational.validate_thought_units([unit], [cue], total_duration_seconds=2.0)


def test_pronunciation_substitutions_are_synthesis_only() -> None:
    script_text = "MatchPulse is hosted on Azure."
    spoken = conversational.synthesis_text(script_text, [{"from": "MatchPulse", "to": "Match Pulse"}])
    assert spoken == "Match Pulse is hosted on Azure."
    assert script_text == "MatchPulse is hosted on Azure."
    with pytest.raises(local_tts.LocalTTSError, match="does not match"):
        conversational.synthesis_text(script_text, [{"from": "Missing", "to": "Words"}])


def test_timeline_duration_and_manifest_are_deterministic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    first_dir, second_dir = tmp_path / "first", tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    first = _render(first_dir, monkeypatch)
    second = _render(second_dir, monkeypatch)
    assert first == second
    assert first["thought_unit_count"] == 1
    assert first["audio_sha256"] == hashlib.sha256((first_dir / "speech.wav").read_bytes()).hexdigest()
    with wave.open(str(first_dir / "speech.wav"), "rb") as rendered:
        assert rendered.getnframes() == 2 * 48_000
        assert rendered.getframerate() == 48_000
    assert json.loads((first_dir / "speech.json").read_text(encoding="utf-8")) == first


def test_fits_narration_window_and_refuses_output_collisions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cue = _cue(1, 0, 1000, "Caption")
    adapter = FakeAdapter(tmp_path, seconds=0.8)
    monkeypatch.setattr(conversational, "_clean_unit", lambda _ffmpeg, source, target: shutil.copyfile(source, target))
    with pytest.raises(local_tts.LocalTTSError, match="does not fit its visual window"):
        conversational.synthesize_conversational_timeline(
            adapter=adapter, cues=[cue], units=[_unit(1, cue)], total_duration_seconds=1.0,
            output_path=tmp_path / "overrun.wav", manifest_path=tmp_path / "overrun.json",
        )
    assert not (tmp_path / "overrun.wav").exists()
    assert adapter.calls == 1
    (tmp_path / "collision.wav").write_bytes(b"protected")
    with pytest.raises(local_tts.LocalTTSError, match="already exists"):
        conversational.synthesize_conversational_timeline(
            adapter=adapter, cues=[cue], units=[_unit(1, cue)], total_duration_seconds=1.0,
            output_path=tmp_path / "collision.wav", manifest_path=tmp_path / "collision.json",
        )
    assert adapter.calls == 1


def test_conversational_local_renderer_never_falls_back_to_browser_tts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    submission = tmp_path / "submission"
    submission.mkdir()
    for name in (*hosted.ORIGINAL_VIDEO_NAMES, hosted.CANDIDATE_NAME):
        (submission / name).write_bytes(name.encode())
    (submission / "MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt").write_text(
        "1\n00:00:00,000 --> 00:00:05,000\nA short line.\n", encoding="utf-8"
    )
    cue = _cue(1, 0, 5000, "A short line.")
    script = {
        "style_label": conversational.STYLE_LABEL,
        "pronunciation_substitutions": [],
        "units": [_unit(1, cue)],
    }
    (submission / hosted.CONVERSATIONAL_SCRIPT_NAME).write_text(json.dumps(script), encoding="utf-8")
    monkeypatch.setattr(recorder, "verify_required_tools", lambda: {"ffmpeg_bin": "ffmpeg", "ffprobe_bin": "ffprobe"})
    monkeypatch.setattr(
        recorder, "synthesize_narration_wav_bytes",
        lambda *_args, **_kwargs: pytest.fail("browser/System.Speech fallback was called"),
    )

    class FailingLocalTTS:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def health_check(self):
            raise local_tts.LocalTTSError("local service unavailable")

    monkeypatch.setattr(hosted, "LocalDockerTTS", FailingLocalTTS)
    with pytest.raises(local_tts.LocalTTSError, match="local service unavailable"):
        hosted.render_conversational_narration(
            tmp_path, tts_url="http://127.0.0.1:18880", engine="kokoro", voice="bf_emma"
        )
    assert not (submission / hosted.CONVERSATIONAL_TTS_AUDIO_NAME).exists()
    assert not (submission / hosted.CONVERSATIONAL_TTS_CANDIDATE_NAME).exists()
