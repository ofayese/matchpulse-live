# Portal Submission Worksheet

This document contains the information that needs to be manually entered into the challenge submission portal.

**Project name:**
MatchPulse Live

**Primary category:**
Best Multi-Agent System

**Secondary category:**
Enterprise, only if permitted

**Elevator pitch:**
MatchPulse Live: Real-time, personalized football storytelling for every fan.

**Project description:**
Football viewers do not all want the same story. An analyst wants derivations and context, a broadcaster needs concise copy timed to live play, and a casual fan wants an immediate explanation in their language. Most systems either produce raw metrics with no audience or polished text with weak factual grounding.

MatchPulse Live is a new AI-assisted real-time storytelling module that turns synthetic football events into explainable match intelligence and personalized audience experiences. A strict event API accepts passes, shots, goals, tackles, pressure, possession, and match metadata. The interpretation agent maintains live team state and derives pass difficulty, shot-speed highlights, pressing surges, possession swings, and high regains. The explainability agent blocks any output that lacks source event IDs, calculation inputs, and a formula or threshold.

The personalization agent then ranks each grounded moment using persona, favorite club/player, metric interests, severity, and detail level. A curated multilingual renderer produces distinct analyst, fan, and broadcaster narratives in English, Spanish, and French. The same insight ID and evidence remain intact across variants, so judges can compare personalization without losing provenance. Outputs are available as timed WebSocket overlays, API responses, a responsive browser demo, and automated profile-specific recaps.

The optional Microsoft Foundry adapter serves as a constrained copy editor. It cannot create match facts: invalid JSON, timeout, or any new numeric claim causes a deterministic fallback. The Azure deployment path uses Container Apps for the service and Application Insights for operational telemetry. GitHub Actions runs linting, tests, preflight, coverage, a container build, and a blocking vulnerability gate.

MatchPulse Live uses only seeded synthetic data. The public demo contains no real match footage, private player information, club credentials, copyrighted music, or third-party branding. The module remains isolated from the parent platform's player-dispatch and approval capabilities.

**Public repository:**
https://github.com/ofayese/matchpulse-live

**Authoritative source:**
challenge-2026-submission

**Working project or test build:**
The project can be run locally using Docker. The instructions can be found in `submission/TESTING_INSTRUCTIONS.md`.

**Demo video:**
[Human-supplied and verified public URL]

**Technologies:**
Microsoft Foundry (integration-ready), Azure Container Apps (deployment-ready Bicep), Application Insights (integration-ready), Managed Identity (integration-ready), GitHub Actions, GitHub Container Registry, GitHub artifact attestations, Bicep, Docker, Synthetic-data pipeline, Multi-agent coordination.

**Eligibility representations:**
[Human-confirmed checklist]

**Team members:**
[Human-provided]

**Submission owner:**
[Human-provided]
