import os
import subprocess
import sys
from pathlib import Path

import pytest

# Add scripts directory to path to import validator
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


# Constants for tests
SUBJECT_NAME = "ghcr.io/ofayese/matchpulse-live"
SUBJECT_DIGEST = (
    "1bb9df336d95a5549f7384e023c5954710c662f59d6fb9b9ac2d72ed3ee0c96c"
)
COMMIT = "e228610a6d220f5532b0d8d3baac0a629db14208"

FIXTURE_DIR = Path(__file__).parent / "attestation_fixtures"


def run_validator_script(fixture_path, subject_name, subject_digest, commit):
    """Runs the validation script as a subprocess."""
    script_path = (
        Path(__file__).parent.parent
        / "scripts"
        / "validate_attestation_verification.py"
    )
    cmd = [
        sys.executable,
        str(script_path),
        "--input",
        str(fixture_path),
        "--subject-name",
        subject_name,
        "--subject-digest",
        subject_digest,
        commit,
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


@pytest.mark.parametrize(
    "fixture_file",
    [
        "positive_minimal.json",
        "positive_multiple_deps.json",
    ],
)
def test_positive_fixtures(fixture_file):
    """Tests that valid fixtures pass validation."""
    fixture_path = FIXTURE_DIR / fixture_file
    result = run_validator_script(
        fixture_path, SUBJECT_NAME, SUBJECT_DIGEST, COMMIT
    )
    assert result.returncode == 0, (
        f"Validator script failed on {fixture_file}: {result.stderr}"
    )


def test_real_attestation_fixture():
    """Tests the real attestation from the failed workflow run."""
    evidence_fixture = os.environ.get("MATCHPULSE_REAL_ATTESTATION_FIXTURE")
    if not evidence_fixture:
        pytest.skip("Set MATCHPULSE_REAL_ATTESTATION_FIXTURE to run the optional real attestation test.")
    fixture_path = Path(evidence_fixture).expanduser()
    if not fixture_path.is_file():
        pytest.skip("Configured real attestation fixture not found.")

    result = run_validator_script(
        fixture_path, SUBJECT_NAME, SUBJECT_DIGEST, COMMIT
    )
    assert result.returncode == 0, (
        f"Validator script failed on real attestation: {result.stderr}"
    )


@pytest.mark.parametrize(
    "fixture_file, subject_name, subject_digest, commit",
    [
        (
            "negative_wrong_subject_name.json",
            SUBJECT_NAME,
            SUBJECT_DIGEST,
            COMMIT,
        ),
        (
            "negative_wrong_subject_digest.json",
            SUBJECT_NAME,
            SUBJECT_DIGEST,
            COMMIT,
        ),
        ("negative_wrong_commit.json", SUBJECT_NAME, SUBJECT_DIGEST, COMMIT),
        ("negative_missing_commit.json", SUBJECT_NAME, SUBJECT_DIGEST, COMMIT),
        ("negative_empty_deps.json", SUBJECT_NAME, SUBJECT_DIGEST, COMMIT),
    ],
)
def test_negative_fixtures(fixture_file, subject_name, subject_digest, commit):
    """Tests that invalid fixtures fail validation."""
    fixture_path = FIXTURE_DIR / fixture_file
    result = run_validator_script(
        fixture_path, subject_name, subject_digest, commit
    )
    assert result.returncode != 0, (
        f"Validator script should have failed on {fixture_file}, but it passed."
    )


def test_malformed_json():
    """Tests that malformed JSON is handled."""
    fixture_path = FIXTURE_DIR / "negative_malformed.json"
    result = run_validator_script(
        fixture_path, SUBJECT_NAME, SUBJECT_DIGEST, COMMIT
    )
    assert result.returncode != 0
    assert (
        "ERROR: Expected a JSON array with a single element." in result.stderr
    )
