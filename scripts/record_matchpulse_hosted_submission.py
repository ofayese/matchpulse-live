#!/usr/bin/env python3
"""Record one hosted MatchPulse submission candidate within an approved window."""

from __future__ import annotations

import argparse
import asyncio
import base64
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx
import record_matchpulse_demo as recorder
from matchpulse_conversational_tts import (
    STYLE_LABEL,
    synthesize_conversational_timeline,
)
from matchpulse_local_tts import (
    LocalDockerTTS,
    LocalTTSError,
    cue_text,
    estimated_cue_duration,
    plan_segment_window,
    synthesize_timeline,
)
from PIL import Image, ImageDraw

WINDOW_LIMIT_SECONDS = 60 * 60
VIDEO_DURATION_SECONDS = 115.0
CANDIDATE_NAME = "matchpulse-submission-hosted-candidate.mp4"
LOCAL_TTS_AUDIO_NAME = "matchpulse-hosted-narration-kokoro-bf-emma.wav"
LOCAL_TTS_MANIFEST_NAME = "matchpulse-hosted-narration-kokoro-bf-emma.manifest.json"
LOCAL_TTS_CANDIDATE_NAME = "matchpulse-submission-hosted-kokoro-candidate.mp4"
CONVERSATIONAL_TTS_AUDIO_NAME = "matchpulse-hosted-narration-kokoro-bf-emma-conversational.wav"
CONVERSATIONAL_TTS_MANIFEST_NAME = "matchpulse-hosted-narration-kokoro-bf-emma-conversational.manifest.json"
CONVERSATIONAL_TTS_CANDIDATE_NAME = "matchpulse-submission-hosted-kokoro-conversational-candidate.mp4"
CONVERSATIONAL_SCRIPT_NAME = "MATCHPULSE_NARRATION_CONVERSATIONAL.json"
ORIGINAL_VIDEO_NAMES = (
    "matchpulse-submission-demo.mp4",
    "matchpulse-submission-demo-captioned.mp4",
    "matchpulse-technical-demo.mp4",
    "matchpulse-technical-demo-captioned.mp4",
)
LOCAL_GUARD = "if ((scheme === 'http' || scheme === 'ws') && (host === '127.0.0.1' || host === 'localhost')) {"
HOSTED_GUARD = "if ((scheme === 'https' || scheme === 'wss') && parsed.host.toLowerCase() === cfg.allowed_authority) {"
BODY_TEXT_LINE = "      const bodyText = await page.locator('body').innerText();"
LOCAL_FALLBACK_TEXT = "foundryEl.textContent = 'Foundry: disabled (local synthetic mode) · Guard fallback verified: malformed-json & ReadTimeout -> deterministic output';"
HOSTED_FALLBACK_TEXT = "foundryEl.textContent = 'Foundry: disabled (hosted synthetic mode) · Guard fallback verified: malformed-json & ReadTimeout -> deterministic output';"
PROFILE_INJECT_CALL = "    await injectProfilesIntoSelect();\n"
LOCAL_PROFILE_SEQUENCE = """    const profileSequence = [
            { profile: 'analyst-en', locale: '', snapKey: 'profile_analyst_en' },
            { profile: 'broadcaster-en', locale: '', snapKey: 'profile_broadcaster_en' },
            { profile: 'broadcaster-es', locale: 'es', snapKey: 'profile_broadcaster_es' },
            { profile: 'fan-fr', locale: 'fr', snapKey: 'profile_fan_fr' }
        ];"""
HOSTED_PROFILE_SEQUENCE = """    const profileSequence = [
            { profile: 'analyst-en', locale: '', snapKey: 'profile_analyst_en' },
            { profile: 'broadcaster-es', locale: 'es', snapKey: 'profile_broadcaster_es' },
            { profile: 'fan-fr', locale: 'fr', snapKey: 'profile_fan_fr' }
        ];"""
PROFILE_SEQUENCE_RE = re.compile(r"(?ms)^ {4}const profileSequence = \[\n.*?^ {4}\];")
PROFILE_INJECT_FUNCTION_RE = re.compile(r"(?ms)^    async function injectProfilesIntoSelect\(\) \{\n.*?^    \}")
HOSTED_PROFILE_SEQUENCE_TEXT = (
    "    const profileSequence = [\n"
    "      { profile: 'analyst-en', locale: '', snapKey: 'profile_analyst_en' },\n"
    "      { profile: 'broadcaster-es', locale: 'es', snapKey: 'profile_broadcaster_es' },\n"
    "      { profile: 'fan-fr', locale: 'fr', snapKey: 'profile_fan_fr' }\n"
    "    ];"
)
SAFE_BODY_TEXT_LINE = (
    BODY_TEXT_LINE
    + """
      if (/(?:tenant|subscription)[^\\n]{0,60}[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/i.test(bodyText) ||
          /(?:InstrumentationKey|AccountKey|SharedAccessKey)\\s*=\\s*[^;\\s]+/i.test(bodyText) ||
          /Bearer\\s+[A-Za-z0-9._-]{16,}/i.test(bodyText) ||
          /[A-Za-z]:\\\\Users\\\\|\\/Users\\//.test(bodyText)) {
        throw new Error(`Sensitive text detected on page at stage ${stage}`);
      }
"""
)


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return parsed.astimezone(UTC)


