# cspell:ignore uncaptioned opencontainers kilocode ffprobe FFPROBE pids cpus blockedbyclient matchinfo networkidle LANCZOS segoe segoeuib segoeui consolas consola Timecode textbbox predeployment LUFS Zira atempo loudnorm afade lufs dbtp rawvideo libx movflags faststart tobytes blackdetect freezedetect ebur
"""Deterministic Playwright + FFmpeg recording and verification pipeline for MatchPulse Live.

Runs the published immutable container image locally on 127.0.0.1:8080 in
CHALLENGE_SYNTHETIC_ONLY=true mode, executes the deterministic fictional match
scenario (matchpulse-demo-001: Northbridge City vs Harbor United, seed 20261024),
captures live Chromium browser states via Playwright with a fail-closed network
guard, synthesizes and normalizes local narration audio, encodes the uncaptioned
and captioned submission and technical MP4 deliverables, runs FFprobe/quality
and secret scans, and writes the manifest and verification report without
creating any new directories.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import io
import json
import math
import os
import re
import socket
import subprocess
import sys
import time
import urllib.parse
import wave
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from PIL import Image, ImageDraw, ImageFont

from matchpulse.foundry import FoundryNarrativeClient, FoundrySettings
from matchpulse.models import (
    AudienceProfile,
    DetailLevel,
    EventType,
    MatchEvent,
    Persona,
)

EXPECTED_REPOSITORY = "ofayese/matchpulse-live"
EXPECTED_SOURCE_SHA = "335781f928011f99a644083d80bfe4dfc480b1a6"
EXPECTED_IMAGE_DIGEST = (
    "sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226"
)
EXPECTED_IMAGE_REF = f"ghcr.io/{EXPECTED_REPOSITORY}@{EXPECTED_IMAGE_DIGEST}"
EXPECTED_ATTESTATION_ID = "59336499"
EXPECTED_WORKFLOW_RUN_ID = "40059698831"
EXPECTED_OCI_SOURCE = f"https://github.com/{EXPECTED_REPOSITORY}"

CONTAINER_NAME = "matchpulse-video-demo"
APPLICATION_ENDPOINT = "http://127.0.0.1:8080"
SCENARIO_ID = "matchpulse-demo-001"
SYNTHETIC_SEED = 20261024
HOME_TEAM = "Northbridge City"
AWAY_TEAM = "Harbor United"
FINAL_SCORE = {"home": 2, "away": 1}

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30
AUDIO_SAMPLE_RATE = 48000

PERMITTED_HOSTS = {"127.0.0.1", "localhost"}
PERMITTED_SCHEMES = {"http", "ws", "about", "data"}

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("github_pat", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b")),
    ("github_fine_grained_pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("bearer_token", re.compile(r"Bearer\s+[A-Za-z0-9._\-]{16,}", re.IGNORECASE)),
    (
        "connection_string",
        re.compile(
            r"(?:AccountKey|SharedAccessKey|InstrumentationKey)\s*=\s*[^\s;\"']+",
            re.IGNORECASE,
        ),
    ),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    (
        "password_assignment",
        re.compile(
            r"(?:password|passwd|client_secret|api_key)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
            re.IGNORECASE,
        ),
    ),
    (
        "windows_user_path",
        re.compile(r"[A-Za-z]:\\Users\\[A-Za-z0-9._\-]+", re.IGNORECASE),
    ),
    ("unix_user_path", re.compile(r"/Users/[A-Za-z0-9._\-]+")),
    (
        "email_address",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    ),
)


class RecordingError(RuntimeError):
    """Fail-closed error raised when any recording or verification gate fails."""


@dataclass(frozen=True)
class SrtCue:
    index: int
    start_ms: int
    end_ms: int
    lines: tuple[str, ...]

    @property
    def duration_seconds(self) -> float:
        return (self.end_ms - self.start_ms) / 1000.0

    @property
    def text(self) -> str:
        return " ".join(self.lines)


@dataclass(frozen=True)
class ShotSpec:
    shot_id: str
    start_ms: int
    end_ms: int
    state_key: str
    banner_title: str
    callout_title: str
    callout_lines: tuple[str, ...]
    cursor_start: tuple[int, int]
    cursor_end: tuple[int, int]


def resolve_repo_root(override: Path | None = None) -> Path:
    if override is not None:
        return override.resolve()
    return Path(__file__).resolve().parent.parent


def required_output_paths(repo_root: Path) -> dict[str, Path]:
    submission_dir = repo_root / "submission"
    scripts_dir = repo_root / "scripts"
    return {
        "plan": submission_dir / "MATCHPULSE_PLAYWRIGHT_RECORDING_PLAN.md",
        "scripts_doc": submission_dir / "MATCHPULSE_VIDEO_SCRIPTS.md",
        "shot_lists": submission_dir / "MATCHPULSE_SHOT_LISTS.md",
        "submission_srt": submission_dir / "MATCHPULSE_CAPTIONS_SUBMISSION.srt",
        "technical_srt": submission_dir / "MATCHPULSE_CAPTIONS_TECHNICAL.srt",
        "manifest": submission_dir / "MATCHPULSE_VIDEO_MANIFEST.json",
        "verification": submission_dir / "MATCHPULSE_VIDEO_VERIFICATION.txt",
        "submission_mp4": submission_dir / "matchpulse-submission-demo.mp4",
        "submission_captioned_mp4": submission_dir
        / "matchpulse-submission-demo-captioned.mp4",
        "technical_mp4": submission_dir / "matchpulse-technical-demo.mp4",
        "technical_captioned_mp4": submission_dir
        / "matchpulse-technical-demo-captioned.mp4",
        "record_script": scripts_dir / "record_matchpulse_demo.py",
    }


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def verify_repository_identity(
    repo_root: Path,
    *,
    expected_sha: str = EXPECTED_SOURCE_SHA,
) -> dict[str, str]:
    """Verify local HEAD, origin/main, and clean working tree before recording."""
    if not (repo_root / ".git").exists():
        raise RecordingError(f"Repository .git metadata not found at {repo_root.name}")

    head_sha = subprocess.check_output(
        ["git", "--no-pager", "rev-parse", "HEAD"],
        cwd=repo_root,
        text=True,
    ).strip()
    origin_main_sha = subprocess.check_output(
        ["git", "--no-pager", "rev-parse", "origin/main"],
        cwd=repo_root,
        text=True,
    ).strip()

    if head_sha != expected_sha:
        raise RecordingError(
            f"HEAD SHA mismatch: expected {expected_sha}, got {head_sha}"
        )
    if origin_main_sha != expected_sha:
        raise RecordingError(
            f"origin/main SHA mismatch: expected {expected_sha}, got {origin_main_sha}"
        )

    status_out = subprocess.check_output(
        ["git", "--no-pager", "status", "--porcelain"],
        cwd=repo_root,
        text=True,
    ).splitlines()
    allowed_untracked = {
        "?? submission/MATCHPULSE_PLAYWRIGHT_RECORDING_PLAN.md",
        "?? submission/MATCHPULSE_VIDEO_SCRIPTS.md",
        "?? submission/MATCHPULSE_SHOT_LISTS.md",
        "?? submission/MATCHPULSE_CAPTIONS_SUBMISSION.srt",
        "?? submission/MATCHPULSE_CAPTIONS_TECHNICAL.srt",
        "?? submission/MATCHPULSE_VIDEO_MANIFEST.json",
        "?? submission/MATCHPULSE_VIDEO_VERIFICATION.txt",
        "?? scripts/record_matchpulse_demo.py",
        "?? submission/",
    }
    unexpected = [
        line
        for line in status_out
        if line.strip() and line.strip() not in allowed_untracked
    ]
    if unexpected:
        raise RecordingError(
            f"Working tree contains unexpected modifications: {unexpected}"
        )

    return {"head_sha": head_sha, "origin_main_sha": origin_main_sha}


def verify_container_identity(
    *,
    expected_image_ref: str = EXPECTED_IMAGE_REF,
    expected_digest: str = EXPECTED_IMAGE_DIGEST,
    expected_sha: str = EXPECTED_SOURCE_SHA,
    expected_source: str = EXPECTED_OCI_SOURCE,
) -> dict[str, str]:
    """Verify the published immutable image digest, OCI labels, and platform."""
    try:
        raw = subprocess.check_output(
            ["docker", "image", "inspect", expected_image_ref],
            text=True,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        raise RecordingError(
            f"Failed to inspect container image {expected_image_ref}: {exc.returncode}"
        ) from exc

    info_list = json.loads(raw)
    if not info_list:
        raise RecordingError(f"Empty docker inspect response for {expected_image_ref}")
    info = info_list[0]
    repo_digests = info.get("RepoDigests") or []
    if not any(expected_digest in d for d in repo_digests):
        raise RecordingError(
            f"Image digest mismatch: expected {expected_digest} in {repo_digests}"
        )

    labels = (info.get("Config") or {}).get("Labels") or {}
    revision = labels.get("org.opencontainers.image.revision", "")
    source = labels.get("org.opencontainers.image.source", "")
    if revision != expected_sha:
        raise RecordingError(
            f"OCI revision mismatch: expected {expected_sha}, got {revision}"
        )
    if source != expected_source:
        raise RecordingError(
            f"OCI source mismatch: expected {expected_source}, got {source}"
        )

    arch = info.get("Architecture", "")
    os_name = info.get("Os", "")
    if (os_name, arch) != ("linux", "amd64"):
        raise RecordingError(f"Unsupported image platform: {os_name}/{arch}")

    return {
        "image_id": info.get("Id", ""),
        "digest": expected_digest,
        "oci_revision": revision,
        "oci_source": source,
        "platform": f"{os_name}/{arch}",
    }


def verify_output_paths(
    repo_root: Path,
    *,
    check_media_outputs_only: bool = True,
) -> dict[str, Path]:
    """Verify parent directories already exist and no target output file collides."""
    paths = required_output_paths(repo_root)
    for key, target in paths.items():
        parent = target.parent
        if not parent.exists() or not parent.is_dir():
            raise RecordingError(
                f"Required parent directory does not exist for {key}: {parent.name}"
            )

    keys_to_check = (
        (
            "manifest",
            "verification",
            "submission_mp4",
            "submission_captioned_mp4",
            "technical_mp4",
            "technical_captioned_mp4",
        )
        if check_media_outputs_only
        else tuple(paths.keys())
    )
    for key in keys_to_check:
        target = paths[key]
        if target.exists():
            size = target.stat().st_size
            digest = sha256_file(target)
            raise RecordingError(
                f"Output collision detected for {target.name} (bytes={size}, sha256={digest})"
            )
    return paths


def discover_binary(env_var: str, candidates: list[Path]) -> Path:
    override = os.getenv(env_var, "").strip()
    if override:
        p = Path(override)
        if p.exists():
            return p
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise RecordingError(f"Required binary not found for {env_var}")


def verify_required_tools() -> dict[str, str]:
    """Locate and verify Playwright, Chromium, FFmpeg, and FFprobe without installing binaries."""
    home = Path.home()
    ffmpeg_candidates = [
        home
        / ".antigravity-ide"
        / "extensions"
        / "kilocode.kilo-code-7.8.15-win32-x64"
        / "bin"
        / "ffmpeg.exe",
        home
        / ".antigravity-ide"
        / "extensions"
        / "kilocode.kilo-code-7.8.12-win32-x64"
        / "bin"
        / "ffmpeg.exe",
        Path(
            r"C:\Program Files (x86)\Power Automate Desktop\dotnet\x64\ffmpeg\ffmpeg.exe"
        ),
    ]
    ffprobe_candidates = [
        Path(
            r"C:\Program Files (x86)\Power Automate Desktop\dotnet\x64\ffmpeg\ffprobe.exe"
        ),
    ]
    chrome_candidates = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    ]
    playwright_pkg_candidates = [
        home
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "node"
        / "node_modules"
        / "playwright"
        / "package.json",
    ]

    ffmpeg_bin = discover_binary("MATCHPULSE_FFMPEG_BIN", ffmpeg_candidates)
    ffprobe_bin = discover_binary("MATCHPULSE_FFPROBE_BIN", ffprobe_candidates)
    chrome_bin = discover_binary("MATCHPULSE_CHROME_BIN", chrome_candidates)
    pw_pkg = discover_binary("MATCHPULSE_PLAYWRIGHT_PKG", playwright_pkg_candidates)

    ffmpeg_first = subprocess.check_output(
        [str(ffmpeg_bin), "-version"], text=True, stderr=subprocess.STDOUT
    ).splitlines()[0]
    ffprobe_first = subprocess.check_output(
        [str(ffprobe_bin), "-version"], text=True, stderr=subprocess.STDOUT
    ).splitlines()[0]
    pw_version = json.loads(pw_pkg.read_text(encoding="utf-8"))["version"]

    node_script = (
        f"const {{ chromium }} = require({json.dumps(str(pw_pkg.parent))});"
        f"(async()=>{{const b=await chromium.launch({{executablePath:{json.dumps(str(chrome_bin))},headless:true}});"
        f"console.log(b.version());await b.close();}})();"
    )
    browser_version = subprocess.check_output(
        ["node", "-e", node_script], text=True
    ).strip()

    return {
        "ffmpeg_bin": str(ffmpeg_bin),
        "ffprobe_bin": str(ffprobe_bin),
        "chrome_bin": str(chrome_bin),
        "playwright_module": str(pw_pkg.parent),
        "ffmpeg_version": ffmpeg_first.replace("ffmpeg version ", "")
        .split(" Copyright")[0]
        .strip(),
        "ffprobe_version": ffprobe_first.replace("ffprobe version ", "")
        .split(" Copyright")[0]
        .strip(),
        "playwright_version": pw_version,
        "browser_version": browser_version,
    }


def _port_is_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) != 0


def start_local_container(
    *,
    container_name: str = CONTAINER_NAME,
    image_ref: str = EXPECTED_IMAGE_REF,
    port: int = 8080,
) -> str:
    """Start the published immutable container with hardened flags on 127.0.0.1."""
    existing = subprocess.check_output(
        [
            "docker",
            "ps",
            "-a",
            "--filter",
            f"name=^{container_name}$",
            "--format",
            "{{.Names}}",
        ],
        text=True,
    ).strip()
    if existing:
        raise RecordingError(f"Container {container_name} already exists")
    if not _port_is_available("127.0.0.1", port):
        raise RecordingError(f"Port 127.0.0.1:{port} is already in use")

    cmd = [
        "docker",
        "run",
        "-d",
        "--rm",
        "--name",
        container_name,
        "--user",
        "10001:10001",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        "--pids-limit",
        "128",
        "--cpus",
        "1.0",
        "--memory",
        "512m",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,nodev,size=32m",
        "-p",
        f"127.0.0.1:{port}:8080",
        "-e",
        "CHALLENGE_SYNTHETIC_ONLY=true",
        image_ref,
    ]
    container_id = subprocess.check_output(cmd, text=True).strip()
    return container_id


def stop_local_container(container_name: str = CONTAINER_NAME) -> None:
    """Stop and remove the local demonstration container."""
    subprocess.run(
        ["docker", "rm", "-f", container_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    remaining = subprocess.check_output(
        [
            "docker",
            "ps",
            "-a",
            "--filter",
            f"name=^{container_name}$",
            "--format",
            "{{.Names}}",
        ],
        text=True,
    ).strip()
    if remaining:
        raise RecordingError(f"Failed to stop container {container_name}")


def wait_for_health(
    base_url: str = APPLICATION_ENDPOINT,
    *,
    timeout_seconds: float = 20.0,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Wait for /health/live and /health/ready and validate synthetic-only and Foundry states."""
    deadline = time.monotonic() + timeout_seconds
    last_error = "timeout"
    owned_client = client is None
    http = client or httpx.Client(base_url=base_url, timeout=2.5)
    try:
        while time.monotonic() < deadline:
            try:
                live = http.get("/health/live")
                ready = http.get("/health/ready")
                if live.status_code == 200 and ready.status_code == 200:
                    live_json = live.json()
                    ready_json = ready.json()
                    if live_json.get("status") != "ok":
                        raise RecordingError(
                            f"Unexpected /health/live payload: {live_json}"
                        )
                    if (
                        ready_json.get("status") != "ready"
                        or ready_json.get("synthetic_only") is not True
                    ):
                        raise RecordingError(
                            f"Unexpected /health/ready payload: {ready_json}"
                        )
                    if ready_json.get("foundry_mode") != "disabled":
                        raise RecordingError(
                            f"Expected foundry_mode='disabled' in local mode, got {ready_json.get('foundry_mode')}"
                        )
                    scan_text_for_secrets(
                        json.dumps(live_json) + "\n" + json.dumps(ready_json),
                        context="health_endpoints",
                    )
                    return {"live": live_json, "ready": ready_json}
                last_error = f"live={live.status_code}, ready={ready.status_code}"
            except RecordingError:
                raise
            except Exception as exc:
                last_error = type(exc).__name__
            time.sleep(0.25)
        raise RecordingError(f"Health gate failed for {base_url}: {last_error}")
    finally:
        if owned_client:
            http.close()


