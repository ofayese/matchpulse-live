from __future__ import annotations

import importlib
import json
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
v2 = importlib.import_module("matchpulse_kokoro_v2")
conversational = importlib.import_module("matchpulse_conversational_tts")
local_tts = importlib.import_module("matchpulse_local_tts")


def _cue(index: int, start: int, end: int, text: str) -> SimpleNamespace:
    return SimpleNamespace(index=index, start_ms=start, end_ms=end, lines=(text,))


def _unit(cue: SimpleNamespace, *, speed: float = 0.93) -> dict:
    return {
        "unit": cue.index,
        "visual_start_seconds": cue.start_ms / 1000,
        "visual_end_seconds": cue.end_ms / 1000,
        "available_duration_seconds": (cue.end_ms - cue.start_ms) / 1000,
        "cue_ids": [cue.index],
        "original_captions": [{"cue_id": cue.index, "text": " ".join(cue.lines)}],
        "revised_spoken_text": "A short sentence.",
        "spoken_segments": [
            {"text": "A short sentence.", "pause_after_seconds": 0, "pause_kind": ""}
        ],
        "change_classification": "PACING_FIX",
        "delivery_label": "explanatory",
        "preferred_speed": speed,
        "opening_pause_seconds": 0.22,
        "closing_pause_seconds": 0.5 if cue.index == 1 else 0.2,
        "connected_to_next": False,
        "factual_changes": [],
    }


def _local_v2_input(filename: str) -> Path | None:
    candidates = (
        ROOT / "submission" / filename,
        ROOT / "submission" / "final-support" / filename,
    )
    for p in candidates:
        if p.exists():
            return p
    return None


def _require_local_v2_input(filename: str) -> Path:
    path = _local_v2_input(filename)
    if path is None:
        pytest.skip(f"Local-only submission input is not included in a clean clone: {filename}")
    return path


def _load_v2_script() -> dict:
    path = _require_local_v2_input(v2.V2_SCRIPT)
    return json.loads(path.read_text(encoding="utf-8"))


def _get_hosted_captions_path() -> Path:
    return _require_local_v2_input("MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt")


def test_v2_welcome_repair_and_exact_diagnostic_variants() -> None:
    script = _load_v2_script()
    opening = script["units"][0]["revised_spoken_text"]
    assert opening.startswith("Here’s MatchPulse Live.")
    assert "Welcome in." not in opening
    assert v2.WELCOME_PHRASE_VARIANTS == (
        "Welcome to MatchPulse Live.",
        "Welcome. This is MatchPulse Live.",
        "Welcome... to MatchPulse Live.",
        "Welcome to Match Pulse Live.",
        "Here’s MatchPulse Live.",
    )
    jobs = v2.diagnostic_jobs()
    assert all(any(job["text"] == phrase for job in jobs) for phrase in v2.WELCOME_PHRASE_VARIANTS)
    for term in v2.PRONUNCIATION_AUDIT_TERMS:
        slug = term.lower().replace(" ", "-")
        assert {f"{slug}-isolated", f"{slug}-sentence-normal", f"{slug}-sentence-speech-only"} <= {
            job["variant"] for job in jobs
        }


def test_v2_script_keeps_captions_whitespace_and_speed_invariants() -> None:
    recorder = importlib.import_module("record_matchpulse_demo")
    script = _load_v2_script()
    cues = recorder.parse_srt(
        _get_hosted_captions_path(),
        max_duration_seconds=115,
    )
    units = v2.validate_v2_script(script, cues)
    assert len(units) == 10
    assert sum(unit["_speed"] for unit in units) / len(units) == pytest.approx(0.93)
    assert units[-1]["_closing"] >= 0.5
    assert len({cue_id for unit in units for cue_id in unit["_cue_ids"]}) == len(cues)
    for unit in script["units"]:
        assert " ".join(segment["text"] for segment in unit["spoken_segments"]) == unit["revised_spoken_text"]
        assert all(segment["text"] == segment["text"].strip() for segment in unit["spoken_segments"])


@pytest.mark.parametrize(
    ("pause_kind", "pause", "message"),
    [
        ("clause", 0.07, "80 and 120"),
        ("sentence", 0.31, "180 and 300"),
        ("transition", 0.51, "350 and 500"),
    ],
)
def test_internal_pause_lengths_are_enforced(
    pause_kind: str, pause: float, message: str,
) -> None:
    cue = _cue(1, 0, 4000, "Clause one, clause two. Sentence two.")
    unit = _unit(cue)
    unit["revised_spoken_text"] = cue.lines[0]
    unit["spoken_segments"] = [
        {"text": "Clause one,", "pause_after_seconds": pause, "pause_kind": pause_kind},
        {"text": "clause two.", "pause_after_seconds": 0.22, "pause_kind": "sentence"},
        {"text": "Sentence two.", "pause_after_seconds": 0, "pause_kind": ""},
    ]
    with pytest.raises(local_tts.LocalTTSError, match=message):
        conversational.validate_thought_units([unit], [cue], total_duration_seconds=4)


