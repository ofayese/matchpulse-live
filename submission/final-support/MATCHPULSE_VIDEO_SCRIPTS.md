# MatchPulse Live — Demonstration Video Scripts

## Disclosure and Compliance Rules

- **Product Independence:** MatchPulse Live is presented solely as an independent real-time match storytelling application.
- **Synthetic Data Disclosure:** Every video visibly and audibly discloses `LOCAL DEMONSTRATION`, `SEEDED SYNTHETIC MATCH DATA`, and `NO LIVE EXTERNAL DATA SOURCE`.
- **Fictional Scenario:** Match ID `matchpulse-demo-001` (seed `20261024`) features fictional teams `Northbridge City` and `Harbor United` (`Northbridge City 2 - 1 Harbor United`).
- **Model Truthfulness:** `CHALLENGE_SYNTHETIC_ONLY=true` and Foundry runtime disabled (`foundry_mode="disabled"`, 0 model calls). The approved final candidate was recorded against the Azure Container Apps hosted deployment (public ingress now disabled); archived predeployment videos ran the container locally. No external model call is claimed.

## Hosted Submission Candidate — Approved Final Video

The approved authoritative video for submission is `submission/matchpulse-submission-hosted-elevenlabs-lily-v1-candidate.mp4` (SHA-256: `f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`, 115.0 seconds).

The video shows the Azure Container Apps hosted deployment, confirms HTTPS readiness, runs the fictional seeded 2–1 scenario, demonstrates duplicate/out-of-order handling, visits fan/analyst/Spanish broadcaster/French fan variants, shows the grounded recap and deterministic fallback, and closes with the repository context. Synthetic-only operation is explicitly disclosed and Foundry runtime is disabled (0 model calls). The approved candidate contains no browser/System.Speech narration; it uses ElevenLabs stock voice Lily (Kokoro `bf_emma` V2 is superseded). A legacy System.Speech helper remains in the shared recorder for historical workflows and is not invoked by the V2 render.

Authoritative support files reside in `submission/final-support/`:
- `submission/final-support/MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt`
- `submission/final-support/MATCHPULSE_NARRATION_CONVERSATIONAL_V2.json`
- `submission/final-support/matchpulse-hosted-narration-elevenlabs-lily-v1.wav`
- `submission/final-support/matchpulse-hosted-narration-elevenlabs-lily-v1.manifest.json`

All earlier predeployment demonstration recordings (`submission/matchpulse-submission-demo.mp4`, `submission/matchpulse-technical-demo.mp4`, etc.) and intermediate audio/manifests have been archived to `submission/archive/` (see `submission/archive/ARCHIVE_INDEX.md`) and are **NOT FOR SUBMISSION**. Ingress is currently disabled and upload/submission remain pending human authorization.

---

## Video 1: Archived Predeployment Submission Video (`submission/archive/videos/matchpulse-submission-demo.mp4`)

- **Total Duration:** `01:55.0` (`115.0` seconds, `3,450` frames at `30 fps`)
- **Caption File:** `submission/archive/scripts/MATCHPULSE_CAPTIONS_SUBMISSION.srt` (`13` cues)

### Cue-by-Cue Narration Script

