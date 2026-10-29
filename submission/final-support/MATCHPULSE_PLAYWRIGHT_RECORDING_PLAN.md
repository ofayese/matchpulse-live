# MatchPulse Live — Deterministic Playwright Recording Plan

> **Historical capture procedure, not current authorization.** The approved
> candidate has already been recorded locally. Azure public ingress is
> currently disabled, and this review does not authorize re-enabling it,
> uploading the video, or submitting the challenge. Do not execute the
> historical ingress-restoration steps below without separate explicit
> authorization.

## 1. Purpose and Scope

This document defines the deterministic browser recording, synthetic scenario execution, network isolation, audio normalization, and media verification plan for MatchPulse Live demonstration videos.

The authoritative approved submission video is:
- **Final Approved Submission Video:** `submission/matchpulse-submission-hosted-elevenlabs-lily-v1-candidate.mp4`
- **SHA-256:** `f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`
- **Duration:** `115.0` seconds (`01:55.0`, target window `01:45` to `01:55`, hard limit `< 02:00`)
- **Status:** `APPROVED LOCALLY — NOT YET UPLOADED`

All historical predeployment recordings (`matchpulse-submission-demo.mp4`, `matchpulse-submission-demo-captioned.mp4`, `matchpulse-technical-demo.mp4`, `matchpulse-technical-demo-captioned.mp4`) and intermediate candidates have been archived to `submission/archive/` (see `submission/archive/ARCHIVE_INDEX.md`) and are strictly **NOT FOR SUBMISSION**.

All recordings demonstrate MatchPulse Live as an independent product operating on deterministic, seeded synthetic match-event data (`LOCAL DEMONSTRATION · SEEDED SYNTHETIC MATCH DATA · NO LIVE EXTERNAL DATA SOURCE`). No third-party video game, publisher, community API, club, league, player likeness, or copyrighted broadcast asset is referenced or displayed.

## Final Approved Hosted Candidate Addendum — 2026-10-25 / 2026-10-26

This addendum defines the final approved candidate and its support artifacts:

| Setting | Final Approved Submission Candidate |
| --- | --- |
| Output Video | `submission/matchpulse-submission-hosted-elevenlabs-lily-v1-candidate.mp4` |
| Video SHA-256 | `f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786` |
| Narration Audio | `submission/final-support/matchpulse-hosted-narration-elevenlabs-lily-v1.wav` |
| Narration Manifest | `submission/final-support/matchpulse-hosted-narration-elevenlabs-lily-v1.manifest.json` |
| Thought-Unit Script | `submission/final-support/MATCHPULSE_NARRATION_CONVERSATIONAL_V2.json` |
| Captions / Narration Cues | `submission/final-support/MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt` |
| Voice Engine | ElevenLabs Starter, stock voice Lily (`pFZP5JQG7iQjIQuC4Bku`), `eleven_multilingual_v2` (Kokoro V2 superseded) |
| Duration / FPS | 115.0 seconds, 30.0 fps constant |
| Viewport | 1920 × 1080, device scale factor 1, Chromium dark site scheme |
| Encoding | H.264/yuv420p video, AAC 48 kHz stereo audio; -16.01 LUFS / -2.0 dBTP |
| Browser TTS | Absent from the approved candidate; the final candidate uses ElevenLabs Lily. A legacy System.Speech helper remains in the shared recorder and is not invoked by this render. |
| Video Stream MD5 | `c85bef1de55944edebd4f4d003c70b59` (identical to visual candidate) |
| Human Approval | `APPROVE_CONVERSATIONAL_V2` |
| Azure Ingress | DISABLED |
| Upload / Portal | `VIDEO_UPLOADED=NO`, `CHALLENGE_SUBMITTED=NO` |

### Preparation and opening gate

