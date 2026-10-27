# Project description

## MatchPulse Live

**Core positioning:** MatchPulse Live transforms synthetic football events into explainable, audience-specific match intelligence for broadcast and streaming experiences.

MatchPulse Live is a synthetic-data prototype for evidence-linked football storytelling. Its local pipeline interprets event sequences, derives match moments, records source event IDs and calculation details, and renders the same grounded moment for fans, analysts, and broadcasters in English, Spanish, and French.

An optional guarded Microsoft Foundry adapter can rewrite narrative copy. The deterministic renderer remains available when the model is disabled or returns unusable output. The repository includes a Bicep path for Azure Container Apps and optional Application Insights configuration; the application was deployed and verified on Azure Container Apps. A fresh read-only check on 2026-10-26 confirmed no ingress configuration and the expected immutable image digest. No Foundry runtime setting or model deployment was found; The recorded run made zero model calls. The resource group contains a
Cognitive Services account and project, but no model deployment or app
Foundry runtime setting was found. Hosted-agent inventory could not be
verified because the optional Preview returned 403; no hosted agent is claimed.

The separately user-authorized Foundry account and project are development
resources, not part of the submitted MatchPulse runtime and not deployed by
MatchPulse Bicep. Foundry runtime is disabled in the submitted MatchPulse
deployment, and the demonstrated workflow makes zero model calls. The
approved video does not demonstrate Foundry usage.

The baseline uses HTTP event ingestion. It does not include an active Event Hubs consumer. State is held in process memory, and multi-replica WebSocket fan-out is not supported without a managed backplane.

**Public repository:** <https://github.com/ofayese/matchpulse-live>

**Current published image candidate:** `ghcr.io/ofayese/matchpulse-live@sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226` (source revision `335781f928011f99a644083d80bfe4dfc480b1a6`; attestation identifier `59336499`).

The image is tied to that source revision, not to later checkout changes.
Application and infrastructure changes in the current checkout have not been
built into or deployed as this image.

**Hosted demo:** Deployed and validated on Azure Container Apps. A fresh read-only check confirmed that no ingress configuration is present, so no public endpoint is enabled. Specific Azure resource identifiers are omitted from this public description.

**Demo video:** Approved active candidate: `submission/matchpulse-submission-hosted-elevenlabs-lily-v1-candidate.mp4` (SHA-256: `f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`, 115.0s, ElevenLabs stock voice Lily). Video upload is pending human authorization (`VIDEO_UPLOADED=NO`).

**Technologies present in the repository:** Python, FastAPI, Docker, Azure Container Apps, Bicep, GitHub Actions, GitHub Container Registry, GitHub artifact attestations, optional guarded Microsoft Foundry adapter, optional Application Insights configuration.
