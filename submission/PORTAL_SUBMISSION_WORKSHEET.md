# Portal submission worksheet — blocked pending organizer exception

This worksheet is preparation only. The challenge portal has not been submitted.

## Project fields

- **Project name:** MatchPulse Live
- **Primary category:** Best Multi-Agent System
- **Secondary category:** Leave blank unless the portal allows multiple categories and the organizer confirms eligibility.
- **Repository:** https://github.com/ofayese/matchpulse-live
- **Working branch:** `chore/final-challenge-submission`
- **Authoritative release tag:** `challenge-2026-submission` already exists at a prior commit. Do not move or represent it as this working branch.
- **Accepted published image:** `ghcr.io/ofayese/matchpulse-live@sha256:1bb9df336d95a5549f7384e023c5954710c662f59d6fb9b9ac2d72ed3ee0c96c`
- **Accepted artifact candidate:** `e228610a6d220f5532b0d8d3baac0a629db14208`
- **Hosted demo:** Not available. No Azure deployment was created because registration confirmation arrived after the stated registration deadline; an organizer exception is required before any billable work.
- **Demo video:** Not available. No recording or upload has been represented as complete.

## Pitch

MatchPulse Live turns synthetic football events into evidence-linked match insights, then adapts the same verified moment for fans, analysts, and broadcasters in multiple languages.

## Verified description

MatchPulse Live is a synthetic-data prototype for real-time football storytelling. Its local pipeline interprets event sequences, attaches source event IDs and calculation details, and renders audience-specific narratives in English, Spanish, and French. A guarded optional Microsoft Foundry adapter can rewrite copy while deterministic rendering remains available as fallback. The repository includes an Azure Container Apps Bicep deployment path and optional Application Insights telemetry configuration; neither a live Azure deployment nor a live Foundry call is verified for this submission. State is in process memory, and Event Hubs has no active consumer in the submitted baseline.

## Technologies supported by repository evidence

Python, FastAPI, Docker, Bicep deployment templates, GitHub Actions, GitHub Container Registry, GitHub artifact attestations, deterministic synthetic event generation, optional guarded Microsoft Foundry adapter, optional Application Insights telemetry configuration.

## Judge testing

No-login hosted judge testing is unavailable. The existing instructions describe local execution and do not provide a verified public demo URL. Do not enter a guessed URL. The portal submission remains blocked until an organizer exception is granted, a hosted demo and video are produced, and their public links are tested signed out.

## Known limitations

- Match state is in process memory and resets when the process restarts.
- WebSocket fan-out is limited to one replica without a managed backplane.
- Event Hubs is not deployed; the baseline ingests events over HTTP.
- Azure deployment, managed identity, live Foundry inference, and Application Insights evidence are not verified.
- No public hosted demo or video URL is verified.

## Human-provided fields

Team members, authorized representative, and every eligibility attestation must be supplied and confirmed by the entrant. The registration email provided for this review is timestamped after the stated deadline; organizer confirmation of an exception is required before asserting eligibility.
