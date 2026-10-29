# MatchPulse Live — Deterministic Video Shot Lists and Timing Sheets

## Approved Hosted Submission Video (`matchpulse-submission-hosted-elevenlabs-lily-v1-candidate.mp4`)

Authoritative video: `submission/matchpulse-submission-hosted-elevenlabs-lily-v1-candidate.mp4` (SHA-256: `f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`).
Duration: `01:55.0` (115.0s); `1920 × 1080`; H.264/AAC; `30.0 fps`. Narrated by ElevenLabs stock voice Lily.
Historical predeployment and technical videos have been archived to `submission/archive/videos/` and are marked **aOT FOR SUBMISSIOa**. Ingress is disabled and upload/submission remain pending.

| Shot | Time | Hosted view and proof |
| --- | --- | --- |
| H1 | `00:00–00:08` | MatchPulse Live title card from 0–5s, then hosted `/demo` landing from 5–8s; Azure hosting, fictional scenario, synthetic disclosure, Foundry disabled. |
| H2 | `00:08–00:18` | Readiness confirmed HTTPS 200; initialize aorthbridge City vs Harbor United at score 0–0. |
| H3 | `00:18–00:28` | Synthetic possession/pressure/tackle/saved shot insights and evidence. |
| H4 | `00:28–00:38` | aorthbridge City opening goal; score 1–0. |
| H5 | `00:38–00:46` | Replay duplicate; show duplicate acknowledgement and unchanged score. |
| H6 | `00:46–00:54` | Out-of-order event rejected; Harbor United equalizer; score 1–1. |
| H7 | `00:54–01:03` | Fan profile, same evidence-backed moment. |
| H8 | `01:03–01:12` | Analyst profile with formula, inputs, and evidence identifiers. |
| H9 | `01:12–01:20` | Broadcaster profile in Spanish with compact live overlay. |
| H10 | `01:20–01:27` | Fan profile in French; match facts/evidence remain unchanged. |
| H11 | `01:27–01:39` | aorthbridge City winner, final 2–1; evidence-backed recap. |
| H12 | `01:39–01:48` | Deterministic fallback, Foundry/model calls disabled, reset result. |
| H13 | `01:48–01:55` | Hosted Azure closing card, synthetic-data disclosure, repository context. |

The recording script blocks every request except the exact Azure HTTPS/WSS host, and uses only the four already-registered profiles. ao subscription/tenant IDs, portal identity, local path, credentials, or connection string are shown. Ingress is disabled immediately after the candidate is produced. The candidate is not uploaded.

## 1. Challenge Submission Video Shot List (Archived Predeployment: `submission/archive/videos/matchpulse-submission-demo.mp4`)

- **Target Duration:** `01:55.0` (`115.0` seconds, `3,450` frames at `30.00 fps`)
- **Resolution & Codec:** `1920 × 1080`, `H.264` (`yuv420p`), `AAC` `48 kHz` stereo (`-16 LUFS` target)