Complete `python scripts/record_matchpulse_hosted_submission.py --preflight` while ingress is disabled. This verifies the candidate path is unused, the hosted caption cues are valid, audio synthesis works, and Playwright/Chromium/FFmpeg/FFprobe are ready. Review the Azure baseline and prepare both ingress commands before enabling. An opt-in local narration path is available through `--narration-preflight --tts-provider local-docker --tts-url http://127.0.0.1:PORT`; it checks only a loopback TTS service and does not contact Azure or write narration. `--render-local-narration` writes a separate narration WAV and remuxed candidate without altering the existing videos. The default recording preflight continues to use its existing narration path.

Immediately before re-enabling, record `RECORDING_WINDOW_START_UTC`, set `RECORDING_WINDOW_END_UTC` to exactly 60 minutes later, and run the pre-record hosted validation with that window. Re-enable ingress only once, using the supported Container Apps ingress command. If HTTPS health or the deterministic scenario fails, disable ingress immediately and stop. If recording does not begin within five minutes of restoration, disable ingress and stop.

Run one hosted validation and reset its scenario, then record the 115-second candidate. The recorder accepts the exact Azure FQDN only, requires HTTPS readiness with synthetic-only enabled and Foundry disabled, performs duplicate/out-of-order/profile/recap/fallback checks, and resets `matchpulse-demo-001` after capture. It does not start Docker, create directories, mutate profiles, upload files, or touch the existing MP4s.

Disable public ingress immediately after the candidate is produced (or after a failed attempt). Confirm the Container App, image, revision, replica bounds, retained resources, and five-resource count. Do not re-enable ingress automatically. Upload and challenge submission each need separate authorization.

### Hosted candidate shot order

Use the hosted submission shot list in `MATCHPULSE_SHOT_LISTS.md`. The candidate displays Azure hosting without showing subscription/tenant IDs, portal identity, local paths, connection strings, or credentials. It is a technical candidate only; a person must review the entire video before upload authorization.

---

## 2. Repository and Container Identity Gates

Before any browser session or recording starts, `scripts/record_matchpulse_demo.py` enforces the following fail-closed checks:

| Gate | Expected Value |
| --- | --- |
| Repository | `ofayese/matchpulse-live` |
| `origin/main` SHA | `335781f928011f99a644083d80bfe4dfc480b1a6` |
| Local `HEAD` SHA | `335781f928011f99a644083d80bfe4dfc480b1a6` |
| Published Image Digest | `ghcr.io/ofayese/matchpulse-live@sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226` |
| Attestation ID | `59336499` |
| Protected Workflow Run | `40059698831` |
| `org.opencontainers.image.revision` | `335781f928011f99a644083d80bfe4dfc480b1a6` |
| `org.opencontainers.image.source` | `https://github.com/ofayese/matchpulse-live` |
| Container Runtime User | `10001:10001` |

The published immutable container is executed locally with loopback-only port binding and hardened runtime flags:

```text
docker run -d --rm \
  --name matchpulse-video-demo \
  --user 10001:10001 \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  --pids-limit 128 \
  --cpus 1.0 \
  --memory 512m \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=32m \
  -p 127.0.0.1:8080:8080 \
  -e CHALLENGE_SYNTHETIC_ONLY=true \
  ghcr.io/ofayese/matchpulse-live@sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226
```

No Azure credentials, model API keys, or external endpoints are passed to the container.

---

## 3. Browser Configuration and Privacy Isolation

| Setting | Value |
| --- | --- |
| Browser Engine | Chromium (`156.0.8078.47` via Playwright `1.62.1`) |
| Viewport | `1920 × 1080` |
| Video Frame Size | `1920 × 1080` |
| Device Scale Factor | `1` |
| Frame Rate Target | `30 fps` (`30/1` constant frame rate) |
| Locale | `en-US` |
| Color Scheme | `dark` |
| Reduced Motion | `reduce` |
| Downloads | `acceptDownloads: false` |
| Service Workers | `serviceWorkers: "block"` |
| Default Base URL | `http://127.0.0.1:8080` |

### Browser Privacy Controls