| Cue | Time Window | Spoken Narration | Visual Focus |
| --- | --- | --- | --- |
| 1 | `00:00.0 – 00:08.0` | "MatchPulse Live turns seeded synthetic match events into evidence-aware stories." | Title card with `MATCHPULSE LIVE`, `SEEDED SYNTHETIC MATCH DATA`, `LOCAL DEMONSTRATION`, then transition to `/demo` landing view showing `SYNTHETIC DATA ONLY`. |
| 2 | `00:08.0 – 00:18.0` | "Every match fact comes from a deterministic synthetic event stream." | `/demo` connected to `matchpulse-demo-001` (`Northbridge City` vs `Harbor United`, `0-0`), showing `/health/ready` (`synthetic_only: true`, `foundry_mode: disabled`). |
| 3 | `00:18.0 – 00:28.0` | "Passes, pressure, shots, saves, and goals arrive through the event API." | Live ingestion of `evt-mp-002` (`possession_swing`), `evt-mp-003..005` (`Harbor United` `pressing_surge`), `evt-mp-006` (`Northbridge City` high regain), and `evt-mp-007` (`104.5 km/h` saved shot). |
| 4 | `00:28.0 – 00:38.0` | "Match state updates immediately as the synthetic scenario progresses." | Progressive counterattack pass (`evt-mp-008`) followed by `Northbridge City` opening goal (`evt-mp-009`, `NC-09` at `21:00`), updating score to `Northbridge City 1 - 0 Harbor United`. |
| 5 | `00:38.0 – 00:46.0` | "Duplicate events are acknowledged without duplicating match state." | Re-submission of `evt-mp-009` returns `HTTP 202` with `duplicate: true` and `duplicate_count: 1` while score remains `1 - 0`. |
| 6 | `00:46.0 – 00:54.0` | "Out-of-order events are rejected to preserve a consistent timeline." | Out-of-order event `evt-mp-010-ooo` (`sequence: 5 <= last_sequence: 8`) is rejected with `HTTP 409 Conflict`; timeline integrity preserved, followed by `Harbor United` equalizer (`evt-mp-012`, `1 - 1`). |
| 7 | `00:54.0 – 01:03.0` | "Fan mode makes the same evidence-backed moment immediate." | Audience profile `fan-en` view of the authoritative moment, highlighting `GOAL!` / energetic fan copy backed by `evt-mp-012`. |
| 8 | `01:03.0 – 01:12.0` | "Analyst mode exposes inputs, derivation, and confidence." | Switch to `analyst-en` on the same `insight_id`, exposing `Evidence: authoritative goal event + aggregate team goals`, `inputs`, and `confidence 1.0`. |
| 9 | `01:12.0 – 01:20.0` | "Broadcaster mode compresses the insight for live delivery." | Switch to `broadcaster-en`, showing compact on-air overlay copy (`GOAL - Harbor United`) with identical `insight_id` and `evidence_event_ids`. |
| 10 | `01:20.0 – 01:27.0` | "Language changes while the underlying facts and evidence remain stable." | Switch across `broadcaster-es` (`¡GOL!` / `Marca Harbor United`) and `fan-fr` (`BUT !` / `Harbor United change le match`) while `match_id`, score, and `evidence_event_ids` remain unchanged. |
| 11 | `01:27.0 – 01:39.0` | "At full time, the validated state produces a profile-specific recap." | `Northbridge City` scores the `88:00` winner (`evt-mp-015`, `2 - 1`), `evt-mp-016` finishes the match (`90:00`), and `/demo` renders the full-time recap with grounded `evidence_event_ids`. |
| 12 | `01:39.0 – 01:48.0` | "Invalid optional output falls back to safe, deterministic copy." | Resilience & fallback panel showing `foundry_mode: disabled` and `FoundryNarrativeClient` rejecting malformed or timed-out rewrites in favor of deterministic copy, plus `POST /v1/matches/matchpulse-demo-001/reset`. |
| 13 | `01:48.0 – 01:55.0` | "One match. Multiple audiences. Traceable stories." | Closing card: `MATCHPULSE LIVE — REAL-TIME EVENT ANALYSIS · AUDIENCE-SPECIFIC INSIGHTS · MULTILINGUAL STORYTELLING · TRACEABLE RECAPS — SYNTHETIC DEMONSTRATION`. |

---

## Video 2: Archived Technical Evidence Video (`submission/archive/videos/matchpulse-technical-demo.mp4`)

- **Total Duration:** `03:30.0` (`210.0` seconds, `6,300` frames at `30 fps`)
- **Caption File:** `submission/archive/scripts/MATCHPULSE_CAPTIONS_TECHNICAL.srt` (`26` cues)

### Cue-by-Cue Narration Script