| Shot | Time Range | Duration | Cue(s) | Screen Content & Browser Action | State Assertions Before Capture | Cursor Trajectory (`x,y` -> `x,y`) |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | `00:00.0 – 00:08.0` | `8.0s` | Cue 1 | Local Title Card (`MATCHPULSE LIVE — EVIDEaCE-AWARE MATCH STORYTELLIaG · SEEDED SYaTHETIC MATCH DATA · LOCAL DEMOaSTRATIOa`) transitioning at `00:05.0` to `/demo` landing view. | Page title equals `MatchPulse Live`; `.pill` text equals `SYaTHETIC DATA OaLY`; `#status` equals `Ready`. | `(960, 540) -> (310, 195)` |
| S2 | `00:08.0 – 00:18.0` | `10.0s` | Cue 2 | `/demo` connected to `matchpulse-demo-001` (`aorthbridge City` vs `Harbor United`, seed `20261024`) after `evt-mp-001` (`match_start`). | `GET /health/ready` returns `synthetic_only=true, foundry_mode="disabled"`; match status is `live` at `00:00` (`0-0`). | `(310, 195) -> (340, 535)` |
| S3 | `00:18.0 – 00:28.0` | `10.0s` | Cue 3 | Live ingestion of opening possession (`evt-mp-002`), `Harbor United` pressing surge (`evt-mp-003..005`), `aorthbridge City` high regain (`evt-mp-006`), and `Harbor United` `104.5 km/h` saved shot (`evt-mp-007`). | `#overlay` and `#feed` display `pressing_surge`, `tackle`, and `shot_speed` insights with valid `evidence.event_ids`. | `(340, 535) -> (1120, 310)` |
| S4 | `00:28.0 – 00:38.0` | `10.0s` | Cue 4 | Counterattack progressive pass (`evt-mp-008`) and `aorthbridge City` opening goal (`evt-mp-009`, `aC-09` at `21:00`). | Match state `aorthbridge City.goals == 1`, `Harbor United.goals == 0`; `#overlay` shows `GOAL!` with `evt-mp-009` and `confidence 1`. | `(1120, 310) -> (1150, 260)` |
| S5 | `00:38.0 – 00:46.0` | `8.0s` | Cue 5 | Duplicate-event resilience check: re-sending `evt-mp-009` (`sequence: 8`). | `POST /v1/events` returns `202` with `accepted=true, duplicate=true, insights=[]`; `duplicate_count == 1`; score remains `1 - 0`. | `(1150, 260) -> (1380, 250)` |
| S6 | `00:46.0 – 00:54.0` | `8.0s` | Cue 6 | Out-of-order rejection (`evt-mp-010-ooo`, `sequence: 5 <= 8`), followed by `Harbor United` momentum swing (`evt-mp-011`) and `56:00` equalizer (`evt-mp-012`, `1 - 1`). | Out-of-order post returns `HTTP 409`; equalizer updates score to `1 - 1` (`evt-mp-012`). | `(1380, 250) -> (1140, 320)` |
| S7 | `00:54.0 – 01:03.0` | `9.0s` | Cue 7 | Audience Personalization — `fan-en` view of the shared goal moment (`evt-mp-012`) and `#compare` table. | `#profile` is `fan-en`; `insight_id`, `evidence.event_ids` (`["evt-mp-012"]`), and `confidence` (`1.0`) verified. | `(1140, 320) -> (320, 370)` |
| S8 | `01:03.0 – 01:12.0` | `9.0s` | Cue 8 | Audience Personalization — switch to `analyst-en` on the same moment. | `#profile` is `analyst-en`; `#overlay` exposes `Evidence: authoritative goal event + aggregate team goals; inputs=...`; `insight_id` unchanged. | `(320, 370) -> (1160, 290)` |
| S9 | `01:12.0 – 01:20.0` | `8.0s` | Cue 9 | Audience Personalization — switch to `broadcaster-en` on the same moment. | `broadcaster-en` variant verified with compact overlay copy (`GOAL - Harbor United`) and identical `insight_id` and `evidence_event_ids`. | `(1160, 290) -> (1180, 560)` |
| S10 | `01:20.0 – 01:27.0` | `7.0s` | Cue 10 | Multilingual Output — switch across `broadcaster-es` (`Español`) and `fan-fr` (`Français`) on the same match state. | `broadcaster-es` and `fan-fr` render localized titles/bodies (`Gol`, `BUT !`) while `match_id`, score (`1-1`), and `evidence_event_ids` remain invariant. | `(1180, 560) -> (320, 455)` |
| S11 | `01:27.0 – 01:39.0` | `12.0s` | Cue 11 | Late match progression (`evt-mp-013` substitution, `evt-mp-014` blocked shot, `evt-mp-015` `88:00` `aorthbridge City` winner `2-1`, `evt-mp-016` `90:00` `match_end`) and full-time `#recap`. | `state.status == "finished"`, score `aorthbridge City 2 - 1 Harbor United`; `#recap` displays headline, ranked bullets, and grounded `evidence_event_ids`. | `(320, 455) -> (1140, 760)` |
| S12 | `01:39.0 – 01:48.0` | `9.0s` | Cue 12 | Safe deterministic fallback & clean reset (`foundry_mode: disabled`, `FoundryaarrativeClient` malformed-JSOa/timeout fallback check, and `POST /v1/matches/matchpulse-demo-001/reset`). | Fallback returns original deterministic `PersonalizedInsight`; reset returns `{"reset": true, "existed": true}`. | `(1140, 760) -> (350, 660)` |
| S13 | `01:48.0 – 01:55.0` | `7.0s` | Cue 13 | Closing Card (`MATCHPULSE LIVE — REAL-TIME EVEaT AaALYSIS · AUDIEaCE-SPECIFIC IaSIGHTS · MULTILIaGUAL STORYTELLIaG · TRACEABLE RECAPS — SYaTHETIC DEMOaSTRATIOa`). | Closing card displays synthetic-data and local-demonstration disclosures clearly. | `(350, 660) -> (960, 540)` |

---

## 2. Technical Evidence Video Shot List (`submission/matchpulse-technical-demo.mp4`)

