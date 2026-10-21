"""Verify the immutable release image binding used by the release attestation.

The script carries no hard coded release identity. Every value it verifies is
supplied on the command line by the calling workflow, so the workflow file
stays the single reviewable source of truth for the release identity.

Two checks are available.

``digest``
    Resolve the image manifest anonymously from the registry, hash the
    returned manifest bytes and require the hash to equal the expected
    digest. The OCI configuration blob is hashed as well and the declared
    runtime user is required to be a non-root user.

``source``
    Bind the image to a source commit independently of the attestation that is
    about to be created. The application package inside the published image is
    compared byte for byte with the same package in the source commit, and the
    public GitHub run record of the publishing workflow is required to show a
    successful run of a GitHub-hosted runner at that commit.

The script never logs in to the registry, never prints a credential and uses
only the standard library. A GitHub API token is used only when one is
supplied, and it is only ever sent to the GitHub API host.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import urllib.error
import urllib.request
from pathlib import Path

MANIFEST_ACCEPT = ", ".join(
    [
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
        "application/vnd.oci.image.index.v1+json",
    ]
)
SLSA_PROVENANCE_PREDICATE_TYPE = "https://slsa.dev/provenance/v1"
GITHUB_API = "https://api.github.com"


class VerificationError(Exception):
    """A verification requirement was not met."""


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def http_get(url: str, headers: dict[str, str] | None = None) -> tuple[int, bytes]:
    request = urllib.request.Request(url)
    for name, value in (headers or {}).items():
        request.add_header(name, value)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def registry_pull_token(registry: str, repository: str) -> str:
    """Obtain an anonymous pull token for a public container repository."""
    url = f"https://{registry}/token?scope=repository:{repository}:pull&service={registry}"
    status, body = http_get(url, {"Accept": "application/json"})
    if status != 200:
        raise VerificationError(f"the registry token endpoint returned HTTP {status}")
    payload = json.loads(body)
    token = payload.get("token") or payload.get("access_token")
    if not token:
        raise VerificationError("the registry did not return an anonymous pull token")
    return token


def registry_get(registry: str, repository: str, path: str, token: str, accept: str | None = None) -> bytes:
    headers = {"Authorization": f"Bearer {token}"}
    if accept:
        headers["Accept"] = accept
    status, body = http_get(f"https://{registry}/v2/{repository}/{path}", headers)
    if status != 200:
        raise VerificationError(f"the registry returned HTTP {status} for {path}")
    return body


def fetch_manifest(registry: str, repository: str, digest: str, token: str) -> bytes:
    return registry_get(registry, repository, f"manifests/{digest}", token, MANIFEST_ACCEPT)


def expected_digest_hex(digest: str) -> str:
    if not digest.startswith("sha256:"):
        raise VerificationError(f"the expected digest is not a sha256 digest: {digest}")
    value = digest.removeprefix("sha256:")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise VerificationError(f"the expected digest is not a full lowercase sha256 digest: {digest}")
    return value


def check_digest(registry: str, repository: str, digest: str) -> dict[str, object]:
    """Resolve the image anonymously and require the manifest bytes to hash to the expected digest."""
    expected = expected_digest_hex(digest)
    token = registry_pull_token(registry, repository)
    manifest_bytes = fetch_manifest(registry, repository, digest, token)
    computed = sha256_hex(manifest_bytes)
    if computed != expected:
        raise VerificationError(f"the manifest bytes hash to {computed} instead of {expected}")
    manifest = json.loads(manifest_bytes)
    config_digest = manifest.get("config", {}).get("digest")
    if not config_digest:
        raise VerificationError("the manifest does not reference an OCI configuration blob")
    config_bytes = registry_get(registry, repository, f"blobs/{config_digest}", token)
    computed_config = sha256_hex(config_bytes)
    if computed_config != config_digest.removeprefix("sha256:"):
        raise VerificationError("the OCI configuration blob does not match the digest in the manifest")
    config = json.loads(config_bytes)
    user = config.get("config", {}).get("User") or ""
    if not user or user in {"0", "root"}:
        raise VerificationError(f"the image does not declare a non-root runtime user: {user!r}")
    layers = manifest.get("layers") or []
    if not layers:
        raise VerificationError("the manifest does not contain any layer")
    print(f"PASS: the manifest bytes hash to {digest}")
    print(f"PASS: the OCI configuration blob matches {config_digest}")
    print(f"PASS: the image declares the non-root runtime user {user}")
    return {"manifest": manifest, "config": config, "config_digest": config_digest}


def extract_package(manifest: dict[str, object], registry: str, repository: str, token: str, prefix: str) -> dict[str, str]:
    """Return the sha256 of every regular file of a package directory inside the image."""
    package: dict[str, str] = {}
    for layer in manifest.get("layers") or []:
        digest = layer.get("digest")
        if not digest:
            raise VerificationError("a layer of the manifest does not reference a digest")
        blob = registry_get(registry, repository, f"blobs/{digest}", token)
        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as archive:
            for member in archive.getmembers():
                if not member.isfile():
                    continue
                name = member.name[2:] if member.name.startswith("./") else member.name
                if not name.startswith(f"{prefix}/"):
                    continue
                relative = name[len(prefix) + 1 :]
                if "/" in relative:
                    continue
                extracted = archive.extractfile(member)
                if extracted is None:
                    raise VerificationError(f"the layer entry {name} could not be read")
                package[relative] = sha256_hex(extracted.read())
    if not package:
        raise VerificationError(f"the image does not contain a package at {prefix}")
    return package


def git_output(*arguments: str, cwd: Path) -> str:
    completed = subprocess.run(  # noqa: S603
        ["git", *arguments],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise VerificationError(f"git {' '.join(arguments)} failed: {completed.stderr.strip()}")
    return completed.stdout


def git_tree_package(repository_root: Path, commit: str, path: str) -> dict[str, str]:
    """Return the sha256 of every file of a directory in the tree of a commit."""
    listing = git_output("ls-tree", "-r", commit, "--", path, cwd=repository_root)
    package: dict[str, str] = {}
    for line in listing.splitlines():
        if not line.strip():
            continue
        header, _, name = line.partition("\t")
        fields = header.split()
        if len(fields) != 3 or fields[1] != "blob":
            continue
        relative = name[len(path) + 1 :] if name.startswith(f"{path}/") else name
        blob = subprocess.run(  # noqa: S603
            ["git", "cat-file", "blob", f"{commit}:{name}"],
            cwd=repository_root,
            capture_output=True,
            check=False,
        )
        if blob.returncode != 0:
            raise VerificationError(f"the blob {name} could not be read from {commit}")
        package[relative] = sha256_hex(blob.stdout)
    if not package:
        raise VerificationError(f"the commit {commit} does not contain a package at {path}")
    return package


def github_api(path: str, token: str | None) -> tuple[int, bytes]:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return http_get(f"{GITHUB_API}{path}", headers)


def github_json(path: str, token: str | None) -> tuple[int, dict[str, object]]:
    status, body = github_api(path, token)
    if status != 200:
        return status, {}
    try:
        return status, json.loads(body)
    except json.JSONDecodeError as error:
        raise VerificationError(f"the GitHub API returned a malformed document for {path}") from error


def check_publish_run(
    source_repository: str,
    source_commit: str,
    publish_run_id: str,
    publish_workflow_path: str,
    token: str | None,
) -> None:
    """Require the publishing run to be a successful GitHub-hosted run at the source commit."""
    status, run = github_json(f"/repos/{source_repository}/actions/runs/{publish_run_id}", token)
    if status != 200:
        raise VerificationError(f"the publishing run {publish_run_id} is not available (HTTP {status})")
    if run.get("head_sha") != source_commit:
        raise VerificationError(f"the publishing run was not executed at {source_commit}")
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        raise VerificationError(f"the publishing run did not succeed: {run.get('conclusion')}")
    if run.get("path") != publish_workflow_path:
        raise VerificationError(f"the publishing run used {run.get('path')} instead of {publish_workflow_path}")
    head_repository = run.get("head_repository") or {}
    if head_repository.get("full_name") != source_repository:
        raise VerificationError("the publishing run did not belong to the source repository")
    status, jobs = github_json(f"/repos/{source_repository}/actions/runs/{publish_run_id}/jobs", token)
    if status != 200:
        raise VerificationError(f"the jobs of the publishing run are not available (HTTP {status})")
    job_list = jobs.get("jobs") or []
    if not job_list:
        raise VerificationError("the publishing run does not report any job")
    for job in job_list:
        if job.get("conclusion") != "success":
            raise VerificationError(f"the job {job.get('name')} of the publishing run did not succeed")
        if job.get("runner_group_name") != "GitHub Actions":
            raise VerificationError(f"the job {job.get('name')} of the publishing run was not GitHub-hosted")
        labels = job.get("labels") or []
        if "self-hosted" in labels:
            raise VerificationError(f"the job {job.get('name')} of the publishing run used a self-hosted runner")
    print(f"PASS: the publishing run {publish_run_id} succeeded at {source_commit} on a GitHub-hosted runner")


def check_existing_attestations(
    source_repository: str,
    digest: str,
    source_commit: str,
    token: str | None,
) -> None:
    """Require that no pre-existing attestation binds the subject to a different source commit."""
    status, body = github_api(f"/repos/{source_repository}/attestations/{digest}", token)
    if status == 404:
        print(f"NOTE: no artifact attestation exists yet for {digest}")
        return
    if status != 200:
        raise VerificationError(f"the attestations API returned HTTP {status} for {digest}")
    record = json.loads(body)
    attestations = record.get("attestations") or []
    print(f"NOTE: {len(attestations)} pre-existing attestation(s) are recorded for {digest}")
    for attestation in attestations:
        envelope = (attestation.get("bundle") or {}).get("dsseEnvelope") or {}
        payload = envelope.get("payload")
        if not isinstance(payload, str) or not payload:
            raise VerificationError("a pre-existing attestation does not expose a DSSE payload")
        try:
            statement = json.loads(base64.b64decode(payload))
        except (ValueError, json.JSONDecodeError) as error:
            raise VerificationError("a pre-existing attestation does not expose a decodable in-toto statement") from error
        subjects = statement.get("subject") or []
        for subject in subjects:
            subject_digest = (subject.get("digest") or {}).get("sha256")
            if subject_digest and subject_digest != digest.removeprefix("sha256:"):
                raise VerificationError("a pre-existing attestation declares a different subject digest")
        predicate_type = statement.get("predicateType")
        if predicate_type == SLSA_PROVENANCE_PREDICATE_TYPE:
            predicate = statement.get("predicate") or {}
            sources = collect_slsa_source_commits(predicate)
            if not sources:
                raise VerificationError("a pre-existing SLSA provenance attestation does not name a source commit")
            if any(source != source_commit for source in sources):
                raise VerificationError(
                    "a pre-existing SLSA provenance attestation binds the image to a different source commit"
                )
            print("PASS: a pre-existing SLSA provenance attestation binds the image to the source commit")
        else:
            print(f"NOTE: a pre-existing attestation has the predicate type {predicate_type}")


def collect_slsa_source_commits(predicate: dict[str, object]) -> set[str]:
    """Collect the source commits named by a SLSA provenance predicate."""
    commits: set[str] = set()
    build_definition = predicate.get("buildDefinition") or {}
    external_parameters = build_definition.get("externalParameters") or {}
    source = external_parameters.get("source")
    if isinstance(source, dict):
        for digest in (source.get("digest") or {}).values():
            if isinstance(digest, str) and digest.startswith("git+"):
                commits.add(digest.removeprefix("git+"))
    for dependency in build_definition.get("resolvedDependencies") or []:
        if not isinstance(dependency, dict):
            continue
        for digest in (dependency.get("digest") or {}).values():
            if isinstance(digest, str) and len(digest) == 40:
                commits.add(digest)
    materials = external_parameters.get("materials")
    for material in materials or []:
        if isinstance(material, dict) and isinstance(material.get("uri"), str) and "@" in material["uri"]:
            commits.add(material["uri"].rsplit("@", 1)[1])
    return {commit for commit in commits if len(commit) == 40}


def check_source(
    registry: str,
    repository: str,
    digest: str,
    source_repository: str,
    source_commit: str,
    publish_run_id: str,
    publish_workflow_path: str,
    image_package_path: str,
    source_package_path: str,
    repository_root: Path,
    token: str | None,
) -> None:
    """Bind the published image to the source commit independently of the attestation."""
    expected = expected_digest_hex(digest)
    token_value = registry_pull_token(registry, repository)
    manifest_bytes = fetch_manifest(registry, repository, digest, token_value)
    if sha256_hex(manifest_bytes) != expected:
        raise VerificationError("the manifest bytes do not hash to the expected digest")
    manifest = json.loads(manifest_bytes)

    resolved = git_output("rev-parse", "--verify", f"{source_commit}^{{commit}}", cwd=repository_root).strip()
    if resolved != source_commit:
        raise VerificationError(f"the source commit {source_commit} is not present in the checkout")
    ancestry = subprocess.run(  # noqa: S603
        ["git", "merge-base", "--is-ancestor", source_commit, "HEAD"],
        cwd=repository_root,
        capture_output=True,
        check=False,
    )
    if ancestry.returncode != 0:
        raise VerificationError(f"the source commit {source_commit} is not an ancestor of the attested commit")
    local_tree = git_output("rev-parse", "--verify", f"{source_commit}^{{tree}}", cwd=repository_root).strip()
    status, record = github_json(f"/repos/{source_repository}/commits/{source_commit}", token)
    if status != 200:
        raise VerificationError(f"the public commit record for {source_commit} is not available (HTTP {status})")
    if record.get("sha") != source_commit:
        raise VerificationError("the public commit record does not match the source commit")
    remote_tree = ((record.get("commit") or {}).get("tree") or {}).get("sha")
    if remote_tree != local_tree:
        raise VerificationError("the public commit record tree does not match the local tree")
    print(f"PASS: the public commit record agrees with the local tree {local_tree}")

    image_package = extract_package(manifest, registry, repository, token_value, image_package_path)
    source_package = git_tree_package(repository_root, source_commit, source_package_path)
    if set(image_package) != set(source_package):
        missing = sorted(set(source_package) - set(image_package))
        extra = sorted(set(image_package) - set(source_package))
        raise VerificationError(f"the image package and the source package differ: missing={missing} extra={extra}")
    for name in sorted(source_package):
        if image_package[name] != source_package[name]:
            raise VerificationError(f"the file {name} differs between the image and the source commit")
    print(f"PASS: {len(source_package)} application files are byte identical to {source_commit}")

    check_publish_run(source_repository, source_commit, publish_run_id, publish_workflow_path, token)
    check_existing_attestations(source_repository, digest, source_commit, token)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify the immutable release image binding.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    digest_parser = subparsers.add_parser("digest", help="Check the immutable image digest.")
    digest_parser.add_argument("--registry", required=True)
    digest_parser.add_argument("--repository", required=True)
    digest_parser.add_argument("--digest", required=True)

    source_parser = subparsers.add_parser("source", help="Check the independent source binding.")
    source_parser.add_argument("--registry", required=True)
    source_parser.add_argument("--repository", required=True)
    source_parser.add_argument("--digest", required=True)
    source_parser.add_argument("--source-repository", required=True)
    source_parser.add_argument("--source-commit", required=True)
    source_parser.add_argument("--publish-run-id", required=True)
    source_parser.add_argument("--publish-workflow-path", required=True)
    source_parser.add_argument("--image-package-path", required=True)
    source_parser.add_argument("--source-package-path", required=True)
    source_parser.add_argument("--repository-root", default=".")
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    try:
        if arguments.command == "digest":
            check_digest(arguments.registry, arguments.repository, arguments.digest)
        else:
            check_source(
                registry=arguments.registry,
                repository=arguments.repository,
                digest=arguments.digest,
                source_repository=arguments.source_repository,
                source_commit=arguments.source_commit,
                publish_run_id=arguments.publish_run_id,
                publish_workflow_path=arguments.publish_workflow_path,
                image_package_path=arguments.image_package_path,
                source_package_path=arguments.source_package_path,
                repository_root=Path(arguments.repository_root).resolve(),
                token=os.environ.get("GITHUB_TOKEN", "").strip() or None,
            )
    except VerificationError as error:
        fail(str(error))
    print("PASS: the release binding is verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
