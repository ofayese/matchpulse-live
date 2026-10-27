"""Render the MatchPulse conversational narration with a stock ElevenLabs voice.

Stages: ``audition`` (pronunciation gate), ``units`` (one request per thought
unit, at most three attempts each) and ``assemble`` (timeline, mastering, WAV,
manifest, stream-copy remux and validation). The API key is read only through
the existing adapter from the process environment or the ignored ``.env`` and
is never written anywhere.
"""

from __future__ import annotations

import argparse
import array
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matchpulse_conversational_tts as conv  # noqa: E402
import matchpulse_elevenlabs_tts as eleven  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "submission" / "final-support" / "MATCHPULSE_NARRATION_CONVERSATIONAL_V2.json"
SCRIPT_SHA256 = "9930d8b267fc881f48d43537d1b3a999e003e9024e27c04b316a9fc3c7d3c3e2"
VISUAL_SOURCE = ROOT / "submission" / "archive" / "videos" / "matchpulse-submission-hosted-candidate.mp4"
VISUAL_SHA256 = "5a6faaf2bef5603f973e6774568064eb21d91dd9dd60e1f7f87f4b86da939387"
KOKORO_MP4 = ROOT / "submission" / "matchpulse-submission-hosted-kokoro-conversational-v2-candidate.mp4"
KOKORO_SHA256 = "b89c016d8d0c790ae42b3a761d6ec7f709cfa988159649c4cf0e07eb8906dcbf"
VIDEO_STREAM_MD5 = "c85bef1de55944edebd4f4d003c70b59"
OUT_WAV = ROOT / "submission" / "matchpulse-hosted-narration-elevenlabs-lily-v1.wav"
OUT_MANIFEST = ROOT / "submission" / "matchpulse-hosted-narration-elevenlabs-lily-v1.manifest.json"
OUT_MP4 = ROOT / "submission" / "matchpulse-submission-hosted-elevenlabs-lily-v1-candidate.mp4"
VOICE_ID = "pFZP5JQG7iQjIQuC4Bku"
VOICE_NAME = "Lily"
VARIANT = "MEASURED_CONVERSATIONAL"
WORK_DIR = Path(tempfile.gettempdir()) / "matchpulse-elevenlabs-auditions"
STATE_PATH = WORK_DIR / "lily-v1-state.json"
CLEAN_DIR = WORK_DIR / "lily-v1-clean"
PRONUNCIATION_AUDITION = (
    "Here\u2019s MatchPulse Live. Azure Container Apps supports the synthetic match between "
    "Northbridge City and Harbor United. Analysts and broadcasters receive evidence-grounded views "
    "with deterministic fallback while Foundry is switched off."
)
MAX_UNIT_ATTEMPTS = 3
TOTAL_SECONDS = 115.0
SAMPLE_RATE = conv.SAMPLE_RATE
CHANNELS = conv.CHANNELS
MAX_SPEED = 1.12
CLEARANCE = 0.1


class RenderError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def require_identity(path: Path, expected: str) -> None:
    if not path.is_file() or sha256_file(path) != expected:
        raise RenderError(f"Protected input identity mismatch: {path.name}")


def load_script() -> dict[str, Any]:
    require_identity(SCRIPT_PATH, SCRIPT_SHA256)
    data = json.loads(SCRIPT_PATH.read_text(encoding="utf-8"))
    if len(data["units"]) != 10:
        raise RenderError("The narration script must contain ten thought units")
    return data


def unit_window(unit: dict[str, Any]) -> tuple[float, float]:
    """Earliest speech start and latest permitted speech end, in seconds."""
    start = unit["visual_start_seconds"] + unit["opening_pause_seconds"]
    end = unit["visual_end_seconds"] - CLEARANCE
    if unit["unit"] == 10:
        end = min(end, 114.5)
    return start, end


def load_state() -> dict[str, Any]:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"units": {}, "audition": None}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def apply_aliases(text: str, aliases: dict[str, str]) -> str:
    for source, replacement in aliases.items():
        text = text.replace(source, replacement)
    return text