def validate_url(value: str, allowed_host: str) -> tuple[str, str]:
    parsed = urlsplit(value)
    host = (parsed.hostname or "").lower()
    expected_host = allowed_host.strip().lower().rstrip(".")
    if (
        not re.fullmatch(
            r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+azurecontainerapps\.io",
            expected_host,
        )
        or host != expected_host
        or parsed.scheme != "https"
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.port not in (None, 443)
    ):
        raise ValueError(
            "URL must be HTTPS and match the explicitly allowed Azure Container Apps host"
        )
    return f"https://{host}", host


def existing_video_hashes(submission_dir: Path, *, exclude_names: set[str] | None = None) -> dict[str, str]:
    excluded = exclude_names or set()
    return {
        path.name: recorder.sha256_file(path)
        for path in sorted(submission_dir.glob("*.mp4"))
        if path.name not in excluded
    }


def hosted_capture_source() -> str:
    source = recorder.NODE_PLAYWRIGHT_CAPTURE_SCRIPT
    profile_sequence_match = PROFILE_SEQUENCE_RE.search(source)
    profile_inject_match = PROFILE_INJECT_FUNCTION_RE.search(source)
    if (
        source.count(LOCAL_GUARD) != 1
        or source.count(BODY_TEXT_LINE) != 1
        or source.count(LOCAL_FALLBACK_TEXT) != 1
        or source.count(PROFILE_INJECT_CALL) != 1
        or profile_sequence_match is None
        or profile_inject_match is None
        or "broadcaster-en" not in profile_sequence_match.group(0)
    ):
        raise recorder.RecordingError("Capture script safety anchors changed")
    source = source.replace(LOCAL_GUARD, HOSTED_GUARD, 1)
    source = source.replace(BODY_TEXT_LINE, SAFE_BODY_TEXT_LINE, 1)
    source = source.replace(LOCAL_FALLBACK_TEXT, HOSTED_FALLBACK_TEXT, 1)
    source = source.replace(PROFILE_INJECT_CALL, "", 1)
    source = PROFILE_INJECT_FUNCTION_RE.sub("", source, count=1)
    source = PROFILE_SEQUENCE_RE.sub(HOSTED_PROFILE_SEQUENCE_TEXT, source, count=1)
    if "127.0.0.1" in source or "localhost" in source or "broadcaster-en" in source:
        raise recorder.RecordingError("Hosted capture still contains a local-only path")
    return source


def verify_hosted_fallback(sample_insight: dict[str, Any]) -> dict[str, str]:
    from matchpulse.models import PersonalizedInsight

    original = PersonalizedInsight.model_validate(sample_insight)

    def malformed_handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "{not-valid-json"}}]},
        )

    def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("simulated local timeout", request=request)

    settings = recorder.FoundrySettings(
        endpoint="https://127.0.0.1:65535",
        deployment="local-mock",
        api_key="mock",
        timeout_seconds=0.2,
    )

    async def verify() -> dict[str, str]:
        checks = {}
        cases = (
            ("malformed-json", malformed_handler, "Foundry fallback: malformed-json"),
            ("timeout", timeout_handler, "Foundry fallback: ReadTimeout"),
        )
        for label, handler, expected_warning in cases:
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                foundry = recorder.FoundryNarrativeClient(settings, http_client=client)
                rewritten, warning = await foundry.rewrite(original)
                if rewritten != original or warning != expected_warning:
                    raise recorder.RecordingError(f"Hosted {label} deterministic fallback failed")
                if foundry.state != "degraded-fallback":
                    raise recorder.RecordingError(f"Hosted {label} fallback state mismatch")
                checks[label] = "PASS"
        return checks

    return asyncio.run(verify())


def prepare_paths(repo_root: Path, output_name: str) -> tuple[Path, Path, Path]:
    submission_dir = repo_root / "submission"
    output = submission_dir / output_name
    if output_name != CANDIDATE_NAME:
        raise ValueError(f"Output must be the prepared candidate filename: {CANDIDATE_NAME}")
    if not submission_dir.is_dir():
        raise ValueError("The existing submission directory is unavailable")
    if output.exists():
        raise ValueError("Candidate output already exists; refusing to overwrite")
    srt = submission_dir / "MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt"
    if not srt.is_file():
        raise ValueError("Existing submission captions are missing")
    return submission_dir, output, srt


def preflight(repo_root: Path, output_name: str) -> dict[str, Any]:
    submission_dir, output, srt_path = prepare_paths(repo_root, output_name)
    tools = recorder.verify_required_tools()
    source = hosted_capture_source()
    node_env = dict(os.environ)
    node_env["MATCHPULSE_CAPTURE_SOURCE"] = source
    syntax_check = subprocess.run(
        ["node", "-e", "new Function(process.env.MATCHPULSE_CAPTURE_SOURCE);"],
        env=node_env,
        capture_output=True,
        text=True,
        check=False,
    )
    if syntax_check.returncode != 0:
        raise recorder.RecordingError("Hosted Playwright source failed JavaScript syntax check")
    cues = recorder.parse_srt(srt_path, max_duration_seconds=VIDEO_DURATION_SECONDS)
    narration, audio_stats = recorder.synthesize_narration_wav_bytes(
        cues, VIDEO_DURATION_SECONDS, ffmpeg_bin=tools["ffmpeg_bin"]
    )
    return {
        "status": "READY",
        "candidate": output.name,
        "candidate_parent_exists": output.parent.is_dir(),
        "candidate_exists": output.exists(),
        "existing_video_hashes": existing_video_hashes(submission_dir),
        "caption_cues": len(cues),
        "duration_seconds": VIDEO_DURATION_SECONDS,
        "narration_bytes": len(narration),
        "narration_lufs": audio_stats["integrated_lufs"],
        "narration_true_peak_dbtp": audio_stats["true_peak_dbtp"],
        "ffmpeg_version": tools["ffmpeg_version"],
        "ffprobe_version": tools["ffprobe_version"],
        "playwright_version": tools["playwright_version"],
        "chromium_version": tools["browser_version"],
        "viewport": "1920x1080",
        "frame_rate": "30/1",
        "network_policy": "exact Azure HTTPS/WSS authority only",
        "hosted_playwright_syntax": "PASS",
        "ingress_mutation_performed": False,
    }



