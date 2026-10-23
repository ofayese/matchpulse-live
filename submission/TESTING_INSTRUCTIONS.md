# Testing instructions

## Hosted judge path

**Unavailable.** There is no verified public HTTPS demo URL. The supplied registration confirmation is dated October 20, 2026 at 1:29 PM Eastern, before the stated 3:00 PM Eastern cutoff. No Azure resources were deployed because an approved subscription, resource group, region, budget ceiling, and explicit cost authorization were not provided. The hosted-demo and video gates remain incomplete.

## Run the accepted immutable image locally

The following image reference is the previously accepted artifact supplied for this task. It is pinned by digest; this command does not prove that a public demo is available:

```bash
docker run --rm -p 8080:8080 \
  ghcr.io/ofayese/matchpulse-live@sha256:1bb9df336d95a5549f7384e023c5954710c662f59d6fb9b9ac2d72ed3ee0c96c
```

Open `http://127.0.0.1:8080/demo` on the same machine. This local flow requires Docker and is not a terminal-free hosted judge path.

Artifact references supplied for the accepted release:

- Candidate revision: `e228610a6d220f5532b0d8d3baac0a629db14208`
- Image digest: `sha256:1bb9df336d95a5549f7384e023c5954710c662f59d6fb9b9ac2d72ed3ee0c96c`
- Attestation identifier: `58474240` (historical result must retain its recorded conclusion)

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
- Without Foundry credentials, `foundry_mode` reports `disabled`; the deterministic demo remains available.
- A demo run has a unique match identifier, accepts at most 24 events, permits one concurrent run, and enforces a cooldown.

## Known MVP limits

- State is in process memory; restarting clears the demo match.
- Multi-replica WebSocket fan-out needs a managed backplane before production scale.
- Event Hubs is not deployed and has no active consumer, checkpoint store, or processed-message trace. The baseline uses `POST /v1/events`.
- A live Foundry call, managed identity, Azure deployment, and Application Insights evidence have not been verified.
- Languages beyond English, Spanish, and French need reviewed templates or a translation adapter.
