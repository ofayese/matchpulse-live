# Protected Publication Approval

This document describes the exact release contract required for publishing the MatchPulse Live container image.

## Release Policy
- **Workflow**: .github/workflows/release-attest.yml
- **Workflow SHA-256**: 366278d67e4917b4173838ae35fa380d8f89866f75b6464a2e3fef6365124ed8
- **Approval-before-publication**: A validation job checks all constraints without pushing or attesting. The publishing job runs in the elease-attestation environment and requires explicit human approval before registry login, push, or attestation generation.
- **Main dispatch contract**: Publication can only be dispatched from efs/heads/main.
- **Expected-commit check**: The dispatch SHA must exactly match the current origin/main tip.
- **GHCR Target**: Images are pushed to the GitHub Container Registry.
- **OCI-label contract**: Published images must include standard OCI source and revision labels.
- **Hardened smoke contract**: The container runs in a hardened unprivileged sandbox (read-only rootfs, dropped capabilities, no-new-privileges) without crashing or emitting secrets.
- **Attestation contract**: A SLSA v1 build provenance attestation is generated and publicly verified.
- **Current environment limitation**: The elease-attestation environment policy currently permits only the emediation/pebble-removal branch.
- **Required policy migration**: The environment policy must be migrated to permit only main.
- **Publication prohibition**: Publication is explicitly prohibited until the environment policy is migrated and fresh authorization is acquired.
