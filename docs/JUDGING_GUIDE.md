# MatchPulse Live judging guide

## Quick links

- [Repository](https://github.com/ofayese/matchpulse-live)
- [115-second YouTube demo](https://www.youtube.com/watch?v=O5gHkl_UFHc)
- [Innovation Studio project 127196](https://innovationstudio.microsoft.com/hackathons/insidethegamedeveloperhackathon/project/127196)
- [Architecture](ARCHITECTURE.md)
- [Testing instructions](../submission/TESTING_INSTRUCTIONS.md)
- [Azure deployment record](AZURE_DEPLOYMENT.md)
- [Third-party notices](../THIRD_PARTY_NOTICES.md)

## 115-second demo map

Times are the approved Lily narration manifest's speech windows; the video
may include brief visual-only transitions between units.

| Time | Demo moment |
|---|---|
| 00:00.220–00:17.336 | Product overview, Azure Container Apps context, synthetic-data boundary, fictional matchup, and evidence-linked insights |
| 00:18.220–00:27.610 | Accepted-event lineage and how evidence supports each match insight |
| 00:28.220–00:37.684 | Synthetic goal and attached evidence |
| 00:38.220–00:52.742 | Duplicate replay remains idempotent; out-of-order event is rejected without corrupting state |
| 00:54.220–01:02.313 | Fan view |
| 01:03.220–01:19.785 | Analyst calculation and evidence identifiers; broadcaster overlay |
| 01:20.220–01:26.289 | English, Spanish, and French presentations retain the same match evidence |
| 01:27.220–01:37.933 | Synthetic 2–1 recap grounded in accepted events |
| 01:39.220–01:47.558 | Deterministic fallback; Foundry disabled and zero model calls in the demonstrated flow |
| 01:48.220–01:53.898 | Azure and synthetic-feed disclosure; fictional-match closing |
| 01:53.898–01:55.000 | Closing visual; narration has ended |

## Judging evidence map

| Area | What judges should verify | Repository evidence | Demo timestamp |
|---|---|---|---|
| Problem and product value | One accepted-event lineage can serve fans, analysts, and broadcasters | [README](../README.md), [project description](../submission/PROJECT_DESCRIPTION.md) | 00:00.220–00:17.336 |
| Determinism | Rule-based fallback remains usable without a model | [state](../src/matchpulse/state.py), [demo](../src/matchpulse/demo.py), `test_duplicate_is_idempotent_and_out_of_order_is_rejected` | 01:39.220–01:47.558 |
| Duplicate handling | Replaying an event ID does not apply the event twice | [pipeline test](../tests/test_pipeline.py), `MatchAccumulator.apply` in [state](../src/matchpulse/state.py) | 00:38.220–00:46.261 |
| Out-of-order rejection | Older sequence values are rejected and state stays intact | [API test](../tests/test_api.py), [pipeline test](../tests/test_pipeline.py) | 00:46.481–00:52.742 |
| Evidence lineage | Insights retain accepted source-event IDs and calculation evidence | [agents](../src/matchpulse/agents.py), [state](../src/matchpulse/state.py), [personalization tests](../tests/test_personalization.py) | 00:18.220–00:27.610; 01:27.220–01:37.933 |
| Audience profiles | Fan, analyst, and broadcaster outputs vary in presentation | [localization](../src/matchpulse/localization.py), [personalization tests](../tests/test_personalization.py) | 00:54.220–01:19.785 |
| Multilingual behavior | English, Spanish, and French change wording, not evidence | [localization test](../tests/test_localization.py), [variant tests](../tests/test_variants.py) | 01:20.220–01:26.289 |
| REST API | Synthetic events and match outputs use validated HTTP routes | [service](../src/matchpulse/service.py), [API tests](../tests/test_api.py) | Repository/test evidence |
| WebSocket delivery | Profile-specific overlays are delivered to connected clients | [service](../src/matchpulse/service.py), `test_websocket_receives_personalized_overlay` in [API tests](../tests/test_api.py) | Repository/test evidence |
| Azure Container Apps | Deployment uses an immutable image; ingress is currently disabled | [deployment record](AZURE_DEPLOYMENT.md), [deployment guide](../submission/TESTING_INSTRUCTIONS.md) | 00:00.220–00:17.336; 01:48.220–01:53.898 |
| Observability | Telemetry is optional and its disabled state is tested | [telemetry](../src/matchpulse/telemetry.py), [telemetry tests](../tests/test_telemetry.py) | Repository/test evidence |
| Infrastructure as code | Container Apps resources and probes are described in Bicep | [Bicep template](../infra/main.bicep), [deployment record](AZURE_DEPLOYMENT.md) | Repository evidence |
| Testing | Behavior is covered by the Python test suite | [tests](../tests), [testing instructions](../submission/TESTING_INSTRUCTIONS.md) | Repository evidence |
| Security/publication controls | Synthetic-only input, guarded optional model use, and publication boundaries | [security policy](../SECURITY.md), [Foundry guard tests](../tests/test_foundry_guard.py), [readiness](../submission/SUBMISSION_READINESS.md) | 00:00.220–00:17.336; 01:39.220–01:47.558 |
| Narration rights | Final narration uses paid-plan stock Lily; no cloning | [third-party notices](../THIRD_PARTY_NOTICES.md), [narration record](ELEVENLABS_NARRATION.md) | Throughout narration; rights evidence is in the repository |
| Synthetic-data disclosure | Match, teams, and events are fictional; no live feed is used | [README](../README.md), [synthetic generator](../src/matchpulse/synthetic.py) | 00:00.220–00:17.336; 01:48.220–01:53.898 |
| Foundry-off / zero-model-call disclosure | Demonstration uses deterministic fallback; no model calls | [project description](../submission/PROJECT_DESCRIPTION.md), [deployment record](AZURE_DEPLOYMENT.md) | 01:39.220–01:47.558 |

## Current submission boundaries

- Synthetic match events and fictional teams only; no live external feed.
- The demonstrated analysis uses deterministic fallback. Foundry runtime is
  off and the demonstrated/reviewed flow made zero model calls.
- The existing Azure Container Apps ingress is disabled; this guide does not
  claim a publicly reachable application endpoint.
- ElevenLabs stock voice Lily is used only for the final narration. No voice
  cloning was used; see [third-party notices](../THIRD_PARTY_NOTICES.md).
- The Innovation Studio project is saved and listed. Organizer confirmation
  of submission state remains pending; do not describe the challenge as
  confirmed submitted.
- Portal video processing remains under review. The verified playable demo
  is the YouTube URL above.

## Roadmap — not submitted capabilities

The following are not current demonstrated capabilities: Event Hubs ingestion,
durable replay, a multi-replica WebSocket backplane, authenticated preferences,
additional languages, Foundry-enabled analysis, play-style classification,
counterattack detection, player-performance patterns, and evidence-handoff
visualization.
