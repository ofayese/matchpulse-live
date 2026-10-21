"""Check the Phase A2 release workflow security contract without executing it."""

from __future__ import annotations

import sys
from pathlib import Path

CONDITION = "github.event_name == 'workflow_dispatch' &&"
BRANCH_CONDITION = "github.ref == 'refs/heads/remediation/pebble-removal'"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".github/workflows/release-attest.yml")
    workflow = path.read_text(encoding="utf-8")
    challenge = Path(".github/workflows/challenge-ci.yml").read_text(encoding="utf-8")
    smoke = Path("scripts/hardened_smoke_test.py").read_text(encoding="utf-8")

    require("name: release-attest" in workflow, "release-attest.yml is not named release-attest")
    permissions = "permissions:\n  contents: read\n  packages: write\n  id-token: write\n  attestations: write"
    require(permissions in workflow, "release workflow permissions differ from the approved set")
    require("artifact-metadata:" not in workflow, "unexpected artifact-metadata permission")
    require(workflow.count(CONDITION) == 2 and workflow.count(BRANCH_CONDITION) == 2,
            "both release jobs must use the workflow_dispatch and remediation-branch condition")

    build = workflow.split("  build-publish-attest:", 1)[1].split("  release-approval:", 1)[0]
    approval = workflow.split("  release-approval:", 1)[1]
    require("environment:" not in build, "the build job must not use a protected environment")
    require("needs: [build-publish-attest]" in approval, "approval must depend on the build job")
    require("environment: release-attestation" in approval, "approval must use release-attestation")

    ordered = [
        "Build the image locally with push disabled",
        "Run hardened smoke against the local image",
        "Block on HIGH or CRITICAL vulnerabilities",
        "Log in to GHCR",
        "Push the scanned image under the immutable full-SHA tag",
        "Resolve the immutable digest",
        "Generate artifact attestation",
        "Verify the attestation publicly",
        "Verify an anonymous digest pull and the source binding",
        "Rescan the published digest",
        "Run the hardened runtime smoke against the published digest",
        "Hand the digest to the independent auditor",
    ]
    positions = [build.find(name) for name in ordered]
    require(all(position >= 0 for position in positions), "a required build/publish/attest gate is missing")
    require(positions == sorted(positions), "release gates are out of order")
    require(build.count("uses: docker/build-push-action@") == 1, "the release job must build exactly once")
    require("push: false" in build, "the image build must have push disabled")
    require("uses: actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6 # v4" in build,
            "the attestation action must remain SHA-pinned v4")
    require("custom in-toto" not in workflow.lower(), "custom in-toto authoring is prohibited")
    for required in ("Revalidate commit, digest and gate evidence", "Re-run the published digest scan and hardened smoke",
                     "Re-verify the approved digest and its attestation"):
        require(required in approval, f"approval does not revalidate: {required}")
    require("docker/build-push-action@" not in approval and "docker/login-action@" not in approval
            and "actions/attest@" not in approval and "docker push" not in approval,
            "the protected approval job must not rebuild, publish or attest")
    require("release-attest.yml" in challenge and "Phase A2 release workflow audit" in challenge,
            "challenge-ci.yml must audit the named release workflow")
    require("docker/login-action@" not in challenge and "actions/attest@" not in challenge
            and "docker push" not in challenge,
            "challenge-ci.yml must remain non-publishing")
    require('"run", "--pull=never"' in smoke and 'if pull:' in smoke and 'docker_text(["pull", image])' in smoke,
            "local smoke must never pull and published smoke must pull explicitly")
    for hardening in ('"--network", "none"', '"--user", RUNTIME_USER', '"--read-only"',
                      '"--tmpfs", TMPFS', '"--cap-drop", "ALL"',
                      '"--security-opt", "no-new-privileges:true"', '"--pids-limit", PIDS_LIMIT',
                      '"--memory", MEMORY_LIMIT', '"--cpus", CPU_LIMIT',
                      '"CHALLENGE_SYNTHETIC_ONLY=true"'):
        require(hardening in smoke, f"hardened smoke is missing {hardening}")
    for readiness in ('ready', 'synthetic_only', 'foundry_mode', 'telemetry_mode'):
        require(readiness in smoke, f"hardened smoke does not check readiness field {readiness}")

    print(f"PASS: Phase A2 release contract audited in {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
