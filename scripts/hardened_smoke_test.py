"""Hardened smoke test of the published MatchPulse Live image.

Usage:
    python scripts/hardened_smoke_test.py --image <registry>/<repository>@sha256:<digest>

The image is started with the release hardening applied: no network, a
non-root user, a read-only root filesystem, no Linux capabilities, a small
tmpfs, bounded process and memory limits, and the synthetic-only gate
enabled. No host port is published, so every request is made from inside the
container with ``docker exec`` and nothing is reachable from the host.

The test verifies the hardening that the container actually received, calls
the live, readiness, profile, event and match state endpoints, streams a
seeded synthetic match with the packaged synthetic client, reviews the
container log for tracebacks, secrets and external service contact, and
always removes the container it created.

The script carries no hard coded release identity. The image reference is
supplied on the command line so the caller stays the single reviewable source
of truth for the release identity.
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
CPU_LIMIT = "1.0"
PIDS_LIMIT = "256"
TMPFS = "/tmp:rw,noexec,nosuid,nodev,size=16m"
PORT = 8080
BASE_URL = f"http://127.0.0.1:{PORT}"
SYNTHETIC_ENVIRONMENT = {"CHALLENGE_SYNTHETIC_ONLY": "true"}
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
    "credential shaped value": re.compile(r"(?i)\b(sk-[A-Za-z0-9]{8,}|gh[pousr]_[A-Za-z0-9]{10,}|AccountKey=[A-Za-z0-9+/=]{40,})"),
    "external service reference": re.compile(
        r"(?i)\b(azure|openai|foundry|cognitiveservices|management\.azure|oai\.|api\.openai\.com)\b"
    ),
    "outbound failure": re.compile(r"(?i)(getaddrinfo|connection refused|name resolution|no route to host)"),
}
CONTAINER_CHECKS = r'''
"""Endpoint checks executed inside the hardened container."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

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
    with urllib.request.urlopen(call, timeout=timeout) as response:
        return response.status, response.read().decode("utf-8")


last_error = "no attempt"
live_body = None
for _ in range(30):
    try:
        status, body = request("/health/live", timeout=3)
        if status == 200:
            live_body = body
            break
        last_error = "HTTP %d" % status
    except Exception as error:
        last_error = "%s: %s" % (type(error).__name__, error)
    time.sleep(1)
check("GET /health/live returns success", live_body is not None, (live_body or last_error)[:160])

live = {}
if live_body is not None:
    try:
        live = json.loads(live_body)
    except ValueError as error:
        check("GET /health/live returns valid JSON", False, str(error))
    else:
        check("GET /health/live returns valid JSON", True, live_body[:160])
        check("GET /health/live reports status ok", live.get("status") == "ok", str(live.get("status")))

try:
    status, body = request("/health/ready", timeout=10)
except Exception as error:
    status, body = 0, "%s: %s" % (type(error).__name__, error)
check("GET /health/ready returns success", status == 200, body[:200])

ready = {}
if status == 200:
    try:
        ready = json.loads(body)
    except ValueError as error:
        check("GET /health/ready returns valid JSON", False, str(error))
    else:
        check("GET /health/ready returns valid JSON", True, body[:200])
        check("GET /health/ready reports status ready", ready.get("status") == "ready", str(ready.get("status")))
        check("GET /health/ready reports synthetic_only", ready.get("synthetic_only") is True, str(ready.get("synthetic_only")))
        check(
            "GET /health/ready reports the disabled foundry mode",
            ready.get("foundry_mode") == "disabled",
            "foundry_mode=%s" % ready.get("foundry_mode"),
        )
        check(
            "GET /health/ready reports the disabled telemetry mode",
            ready.get("telemetry_mode") == "disabled",
            "telemetry_mode=%s" % ready.get("telemetry_mode"),
        )
        check("GET /health/ready reports loaded profiles", int(ready.get("profiles") or 0) > 0, str(ready.get("profiles")))

try:
    status, body = request("/v1/profiles", timeout=10)
except Exception as error:
    status, body = 0, "%s: %s" % (type(error).__name__, error)
check("GET /v1/profiles returns success", status == 200, body[:200])

profiles = []
if status == 200:
    try:
        profiles = json.loads(body)
    except ValueError as error:
        check("GET /v1/profiles returns valid JSON", False, str(error))
    else:
        check("GET /v1/profiles returns valid JSON", True, body[:200])
        check("GET /v1/profiles returns a non-empty list", isinstance(profiles, list) and len(profiles) > 0, str(type(profiles)))
        if isinstance(profiles, list) and profiles:
            check(
                "GET /v1/profiles entries carry a profile_id",
                all("profile_id" in item for item in profiles),
                json.dumps(profiles)[:160],
            )

match_id = "smoke-hardened-%d" % int(time.time() * 1000)
event = {
    "match_id": match_id,
    "sequence": 0,
    "clock_ms": 0,
    "event_type": "match_start",
    "source": "synthetic",
}
try:
    status, body = request("/v1/events", method="POST", payload=event, timeout=15)