The recording uses an ephemeral, isolated browser context (`browser.newContext(...)`) with Chromium flags `--disable-extensions`, `--disable-sync`, `--disable-notifications`, `--disable-translate`, `--no-first-run`, `--no-default-browser-check`, and `--password-store=basic`. Personal browser profiles, autofill, saved passwords, bookmarks, notifications, and unrelated tabs are completely disabled.

### Expected Application Endpoints and Profiles

- **Endpoints:**
  - `GET /demo` — Live interactive demonstration UI
  - `GET /health/live` — Liveness probe (`{"status": "ok"}`)
  - `GET /health/ready` — Readiness probe (`{"status": "ready", "synthetic_only": true, "foundry_mode": "disabled", ...}`)
  - `GET /v1/matches/matchpulse-demo-001/state` — Authoritative match state
  - `GET /v1/matches/matchpulse-demo-001/variants` — Cross-audience moment comparison
  - `GET /v1/matches/matchpulse-demo-001/recap` — Profile-specific and localized full-time recap
  - `POST /v1/matches/matchpulse-demo-001/reset` — Deterministic state reset
- **Audience Profiles (tested in strict order):**
  1. `fan-en` (`persona="fan"`, `locale="en"`, `detail="standard"`)
  2. `analyst-en` (`persona="analyst"`, `locale="en"`, `detail="deep"`)
  3. `broadcaster-en` (`persona="broadcaster"`, `locale="en"`, `detail="compact"`, registered via `PUT /v1/profiles/broadcaster-en`)
  4. `broadcaster-es` (`persona="broadcaster"`, `locale="es"`, `detail="compact"`)
  5. `fan-fr` (`persona="fan"`, `locale="fr"`, `detail="standard"`)

---

## 4. Fail-Closed Network Guard

Every browser request is intercepted via `context.route("**/*", ...)`:

- **Permitted Origins & Schemes:**
  - `http://127.0.0.1:8080` and `ws://127.0.0.1:8080`
  - `http://localhost:8080` and `ws://localhost:8080`
  - `about:blank`
  - Local `data:` URLs for self-contained title cards
- **Blocked Traffic:**
  - Every other host or scheme (analytics, telemetry, external fonts, CDNs, images, remote scripts, cloud control-plane APIs, GitHub mutation endpoints, or upload services) is immediately aborted (`route.abort("blockedbyclient")`).
  - Blocked requests are logged by `method`, `scheme`, `host`, `sanitized_path` (query strings stripped), `resource_type`, and `block_reason`.
  - Any unexpected external request causes the recording run to fail closed (`external_requests_detected == 0` required).

---

## 5. Accessible Selector Strategy and Runtime Safety Assertions

All browser interactions and verifications use semantic, accessible selectors and bounded waits (`<= 5,000 ms`):

1. **Synthetic Disclosure Gate:** `page.locator(".pill", has_text="SYNTHETIC DATA ONLY")` must be visible before any event is ingested.
2. **Controls:**
   - Audience profile selector: `page.getByLabel("Audience profile")` (`#profile`)
   - Comparison language selector: `page.getByLabel("Comparison language")` (`#language`)
   - Action buttons: `page.getByRole("button", { name: "Start synthetic demo" })` (`#start`) and `page.getByRole("button", { name: "Replay demo" })` (`#replay`)
3. **Live Regions:**
   - Status indicator: `page.getByRole("status")` (`#status`)
   - Primary insight overlay: `page.locator("#overlay")`
   - Live insight feed: `page.locator("#feed")`
   - Cross-audience comparison table: `page.locator("#compare")`
   - Full-time recap panel: `page.locator("#recap")`
   - Foundry status indicator: `page.locator("#foundry")`
4. **DOM Safety Scanner:** Before capturing every scene, the visible page text is scanned to ensure zero unhandled exceptions, stack traces, secret patterns (bearer tokens, API keys, personal access tokens, storage account keys, or telemetry instrumentation keys), or local user filesystem paths appear on screen.

---

## 6. Deterministic Synthetic Scenario (`matchpulse-demo-001`)

