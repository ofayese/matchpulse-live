"""Validation helpers for the isolated, human-reviewable Kokoro V2 candidate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from matchpulse_conversational_tts import validate_thought_units
from matchpulse_local_tts import LocalTTSError

V2_OUTPUTS = {
    "audio": "matchpulse-hosted-narration-kokoro-bf-emma-conversational-v2.wav",
    "manifest": "matchpulse-hosted-narration-kokoro-bf-emma-conversational-v2.manifest.json",
    "video": "matchpulse-submission-hosted-kokoro-conversational-v2-candidate.mp4",
}
V2_SCRIPT = "MATCHPULSE_NARRATION_CONVERSATIONAL_V2.json"
WELCOME_PHRASE_VARIANTS = (
    "Welcome to MatchPulse Live.",
    "Welcome. This is MatchPulse Live.",
    "Welcome... to MatchPulse Live.",
    "Welcome to Match Pulse Live.",
    "Here’s MatchPulse Live.",
)
PRONUNCIATION_AUDIT_TERMS = (
    "MatchPulse",
    "Azure",
    "Azure Container Apps",
    "Northbridge City",
    "Harbor United",
    "synthetic",
    "evidence-grounded",
    "idempotent",
    "out of order",
    "analyst",
    "broadcaster",
    "deterministic",
    "fallback",
    "Foundry",
    "model calls",
    "multilingual",
    "recap",
    "welcome",
    "welcoming",
)
CHANGE_CLASSIFICATIONS = {
    "KEEP",
    "PRONUNCIATION_FIX",
    "PACING_FIX",
    "WORDING_AND_PACING_FIX",
}


def diagnostic_jobs() -> list[dict[str, str]]:
    """Return exact text inputs for isolated, contextual, and speech-only auditions."""
    jobs = [
        {"category": "welcome", "variant": f"phrase-{index}", "text": phrase}
        for index, phrase in enumerate(WELCOME_PHRASE_VARIANTS, start=1)
    ]
    for term in PRONUNCIATION_AUDIT_TERMS:
        slug = term.lower().replace(" ", "-")
        jobs.extend(
            (
                {"category": "term", "variant": f"{slug}-isolated", "text": f"{term}."},
                {
                    "category": "term",
                    "variant": f"{slug}-sentence-normal",
                    "text": f"The demo mentions {term} in its match report.",
                },
                {
                    "category": "term",
                    "variant": f"{slug}-sentence-speech-only",
                    "text": f"Please say {term} clearly.",
                },
            )
        )
    return jobs


def protected_media_hashes(
    submission: Path,
    *,
    exclude_paths: tuple[Path, ...] = (),
) -> dict[str, str]:
    """Hash existing media, manifests, and captions using submission-relative paths."""
    excluded = {path.resolve() for path in exclude_paths}
    paths = {
        path
        for pattern in ("*.mp4", "*.wav", "*.manifest.json", "*.srt")
        for path in submission.rglob(pattern)
        if path.resolve() not in excluded
    }
    return {
        path.relative_to(submission).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths, key=lambda item: item.relative_to(submission).as_posix())
    }


def validate_v2_script(script: dict[str, Any], cues: list[Any]) -> list[dict[str, Any]]:
    if script.get("schema_version") != 2 or script.get("model") != "kokoro-v1.0":
        raise LocalTTSError("V2 narration script has an unsupported schema or model")
    if script.get("voice") != "bf_emma" or not isinstance(script.get("units"), list):
        raise LocalTTSError("V2 narration requires bf_emma and a thought-unit list")
    units = script["units"]
    speeds = [float(unit.get("preferred_speed", 0)) for unit in units]
    if not speeds or any(not 0.91 <= speed <= 0.95 for speed in speeds):
        raise LocalTTSError("V2 speed must remain between 0.91 and 0.95")
    average_speed = sum(speeds) / len(speeds)
    if not 0.91 <= average_speed <= 0.95 or abs(average_speed - 0.93) > 0.01:
        raise LocalTTSError("V2 average narration speed must target 0.93")
    for unit in units:
        text = str(unit.get("revised_spoken_text", ""))
        if not text or text != text.strip() or "  " in text:
            raise LocalTTSError("V2 narration text must have normalized whitespace")
        if unit.get("change_classification") not in CHANGE_CLASSIFICATIONS:
            raise LocalTTSError("Every V2 thought unit needs an explicit change classification")
        segments = unit.get("spoken_segments")
        if not isinstance(segments, list) or not segments:
            raise LocalTTSError("Every V2 thought unit needs explicit, timed speech segments")
        segment_text = [str(segment.get("text", "")) for segment in segments]
        if any(not value or value != value.strip() or "  " in value for value in segment_text):
            raise LocalTTSError("V2 speech segments must have normalized whitespace")
        if " ".join(segment_text) != text:
            raise LocalTTSError("V2 speech segments must reconstruct the spoken text exactly")
    validated = validate_thought_units(units, cues, total_duration_seconds=115.0)
    if validated[-1]["_closing"] < 0.5:
        raise LocalTTSError("V2 closing silence must be at least 0.5 seconds")
    return validated


def validate_v2_manifest(manifest: dict[str, Any]) -> dict[str, float]:
    units = manifest.get("units")
    if not isinstance(units, list) or len(units) != 10:
        raise LocalTTSError("V2 manifest must contain all ten thought units")
    previous_end = 0.0
    for index, unit in enumerate(units):
        speech_start = float(unit["speech_start_seconds"])
        speech_end = float(unit["speech_end_seconds"])
        visual_end = float(unit["timeline_end_seconds"])
        if speech_start < previous_end or speech_end <= speech_start or speech_end > visual_end:
            raise LocalTTSError("V2 manifest contains overlapping or out-of-window speech")
        if speech_start < float(unit["timeline_start_seconds"]) + float(unit["opening_silence_seconds"]):
            raise LocalTTSError("V2 manifest starts speech before the reserved opening pause")
        if index + 1 < len(units):
            next_start = float(units[index + 1]["speech_start_seconds"])
            gap = next_start - speech_end
            if gap > 1.2:
                raise LocalTTSError(
                    f"V2 manifest has an inter-unit gap of {gap:.3f}s between units {index + 1} and {index + 2}"
                )
        previous_end = speech_end
    last = units[-1]
    closing_silence = float(last["timeline_end_seconds"]) - float(last["speech_end_seconds"])
    if float(last["speech_end_seconds"]) > 114.5 or closing_silence < 0.5:
        raise LocalTTSError("V2 closing speech misses the 114.5-second deadline or silence requirement")
    speeds = [float(unit["speed"]) for unit in units]
    average_speed = sum(speeds) / len(speeds)
    if any(not 0.91 <= speed <= 0.95 for speed in speeds) or abs(average_speed - 0.93) > 0.01:
        raise LocalTTSError("V2 manifest speed bounds or average are outside the approved range")
    if abs(float(manifest.get("average_speed", -1)) - average_speed) > 0.001:
        raise LocalTTSError("V2 manifest average speed does not match its thought units")
    return {
        "average_speed": average_speed,
        "first_speech_end_seconds": float(units[0]["speech_end_seconds"]),
        "final_speech_end_seconds": float(last["speech_end_seconds"]),
        "final_silence_seconds": closing_silence,
    }


def render_v2_candidate(
    repo_root: Path,
    *,
    tts_url: str,
    output_dir: Path,
) -> dict[str, Any]:
    """Render V2 from canonical archived inputs into a separate, collision-checked directory."""
    import record_matchpulse_demo as recorder
    import record_matchpulse_hosted_submission as hosted

    repo_root = Path(repo_root).resolve()
    submission = repo_root / "submission"
    source = submission / "archive" / "videos" / hosted.CANDIDATE_NAME
    script_path = submission / "final-support" / V2_SCRIPT
    captions_path = submission / "final-support" / "MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt"
    output_dir = Path(output_dir).resolve()
    if not output_dir.is_dir():
        raise LocalTTSError("The V2 output directory must already exist")
    try:
        output_dir.relative_to(submission)
    except ValueError:
        pass
    else:
        raise LocalTTSError("The V2 output directory must be outside the submission tree")
    outputs = {key: output_dir / name for key, name in V2_OUTPUTS.items()}
    collisions = [path.name for path in outputs.values() if path.exists()]
    if collisions:
        raise LocalTTSError("V2 output already exists; refusing overwrite: " + ", ".join(collisions))
    if not source.is_file() or not script_path.is_file() or not captions_path.is_file():
        raise LocalTTSError("The archived hosted source video and final-support V2 inputs are required")
    cues = recorder.parse_srt(captions_path, max_duration_seconds=115.0)
    script = json.loads(script_path.read_text(encoding="utf-8"))
    validate_v2_script(script, cues)
    protected_videos = tuple(sorted(submission.rglob("*.mp4")))
    protected_before = hosted._protected_video_hashes(
        submission,
        video_paths=protected_videos,
    )
    protected_media_before = protected_media_hashes(
        submission,
        exclude_paths=tuple(outputs.values()),
    )
    result = hosted.render_conversational_narration(
        repo_root,
        tts_url=tts_url,
        engine="kokoro",
        voice="bf_emma",
        source_video_path=source,
        captions_path=captions_path,
        script_path=script_path,
        audio_output_path=outputs["audio"],
        manifest_output_path=outputs["manifest"],
        video_output_path=outputs["video"],
        protected_video_paths=protected_videos,
    )
    manifest = json.loads(outputs["manifest"].read_text(encoding="utf-8"))
    metrics = validate_v2_manifest(manifest)
    script_hash = hashlib.sha256(script_path.read_bytes()).hexdigest()
    protected_after = hosted._protected_video_hashes(
        submission,
        video_paths=protected_videos,
    )
    protected_media_after = protected_media_hashes(submission)
    if protected_after != protected_before or protected_media_after != protected_media_before:
        raise recorder.RecordingError("A protected video changed during V2 rendering")
    if not result.get("existing_videos_unchanged") or result.get("azure_contacted") is not False:
        raise recorder.RecordingError("V2 render did not satisfy local-only media safety checks")
    return {
        **result,
        "manifest_metrics": metrics,
        "script_sha256": script_hash,
        "protected_video_hashes": protected_after,
        "protected_media_hashes": protected_media_after,
        "outputs": {key: path.name for key, path in outputs.items()},
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Render the local-only MatchPulse Kokoro V2 candidate")
    parser.add_argument("--tts-url", required=True, help="Loopback HTTP URL for the local Docker Kokoro service")
    parser.add_argument("--output-dir", required=True, type=Path, help="Existing directory for new, non-overwriting outputs")
    args = parser.parse_args()
    import json as json_module

    try:
        result = render_v2_candidate(
            Path(__file__).resolve().parents[1],
            tts_url=args.tts_url,
            output_dir=args.output_dir,
        )
    except (LocalTTSError, ValueError) as exc:
        parser.error(str(exc))
    print(json_module.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
