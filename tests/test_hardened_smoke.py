# cspell:ignore pids cpus opencontainers Rootfs Pids Cpus
"""Focused unit tests for hardened smoke test."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import hardened_smoke_test as hst  # noqa: E402  # type: ignore

VALID_SHA = "a3397938b866e1694b9282d1e353446aea30e696"
VALID_DIGEST = "sha256:" + ("b" * 64)


def test_build_docker_run_args_enforces_hardened_flags():
    args = hst.build_docker_run_args(
        "mp-test-container", "matchpulse-live:test"
    )
    assert args[:5] == [
        "run",
        "--pull=never",
        "-d",
        "--name",
        "mp-test-container",
    ]
    assert "--network" in args
    assert args[args.index("--network") + 1] == "none"
    assert "--user" in args
    assert args[args.index("--user") + 1] == "10001:10001"
    assert "--read-only" in args
    assert "--tmpfs" in args
    assert (
        args[args.index("--tmpfs") + 1]
        == "/tmp:rw,noexec,nosuid,nodev,size=16m"
    )
    assert "--cap-drop" in args
    assert args[args.index("--cap-drop") + 1] == "ALL"
    assert "--security-opt" in args
    assert args[args.index("--security-opt") + 1] == "no-new-privileges:true"
    assert "--pids-limit" in args
    assert args[args.index("--pids-limit") + 1] == "256"
    assert "--memory" in args
    assert args[args.index("--memory") + 1] == "512m"
    assert "--memory-swap" in args
    assert args[args.index("--memory-swap") + 1] == "512m"
    assert "--cpus" in args
    assert args[args.index("--cpus") + 1] == "1.0"
    assert "-e" in args
    assert args[args.index("-e") + 1] == "CHALLENGE_SYNTHETIC_ONLY=true"
    assert "--privileged" not in args
    assert not any("docker.sock" in token for token in args)
    assert "-p" not in args
    assert "--publish" not in args
    assert args[-1] == "matchpulse-live:test"


def test_validate_oci_labels_accepts_valid_standard_labels():
    labels = {
        "org.opencontainers.image.revision": VALID_SHA,
        "org.opencontainers.image.source": (
            "https://github.com/ofayese/matchpulse-live"
        ),
        "org.opencontainers.image.version": "24.04",
    }
    errors = hst.validate_oci_labels(labels, expected_revision=VALID_SHA)
    assert errors == []


@pytest.mark.parametrize(
    "labels,expected_rev,expected_sub",
    [
        ({}, None, "missing org.opencontainers.image.revision"),
        (
            {
                "OCI_REVISION": VALID_SHA,
                "OCI_SOURCE": "https://github.com/ofayese/matchpulse-live",
            },
            None,
            "missing org.opencontainers.image.revision",
        ),
        (
            {
                "org.opencontainers.image.revision": "short-sha",
                "org.opencontainers.image.source": (
            "https://github.com/ofayese/matchpulse-live"
        ),
            },
            None,
            "not a 40-character lowercase hex SHA",
        ),
        (
            {
                "org.opencontainers.image.revision": VALID_SHA.upper(),
                "org.opencontainers.image.source": (
            "https://github.com/ofayese/matchpulse-live"
        ),
            },
            None,
            "not a 40-character lowercase hex SHA",
        ),
        (
            {
                "org.opencontainers.image.revision": VALID_SHA,
                "org.opencontainers.image.source": (
            "https://github.com/ofayese/matchpulse-live"
        ),
            },
            "0" * 40,
            "org.opencontainers.image.revision mismatch",
        ),
        (
            {
                "org.opencontainers.image.revision": VALID_SHA,
                "org.opencontainers.image.source": "",
            },
            None,
            "missing org.opencontainers.image.source",
        ),
        (
            {
                "org.opencontainers.image.revision": VALID_SHA,
                "org.opencontainers.image.source": (
            "https://example.invalid/other/repo"
        ),
            },
            None,
            "org.opencontainers.image.source mismatch",
        ),
    ],
)
def test_validate_oci_labels_rejects_missing_or_invalid_values(
    labels, expected_rev, expected_sub
):
    errors = hst.validate_oci_labels(labels, expected_revision=expected_rev)
    assert any(expected_sub in e for e in errors), errors


def test_main_rejects_unpinned_published_image():
    with pytest.raises(SystemExit) as exc:
        hst.main(
            ["--published-image", "ghcr.io/ofayese/matchpulse-live:latest"]
        )
    assert exc.value.code == 1


def test_main_rejects_invalid_expected_revision():
    with pytest.raises(SystemExit) as exc:
        hst.main(
            [
                "--local-image",
                "matchpulse-live:test",
                "--expected-revision",
                "not-a-sha",
            ]
        )
    assert exc.value.code == 1


def test_review_log_fails_closed_on_secret_or_external_url(monkeypatch):
    def fake_docker(arguments, *, stdin=None):
        _ = stdin
        return subprocess.CompletedProcess(
            args=["docker", *arguments],
            returncode=0,
            stdout=(
                "WARNING: leaked api_key=secret123 "
                "and contacted https://api.openai.com/v1\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(hst, "docker", fake_docker)
    failures = hst.review_log("mp-fake")
    assert failures >= 2


def test_run_removes_container_and_fails_closed_when_checks_fail(monkeypatch):
    calls: list[list[str]] = []

    def fake_docker(arguments, *, stdin=None):
        _ = stdin
        calls.append(list(arguments))
        if arguments[:2] == ["image", "inspect"]:
            return subprocess.CompletedProcess(
                args=["docker", *arguments],
                returncode=0,
                stdout=json.dumps(
                    {
                        "org.opencontainers.image.revision": VALID_SHA,
                        "org.opencontainers.image.source": (
            "https://github.com/ofayese/matchpulse-live"
        ),
                    }
                ),
                stderr="",
            )
        if arguments[0] == "run":
            return subprocess.CompletedProcess(
                args=["docker", *arguments],
                returncode=0,
                stdout="cid123\n",
                stderr="",
            )
        if arguments[0] == "inspect":
            fmt = arguments[-1]
            if "HostConfig" in fmt:
                return subprocess.CompletedProcess(
                    args=["docker", *arguments],
                    returncode=0,
                    stdout=json.dumps(
                        {
                            "NetworkMode": "none",
                            "ReadonlyRootfs": True,
                            "CapDrop": ["ALL"],
                            "CapAdd": None,
                            "SecurityOpt": ["no-new-privileges:true"],
                            "Privileged": False,
                            "Binds": [],
                            "PidsLimit": 256,
                            "Memory": 536870912,
                            "NanoCpus": 1000000000,
                            "Tmpfs": {
                                "/tmp": "rw,noexec,nosuid,nodev,size=16m"
                            },
                            "PortBindings": {},
                        }
                    ),
                    stderr="",
                )
            if "Config" in fmt:
                return subprocess.CompletedProcess(
                    args=["docker", *arguments],
                    returncode=0,
                    stdout=json.dumps(
                        {
                            "User": "10001:10001",
                            "Env": [
                                "CHALLENGE_SYNTHETIC_ONLY=true",
                                "PATH=/usr/bin",
                            ],
                        }
                    ),
                    stderr="",
                )
            return subprocess.CompletedProcess(
                args=["docker", *arguments],
                returncode=0,
                stdout="[]",
                stderr="",
            )
        if arguments[0] == "exec" and stdin is not None:
            return subprocess.CompletedProcess(
                args=["docker", *arguments],
                returncode=1,
                stdout="FAIL: endpoint\n",
                stderr="",
            )
        if arguments[0] == "exec":
            return subprocess.CompletedProcess(
                args=["docker", *arguments],
                returncode=0,
                stdout="/usr/bin/python3.12\n",
                stderr="",
            )
        if arguments[:2] == ["rm", "-f"]:
            return subprocess.CompletedProcess(
                args=["docker", *arguments],
                returncode=0,
                stdout="removed\n",
                stderr="",
            )
        return subprocess.CompletedProcess(
            args=["docker", *arguments], returncode=0, stdout="", stderr=""
        )

    monkeypatch.setattr(hst, "docker", fake_docker)
    rc = hst.run(
        "matchpulse-live:test",
        events=5,
        seed=27,
        pull=False,
        expected_revision=VALID_SHA,
    )
    assert rc == 1
    assert any(c[:2] == ["rm", "-f"] for c in calls)
