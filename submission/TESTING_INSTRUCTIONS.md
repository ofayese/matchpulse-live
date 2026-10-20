# Testing instructions for judges

## Run the published image (no setup required)

The audited image is published to the GitHub Container Registry and is
readable without any credential:

```bash
docker run --rm -p 8080:8080 \
  ghcr.io/ofayese/matchpulse-live@sha256:67546291cf1fc9aa236327a1d53230e8caa589ce0f72c758b28c6a6effee4d90
```

Then open <http://127.0.0.1:8080/demo>.

| Property | Value |
| -------- | ----- |
| Tag | `ghcr.io/ofayese/matchpulse-live:sha-e8289265dc1920a2f313a9ec45ebf748591a3071` |
| Digest | `sha256:67546291cf1fc9aa236327a1d53230e8caa589ce0f72c758b28c6a6effee4d90` |
| Source commit | `e8289265dc1920a2f313a9ec45ebf748591a3071` |
| Runtime user | `10001:10001` |
| Platform | `linux/amd64` |

## Hosted demo

**URL:** `<ADD_AZURE_CONTAINER_APP_URL>/demo`

No login should be required. Keep the deployment available through the end of judging.

1. Open `/demo`.
2. Select `fan-en`, `analyst-en`, `broadcaster-es`, or `fan-fr`.
3. Click **Start synthetic demo**. The server seeds a unique synthetic match,
   waits for the browser to connect, and streams the moments to the overlay.
4. Compare the same insight ID and evidence IDs across profiles.
5. Use the **Comparison language** selector to force `en`, `es`, or `fr` for
   every audience at once.
6. Open `/v1/matches/<demo match id>/recap?profile_id=broadcaster-es` after
   the run finishes. The demo match id is shown in the left panel.

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
matchpulse-synthetic --delay .15 --events 50
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