| Cue | Time Window | Spoken Narration | Technical Checkpoint |
| --- | --- | --- | --- |
| 1 | `00:00.0 – 00:08.0` | "MatchPulse Live technical verification. This local demonstration uses seeded synthetic match data only." | Title & synthetic disclosure card (`LOCAL DEMONSTRATION · SEEDED SYNTHETIC MATCH DATA · NO LIVE EXTERNAL DATA SOURCE`). |
| 2 | `00:08.0 – 00:16.0` | "The container runs from audited source commit 335781f9 and published digest sha256 f413c32f." | Technical identity card showing commit `335781f928011f99a644083d80bfe4dfc480b1a6`, digest `sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226`, and attestation `59336499`. |
| 3 | `00:16.0 – 00:24.0` | "Standard OCI labels bind the image to the repository URL, exact commit SHA, and non-root user 10001." | OCI label inspection (`org.opencontainers.image.revision`, `org.opencontainers.image.source`, `User=10001:10001`, hardened Docker flags). |
| 4 | `00:24.0 – 00:32.0` | "Health live and health ready return HTTP 200 with synthetic-only mode enabled and Foundry disabled." | Live HTTP responses from `GET /health/live` and `GET /health/ready` (`synthetic_only: true`, `foundry_mode: "disabled"`). |
| 5 | `00:32.0 – 00:40.0` | "Before ingestion begins, the match reset endpoint clears state for scenario matchpulse-demo-001." | `POST /v1/matches/matchpulse-demo-001/reset` response and `/demo` initial state (`SYNTHETIC DATA ONLY` pill verified). |
| 6 | `00:40.0 – 00:48.0` | "Event one starts the match between fictional clubs Northbridge City and Harbor United at zero-zero." | `evt-mp-001` (`match_start`, `sequence: 0`, `clock_ms: 0`) and `evt-mp-002` (`possession_swing` for `Harbor United`, `50% -> 62%`). |
| 7 | `00:48.0 – 00:56.0` | "Three Harbor United pressure events within thirty seconds trigger a pressing surge insight." | `evt-mp-003`, `evt-mp-004`, `evt-mp-005` (`pressure >= 0.78`) generating `pressing_surge` with `confidence: 0.94`. |
| 8 | `00:56.0 – 01:04.0` | "Northbridge City wins a high tackle at field position seventy-four, followed by a saved Harbor shot." | `evt-mp-006` (`tackle` at `x=74.0`, `confidence: 0.97`) and `evt-mp-007` (`shot` on target at `104.5 km/h`, `confidence: 0.96`). |
| 9 | `01:04.0 – 01:12.0` | "A progressive counterattack pass sets up Northbridge City to score the opening goal in minute twenty-one." | `evt-mp-008` (`pass_quality` insight) and `evt-mp-009` (`goal` by `NC-09`, score `Northbridge City 1 - 0 Harbor United`). |
| 10 | `01:12.0 – 01:20.0` | "Re-sending event nine is acknowledged as a duplicate without changing the score or emitting insights." | Duplicate `evt-mp-009` test: `accepted: true, duplicate: true, duplicate_count: 1`, score remains `1 - 0`. |
| 11 | `01:20.0 – 01:28.0` | "Submitting sequence five after sequence eight is rejected with HTTP 409 as an out-of-order event." | Out-of-order `evt-mp-010-ooo` test: `HTTP 409 Conflict` (`out-of-order sequence 5; last accepted is 8`). |
| 12 | `01:28.0 – 01:36.0` | "Second-half momentum shifts to Harbor United, producing the equalizer for a one-all scoreline." | `evt-mp-011` (`possession_swing` at `48:00`) and `evt-mp-012` (`goal` by `HU-11` at `56:00`, score `1 - 1`). |
| 13 | `01:36.0 – 01:44.0` | "The match state endpoint confirms ten accepted sequences, one duplicate, and balanced team totals." | `GET /v1/matches/matchpulse-demo-001/state` JSON inspection at `56:00`. |
| 14 | `01:44.0 – 01:52.0` | "Every insight records its source event IDs, input parameters, derivation formula, and confidence." | Explainability agent trace on `#overlay` and `/v1/matches/matchpulse-demo-001/variants`. |
| 15 | `01:52.0 – 02:00.0` | "Fan mode in English presents immediate match excitement for the shared authoritative moment." | Profile `fan-en` inspection in `/demo` (`#overlay` and `#compare` row 1). |
| 16 | `02:00.0 – 02:08.0` | "Analyst mode in English appends the exact formula and input values while keeping the same insight ID." | Transition to `analyst-en`, verifying unchanged `match_id`, score, `insight_id`, `evidence_event_ids`, and `confidence`. |
| 17 | `02:08.0 – 02:16.0` | "Broadcaster mode in English condenses the narrative into a compact live-production overlay." | Transition to `broadcaster-en`, verifying compact body equals `overlay_text` with identical underlying evidence. |
| 18 | `02:16.0 – 02:24.0` | "Switching to Spanish broadcaster mode localizes the text while preserving every underlying statistic." | Transition to `broadcaster-es` (`locale="es"`), verifying Spanish copy (`Gol` / `GOL - Harbor United`) and unchanged evidence. |
| 19 | `02:24.0 – 02:32.0` | "Switching to French fan mode delivers native French copy from the same validated match state." | Transition to `fan-fr` (`locale="fr"`), verifying French copy (`BUT !`) and unchanged evidence. |
| 20 | `02:32.0 – 02:40.0` | "After a substitution and blocked shot, Northbridge City scores in minute eighty-eight to lead two-one." | `evt-mp-013` (`substitution` at `72:00`), `evt-mp-014` (`shot` blocked at `84:00`), and `evt-mp-015` (`goal` at `88:00`, `2 - 1`). |
| 21 | `02:40.0 – 02:48.0` | "Event sixteen ends the match at ninety minutes with status finished and fifteen accepted events." | `evt-mp-016` (`match_end` at `90:00`), `GET /v1/matches/matchpulse-demo-001/state` (`status: "finished"`, `Northbridge City 2 - 1 Harbor United`). |
| 22 | `02:48.0 – 02:56.0` | "The recap endpoint compiles top ranked moments and evidence event IDs in English, Spanish, and French." | `GET /v1/matches/matchpulse-demo-001/recap` rendered in `/demo` `#recap` across `en`, `es`, and `fr`. |
| 23 | `02:56.0 – 03:04.0` | "When optional model output is disabled, timed out, or malformed, the guard falls back to deterministic text." | Deterministic fallback inspection: `foundry_mode="disabled"` and `FoundryNarrativeClient` guard rails (`malformed-json`, `timeout`, `ungrounded-number` fallback). |
| 24 | `03:04.0 – 03:12.0` | "Runtime security and logging redaction ensure zero external network requests and zero exposed secrets." | Network guard & redaction summary (`external_requests_detected: 0`, `exposed_secrets_detected: 0`, loopback-only container). |
| 25 | `03:12.0 – 03:20.0` | "A final call to the reset endpoint removes the finished match state so every run starts clean." | `POST /v1/matches/matchpulse-demo-001/reset` (`{"reset": true, "existed": true}`) followed by `404` state confirmation. |
| 26 | `03:20.0 – 03:30.0` | "One event stream, multiple audiences and languages, with traceable stories and resilient fallback behavior." | Closing card with full synthetic and local predeployment demonstration disclosure. |
