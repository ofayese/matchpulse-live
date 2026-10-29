import hashlib
import json
from pathlib import Path


def test_release_policy_consistency():
    root = Path(__file__).parent.parent
    policy_path = root / ".github" / "release-policy.json"
    workflow_path = root / ".github" / "workflows" / "release-attest.yml"

    assert policy_path.exists()
    assert workflow_path.exists()

    with open(policy_path, encoding="utf-8") as f:
        policy = json.load(f)

    with open(workflow_path, "rb") as f:
        workflow_bytes = f.read()

    actual_sha256 = hashlib.sha256(workflow_bytes).hexdigest()

    assert policy["workflow_path"] == ".github/workflows/release-attest.yml"
    assert policy["workflow_sha256"] == actual_sha256
    assert policy["allowed_publication_branch"] == "main"
    assert policy["required_environment"] == "release-attestation"
    assert policy["required_distinct_human_approval"] is True
    assert policy["self_review_prohibited"] is True
    assert policy["admin_bypass_prohibited"] is True
    assert policy["immutable_sha_tag_required"] is True
    assert policy["standard_oci_revision_required"] is True
    assert policy["standard_oci_source_required"] is True
    assert policy["final_digest_audit_required"] is True
    assert policy["azure_deployment_coupled"] is False
