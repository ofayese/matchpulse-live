# cspell:ignore cpus pids rootfs getuid getgid accountkey pousr cognitiveservices nonsynth opencontainers Rootfs Pids Cpus
"""Hardened smoke test of a local or published MatchPulse Live container image.

Usage:
    python scripts/hardened_smoke_test.py --local-image <local-tag-or-id> [--expected-revision <40-hex-sha>]
    python scripts/hardened_smoke_test.py --published-image <name>@sha256:<digest> [--expected-revision <40-hex-sha>]

The image is started with release hardening applied:
  * non-root user 10001:10001
  * read-only root filesystem
  * all Linux capabilities dropped (--cap-drop ALL)
  * privilege escalation disabled (--security-opt no-new-privileges:true)
  * no Docker socket or host bind mounts
  * bounded non-executable tmpfs (/tmp:rw,noexec,nosuid,nodev,size=16m)
  * bounded PID, CPU and memory limits
  * isolated network (--network none) with zero published host ports
  * CHALLENGE_SYNTHETIC_ONLY=true with no populated secrets

All endpoint probes execute inside the container over loopback (127.0.0.1:8080)
and verify health/live, health/ready, profiles, synthetic event ingestion,
duplicate handling, out-of-order rejection, match state, audiences (fan,
analyst, broadcaster), languages (en, es, fr), recaps, deterministic fallback,
match reset, and log redaction before removing the container in a finally block.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import uuid

RUNTIME_USER = "10001:10001"
MEMORY_LIMIT = "512m"
MEMORY_LIMIT_BYTES = 536_870_912
CPU_LIMIT = "1.0"
NANO_CPUS = 1_000_000_000
PIDS_LIMIT = "256"
TMPFS_SPEC = "/tmp:rw,noexec,nosuid,nodev,size=16m"
PORT = 8080
BASE_URL = f"http://127.0.0.1:{PORT}"
EXPECTED_OCI_SOURCE = "https://github.com/ofayese/matchpulse-live"
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
PUBLISHED_DIGEST_RE = re.compile(r"^[^\s]+@sha256:[0-9a-f]{64}$")
LOCAL_HOSTS = {"127.0.0.1", "0.0.0.0", "localhost", "::1"}
LOOPBACK_URL = re.compile(r"(?i)\bhttps?://[^\s\"'\\)]+")
URL_HOST = re.compile(r"(?i)^https?://([^/:\s]+)")
LOG_FORBIDDEN_PATTERNS = {
    "traceback": re.compile(r"(?i)traceback \(most recent call last\)"),
    "error level": re.compile(r"(?i)\b(error|critical|fatal)\b"),
    "exception": re.compile(r"(?i)\bexception\b"),
    "crash": re.compile(r"(?i)\b(panic|segmentation fault|core dump)\b"),
    "secret like value": re.compile(
        r"(?i)(api[_-]?key|password|passwd|secret|token|bearer\s|accountkey=|-----begin .*private key-----)"
    ),
    "credential shaped value": re.compile(
        r"(?i)\b(sk-[A-Za-z0-9]{8,}|gh[pousr]_[A-Za-z0-9]{10,}|AccountKey=[A-Za-z0-9+/=]{40,})"
    ),
    "external service reference": re.compile(
        r"(?i)\b(azure|openai|foundry|cognitiveservices|management\.azure|oai\.|api\.openai\.com)\b"
    ),
    "outbound failure": re.compile(r"(?i)(getaddrinfo|connection refused|name resolution|no route to host)"),
}

CONTAINER_CHECKS = r'''
"""Endpoint and runtime checks executed inside the hardened container."""

from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request
import httpx

import matchpulse.foundry as foundry_mod
from matchpulse.models import Evidence, PersonalizedInsight

BASE = "http://127.0.0.1:8080"
failures = []


def check(label, ok, detail=""):
    line = ("PASS: " if ok else "FAIL: ") + label
    if detail:
        line += " - " + detail
    print(line, flush=True)
    if not ok:
        failures.append(label)
    return ok


def request(path, method="GET", payload=None, timeout=10):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    call = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(call, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8", "replace")


# 1. Verify in-container UID/GID and read-only rootfs enforcement
check("process runs as uid 10001", os.getuid() == 10001, f"uid={os.getuid()}")
check("process runs as gid 10001", os.getgid() == 10001, f"gid={os.getgid()}")

rootfs_readonly = False
try:
    pathlib.Path("/app/.smoke-write-probe").write_text("x", encoding="utf-8")
except OSError:
    rootfs_readonly = True
check("root filesystem rejects writes inside container", rootfs_readonly)

# 2. Wait for service readiness and test /health/live and /health/ready
last_error = "no attempt"
live_body = None
for _ in range(30):
    try:
        status, body = request("/health/live", timeout=3)
        if status == 200:
            live_body = body
            break
        last_error = f"HTTP {status}"
    except Exception as error:
        last_error = f"{type(error).__name__}: {error}"
    time.sleep(0.5)
check("GET /health/live returns 200", live_body is not None, (live_body or last_error)[:160])

if live_body is not None:
    live = json.loads(live_body)
    check("GET /health/live reports status ok", live.get("status") == "ok", str(live))

status, body = request("/health/ready", timeout=10)
check("GET /health/ready returns 200", status == 200, body[:200])
if status == 200:
    ready = json.loads(body)
    check("GET /health/ready reports status ready", ready.get("status") == "ready")
    check("GET /health/ready reports synthetic_only true", ready.get("synthetic_only") is True)
    check("GET /health/ready reports foundry_mode disabled", ready.get("foundry_mode") == "disabled")
    check("GET /health/ready reports telemetry_mode disabled", ready.get("telemetry_mode") == "disabled")
    check("GET /health/ready reports 4 profiles", ready.get("profiles") == 4)

# 3. Profiles check
status, body = request("/v1/profiles", timeout=10)
check("GET /v1/profiles returns 200", status == 200, body[:200])
if status == 200:
    profiles = json.loads(body)
    personas = {item.get("persona") for item in profiles}
    locales = {item.get("locale") for item in profiles}
    check("GET /v1/profiles covers fan, analyst, broadcaster", personas == {"fan", "analyst", "broadcaster"}, str(personas))
    check("GET /v1/profiles covers en, es, fr", locales == {"en", "es", "fr"}, str(locales))

# 4. Event ingestion, non-synthetic rejection, duplicate handling, and out-of-order handling
match_id = f"smoke-hardened-{int(time.time() * 1000)}"
ev_shot = {
    "event_id": "evt-smoke-shot-0002",
    "match_id": match_id,
    "sequence": 2,
    "clock_ms": 120000,
    "event_type": "shot",
    "team_id": "Riverside-Athletic",
    "player_id": "RA-9",
    "outcome": "on_target",
    "speed_kmh": 112,
    "source": "synthetic",
}
ev_nonsynth = dict(ev_shot, event_id="evt-smoke-bad-0009", sequence=9, source="real")
ev_out_of_order = {
    "event_id": "evt-smoke-pass-0001",
    "match_id": match_id,
    "sequence": 1,
    "clock_ms": 60000,
    "event_type": "pass",
    "team_id": "Harbor-City",
    "player_id": "HC-6",
    "outcome": "success",
    "x": 20,
    "y": 30,
    "end_x": 65,
    "end_y": 40,
    "speed_kmh": 54,
    "source": "synthetic",
}
ev_goal = {
    "event_id": "evt-smoke-goal-0003",
    "match_id": match_id,
    "sequence": 3,
    "clock_ms": 180000,
    "event_type": "goal",
    "team_id": "Riverside-Athletic",
    "player_id": "RA-10",
    "outcome": "success",
    "speed_kmh": 118,
    "source": "synthetic",
}

st_first, body_first = request("/v1/events", method="POST", payload=ev_shot)
first_json = json.loads(body_first) if st_first == 202 else {}
check(
    "POST /v1/events accepts synthetic event",
    st_first == 202 and first_json.get("accepted") is True and first_json.get("duplicate") is False,
    body_first[:200],
)

st_bad, _ = request("/v1/events", method="POST", payload=ev_nonsynth)
check("POST /v1/events rejects non-synthetic event with 422", st_bad == 422, f"HTTP {st_bad}")

st_dup, body_dup = request("/v1/events", method="POST", payload=ev_shot)
dup_json = json.loads(body_dup) if st_dup == 202 else {}
check(
    "POST /v1/events detects duplicate event_id",
    st_dup == 202 and dup_json.get("duplicate") is True and dup_json.get("insights") == [],
    body_dup[:200],
)

st_ooo, _ = request("/v1/events", method="POST", payload=ev_out_of_order)
check("POST /v1/events rejects out-of-order sequence with 409", st_ooo == 409, f"HTTP {st_ooo}")

st_goal, _ = request("/v1/events", method="POST", payload=ev_goal)
check("POST /v1/events accepts subsequent goal event", st_goal == 202, f"HTTP {st_goal}")

# 5. Match state verification
st_state, body_state = request(f"/v1/matches/{match_id}/state")
state_json = json.loads(body_state) if st_state == 200 else {}
check(
    "GET /v1/matches/{id}/state reports expected sequence, event_count, duplicate_count, and score",
    st_state == 200
    and state_json.get("last_sequence") == 3
    and state_json.get("event_count") == 2
    and state_json.get("duplicate_count") == 1
    and state_json.get("teams", {}).get("Riverside-Athletic", {}).get("goals") == 1,
    body_state[:240],
)

# 6. Audiences (fan, analyst, broadcaster) and languages (en, es, fr)
for loc in ("en", "es", "fr"):
    st_var, body_var = request(f"/v1/matches/{match_id}/variants?locale={loc}")
    var_json = json.loads(body_var) if st_var == 200 else {}
    moments = var_json.get("moments", [])
    personas_in_moments = {
        v.get("persona")
        for m in moments
        for v in m.get("variants", [])
    }
    locales_in_moments = {
        v.get("locale")
        for m in moments
        for v in m.get("variants", [])
    }
    check(
        f"GET /v1/matches/{{id}}/variants?locale={loc} covers fan, analyst, broadcaster in {loc}",
        st_var == 200
        and len(moments) >= 2
        and personas_in_moments == {"fan", "analyst", "broadcaster"}
        and locales_in_moments == {loc},
        f"HTTP {st_var} personas={personas_in_moments} locales={locales_in_moments}",
    )

# 7. Recaps across audiences and locales
for prof, loc in (("fan-en", "en"), ("analyst-en", "en"), ("broadcaster-es", "es"), ("fan-fr", "fr")):
    st_rec, body_rec = request(f"/v1/matches/{match_id}/recap?profile_id={prof}&locale={loc}")
    rec_json = json.loads(body_rec) if st_rec == 200 else {}
    check(
        f"GET /v1/matches/{{id}}/recap for {prof} ({loc}) returns grounded recap",
        st_rec == 200
        and rec_json.get("locale") == loc
        and bool(rec_json.get("headline"))
        and bool(rec_json.get("bullets"))
        and bool(rec_json.get("evidence_event_ids")),
        body_rec[:200],
    )

# 8. Deterministic fallback and model-control verification inside image
check("image DEFAULT_CALL_BUDGET is 20", foundry_mod.DEFAULT_CALL_BUDGET == 20, str(foundry_mod.DEFAULT_CALL_BUDGET))
check("image DEFAULT_MAX_CONCURRENCY is 1", foundry_mod.DEFAULT_MAX_CONCURRENCY == 1, str(foundry_mod.DEFAULT_MAX_CONCURRENCY))
check("image MAX_PROMPT_PAYLOAD_BYTES is 4096", foundry_mod.MAX_PROMPT_PAYLOAD_BYTES == 4096, str(foundry_mod.MAX_PROMPT_PAYLOAD_BYTES))
check("image MAX_OUTPUT_TOKENS is 128", foundry_mod.MAX_OUTPUT_TOKENS == 128, str(foundry_mod.MAX_OUTPUT_TOKENS))
check("image DEFAULT_TIMEOUT_SECONDS is 1.4", foundry_mod.DEFAULT_TIMEOUT_SECONDS == 1.4, str(foundry_mod.DEFAULT_TIMEOUT_SECONDS))

async def verify_fallback():
    sample = PersonalizedInsight(
        insight_id="smoke-i1",
        match_id=match_id,
        profile_id="fan-en",
        locale="en",
        persona="fan",
        priority=0.8,
        title="Shot",
        body="SecretPromptMarker98765 shot reached 112 km/h.",
        overlay_text="112 km/h shot",
        clock_ms=120000,
        sequence=2,
        severity="notable",
        evidence=Evidence(event_ids=["evt-smoke-shot-0002"], inputs={"speed_kmh": 112}, formula="speed >= 95", confidence=0.96),
        stats={"speed_kmh": 112},
        expires_in_ms=12000,
    )
    def failing_handler(req: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("simulated timeout SecretCredentialMarker98765")

    log_buf = io.StringIO()
    log_handler = logging.StreamHandler(log_buf)
    foundry_mod.log.addHandler(log_handler)
    try:
        client = foundry_mod.FoundryNarrativeClient(
            foundry_mod.FoundrySettings("https://example.test", "model", "SecretCredentialMarker98765"),
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(failing_handler)),
        )
        out, warn = await client.rewrite(sample)
    finally:
        foundry_mod.log.removeHandler(log_handler)
    logged = log_buf.getvalue()
    return (
        out == sample
        and warn == "Foundry fallback: TimeoutException"
        and "SecretPromptMarker98765" not in logged
        and "SecretCredentialMarker98765" not in logged
    )

check("Foundry deterministic fallback preserves source and redacts logs", asyncio.run(verify_fallback()))

# 9. Reset endpoint verification
st_rst, body_rst = request(f"/v1/matches/{match_id}/reset", method="POST")
rst_json = json.loads(body_rst) if st_rst == 200 else {}
st_after_rst, _ = request(f"/v1/matches/{match_id}/state")
check(
    "POST /v1/matches/{id}/reset clears match state",
    st_rst == 200 and rst_json.get("reset") is True and st_after_rst == 404,
    f"reset={st_rst} state_after={st_after_rst}",
)

print("CHECK_FAILURES=%d" % len(failures), flush=True)
for item in failures:
    print("FAILED_CHECK: %s" % item, flush=True)
sys.exit(1 if failures else 0)
'''


class SmokeError(Exception):
    """A requirement of the hardened smoke test was not met."""


def check(label: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    print(f"{status}: {label}{(' - ' + detail) if detail else ''}")
    return condition


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def build_docker_run_args(name: str, image: str) -> list[str]:
    """Build the fail-closed docker run argument list for the hardened container."""
    return [
        "run",
        "--pull=never",
        "-d",
        "--name",
        name,
        "--network",
        "none",
        "--user",
        RUNTIME_USER,
        "--read-only",
        "--tmpfs",
        TMPFS_SPEC,
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        "--pids-limit",
        PIDS_LIMIT,
        "--memory",
        MEMORY_LIMIT,
        "--memory-swap",
        MEMORY_LIMIT,
        "--cpus",
        CPU_LIMIT,
        "-e",
        "CHALLENGE_SYNTHETIC_ONLY=true",
        image,
    ]


def validate_oci_labels(
    labels: dict[str, str] | None,
    *,
    expected_revision: str | None = None,
    expected_source: str = EXPECTED_OCI_SOURCE,
) -> list[str]:
    """Validate standard OCI revision and source labels and return any error messages."""
    errors: list[str] = []
    label_map = labels or {}
    revision = (label_map.get("org.opencontainers.image.revision") or "").strip()
    source = (label_map.get("org.opencontainers.image.source") or "").strip()

    if not revision:
        errors.append("missing org.opencontainers.image.revision label")
    elif not SHA40_RE.fullmatch(revision):
        errors.append(f"org.opencontainers.image.revision is not a 40-character lowercase hex SHA: {revision}")
    elif expected_revision is not None and revision != expected_revision:
        errors.append(
            f"org.opencontainers.image.revision mismatch: expected {expected_revision}, got {revision}"
        )

    if not source:
        errors.append("missing org.opencontainers.image.source label")
    elif source != expected_source:
        errors.append(f"org.opencontainers.image.source mismatch: expected {expected_source}, got {source}")

    return errors


def docker(arguments: list[str], *, stdin: bytes | None = None) -> subprocess.CompletedProcess:
    if shutil.which("docker") is None:
        raise SmokeError("the docker command line client is not available")
    if stdin is None:
        return subprocess.run(  # noqa: S603
            ["docker", *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    return subprocess.run(  # noqa: S603
        ["docker", *arguments],
        input=stdin,
        capture_output=True,
        text=False,
        check=False,
    )


def docker_text(arguments: list[str], *, stdin: bytes | None = None) -> str:
    completed = docker(arguments, stdin=stdin)
    output = completed.stdout if isinstance(completed.stdout, str) else completed.stdout.decode("utf-8", "replace")
    if completed.returncode != 0:
        errors = completed.stderr if isinstance(completed.stderr, str) else completed.stderr.decode("utf-8", "replace")
        raise SmokeError(f"docker {' '.join(arguments[:2])} failed: {errors.strip() or output.strip()}")
    return output


def verify_image_oci_labels(image: str, expected_revision: str | None = None) -> int:
    """Inspect the image and verify standard OCI labels before/during smoke testing."""
    raw = docker_text(["image", "inspect", image, "--format", "{{json .Config.Labels}}"]).strip()
    labels = json.loads(raw) if raw and raw != "null" else {}
    errors = validate_oci_labels(labels, expected_revision=expected_revision)
    if errors:
        for err in errors:
            check(f"OCI label check ({err})", False)
        return len(errors)
    check(
        "standard org.opencontainers.image.revision label is valid",
        True,
        labels.get("org.opencontainers.image.revision", ""),
    )
    check(
        "standard org.opencontainers.image.source label is valid",
        True,
        labels.get("org.opencontainers.image.source", ""),
    )
    return 0


def container_interpreter(name: str) -> str:
    """Return the python interpreter that the image provides."""
    candidates = ["/usr/bin/python3.12", "python3.12", "python3", "python"]
    probe = "command -v %s 2>/dev/null || true"
    for candidate in candidates:
        found = docker_text(["exec", name, "sh", "-c", probe % candidate]).strip()
        if found:
            return found.splitlines()[-1].strip()
    raise SmokeError("the image does not provide a python interpreter")


def verify_hardening(name: str) -> int:
    """Require that the running container received every release hardening control."""
    failures = 0
    host = json.loads(docker_text(["inspect", name, "--format", "{{json .HostConfig}}"]))
    config = json.loads(docker_text(["inspect", name, "--format", "{{json .Config}}"]))
    mounts = json.loads(docker_text(["inspect", name, "--format", "{{json .Mounts}}"])) or []

    failures += not check("the container has no network", host.get("NetworkMode") == "none", str(host.get("NetworkMode")))
    failures += not check("the container root filesystem is read only", host.get("ReadonlyRootfs") is True)
    failures += not check("the container runs as non-root user 10001:10001", config.get("User") == RUNTIME_USER, str(config.get("User")))
    failures += not check("the container drops all capabilities", host.get("CapDrop") == ["ALL"] and not host.get("CapAdd"), str(host.get("CapDrop")))
    failures += not check(
        "the container forbids privilege escalation",
        "no-new-privileges:true" in (host.get("SecurityOpt") or []),
        str(host.get("SecurityOpt")),
    )
    failures += not check("the container is not privileged", host.get("Privileged") is False, str(host.get("Privileged")))
    failures += not check(
        "the container mounts no Docker socket or unexpected volumes",
        len(mounts) == 0 and not (host.get("Binds") or []),
        json.dumps(mounts),
    )
    failures += not check("the container is bound by a process limit", host.get("PidsLimit") == int(PIDS_LIMIT), str(host.get("PidsLimit")))
    failures += not check("the container is bound by a memory limit", host.get("Memory") == MEMORY_LIMIT_BYTES, str(host.get("Memory")))
    failures += not check("the container is bound by a cpu limit", host.get("NanoCpus") == NANO_CPUS, str(host.get("NanoCpus")))
    failures += not check("the container uses the bounded tmpfs", host.get("Tmpfs") == {"/tmp": "rw,noexec,nosuid,nodev,size=16m"}, str(host.get("Tmpfs")))
    failures += not check("the container publishes no host port", not (host.get("PortBindings") or {}), str(host.get("PortBindings")))

    environment = {item.split("=", 1)[0]: item.split("=", 1)[1] for item in (config.get("Env") or []) if "=" in item}
    failures += not check(
        "the synthetic-only gate is enabled",
        environment.get("CHALLENGE_SYNTHETIC_ONLY") == "true",
        str(environment.get("CHALLENGE_SYNTHETIC_ONLY")),
    )
    unexpected = sorted(
        key for key in environment
        if key not in {"CHALLENGE_SYNTHETIC_ONLY", "PATH", "PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "PYTHONUNBUFFERED"}
        and "FOUNDRY" not in key and "AZURE" not in key and "TELEMETRY" not in key
    )
    failures += not check("the container receives no unexpected configuration", not unexpected, ",".join(unexpected))
    secrets = sorted(key for key, value in environment.items() if re.search(r"(?i)(key|secret|password|token)", key) and value)
    failures += not check("the container receives no configured secret", not secrets, ",".join(secrets))
    return failures


def run_container_checks(name: str, interpreter: str) -> int:
    """Run the endpoint checks inside the container and require every one to pass."""
    completed = docker(["exec", "-i", name, interpreter, "-"], stdin=CONTAINER_CHECKS.encode("utf-8"))
    output = completed.stdout if isinstance(completed.stdout, str) else completed.stdout.decode("utf-8", "replace")
    errors = completed.stderr if isinstance(completed.stderr, str) else completed.stderr.decode("utf-8", "replace")
    print(output.rstrip())
    if completed.returncode != 0:
        check("the in-container endpoint checks pass", False, (errors or output).strip()[-400:])
        raise SmokeError("the in-container endpoint checks failed")
    check("the in-container endpoint checks pass", True)
    return 0


def run_synthetic_client(name: str, interpreter: str, events: int, seed: int) -> int:
    """Stream a seeded synthetic match into the running service from inside the container."""
    failures = 0
    help_result = docker(["exec", name, interpreter, "-m", "matchpulse.synthetic", "--help"])
    help_output = help_result.stdout if isinstance(help_result.stdout, str) else help_result.stdout.decode("utf-8", "replace")
    failures += not check("the synthetic module help command succeeds", help_result.returncode == 0, help_output[:200])
    if help_result.returncode != 0:
        raise SmokeError("the synthetic module help command failed")
    completed = docker(
        [
            "exec", name, interpreter, "-m", "matchpulse.synthetic",
            "--url", BASE_URL, "--events", str(events), "--delay", "0.05", "--seed", str(seed),
        ]
    )
    output = completed.stdout if isinstance(completed.stdout, str) else completed.stdout.decode("utf-8", "replace")
    errors = completed.stderr if isinstance(completed.stderr, str) else completed.stderr.decode("utf-8", "replace")
    lines = [line for line in output.splitlines() if line.strip()]
    failures += not check("the synthetic client streams a match", len(lines) >= events, f"{len(lines)} line(s) for {events} event(s)")
    failures += not check("the synthetic client exits successfully", completed.returncode == 0, (errors or output).strip()[-300:])
    for line in lines:
        try:
            record = json.loads(line)
        except ValueError:
            failures += not check("the synthetic client reports structured output", False, line[:160])
            return failures
        if "insights" not in record:
            failures += not check("the synthetic client reports structured output", False, line[:160])
            return failures
    failures += not check("the synthetic client reports structured output", True)
    return failures


def review_log(name: str) -> int:
    """Require that the container log carries no failure, secret, prompt body, or external contact."""
    failures = 0
    completed = docker(["logs", name])
    output = completed.stdout if isinstance(completed.stdout, str) else completed.stdout.decode("utf-8", "replace")
    errors = completed.stderr if isinstance(completed.stderr, str) else completed.stderr.decode("utf-8", "replace")
    failures += not check("docker logs inspection succeeds", completed.returncode == 0, f"lines={len((output + errors).splitlines())}")
    lines = [line for line in (output + errors).splitlines() if line.strip()]
    for label, pattern in LOG_FORBIDDEN_PATTERNS.items():
        matches = [line for line in lines if pattern.search(line)]
        failures += not check(f"the container log carries no {label}", not matches, " | ".join(matches)[:300])
    external = []
    for line in lines:
        for url in LOOPBACK_URL.findall(line):
            host = URL_HOST.match(url)
            if host and host.group(1).lower() not in LOCAL_HOSTS:
                external.append(url)
    failures += not check("the container log references no external endpoint", not external, " | ".join(external[:5]))
    return failures


def run(
    image: str,
    events: int,
    seed: int,
    *,
    pull: bool,
    expected_revision: str | None = None,
    require_oci_labels: bool = True,
) -> int:
    """Start the hardened container, exercise it, review its log and remove it."""
    name = f"mp-hardened-smoke-{uuid.uuid4().hex[:8]}"
    if pull:
        docker_text(["pull", image])
    failures = 0
    if require_oci_labels:
        failures += verify_image_oci_labels(image, expected_revision=expected_revision)

    started = docker(build_docker_run_args(name, image))
    if started.returncode != 0:
        errors = started.stderr if isinstance(started.stderr, str) else started.stderr.decode("utf-8", "replace")
        fail(f"the hardened container did not start: {errors.strip()}")
    try:
        failures += verify_hardening(name)
        interpreter = container_interpreter(name)
        failures += run_container_checks(name, interpreter)
        failures += run_synthetic_client(name, interpreter, events, seed)
        failures += review_log(name)
    except SmokeError as error:
        failures += not check("the hardened smoke test completes", False, str(error))
    finally:
        removed = docker(["rm", "-f", name])
        failures += not check("the hardened container is removed", removed.returncode == 0)
    print(f"RESULT: {'PASS' if not failures else 'FAIL'} ({failures} failed check(s))")
    return 1 if failures else 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hardened smoke test of a MatchPulse Live image.")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--local-image", help="A local Docker tag or image ID. This mode never pulls.")
    modes.add_argument("--published-image", help="A published image reference pinned to a sha256 digest.")
    parser.add_argument("--expected-revision", default=None, help="Optional expected 40-character lowercase SHA for org.opencontainers.image.revision.")
    parser.add_argument("--events", type=int, default=5, help="The number of synthetic events to stream.")
    parser.add_argument("--seed", type=int, default=27, help="The synthetic match seed.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_args(argv)
    image = arguments.local_image or arguments.published_image
    published = arguments.published_image is not None
    if published and not PUBLISHED_DIGEST_RE.fullmatch(image):
        fail("--published-image must be pinned to a full lowercase sha256 digest")
    if arguments.expected_revision is not None and not SHA40_RE.fullmatch(arguments.expected_revision):
        fail("--expected-revision must be a full 40-character lowercase hexadecimal SHA")
    try:
        return run(
            image,
            arguments.events,
            arguments.seed,
            pull=published,
            expected_revision=arguments.expected_revision,
        )
    except SmokeError as error:
        fail(str(error))
    return 0


if __name__ == "__main__":
    sys.exit(main())