def wav_pcm(path: Path) -> bytes:
    with wave.open(str(path), "rb") as handle:
        if (handle.getframerate(), handle.getnchannels(), handle.getsampwidth()) != (SAMPLE_RATE, CHANNELS, 2):
            raise RenderError("Unexpected cleaned unit format")
        return handle.readframes(handle.getnframes())


def open_session() -> tuple[Any, Any, dict[str, Any], dict[str, Any]]:
    """Return client, preflight, eligible voices and verified Lily settings."""
    eleven._load_local_env()
    client = eleven.create_client()
    preflight = eleven.verify_model_and_subscription(client, voice_count=1)
    if preflight.tier != "starter" or preflight.status != "active":
        raise RenderError("An active Starter subscription is required")
    voices = {v.voice_id: v for v in eleven.discover_voices(client, starter_verified=True)}
    voice = voices.get(VOICE_ID)
    if voice is None or voice.category != "premade" or preflight.model_id not in voice.compatible_model_ids:
        raise RenderError("Lily is not an eligible stock voice for the stable model")
    settings = eleven._variant_settings(VARIANT, preflight)
    return client, preflight, voices, settings


def generate(client: Any, preflight: Any, voices: dict[str, Any], text: str, settings: dict[str, Any], name: str) -> dict[str, Any]:
    return eleven.synthesize_audio(
        client,
        text=text,
        voice_id=VOICE_ID,
        model_id=preflight.model_id,
        settings=settings,
        output_path=WORK_DIR / name,
        eligible_voices=voices,
        available_stable_models={preflight.model_id},
    )


def stage_audition(aliases: dict[str, str]) -> None:
    load_script()
    client, preflight, voices, settings = open_session()
    state = load_state()
    index = len(state.get("audition_runs", [])) + 1
    text = apply_aliases(PRONUNCIATION_AUDITION, aliases)
    result = generate(client, preflight, voices, text, settings, f"lily-v1-pronunciation-gate-{index}.mp3")
    state.setdefault("audition_runs", []).append(
        {
            "file": result["path"].name,
            "sha256": result["sha256"],
            "duration_seconds": result["duration_seconds"],
            "characters": result["requested_characters"],
            "aliases": aliases,
            "settings": settings,
            "generation_utc": result["generation_utc"],
        }
    )
    save_state(state)
    print(json.dumps(state["audition_runs"][-1], indent=2))


def stage_units(only: list[int] | None, aliases: dict[str, str], overrides: dict[str, str]) -> None:
    script = load_script()
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    CLEAN_DIR.mkdir(exist_ok=True)
    client, preflight, voices, base_settings = open_session()
    state = load_state()
    for unit in script["units"]:
        number = unit["unit"]
        if only and number not in only:
            continue
        record = state["units"].setdefault(str(number), {"attempts": []})
        if record.get("accepted"):
            continue
        start, end = unit_window(unit)
        budget = end - start
        spoken = overrides.get(str(number), unit["revised_spoken_text"])
        text = apply_aliases(spoken, aliases)
        speed = base_settings["speed"]
        while len(record["attempts"]) < MAX_UNIT_ATTEMPTS:
            attempt = len(record["attempts"]) + 1
            settings = dict(base_settings, speed=round(speed, 3))
            result = generate(client, preflight, voices, text, settings, f"lily-v1-unit-{number:02d}-a{attempt}.mp3")
            clean = CLEAN_DIR / f"unit-{number:02d}-a{attempt}.wav"
            conv._clean_unit(ffmpeg, result["path"], clean)
            pcm = wav_pcm(clean)
            speech = len(pcm) / (SAMPLE_RATE * CHANNELS * 2)
            fits = speech <= budget
            record["attempts"].append(
                {
                    "attempt": attempt,
                    "raw_file": result["path"].name,
                    "raw_sha256": result["sha256"],
                    "raw_duration_seconds": round(result["duration_seconds"], 3),
                    "cleaned_file": clean.name,
                    "cleaned_speech_seconds": round(speech, 3),
                    "budget_seconds": round(budget, 3),
                    "fits": fits,
                    "settings": settings,
                    "characters": result["requested_characters"],
                    "api_attempts": result["api_attempts"],
                    "generation_utc": result["generation_utc"],
                    "text": text,
                    "text_overridden": str(number) in overrides,
                    "aliases": aliases,
                }
            )
            print(f"unit {number} attempt {attempt}: speech {speech:.2f}s budget {budget:.2f}s speed {settings['speed']}")
            if fits:
                record["accepted"] = attempt
                break
            speed = min(MAX_SPEED, round(speed * (speech / budget) * 1.02, 3))
            save_state(state)
        save_state(state)
        if not record.get("accepted"):
            print(f"unit {number} did not fit within {MAX_UNIT_ATTEMPTS} attempts")