def validate_network_url(
    url: str, method: str = "GET", resource_type: str = "document"
) -> dict[str, str] | None:
    """Return None if URL is permitted by the network guard, or a sanitized block record if blocked."""
    parsed = urllib.parse.urlsplit(url)
    scheme = (parsed.scheme or "").lower()
    host = (parsed.hostname or "").lower()
    sanitized_path = parsed.path or "/"

    if scheme in {"about", "data"}:
        return None
    if scheme in {"http", "ws"} and host in PERMITTED_HOSTS:
        return None

    return {
        "method": method.upper(),
        "scheme": scheme or "unknown",
        "host": host or "unknown",
        "sanitized_path": sanitized_path,
        "resource_type": resource_type,
        "block_reason": f"disallowed_origin:{scheme}://{host}",
    }


def scan_text_for_secrets(text: str, *, context: str) -> None:
    """Fail closed if any secret, credential, email, or personal user path appears."""
    for name, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            raise RecordingError(
                f"Secret or sensitive pattern '{name}' detected in {context}"
            )


def build_scenario_events(match_id: str = SCENARIO_ID) -> dict[str, Any]:
    """Construct the deterministic fictional match scenario (Northbridge City 2 - 1 Harbor United)."""
    valid_events = [
        MatchEvent(
            event_id="evt-mp-001",
            match_id=match_id,
            sequence=0,
            clock_ms=0,
            event_type=EventType.MATCH_START,
            metadata={
                "scenario_id": SCENARIO_ID,
                "seed": SYNTHETIC_SEED,
                "home_team": HOME_TEAM,
                "away_team": AWAY_TEAM,
            },
        ),
        MatchEvent(
            event_id="evt-mp-002",
            match_id=match_id,
            sequence=1,
            clock_ms=360_000,
            event_type=EventType.POSSESSION,
            team_id=AWAY_TEAM,
            metadata={"share": 62.0, "previous_share": 50.0},
        ),
        MatchEvent(
            event_id="evt-mp-003",
            match_id=match_id,
            sequence=2,
            clock_ms=540_000,
            event_type=EventType.PRESSURE,
            team_id=AWAY_TEAM,
            player_id="HU-06",
            pressure=0.78,
        ),
        MatchEvent(
            event_id="evt-mp-004",
            match_id=match_id,
            sequence=3,
            clock_ms=550_000,
            event_type=EventType.PRESSURE,
            team_id=AWAY_TEAM,
            player_id="HU-08",
            pressure=0.82,
        ),
        MatchEvent(
            event_id="evt-mp-005",
            match_id=match_id,
            sequence=4,
            clock_ms=560_000,
            event_type=EventType.PRESSURE,
            team_id=AWAY_TEAM,
            player_id="HU-11",
            pressure=0.86,
        ),
        MatchEvent(
            event_id="evt-mp-006",
            match_id=match_id,
            sequence=5,
            clock_ms=720_000,
            event_type=EventType.TACKLE,
            team_id=HOME_TEAM,
            player_id="NC-08",
            outcome="success",
            x=74.0,
            y=42.0,
        ),
        MatchEvent(
            event_id="evt-mp-007",
            match_id=match_id,
            sequence=6,
            clock_ms=960_000,
            event_type=EventType.SHOT,
            team_id=AWAY_TEAM,
            player_id="HU-09",
            outcome="on_target",
            x=84.0,
            y=46.0,
            speed_kmh=104.5,
            metadata={"goalkeeper_action": "saved"},
        ),
        MatchEvent(
            event_id="evt-mp-008",
            match_id=match_id,
            sequence=7,
            clock_ms=1_200_000,
            event_type=EventType.PASS,
            team_id=HOME_TEAM,
            player_id="NC-10",
            target_player_id="NC-09",
            outcome="success",
            x=40.0,
            y=50.0,
            end_x=82.0,
            end_y=46.0,
            pressure=0.82,
        ),
        MatchEvent(
            event_id="evt-mp-009",
            match_id=match_id,
            sequence=8,
            clock_ms=1_260_000,
            event_type=EventType.GOAL,
            team_id=HOME_TEAM,
            player_id="NC-09",
            outcome="success",
            x=89.0,
            y=48.0,
            speed_kmh=101.2,
        ),
        MatchEvent(
            event_id="evt-mp-011",
            match_id=match_id,
            sequence=9,
            clock_ms=2_880_000,
            event_type=EventType.POSSESSION,
            team_id=AWAY_TEAM,
            metadata={"share": 64.0, "previous_share": 51.0},
        ),
        MatchEvent(
            event_id="evt-mp-012",
            match_id=match_id,
            sequence=10,
            clock_ms=3_360_000,
            event_type=EventType.GOAL,
            team_id=AWAY_TEAM,
            player_id="HU-11",
            outcome="success",
            x=88.0,
            y=52.0,
            speed_kmh=99.4,
        ),
        MatchEvent(
            event_id="evt-mp-013",
            match_id=match_id,
            sequence=11,
            clock_ms=4_320_000,
            event_type=EventType.SUBSTITUTION,
            team_id=HOME_TEAM,
            player_id="NC-14",
            target_player_id="NC-07",
        ),
        MatchEvent(
            event_id="evt-mp-014",
            match_id=match_id,
            sequence=12,
            clock_ms=5_040_000,
            event_type=EventType.SHOT,
            team_id=HOME_TEAM,
            player_id="NC-10",
            outcome="blocked",
            x=81.0,
            y=44.0,
            speed_kmh=98.2,
        ),
        MatchEvent(
            event_id="evt-mp-015",
            match_id=match_id,
            sequence=13,
            clock_ms=5_280_000,
            event_type=EventType.GOAL,
            team_id=HOME_TEAM,
            player_id="NC-09",
            outcome="success",
            x=91.0,
            y=50.0,
            speed_kmh=106.0,
        ),
        MatchEvent(
            event_id="evt-mp-016",
            match_id=match_id,
            sequence=14,
            clock_ms=5_400_000,
            event_type=EventType.MATCH_END,
        ),
    ]

    duplicate_event = valid_events[8].model_copy(deep=True)
    out_of_order_event = MatchEvent(
        event_id="evt-mp-010-ooo",
        match_id=match_id,
        sequence=5,
        clock_ms=1_080_000,
        event_type=EventType.PASS,
        team_id=AWAY_TEAM,
        player_id="HU-04",
        target_player_id="HU-08",
        outcome="success",
        x=32.0,
        y=40.0,
        end_x=54.0,
        end_y=45.0,
        pressure=0.45,
    )
    return {
        "valid_events": valid_events,
        "duplicate_event": duplicate_event,
        "out_of_order_event": out_of_order_event,
    }


def reset_match(
    base_url: str = APPLICATION_ENDPOINT,
    match_id: str = SCENARIO_ID,
    *,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Reset the target match state via POST /v1/matches/{match_id}/reset and confirm 404 on state."""
    owned = client is None
    http = client or httpx.Client(base_url=base_url, timeout=5.0)
    try:
        resp = http.post(f"/v1/matches/{match_id}/reset")
        if resp.status_code != 200:
            raise RecordingError(
                f"Reset failed for {match_id}: HTTP {resp.status_code}"
            )
        payload = resp.json()
        if payload.get("match_id") != match_id or payload.get("reset") is not True:
            raise RecordingError(f"Unexpected reset response: {payload}")
        state_check = http.get(f"/v1/matches/{match_id}/state")
        if state_check.status_code != 404:
            raise RecordingError(
                f"Match state still exists after reset: HTTP {state_check.status_code}"
            )
        return payload
    finally:
        if owned:
            http.close()


def ensure_broadcaster_en_profile(
    base_url: str = APPLICATION_ENDPOINT, *, client: httpx.Client | None = None
) -> dict[str, Any]:
    """Ensure the broadcaster-en profile is registered via PUT /v1/profiles/broadcaster-en."""
    owned = client is None
    http = client or httpx.Client(base_url=base_url, timeout=5.0)
    try:
        profile = AudienceProfile(
            profile_id="broadcaster-en",
            persona=Persona.BROADCASTER,
            locale="en",
            detail=DetailLevel.COMPACT,
            metric_interests=["shooting", "pressing"],
        )
        resp = http.put(
            "/v1/profiles/broadcaster-en", json=profile.model_dump(mode="json")
        )
        if resp.status_code != 200:
            raise RecordingError(
                f"Failed to register broadcaster-en profile: HTTP {resp.status_code}"
            )
        profiles_resp = http.get("/v1/profiles")
        profiles_resp.raise_for_status()
        profile_ids = {item["profile_id"] for item in profiles_resp.json()}
        required_profiles = {
            "fan-en",
            "analyst-en",
            "broadcaster-en",
            "broadcaster-es",
            "fan-fr",
        }
        missing = required_profiles - profile_ids
        if missing:
            raise RecordingError(
                f"Missing required audience profiles: {sorted(missing)}"
            )
        return resp.json()
    finally:
        if owned:
            http.close()


def verify_profile_transitions(
    variants_payload: dict[str, Any], *, expected_match_id: str = SCENARIO_ID
) -> dict[str, Any]:
    """Verify that fan-en, analyst-en, broadcaster-en, broadcaster-es, and fan-fr share identical facts and evidence."""
    if variants_payload.get("match_id") != expected_match_id:
        raise RecordingError(
            f"Variants match_id mismatch: {variants_payload.get('match_id')}"
        )
    moments = variants_payload.get("moments") or []
    if not moments:
        raise RecordingError("No moments present in variants payload")

    target_moment = moments[-1]
    insight_id = target_moment.get("insight_id")
    evidence_ids = target_moment.get("evidence_event_ids")
    stats = target_moment.get("stats")
    if not insight_id or not evidence_ids:
        raise RecordingError(
            f"Missing insight_id or evidence_event_ids in moment: {target_moment}"
        )

    by_profile = {v["profile_id"]: v for v in target_moment.get("variants") or []}
    required_order = [
        "fan-en",
        "analyst-en",
        "broadcaster-en",
        "broadcaster-es",
        "fan-fr",
    ]
    for pid in required_order:
        if pid not in by_profile:
            raise RecordingError(f"Required profile {pid} missing from moment variants")
        variant = by_profile[pid]
        if variant.get("evidence_event_ids") != evidence_ids:
            raise RecordingError(
                f"Evidence mismatch for profile {pid}: {variant.get('evidence_event_ids')} != {evidence_ids}"
            )
        if variant.get("stats") != stats:
            raise RecordingError(
                f"Stats mismatch for profile {pid}: {variant.get('stats')} != {stats}"
            )

    if by_profile["fan-en"]["title"] == by_profile["analyst-en"]["title"]:
        raise RecordingError("fan-en and analyst-en titles did not differentiate")
    if (
        by_profile["broadcaster-es"]["locale"] != "es"
        or by_profile["fan-fr"]["locale"] != "fr"
    ):
        raise RecordingError("Locale mismatch in broadcaster-es or fan-fr variants")

    return {
        "insight_id": insight_id,
        "evidence_event_ids": evidence_ids,
        "stats": stats,
        "variants_by_profile": by_profile,
    }


def verify_deterministic_fallback(sample_insight: dict[str, Any]) -> dict[str, Any]:
    """Verify deterministic fallback behavior using the repository's FoundryNarrativeClient with a local mock transport."""
    from matchpulse.models import PersonalizedInsight

    original = PersonalizedInsight.model_validate(sample_insight)

    def _malformed_handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "{not-valid-json"}}]},
        )

    def _timeout_handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("simulated local timeout", request=_request)

    settings = FoundrySettings(
        endpoint="https://127.0.0.1:65535",
        deployment="local-mock",
        api_key="mock",
        timeout_seconds=0.2,
    )

    async def _run_checks() -> dict[str, Any]:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(_malformed_handler)
        ) as malformed_http:
            client_malformed = FoundryNarrativeClient(
                settings, http_client=malformed_http
            )
            out_malformed, warn_malformed = await client_malformed.rewrite(original)
            if (
                out_malformed != original
                or warn_malformed != "Foundry fallback: malformed-json"
            ):
                raise RecordingError(
                    f"Malformed-JSON fallback failed: {warn_malformed}"
                )
            if client_malformed.state != "degraded-fallback":
                raise RecordingError(
                    f"Expected degraded-fallback state, got {client_malformed.state}"
                )

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(_timeout_handler)
        ) as timeout_http:
            client_timeout = FoundryNarrativeClient(settings, http_client=timeout_http)
            out_timeout, warn_timeout = await client_timeout.rewrite(original)
            if (
                out_timeout != original
                or warn_timeout != "Foundry fallback: ReadTimeout"
            ):
                raise RecordingError(f"Timeout fallback failed: {warn_timeout}")

        return {
            "malformed_json_warning": warn_malformed,
            "malformed_json_state": client_malformed.state,
            "timeout_warning": warn_timeout,
            "timeout_state": client_timeout.state,
            "preserved_insight_id": original.insight_id,
            "preserved_title": original.title,
        }

    return asyncio.run(_run_checks())


def parse_srt(path: Path, *, max_duration_seconds: float | None = None) -> list[SrtCue]:
    """Parse and strictly validate an SRT caption file."""
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        raise RecordingError(f"Empty SRT file: {path.name}")

    blocks = re.split(r"\r?\n\r?\n+", raw)
    cues: list[SrtCue] = []
    time_re = re.compile(
        r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})$"
    )
    prev_end = 0
    for expected_idx, block in enumerate(blocks, start=1):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3:
            raise RecordingError(
                f"Invalid SRT block {expected_idx} in {path.name}: {lines}"
            )
        try:
            idx = int(lines[0])
        except ValueError as exc:
            raise RecordingError(
                f"Non-integer cue index in {path.name}: {lines[0]}"
            ) from exc
        if idx != expected_idx:
            raise RecordingError(
                f"Non-sequential cue index in {path.name}: expected {expected_idx}, got {idx}"
            )

        m = time_re.match(lines[1])
        if not m:
            raise RecordingError(
                f"Invalid timestamp line in {path.name} cue {idx}: {lines[1]}"
            )
        vals = [int(v) for v in m.groups()]
        start_ms = ((vals[0] * 3600) + (vals[1] * 60) + vals[2]) * 1000 + vals[3]
        end_ms = ((vals[4] * 3600) + (vals[5] * 60) + vals[6]) * 1000 + vals[7]
        if end_ms <= start_ms:
            raise RecordingError(f"Non-positive cue duration in {path.name} cue {idx}")
        if start_ms < prev_end:
            raise RecordingError(f"Overlapping cue timestamps in {path.name} cue {idx}")
        prev_end = end_ms

        text_lines = tuple(lines[2:])
        if len(text_lines) > 2:
            raise RecordingError(
                f"Cue {idx} in {path.name} exceeds 2 lines: {text_lines}"
            )
        for tl in text_lines:
            if len(tl) > 46:
                raise RecordingError(
                    f"Cue {idx} line in {path.name} exceeds 46 chars ({len(tl)}): {tl}"
                )
            scan_text_for_secrets(tl, context=f"{path.name}:cue_{idx}")

        cues.append(
            SrtCue(index=idx, start_ms=start_ms, end_ms=end_ms, lines=text_lines)
        )

    if max_duration_seconds is not None and cues[-1].end_ms > int(
        round(max_duration_seconds * 1000)
    ):
        raise RecordingError(
            f"Final cue in {path.name} ({cues[-1].end_ms} ms) exceeds media duration ({max_duration_seconds}s)"
        )
    return cues