def _local_tts_paths(repo_root: Path) -> tuple[Path, Path, Path, Path, Path]:
    submission_dir = repo_root / "submission"
    source = submission_dir / CANDIDATE_NAME
    audio = submission_dir / LOCAL_TTS_AUDIO_NAME
    manifest = submission_dir / LOCAL_TTS_MANIFEST_NAME
    output = submission_dir / LOCAL_TTS_CANDIDATE_NAME
    srt_path = submission_dir / "MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt"
    if not submission_dir.is_dir() or not srt_path.is_file():
        raise ValueError("Existing submission directory or hosted captions are unavailable")
    if not source.is_file():
        raise ValueError("The existing hosted candidate video is required as the remux source")
    return submission_dir, source, audio, manifest, output


def _protected_video_hashes(
    submission_dir: Path,
    *,
    video_paths: tuple[Path, ...] | None = None,
) -> dict[str, str]:
    root = submission_dir.resolve()
    paths = (
        tuple(submission_dir / name for name in (*ORIGINAL_VIDEO_NAMES, CANDIDATE_NAME))
        if video_paths is None
        else video_paths
    )
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise ValueError("Protected source video is missing: " + ", ".join(path.name for path in missing))
    try:
        relative_paths = {path: path.resolve().relative_to(root).as_posix() for path in paths}
    except ValueError as exc:
        raise ValueError("Protected source videos must be inside the submission directory") from exc
    return {relative_paths[path]: recorder.sha256_file(path) for path in paths}


def _verify_protected_video_hashes(submission_dir: Path, expected: dict[str, str]) -> None:
    current = {
        name: recorder.sha256_file(submission_dir / Path(name))
        for name in expected
    }
    if current != expected:
        raise recorder.RecordingError("An original or source candidate video changed during local narration")


def narration_preflight(
    repo_root: Path,
    *,
    tts_url: str,
    engine: str = "kokoro",
    voice: str = "bf_emma",
    speed: float = 0.95,
) -> dict[str, Any]:
    if engine != "kokoro":
        raise ValueError("Only the local kokoro engine is supported")
    if not 0.90 <= speed <= 1.05:
        raise ValueError("TTS speed must be between 0.90 and 1.05")
    submission_dir, source, audio, manifest, output = _local_tts_paths(repo_root)
    collisions = [path.name for path in (audio, manifest, output) if path.exists()]
    if collisions:
        raise ValueError("Local narration output already exists; refusing overwrite: " + ", ".join(collisions))
    cues = recorder.parse_srt(
        submission_dir / "MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt",
        max_duration_seconds=VIDEO_DURATION_SECONDS,
    )
    hashes = _protected_video_hashes(submission_dir)
    with LocalDockerTTS(tts_url, approved_output_dirs=(submission_dir, Path(tempfile.gettempdir()))) as tts:
        health = tts.health_check()
        voices = tts.discover_voices()
        if voice not in voices:
            raise LocalTTSError(f"Requested local TTS voice is unavailable: {voice}")
    timeline = []
    for cue in cues:
        window = plan_segment_window(cue)
        estimate = estimated_cue_duration(cue_text(cue)) / speed
        timeline.append({
            "cue_index": cue.index,
            "start_ms": window.start_ms,
            "end_ms": window.end_ms,
            "speech_start_ms": window.speech_start_ms,
            "speech_end_ms": window.speech_end_ms,
            "estimated_duration_seconds": round(estimate, 3),
            "fits_estimated_window": estimate <= window.max_duration,
        })
    return {
        "status": "READY", "provider": "local-docker", "engine": engine,
        "voice": voice, "speed": speed, "health": health, "voice_available": True,
        "caption_cues": len(cues), "duration_seconds": VIDEO_DURATION_SECONDS,
        "timeline": timeline, "candidate_collision_check": "PASS",
        "existing_video_hashes": hashes, "source_candidate": source.name,
        "outputs": [audio.name, manifest.name, output.name],
        "azure_contacted": False, "narration_written": False,
    }