def test_v2_manifest_closing_deadline_and_inter_unit_gap() -> None:
    starts = [0, 18, 28, 38, 54, 63, 80, 87, 99, 108]
    ends = [18, 28, 38, 54, 63, 80, 87, 99, 108, 115]
    units = [
        {
            "speed": 0.93,
            "timeline_start_seconds": start,
            "opening_silence_seconds": 0.22,
            "speech_start_seconds": start + 0.22,
            "speech_end_seconds": end - 0.5,
            "timeline_end_seconds": end,
        }
        for start, end in zip(starts, ends, strict=True)
    ]
    manifest = {"average_speed": 0.93, "units": units}
    metrics = v2.validate_v2_manifest(manifest)
    assert metrics["final_silence_seconds"] == 0.5
    units[-1]["speech_end_seconds"] = 114.6
    with pytest.raises(local_tts.LocalTTSError, match="114.5-second deadline"):
        v2.validate_v2_manifest(manifest)


def test_manifest_rejects_long_inter_unit_silence() -> None:
    starts = [0, 18, 28, 38, 54, 63, 80, 87, 99, 108]
    ends = [18, 28, 38, 54, 63, 80, 87, 99, 108, 115]
    units = []
    for index, (start, end) in enumerate(zip(starts, ends, strict=True)):
        speech_start = start + 0.22
        units.append({
            "speed": 0.93,
            "timeline_start_seconds": start,
            "opening_silence_seconds": 0.22,
            "speech_start_seconds": speech_start,
            "speech_end_seconds": start + (2 if index == 0 else end - start - 0.5),
            "timeline_end_seconds": end,
        })
    units[-1]["speech_end_seconds"] = 114.4
    with pytest.raises(local_tts.LocalTTSError, match="inter-unit gap"):
        v2.validate_v2_manifest({"average_speed": 0.93, "units": units})


def test_manifest_rejects_overlapping_units() -> None:
    starts = [0, 18, 28, 38, 54, 63, 80, 87, 99, 108]
    ends = [18, 28, 38, 54, 63, 80, 87, 99, 108, 115]
    units = []
    for start, end in zip(starts, ends, strict=True):
        units.append({
            "speed": 0.93,
            "timeline_start_seconds": start,
            "opening_silence_seconds": 0.22,
            "speech_start_seconds": start + 0.22,
            "speech_end_seconds": end - 0.5,
            "timeline_end_seconds": end,
        })
    units[1]["speech_start_seconds"] = units[0]["speech_end_seconds"] - 0.1
    with pytest.raises(local_tts.LocalTTSError, match="overlapping"):
        v2.validate_v2_manifest({"average_speed": 0.93, "units": units})


def test_fades_are_applied_only_at_segment_joins() -> None:
    import array

    source = array.array("h", [1000] * (480 * 2)).tobytes()
    faded = array.array("h")
    faded.frombytes(conversational._fade_pcm(source))
    assert faded[0] == 0
    assert faded[-1] == 0
    assert max(faded) > 900


def test_segment_cleanup_trims_edges_without_stopping_at_internal_pauses(monkeypatch: pytest.MonkeyPatch) -> None:
    commands = []
    monkeypatch.setattr(conversational.subprocess, "run", lambda command, **_kwargs: commands.append(command))
    conversational._clean_unit("ffmpeg", Path("input.wav"), Path("output.wav"))
    filters = commands[0][commands[0].index("-af") + 1]
    assert filters.count("areverse") == 2
    assert "stop_periods=1" not in filters
    assert "start_periods=1" in filters


def test_protected_video_hash_check_detects_mutation(tmp_path: Path) -> None:
    hosted = importlib.import_module("record_matchpulse_hosted_submission")
    for name in (*hosted.ORIGINAL_VIDEO_NAMES, hosted.CANDIDATE_NAME):
        (tmp_path / name).write_bytes(name.encode())
    before = hosted._protected_video_hashes(tmp_path)
    assert all(len(value) == 64 for value in before.values())
    with pytest.raises(importlib.import_module("record_matchpulse_demo").RecordingError):
        hosted._verify_protected_video_hashes(tmp_path, {**before, hosted.CANDIDATE_NAME: "0" * 64})


