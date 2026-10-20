# Project description

## MatchPulse Live

Football viewers do not all want the same story. An analyst wants derivations and context, a broadcaster needs concise copy timed to live play, and a casual fan wants an immediate explanation in their language. Most systems either produce raw metrics with no audience or polished text with weak factual grounding.

MatchPulse Live is a new AI-assisted real-time storytelling module that turns synthetic football events into explainable match intelligence and personalized audience experiences. A strict event API accepts passes, shots, goals, tackles, pressure, possession, and match metadata. The interpretation agent maintains live team state and derives pass difficulty, shot-speed highlights, pressing surges, possession swings, and high regains. The explainability agent blocks any output that lacks source event IDs, calculation inputs, and a formula or threshold.

The personalization agent then ranks each grounded moment using persona, favorite club/player, metric interests, severity, and detail level. A curated multilingual renderer produces distinct analyst, fan, and broadcaster narratives in English, Spanish, and French. The same insight ID and evidence remain intact across variants, so judges can compare personalization without losing provenance. Outputs are available as timed WebSocket overlays, API responses, a responsive browser demo, and automated profile-specific recaps.

The optional Microsoft Foundry adapter serves as a constrained copy editor. It cannot create match facts: invalid JSON, timeout, or any new numeric claim causes a deterministic fallback. The Azure deployment path uses Container Apps for the service and Application Insights for operational telemetry. GitHub Actions runs linting, tests, preflight, coverage, a container build, and a blocking vulnerability gate.

MatchPulse Live uses only seeded synthetic data. The public demo contains no real match footage, private player information, club credentials, copyrighted music, or third-party branding. The module remains isolated from the parent platform's player-dispatch and approval capabilities.

**Public repository:** <https://github.com/ofayese/matchpulse-live>

**Published container image:** `ghcr.io/ofayese/matchpulse-live@sha256:67546291cf1fc9aa236327a1d53230e8caa589ce0f72c758b28c6a6effee4d90` (source commit `e8289265dc1920a2f313a9ec45ebf748591a3071`, `linux/amd64`, non-root user `10001:10001`). The image is anonymously pullable, was scanned with 0 HIGH and 0 CRITICAL findings, and passed the smoke test with 0 failed checks.

**Microsoft/Azure technologies:** Microsoft Foundry/Azure OpenAI-compatible model endpoint (optional guarded rewrite), Azure Container Apps, Application Insights/Log Analytics, Bicep, GitHub Actions, and GitHub Container Registry.
