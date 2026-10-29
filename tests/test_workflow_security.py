# cspell:ignore containerapp cognitiveservices opencontainers
"""Positive and negative security tests for the protected release workflow and Dockerfile OCI labels."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "release-attest.yml"
DOCKERFILE_PATH = ROOT / "Dockerfile"


def _extract_job_block(workflow_text: str, job_name: str) -> str:
    pattern = re.compile(
        rf"(?ms)^  {re.escape(job_name)}:\n(.*?)(?=^  [a-zA-Z0-9_-]+:\n|\Z)"
    )
    match = pattern.search(workflow_text)
    if not match:
        raise ValueError(f"job '{job_name}' not found in workflow")
    return match.group(1)


def validate_release_workflow_security(workflow_text: str) -> list[str]:
    """Validate all Gate 10 security invariants on release-attest.yml text and return any violations."""
    errors: list[str] = []

    if "workflow_dispatch:" not in workflow_text:
        errors.append("workflow_dispatch trigger is missing")

    if "expected_commit:" not in workflow_text or "required: true" not in workflow_text:
        errors.append(
            "explicit required expected_commit input is missing from workflow_dispatch"
        )

    if "remediation/pebble-removal" in workflow_text:
        errors.append("stale remediation/pebble-removal branch reference still present")

    if "release-approval:" in workflow_text or "build-publish-attest:" in workflow_text:
        errors.append("legacy post-publication approval job structure still present")

    # Top-level permissions must be read-only
    top_perm_match = re.search(
        r"(?ms)^permissions:\n(.*?)(?=^[a-zA-Z0-9_-]+:)", workflow_text
    )
    if not top_perm_match:
        errors.append("top-level permissions block is missing")
    else:
        top_perm = top_perm_match.group(1)
        if "contents: read" not in top_perm:
            errors.append("top-level permissions must grant contents: read")
        for write_perm in ("packages: write", "id-token: write", "attestations: write"):
            if write_perm in top_perm:
                errors.append(f"top-level permissions must not grant '{write_perm}'")

    try:
        validate_block = _extract_job_block(workflow_text, "validate")
    except ValueError as exc:
        errors.append(str(exc))
        validate_block = ""

    try:
        publish_block = _extract_job_block(workflow_text, "publish")
    except ValueError as exc:
        errors.append(str(exc))
        publish_block = ""

    if validate_block:
        if "github.ref == 'refs/heads/main'" not in validate_block:
            errors.append(
                "validate job does not enforce github.ref == 'refs/heads/main'"
            )
        for forbidden_in_validate in (
            "docker/login-action",
            "docker push",
            "actions/attest",
            "packages: write",
            "id-token: write",
            "attestations: write",
            "push: true",
        ):
            if forbidden_in_validate in validate_block:
                errors.append(
                    f"validate job must not contain '{forbidden_in_validate}'"
                )
        if "push: false" not in validate_block:
            errors.append("validate job must build locally with push: false")
        if "OCI_REVISION=${{ env.RELEASE_COMMIT }}" not in validate_block:
            errors.append(
                "validate job must pass OCI_REVISION=${{ env.RELEASE_COMMIT }}"
            )
        if "OCI_SOURCE=https://github.com/${{ env.REPOSITORY }}" not in validate_block:
            errors.append(
                "validate job must pass OCI_SOURCE=https://github.com/${{ env.REPOSITORY }}"
            )
        if "scripts/hardened_smoke_test.py" not in validate_block:
            errors.append("validate job must run scripts/hardened_smoke_test.py")

    if publish_block:
        if (
            "needs: [validate]" not in publish_block
            and "needs: validate" not in publish_block
        ):
            errors.append("publish job must depend on validate job (needs: [validate])")
        if "environment: release-attestation" not in publish_block:
            errors.append(
                "publish job must be gated by environment: release-attestation"
            )
        if "github.ref == 'refs/heads/main'" not in publish_block:
            errors.append(
                "publish job does not enforce github.ref == 'refs/heads/main'"
            )
        for required_in_publish in (
            "packages: write",
            "id-token: write",
            "attestations: write",
            "docker/login-action",
            "docker push",
            "actions/attest",
            "subject-name: ghcr.io/ofayese/matchpulse-live",
            "subject-digest: ${{ steps.digest.outputs.digest }}",
            "--source-ref",
            "--source-digest",
        ):
            if required_in_publish not in publish_block:
                errors.append(f"publish job is missing '{required_in_publish}'")

    if ":latest" in workflow_text:
        errors.append("mutable ':latest' tag must not be used in release-attest.yml")

    for azure_forbidden in (
        "azure/login",
        "az deployment",
        "az group",
        "az containerapp",
        "az cognitiveservices",
    ):
        if azure_forbidden in workflow_text:
            errors.append(
                f"release workflow must not perform Azure operation '{azure_forbidden}'"
            )

    return errors


def validate_dockerfile_oci_labels(dockerfile_text: str) -> list[str]:
    """Validate that Dockerfile declares ARG and standard OCI LABEL instructions in the runtime stage."""
    errors: list[str] = []
    runtime_split = dockerfile_text.split("AS runtime", 1)
    if len(runtime_split) != 2:
        return ["Dockerfile is missing 'AS runtime' stage"]
    runtime_stage = runtime_split[1]
    if not re.search(r"(?m)^ARG\s+OCI_REVISION\s*$", runtime_stage):
        errors.append("Dockerfile runtime stage is missing 'ARG OCI_REVISION'")
    if not re.search(r"(?m)^ARG\s+OCI_SOURCE\s*$", runtime_stage):
        errors.append("Dockerfile runtime stage is missing 'ARG OCI_SOURCE'")
    if not re.search(
        r"(?m)^LABEL\s+org\.opencontainers\.image\.revision=\$OCI_REVISION\s*$",
        runtime_stage,
    ):
        errors.append(
            "Dockerfile runtime stage is missing 'LABEL org.opencontainers.image.revision=$OCI_REVISION'"
        )
    if not re.search(
        r"(?m)^LABEL\s+org\.opencontainers\.image\.source=\$OCI_SOURCE\s*$",
        runtime_stage,
    ):
        errors.append(
            "Dockerfile runtime stage is missing 'LABEL org.opencontainers.image.source=$OCI_SOURCE'"
        )
    return errors


def test_release_workflow_passes_all_security_invariants():
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert validate_release_workflow_security(text) == []
    assert (ROOT / "scripts" / "hardened_smoke_test.py").is_file()
    assert (ROOT / "scripts" / "validate_attestation_verification.py").is_file()


def test_dockerfile_declares_standard_oci_args_and_labels():
    text = DOCKERFILE_PATH.read_text(encoding="utf-8")
    assert validate_dockerfile_oci_labels(text) == []


@pytest.mark.parametrize(
    "mutator,expected_error_substring",
    [
        (
            lambda t: t.replace(
                "environment: release-attestation", "environment: unsecured"
            ),
            "publish job must be gated by environment: release-attestation",
        ),
        (
            lambda t: t.replace(
                "github.ref == 'refs/heads/main'",
                "github.ref == 'refs/heads/remediation/pebble-removal'",
            ),
            "stale remediation/pebble-removal branch reference still present",
        ),
        (
            lambda t: t.replace(
                "permissions:\n  contents: read",
                "permissions:\n  contents: read\n  packages: write",
            ),
            "top-level permissions must not grant 'packages: write'",
        ),
        (
            lambda t: t.replace(
                "      - name: Set up Python",
                "      - uses: docker/login-action@v3\n      - name: Set up Python",
            ),
            "validate job must not contain 'docker/login-action'",
        ),
        (
            lambda t: t.replace("needs: [validate]", ""),
            "publish job must depend on validate job",
        ),
        (
            lambda t: t
            + "\n      - run: docker push ghcr.io/ofayese/matchpulse-live:latest\n",
            "mutable ':latest' tag must not be used",
        ),
        (
            lambda t: t + "\n      - run: az deployment group create\n",
            "release workflow must not perform Azure operation 'az deployment'",
        ),
    ],
)
def test_release_workflow_validator_rejects_unsafe_mutations(
    mutator, expected_error_substring
):
    base_text = WORKFLOW_PATH.read_text(encoding="utf-8")
    mutated = mutator(base_text)
    errors = validate_release_workflow_security(mutated)
    assert any(expected_error_substring in err for err in errors), errors


@pytest.mark.parametrize(
    "mutator,expected_error_substring",
    [
        (
            lambda t: t.replace("ARG OCI_REVISION\n", ""),
            "missing 'ARG OCI_REVISION'",
        ),
        (
            lambda t: t.replace("ARG OCI_SOURCE\n", ""),
            "missing 'ARG OCI_SOURCE'",
        ),
        (
            lambda t: t.replace(
                "LABEL org.opencontainers.image.revision=$OCI_REVISION\n", ""
            ),
            "missing 'LABEL org.opencontainers.image.revision=$OCI_REVISION'",
        ),
        (
            lambda t: t.replace(
                "LABEL org.opencontainers.image.source=$OCI_SOURCE\n", ""
            ),
            "missing 'LABEL org.opencontainers.image.source=$OCI_SOURCE'",
        ),
    ],
)
def test_dockerfile_validator_rejects_missing_oci_instructions(
    mutator, expected_error_substring
):
    base_text = DOCKERFILE_PATH.read_text(encoding="utf-8")
    mutated = mutator(base_text)
    errors = validate_dockerfile_oci_labels(mutated)
    assert any(expected_error_substring in err for err in errors), errors