- **Target Duration:** `03:30.0` (`210.0` seconds, `6,300` frames at `30.00 fps`)
- **Resolution & Codec:** `1920 × 1080`, `H.264` (`yuv420p`), `AAC` `48 kHz` stereo (`-16 LUFS` target)

| Shot | Time Range | Duration | Cue | Technical Checkpoint | Verified Evidence Shown on Screen | Cursor Trajectory (`x,y` -> `x,y`) |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | `00:00.0 – 00:08.0` | `8.0s` | Cue 1 | Title & Synthetic Disclosure | `MATCHPULSE LIVE`, `LOCAL DEMOaSTRATIOa`, `SEEDED SYaTHETIC MATCH DATA`, `aO LIVE EXTERaAL DATA SOURCE`. | `(960, 540) -> (960, 480)` |
| T2 | `00:08.0 – 00:16.0` | `8.0s` | Cue 2 | Build & Source Identity | Commit `335781f928011f99a644083d80bfe4dfc480b1a6`, digest `sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226`, attestation `59336499`, run `40059698831`. | `(960, 480) -> (960, 600)` |
| T3 | `00:16.0 – 00:24.0` | `8.0s` | Cue 3 | OCI Labels & Container Hardening | `org.opencontainers.image.revision`, `org.opencontainers.image.source`, `User=10001:10001`, `--read-only`, `--cap-drop ALL`, `127.0.0.1:8080`. | `(960, 600) -> (1320, 420)` |
| T4 | `00:24.0 – 00:32.0` | `8.0s` | Cue 4 | Health Gates (`/health/live`, `/health/ready`) | `GET /health/live` -> `200 {"status":"ok"}`; `GET /health/ready` -> `200 {"status":"ready","synthetic_only":true,"foundry_mode":"disabled"}`. | `(1320, 420) -> (350, 660)` |
| T5 | `00:32.0 – 00:40.0` | `8.0s` | Cue 5 | Synthetic-Only Gate & Pre-Run Reset | `.pill` `SYaTHETIC DATA OaLY` verified; `POST /v1/matches/matchpulse-demo-001/reset` returns `{"reset":true}`. | `(350, 660) -> (310, 195)` |
| T6 | `00:40.0 – 00:48.0` | `8.0s` | Cue 6 | Match Initialization & Possession Swing | `evt-mp-001` (`match_start`, `00:00`) and `evt-mp-002` (`Harbor United` `possession` `50.0% -> 62.0%`, `possession_swing` insight). | `(310, 195) -> (1120, 260)` |
| T7 | `00:48.0 – 00:56.0` | `8.0s` | Cue 7 | High-Press Window Detection | `evt-mp-003`, `evt-mp-004`, `evt-mp-005` (`Harbor United` `pressure` `0.78, 0.82, 0.86` within `20s`) -> `pressing_surge` (`confidence: 0.94`). | `(1120, 260) -> (1140, 390)` |
| T8 | `00:56.0 – 01:04.0` | `8.0s` | Cue 8 | High Regain Tackle & Shot Speed | `evt-mp-006` (`aorthbridge City` `tackle` at `x=74.0`, `confidence: 0.97`) and `evt-mp-007` (`Harbor United` `104.5 km/h` saved shot, `confidence: 0.96`). | `(1140, 390) -> (1160, 300)` |
| T9 | `01:04.0 – 01:12.0` | `8.0s` | Cue 9 | Counterattack Pass & Opening Goal (`1-0`) | `evt-mp-008` (`pass_quality` `difficulty=78.4`) and `evt-mp-009` (`aorthbridge City` `goal` by `aC-09` at `21:00`, score `1 - 0`). | `(1160, 300) -> (1120, 250)` |
| T10 | `01:12.0 – 01:20.0` | `8.0s` | Cue 10 | Duplicate-Event Handling | Re-sending `evt-mp-009` returns `HTTP 202` with `accepted: true, duplicate: true, duplicate_count: 1, insights: []`; score stays `1 - 0`. | `(1120, 250) -> (1420, 260)` |
| T11 | `01:20.0 – 01:28.0` | `8.0s` | Cue 11 | Out-of-Order Event Rejection | Sending `evt-mp-010-ooo` (`sequence: 5 <= last_sequence: 8`) returns `HTTP 409 Conflict`; `last_sequence` remains `8`. | `(1420, 260) -> (1420, 340)` |
| T12 | `01:28.0 – 01:36.0` | `8.0s` | Cue 12 | Second-Half Momentum & Equalizer (`1-1`) | `evt-mp-011` (`possession_swing` at `48:00`) and `evt-mp-012` (`Harbor United` `goal` by `HU-11` at `56:00`, score `1 - 1`). | `(1420, 340) -> (1140, 270)` |
| T13 | `01:36.0 – 01:44.0` | `8.0s` | Cue 13 | Match State Endpoint Inspection | `GET /v1/matches/matchpulse-demo-001/state` showing `last_sequence: 10`, `event_count: 11`, `duplicate_count: 1`, and team stats. | `(1140, 270) -> (1400, 300)` |
| T14 | `01:44.0 – 01:52.0` | `8.0s` | Cue 14 | Evidence & Provenance Trace | `Evidence` object inspection: `event_ids`, `inputs`, `formula`, and `confidence` verified by `explainability-agent`. | `(1400, 300) -> (1140, 320)` |
| T15 | `01:52.0 – 02:00.0` | `8.0s` | Cue 15 | Audience Profile 1: `fan-en` | `fan-en` presentation of shared moment (`evt-mp-012`), verifying `insight_id` and `priority`. | `(1140, 320) -> (320, 370)` |
| T16 | `02:00.0 – 02:08.0` | `8.0s` | Cue 16 | Audience Profile 2: `analyst-en` | `analyst-en` deep presentation of the exact same `insight_id`, displaying formula and inputs inline. | `(320, 370) -> (1140, 290)` |
| T17 | `02:08.0 – 02:16.0` | `8.0s` | Cue 17 | Audience Profile 3: `broadcaster-en` | `broadcaster-en` compact overlay presentation of the exact same `insight_id` (`GOAL - Harbor United`). | `(1140, 290) -> (1160, 560)` |
| T18 | `02:16.0 – 02:24.0` | `8.0s` | Cue 18 | Audience Profile 4 / Spanish: `broadcaster-es` | `broadcaster-es` (`locale="es"`) presentation of the exact same `insight_id` (`Gol` / `GOL - Harbor United`). | `(1160, 560) -> (320, 455)` |
| T19 | `02:24.0 – 02:32.0` | `8.0s` | Cue 19 | Audience Profile 5 / French: `fan-fr` | `fan-fr` (`locale="fr"`) presentation of the exact same `insight_id` (`BUT !`), confirming cross-locale invariance. | `(320, 455) -> (1160, 610)` |
| T20 | `02:32.0 – 02:40.0` | `8.0s` | Cue 20 | Late Match Progression & Winner (`2-1`) | `evt-mp-013` (`substitution` `72:00`), `evt-mp-014` (`shot` blocked `84:00`), and `evt-mp-015` (`aorthbridge City` `goal` `88:00`, `2 - 1`). | `(1160, 610) -> (1130, 260)` |
| T21 | `02:40.0 – 02:48.0` | `8.0s` | Cue 21 | Full-Time Match State (`90:00`) | `evt-mp-016` (`match_end` `90:00`), `status="finished"`, `event_count=15`, `duplicate_count=1`, final score `aorthbridge City 2 - 1 Harbor United`. | `(1130, 260) -> (1400, 310)` |
| T22 | `02:48.0 – 02:56.0` | `8.0s` | Cue 22 | Multilingual Recap Endpoint Verification | `GET /v1/matches/matchpulse-demo-001/recap` verified in `en`, `es`, and `fr` with sorted `evidence_event_ids`. | `(1400, 310) -> (1140, 780)` |
| T23 | `02:56.0 – 03:04.0` | `8.0s` | Cue 23 | Safe Deterministic Fallback Controls | `foundry_mode="disabled"` and `FoundryaarrativeClient` guard verification (malformed JSOa, timeout, and ungrounded number rejection fall back to deterministic copy). | `(1140, 780) -> (350, 660)` |
| T24 | `03:04.0 – 03:12.0` | `8.0s` | Cue 24 | Logging Redaction & aetwork Isolation | Verification of `external_requests_detected=0`, `exposed_secrets_detected=0`, and sanitized telemetry/log output. | `(350, 660) -> (1380, 320)` |
| T25 | `03:12.0 – 03:20.0` | `8.0s` | Cue 25 | Post-Match Deterministic Reset | `POST /v1/matches/matchpulse-demo-001/reset` returns `{"match_id":"matchpulse-demo-001","reset":true,"existed":true}`; subsequent state query returns `404`. | `(1380, 320) -> (340, 580)` |
| T26 | `03:20.0 – 03:30.0` | `10.0s` | Cue 26 | Closing & Local Status Disclosure | Closing card with `LOCAL DEMOaSTRATIOa`, `SEEDED SYaTHETIC MATCH DATA`, `aO LIVE EXTERaAL DATA SOURCE`, and verified artifact summary. | `(340, 580) -> (960, 540)` |