def _ffmpeg_json_probe(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


def clip_count(pcm: bytes) -> int:
    samples = array.array("h")
    samples.frombytes(pcm)
    return sum(1 for s in samples if s >= 32767 or s <= -32768)


def silent_gaps(ffmpeg: str, path: Path, minimum: float) -> list[tuple[float, float]]:
    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-nostats", "-nostdin", "-i", str(path), "-af", f"silencedetect=n=-45dB:d={minimum}", "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )
    starts, gaps = [], []
    for line in result.stderr.splitlines():
        if "silence_start:" in line:
            starts.append(float(line.split("silence_start:")[1].strip()))
        elif "silence_end:" in line and starts:
            gaps.append((starts.pop(0), float(line.split("silence_end:")[1].split("|")[0].strip())))
    for start in starts:
        gaps.append((start, TOTAL_SECONDS))
    return gaps


def stream_md5(ffmpeg: str, path: Path) -> str:
    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-nostats", "-nostdin", "-i", str(path), "-map", "0:v:0", "-c", "copy", "-f", "md5", "-"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip().split("=")[-1]


def stage_assemble(settings_note: str) -> None:
    script = load_script()
    ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    for path in (OUT_WAV, OUT_MANIFEST, OUT_MP4):
        if path.exists():
            raise RenderError(f"Destination collision: {path.name}")
    require_identity(VISUAL_SOURCE, VISUAL_SHA256)
    require_identity(KOKORO_MP4, KOKORO_SHA256)
    state = load_state()
    total_frames = round(TOTAL_SECONDS * SAMPLE_RATE)
    buffer = array.array("h", bytes(total_frames * CHANNELS * 2))
    unit_rows: list[dict[str, Any]] = []
    previous_end = 0.0
    for unit in script["units"]:
        number = unit["unit"]
        record = state["units"].get(str(number), {})
        accepted = record.get("accepted")
        if not accepted:
            raise RenderError(f"Unit {number} has no accepted attempt")
        attempt = record["attempts"][accepted - 1]
        pcm = conv._fade_pcm(wav_pcm(CLEAN_DIR / attempt["cleaned_file"]))
        start, limit = unit_window(unit)
        speech = len(pcm) / (SAMPLE_RATE * CHANNELS * 2)
        if start < previous_end or start + speech > limit + 1e-6:
            raise RenderError(f"Unit {number} overlaps or exceeds its window")
        offset = round(start * SAMPLE_RATE) * CHANNELS
        samples = array.array("h")
        samples.frombytes(pcm)
        buffer[offset:offset + len(samples)] = samples
        previous_end = start + speech
        unit_rows.append(
            {
                "unit": number,
                "visual_start_seconds": unit["visual_start_seconds"],
                "visual_end_seconds": unit["visual_end_seconds"],
                "available_duration_seconds": unit["available_duration_seconds"],
                "spoken_text_sha256": sha256_text(unit["revised_spoken_text"]),
                "synthesis_text_sha256": sha256_text(attempt["text"]),
                "text_overridden": attempt["text_overridden"],
                "voice_name": VOICE_NAME,
                "voice_id": VOICE_ID,
                "variant": VARIANT,
                "voice_settings": attempt["settings"],
                "generation_utc": attempt["generation_utc"],
                "raw_duration_seconds": attempt["raw_duration_seconds"],
                "target_duration_seconds": attempt["budget_seconds"],
                "speech_start_seconds": round(start, 3),
                "speech_end_seconds": round(start + speech, 3),
                "opening_silence_seconds": unit["opening_pause_seconds"],
                "closing_silence_seconds": round(unit["visual_end_seconds"] - (start + speech), 3),
                "pronunciation_aliases": attempt["aliases"],
                "attempt_number": accepted,
                "attempts_used": len(record["attempts"]),
                "raw_audio_sha256": attempt["raw_sha256"],
                "character_usage": sum(a["characters"] for a in record["attempts"]),
            }
        )
    stage = WORK_DIR / "lily-v1-timeline.wav"
    mastered = WORK_DIR / "lily-v1-mastered.wav"
    for path in (stage, mastered):
        path.unlink(missing_ok=True)
    with wave.open(str(stage), "wb") as handle:
        handle.setnchannels(CHANNELS)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(buffer.tobytes())
    mastering = conv._two_pass_loudnorm(ffmpeg, stage, mastered)
    final_pcm = wav_pcm(mastered)
    duration = len(final_pcm) / (SAMPLE_RATE * CHANNELS * 2)
    clipped = clip_count(final_pcm)
    loud = conv.measure_loudness(ffmpeg, mastered)
    narration_ok = (
        abs(duration - TOTAL_SECONDS) <= 0.01
        and -16.5 <= loud["integrated_lufs"] <= -15.5
        and loud["true_peak_dbtp"] <= -1.5
        and clipped == 0
    )
    if not narration_ok:
        raise RenderError(f"Narration validation failed: duration={duration} loudness={loud} clipped={clipped}")
    conv._exclusive_copy(mastered, OUT_WAV)
    wav_hash = sha256_file(OUT_WAV)
    video_probe = _ffmpeg_json_probe(VISUAL_SOURCE)

    subprocess.run(
        [
            ffmpeg, "-hide_banner", "-nostats", "-nostdin", "-n",
            "-i", str(VISUAL_SOURCE), "-i", str(OUT_WAV),
            "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", "-t", str(TOTAL_SECONDS), str(OUT_MP4),
        ],
        capture_output=True, check=True,
    )
    probe = _ffmpeg_json_probe(OUT_MP4)
    v = next(s for s in probe["streams"] if s["codec_type"] == "video")
    a = next(s for s in probe["streams"] if s["codec_type"] == "audio")
    decode = subprocess.run(
        [ffmpeg, "-v", "error", "-nostdin", "-i", str(OUT_MP4), "-f", "null", "-"], capture_output=True, text=True
    )
    video_duration = float(probe["format"]["duration"])
    md5 = stream_md5(ffmpeg, OUT_MP4)
    video_loud = conv.measure_loudness(ffmpeg, OUT_MP4)
    internal_gaps = [
        gap for gap in silent_gaps(ffmpeg, OUT_WAV, 1.2)
        if any(r["speech_start_seconds"] <= gap[0] and gap[1] <= r["speech_end_seconds"] for r in unit_rows)
    ]
    num, den = v["avg_frame_rate"].split("/")
    checks = {
        "container_mp4": "mp4" in probe["format"]["format_name"],
        "video_h264": v["codec_name"] == "h264",
        "resolution_1920x1080": (v["width"], v["height"]) == (1920, 1080),
        "frame_rate_30": abs(int(num) / int(den) - 30) < 0.05,
        "audio_aac_stereo_48k": a["codec_name"] == "aac" and a["channels"] == 2 and int(a["sample_rate"]) == 48000,
        "duration_within_100ms": abs(video_duration - TOTAL_SECONDS) <= 0.1,
        "full_decode_clean": decode.returncode == 0 and not decode.stderr.strip(),
        "video_stream_copied_md5": md5 == VIDEO_STREAM_MD5,
        "video_loudness_in_range": -16.5 <= video_loud["integrated_lufs"] <= -15.5,
        "video_true_peak_ok": video_loud["true_peak_dbtp"] <= -1.5,
        "ten_units": len(unit_rows) == 10,
        "no_internal_silence_over_1_2s": not internal_gaps,
        "closing_speech_before_visual_end": unit_rows[-1]["speech_end_seconds"] <= 114.5,
        "final_silence_at_least_500ms": TOTAL_SECONDS - unit_rows[-1]["speech_end_seconds"] >= 0.5,
    }
    manifest = {
        "schema_version": 1,
        "tts_provider": "ELEVENLABS",
        "elevenlabs_plan": "STARTER",
        "elevenlabs_voice_name": VOICE_NAME,
        "elevenlabs_voice_id": VOICE_ID,
        "elevenlabs_variant": VARIANT,
        "elevenlabs_stock_voice": "YES",
        "elevenlabs_voice_cloning_used": "NO",
        "elevenlabs_beta_service_used": "NO",
        "elevenlabs_generation_during_paid_subscription": "YES",
        "third_party_rights_declaration": "PENDING_HUMAN_APPROVAL",
        "kokoro_voice_rights_conclusion": "RIGHTS_UNRESOLVED",
        "model_id": eleven.MODEL_ID,
        "script_sha256": SCRIPT_SHA256,
        "visual_source_sha256": VISUAL_SHA256,
        "settings_note": settings_note,
        "pronunciation_audition_runs": state.get("audition_runs", []),
        "units": unit_rows,
        "total_character_usage": sum(r["character_usage"] for r in unit_rows),
        "narration": {
            "file": OUT_WAV.name,
            "sha256": wav_hash,
            "duration_seconds": round(duration, 4),
            "integrated_lufs": loud["integrated_lufs"],
            "true_peak_dbtp": loud["true_peak_dbtp"],
            "loudness_range_lu": loud["lra_lu"],
            "clipped_samples": clipped,
            "mastering": mastering,
        },
        "candidate_video": {
            "file": OUT_MP4.name,
            "sha256": sha256_file(OUT_MP4),
            "duration_seconds": round(video_duration, 4),
            "video_stream_md5": md5,
            "integrated_lufs": video_loud["integrated_lufs"],
            "true_peak_dbtp": video_loud["true_peak_dbtp"],
            "source_video_codec": video_probe["streams"][0].get("codec_name"),
            "checks": checks,
        },
        "human_review": "NOT_COMPLETED",
    }
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checks": checks, "narration": manifest["narration"], "video": manifest["candidate_video"]}, indent=2))
    if not all(checks.values()):
        raise RenderError("Technical validation failed; inspect the checks above")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["audition", "units", "assemble"])
    parser.add_argument("--units", type=int, nargs="*")
    parser.add_argument("--aliases", type=Path, help="JSON object of synthesis-only pronunciation aliases")
    parser.add_argument("--overrides", type=Path, help="JSON object mapping unit number to revised spoken text")
    parser.add_argument("--settings-note", default="Baseline MEASURED_CONVERSATIONAL settings; speed raised only as recorded per attempt.")
    args = parser.parse_args()
    aliases = json.loads(args.aliases.read_text(encoding="utf-8")) if args.aliases else {}
    overrides = json.loads(args.overrides.read_text(encoding="utf-8")) if args.overrides else {}
    try:
        WORK_DIR.mkdir(exist_ok=True)
        if args.stage == "audition":
            stage_audition(aliases)
        elif args.stage == "units":
            stage_units(args.units, aliases, overrides)
        else:
            stage_assemble(args.settings_note)
    except (RenderError, eleven.ElevenLabsError, conv.LocalTTSError, subprocess.CalledProcessError) as exc:
        print(f"Render stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
