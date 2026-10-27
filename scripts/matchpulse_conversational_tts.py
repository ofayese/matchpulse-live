from __future__ import annotations

import array
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Any

from matchpulse_local_tts import (
    CHANNELS,
    SAMPLE_RATE,
    SAMPLE_WIDTH,
    LocalDockerTTS,
    LocalTTSError,
    _approved_path,
    _probe_wav,
)

DELIVERY_LABELS = {
    "welcoming", "explanatory", "emphasis", "reassuring", "analytical", "transition", "closing"
}
CHANGE_CLASSIFICATIONS = {
    "KEEP", "PRONUNCIATION_FIX", "PACING_FIX", "WORDING_AND_PACING_FIX"
}
MIN_SPEED = 0.92
MAX_SPEED = 1.01
STYLE_LABEL = "PROVISIONAL_CONVERSATIONAL_STYLE"


def validate_thought_units(
    units: list[dict[str, Any]], cues: list[Any], *, total_duration_seconds: float = 115.0
) -> list[dict[str, Any]]:
    if not units or not cues or total_duration_seconds <= 0:
        raise LocalTTSError("Conversational narration requires thought units, caption cues, and a positive duration")
    cue_map = {int(cue.index): cue for cue in cues}
    seen: list[int] = []
    validated: list[dict[str, Any]] = []
    previous_end = 0.0
    previous_speed: float | None = None
    previous_connected = False
    for position, raw in enumerate(units):
        unit = dict(raw)
        try:
            number = int(unit["unit"])
            cue_ids = [int(value) for value in unit["cue_ids"]]
            start = float(unit["visual_start_seconds"])
            end = float(unit["visual_end_seconds"])
            available = float(unit["available_duration_seconds"])
            speed = float(unit["preferred_speed"])
            opening = float(unit["opening_pause_seconds"])
            closing = float(unit["closing_pause_seconds"])
            text = str(unit["revised_spoken_text"])
            delivery = str(unit["delivery_label"])
            connected = bool(unit["connected_to_next"])
        except (KeyError, TypeError, ValueError) as exc:
            raise LocalTTSError(f"Conversational thought unit {position + 1} has invalid fields") from exc
        if number != position + 1 or not cue_ids or cue_ids != list(range(cue_ids[0], cue_ids[-1] + 1)):
            raise LocalTTSError("Thought units must be numbered and map contiguous caption cues")
        if any(cue_id not in cue_map for cue_id in cue_ids) or seen and cue_ids[0] != seen[-1] + 1:
            raise LocalTTSError("Thought-unit cue mapping has missing, repeated, or out-of-order captions")
        mapped = [cue_map[cue_id] for cue_id in cue_ids]
        expected_start = int(mapped[0].start_ms) / 1000.0
        expected_end = int(mapped[-1].end_ms) / 1000.0
        if abs(start - expected_start) > 0.001 or abs(end - expected_end) > 0.001:
            raise LocalTTSError(f"Thought unit {number} crosses or misstates a visual boundary")
        if abs(available - (end - start)) > 0.001 or end > total_duration_seconds or start < previous_end:
            raise LocalTTSError(f"Thought unit {number} has an invalid available duration or timeline order")
        if not MIN_SPEED <= speed <= MAX_SPEED:
            raise LocalTTSError(f"Thought unit {number} speed must be between {MIN_SPEED:.2f} and {MAX_SPEED:.2f}")
        if previous_connected and previous_speed is not None and abs(speed - previous_speed) > 0.0300001:
            raise LocalTTSError("Connected thought units may not differ in speed by more than 0.03")
        if not 0.10 <= opening <= 0.45 or not 0.10 <= closing <= 0.50:
            raise LocalTTSError("Opening and closing pauses must each be between 0.10 and 0.45 seconds")
        if opening + closing >= available or not text.strip() or delivery not in DELIVERY_LABELS:
            raise LocalTTSError(f"Thought unit {number} has no safe speech window or invalid spoken text/delivery")
        captions = unit.get("original_captions")
        expected_captions = [
            {"cue_id": cue_id, "text": " ".join(getattr(cue_map[cue_id], "lines", ())) }
            for cue_id in cue_ids
        ]
        if captions != expected_captions:
            raise LocalTTSError(f"Thought unit {number} original captions do not match the unchanged SRT")
        if unit.get("factual_changes", []) != []:
            raise LocalTTSError("Conversational narration may not introduce factual changes")
        classification = unit.get("change_classification", "KEEP")
        if classification not in CHANGE_CLASSIFICATIONS:
            raise LocalTTSError(f"Thought unit {number} has an invalid change classification")
        raw_segments = unit.get("spoken_segments")
        segments: list[dict[str, Any]] = []
        if raw_segments is not None:
            if not isinstance(raw_segments, list) or not raw_segments:
                raise LocalTTSError(f"Thought unit {number} has invalid spoken segments")
            reconstructed: list[str] = []
            for index, raw_segment in enumerate(raw_segments):
                if not isinstance(raw_segment, dict):
                    raise LocalTTSError(f"Thought unit {number} has an invalid spoken segment")
                segment_text = str(raw_segment.get("text", ""))
                pause = float(raw_segment.get("pause_after_seconds", 0.0))
                pause_kind = str(raw_segment.get("pause_kind", ""))
                if not segment_text.strip():
                    raise LocalTTSError(f"Thought unit {number} has an empty spoken segment")
                if index == len(raw_segments) - 1:
                    if pause != 0 or pause_kind:
                        raise LocalTTSError("The final spoken segment may not add an internal pause")
                elif pause_kind == "clause":
                    if not 0.08 <= pause <= 0.12:
                        raise LocalTTSError("Clause pauses must be between 80 and 120 milliseconds")
                elif pause_kind == "sentence":
                    if not 0.18 <= pause <= 0.30:
                        raise LocalTTSError("Sentence pauses must be between 180 and 300 milliseconds")
                elif pause_kind == "transition":
                    if not 0.35 <= pause <= 0.50:
                        raise LocalTTSError("Major transition pauses must be between 350 and 500 milliseconds")
                else:
                    raise LocalTTSError("Every internal spoken-segment pause needs a supported pause kind")
                reconstructed.append(segment_text)
                segments.append({
                    "text": segment_text,
                    "pause_after_seconds": pause,
                    "pause_kind": pause_kind,
                })
            if " ".join(reconstructed) != text:
                raise LocalTTSError(f"Thought unit {number} spoken segments do not match the script text")
        else:
            segments = [{"text": text, "pause_after_seconds": 0.0, "pause_kind": ""}]
        unit["_start"] = start
        unit["_end"] = end
        unit["_speed"] = speed
        unit["_opening"] = opening
        unit["_closing"] = closing
        unit["_text"] = text
        unit["_cue_ids"] = cue_ids
        unit["_segments"] = segments
        unit["_change_classification"] = classification
        validated.append(unit)
        seen.extend(cue_ids)
        previous_end = end
        previous_speed = speed
        previous_connected = connected
    if seen != sorted(cue_map) or validated[-1]["connected_to_next"]:
        raise LocalTTSError("Thought units must cover all captions exactly once and terminate their connected sequence")
    for previous, current in zip(validated, validated[1:], strict=False):
        gap = previous["_closing"] + current["_opening"]
        if gap <= 0 or gap > 1.0:
            raise LocalTTSError("Adjacent thought units require a nonzero pause no longer than one second")
    return validated


