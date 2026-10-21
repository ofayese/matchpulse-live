# Testing instructions for judges

## Published release image

**NO-GO:** The immutable release image digest is pending successful protected
release publication. Do not use a previous image tag or digest as evidence for
the current source.

## Hosted demo

**NO-GO:** No authoritative Azure Container App URL is available yet. The demo
URL will be added only after Azure Phase 1 deployment succeeds. Use the local
synthetic-only validation below in the meantime.

## Local build

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
python -m matchpulse.synthetic --delay .15 --events 50
```

Open `http://127.0.0.1:8080/demo`.

## Expected behavior

- `/health/ready` returns `synthetic_only: true`.
- Valid ordered events return HTTP 202.
- Duplicate event IDs are acknowledged without duplicating state.
- Out-of-order events return HTTP 409.
- Any non-synthetic source value fails schema validation.
- Each insight includes source event IDs, calculation inputs, a formula, and confidence.
- English, Spanish, and French variants retain the same evidence.
- With no Foundry credentials, `foundry_mode` reports `disabled` and the full demo still works.
- A demo run returns a unique `demo-<id>` match, accepts at most 24 events, and
  refuses a second run with HTTP 409 while one is in flight or HTTP 429 during
  the cooldown window.

## Known MVP limits

- State is in process memory; restarting clears the demo match.
- Multi-replica WebSocket fan-out needs a managed backplane before production scale.
- Event Hubs is NOT part of the deployed baseline; no consumer, checkpoint store, or processed-message trace exists. The submitted HTTP MVP uses `POST /v1/events`.
- Languages beyond en/es/fr require reviewed templates or a translation adapter.