def test_all_preexisting_media_and_captions_are_protected(tmp_path: Path) -> None:
    final_support = tmp_path / "final-support"
    final_support.mkdir()
    (tmp_path / "existing.mp4").write_bytes(b"video")
    (final_support / "existing.wav").write_bytes(b"audio")
    (final_support / "existing.manifest.json").write_bytes(b"manifest")
    (final_support / "MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt").write_bytes(b"captions")
    output_dir = tmp_path / "render-output"
    output_dir.mkdir()
    (output_dir / v2.V2_OUTPUTS["audio"]).write_bytes(b"new V2 output")
    protected = v2.protected_media_hashes(
        tmp_path,
        exclude_paths=(output_dir / v2.V2_OUTPUTS["audio"],),
    )
    assert set(protected) == {
        "existing.mp4",
        "final-support/existing.wav",
        "final-support/existing.manifest.json",
        "final-support/MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt",
    }


def test_v2_renderer_refuses_any_output_collision(tmp_path: Path) -> None:
    output_dir = tmp_path / "render-output"
    output_dir.mkdir()
    target = output_dir / v2.V2_OUTPUTS["audio"]
    target.write_bytes(b"protected")
    with pytest.raises(local_tts.LocalTTSError, match="refusing overwrite") as exc:
        v2.render_v2_candidate(
            tmp_path,
            tts_url="http://127.0.0.1:18880",
            output_dir=output_dir,
        )
    assert str(tmp_path) not in str(exc.value)
    assert target.read_bytes() == b"protected"


def test_v2_renderer_rejects_output_directory_inside_submission(tmp_path: Path) -> None:
    submission_output = tmp_path / "submission" / "render-output"
    submission_output.mkdir(parents=True)
    with pytest.raises(local_tts.LocalTTSError, match="outside the submission tree"):
        v2.render_v2_candidate(
            tmp_path,
            tts_url="http://127.0.0.1:18880",
            output_dir=submission_output,
        )


def test_v2_renderer_uses_archived_inputs_and_separate_output_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path
    submission = repo_root / "submission"
    source = submission / "archive" / "videos" / "matchpulse-submission-hosted-candidate.mp4"
    final_support = submission / "final-support"
    output_dir = repo_root / "render-output"
    source.parent.mkdir(parents=True)
    final_support.mkdir()
    output_dir.mkdir()
    source.write_bytes(b"source-video")

    filenames = (
        v2.V2_SCRIPT,
        "MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt",
        "matchpulse-hosted-narration-kokoro-bf-emma-conversational-v2.manifest.json",
    )
    paths = [_local_v2_input(filename) for filename in filenames]
    missing = [filename for filename, path in zip(filenames, paths, strict=True) if path is None]
    if missing:
        pytest.skip(f"Local-only V2 inputs are not included in a clean clone: {', '.join(missing)}")
    for path in paths:
        assert path is not None
        shutil.copy2(path, final_support / path.name)

    expected_manifest = final_support / "matchpulse-hosted-narration-kokoro-bf-emma-conversational-v2.manifest.json"
    hosted = importlib.import_module("record_matchpulse_hosted_submission")

    def fake_render(root: Path, **kwargs: Path | str) -> dict:
        assert root == repo_root
        assert kwargs["source_video_path"] == source
        assert kwargs["captions_path"] == final_support / "MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt"
        assert kwargs["script_path"] == final_support / v2.V2_SCRIPT
        assert kwargs["protected_video_paths"] == (source,)
        kwargs["audio_output_path"].write_bytes(b"rendered-audio")
        shutil.copy2(expected_manifest, kwargs["manifest_output_path"])
        kwargs["video_output_path"].write_bytes(b"rendered-video")
        return {"existing_videos_unchanged": True, "azure_contacted": False}

    monkeypatch.setattr(hosted, "render_conversational_narration", fake_render)
    result = v2.render_v2_candidate(
        repo_root,
        tts_url="http://127.0.0.1:18880",
        output_dir=output_dir,
    )

    assert result["existing_videos_unchanged"] is True
    assert result["protected_video_hashes"]["archive/videos/matchpulse-submission-hosted-candidate.mp4"]
    assert result["outputs"] == v2.V2_OUTPUTS
    assert (output_dir / v2.V2_OUTPUTS["audio"]).read_bytes() == b"rendered-audio"
    assert (output_dir / v2.V2_OUTPUTS["video"]).read_bytes() == b"rendered-video"