def synthesis_text(text: str, substitutions: list[dict[str, str]]) -> str:
    result = text
    for entry in substitutions:
        source, replacement = entry.get("from", ""), entry.get("to", "")
        if not source or not replacement or source not in result:
            raise LocalTTSError("Pronunciation substitution is invalid or does not match the spoken script")
        result = result.replace(source, replacement)
    return result


def _fade_pcm(pcm: bytes, *, sample_rate: int = SAMPLE_RATE, fade_seconds: float = 0.005) -> bytes:
    samples = array.array("h")
    samples.frombytes(pcm)
    fade_frames = min(round(sample_rate * fade_seconds), len(samples) // CHANNELS)
    fade_samples = fade_frames * CHANNELS
    if fade_samples < 2:
        return pcm
    for index in range(fade_samples):
        samples[index] = round(samples[index] * index / fade_samples)
        samples[-fade_samples + index] = round(samples[-fade_samples + index] * (fade_samples - index - 1) / fade_samples)
    return samples.tobytes()


def _json_stats(stderr: str) -> dict[str, str]:
    matches = re.findall(r"\{\s*\"input_i\".*?\n\}", stderr, flags=re.DOTALL)
    if not matches:
        raise LocalTTSError("FFmpeg did not return loudness measurement data")
    try:
        return json.loads(matches[-1])
    except json.JSONDecodeError as exc:
        raise LocalTTSError("FFmpeg returned invalid loudness measurement data") from exc


def measure_loudness(ffmpeg_bin: str, source: Path, *, target_i: float = -16.0, target_tp: float = -1.5, target_lra: float = 9.0) -> dict[str, float]:
    command = [
        ffmpeg_bin, "-hide_banner", "-nostats", "-nostdin", "-i", str(source),
        "-af", f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:print_format=json",
        "-f", "null", "-",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise LocalTTSError("FFmpeg could not measure conversational narration loudness") from exc
    stats = _json_stats(result.stderr)
    keys = {"integrated_lufs": "input_i", "true_peak_dbtp": "input_tp", "lra_lu": "input_lra"}
    return {name: float(stats[key]) for name, key in keys.items()}


def _two_pass_loudnorm(ffmpeg_bin: str, source: Path, destination: Path) -> dict[str, float]:
    target_i, target_tp, target_lra = -16.0, -2.0, 9.0
    analysis_cmd = [
        ffmpeg_bin, "-hide_banner", "-nostats", "-nostdin", "-i", str(source),
        "-af", f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:print_format=json",
        "-f", "null", "-",
    ]
    try:
        analysis = subprocess.run(analysis_cmd, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise LocalTTSError("FFmpeg loudness analysis failed") from exc
    measured = _json_stats(analysis.stderr)
    loudnorm = (
        f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:"
        f"measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:"
        f"measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:"
        f"offset={measured['target_offset']}:linear=true:print_format=json"
    )
    render_cmd = [
        ffmpeg_bin, "-hide_banner", "-nostats", "-nostdin", "-i", str(source), "-af", loudnorm,
        "-ar", str(SAMPLE_RATE), "-ac", str(CHANNELS), "-c:a", "pcm_s16le", "-f", "wav", "-n", str(destination),
    ]
    try:
        rendered = subprocess.run(render_cmd, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise LocalTTSError("FFmpeg two-pass conversational loudness render failed") from exc
    result = _json_stats(rendered.stderr)
    return {
        "integrated_lufs": float(result["output_i"]),
        "true_peak_dbtp": float(result["output_tp"]),
        "lra_lu": float(result["output_lra"]),
        "normalization_type_linear": result.get("normalization_type") == "linear",
    }


def _clean_unit(ffmpeg_bin: str, source: Path, destination: Path) -> None:
    command = [
        ffmpeg_bin, "-hide_banner", "-loglevel", "error", "-nostats", "-nostdin", "-i", str(source),
        "-af", (
            "highpass=f=70,lowpass=f=15000,"
            "silenceremove=start_periods=1:start_duration=0.03:start_threshold=-55dB:start_silence=0.02,"
            "areverse,"
            "silenceremove=start_periods=1:start_duration=0.03:start_threshold=-55dB:start_silence=0.02,"
            "areverse"
        ),
        "-ar", str(SAMPLE_RATE), "-ac", str(CHANNELS),
        "-c:a", "pcm_s16le", "-f", "wav", "-n", str(destination),
    ]
    try:
        subprocess.run(command, capture_output=True, check=True)
    except subprocess.CalledProcessError as exc:
        details = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else str(exc.stderr or "")
        raise LocalTTSError("FFmpeg could not clean a conversational narration unit: " + details[-400:]) from exc
    except OSError as exc:
        raise LocalTTSError("FFmpeg could not start while cleaning a conversational narration unit") from exc


def _exclusive_copy(source: Path, destination: Path) -> None:
    with destination.open("xb") as target:
        try:
            with source.open("rb") as origin:
                shutil.copyfileobj(origin, target)
        except Exception:
            target.close()
            destination.unlink(missing_ok=True)
            raise


def synthesize_conversational_timeline(
    *,
    adapter: LocalDockerTTS,
    cues: list[Any],
    units: list[dict[str, Any]],
    total_duration_seconds: float,
    output_path: Path,
    manifest_path: Path,
    ffmpeg_bin: str = "ffmpeg",
    voice: str = "bf_emma",
    substitutions: list[dict[str, str]] | None = None,
    style_label: str = STYLE_LABEL,
    generation_attempt: int = 1,
) -> dict[str, Any]:
    if generation_attempt < 1:
        raise LocalTTSError("Conversational render generation must be positive")
    if voice != "bf_emma":
        raise LocalTTSError("Conversational MatchPulse narration requires the bf_emma voice")
    validated = validate_thought_units(units, cues, total_duration_seconds=total_duration_seconds)
    allowed = adapter.approved_output_dirs
    output = _approved_path(Path(output_path), allowed)
    manifest_output = _approved_path(Path(manifest_path), allowed)
    if output.exists() or manifest_output.exists():
        raise LocalTTSError("Conversational narration output or manifest already exists; refusing to overwrite")
    substitutions = substitutions or []
    total_frames = round(total_duration_seconds * SAMPLE_RATE)
    timeline = bytearray(total_frames * CHANNELS * 2)
    unit_entries: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="mp-conversational-tts-") as work_dir:
        work = Path(work_dir)
        occupied_until = -1
        for unit in validated:
            speech_start = unit["_start"] + unit["_opening"]
            start_frame = round(speech_start * SAMPLE_RATE)
            end_frame_limit = round((unit["_end"] - unit["_closing"]) * SAMPLE_RATE)
            source_text = unit["_text"]
            spoken = synthesis_text(source_text, substitutions)
            unit_pcm = bytearray()
            segment_entries: list[dict[str, Any]] = []
            segment_offset_frames = 0
            for segment_index, segment in enumerate(unit["_segments"]):
                spoken_segment = synthesis_text(segment["text"], substitutions)
                raw_path = work / f"unit-{unit['unit']}-segment-{segment_index + 1}-raw.wav"
                try:
                    result = adapter.synthesize_segment(
                        text=spoken_segment,
                        output_path=raw_path,
                        voice=voice,
                        speed=unit["_speed"],
                        language="b",
                    )
                except LocalTTSError as exc:
                    raise LocalTTSError(f"Thought unit {unit['unit']} synthesis request failed") from exc
                clean_path = work / f"unit-{unit['unit']}-segment-{segment_index + 1}-clean.wav"
                try:
                    _clean_unit(ffmpeg_bin, raw_path, clean_path)
                except LocalTTSError as exc:
                    raise LocalTTSError(f"Thought unit {unit['unit']}: {exc}") from exc
                segment_frames, _, _, segment_pcm = _probe_wav(clean_path)
                segment_pcm = _fade_pcm(segment_pcm)
                segment_start = segment_offset_frames
                unit_pcm.extend(segment_pcm)
                segment_offset_frames += segment_frames
                if segment["pause_after_seconds"]:
                    pause_frames = round(segment["pause_after_seconds"] * SAMPLE_RATE)
                    unit_pcm.extend(b"\x00" * (pause_frames * CHANNELS * SAMPLE_WIDTH))
                    segment_offset_frames += pause_frames
                segment_entries.append({
                    "text_sha256": hashlib.sha256(segment["text"].encode("utf-8")).hexdigest(),
                    "synthesis_text_sha256": hashlib.sha256(spoken_segment.encode("utf-8")).hexdigest(),
                    "speech_start_offset_seconds": round(segment_start / SAMPLE_RATE, 6),
                    "speech_end_offset_seconds": round((segment_start + segment_frames) / SAMPLE_RATE, 6),
                    "pause_after_seconds": segment["pause_after_seconds"],
                    "pause_kind": segment["pause_kind"],
                    "raw_duration_seconds": round(result.duration, 6),
                    "api_request_attempts": result.attempts,
                })
            duration = segment_offset_frames / SAMPLE_RATE
            frames = segment_offset_frames
            pcm = bytes(unit_pcm)
            if start_frame < occupied_until:
                raise LocalTTSError("Conversational units overlap on the timeline")
            if start_frame + frames > end_frame_limit:
                raise LocalTTSError(
                    f"Thought unit {unit['unit']} does not fit its visual window at speed {unit['_speed']:.2f}; shorten its wording"
                )
            samples = array.array("h")
            samples.frombytes(pcm)
            if max(samples, default=0) >= 32767 or min(samples, default=0) <= -32768:
                raise LocalTTSError(f"Conversational unit {unit['unit']} clipped before mastering")
            byte_start = start_frame * CHANNELS * 2
            byte_end = byte_start + len(pcm)
            timeline[byte_start:byte_end] = pcm
            speech_end = speech_start + duration
            occupied_until = start_frame + frames
            unit_entries.append({
                "unit": int(unit["unit"]),
                "cue_ids": unit["_cue_ids"],
                "delivery_label": unit["delivery_label"],
                "change_classification": unit["_change_classification"],
                "text_sha256": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
                "synthesis_text_sha256": hashlib.sha256(spoken.encode("utf-8")).hexdigest(),
                "voice": voice,
                "speed": unit["_speed"],
                "raw_duration_seconds": round(
                    sum(segment["raw_duration_seconds"] for segment in segment_entries), 6
                ),
                "clean_duration_seconds": round(duration, 6),
                "opening_silence_seconds": unit["_opening"],
                "closing_silence_seconds": round(unit["_end"] - speech_end, 6),
                "timeline_start_seconds": unit["_start"],
                "timeline_end_seconds": unit["_end"],
                "speech_start_seconds": round(speech_start, 6),
                "speech_end_seconds": round(speech_end, 6),
                "audio_sha256": hashlib.sha256(pcm).hexdigest(),
                "synthesis_request_attempts": sum(
                    segment["api_request_attempts"] for segment in segment_entries
                ),
                "api_request_attempts": sum(segment["api_request_attempts"] for segment in segment_entries),
                "spoken_segments": segment_entries,
                "connected_to_next": bool(unit["connected_to_next"]),
            })
        assembled = work / "timeline.wav"
        with wave.open(str(assembled), "wb") as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(2)
            wav_file.setframerate(SAMPLE_RATE)
            wav_file.writeframes(timeline)
        mastered = work / "mastered.wav"
        measurements = _two_pass_loudnorm(ffmpeg_bin, assembled, mastered)
        with wave.open(str(mastered), "rb") as final_wav:
            frames = final_wav.getnframes()
            pcm = final_wav.readframes(frames)
            sample_rate, channels, width = final_wav.getframerate(), final_wav.getnchannels(), final_wav.getsampwidth()
        if sample_rate != SAMPLE_RATE or channels != CHANNELS or width != 2 or abs(frames / SAMPLE_RATE - total_duration_seconds) > 0.01:
            raise LocalTTSError("Final conversational WAV has an invalid format or duration")
        samples = array.array("h")
        samples.frombytes(pcm)
        if max(samples, default=0) >= 32767 or min(samples, default=0) <= -32768:
            raise LocalTTSError("Final conversational WAV clips")
        audio_hash = hashlib.sha256(mastered.read_bytes()).hexdigest()
        manifest = {
            "format": "wav",
            "sample_rate": SAMPLE_RATE,
            "channels": CHANNELS,
            "duration_seconds": round(frames / SAMPLE_RATE, 6),
            "model": "kokoro-v1.0",
            "voice": voice,
            "speed_range": [min(entry["speed"] for entry in unit_entries), max(entry["speed"] for entry in unit_entries)],
            "average_speed": round(sum(entry["speed"] for entry in unit_entries) / len(unit_entries), 3),
            "thought_unit_count": len(unit_entries),
            "style_label": style_label,
            "spoken_text_sha256": hashlib.sha256("\n".join(unit["_text"] for unit in validated).encode("utf-8")).hexdigest(),
            "pronunciation_substitutions": substitutions,
            "render_generation_attempt": generation_attempt,
            "regeneration_attempts": generation_attempt - 1,
            "audio_sha256": audio_hash,
            "loudness": measurements,
            "units": unit_entries,
        }
        manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
        output_created = False
        manifest_created = False
        try:
            _exclusive_copy(mastered, output)
            output_created = True
            with manifest_output.open("xb") as manifest_file:
                manifest_created = True
                manifest_file.write(manifest_bytes)
        except Exception:
            if output_created:
                output.unlink(missing_ok=True)
            if manifest_created:
                manifest_output.unlink(missing_ok=True)
            raise
    return manifest