def render_local_narration(
    repo_root: Path,
    *,
    tts_url: str,
    engine: str = "kokoro",
    voice: str = "bf_emma",
    speed: float = 0.95,
) -> dict[str, Any]:
    if engine != "kokoro":
        raise ValueError("Only the local kokoro engine is supported")
    if not 0.90 <= speed <= 1.05:
        raise ValueError("TTS speed must be between 0.90 and 1.05")
    submission_dir, source, audio, manifest_path, output = _local_tts_paths(repo_root)
    collisions = [path.name for path in (audio, manifest_path, output) if path.exists()]
    if collisions:
        raise ValueError("Local narration output already exists; refusing overwrite: " + ", ".join(collisions))
    cues = recorder.parse_srt(
        submission_dir / "MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt",
        max_duration_seconds=VIDEO_DURATION_SECONDS,
    )
    before_hashes = _protected_video_hashes(submission_dir)
    tools = recorder.verify_required_tools()
    with LocalDockerTTS(tts_url, approved_output_dirs=(submission_dir, Path(tempfile.gettempdir()))) as tts:
        tts.health_check()
        if voice not in tts.discover_voices():
            raise LocalTTSError(f"Requested local TTS voice is unavailable: {voice}")
        manifest = synthesize_timeline(
            adapter=tts, cues=cues, total_duration_seconds=VIDEO_DURATION_SECONDS,
            output_path=audio, manifest_path=manifest_path,
            ffmpeg_bin=tools["ffmpeg_bin"], voice=voice, speed=speed, language="b",
        )
    with tempfile.TemporaryDirectory(prefix="matchpulse-local-remux-") as work_dir:
        staged = Path(work_dir) / output.name
        command = [
            tools["ffmpeg_bin"], "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
            "-i", str(source), "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-t", str(VIDEO_DURATION_SECONDS), "-movflags", "+faststart", str(staged),
        ]
        try:
            subprocess.run(command, capture_output=True, check=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise recorder.RecordingError("FFmpeg could not remux the local narration candidate") from exc
        media = recorder.verify_media_file(
            ffprobe_bin=tools["ffprobe_bin"], ffmpeg_bin=tools["ffmpeg_bin"],
            video_path=staged, min_duration=114.0, max_duration=116.0,
        )
        _verify_protected_video_hashes(submission_dir, before_hashes)
        if output.exists():
            raise ValueError("Local narration candidate appeared during rendering; refusing overwrite")
        created_output = False
        try:
            with output.open("xb") as destination:
                created_output = True
                with staged.open("rb") as staged_file:
                    shutil.copyfileobj(staged_file, destination)
            _verify_protected_video_hashes(submission_dir, before_hashes)
        except FileExistsError as exc:
            raise ValueError("Local narration candidate appeared during rendering; refusing overwrite") from exc
        except Exception:
            if created_output:
                output.unlink(missing_ok=True)
            raise
    return {
        "status": "LOCAL_NARRATION_RENDERED", "candidate": output.name,
        "narration": audio.name, "manifest": manifest_path.name,
        "segments": len(manifest["segments"]), "media": media,
        "existing_videos_unchanged": True, "provider": "local-docker", "azure_contacted": False,
    }

def render_conversational_narration(
    repo_root: Path,
    *,
    tts_url: str,
    engine: str = "kokoro",
    voice: str = "bf_emma",
    source_video_path: Path | None = None,
    captions_path: Path | None = None,
    script_path: Path | None = None,
    audio_output_path: Path | None = None,
    manifest_output_path: Path | None = None,
    video_output_path: Path | None = None,
    protected_video_paths: tuple[Path, ...] | None = None,
) -> dict[str, Any]:
    if engine != "kokoro" or voice != "bf_emma":
        raise ValueError("Conversational narration requires the local kokoro engine and bf_emma voice")
    submission_dir = repo_root / "submission"
    source = source_video_path or submission_dir / CANDIDATE_NAME
    captions = captions_path or submission_dir / "MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt"
    script_path = script_path or submission_dir / CONVERSATIONAL_SCRIPT_NAME
    audio = audio_output_path or submission_dir / CONVERSATIONAL_TTS_AUDIO_NAME
    manifest_path = manifest_output_path or submission_dir / CONVERSATIONAL_TTS_MANIFEST_NAME
    output = video_output_path or submission_dir / CONVERSATIONAL_TTS_CANDIDATE_NAME
    if not source.is_file() or not script_path.is_file():
        raise ValueError("Hosted source candidate and conversational script must exist")
    collisions = [path.name for path in (audio, manifest_path, output) if path.exists()]
    if collisions:
        raise ValueError("Conversational narration output already exists; refusing overwrite: " + ", ".join(collisions))
    cues = recorder.parse_srt(
        captions,
        max_duration_seconds=VIDEO_DURATION_SECONDS,
    )
    script = json.loads(script_path.read_text(encoding="utf-8"))
    if script.get("style_label") != STYLE_LABEL or not isinstance(script.get("units"), list):
        raise ValueError("Conversational narration script has an unsupported style or structure")
    before_hashes = _protected_video_hashes(
        submission_dir,
        video_paths=protected_video_paths,
    )
    tools = recorder.verify_required_tools()
    ffmpeg_bin = shutil.which("ffmpeg") or tools["ffmpeg_bin"]
    ffprobe_bin = shutil.which("ffprobe") or tools["ffprobe_bin"]
    with LocalDockerTTS(
        tts_url, approved_output_dirs=(submission_dir, Path(tempfile.gettempdir())),
        timeout_seconds=30.0, retries=3,
    ) as tts:
        tts.health_check()
        if voice not in tts.discover_voices():
            raise LocalTTSError(f"Requested local TTS voice is unavailable: {voice}")
        manifest = synthesize_conversational_timeline(
            adapter=tts, cues=cues, units=script["units"],
            total_duration_seconds=VIDEO_DURATION_SECONDS, output_path=audio,
            manifest_path=manifest_path, ffmpeg_bin=ffmpeg_bin,
            voice=voice, substitutions=script.get("pronunciation_substitutions", []),
            style_label=script["style_label"],
            generation_attempt=int(script.get("generation_attempt", 1)),
        )
    with tempfile.TemporaryDirectory(prefix="matchpulse-conversational-remux-") as work_dir:
        staged = Path(work_dir) / output.name
        command = [
            ffmpeg_bin, "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
            "-i", str(source), "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-t", str(VIDEO_DURATION_SECONDS), "-movflags", "+faststart", str(staged),
        ]
        try:
            subprocess.run(command, capture_output=True, check=True)
        except (OSError, subprocess.CalledProcessError) as exc:
            raise recorder.RecordingError("FFmpeg could not remux the conversational narration candidate") from exc
        media = recorder.verify_media_file(
            ffprobe_bin=ffprobe_bin, ffmpeg_bin=ffmpeg_bin,
            video_path=staged, min_duration=114.0, max_duration=116.0,
        )
        _verify_protected_video_hashes(submission_dir, before_hashes)
        if output.exists():
            raise ValueError("Conversational candidate appeared during rendering; refusing overwrite")
        try:
            with output.open("xb") as destination, staged.open("rb") as staged_file:
                shutil.copyfileobj(staged_file, destination)
            _verify_protected_video_hashes(submission_dir, before_hashes)
        except FileExistsError as exc:
            raise ValueError("Conversational candidate appeared during rendering; refusing overwrite") from exc
        except Exception:
            output.unlink(missing_ok=True)
            raise
    return {
        "status": "CONVERSATIONAL_NARRATION_RENDERED",
        "candidate": output.name, "narration": audio.name, "manifest": manifest_path.name,
        "thought_units": manifest["thought_unit_count"], "speed_range": manifest["speed_range"],
        "media": media, "existing_videos_unchanged": True,
        "provider": "local-docker", "azure_contacted": False,
    }


def _verify_hosted_profiles(payload: dict[str, Any], expected_match_id: str) -> dict[str, Any]:
    if payload.get("match_id") != expected_match_id:
        raise recorder.RecordingError("Hosted variant match ID mismatch")
    moments = payload.get("moments") or []
    if not moments:
        raise recorder.RecordingError("Hosted variants returned no moments")
    target = moments[-1]
    variants = {item["profile_id"]: item for item in target.get("variants", [])}
    expected_profiles = {"fan-en", "analyst-en", "broadcaster-es", "fan-fr"}
    if not expected_profiles.issubset(variants):
        raise recorder.RecordingError("Hosted variants are missing an expected profile")
    evidence = target.get("evidence_event_ids")
    stats = target.get("stats")
    if not evidence or any(
        variants[profile].get("evidence_event_ids") != evidence or variants[profile].get("stats") != stats
        for profile in expected_profiles
    ):
        raise recorder.RecordingError("Hosted profile facts/evidence are inconsistent")
    if variants["broadcaster-es"].get("locale") != "es":
        raise recorder.RecordingError("Hosted Spanish broadcaster locale mismatch")
    if variants["fan-fr"].get("locale") != "fr":
        raise recorder.RecordingError("Hosted French fan locale mismatch")
    if variants["fan-en"].get("title") == variants["analyst-en"].get("title"):
        raise recorder.RecordingError("Hosted fan and analyst presentation did not differ")
    return {
        "insight_id": target["insight_id"],
        "evidence_event_ids": evidence,
        "stats": stats,
        "variants_by_profile": variants,
    }


def _capture_hosted_take(tools: dict[str, str], base_url: str, authority: str) -> dict[str, Any]:
    match_id = recorder.SCENARIO_ID
    reset_before = recorder.reset_match(base_url, match_id)
    scenario = recorder.build_scenario_events(match_id)
    source = hosted_capture_source()

    config = {
        "playwright_module": tools["playwright_module"],
        "chrome_bin": tools["chrome_bin"],
        "base_url": base_url,
        "allowed_authority": authority,
        "match_id": match_id,
        "valid_events": [event.model_dump(mode="json") for event in scenario["valid_events"]],
        "duplicate_event": scenario["duplicate_event"].model_dump(mode="json"),
        "out_of_order_event": scenario["out_of_order_event"].model_dump(mode="json"),
    }
    env = dict(os.environ)
    env["MATCHPULSE_CAPTURE_CONFIG"] = json.dumps(config)
    process = subprocess.run(
        ["node", "-e", source],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=900,
    )
    try:
        if process.returncode != 0:
            raise recorder.RecordingError("Hosted Playwright capture failed")
        capture_result = json.loads(process.stdout)
        if capture_result.get("blocked_requests"):
            raise recorder.RecordingError("Unexpected browser network request was blocked")

        evidence = capture_result["api_evidence"]
        final_state = evidence["final_state"]
        teams = final_state.get("teams") or {}
        goals = (
            (teams.get(recorder.HOME_TEAM) or {}).get("goals", 0),
            (teams.get(recorder.AWAY_TEAM) or {}).get("goals", 0),
        )
        if goals != (2, 1) or final_state.get("status") != "finished":
            raise recorder.RecordingError("Hosted synthetic final score/state mismatch")
        if final_state.get("duplicate_count") != 1:
            raise recorder.RecordingError("Hosted duplicate-event assertion failed")
        if evidence["out_of_order_response"].get("status") != 409:
            raise recorder.RecordingError("Hosted out-of-order assertion failed")
        if not (evidence.get("recap_en") or {}).get("evidence_event_ids"):
            raise recorder.RecordingError("Hosted recap lacks accepted evidence")

        profile_check = _verify_hosted_profiles(evidence["variants_default"], expected_match_id=match_id)
        fallback_check = verify_hosted_fallback(evidence["equalizer_response"]["insights"][0])
        images = {
            key: Image.open(io.BytesIO(base64.b64decode(data))).convert("RGB")
            for key, data in (capture_result.get("states") or {}).items()
        }
        return {
            "images": images,
            "api_evidence": evidence,
            "profile_check": profile_check,
            "fallback_check": fallback_check,
            "blocked_requests": [],
            "reset_before": reset_before,
        }
    finally:
        recorder.reset_match(base_url, match_id)


def validate_hosted(
    base_url: str,
    window_start: datetime,
    window_end: datetime,
    *,
    allowed_host: str,
) -> dict[str, Any]:
    base_url, authority = validate_url(base_url, allowed_host)
    now = datetime.now(UTC)
    if not window_start <= now <= window_end:
        raise ValueError("Current time is outside the authorized recording window")
    if (window_end - window_start).total_seconds() > WINDOW_LIMIT_SECONDS:
        raise ValueError("Authorized recording window exceeds 60 minutes")
    tools = recorder.verify_required_tools()
    recorder.wait_for_health(base_url)
    with httpx.Client(base_url=base_url, timeout=15.0) as client:
        ready = client.get("/health/ready")
        ready.raise_for_status()
        ready_payload = ready.json()
    if ready_payload.get("synthetic_only") is not True or ready_payload.get("foundry_mode") != "disabled":
        raise recorder.RecordingError("Hosted readiness did not confirm synthetic-only and Foundry-off")
    capture = _capture_hosted_take(tools, base_url, authority)
    final_state = capture["api_evidence"]["final_state"]
    teams = final_state.get("teams") or {}
    return {
        "status": "HOSTED_VALIDATION_PASSED",
        "scenario": recorder.SCENARIO_ID,
        "seed": recorder.SYNTHETIC_SEED,
        "score": {
            recorder.HOME_TEAM: (teams.get(recorder.HOME_TEAM) or {}).get("goals", 0),
            recorder.AWAY_TEAM: (teams.get(recorder.AWAY_TEAM) or {}).get("goals", 0),
        },
        "duplicate_count": final_state.get("duplicate_count"),
        "out_of_order_status": capture["api_evidence"]["out_of_order_response"].get("status"),
        "profile_ids": sorted(capture["profile_check"]["variants_by_profile"]),
        "fallback_verified": bool(capture["fallback_check"]),
        "scenario_reset_after_validation": True,
        "network_policy": "exact Azure HTTPS/WSS authority only",
    }


def hosted_shots(capture: dict[str, Any]) -> list[recorder.ShotSpec]:
    shots = recorder.build_submission_shots(capture)
    hosted = []
    for shot in shots:
        if shot.shot_id == "S9":
            shot = replace(
                shot,
                state_key="profile_broadcaster_es",
                banner_title="SHOT 9 · BROADCASTER PROFILE IN SPANISH",
                callout_title="BROADCASTER PROFILE: broadcaster-es",
                callout_lines=(
                    "Locale: Spanish",
                    "Same accepted match facts and event evidence",
                    "Overlay: GOL - Harbor United",
                ),
            )
        elif shot.shot_id == "S10a":
            shot = replace(
                shot,
                end_ms=87_000,
                state_key="profile_fan_fr",
                banner_title="SHOT 10 · FAN PROFILE IN FRENCH",
                callout_title="FAN PROFILE: fan-fr",
                callout_lines=(
                    "Locale: French",
                    "Same accepted match facts and event evidence",
                    "Overlay: BUT !",
                ),
            )
        elif shot.shot_id == "S10b":
            continue
        lines = tuple(
            line.replace(
                "Endpoint: http://127.0.0.1:8080/demo",
                "Endpoint: Hosted Azure Container Apps",
            ).replace("Mode: Local Immutable Container", "Hosting: Azure Container Apps")
            for line in shot.callout_lines
        )
        hosted.append(
            replace(
                shot,
                banner_title=shot.banner_title.replace("LOCAL", "HOSTED"),
                callout_lines=lines,
            )
        )
    return hosted


def render_hosted_card(title: str, subtitle: str, lines: tuple[str, ...], footer: str) -> Image.Image:
    fonts = recorder._load_fonts()
    image = Image.new("RGB", (recorder.VIDEO_WIDTH, recorder.VIDEO_HEIGHT), (7, 26, 43))
    draw = ImageDraw.Draw(image)
    draw.rectangle([80, 70, recorder.VIDEO_WIDTH - 80, 130], fill=(12, 42, 66))
    draw.text(
        (115, 86),
        "HOSTED AZURE DEMONSTRATION · SEEDED SYNTHETIC DATA · NO LIVE EXTERNAL DATA",
        font=fonts["small"],
        fill=(200, 245, 96),
    )
    draw.text((130, 190), title, font=fonts["h1"], fill=(237, 247, 255))
    draw.text((130, 265), subtitle, font=fonts["h2"], fill=(22, 184, 243))
    y = 350
    for line in lines:
        draw.text((145, y), line, font=fonts["mono"], fill=(213, 231, 242))
        y += 42
    draw.rectangle(
        [
            130,
            recorder.VIDEO_HEIGHT - 165,
            recorder.VIDEO_WIDTH - 130,
            recorder.VIDEO_HEIGHT - 105,
        ],
        fill=(10, 32, 50),
        outline=(59, 97, 119),
    )
    draw.text(
        (155, recorder.VIDEO_HEIGHT - 148),
        footer,
        font=fonts["body"],
        fill=(200, 245, 96),
    )
    return image


def hosted_composite(
    state_images: dict[str, Image.Image],
    shot: recorder.ShotSpec,
    base_compositor: Any,
) -> Image.Image:
    if shot.state_key == "card_title":
        return render_hosted_card(
            "MATCHPULSE LIVE",
            "EVIDENCE-AWARE MATCH STORYTELLING",
            (
                "Hosting: Azure Container Apps",
                "Scenario: matchpulse-demo-001 · Seed 20261024",
                "Fictional teams: Northbridge City vs Harbor United",
                "Data: SEEDED SYNTHETIC MATCH DATA",
                "Foundry: disabled · Model calls: zero",
                f"Image: {recorder.EXPECTED_IMAGE_DIGEST}",
            ),
            "Hosted endpoint verified · no live external data source",
        )
    if shot.state_key == "card_closing":
        return render_hosted_card(
            "MATCHPULSE LIVE",
            "ONE MATCH · MULTIPLE AUDIENCES · TRACEABLE STORIES",
            (
                "Northbridge City 2 - 1 Harbor United",
                "Fan · Analyst · Broadcaster",
                "English · Spanish · French",
                "Evidence-linked recap · deterministic fallback",
                "Hosted on Azure Container Apps",
                "SEEDED SYNTHETIC MATCH DATA · FOUNDRY DISABLED",
            ),
            "ofayese/matchpulse-live · synthetic demonstration",
        )

    base = base_compositor(state_images, shot)
    draw = ImageDraw.Draw(base)
    draw.rectangle([0, 0, recorder.VIDEO_WIDTH, 38], fill=(6, 21, 33))
    draw.line([(0, 36), (recorder.VIDEO_WIDTH, 36)], fill=(200, 245, 96), width=2)
    draw.text(
        (24, 7),
        f"HOSTED AZURE DEMONSTRATION · SEEDED SYNTHETIC DATA · NO LIVE EXTERNAL DATA  |  {shot.banner_title}",
        font=recorder._load_fonts()["mono_sm"],
        fill=(200, 245, 96),
    )
    return base


def record_candidate(
    repo_root: Path,
    base_url: str,
    window_start: datetime,
    window_end: datetime,
    output_name: str,
    *,
    allowed_host: str,
    tts_provider: str = "system",
    tts_url: str = "",
    tts_engine: str = "kokoro",
    tts_voice: str = "bf_emma",
    tts_speed: float = 0.95,
) -> dict[str, Any]:
    base_url, authority = validate_url(base_url, allowed_host)
    now = datetime.now(UTC)
    if not window_start <= now <= window_end:
        raise ValueError("Current time is outside the authorized recording window")
    if (window_end - window_start).total_seconds() > WINDOW_LIMIT_SECONDS:
        raise ValueError("Authorized recording window exceeds 60 minutes")

    submission_dir, output_path, srt_path = prepare_paths(repo_root, output_name)
    original_hashes = existing_video_hashes(submission_dir, exclude_names={output_path.name})
    tools = recorder.verify_required_tools()
    cues = recorder.parse_srt(srt_path, max_duration_seconds=VIDEO_DURATION_SECONDS)
    if tts_provider == "system":
        narration, narration_stats = recorder.synthesize_narration_wav_bytes(
            cues, VIDEO_DURATION_SECONDS, ffmpeg_bin=tools["ffmpeg_bin"]
        )
    elif tts_provider == "local-docker":
        if not tts_url:
            raise ValueError("--tts-provider local-docker requires --tts-url")
        if tts_engine != "kokoro":
            raise ValueError("Only the local kokoro engine is supported")
        with tempfile.TemporaryDirectory(prefix="matchpulse-local-tts-record-") as work_dir:
            work = Path(work_dir)
            with LocalDockerTTS(tts_url, approved_output_dirs=(work, Path(tempfile.gettempdir()))) as tts:
                tts.health_check()
                if tts_voice not in tts.discover_voices():
                    raise LocalTTSError(f"Requested local TTS voice is unavailable: {tts_voice}")
                synthesize_timeline(
                    adapter=tts, cues=cues, total_duration_seconds=VIDEO_DURATION_SECONDS,
                    output_path=work / "narration.wav", manifest_path=work / "manifest.json",
                    ffmpeg_bin=tools["ffmpeg_bin"], voice=tts_voice, speed=tts_speed, language="b",
                )
            narration = (work / "narration.wav").read_bytes()
        narration_stats = {}
    else:
        raise ValueError("Unsupported TTS provider")
    recorder.wait_for_health(base_url)
    with httpx.Client(base_url=base_url, timeout=15.0) as client:
        ready = client.get("/health/ready")
        ready.raise_for_status()
        ready_payload = ready.json()
        if ready_payload.get("synthetic_only") is not True or ready_payload.get("foundry_mode") != "disabled":
            raise recorder.RecordingError("Hosted readiness did not confirm synthetic-only and Foundry-off")

    capture = _capture_hosted_take(tools, base_url, authority)
    shots = hosted_shots(capture)
    original_compositor = recorder.composite_shot_base
    recorder.composite_shot_base = lambda images, shot: hosted_composite(images, shot, original_compositor)
    try:
        recorder.encode_video_with_ffmpeg(
            ffmpeg_bin=tools["ffmpeg_bin"],
            output_path=output_path,
            shots=shots,
            state_images=capture["images"],
            wav_bytes=narration,
            total_duration_seconds=VIDEO_DURATION_SECONDS,
            cues=cues,
        )
    finally:
        recorder.composite_shot_base = original_compositor

    media = recorder.verify_media_file(
        ffprobe_bin=tools["ffprobe_bin"],
        ffmpeg_bin=tools["ffmpeg_bin"],
        video_path=output_path,
        min_duration=105.0,
        max_duration=119.0,
    )
    if existing_video_hashes(submission_dir, exclude_names={output_path.name}) != original_hashes:
        raise recorder.RecordingError("An existing video changed during candidate recording")
    if datetime.now(UTC) > window_end:
        raise recorder.RecordingError("Recording completed after the authorized window end")
    return {
        "status": "CANDIDATE_RECORDED",
        "candidate": output_path.name,
        "media": media,
        "shot_count": len(shots),
        "narration_lufs": narration_stats.get("integrated_lufs"),
        "narration_true_peak_dbtp": narration_stats.get("true_peak_dbtp"),
        "blocked_external_requests": len(capture["blocked_requests"]),
        "existing_videos_unchanged": True,
        "scenario_reset_after_capture": True,
        "recording_window_end_utc": window_end.isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--validate-hosted", action="store_true")
    mode.add_argument("--record", action="store_true")
    mode.add_argument("--narration-preflight", action="store_true")
    mode.add_argument("--render-local-narration", action="store_true")
    mode.add_argument("--render-conversational-narration", action="store_true")
    parser.add_argument("--tts-provider", choices=("system", "local-docker"), default="system")
    parser.add_argument("--tts-url", default="")
    parser.add_argument("--tts-engine", default="kokoro")
    parser.add_argument("--tts-voice", default="bf_emma")
    parser.add_argument("--tts-speed", type=float, default=0.95)
    parser.add_argument("--url", default="")
    parser.add_argument(
        "--allowed-host",
        default=os.environ.get("MATCHPULSE_HOSTED_ALLOWED_HOST", ""),
        help="Exact Azure Container Apps hostname permitted for hosted recording",
    )
    parser.add_argument("--output", default=CANDIDATE_NAME)
    parser.add_argument("--window-start", default="")
    parser.add_argument("--window-end", default="")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    try:
        if args.narration_preflight or (args.preflight and args.tts_provider == "local-docker"):
            if args.tts_provider != "local-docker" or not args.tts_url:
                raise ValueError("--narration-preflight requires --tts-provider local-docker and --tts-url")
            result = narration_preflight(
                repo_root, tts_url=args.tts_url, engine=args.tts_engine,
                voice=args.tts_voice, speed=args.tts_speed,
            )
        elif args.render_conversational_narration:
            if args.tts_provider != "local-docker" or not args.tts_url:
                raise ValueError("--render-conversational-narration requires --tts-provider local-docker and --tts-url")
            result = render_conversational_narration(
                repo_root, tts_url=args.tts_url, engine=args.tts_engine, voice=args.tts_voice,
            )
        elif args.render_local_narration:
            if args.tts_provider != "local-docker" or not args.tts_url:
                raise ValueError("--render-local-narration requires --tts-provider local-docker and --tts-url")
            result = render_local_narration(
                repo_root, tts_url=args.tts_url, engine=args.tts_engine,
                voice=args.tts_voice, speed=args.tts_speed,
            )
        elif args.preflight:
            result = preflight(repo_root, args.output)
        elif args.validate_hosted:
            if not args.url or not args.window_start or not args.window_end:
                raise ValueError("--validate-hosted requires --url, --window-start, and --window-end")
            result = validate_hosted(
                args.url,
                parse_utc(args.window_start),
                parse_utc(args.window_end),
                allowed_host=args.allowed_host,
            )
        else:
            if not args.url or not args.window_start or not args.window_end:
                raise ValueError("--record requires --url, --window-start, and --window-end")
            result = record_candidate(
                repo_root,
                args.url,
                parse_utc(args.window_start),
                parse_utc(args.window_end),
                args.output,
                allowed_host=args.allowed_host,
                tts_provider=args.tts_provider,
                tts_url=args.tts_url,
                tts_engine=args.tts_engine,
                tts_voice=args.tts_voice,
                tts_speed=args.tts_speed,
            )
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "FAILED", "error": type(exc).__name__, "message": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
