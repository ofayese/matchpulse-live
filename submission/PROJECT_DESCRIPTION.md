# Project description

## MatchPulse Live

MatchPulse Live is a synthetic-data prototype for evidence-linked football storytelling. Its local pipeline interprets event sequences, derives match moments, records source event IDs and calculation details, and renders the same grounded moment for fans, analysts, and broadcasters in English, Spanish, and French.

An optional guarded Microsoft Foundry adapter can rewrite narrative copy. The deterministic renderer remains available when the model is disabled or returns unusable output. The repository includes a Bicep path for Azure Container Apps and optional Application Insights configuration; no live Azure deployment, managed identity, telemetry, or Foundry call is verified for this submission.

The baseline uses HTTP event ingestion. It does not include an active Event Hubs consumer. State is held in process memory, and multi-replica WebSocket fan-out is not supported without a managed backplane.

**Public repository:** <https://github.com/ofayese/matchpulse-live>

**Previously accepted immutable image:** `ghcr.io/ofayese/matchpulse-live@sha256:1bb9df336d95a5549f7384e023c5954710c662f59d6fb9b9ac2d72ed3ee0c96c` (candidate revision `e228610a6d220f5532b0d8d3baac0a629db14208`; attestation identifier `58474240`, as supplied for this task). This image is not represented as built from the current working branch.

**Hosted demo:** Not available. No Azure deployment was performed.

**Demo video:** Not available. No video was recorded or uploaded.

**Technologies present in the repository:** Python, FastAPI, Docker, Bicep, GitHub Actions, GitHub Container Registry, GitHub artifact attestations, optional guarded Microsoft Foundry adapter, optional Application Insights configuration.