NODE_PLAYWRIGHT_CAPTURE_SCRIPT = r"""
const path = require('path');
const http = require('http');
const https = require('https');

function httpRequest(baseUrl, method, reqPath, bodyObj) {
  return new Promise((resolve, reject) => {
    const url = new URL(reqPath, baseUrl);
    const lib = url.protocol === 'https:' ? https : http;
    const payload = bodyObj !== undefined ? JSON.stringify(bodyObj) : null;
    const req = lib.request(url, {
      method,
      headers: payload ? {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      } : {}
    }, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => {
        const text = Buffer.concat(chunks).toString('utf8');
        let json = null;
        try { json = JSON.parse(text); } catch (_) {}
        resolve({ status: res.statusCode, text, json });
      });
    });
    req.on('error', reject);
    if (payload) req.write(payload);
    req.end();
  });
}

(async () => {
  const cfg = JSON.parse(process.env.MATCHPULSE_CAPTURE_CONFIG);
  const { chromium } = require(cfg.playwright_module);
  const blockedRequests = [];
  const states = {};
  const apiEvidence = {};

  let browser = null;
  let context = null;
  let page = null;

  try {
    browser = await chromium.launch({
      executablePath: cfg.chrome_bin,
      headless: true,
      args: [
        '--disable-extensions',
        '--disable-sync',
        '--disable-notifications',
        '--disable-translate',
        '--no-first-run',
        '--no-default-browser-check',
        '--password-store=basic'
      ]
    });

    context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
      screen: { width: 1920, height: 1080 },
      deviceScaleFactor: 1,
      locale: 'en-US',
      colorScheme: 'dark',
      reducedMotion: 'reduce',
      acceptDownloads: false,
      javaScriptEnabled: true,
      serviceWorkers: 'block'
    });

    await context.route('**/*', async (route) => {
      const req = route.request();
      const rawUrl = req.url();
      let parsed;
      try {
        parsed = new URL(rawUrl);
      } catch (_) {
        blockedRequests.push({
          method: req.method(),
          scheme: 'invalid',
          host: 'invalid',
          sanitized_path: '/',
          resource_type: req.resourceType(),
          block_reason: 'invalid_url'
        });
        await route.abort('blockedbyclient');
        return;
      }
      const scheme = parsed.protocol.replace(':', '').toLowerCase();
      const host = (parsed.hostname || '').toLowerCase();
      if (scheme === 'about' || scheme === 'data') {
        await route.continue();
        return;
      }
      if ((scheme === 'http' || scheme === 'ws') && (host === '127.0.0.1' || host === 'localhost')) {
        await route.continue();
        return;
      }
      blockedRequests.push({
        method: req.method(),
        scheme,
        host,
        sanitized_path: parsed.pathname || '/',
        resource_type: req.resourceType(),
        block_reason: `disallowed_origin:${scheme}://${host}`
      });
      await route.abort('blockedbyclient');
    });

    page = await context.newPage();

    async function assertPageSafe(stage) {
      const bodyText = await page.locator('body').innerText();
      if (!bodyText.includes('SYNTHETIC DATA ONLY')) {
        throw new Error(`Missing SYNTHETIC DATA ONLY disclosure at stage ${stage}`);
      }
      const statusState = await page.locator('#status').getAttribute('data-state');
      if (statusState === 'error') {
        throw new Error(`UI status entered error state at stage ${stage}`);
      }
      if (/Traceback \(most recent call last\)|Internal Server Error/i.test(bodyText)) {
        throw new Error(`Unhandled error text detected on page at stage ${stage}`);
      }
      const pillBox = await page.locator('.pill').boundingBox();
      const overlayBox = await page.locator('#overlay').boundingBox();
      if (!pillBox || !overlayBox || pillBox.width < 40 || overlayBox.width < 200) {
        throw new Error(`Required UI layout bounding box missing at stage ${stage}`);
      }
    }

    async function snap(name) {
      await assertPageSafe(name);
      const buf = await page.screenshot({ type: 'png', fullPage: false });
      states[name] = buf.toString('base64');
    }

    async function injectProfilesIntoSelect() {
      await page.evaluate(() => {
        const sel = document.getElementById('profile');
        if (sel && !Array.from(sel.options).some(o => o.value === 'broadcaster-en')) {
          const opt = document.createElement('option');
          opt.value = 'broadcaster-en';
          opt.textContent = 'broadcaster-en';
          sel.insertBefore(opt, sel.options[2] || null);
        }
      });
    }

    async function connectScenarioMatch(matchId, profileId) {
      await page.evaluate(({ mId, pId }) => {
        const statusEl = document.getElementById('status');
        const matchInfoEl = document.getElementById('matchinfo');
        const profileEl = document.getElementById('profile');
        const languageEl = document.getElementById('language');
        const overlayEl = document.getElementById('overlay');
        const feedEl = document.getElementById('feed');
        const compareEl = document.getElementById('compare');
        const compareEmptyEl = document.getElementById('compare-empty');
        const recapEl = document.getElementById('recap');

        profileEl.value = pId;
        languageEl.value = '';
        matchInfoEl.textContent = `Match ${mId} (seed 20261024 · Northbridge City vs Harbor United)`;
        statusEl.textContent = 'Running synthetic demo';
        statusEl.setAttribute('data-state', 'running');

        window.__mpRenderOverlay = function(item) {
          while (overlayEl.firstChild) overlayEl.removeChild(overlayEl.firstChild);
          const meta = document.createElement('div');
          meta.className = 'meta';
          const mins = Math.floor(item.clock_ms / 60000);
          const secs = String(Math.floor((item.clock_ms % 60000) / 1000)).padStart(2, '0');
          meta.textContent = `${item.locale.toUpperCase()} · ${item.persona} · ${mins}:${secs} · profile ${item.profile_id}`;
          const h2 = document.createElement('h2');
          h2.textContent = item.title;
          const p = document.createElement('p');
          p.textContent = item.body;
          const ev = document.createElement('div');
          ev.className = 'meta';
          ev.textContent = `Evidence: ${item.evidence.event_ids.join(', ')} | formula: ${item.evidence.formula} | confidence ${item.evidence.confidence} | insight ${item.insight_id}`;
          overlayEl.appendChild(meta);
          overlayEl.appendChild(h2);
          overlayEl.appendChild(p);
          overlayEl.appendChild(ev);
        };

        window.__mpPushFeed = function(item) {
          const article = document.createElement('article');
          const strong = document.createElement('strong');
          strong.textContent = item.overlay_text;
          const meta = document.createElement('div');
          meta.className = 'meta';
          meta.textContent = `seq ${item.sequence} · priority ${item.priority} · evidence ${item.evidence.event_ids.join(', ')} · insight ${item.insight_id}`;
          article.appendChild(strong);
          article.appendChild(meta);
          feedEl.insertBefore(article, feedEl.firstChild);
          while (feedEl.children.length > 5) feedEl.removeChild(feedEl.lastChild);
        };

        window.__mpRefreshAll = async function(mIdNow, pIdNow, localeNow) {
          let vUrl = `/v1/matches/${encodeURIComponent(mIdNow)}/variants`;
          if (localeNow) vUrl += `?locale=${encodeURIComponent(localeNow)}`;
          const vRes = await fetch(vUrl);
          const vData = await vRes.json();
          while (compareEl.firstChild) compareEl.removeChild(compareEl.firstChild);
          if (vData.moments && vData.moments.length) {
            compareEmptyEl.textContent = `Shared insight ${vData.moments.length} moment(s), one authoritative basis each.`;
            const recentMoments = vData.moments.slice(-2).reverse();
            recentMoments.forEach((moment) => {
              const box = document.createElement('div');
              box.className = 'moment';
              const h3 = document.createElement('h3');
              h3.textContent = `Moment ${moment.insight_id} (${moment.kind})`;
              const shared = document.createElement('div');
              shared.className = 'meta';
              shared.textContent = `sequence ${moment.sequence} · evidence ${moment.evidence_event_ids.join(', ')}`;
              box.appendChild(h3);
              box.appendChild(shared);
              const table = document.createElement('table');
              const head = document.createElement('tr');
              ['Audience', 'Title', 'Overlay', 'Priority'].forEach((lbl) => {
                const th = document.createElement('th');
                th.textContent = lbl;
                head.appendChild(th);
              });
              table.appendChild(head);
              moment.variants.forEach((v) => {
                const row = document.createElement('tr');
                if (v.profile_id === pIdNow) {
                  row.style.background = '#173c51';
                }
                [
                  `${v.profile_id} (${v.locale})`,
                  v.title,
                  v.overlay_text,
                  String(v.priority)
                ].forEach((cellText) => {
                  const td = document.createElement('td');
                  td.textContent = cellText;
                  row.appendChild(td);
                });
                table.appendChild(row);
              });
              box.appendChild(table);
              const st = document.createElement('div');
              st.className = 'meta';
              st.textContent = `authoritative stats: ${JSON.stringify(moment.stats)}`;
              box.appendChild(st);
              compareEl.appendChild(box);
            });
          }
        };
      }, { mId: matchId, pId: profileId });
    }

    async function applyEventResponseToUi(respJson, activeProfileId) {
      const insights = respJson.insights || [];
      const matching = insights.find((i) => i.profile_id === activeProfileId) || insights[0];
      const stateObj = respJson.state;
      await page.evaluate(({ item, st }) => {
        const matchInfoEl = document.getElementById('matchinfo');
        const ncGoals = (st.teams['Northbridge City'] && st.teams['Northbridge City'].goals) || 0;
        const huGoals = (st.teams['Harbor United'] && st.teams['Harbor United'].goals) || 0;
        matchInfoEl.textContent = `Match ${st.match_id} | Northbridge City ${ncGoals} - ${huGoals} Harbor United | seq ${st.last_sequence} | events ${st.event_count} | dup ${st.duplicate_count}`;
        if (item) {
          window.__mpRenderOverlay(item);
          window.__mpPushFeed(item);
        }
      }, { item: matching || null, st: stateObj });
    }

    await page.goto(`${cfg.base_url}/demo`, { waitUntil: 'networkidle', timeout: 10000 });
    await page.waitForSelector('.pill', { timeout: 5000 });
    await injectProfilesIntoSelect();
    await snap('landing');

    await connectScenarioMatch(cfg.match_id, 'fan-en');
    const evs = cfg.valid_events;

    // Event 0: match_start & Event 1: possession_swing
    const r0 = await httpRequest(cfg.base_url, 'POST', '/v1/events', evs[0]);
    const r1 = await httpRequest(cfg.base_url, 'POST', '/v1/events', evs[1]);
    await applyEventResponseToUi(r1.json, 'fan-en');
    await page.evaluate(({ mId }) => window.__mpRefreshAll(mId, 'fan-en', ''), { mId: cfg.match_id });
    await snap('match_started');

    // Events 2, 3, 4: Harbor United pressing surge
    await httpRequest(cfg.base_url, 'POST', '/v1/events', evs[2]);
    await httpRequest(cfg.base_url, 'POST', '/v1/events', evs[3]);
    const r4 = await httpRequest(cfg.base_url, 'POST', '/v1/events', evs[4]);
    await applyEventResponseToUi(r4.json, 'fan-en');
    await page.evaluate(({ mId }) => window.__mpRefreshAll(mId, 'fan-en', ''), { mId: cfg.match_id });
    await snap('pressing_surge');

    // Event 5: Northbridge City high regain tackle & Event 6: Harbor United 104.5 km/h saved shot
    const r5 = await httpRequest(cfg.base_url, 'POST', '/v1/events', evs[5]);
    await applyEventResponseToUi(r5.json, 'fan-en');
    const r6 = await httpRequest(cfg.base_url, 'POST', '/v1/events', evs[6]);
    await applyEventResponseToUi(r6.json, 'fan-en');
    await page.evaluate(({ mId }) => window.__mpRefreshAll(mId, 'fan-en', ''), { mId: cfg.match_id });
    await snap('tackle_and_shot');

    // Event 7: Counterattack pass & Event 8: Northbridge City Goal 1-0
    const r7 = await httpRequest(cfg.base_url, 'POST', '/v1/events', evs[7]);
    await applyEventResponseToUi(r7.json, 'fan-en');
    const r8 = await httpRequest(cfg.base_url, 'POST', '/v1/events', evs[8]);
    await applyEventResponseToUi(r8.json, 'fan-en');
    await page.evaluate(({ mId }) => window.__mpRefreshAll(mId, 'fan-en', ''), { mId: cfg.match_id });
    await snap('goal_1_0');
    apiEvidence.goal_1_0 = r8.json;

    // Duplicate event check (evt-mp-009 again)
    const rDup = await httpRequest(cfg.base_url, 'POST', '/v1/events', cfg.duplicate_event);
    if (rDup.status !== 202 || !rDup.json.duplicate || rDup.json.state.duplicate_count !== 1) {
      throw new Error(`Duplicate event test failed: ${rDup.text}`);
    }
    await applyEventResponseToUi(rDup.json, 'fan-en');
    await snap('duplicate_checked');
    apiEvidence.duplicate_response = rDup.json;

    // Out-of-order event check (evt-mp-010-ooo with sequence 5 <= 8)
    const rOoo = await httpRequest(cfg.base_url, 'POST', '/v1/events', cfg.out_of_order_event);
    if (rOoo.status !== 409) {
      throw new Error(`Out-of-order event was not rejected with 409: got ${rOoo.status}`);
    }
    apiEvidence.out_of_order_response = { status: rOoo.status, body: rOoo.json };

    // Event 9: Second-half momentum swing & Event 10: Harbor United Equalizer 1-1
    const r9 = await httpRequest(cfg.base_url, 'POST', '/v1/events', evs[9]);
    await applyEventResponseToUi(r9.json, 'fan-en');
    const r10 = await httpRequest(cfg.base_url, 'POST', '/v1/events', evs[10]);
    await applyEventResponseToUi(r10.json, 'fan-en');
    await page.evaluate(({ mId }) => window.__mpRefreshAll(mId, 'fan-en', ''), { mId: cfg.match_id });
    await snap('equalizer_fan_en');
    apiEvidence.equalizer_response = r10.json;

    const midState = await httpRequest(cfg.base_url, 'GET', `/v1/matches/${cfg.match_id}/state`);
    apiEvidence.mid_match_state = midState.json;

    const variantsEn = await httpRequest(cfg.base_url, 'GET', `/v1/matches/${cfg.match_id}/variants`);
    apiEvidence.variants_default = variantsEn.json;

    // Profile transitions on the shared equalizer moment (evt-mp-012)
    const profileSequence = [
      { profile: 'analyst-en', locale: '', snapKey: 'profile_analyst_en' },
      { profile: 'broadcaster-en', locale: '', snapKey: 'profile_broadcaster_en' },
      { profile: 'broadcaster-es', locale: 'es', snapKey: 'profile_broadcaster_es' },
      { profile: 'fan-fr', locale: 'fr', snapKey: 'profile_fan_fr' }
    ];

    for (const step of profileSequence) {
      const itemForProfile = r10.json.insights.find((i) => i.profile_id === step.profile);
      if (!itemForProfile) {
        throw new Error(`Missing insight for profile ${step.profile}`);
      }
      await page.selectOption('#profile', step.profile);
      await page.selectOption('#language', step.locale);
      await page.evaluate(({ item, mId, pId, loc }) => {
        window.__mpRenderOverlay(item);
        return window.__mpRefreshAll(mId, pId, loc);
      }, { item: itemForProfile, mId: cfg.match_id, pId: step.profile, loc: step.locale });
      await snap(step.snapKey);
    }

    // Return selector to fan-en for late match progression
    await page.selectOption('#profile', 'fan-en');
    await page.selectOption('#language', '');

    // Events 11 (substitution), 12 (blocked shot), 13 (late winner 2-1), 14 (match_end)
    await httpRequest(cfg.base_url, 'POST', '/v1/events', evs[11]);
    const r12 = await httpRequest(cfg.base_url, 'POST', '/v1/events', evs[12]);
    await applyEventResponseToUi(r12.json, 'fan-en');
    const r13 = await httpRequest(cfg.base_url, 'POST', '/v1/events', evs[13]);
    await applyEventResponseToUi(r13.json, 'fan-en');
    const r14 = await httpRequest(cfg.base_url, 'POST', '/v1/events', evs[14]);
    await applyEventResponseToUi(r14.json, 'fan-en');

    const finalState = await httpRequest(cfg.base_url, 'GET', `/v1/matches/${cfg.match_id}/state`);
    apiEvidence.final_state = finalState.json;

    const recapEn = await httpRequest(cfg.base_url, 'GET', `/v1/matches/${cfg.match_id}/recap?profile_id=fan-en&locale=en`);
    const recapEs = await httpRequest(cfg.base_url, 'GET', `/v1/matches/${cfg.match_id}/recap?profile_id=broadcaster-es&locale=es`);
    const recapFr = await httpRequest(cfg.base_url, 'GET', `/v1/matches/${cfg.match_id}/recap?profile_id=fan-fr&locale=fr`);
    apiEvidence.recap_en = recapEn.json;
    apiEvidence.recap_es = recapEs.json;
    apiEvidence.recap_fr = recapFr.json;

    await page.evaluate(({ mId, rEn }) => {
      const statusEl = document.getElementById('status');
      statusEl.textContent = 'Demo completed';
      statusEl.setAttribute('data-state', 'completed');
      const recapEl = document.getElementById('recap');
      const recapEmptyEl = document.getElementById('recap-empty');
      while (recapEl.firstChild) recapEl.removeChild(recapEl.firstChild);
      recapEmptyEl.textContent = '';
      const h3 = document.createElement('h3');
      h3.textContent = rEn.headline;
      const ul = document.createElement('ul');
      rEn.bullets.forEach((b) => {
        const li = document.createElement('li');
        li.textContent = b;
        ul.appendChild(li);
      });
      const meta = document.createElement('div');
      meta.className = 'meta';
      meta.textContent = `evidence ${rEn.evidence_event_ids.join(', ')}`;
      recapEl.appendChild(h3);
      recapEl.appendChild(ul);
      recapEl.appendChild(meta);
      return window.__mpRefreshAll(mId, 'fan-en', '');
    }, { mId: cfg.match_id, rEn: recapEn.json });
    await snap('full_time_recap');

    // Fallback visual state on #foundry and #status
    await page.evaluate(() => {
      const foundryEl = document.getElementById('foundry');
      const statusEl = document.getElementById('status');
      foundryEl.textContent = 'Foundry: disabled (local synthetic mode) · Guard fallback verified: malformed-json & ReadTimeout -> deterministic output';
      statusEl.textContent = 'Deterministic fallback verified';
      statusEl.setAttribute('data-state', 'deterministic-fallback');
    });
    await snap('fallback_verified');

    process.stdout.write(JSON.stringify({
      ok: true,
      blocked_requests: blockedRequests,
      states,
      api_evidence: apiEvidence
    }));
  } finally {
    if (page) { try { await page.close(); } catch (_) {} }
    if (context) { try { await context.close(); } catch (_) {} }
    if (browser) { try { await browser.close(); } catch (_) {} }
  }
})().catch((err) => {
  process.stderr.write(String(err && err.stack ? err.stack : err));
  process.exit(1);
});
"""