The scenario uses fixed seed `20261024`, match ID `matchpulse-demo-001`, fictional home team `Northbridge City`, and fictional away team `Harbor United`, validating strictly against `MatchEvent` in `src/matchpulse/models.py`:

| Step | Event ID | Seq | Clock (`ms` / `MM:SS`) | Event Type | Team / Player | Key Parameters & Verified Outcome |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `evt-mp-001` | `0` | `0` (`00:00`) | `match_start` | — | Match initialized (`status="live"`, score `0-0`) |
| 2 | `evt-mp-002` | `1` | `360000` (`06:00`) | `possession` | `Harbor United` | `share=62.0, previous_share=50.0` → `possession_swing` insight (`confidence=0.98`) |
| 3a | `evt-mp-003` | `2` | `540000` (`09:00`) | `pressure` | `Harbor United` / `HU-06` | `pressure=0.78` (1st high-press action in 30s window) |
| 3b | `evt-mp-004` | `3` | `550000` (`09:10`) | `pressure` | `Harbor United` / `HU-08` | `pressure=0.82` (2nd high-press action in 30s window) |
| 3c | `evt-mp-005` | `4` | `560000` (`09:20`) | `pressure` | `Harbor United` / `HU-11` | `pressure=0.86` → `pressing_surge` insight (`events=3`, `average=0.82`, `confidence=0.94`) |
| 4 | `evt-mp-006` | `5` | `720000` (`12:00`) | `tackle` | `Northbridge City` / `NC-08` | `outcome="success", x=74.0, y=42.0` → `tackle` high regain insight (`confidence=0.97`) |
| 5 | `evt-mp-007` | `6` | `960000` (`16:00`) | `shot` | `Harbor United` / `HU-09` | `outcome="on_target", speed_kmh=104.5` → saved shot + `shot_speed` insight (`confidence=0.96`) |
| 6 | `evt-mp-008` | `7` | `1200000` (`20:00`) | `pass` | `Northbridge City` / `NC-10` | `x=40.0, y=50.0, end_x=82.0, end_y=46.0, pressure=0.82` → counterattack `pass_quality` insight (`confidence=0.91`) |
| 7 | `evt-mp-009` | `8` | `1260000` (`21:00`) | `goal` | `Northbridge City` / `NC-09` | `outcome="success", x=89.0, y=48.0` → `goal` insight (`confidence=1.0`), score `Northbridge City 1 - 0 Harbor United` |
| 8 | `evt-mp-009` | `8` | `1260000` (`21:00`) | `goal` (duplicate) | `Northbridge City` / `NC-09` | Re-sent `evt-mp-009` → `HTTP 202`, `duplicate=true`, `duplicate_count=1`, score stays `1-0` |
| 9 | `evt-mp-010-ooo` | `5` | `1080000` (`18:00`) | `pass` (out-of-order) | `Harbor United` / `HU-04` | `sequence=5 <= last_sequence=8` → rejected with `HTTP 409 Conflict`, state unchanged |
| 10 | `evt-mp-011` | `9` | `2880000` (`48:00`) | `possession` | `Harbor United` | `share=64.0, previous_share=51.0` → tactical momentum shift `possession_swing` insight |
| 11 | `evt-mp-012` | `10` | `3360000` (`56:00`) | `goal` | `Harbor United` / `HU-11` | `outcome="success", x=88.0, y=52.0` → equalizer `goal` insight, score `Northbridge City 1 - 1 Harbor United` |
| 12 | — | `10` | `3360000` (`56:00`) | Profile inspection | `analyst-en` | Verifies formula, inputs, and confidence on shared insight |
| 13 | — | `10` | `3360000` (`56:00`) | Profile & locale transitions | `fan-en`, `analyst-en`, `broadcaster-en`, `broadcaster-es`, `fan-fr` | Verifies identical `match_id`, score, `insight_id`, `evidence.event_ids`, and `confidence` across all 5 variants |
| 14a | `evt-mp-013` | `11` | `4320000` (`72:00`) | `substitution` | `Northbridge City` / `NC-14` | Tactical substitution (`NC-14` for `NC-07`) |
| 14b | `evt-mp-014` | `12` | `5040000` (`84:00`) | `shot` | `Northbridge City` / `NC-10` | `outcome="blocked", speed_kmh=98.2` → late pressure `shot_speed` insight |
| 14c | `evt-mp-015` | `13` | `5280000` (`88:00`) | `goal` | `Northbridge City` / `NC-09` | `outcome="success", x=91.0, y=50.0` → late winner `goal` insight, score `Northbridge City 2 - 1 Harbor United` |
| 15 | `evt-mp-016` | `14` | `5400000` (`90:00`) | `match_end` | — | Final match state (`status="finished"`, `event_count=15`, `duplicate_count=1`, score `2-1`) |
| 16 | — | `14` | `5400000` (`90:00`) | Recap generation | All profiles / `en`, `es`, `fr` | `GET /v1/matches/matchpulse-demo-001/recap` verified with grounded `evidence_event_ids` |
| 17 | — | `14` | `5400000` (`90:00`) | Deterministic fallback | Local guard check | Verifies `foundry_mode="disabled"` and `FoundryNarrativeClient` malformed-JSON/timeout fallback preserving deterministic copy |
| 18 | — | — | — | Match reset | `POST /v1/matches/matchpulse-demo-001/reset` | Returns `{"match_id": "matchpulse-demo-001", "reset": true, "existed": true}` and clears state (`404` on subsequent state lookup) |

