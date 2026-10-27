# Challenge alignment trace

This trace maps the challenge brief to concrete evidence in this package. The
rendered live portal rules were not independently available during this
review. MatchPulse Live was deployed on Azure Container Apps; a fresh
read-only check on 2026-10-26 confirmed no ingress configuration and the
expected immutable image digest. No Foundry runtime setting or model
deployment was found; the observed run made zero model calls. The
resource-group inventory returned seven resources, including a Cognitive
Services account and project, rather than the earlier expected five.
The approved local video has not been uploaded, and the challenge has not been
submitted.

## Challenge requirements

| Requirement | Status | Evidence / action |
|---|---|---|
| New solution | Implemented | New MatchPulse challenge module, version 0.1.0; keep its commit history after the registration-period start |
| Synthetic football-realistic data | Implemented | `matchpulse.synthetic`; schema literal `source="synthetic"`; safety gate |
| Ingest as events happen | Implemented | Single/batch event APIs and live seeded producer |
| Meaningful statistics and patterns | Implemented | Pass difficulty, shot speed, pressing surge, possession swing, high regain |
| Explain why moments matter | Implemented | Evidence IDs, inputs, formula, confidence; a deterministic evidence-validation stage drops ungrounded insights |
| Render alongside live match | Implemented | Timed WebSocket JSON and `/demo` overlay UI |
| Personalize for different audiences | Implemented | Analyst/fan/broadcaster profiles, favorites, interests, detail levels |
| Real-time narratives and recap | Implemented | Live narrative outputs and profile-specific recap endpoint |
| Multi-language storytelling | Implemented | English, Spanish, French deterministic catalogs |
| Microsoft platform use | Deployed | Azure Container Apps deployment verified; fresh read-only state confirms no ingress configuration. No Foundry runtime setting or model deployment was found; do not claim an active Foundry model call. |
| Public source repository | Published; review pending | Repository URL is public; complete the current source/privacy/license review before publication changes. |
| Demo under two minutes | Local candidate approved | `submission/matchpulse-submission-hosted-elevenlabs-lily-v1-candidate.mp4` is the human-approved 115-second final video; not uploaded. |
| Public video URL | `REQUIREMENT_NOT_FOUND` in accessible official materials | The portal returned only an SPA/404 shell, so no hosting requirement was confirmed; this does not prove the live form has no video requirement. The video URL is still absent. |
| Testable project link/build | Image available; no public endpoint enabled | The immutable GHCR image can be run locally; fresh read-only state confirms no ingress configuration. |
| English submission materials | Implemented | All submission documents are in English |

## Judging criteria (equally weighted)

| Criterion | Evidence judges can see | Final proof to capture |
|---|---|---|
| Technological implementation | Strict models, deterministic state, guarded Foundry adapter, Docker, CI, tests, Bicep | Green CI; public commit; Azure resource screenshot; test output |
| Agentic design and innovation | Specialized deterministic processing pipeline with interpretation, evidence validation, personalization, and localization stages; it is not an autonomous or multi-agent system | Describe the implemented pipeline accurately; do not claim autonomous agents or deployed model use |
| Real-world impact and applicability | Broadcast overlay, analyst detail, fan mode, multilingual global reach; safe model fallback | Brief use-case slide and running public demo |
| User experience and presentation | Responsive demo UI, live overlay, profiles, machine-readable WebSocket | 120-second video with visible profile/language switch |
| Category adherence | Synthetic-only guard, five-stage pipeline, evidence-backed narrative, recap | Link this trace and show source event IDs in demo |

## Supported category language and limits

Use the judging-criterion names above as written, but describe only the
evidence in the adjacent column. The implementation is a deterministic
specialized processing pipeline, not an autonomous or multi-agent system.
Microsoft Foundry was off in the validated deployment and made zero model
calls; the optional adapter alone is not evidence of Foundry model usage. Do
not claim a multi-agent or Foundry-specific award/category based on the
current submission.

## Disqualifier prevention

- Do not publish secrets or private club/player information.
- Do not use real match footage or copyrighted music in the video.
- Do not use Premier League or club trademarks as if endorsed.
- Do not demonstrate the EA-backed path; use only the provided synthetic generator.
- Confirm the entrant/team is eligible and that every contributor is authorized.
- Keep the public repository accessible through the end of judging.
- Make the demo match the actual behavior and final commit.