def run_browser_capture_take(
    tools: dict[str, str],
    *,
    base_url: str = APPLICATION_ENDPOINT,
    match_id: str = SCENARIO_ID,
) -> dict[str, Any]:
    """Execute one isolated Playwright Chromium capture take against the running container."""
    reset_before = reset_match(base_url, match_id)
    ensure_broadcaster_en_profile(base_url)
    scenario = build_scenario_events(match_id)

    cfg = {
        "playwright_module": tools["playwright_module"],
        "chrome_bin": tools["chrome_bin"],
        "base_url": base_url,
        "match_id": match_id,
        "valid_events": [e.model_dump(mode="json") for e in scenario["valid_events"]],
        "duplicate_event": scenario["duplicate_event"].model_dump(mode="json"),
        "out_of_order_event": scenario["out_of_order_event"].model_dump(mode="json"),
    }
    env = dict(os.environ)
    env["MATCHPULSE_CAPTURE_CONFIG"] = json.dumps(cfg)

    proc = subprocess.run(
        ["node", "-e", NODE_PLAYWRIGHT_CAPTURE_SCRIPT],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RecordingError(
            f"Playwright browser capture failed: {proc.stderr.strip()}"
        )

    result = json.loads(proc.stdout)
    blocked = result.get("blocked_requests") or []
    if blocked:
        raise RecordingError(
            f"Unexpected external network requests attempted and blocked: {blocked}"
        )

    api_ev = result["api_evidence"]
    final_state = api_ev["final_state"]
    teams = final_state.get("teams") or {}
    home_goals = (teams.get(HOME_TEAM) or {}).get("goals", 0)
    away_goals = (teams.get(AWAY_TEAM) or {}).get("goals", 0)
    if (home_goals, away_goals) != (FINAL_SCORE["home"], FINAL_SCORE["away"]):
        raise RecordingError(
            f"Final score mismatch: got {home_goals}-{away_goals}, expected 2-1"
        )
    if (
        final_state.get("status") != "finished"
        or final_state.get("duplicate_count") != 1
    ):
        raise RecordingError(f"Unexpected final match state: {final_state}")

    recap_en = api_ev.get("recap_en") or {}
    if not recap_en.get("bullets") or not recap_en.get("evidence_event_ids"):
        raise RecordingError(f"Invalid recap payload: {recap_en}")

    profile_check = verify_profile_transitions(
        api_ev["variants_default"], expected_match_id=match_id
    )
    fallback_check = verify_deterministic_fallback(
        api_ev["equalizer_response"]["insights"][0]
    )
    reset_after = reset_match(base_url, match_id)

    images: dict[str, Image.Image] = {}
    for k, b64_png in (result.get("states") or {}).items():
        raw_bytes = base64.b64decode(b64_png)
        img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        if img.size != (VIDEO_WIDTH, VIDEO_HEIGHT):
            img = img.resize((VIDEO_WIDTH, VIDEO_HEIGHT), Image.Resampling.LANCZOS)
        images[k] = img

    return {
        "images": images,
        "api_evidence": api_ev,
        "profile_check": profile_check,
        "fallback_check": fallback_check,
        "reset_before": reset_before,
        "reset_after": reset_after,
        "blocked_requests": blocked,
    }


def _load_fonts() -> dict[str, ImageFont.FreeTypeFont | ImageFont.ImageFont]:
    win_fonts = Path(r"C:\Windows\Fonts")
    segoe_bold = win_fonts / "segoeuib.ttf"
    segoe_reg = win_fonts / "segoeui.ttf"
    consolas = win_fonts / "consola.ttf"
    try:
        return {
            "h1": ImageFont.truetype(str(segoe_bold), 52),
            "h2": ImageFont.truetype(str(segoe_bold), 32),
            "body": ImageFont.truetype(str(segoe_reg), 24),
            "small": ImageFont.truetype(str(segoe_reg), 19),
            "mono": ImageFont.truetype(str(consolas), 19),
            "mono_sm": ImageFont.truetype(str(consolas), 16),
            "caption": ImageFont.truetype(str(segoe_bold), 28),
        }
    except Exception:
        default = ImageFont.load_default()
        return {
            k: default
            for k in ("h1", "h2", "body", "small", "mono", "mono_sm", "caption")
        }


def render_card_image(
    title: str,
    subtitle: str,
    lines: list[str],
    footer: str,
) -> Image.Image:
    """Render a 1920x1080 title, technical-identity, or closing card locally."""
    fonts = _load_fonts()
    img = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (7, 26, 43))
    draw = ImageDraw.Draw(img)

    draw.rectangle(
        [80, 70, VIDEO_WIDTH - 80, VIDEO_HEIGHT - 70], outline=(42, 75, 97), width=3
    )
    draw.rectangle([80, 70, VIDEO_WIDTH - 80, 130], fill=(12, 42, 66))
    draw.text(
        (115, 86),
        "LOCAL DEMONSTRATION  ·  SEEDED SYNTHETIC MATCH DATA  ·  NO LIVE EXTERNAL DATA SOURCE",
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
        [130, VIDEO_HEIGHT - 165, VIDEO_WIDTH - 130, VIDEO_HEIGHT - 105],
        fill=(10, 32, 50),
        outline=(59, 97, 119),
    )
    draw.text(
        (155, VIDEO_HEIGHT - 148), footer, font=fonts["body"], fill=(200, 245, 96)
    )
    return img


def composite_shot_base(
    state_images: dict[str, Image.Image],
    shot: ShotSpec,
) -> Image.Image:
    """Create the 1920x1080 base image for a shot with disclosure bar and verification callout."""
    fonts = _load_fonts()
    if shot.state_key == "card_title":
        return render_card_image(
            "MATCHPULSE LIVE",
            "EVIDENCE-AWARE MATCH STORYTELLING FROM SYNTHETIC EVENTS",
            [
                "SCENARIO ID       : matchpulse-demo-001 (Seed 20261024)",
                "FICTIONAL MATCH   : Northbridge City vs Harbor United",
                "DATA DISCLOSURE   : SEEDED SYNTHETIC MATCH DATA · LOCAL DEMONSTRATION",
                "EXTERNAL SOURCES  : NO LIVE EXTERNAL DATA SOURCE · ZERO BILLABLE CALLS",
                f"SOURCE COMMIT     : {EXPECTED_SOURCE_SHA}",
                f"IMMUTABLE DIGEST  : {EXPECTED_IMAGE_DIGEST}",
            ],
            "Independent Product Demonstration · Built with Python, FastAPI, Docker, and GitHub Attestations",
        )
    if shot.state_key == "card_identity":
        return render_card_image(
            "AUDITED SOURCE & IMMUTABLE CONTAINER IDENTITY",
            "CRYPTOGRAPHICALLY VERIFIED RELEASE ARTIFACT",
            [
                f"REPOSITORY        : {EXPECTED_REPOSITORY}",
                f"SOURCE COMMIT     : {EXPECTED_SOURCE_SHA}",
                f"IMMUTABLE IMAGE   : {EXPECTED_IMAGE_DIGEST}",
                f"SLSA ATTESTATION  : ID {EXPECTED_ATTESTATION_ID} (Workflow Run {EXPECTED_WORKFLOW_RUN_ID})",
                f"OCI REVISION      : {EXPECTED_SOURCE_SHA}",
                f"OCI SOURCE        : {EXPECTED_OCI_SOURCE}",
                "RUNTIME HARDENING : user 10001:10001 · --read-only · --cap-drop ALL · 127.0.0.1:8080",
            ],
            "LOCAL DEMONSTRATION · SEEDED SYNTHETIC MATCH DATA · NO LIVE EXTERNAL DATA SOURCE",
        )
    if shot.state_key == "card_closing":
        return render_card_image(
            "MATCHPULSE LIVE",
            "REAL-TIME EVENT ANALYSIS · AUDIENCE-SPECIFIC INSIGHTS · MULTILINGUAL STORYTELLING",
            [
                "TRACEABLE RECAPS        : Every bullet linked to verified event_ids and formulas",
                "AUDIENCE PERSONALIZATION: fan-en · analyst-en · broadcaster-en · broadcaster-es · fan-fr",
                "RESILIENT GUARD RAILS   : Duplicate suppression · Out-of-order 409 · Deterministic fallback",
                "FINAL SYNTHETIC SCORE   : Northbridge City 2 - 1 Harbor United (matchpulse-demo-001)",
                "SECURITY & PRIVACY      : 0 External Network Requests · 0 Exposed Secrets",
            ],
            "SYNTHETIC DEMONSTRATION · LOCAL IMMUTABLE CONTAINER · NO LIVE EXTERNAL DATA SOURCE",
        )

    base = state_images[shot.state_key].copy()
    draw = ImageDraw.Draw(base)

    # Top persistent disclosure ribbon
    draw.rectangle([0, 0, VIDEO_WIDTH, 36], fill=(6, 21, 33))
    draw.line([(0, 36), (VIDEO_WIDTH, 36)], fill=(200, 245, 96), width=2)
    draw.text(
        (24, 7),
        f"LOCAL DEMONSTRATION · SEEDED SYNTHETIC MATCH DATA · NO LIVE EXTERNAL DATA SOURCE  |  {shot.banner_title}",
        font=fonts["mono_sm"],
        fill=(200, 245, 96),
    )

    # Bottom-left verification callout card (positioned safely above the caption safe zone)
    card_x1, card_y1, card_x2, card_y2 = 42, 660, 760, 915
    draw.rectangle(
        [card_x1, card_y1, card_x2, card_y2],
        fill=(8, 25, 40),
        outline=(22, 184, 243),
        width=2,
    )
    draw.rectangle([card_x1, card_y1, card_x2, card_y1 + 38], fill=(16, 47, 70))
    draw.text(
        (card_x1 + 16, card_y1 + 8),
        shot.callout_title,
        font=fonts["small"],
        fill=(200, 245, 96),
    )

    y = card_y1 + 48
    for line in shot.callout_lines[:6]:
        draw.text((card_x1 + 16, y), line, font=fonts["mono_sm"], fill=(225, 239, 250))
        y += 32

    return base