except Exception as error:
    status, body = 0, "%s: %s" % (type(error).__name__, error)
check("POST /v1/events returns the accepted status", status == 202, "HTTP %d %s" % (status, body[:200]))

if status == 202:
    try:
        ingested = json.loads(body)
    except ValueError as error:
        check("POST /v1/events returns valid JSON", False, str(error))
    else:
        check("POST /v1/events returns valid JSON", True, body[:200])
        check("POST /v1/events returns insights", isinstance(ingested.get("insights"), list), json.dumps(ingested)[:200])

try:
    status, body = request("/v1/matches/%s/state" % match_id, timeout=10)
except Exception as error:
    status, body = 0, "%s: %s" % (type(error).__name__, error)
check("GET /v1/matches/{id}/state returns success", status == 200, "HTTP %d %s" % (status, body[:200]))

if status == 200:
    try:
        state = json.loads(body)
    except ValueError as error:
        check("GET /v1/matches/{id}/state returns valid JSON", False, str(error))
    else:
        check("GET /v1/matches/{id}/state returns valid JSON", True, body[:200])
        check(
            "GET /v1/matches/{id}/state reports the match",
            state.get("match_id") == match_id,
            json.dumps(state)[:200],
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


def docker(arguments: list[str], *, stdin: bytes | None = None) -> subprocess.CompletedProcess[str]:
    if shutil.which("docker") is None:
        raise SmokeError("the docker command line client is not available")
    return subprocess.run(  # noqa: S603
        ["docker", *arguments],
        input=stdin,
        capture_output=True,
        text=stdin is None,
        check=False,
    )


def docker_text(arguments: list[str], *, stdin: bytes | None = None) -> str:
    completed = docker(arguments, stdin=stdin)
    output = completed.stdout if isinstance(completed.stdout, str) else completed.stdout.decode("utf-8", "replace")
    if completed.returncode != 0:
        errors = completed.stderr if isinstance(completed.stderr, str) else completed.stderr.decode("utf-8", "replace")
        raise SmokeError(f"docker {' '.join(arguments[:2])} failed: {errors.strip() or output.strip()}")
    return output


def container_interpreter(name: str) -> str:
    """Return the python interpreter that the image provides."""
    candidates = ["python3", "python3.12", "python"]
    probe = "command -v %s 2>/dev/null || true"
    for candidate in candidates:
        found = docker_text(["exec", name, "sh", "-c", probe % candidate]).strip()
        if found:
            return found.splitlines()[-1].strip()
    raise SmokeError("the image does not provide a python interpreter")


def verify_hardening(name: str) -> None:
    """Require that the container received the release hardening."""
    host = json.loads(docker_text(["inspect", name, "--format", "{{json .HostConfig}}"]))
    config = json.loads(docker_text(["inspect", name, "--format", "{{json .Config}}"]))
    check("the container has no network", host.get("NetworkMode") == "none", str(host.get("NetworkMode")))
    check("the container root filesystem is read only", host.get("ReadonlyRootfs") is True)
    check("the container runs as a non-root user", config.get("User") == RUNTIME_USER, str(config.get("User")))
    check("the container drops all capabilities", host.get("CapDrop") == ["ALL"], str(host.get("CapDrop")))
    check(
        "the container forbids privilege escalation",
        "no-new-privileges:true" in (host.get("SecurityOpt") or []),
        str(host.get("SecurityOpt")),
    )
    check("the container is bound by a process limit", host.get("PidsLimit") == int(PIDS_LIMIT), str(host.get("PidsLimit")))
    check("the container is bound by a memory limit", host.get("Memory") == 536870912, str(host.get("Memory")))
    check("the container is bound by a cpu limit", host.get("NanoCpus") == 1000000000, str(host.get("NanoCpus")))
    check("the container uses the bounded tmpfs", host.get("Tmpfs") == {"/tmp": "rw,noexec,nosuid,nodev,size=16m"}, str(host.get("Tmpfs")))
    check("the container publishes no host port", not (host.get("PortBindings") or {}), str(host.get("PortBindings")))
    environment = {item.split("=", 1)[0]: item.split("=", 1)[1] for item in (config.get("Env") or []) if "=" in item}
    check(
        "the synthetic-only gate is enabled",
        environment.get("CHALLENGE_SYNTHETIC_ONLY") == "true",
        str(environment.get("CHALLENGE_SYNTHETIC_ONLY")),
    )
    unexpected = sorted(
        key for key, value in environment.items()
        if key not in {"CHALLENGE_SYNTHETIC_ONLY", "PATH", "PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "PYTHONUNBUFFERED"}
        and "FOUNDRY" not in key and "AZURE" not in key and "TELEMETRY" not in key
    )
    check("the container receives no unexpected configuration", not unexpected, ",".join(unexpected))
    secrets = sorted(key for key, value in environment.items() if re.search(r"(?i)(key|secret|password|token)", key) and value)
    check("the container receives no configured secret", not secrets, ",".join(secrets))


def run_container_checks(name: str, interpreter: str) -> None:
    """Run the endpoint checks inside the container and require every one to pass."""
    completed = docker(["exec", "-i", name, interpreter, "-"], stdin=CONTAINER_CHECKS.encode("utf-8"))
    output = completed.stdout if isinstance(completed.stdout, str) else completed.stdout.decode("utf-8", "replace")
    errors = completed.stderr if isinstance(completed.stderr, str) else completed.stderr.decode("utf-8", "replace")
    print(output.rstrip())
    if completed.returncode != 0:
        check("the in-container endpoint checks pass", False, (errors or output).strip()[-400:])
        raise SmokeError("the in-container endpoint checks failed")
    check("the in-container endpoint checks pass", True)


def run_synthetic_client(name: str, interpreter: str, events: int, seed: int) -> None:
    """Stream a seeded synthetic match into the running service from inside the container."""
    completed = docker(
        [
            "exec", name, interpreter, "-m", "matchpulse.synthetic",
            "--url", BASE_URL, "--events", str(events), "--delay", "0.05", "--seed", str(seed),
        ]
    )
    output = completed.stdout if isinstance(completed.stdout, str) else completed.stdout.decode("utf-8", "replace")
    errors = completed.stderr if isinstance(completed.stderr, str) else completed.stderr.decode("utf-8", "replace")
    lines = [line for line in output.splitlines() if line.strip()]
    check("the synthetic client streams a match", len(lines) >= events, f"{len(lines)} line(s) for {events} event(s)")
    check("the synthetic client exits successfully", completed.returncode == 0, (errors or output).strip()[-300:])
    for line in lines:
        try:
            record = json.loads(line)
        except ValueError:
            check("the synthetic client reports structured output", False, line[:160])
            return
        if "insights" not in record:
            check("the synthetic client reports structured output", False, line[:160])
            return
    check("the synthetic client reports structured output", True)


def review_log(name: str) -> None:
    """Require that the container log carries no failure, secret or external contact."""
    completed = docker(["logs", name])
    output = completed.stdout if isinstance(completed.stdout, str) else completed.stdout.decode("utf-8", "replace")
    errors = completed.stderr if isinstance(completed.stderr, str) else completed.stderr.decode("utf-8", "replace")
    lines = [line for line in (output + errors).splitlines() if line.strip()]
    check("the container log is not empty", bool(lines), f"{len(lines)} line(s)")
    for label, pattern in LOG_FORBIDDEN_PATTERNS.items():
        matches = [line for line in lines if pattern.search(line)]
        check(f"the container log carries no {label}", not matches, " | ".join(matches)[:300])
    external = []
    for line in lines:
        for url in LOOPBACK_URL.findall(line):
            host = URL_HOST.match(url)
            if host and host.group(1).lower() not in LOCAL_HOSTS:
                external.append(url)
    check("the container log references no external endpoint", not external, " | ".join(external[:5]))


def run(image: str, events: int, seed: int) -> int:
    """Start the hardened container, exercise it, review its log and remove it."""
    name = f"mp-hardened-smoke-{uuid.uuid4().hex[:8]}"
    docker(["rm", "-f", name])
    started = docker(
        [
            "run", "-d", "--name", name,
            "--network", "none",
            "--user", RUNTIME_USER,
            "--read-only",
            "--tmpfs", TMPFS,
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges:true",
            "--pids-limit", PIDS_LIMIT,
            "--memory", MEMORY_LIMIT,
            "--cpus", CPU_LIMIT,
            "-e", "CHALLENGE_SYNTHETIC_ONLY=true",
            image,
        ]
    )
    if started.returncode != 0:
        errors = started.stderr if isinstance(started.stderr, str) else started.stderr.decode("utf-8", "replace")
        fail(f"the hardened container did not start: {errors.strip()}")
    failures = 0
    try:
        verify_hardening(name)
        interpreter = container_interpreter(name)
        run_container_checks(name, interpreter)
        run_synthetic_client(name, interpreter, events, seed)
        review_log(name)
    except SmokeError as error:
        failures += not check("the hardened smoke test completes", False, str(error))
    finally:
        removed = docker(["rm", "-f", name])
        failures += not check("the hardened container is removed", removed.returncode == 0)
    print(f"RESULT: {'PASS' if not failures else 'FAIL'} ({failures} failed check(s))")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Hardened smoke test of the published MatchPulse Live image.")
    parser.add_argument("--image", required=True, help="The immutable image reference to test.")
    parser.add_argument("--events", type=int, default=5, help="The number of synthetic events to stream.")
    parser.add_argument("--seed", type=int, default=27, help="The synthetic match seed.")
    arguments = parser.parse_args()
    if "@sha256:" not in arguments.image:
        fail("the image reference must be pinned to a sha256 digest")
    try:
        return run(arguments.image, arguments.events, arguments.seed)
    except SmokeError as error:
        fail(str(error))
    return 0


if __name__ == "__main__":
    sys.exit(main())
