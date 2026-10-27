# Testing instructions

## Hosted judge path

The application was deployed and verified on Azure Container Apps. A fresh read-only check on 2026-10-26 confirmed that the app has no ingress configuration and uses the expected immutable image digest. The resource group contains five MatchPulse application/monitoring resources and two separately user-authorized Foundry development resources. Foundry runtime is disabled in the submitted MatchPulse deployment, and the demonstrated workflow makes zero model calls. The Foundry resources are not part of the submitted runtime, are not deployed by MatchPulse Bicep, and are not demonstrated in the approved video. Specific Azure resource identifiers are omitted from these public instructions. Judges can run the exact submitted container locally.

## Run the accepted immutable image locally

Judges can execute the immutable container image locally using Docker:

```bash
docker run --rm -p 8080:8080 \
  ghcr.io/ofayese/matchpulse-live@sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226
```

Open `http://127.0.0.1:8080/demo` on the same machine. This runs the verified application in an isolated container.

Artifact references for current submission candidate:
- Candidate revision: `335781f928011f99a644083d80bfe4dfc480b1a6`
- Image digest: `sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226`
- Attestation identifier: `59336499` (Workflow Run 40059698831)

These identifiers bind the image to the stated source revision. Application
and infrastructure changes in the current checkout are newer than that
revision and are not included in this image.

## Build and run from source

Requirements: Python 3.11+ or Docker.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest
uvicorn matchpulse.service:app --host 127.0.0.1 --port 8080
```

In a second terminal:

```bash
matchpulse-synthetic --delay .15 --events 50
```

Open `http://127.0.0.1:8080/demo`.

## Expected behavior

- `/health/ready` reports `synthetic_only: true`.
- Valid ordered synthetic events return HTTP 202.
- Duplicate event IDs are acknowledged without duplicating state.
- Out-of-order events return HTTP 409.
- Non-synthetic source values fail schema validation.
- Insights include source event IDs, calculation inputs, a formula, and confidence.
- English, Spanish, and French variants retain the same evidence.
- With Foundry unconfigured or disabled, `foundry_mode` reports `disabled`; the deterministic pipeline remains the only output and no model calls are made.
- A demo run has a unique match identifier, accepts at most 24 events, permits one concurrent run, and enforces a cooldown.

## Known MVP limits

- State is in process memory; restarting clears the demo match.
- Multi-replica WebSocket fan-out needs a managed backplane before production scale.
- Event Hubs is not deployed and has no active consumer, checkpoint store, or processed-message trace. The baseline uses `POST /v1/events`.
- The current app has no ingress configuration; a public hosted endpoint is not enabled.
- Microsoft Foundry runtime was disabled in the deployed configuration (0 model calls).
- Languages beyond English, Spanish, and French need reviewed templates or a translation adapter.