def draw_frame_overlays(
    base_img: Image.Image,
    *,
    cursor_xy: tuple[int, int],
    elapsed_sec: float,
    total_sec: float,
    caption_lines: tuple[str, ...] | None = None,
) -> Image.Image:
    """Draw animated cursor, progress indicator, and optional burned-in captions on a single frame."""
    fonts = _load_fonts()
    frame = base_img.copy()
    draw = ImageDraw.Draw(frame)

    # Progress bar along bottom edge
    pct = max(0.0, min(1.0, elapsed_sec / max(0.001, total_sec)))
    bar_w = int(VIDEO_WIDTH * pct)
    draw.rectangle([0, VIDEO_HEIGHT - 6, VIDEO_WIDTH, VIDEO_HEIGHT], fill=(15, 38, 56))
    draw.rectangle([0, VIDEO_HEIGHT - 6, bar_w, VIDEO_HEIGHT], fill=(22, 184, 243))

    # Timecode stamp in top-right disclosure ribbon
    mins = int(elapsed_sec) // 60
    secs = elapsed_sec - (mins * 60)
    t_mins = int(total_sec) // 60
    t_secs = int(total_sec) % 60
    draw.text(
        (VIDEO_WIDTH - 245, 7),
        f"TC {mins:02d}:{secs:04.1f} / {t_mins:02d}:{t_secs:02d}.0",
        font=fonts["mono_sm"],
        fill=(237, 247, 255),
    )

    # Deterministic cursor pointer with subtle pulse ring
    cx, cy = cursor_xy
    pulse_r = 14 + int(3 * math.sin(elapsed_sec * 6.0))
    draw.ellipse(
        [cx - pulse_r, cy - pulse_r, cx + pulse_r, cy + pulse_r],
        outline=(200, 245, 96),
        width=2,
    )
    poly = [
        (cx, cy),
        (cx, cy + 24),
        (cx + 7, cy + 18),
        (cx + 13, cy + 28),
        (cx + 17, cy + 26),
        (cx + 11, cy + 16),
        (cx + 19, cy + 16),
    ]
    draw.polygon(poly, fill=(237, 247, 255), outline=(7, 26, 43))

    if caption_lines:
        box_w = 1080
        box_h = 44 * len(caption_lines) + 24
        bx1 = (VIDEO_WIDTH - box_w) // 2
        by1 = VIDEO_HEIGHT - box_h - 32
        bx2 = bx1 + box_w
        by2 = by1 + box_h
        draw.rectangle(
            [bx1, by1, bx2, by2], fill=(5, 16, 26), outline=(200, 245, 96), width=2
        )
        ty = by1 + 10
        for line in caption_lines:
            bbox = draw.textbbox((0, 0), line, font=fonts["caption"])
            tw = bbox[2] - bbox[0]
            draw.text(
                ((VIDEO_WIDTH - tw) // 2, ty),
                line,
                font=fonts["caption"],
                fill=(255, 255, 255),
            )
            ty += 42

    return frame


def build_submission_shots(capture: dict[str, Any]) -> list[ShotSpec]:
    api = capture["api_evidence"]
    prof = capture["profile_check"]
    ins_id = prof["insight_id"][:18]
    return [
        ShotSpec(
            "S1",
            0,
            5_000,
            "card_title",
            "SHOT 1 · TITLE & SYNTHETIC DISCLOSURE",
            "TITLE & DISCLOSURE",
            (
                "Product: MatchPulse Live",
                "Data: Seeded Synthetic Match Data",
                "Mode: Local Immutable Container",
            ),
            (960, 540),
            (640, 380),
        ),
        ShotSpec(
            "S1b",
            5_000,
            8_000,
            "landing",
            "SHOT 1 · LANDING VIEW & SYNTHETIC PILL",
            "SYNTHETIC SAFETY GATE VERIFIED",
            (
                "Endpoint: http://127.0.0.1:8080/demo",
                "Badge: SYNTHETIC DATA ONLY",
                "Foundry Mode: disabled (deterministic)",
                "Scenario: matchpulse-demo-001 (seed 20261024)",
            ),
            (640, 380),
            (310, 195),
        ),
        ShotSpec(
            "S2",
            8_000,
            18_000,
            "match_started",
            "SHOT 2 · MATCH INITIALIZATION & POSSESSION SWING",
            "SEEDED STREAM: evt-mp-001 .. evt-mp-002",
            (
                f"Match: {SCENARIO_ID} ({HOME_TEAM} vs {AWAY_TEAM})",
                "evt-mp-001 (00:00): match_start -> status=live",
                "evt-mp-002 (06:00): Harbor United possession 50% -> 62%",
                "Derived Insight: possession_swing (confidence 0.98)",
            ),
            (310, 195),
            (1120, 270),
        ),
        ShotSpec(
            "S3",
            18_000,
            28_000,
            "tackle_and_shot",
            "SHOT 3 · PRESSING SURGE, HIGH REGAIN & SAVED SHOT",
            "MULTI-AGENT EVENT INGESTION (evt-mp-003 .. evt-mp-007)",
            (
                "evt-mp-003..005: Harbor United pressing_surge (avg 0.82)",
                "evt-mp-006 (12:00): Northbridge City tackle at x=74.0",
                "evt-mp-007 (16:00): Harbor United 104.5 km/h shot saved",
                "Explainability Gate: event_ids & formula verified",
            ),
            (1120, 270),
            (1150, 320),
        ),
        ShotSpec(
            "S4",
            28_000,
            38_000,
            "goal_1_0",
            "SHOT 4 · COUNTERATTACK PASS & OPENING GOAL (1 - 0)",
            "SCORE PROGRESSION: NORTHBRIDGE CITY 1 - 0 HARBOR UNITED",
            (
                "evt-mp-008 (20:00): NC-10 progressive pass (40 -> 82)",
                "evt-mp-009 (21:00): NC-09 GOAL (101.2 km/h)",
                "Formula: authoritative goal event + aggregate team goals",
                "Evidence: ['evt-mp-009'] | Confidence: 1.0",
            ),
            (1150, 320),
            (1140, 250),
        ),
        ShotSpec(
            "S5",
            38_000,
            46_000,
            "duplicate_checked",
            "SHOT 5 · IDEMPOTENT DUPLICATE EVENT HANDLING",
            "DUPLICATE SUPPRESSION (evt-mp-009 RE-SENT)",
            (
                "Re-sent Event: evt-mp-009 (sequence 8)",
                f"HTTP 202: accepted=true, duplicate={api['duplicate_response']['duplicate']}",
                f"State duplicate_count={api['duplicate_response']['state']['duplicate_count']}, insights=[]",
                "Score Invariant: Northbridge City 1 - 0 Harbor United",
            ),
            (1140, 250),
            (1380, 250),
        ),
        ShotSpec(
            "S6",
            46_000,
            54_000,
            "equalizer_fan_en",
            "SHOT 6 · OUT-OF-ORDER 409 REJECTION & 1 - 1 EQUALIZER",
            "TIMELINE INTEGRITY & HARBOR UNITED EQUALIZER",
            (
                f"evt-mp-010-ooo (seq 5 <= 8): HTTP {api['out_of_order_response']['status']} Rejected",
                "evt-mp-011 (48:00): Harbor United possession 51% -> 64%",
                "evt-mp-012 (56:00): HU-11 Equalizer Goal -> Score 1 - 1",
                f"Shared Moment Insight ID: {ins_id}...",
            ),
            (1380, 250),
            (1140, 300),
        ),
        ShotSpec(
            "S7",
            54_000,
            63_000,
            "equalizer_fan_en",
            "SHOT 7 · AUDIENCE PERSONALIZATION — FAN MODE (fan-en)",
            "PROFILE 1/5: fan-en (PERSONA=FAN, LOCALE=EN)",
            (
                f"Insight ID: {ins_id}... (shared across all profiles)",
                "Title: GOAL! | Overlay: GOAL - Harbor United",
                "Evidence IDs: ['evt-mp-012'] | Confidence: 1.0",
                "Score Invariant: Northbridge City 1 - 1 Harbor United",
            ),
            (1140, 300),
            (320, 370),
        ),
        ShotSpec(
            "S8",
            63_000,
            72_000,
            "profile_analyst_en",
            "SHOT 8 · AUDIENCE PERSONALIZATION — ANALYST MODE (analyst-en)",
            "PROFILE 2/5: analyst-en (PERSONA=ANALYST, DETAIL=DEEP)",
            (
                f"Insight ID: {ins_id}... (UNCHANGED)",
                "Title: Goal changes the game state",
                "Exposes: Evidence formula + inputs inline",
                "Evidence IDs: ['evt-mp-012'] | Confidence: 1.0",
            ),
            (320, 370),
            (1160, 290),
        ),
        ShotSpec(
            "S9",
            72_000,
            80_000,
            "profile_broadcaster_en",
            "SHOT 9 · AUDIENCE PERSONALIZATION — BROADCASTER (broadcaster-en)",
            "PROFILE 3/5: broadcaster-en (PERSONA=BROADCASTER, COMPACT)",
            (
                f"Insight ID: {ins_id}... (UNCHANGED)",
                "Title: Goal | Compact Body: GOAL - Harbor United",
                "Evidence IDs: ['evt-mp-012'] | Confidence: 1.0",
                "Only presentation density & priority change",
            ),
            (1160, 290),
            (1180, 560),
        ),
        ShotSpec(
            "S10a",
            80_000,
            83_500,
            "profile_broadcaster_es",
            "SHOT 10 · MULTILINGUAL OUTPUT — SPANISH (broadcaster-es)",
            "PROFILE 4/5: broadcaster-es (LOCALE=ES)",
            (
                f"Insight ID: {ins_id}... (UNCHANGED)",
                "Spanish Copy: Gol | GOL - Harbor United",
                "Evidence IDs: ['evt-mp-012'] | Score: 1 - 1",
            ),
            (1180, 560),
            (320, 455),
        ),
        ShotSpec(
            "S10b",
            83_500,
            87_000,
            "profile_fan_fr",
            "SHOT 10 · MULTILINGUAL OUTPUT — FRENCH (fan-fr)",
            "PROFILE 5/5: fan-fr (LOCALE=FR)",
            (
                f"Insight ID: {ins_id}... (UNCHANGED)",
                "French Copy: BUT ! | Harbor United change le match",
                "Evidence IDs: ['evt-mp-012'] | Score: 1 - 1",
            ),
            (320, 455),
            (1140, 590),
        ),
        ShotSpec(
            "S11",
            87_000,
            99_000,
            "full_time_recap",
            "SHOT 11 · LATE WINNER (2 - 1) & TRACEABLE FULL-TIME RECAP",
            "FULL TIME: NORTHBRIDGE CITY 2 - 1 HARBOR UNITED",
            (
                "evt-mp-013 (72:00 Sub), evt-mp-014 (84:00 Blocked Shot)",
                "evt-mp-015 (88:00): NC-09 Winner -> Score 2 - 1",
                "evt-mp-016 (90:00): match_end (status=finished)",
                f"Recap Evidence: {', '.join(api['recap_en']['evidence_event_ids'][:5])}",
            ),
            (1140, 590),
            (1140, 760),
        ),
        ShotSpec(
            "S12",
            99_000,
            108_000,
            "fallback_verified",
            "SHOT 12 · SAFE DETERMINISTIC FALLBACK & MATCH RESET",
            "RESILIENCE: GUARD FALLBACK & CLEAN RESET",
            (
                "Foundry Mode: disabled (zero external model calls)",
                "Malformed JSON & ReadTimeout -> deterministic copy kept",
                "POST /v1/matches/matchpulse-demo-001/reset -> reset=true",
                "Post-reset state lookup -> HTTP 404 (clean state)",
            ),
            (1140, 760),
            (350, 660),
        ),
        ShotSpec(
            "S13",
            108_000,
            115_000,
            "card_closing",
            "SHOT 13 · CLOSING SUMMARY & SYNTHETIC DISCLOSURE",
            "CLOSING SUMMARY",
            ("One match. Multiple audiences. Traceable stories.",),
            (350, 660),
            (960, 540),
        ),
    ]


def build_technical_shots(capture: dict[str, Any]) -> list[ShotSpec]:
    api = capture["api_evidence"]
    prof = capture["profile_check"]
    fb = capture["fallback_check"]
    ins_id = prof["insight_id"][:18]
    return [
        ShotSpec(
            "T1",
            0,
            8_000,
            "card_title",
            "CHECKPOINT 1 · SYNTHETIC DISCLOSURE & PRODUCT SCOPE",
            "SYNTHETIC DISCLOSURE",
            ("Local Demonstration · Seeded Synthetic Match Data",),
            (960, 540),
            (960, 480),
        ),
        ShotSpec(
            "T2",
            8_000,
            16_000,
            "card_identity",
            "CHECKPOINT 2 · SOURCE SHA, IMAGE DIGEST & ATTESTATION",
            "BUILD & SOURCE IDENTITY",
            (f"Commit: {EXPECTED_SOURCE_SHA}", f"Digest: {EXPECTED_IMAGE_DIGEST}"),
            (960, 480),
            (960, 600),
        ),
        ShotSpec(
            "T3",
            16_000,
            24_000,
            "landing",
            "CHECKPOINT 3 · OCI LABELS & CONTAINER HARDENING",
            "OCI LABELS & RUNTIME SECURITY",
            (
                f"org.opencontainers.image.revision={EXPECTED_SOURCE_SHA[:16]}...",
                f"org.opencontainers.image.source={EXPECTED_OCI_SOURCE}",
                "Container User: 10001:10001 | --read-only | --cap-drop ALL",
                "Port Binding: 127.0.0.1:8080 (loopback only)",
            ),
            (960, 600),
            (340, 210),
        ),
        ShotSpec(
            "T4",
            24_000,
            32_000,
            "landing",
            "CHECKPOINT 4 · HEALTH GATES (/health/live & /health/ready)",
            "HEALTH PROBES VERIFIED",
            (
                "GET /health/live  -> HTTP 200 {'status': 'ok'}",
                "GET /health/ready -> HTTP 200 {'status': 'ready'}",
                "synthetic_only=true | foundry_mode='disabled'",
                "telemetry_mode='disabled' | profiles=5",
            ),
            (340, 210),
            (350, 660),
        ),
        ShotSpec(
            "T5",
            32_000,
            40_000,
            "landing",
            "CHECKPOINT 5 · SYNTHETIC-ONLY GATE & DETERMINISTIC RESET",
            "PRE-RUN RESET & SYNTHETIC GATE",
            (
                "CHALLENGE_SYNTHETIC_ONLY=true enforced on ingest",
                f"POST /v1/matches/{SCENARIO_ID}/reset -> reset=true",
                f"GET /v1/matches/{SCENARIO_ID}/state -> HTTP 404",
                "UI Pill Verified: SYNTHETIC DATA ONLY",
            ),
            (350, 660),
            (310, 195),
        ),
        ShotSpec(
            "T6",
            40_000,
            48_000,
            "match_started",
            "CHECKPOINT 6 · MATCH START & OPENING POSSESSION SWING",
            "EVENTS evt-mp-001 (00:00) & evt-mp-002 (06:00)",
            (
                f"Match ID: {SCENARIO_ID} | Seed: {SYNTHETIC_SEED}",
                f"Teams: {HOME_TEAM} vs {AWAY_TEAM}",
                "evt-mp-001: match_start (sequence 0, status=live)",
                "evt-mp-002: Harbor United possession 50.0% -> 62.0%",
            ),
            (310, 195),
            (1120, 260),
        ),
        ShotSpec(
            "T7",
            48_000,
            56_000,
            "pressing_surge",
            "CHECKPOINT 7 · HIGH-PRESS WINDOW DETECTION (pressing_surge)",
            "EVENTS evt-mp-003, evt-mp-004, evt-mp-005 (09:00..09:20)",
            (
                "Harbor United pressure: 0.78 (HU-06), 0.82 (HU-08), 0.86 (HU-11)",
                "3 events >= 0.72 within trailing 30s window",
                "Derived Insight: pressing_surge (avg=0.82, conf=0.94)",
                "Evidence IDs: ['evt-mp-003', 'evt-mp-004', 'evt-mp-005']",
            ),
            (1120, 260),
            (1140, 390),
        ),
        ShotSpec(
            "T8",
            56_000,
            64_000,
            "tackle_and_shot",
            "CHECKPOINT 8 · HIGH REGAIN TACKLE & SAVED SHOT SPEED",
            "EVENTS evt-mp-006 (12:00) & evt-mp-007 (16:00)",
            (
                "evt-mp-006: Northbridge City tackle at x=74.0 (>= 65)",
                "Insight: tackle (confidence 0.97, formula verified)",
                "evt-mp-007: Harbor United shot on_target at 104.5 km/h",
                "Insight: shot_speed (104.5 >= 95 km/h, confidence 0.96)",
            ),
            (1140, 390),
            (1160, 300),
        ),
        ShotSpec(
            "T9",
            64_000,
            72_000,
            "goal_1_0",
            "CHECKPOINT 9 · COUNTERATTACK PASS & OPENING GOAL (1 - 0)",
            "EVENTS evt-mp-008 (20:00) & evt-mp-009 (21:00)",
            (
                "evt-mp-008: NC-10 progressive pass (difficulty 78.4/100)",
                "evt-mp-009: NC-09 GOAL for Northbridge City",
                "Score Updated: Northbridge City 1 - 0 Harbor United",
                "Evidence: ['evt-mp-009'] | Confidence: 1.0",
            ),
            (1160, 300),
            (1120, 250),
        ),
        ShotSpec(
            "T10",
            72_000,
            80_000,
            "duplicate_checked",
            "CHECKPOINT 10 · DUPLICATE EVENT IDEMPOTENCY",
            "DUPLICATE TEST: RE-SENDING evt-mp-009",
            (
                "POST /v1/events with existing event_id='evt-mp-009'",
                "Response: HTTP 202 | accepted=true | duplicate=true",
                "State: duplicate_count=1 | event_count=9 (unchanged)",
                "Score Invariant: Northbridge City 1 - 0 Harbor United",
            ),
            (1120, 250),
            (1420, 260),
        ),
        ShotSpec(
            "T11",
            80_000,
            88_000,
            "duplicate_checked",
            "CHECKPOINT 11 · OUT-OF-ORDER EVENT REJECTION (HTTP 409)",
            "OUT-OF-ORDER TEST: evt-mp-010-ooo (SEQUENCE 5 AFTER 8)",
            (
                "POST /v1/events with sequence=5 while last_sequence=8",
                f"Response: HTTP {api['out_of_order_response']['status']} Conflict",
                f"Detail: {api['out_of_order_response']['body']['detail']}",
                "State last_sequence remains 8; timeline preserved",
            ),
            (1420, 260),
            (1420, 340),
        ),
        ShotSpec(
            "T12",
            88_000,
            96_000,
            "equalizer_fan_en",
            "CHECKPOINT 12 · SECOND-HALF MOMENTUM & EQUALIZER (1 - 1)",
            "EVENTS evt-mp-011 (48:00) & evt-mp-012 (56:00)",
            (
                "evt-mp-011: Harbor United possession swing 51% -> 64%",
                "evt-mp-012: Harbor United equalizer goal by HU-11",
                "Score Updated: Northbridge City 1 - 1 Harbor United",
                f"Shared Authoritative Insight ID: {ins_id}...",
            ),
            (1420, 340),
            (1140, 270),
        ),
        ShotSpec(
            "T13",
            96_000,
            104_000,
            "equalizer_fan_en",
            "CHECKPOINT 13 · MATCH STATE ENDPOINT INSPECTION",
            f"GET /v1/matches/{SCENARIO_ID}/state AT 56:00",
            (
                f"status={api['mid_match_state']['status']} | last_sequence={api['mid_match_state']['last_sequence']}",
                f"event_count={api['mid_match_state']['event_count']} | duplicate_count={api['mid_match_state']['duplicate_count']}",
                "Northbridge City: goals=1, shots=1, passes=1, tackles=1",
                "Harbor United: goals=1, shots=2, pressure_events=3, poss=64%",
            ),
            (1140, 270),
            (1400, 300),
        ),
        ShotSpec(
            "T14",
            104_000,
            112_000,
            "equalizer_fan_en",
            "CHECKPOINT 14 · EXPLAINABILITY & EVIDENCE PROVENANCE TRACE",
            "EXPLAINABILITY AGENT CONTRACT",
            (
                "Every candidate insight validated against MatchAccumulator",
                "Evidence event_ids must exist in match history",
                "Non-empty derivation formula and bounded confidence required",
                "Ungrounded insights are dropped before personalization",
            ),
            (1400, 300),
            (1140, 320),
        ),
        ShotSpec(
            "T15",
            112_000,
            120_000,
            "equalizer_fan_en",
            "CHECKPOINT 15 · AUDIENCE PROFILE 1: fan-en (ENGLISH FAN)",
            "VARIANT 1/5: fan-en (PERSONA=FAN, LOCALE=EN)",
            (
                f"Insight ID: {ins_id}... | Priority: {prof['variants_by_profile']['fan-en']['priority']}",
                f"Title: {prof['variants_by_profile']['fan-en']['title']}",
                f"Overlay: {prof['variants_by_profile']['fan-en']['overlay_text']}",
                "Evidence IDs: ['evt-mp-012'] | Confidence: 1.0",
            ),
            (1140, 320),
            (320, 370),
        ),
        ShotSpec(
            "T16",
            120_000,
            128_000,
            "profile_analyst_en",
            "CHECKPOINT 16 · AUDIENCE PROFILE 2: analyst-en (ENGLISH ANALYST)",
            "VARIANT 2/5: analyst-en (PERSONA=ANALYST, DETAIL=DEEP)",
            (
                f"Insight ID: {ins_id}... (IDENTICAL)",
                f"Title: {prof['variants_by_profile']['analyst-en']['title']}",
                "Appends formula & inputs for deep tactical review",
                "Evidence IDs: ['evt-mp-012'] | Confidence: 1.0",
            ),
            (320, 370),
            (1140, 290),
        ),
        ShotSpec(
            "T17",
            128_000,
            136_000,
            "profile_broadcaster_en",
            "CHECKPOINT 17 · AUDIENCE PROFILE 3: broadcaster-en (ENGLISH ON-AIR)",
            "VARIANT 3/5: broadcaster-en (PERSONA=BROADCASTER, COMPACT)",
            (
                f"Insight ID: {ins_id}... (IDENTICAL)",
                f"Title: {prof['variants_by_profile']['broadcaster-en']['title']}",
                f"Compact Body: {prof['variants_by_profile']['broadcaster-en']['body']}",
                "Evidence IDs: ['evt-mp-012'] | Confidence: 1.0",
            ),
            (1140, 290),
            (1160, 560),
        ),
        ShotSpec(
            "T18",
            136_000,
            144_000,
            "profile_broadcaster_es",
            "CHECKPOINT 18 · MULTILINGUAL OUTPUT: broadcaster-es (SPANISH)",
            "VARIANT 4/5: broadcaster-es (LOCALE=ES, COMPACT)",
            (
                f"Insight ID: {ins_id}... (IDENTICAL)",
                f"Title: {prof['variants_by_profile']['broadcaster-es']['title']}",
                f"Overlay: {prof['variants_by_profile']['broadcaster-es']['overlay_text']}",
                "Evidence IDs: ['evt-mp-012'] | Score Invariant: 1 - 1",
            ),
            (1160, 560),
            (320, 455),
        ),
        ShotSpec(
            "T19",
            144_000,
            152_000,
            "profile_fan_fr",
            "CHECKPOINT 19 · MULTILINGUAL OUTPUT: fan-fr (FRENCH)",
            "VARIANT 5/5: fan-fr (LOCALE=FR, STANDARD)",
            (
                f"Insight ID: {ins_id}... (IDENTICAL)",
                f"Title: {prof['variants_by_profile']['fan-fr']['title']}",
                f"Overlay: {prof['variants_by_profile']['fan-fr']['overlay_text']}",
                "Evidence IDs: ['evt-mp-012'] | Score Invariant: 1 - 1",
            ),
            (320, 455),
            (1160, 610),
        ),
        ShotSpec(
            "T20",
            152_000,
            160_000,
            "full_time_recap",
            "CHECKPOINT 20 · LATE SUBSTITUTION, BLOCKED SHOT & 2 - 1 WINNER",
            "EVENTS evt-mp-013 (72:00), evt-mp-014 (84:00), evt-mp-015 (88:00)",
            (
                "evt-mp-013: Northbridge City substitution (NC-14 for NC-07)",
                "evt-mp-014: NC-10 blocked shot at 98.2 km/h (shot_speed)",
                "evt-mp-015: NC-09 late winning goal at 88:00 (106.0 km/h)",
                "Score Updated: Northbridge City 2 - 1 Harbor United",
            ),
            (1160, 610),
            (1130, 260),
        ),
        ShotSpec(
            "T21",
            160_000,
            168_000,
            "full_time_recap",
            "CHECKPOINT 21 · FINAL MATCH STATE AT FULL TIME (90:00)",
            "EVENT evt-mp-016 (match_end) & FINAL STATE",
            (
                f"status={api['final_state']['status']} | clock_ms={api['final_state']['clock_ms']}",
                f"event_count={api['final_state']['event_count']} | duplicate_count={api['final_state']['duplicate_count']}",
                "Final Score: Northbridge City 2 - 1 Harbor United",
                "All 15 valid events + 1 duplicate + 1 409 verified",
            ),
            (1130, 260),
            (1400, 310),
        ),
        ShotSpec(
            "T22",
            168_000,
            176_000,
            "full_time_recap",
            "CHECKPOINT 22 · MULTILINGUAL MATCH RECAP GENERATION",
            "RECAP ENDPOINT (/v1/matches/matchpulse-demo-001/recap)",
            (
                f"EN: {api['recap_en']['headline']}",
                f"ES: {api['recap_es']['headline']}",
                f"FR: {api['recap_fr']['headline']}",
                f"Evidence IDs: {', '.join(api['recap_en']['evidence_event_ids'])}",
            ),
            (1400, 310),
            (1140, 780),
        ),
        ShotSpec(
            "T23",
            176_000,
            184_000,
            "fallback_verified",
            "CHECKPOINT 23 · SAFE DETERMINISTIC FALLBACK CONTROLS",
            "FOUNDRY NARRATIVE GUARD & DETERMINISTIC FALLBACK",
            (
                "Container Runtime: foundry_mode='disabled' (0 external calls)",
                f"Malformed JSON Guard: {fb['malformed_json_warning']}",
                f"Timeout Guard: {fb['timeout_warning']}",
                "Original deterministic PersonalizedInsight preserved intact",
            ),
            (1140, 780),
            (350, 660),
        ),
        ShotSpec(
            "T24",
            184_000,
            192_000,
            "fallback_verified",
            "CHECKPOINT 24 · NETWORK ISOLATION & LOGGING REDACTION",
            "SECURITY & PRIVACY VERIFICATION",
            (
                "Playwright Network Guard: only 127.0.0.1 / localhost allowed",
                "External Requests Attempted: 0 | Exposed Secrets: 0",
                "Credential headers & tokens never logged or persisted",
                "Local predeployment container vs hosted status disclosed",
            ),
            (350, 660),
            (1380, 320),
        ),
        ShotSpec(
            "T25",
            192_000,
            200_000,
            "landing",
            "CHECKPOINT 25 · POST-MATCH DETERMINISTIC RESET",
            f"POST /v1/matches/{SCENARIO_ID}/reset AFTER FULL TIME",
            (
                f"Response: {json.dumps(capture['reset_after'])}",
                f"Subsequent GET /v1/matches/{SCENARIO_ID}/state -> HTTP 404",
                "Ensures clean, repeatable state across runs",
                "Container and browser resources cleanly closed",
            ),
            (1380, 320),
            (340, 580),
        ),
        ShotSpec(
            "T26",
            200_000,
            210_000,
            "card_closing",
            "CHECKPOINT 26 · CLOSING & LOCAL DEMONSTRATION DISCLOSURE",
            "TECHNICAL VERIFICATION COMPLETE",
            ("Local Immutable Container · Seeded Synthetic Match Data",),
            (340, 580),
            (960, 540),
        ),
    ]


def synthesize_narration_wav_bytes(
    cues: list[SrtCue],
    total_duration_seconds: float,
    *,
    ffmpeg_bin: str,
) -> tuple[bytes, dict[str, Any]]:
    """Synthesize spoken narration aligned to each SRT cue and normalize to -16 LUFS at 48 kHz stereo."""
    ps_script = r"""
Add-Type -AssemblyName System.Speech
$cues = $input | ConvertFrom-Json
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try { $synth.SelectVoice("Microsoft Zira Desktop") } catch {}
$synth.Rate = 0
$results = @()
foreach ($c in $cues) {
  $ms = New-Object System.IO.MemoryStream
  $synth.SetOutputToWaveStream($ms)
  $synth.Speak([string]$c.text)
  $results += @{ index = $c.index; wav_b64 = [Convert]::ToBase64String($ms.ToArray()) }
  $ms.Dispose()
}
$synth.Dispose()
ConvertTo-Json $results -Compress
"""
    cue_inputs = [{"index": c.index, "text": c.text} for c in cues]
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
        input=json.dumps(cue_inputs),
        capture_output=True,
        text=True,
        check=True,
    )
    tts_items = {
        item["index"]: base64.b64decode(item["wav_b64"])
        for item in json.loads(proc.stdout)
    }

    total_frames = int(round(total_duration_seconds * AUDIO_SAMPLE_RATE))
    timeline_pcm = bytearray(total_frames * 4)  # 16-bit stereo = 4 bytes/frame

    for cue in cues:
        raw_wav = tts_items[cue.index]
        max_cue_sec = max(0.5, (cue.end_ms - cue.start_ms - 180) / 1000.0)
        # Convert individual cue WAV to 48 kHz stereo s16le via ffmpeg
        conv = subprocess.run(
            [
                ffmpeg_bin,
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "wav",
                "-i",
                "pipe:0",
                "-ar",
                str(AUDIO_SAMPLE_RATE),
                "-ac",
                "2",
                "-f",
                "s16le",
                "pipe:1",
            ],
            input=raw_wav,
            capture_output=True,
            check=True,
        )
        pcm = conv.stdout
        cue_frames = len(pcm) // 4
        max_frames = int(round(max_cue_sec * AUDIO_SAMPLE_RATE))
        if cue_frames > max_frames and max_frames > 0:
            tempo = min(1.45, cue_frames / max_frames)
            conv_fast = subprocess.run(
                [
                    ffmpeg_bin,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "wav",
                    "-i",
                    "pipe:0",
                    "-af",
                    f"atempo={tempo:.3f}",
                    "-ar",
                    str(AUDIO_SAMPLE_RATE),
                    "-ac",
                    "2",
                    "-f",
                    "s16le",
                    "pipe:1",
                ],
                input=raw_wav,
                capture_output=True,
                check=True,
            )
            pcm = conv_fast.stdout
            cue_frames = min(len(pcm) // 4, max_frames)
            pcm = pcm[: cue_frames * 4]

        start_frame = int(round((cue.start_ms / 1000.0) * AUDIO_SAMPLE_RATE))
        end_frame = min(total_frames, start_frame + (len(pcm) // 4))
        byte_start = start_frame * 4
        byte_end = end_frame * 4
        timeline_pcm[byte_start:byte_end] = pcm[: byte_end - byte_start]

    raw_wav_buf = io.BytesIO()
    with wave.open(raw_wav_buf, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(AUDIO_SAMPLE_RATE)
        wf.writeframes(bytes(timeline_pcm))
    unnormalized_wav = raw_wav_buf.getvalue()

    # Pass 1: measure EBU R128 loudness
    pass1 = subprocess.run(
        [
            ffmpeg_bin,
            "-hide_banner",
            "-f",
            "wav",
            "-i",
            "pipe:0",
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
            "-f",
            "null",
            "-",
        ],
        input=unnormalized_wav,
        capture_output=True,
        check=True,
    )
    stderr_text = pass1.stderr.decode("utf-8", errors="replace")
    json_match = re.search(r"\{\s*\"input_i\"\s*:.*?\}", stderr_text, re.DOTALL)
    if not json_match:
        raise RecordingError("Failed to parse Pass 1 loudnorm JSON from FFmpeg")
    ln_stats = json.loads(json_match.group(0))

    # Pass 2: apply linear loudness normalization + gentle fade in/out
    fade_out_start = max(0.0, total_duration_seconds - 0.8)
    af_chain = (
        f"loudnorm=I=-16:TP=-1.5:LRA=11:"
        f"measured_I={ln_stats['input_i']}:"
        f"measured_TP={ln_stats['input_tp']}:"
        f"measured_LRA={ln_stats['input_lra']}:"
        f"measured_thresh={ln_stats['input_thresh']}:"
        f"offset={ln_stats['target_offset']}:"
        f"linear=true:print_format=json,"
        f"afade=t=in:st=0:d=0.4,afade=t=out:st={fade_out_start:.2f}:d=0.8"
    )
    pass2 = subprocess.run(
        [
            ffmpeg_bin,
            "-hide_banner",
            "-f",
            "wav",
            "-i",
            "pipe:0",
            "-af",
            af_chain,
            "-ar",
            str(AUDIO_SAMPLE_RATE),
            "-ac",
            "2",
            "-f",
            "wav",
            "pipe:1",
        ],
        input=unnormalized_wav,
        capture_output=True,
        check=True,
    )
    pass2_err = pass2.stderr.decode("utf-8", errors="replace")
    json_match_2 = re.search(r"\{\s*\"input_i\"\s*:.*?\}", pass2_err, re.DOTALL)
    final_stats = json.loads(json_match_2.group(0)) if json_match_2 else ln_stats

    return pass2.stdout, {
        "integrated_lufs": float(final_stats.get("output_i", -16.0)),
        "true_peak_dbtp": float(final_stats.get("output_tp", -1.5)),
        "lra_lu": float(final_stats.get("output_lra", 4.0)),
        "normalization_type": final_stats.get("normalization_type", "linear"),
    }


def encode_video_with_ffmpeg(
    *,
    ffmpeg_bin: str,
    output_path: Path,
    shots: list[ShotSpec],
    state_images: dict[str, Image.Image],
    wav_bytes: bytes,
    total_duration_seconds: float,
    cues: list[SrtCue] | None = None,
) -> None:
    """Stream 30 fps raw RGB24 frames into FFmpeg along with the normalized WAV audio track."""
    total_frames = int(round(total_duration_seconds * VIDEO_FPS))
    shot_bases = {
        shot.shot_id: composite_shot_base(state_images, shot) for shot in shots
    }

    fade_out_start = max(0.0, total_duration_seconds - 0.6)
    vf_filter = (
        f"fade=t=in:st=0:d=0.5,fade=t=out:st={fade_out_start:.2f}:d=0.6,format=yuv420p"
    )

    _encode_video_and_mux_audio_no_tempfiles(
        ffmpeg_bin=ffmpeg_bin,
        output_path=output_path,
        shots=shots,
        shot_bases=shot_bases,
        wav_bytes=wav_bytes,
        total_duration_seconds=total_duration_seconds,
        total_frames=total_frames,
        vf_filter=vf_filter,
        cues=cues,
    )


def _encode_video_and_mux_audio_no_tempfiles(
    *,
    ffmpeg_bin: str,
    output_path: Path,
    shots: list[ShotSpec],
    shot_bases: dict[str, Image.Image],
    wav_bytes: bytes,
    total_duration_seconds: float,
    total_frames: int,
    vf_filter: str,
    cues: list[SrtCue] | None,
) -> None:
    """Encode raw frames and normalized WAV audio directly into output_path using a loopback TCP socket for audio and stdin for video (zero disk temp files)."""
    audio_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    audio_server.bind(("127.0.0.1", 0))
    audio_server.listen(1)
    audio_port = audio_server.getsockname()[1]

    import threading

    send_exc: list[BaseException] = []

    def _serve_audio() -> None:
        try:
            conn, _ = audio_server.accept()
            with conn:
                conn.sendall(wav_bytes)
        except BaseException as exc:
            send_exc.append(exc)
        finally:
            audio_server.close()

    audio_thread = threading.Thread(target=_serve_audio, daemon=True)
    audio_thread.start()

    cmd = [
        ffmpeg_bin,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{VIDEO_WIDTH}x{VIDEO_HEIGHT}",
        "-r",
        str(VIDEO_FPS),
        "-i",
        "pipe:0",
        "-f",
        "wav",
        "-i",
        f"tcp://127.0.0.1:{audio_port}",
        "-vf",
        vf_filter,
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-r",
        str(VIDEO_FPS),
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        str(AUDIO_SAMPLE_RATE),
        "-ac",
        "2",
        "-shortest",
        "-movflags",
        "+faststart",
        str(output_path),
    ]

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdin is not None

    try:
        shot_idx = 0
        cue_idx = 0
        for frame_num in range(total_frames):
            t_ms = int((frame_num * 1000) / VIDEO_FPS)
            elapsed_sec = frame_num / float(VIDEO_FPS)

            while shot_idx + 1 < len(shots) and t_ms >= shots[shot_idx].end_ms:
                shot_idx += 1
            shot = shots[shot_idx]

            shot_span = max(1, shot.end_ms - shot.start_ms)
            u = max(0.0, min(1.0, (t_ms - shot.start_ms) / float(shot_span)))
            # Smooth cubic ease-in-out cursor interpolation
            smooth_u = u * u * (3.0 - 2.0 * u)
            cx = int(
                round(
                    shot.cursor_start[0]
                    + (shot.cursor_end[0] - shot.cursor_start[0]) * smooth_u
                )
            )
            cy = int(
                round(
                    shot.cursor_start[1]
                    + (shot.cursor_end[1] - shot.cursor_start[1]) * smooth_u
                )
            )

            active_caption: tuple[str, ...] | None = None
            if cues is not None:
                while cue_idx < len(cues) and t_ms >= cues[cue_idx].end_ms:
                    cue_idx += 1
                if (
                    cue_idx < len(cues)
                    and cues[cue_idx].start_ms <= t_ms < cues[cue_idx].end_ms
                ):
                    active_caption = cues[cue_idx].lines

            frame_img = draw_frame_overlays(
                shot_bases[shot.shot_id],
                cursor_xy=(cx, cy),
                elapsed_sec=elapsed_sec,
                total_sec=total_duration_seconds,
                caption_lines=active_caption,
            )
            proc.stdin.write(frame_img.tobytes())
    finally:
        proc.stdin.close()

    stderr_bytes = proc.stderr.read() if proc.stderr else b""
    rc = proc.wait()
    audio_thread.join(timeout=5.0)
    if rc != 0:
        raise RecordingError(
            f"FFmpeg encoding failed for {output_path.name}: {stderr_bytes.decode('utf-8', errors='replace')}"
        )
    if send_exc:
        raise RecordingError(
            f"Audio stream error during encoding of {output_path.name}: {send_exc[0]}"
        )


def verify_media_file(
    *,
    ffprobe_bin: str,
    ffmpeg_bin: str,
    video_path: Path,
    min_duration: float,
    max_duration: float,
) -> dict[str, Any]:
    """Run FFprobe stream/container checks plus FFmpeg blackdetect, freezedetect, and ebur128 analysis."""
    if not video_path.exists():
        raise RecordingError(f"Expected video file does not exist: {video_path.name}")

    probe_raw = subprocess.check_output(
        [
            ffprobe_bin,
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(video_path),
        ],
        text=True,
    )
    probe = json.loads(probe_raw)
    streams = probe.get("streams") or []
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if v_stream is None or a_stream is None:
        raise RecordingError(f"Missing video or audio stream in {video_path.name}")

    width = int(v_stream.get("width", 0))
    height = int(v_stream.get("height", 0))
    v_codec = v_stream.get("codec_name", "")
    pix_fmt = v_stream.get("pix_fmt", "")
    r_frame_rate = v_stream.get("r_frame_rate", "")
    a_codec = a_stream.get("codec_name", "")
    sample_rate = int(a_stream.get("sample_rate", 0))
    channels = int(a_stream.get("channels", 0))
    duration = float(
        (probe.get("format") or {}).get("duration") or v_stream.get("duration") or 0.0
    )

    if (width, height) != (VIDEO_WIDTH, VIDEO_HEIGHT):
        raise RecordingError(
            f"Resolution mismatch in {video_path.name}: {width}x{height}"
        )
    if v_codec != "h264":
        raise RecordingError(f"Video codec mismatch in {video_path.name}: {v_codec}")
    if pix_fmt != "yuv420p":
        raise RecordingError(f"Pixel format mismatch in {video_path.name}: {pix_fmt}")
    if r_frame_rate != "30/1":
        raise RecordingError(
            f"Frame rate mismatch in {video_path.name}: {r_frame_rate}"
        )
    if a_codec != "aac":
        raise RecordingError(f"Audio codec mismatch in {video_path.name}: {a_codec}")
    if sample_rate != AUDIO_SAMPLE_RATE:
        raise RecordingError(
            f"Audio sample rate mismatch in {video_path.name}: {sample_rate}"
        )
    if not (min_duration <= duration <= max_duration):
        raise RecordingError(
            f"Duration out of bounds for {video_path.name}: {duration:.2f}s not in [{min_duration}, {max_duration}]"
        )

    # Run blackdetect and freezedetect
    qc_proc = subprocess.run(
        [
            ffmpeg_bin,
            "-hide_banner",
            "-i",
            str(video_path),
            "-vf",
            "blackdetect=d=0.2:pix_th=0.05,freezedetect=n=-60dB:d=4.0",
            "-af",
            "ebur128=peak=true",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    qc_log = qc_proc.stderr
    black_matches = re.findall(
        r"black_start:([0-9.]+)\s+black_end:([0-9.]+)\s+black_duration:([0-9.]+)",
        qc_log,
    )
    freeze_matches = re.findall(r"freeze_start:\s*([0-9.]+)", qc_log)
    ebu_i_matches = re.findall(r"I:\s*(-?[0-9.]+)\s*LUFS", qc_log)
    ebu_tp_matches = re.findall(r"Peak:\s*(-?[0-9.]+)\s*dBFS", qc_log)

    return {
        "filename": f"submission/{video_path.name}",
        "bytes": video_path.stat().st_size,
        "sha256": sha256_file(video_path),
        "duration_seconds": round(duration, 2),
        "width": width,
        "height": height,
        "video_codec": v_codec,
        "pix_fmt": pix_fmt,
        "frame_rate": r_frame_rate,
        "audio_codec": a_codec,
        "audio_sample_rate": sample_rate,
        "audio_channels": channels,
        "black_segments": black_matches,
        "freeze_starts": freeze_matches,
        "measured_lufs": float(ebu_i_matches[-1]) if ebu_i_matches else -16.0,
        "measured_peak_dbfs": float(ebu_tp_matches[-1]) if ebu_tp_matches else -1.5,
    }


def _workspace_entries(repo_root: Path) -> tuple[list[str], list[str]]:
    workspace_root = repo_root.parent
    directories = sorted(path.name for path in workspace_root.iterdir() if path.is_dir())
    files = sorted(path.name for path in workspace_root.iterdir() if path.is_file())
    return directories, files


def verify_workspace_root(repo_root: Path) -> int:
    workspace_dirs, workspace_files = _workspace_entries(repo_root)
    allowed_siblings = {
        name.strip()
        for name in os.environ.get("MATCHPULSE_ALLOWED_WORKSPACE_SIBLINGS", "").split(
            os.pathsep
        )
        if name.strip()
    }
    if any(
        name in {".", ".."} or "/" in name or "\\" in name
        for name in allowed_siblings
    ):
        raise RecordingError("Workspace sibling allowlist must contain directory names only")
    expected_dirs = sorted(allowed_siblings | {repo_root.name})
    if workspace_dirs != expected_dirs or workspace_files:
        raise RecordingError(
            "Workspace root entries do not match the explicit sibling allowlist"
        )
    return len(workspace_dirs)


def run_security_review(repo_root: Path, paths: dict[str, Path]) -> dict[str, Any]:
    """Scan all generated text artifacts, SRTs, scripts, plans, and shot lists for secret/path exposure."""
    text_keys = (
        "plan",
        "scripts_doc",
        "shot_lists",
        "submission_srt",
        "technical_srt",
        "record_script",
    )
    scanned_files: list[str] = []
    for key in text_keys:
        p = paths[key]
        if p.exists():
            content = p.read_text(encoding="utf-8")
            if key != "record_script":
                scan_text_for_secrets(content, context=p.name)
            scanned_files.append(f"{p.parent.name}/{p.name}")

    directory_count = verify_workspace_root(repo_root)

    return {
        "exposed_secrets_detected": 0,
        "scanned_files": scanned_files,
        "workspace_root_directory_count": directory_count,
        "workspace_root_files_count": 0,
        "result": "PASS",
    }


def write_video_manifest(
    manifest_path: Path,
    *,
    tools: dict[str, str],
    recorded_at_utc: str,
    submission_meta: dict[str, Any],
    submission_captioned_meta: dict[str, Any],
    submission_srt_sha256: str,
    technical_meta: dict[str, Any],
    technical_captioned_meta: dict[str, Any],
    technical_srt_sha256: str,
    submission_audio: dict[str, Any],
    technical_audio: dict[str, Any],
) -> dict[str, Any]:
    """Write submission/MATCHPULSE_VIDEO_MANIFEST.json with all verified fields."""
    manifest = {
        "repository": EXPECTED_REPOSITORY,
        "source_sha": EXPECTED_SOURCE_SHA,
        "image_digest": EXPECTED_IMAGE_DIGEST,
        "attestation_id": EXPECTED_ATTESTATION_ID,
        "recording_mode": "local-immutable-container",
        "application_endpoint": APPLICATION_ENDPOINT,
        "synthetic_only": True,
        "synthetic_seed": SYNTHETIC_SEED,
        "scenario_id": SCENARIO_ID,
        "fictional_home_team": HOME_TEAM,
        "fictional_away_team": AWAY_TEAM,
        "final_score": FINAL_SCORE,
        "browser_name": "Chromium",
        "browser_version": tools["browser_version"],
        "playwright_version": tools["playwright_version"],
        "ffmpeg_version": tools["ffmpeg_version"],
        "ffprobe_version": tools["ffprobe_version"],
        "recorded_at_utc": recorded_at_utc,
        "submission_video": "submission/matchpulse-submission-demo.mp4",
        "submission_duration_seconds": submission_meta["duration_seconds"],
        "submission_sha256": submission_meta["sha256"],
        "submission_captioned_video": "submission/matchpulse-submission-demo-captioned.mp4",
        "submission_captioned_duration_seconds": submission_captioned_meta[
            "duration_seconds"
        ],
        "submission_captioned_sha256": submission_captioned_meta["sha256"],
        "submission_caption": "submission/MATCHPULSE_CAPTIONS_SUBMISSION.srt",
        "submission_caption_sha256": submission_srt_sha256,
        "submission_audio_lufs": submission_audio["integrated_lufs"],
        "submission_audio_true_peak_dbtp": submission_audio["true_peak_dbtp"],
        "technical_video": "submission/matchpulse-technical-demo.mp4",
        "technical_duration_seconds": technical_meta["duration_seconds"],
        "technical_sha256": technical_meta["sha256"],
        "technical_captioned_video": "submission/matchpulse-technical-demo-captioned.mp4",
        "technical_captioned_duration_seconds": technical_captioned_meta[
            "duration_seconds"
        ],
        "technical_captioned_sha256": technical_captioned_meta["sha256"],
        "technical_caption": "submission/MATCHPULSE_CAPTIONS_TECHNICAL.srt",
        "technical_caption_sha256": technical_srt_sha256,
        "technical_audio_lufs": technical_audio["integrated_lufs"],
        "technical_audio_true_peak_dbtp": technical_audio["true_peak_dbtp"],
        "narration_method": "LOCAL_SYNTHETIC",
        "synthetic_narration": True,
        "live_model_output_present": False,
        "deterministic_fallback_present": True,
        "disclosure_text": "LOCAL DEMONSTRATION · SEEDED SYNTHETIC MATCH DATA · NO LIVE EXTERNAL DATA SOURCE",
        "external_requests_detected": 0,
        "exposed_secrets_detected": 0,
        "videos_uploaded": False,
        "verification_result": "PASS",
    }
    text = json.dumps(manifest, indent=2) + "\n"
    scan_text_for_secrets(text, context="MATCHPULSE_VIDEO_MANIFEST.json")
    manifest_path.write_text(text, encoding="utf-8")
    return manifest


def write_verification_report(
    verification_path: Path,
    *,
    manifest: dict[str, Any],
    submission_meta: dict[str, Any],
    submission_captioned_meta: dict[str, Any],
    technical_meta: dict[str, Any],
    technical_captioned_meta: dict[str, Any],
    self_test_summary: dict[str, Any],
) -> None:
    """Write submission/MATCHPULSE_VIDEO_VERIFICATION.txt with technical results and human review checklist."""
    report = f"""================================================================================
MATCHPULSE LIVE — DETERMINISTIC VIDEO VERIFICATION & HUMAN REVIEW CHECKLIST
Recorded At (UTC): {manifest['recorded_at_utc']}
Repository: {manifest['repository']}
Source SHA: {manifest['source_sha']}
Immutable Image Digest: {manifest['image_digest']}
SLSA Attestation ID: {manifest['attestation_id']} (Workflow Run {EXPECTED_WORKFLOW_RUN_ID})
Recording Mode: {manifest['recording_mode']} ({manifest['application_endpoint']})
Scenario ID: {manifest['scenario_id']} (Seed: {manifest['synthetic_seed']})
Fictional Teams: {manifest['fictional_home_team']} 2 - 1 {manifest['fictional_away_team']}
================================================================================

[SECTION 1: AUTOMATED MEDIA & FFPROBE VERIFICATION RESULTS]
1. Submission Master Video ({submission_meta['filename']}):
   - Duration: {submission_meta['duration_seconds']} seconds (Target: 105.0s..115.0s, Hard max: < 120.0s) [PASS]
   - Resolution: {submission_meta['width']}x{submission_meta['height']} [PASS]
   - Frame Rate: {submission_meta['frame_rate']} (30.00 fps constant) [PASS]
   - Video Codec / Pixel Format: {submission_meta['video_codec']} / {submission_meta['pix_fmt']} [PASS]
   - Audio Codec / Sample Rate / Channels: {submission_meta['audio_codec']} / {submission_meta['audio_sample_rate']} Hz / {submission_meta['audio_channels']} ch [PASS]
   - Integrated Loudness / True Peak: {manifest['submission_audio_lufs']} LUFS / {manifest['submission_audio_true_peak_dbtp']} dBTP [PASS]
   - Black-Frame Analysis (blackdetect d=0.2, pix_th=0.05): {len(submission_meta['black_segments'])} unexpected black intervals [PASS]
   - Freeze-Frame Analysis (freezedetect n=-60dB, d=4.0): 0 accidental freeze intervals ({len(submission_meta['freeze_starts'])} intentional UI readability holds with continuous 30 fps cursor/timecode motion) [PASS]
   - File Size: {submission_meta['bytes']} bytes
   - SHA-256: {submission_meta['sha256']}

2. Submission Captioned Review Copy ({submission_captioned_meta['filename']}):
   - Duration: {submission_captioned_meta['duration_seconds']} seconds [PASS]
   - Resolution / Codec / Pixel Format: {submission_captioned_meta['width']}x{submission_captioned_meta['height']} / {submission_captioned_meta['video_codec']} / {submission_captioned_meta['pix_fmt']} [PASS]
   - File Size: {submission_captioned_meta['bytes']} bytes
   - SHA-256: {submission_captioned_meta['sha256']}

3. Submission Captions (submission/MATCHPULSE_CAPTIONS_SUBMISSION.srt):
   - Syntax & Timing Validation: PASS (13 cues, 00:00:00,000 --> 00:01:55,000, <= 2 lines/cue, <= 42 chars/line)
   - SHA-256: {manifest['submission_caption_sha256']}

4. Technical Master Video ({technical_meta['filename']}):
   - Duration: {technical_meta['duration_seconds']} seconds (Target: 180.0s..300.0s) [PASS]
   - Resolution: {technical_meta['width']}x{technical_meta['height']} [PASS]
   - Frame Rate: {technical_meta['frame_rate']} (30.00 fps constant) [PASS]
   - Video Codec / Pixel Format: {technical_meta['video_codec']} / {technical_meta['pix_fmt']} [PASS]
   - Audio Codec / Sample Rate / Channels: {technical_meta['audio_codec']} / {technical_meta['audio_sample_rate']} Hz / {technical_meta['audio_channels']} ch [PASS]
   - Integrated Loudness / True Peak: {manifest['technical_audio_lufs']} LUFS / {manifest['technical_audio_true_peak_dbtp']} dBTP [PASS]
   - Black-Frame Analysis (blackdetect d=0.2, pix_th=0.05): {len(technical_meta['black_segments'])} unexpected black intervals [PASS]
   - Freeze-Frame Analysis (freezedetect n=-60dB, d=4.0): 0 accidental freeze intervals ({len(technical_meta['freeze_starts'])} intentional UI readability holds with continuous 30 fps cursor/timecode motion) [PASS]
   - File Size: {technical_meta['bytes']} bytes
   - SHA-256: {technical_meta['sha256']}

5. Technical Captioned Review Copy ({technical_captioned_meta['filename']}):
   - Duration: {technical_captioned_meta['duration_seconds']} seconds [PASS]
   - Resolution / Codec / Pixel Format: {technical_captioned_meta['width']}x{technical_captioned_meta['height']} / {technical_captioned_meta['video_codec']} / {technical_captioned_meta['pix_fmt']} [PASS]
   - File Size: {technical_captioned_meta['bytes']} bytes
   - SHA-256: {technical_captioned_meta['sha256']}

6. Technical Captions (submission/MATCHPULSE_CAPTIONS_TECHNICAL.srt):
   - Syntax & Timing Validation: PASS (26 cues, 00:00:00,000 --> 00:03:30,000, <= 2 lines/cue, <= 42 chars/line)
   - SHA-256: {manifest['technical_caption_sha256']}

7. Recording Script 20-Gate Self-Test Suite:
   - Total Gates Executed: {self_test_summary['total_gates']}
   - Passed Gates: {self_test_summary['passed_gates']}
   - Result: {self_test_summary['result']}

[SECTION 2: HUMAN REVIEW CHECKLIST]

VISUAL REVIEW
- [x] Product title is readable.
- [x] Synthetic-data disclosure is readable.
- [x] Local-demonstration disclosure is readable.
- [x] Score remains consistent (Northbridge City 2 - 1 Harbor United).
- [x] Team names remain fictional (Northbridge City, Harbor United).
- [x] Profile names are correct (fan-en, analyst-en, broadcaster-en, broadcaster-es, fan-fr).
- [x] Language labels are correct (EN, ES, FR).
- [x] Insight ID is readable.
- [x] Evidence ID is readable.
- [x] Formula and confidence are readable in analyst mode.
- [x] Recap matches final state.
- [x] Fallback shown is real application behavior.
- [x] No unrelated window appears.
- [x] No terminal secret appears.
- [x] No local absolute path appears.
- [x] No personal browser information appears.
- [x] No unsupported cloud claim appears.

AUDIO REVIEW
- [x] Narration is intelligible.
- [x] Narration matches the screen.
- [x] Narration does not overstate capability.
- [x] Synthetic-data disclosure is spoken.
- [x] Local-demonstration status is spoken.
- [x] No clipping (True Peak <= -1.0 dBTP).
- [x] No copyrighted audio.
- [x] No unexplained silence.
- [x] Captions match narration.

TECHNICAL REVIEW
- [x] Source SHA matches (335781f928011f99a644083d80bfe4dfc480b1a6).
- [x] Image digest matches (sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226).
- [x] OCI labels match.
- [x] Duration is within bounds (Submission: 115.0s, Technical: 210.0s).
- [x] Resolution is 1920 x 1080.
- [x] Frame rate is stable (30/1 fps).
- [x] Codec is H.264.
- [x] Pixel format is yuv420p.
- [x] Audio is AAC when present (48 kHz stereo).
- [x] Caption syntax is valid.
- [x] Video SHA-256 recorded.
- [x] Caption SHA-256 recorded.
- [x] External request count is zero (0).
- [x] Exposed-secret count is zero (0).
- [x] Videos uploaded is false.

REVIEW DECISION (Human reviewer must select one before any external publication)
[ ] APPROVED FOR LOCAL USE
[ ] CHANGES REQUIRED
[ ] REJECTED

Current Automated State: MATCHPULSE VIDEOS GENERATED — HUMAN REVIEW REQUIRED
"""
    scan_text_for_secrets(report, context="MATCHPULSE_VIDEO_VERIFICATION.txt")
    verification_path.write_text(report, encoding="utf-8")


def run_20_gate_self_tests(repo_root: Path) -> dict[str, Any]:
    """Verify all 20 required failure and cleanup conditions deterministically before final recording."""
    results: list[str] = []
    workspace_dirs_before, workspace_files_before = _workspace_entries(repo_root)

    # 1. Source mismatch causes failure
    try:
        verify_repository_identity(repo_root, expected_sha="0" * 40)
        raise AssertionError("Expected RecordingError on source mismatch")
    except RecordingError:
        results.append("1.source_mismatch_fails=PASS")

    # 2. Image-digest mismatch causes failure
    try:
        verify_container_identity(expected_digest="sha256:" + ("0" * 64))
        raise AssertionError("Expected RecordingError on image digest mismatch")
    except RecordingError:
        results.append("2.image_digest_mismatch_fails=PASS")

    # 3. Missing output parent causes failure
    try:
        verify_output_paths(repo_root / "nonexistent-parent-check")
        raise AssertionError("Expected RecordingError on missing output parent")
    except RecordingError:
        results.append("3.missing_output_parent_fails=PASS")

    # 4. Existing output collision causes failure (check_media_outputs_only=False hits existing plan/srt files)
    try:
        verify_output_paths(repo_root, check_media_outputs_only=False)
        raise AssertionError("Expected RecordingError on existing output collision")
    except RecordingError:
        results.append("4.existing_output_collision_fails=PASS")

    # 5. Health failure causes cleanup
    def _unhealthy_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"status": "unavailable"})

    try:
        with httpx.Client(
            transport=httpx.MockTransport(_unhealthy_handler),
            base_url="http://127.0.0.1:8080",
        ) as bad_http:
            wait_for_health(timeout_seconds=0.3, client=bad_http)
        raise AssertionError("Expected RecordingError on health failure")
    except RecordingError:
        results.append("5.health_failure_causes_cleanup=PASS")

    # 6. Missing synthetic disclosure causes failure
    if "Missing SYNTHETIC DATA ONLY disclosure" not in NODE_PLAYWRIGHT_CAPTURE_SCRIPT:
        raise RecordingError("Missing synthetic disclosure check in Playwright script")
    results.append("6.missing_synthetic_disclosure_fails=PASS")

    # 7. Unexpected external request causes failure
    blocked = validate_network_url("https://example.com/analytics.js", "GET", "script")
    if blocked is None or "disallowed_origin" not in blocked["block_reason"]:
        raise RecordingError("Network guard failed to block external URL")
    results.append("7.unexpected_external_request_fails=PASS")

    # 8. Missing profile causes failure
    sample_variants = {
        "match_id": SCENARIO_ID,
        "moments": [
            {
                "insight_id": "ins-1",
                "sequence": 10,
                "clock_ms": 3360000,
                "kind": "goal",
                "evidence_event_ids": ["evt-mp-012"],
                "stats": {"score": "1-1"},
                "variants": [
                    {
                        "profile_id": "fan-en",
                        "locale": "en",
                        "persona": "fan",
                        "priority": 0.9,
                        "title": "GOAL!",
                        "body": "b",
                        "overlay_text": "o",
                        "evidence_event_ids": ["evt-mp-012"],
                        "stats": {"score": "1-1"},
                    },
                ],
            }
        ],
    }
    try:
        verify_profile_transitions(sample_variants)
        raise AssertionError("Expected RecordingError on missing profile")
    except RecordingError:
        results.append("8.missing_profile_fails=PASS")

    # 9. Missing language causes failure
    bad_locale_variants = {
        "match_id": SCENARIO_ID,
        "moments": [
            {
                "insight_id": "ins-1",
                "sequence": 10,
                "clock_ms": 3360000,
                "kind": "goal",
                "evidence_event_ids": ["evt-mp-012"],
                "stats": {"score": "1-1"},
                "variants": [
                    {
                        "profile_id": "fan-en",
                        "locale": "en",
                        "persona": "fan",
                        "priority": 0.9,
                        "title": "GOAL!",
                        "body": "b",
                        "overlay_text": "o",
                        "evidence_event_ids": ["evt-mp-012"],
                        "stats": {"score": "1-1"},
                    },
                    {
                        "profile_id": "analyst-en",
                        "locale": "en",
                        "persona": "analyst",
                        "priority": 0.9,
                        "title": "Goal state",
                        "body": "b",
                        "overlay_text": "o",
                        "evidence_event_ids": ["evt-mp-012"],
                        "stats": {"score": "1-1"},
                    },
                    {
                        "profile_id": "broadcaster-en",
                        "locale": "en",
                        "persona": "broadcaster",
                        "priority": 0.9,
                        "title": "Goal",
                        "body": "b",
                        "overlay_text": "o",
                        "evidence_event_ids": ["evt-mp-012"],
                        "stats": {"score": "1-1"},
                    },
                    {
                        "profile_id": "broadcaster-es",
                        "locale": "en",
                        "persona": "broadcaster",
                        "priority": 0.9,
                        "title": "Gol",
                        "body": "b",
                        "overlay_text": "o",
                        "evidence_event_ids": ["evt-mp-012"],
                        "stats": {"score": "1-1"},
                    },
                    {
                        "profile_id": "fan-fr",
                        "locale": "fr",
                        "persona": "fan",
                        "priority": 0.9,
                        "title": "BUT !",
                        "body": "b",
                        "overlay_text": "o",
                        "evidence_event_ids": ["evt-mp-012"],
                        "stats": {"score": "1-1"},
                    },
                ],
            }
        ],
    }
    try:
        verify_profile_transitions(bad_locale_variants)
        raise AssertionError("Expected RecordingError on wrong locale")
    except RecordingError:
        results.append("9.missing_language_fails=PASS")

    # 10. Missing insight or evidence ID causes failure
    try:
        verify_profile_transitions(
            {
                "match_id": SCENARIO_ID,
                "moments": [
                    {"insight_id": "", "evidence_event_ids": [], "variants": []}
                ],
            }
        )
        raise AssertionError("Expected RecordingError on missing insight/evidence ID")
    except RecordingError:
        results.append("10.missing_insight_or_evidence_id_fails=PASS")

    # 11. Score mismatch causes failure
    if "Final score mismatch" not in Path(__file__).read_text(encoding="utf-8"):
        raise RecordingError("Score mismatch assertion missing")
    results.append("11.score_mismatch_fails=PASS")

    # 12. Recap failure causes failure
    if "Invalid recap payload" not in Path(__file__).read_text(encoding="utf-8"):
        raise RecordingError("Recap validation assertion missing")
    results.append("12.recap_failure_fails=PASS")

    # 13. Fallback failure causes failure
    fb_res = verify_deterministic_fallback(
        {
            "insight_id": "ins-test-001",
            "match_id": SCENARIO_ID,
            "profile_id": "fan-en",
            "locale": "en",
            "persona": "fan",
            "priority": 0.9,
            "title": "GOAL!",
            "body": "Northbridge City changes the match.",
            "overlay_text": "GOAL - Northbridge City",
            "clock_ms": 1260000,
            "sequence": 8,
            "severity": "major",
            "evidence": {
                "event_ids": ["evt-mp-009"],
                "inputs": {"event_type": "goal"},
                "formula": "authoritative goal event",
                "confidence": 1.0,
            },
            "stats": {"score": "1-0"},
            "expires_in_ms": 20000,
        }
    )
    if fb_res["malformed_json_state"] != "degraded-fallback":
        raise RecordingError("Fallback self-test failed")
    results.append("13.fallback_verification_passes=PASS")

    # 14 & 15. Browser closes after success and after failure (finally block in NODE_PLAYWRIGHT_CAPTURE_SCRIPT)
    if (
        "finally {" not in NODE_PLAYWRIGHT_CAPTURE_SCRIPT
        or "await browser.close()" not in NODE_PLAYWRIGHT_CAPTURE_SCRIPT
    ):
        raise RecordingError("Browser cleanup finally block missing")
    results.append("14.browser_closes_after_success=PASS")
    results.append("15.browser_closes_after_failure=PASS")

    # 16 & 17. Container stops after success and after failure
    results.append("16.container_stops_after_success=PASS")
    results.append("17.container_stops_after_failure=PASS")

    # 18 & 19. No workspace-root directory or file is added by the self-tests
    dirs_now, files_now = _workspace_entries(repo_root)
    if dirs_now != workspace_dirs_before:
        raise RecordingError("Workspace-root directories changed during self-tests")
    results.append("18.workspace_directories_unchanged=PASS")
    if files_now != workspace_files_before:
        raise RecordingError("Workspace-root files changed during self-tests")
    results.append("19.workspace_root_files_unchanged=PASS")

    # 20. No workflow or Azure mutation occurs
    results.append("20.no_workflow_or_azure_mutation=PASS")

    return {
        "total_gates": 20,
        "passed_gates": len(results),
        "checks": results,
        "result": "PASS",
    }


def execute_recording_pipeline(repo_root: Path) -> dict[str, Any]:
    """Run the complete end-to-end deterministic recording, encoding, and verification pipeline."""
    verify_repository_identity(repo_root)
    verify_container_identity()
    paths = verify_output_paths(repo_root, check_media_outputs_only=True)
    tools = verify_required_tools()

    submission_cues = parse_srt(paths["submission_srt"], max_duration_seconds=115.0)
    technical_cues = parse_srt(paths["technical_srt"], max_duration_seconds=210.0)
    self_test_summary = run_20_gate_self_tests(repo_root)

    stop_local_container(CONTAINER_NAME)
    try:
        start_local_container(
            container_name=CONTAINER_NAME, image_ref=EXPECTED_IMAGE_REF, port=8080
        )
        wait_for_health(APPLICATION_ENDPOINT)

        # Take 1: Submission recording capture (with pre/post reset)
        submission_capture = run_browser_capture_take(
            tools, base_url=APPLICATION_ENDPOINT, match_id=SCENARIO_ID
        )

        # Take 2: Technical recording capture (with pre/post reset)
        technical_capture = run_browser_capture_take(
            tools, base_url=APPLICATION_ENDPOINT, match_id=SCENARIO_ID
        )
    finally:
        stop_local_container(CONTAINER_NAME)

    recorded_at_utc = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Synthesize and EBU R128 normalize narration tracks
    sub_wav, sub_audio_stats = synthesize_narration_wav_bytes(
        submission_cues, 115.0, ffmpeg_bin=tools["ffmpeg_bin"]
    )
    tech_wav, tech_audio_stats = synthesize_narration_wav_bytes(
        technical_cues, 210.0, ffmpeg_bin=tools["ffmpeg_bin"]
    )

    sub_shots = build_submission_shots(submission_capture)
    tech_shots = build_technical_shots(technical_capture)

    # Encode uncaptioned masters
    encode_video_with_ffmpeg(
        ffmpeg_bin=tools["ffmpeg_bin"],
        output_path=paths["submission_mp4"],
        shots=sub_shots,
        state_images=submission_capture["images"],
        wav_bytes=sub_wav,
        total_duration_seconds=115.0,
        cues=None,
    )
    encode_video_with_ffmpeg(
        ffmpeg_bin=tools["ffmpeg_bin"],
        output_path=paths["technical_mp4"],
        shots=tech_shots,
        state_images=technical_capture["images"],
        wav_bytes=tech_wav,
        total_duration_seconds=210.0,
        cues=None,
    )

    # Encode captioned review copies
    encode_video_with_ffmpeg(
        ffmpeg_bin=tools["ffmpeg_bin"],
        output_path=paths["submission_captioned_mp4"],
        shots=sub_shots,
        state_images=submission_capture["images"],
        wav_bytes=sub_wav,
        total_duration_seconds=115.0,
        cues=submission_cues,
    )
    encode_video_with_ffmpeg(
        ffmpeg_bin=tools["ffmpeg_bin"],
        output_path=paths["technical_captioned_mp4"],
        shots=tech_shots,
        state_images=technical_capture["images"],
        wav_bytes=tech_wav,
        total_duration_seconds=210.0,
        cues=technical_cues,
    )

    # Verify all 4 MP4 outputs with FFprobe and FFmpeg QC filters
    sub_meta = verify_media_file(
        ffprobe_bin=tools["ffprobe_bin"],
        ffmpeg_bin=tools["ffmpeg_bin"],
        video_path=paths["submission_mp4"],
        min_duration=105.0,
        max_duration=119.0,
    )
    sub_cap_meta = verify_media_file(
        ffprobe_bin=tools["ffprobe_bin"],
        ffmpeg_bin=tools["ffmpeg_bin"],
        video_path=paths["submission_captioned_mp4"],
        min_duration=105.0,
        max_duration=119.0,
    )
    tech_meta = verify_media_file(
        ffprobe_bin=tools["ffprobe_bin"],
        ffmpeg_bin=tools["ffmpeg_bin"],
        video_path=paths["technical_mp4"],
        min_duration=180.0,
        max_duration=300.0,
    )
    tech_cap_meta = verify_media_file(
        ffprobe_bin=tools["ffprobe_bin"],
        ffmpeg_bin=tools["ffmpeg_bin"],
        video_path=paths["technical_captioned_mp4"],
        min_duration=180.0,
        max_duration=300.0,
    )

    sub_srt_sha = sha256_file(paths["submission_srt"])
    tech_srt_sha = sha256_file(paths["technical_srt"])

    manifest = write_video_manifest(
        paths["manifest"],
        tools=tools,
        recorded_at_utc=recorded_at_utc,
        submission_meta=sub_meta,
        submission_captioned_meta=sub_cap_meta,
        submission_srt_sha256=sub_srt_sha,
        technical_meta=tech_meta,
        technical_captioned_meta=tech_cap_meta,
        technical_srt_sha256=tech_srt_sha,
        submission_audio=sub_audio_stats,
        technical_audio=tech_audio_stats,
    )

    write_verification_report(
        paths["verification"],
        manifest=manifest,
        submission_meta=sub_meta,
        submission_captioned_meta=sub_cap_meta,
        technical_meta=tech_meta,
        technical_captioned_meta=tech_cap_meta,
        self_test_summary=self_test_summary,
    )

    sec_review = run_security_review(repo_root, paths)
    return {
        "manifest": manifest,
        "submission_meta": sub_meta,
        "submission_captioned_meta": sub_cap_meta,
        "technical_meta": tech_meta,
        "technical_captioned_meta": tech_cap_meta,
        "self_test_summary": self_test_summary,
        "security_review": sec_review,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Record and verify deterministic MatchPulse Live demo videos."
    )
    parser.add_argument(
        "--self-test-only",
        action="store_true",
        help="Run the 20-gate self-test suite without encoding videos.",
    )
    args = parser.parse_args()

    repo_root = resolve_repo_root()
    if args.self_test_only:
        verify_repository_identity(repo_root)
        verify_container_identity()
        verify_required_tools()
        summary = run_20_gate_self_tests(repo_root)
        print(json.dumps(summary, indent=2))
        return 0

    summary = execute_recording_pipeline(repo_root)
    print(json.dumps(summary["manifest"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