---

## 7. In-Memory Capture, Narration Synthesis, and FFmpeg Encoding Pipeline

To guarantee zero temporary directories are created anywhere on disk:

1. **In-Memory Browser Capture:** Playwright captures full `1920 × 1080` PNG buffers in memory at each verified state checkpoint (`page.screenshot(type="png")`).
2. **Deterministic Compositing & Cursor Trajectory:** Each shot composites the live browser frame with a high-contrast disclosure banner (`LOCAL DEMONSTRATION · SEEDED SYNTHETIC MATCH DATA · NO LIVE EXTERNAL DATA SOURCE`), an inspection callout panel showing the verified API/evidence state, and a smooth 30 fps cubic-bezier cursor trajectory so every frame has deterministic motion and zero accidental freeze frames.
3. **Synchronized Local Narration:** Narration is synthesized locally in memory using Windows `System.Speech.Synthesis.SpeechSynthesizer` (`48 kHz` stereo PCM) aligned to the exact `[start_ms, end_ms]` windows of `submission/MATCHPULSE_CAPTIONS_SUBMISSION.srt` and `submission/MATCHPULSE_CAPTIONS_TECHNICAL.srt`, then normalized with a two-pass FFmpeg EBU R128 `loudnorm` filter (`I=-16:TP=-1.5:LRA=11`).
4. **Master & Captioned Encoding:**
   - Uncaptioned master (historical archive: `submission/archive/videos/matchpulse-submission-demo.mp4`, `submission/archive/videos/matchpulse-technical-demo.mp4`): `libx264 -preset slow -crf 18 -pix_fmt yuv420p -r 30 -c:a aac -b:a 192k -ar 48000 -movflags +faststart`.
   - Captioned review copies (historical archive: `submission/archive/videos/matchpulse-submission-demo-captioned.mp4`, `submission/archive/videos/matchpulse-technical-demo-captioned.mp4`): rendered with title-safe bottom caption overlays synchronized to the SRT files.
5. **Post-Encoding Verification:** Every output MP4 is validated with `ffprobe`, `blackdetect`, `freezedetect`, `ebur128`, SRT parser checks, and a full secret/privacy scan before updating `submission/FINAL_VIDEO_MANIFEST.json`, `submission/MATCHPULSE_VIDEO_VERIFICATION.txt`, `audit-continuation.log`, and `audit-continuation.sha256`.
