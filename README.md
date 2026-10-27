# MatchPulse Live

[![challenge-ci](https://github.com/ofayese/matchpulse-live/actions/workflows/challenge-ci.yml/badge.svg)](https://github.com/ofayese/matchpulse-live/actions/workflows/challenge-ci.yml)

Live match feeds and raw statistics can be difficult to interpret at broadcast
speed, and the same moment is not equally useful to analysts, commentators,
and fans. **MatchPulse Live transforms synthetic football events into
explainable, audience-specific match intelligence for broadcast and streaming
experiences.** It presents each moment in a profile- and language-appropriate
overlay.

**Synthetic-data disclosure:** all demo events, match states, clubs, and
players are generated fictional data. The application does not ingest real
match feeds or player data.

**Supported views:** analyst, broadcaster, and fan profiles; deterministic
English, Spanish, and French narratives. The specialized processing stages
are deterministic Python components, not autonomous model-driven agents.

**Approved demo:** a human-approved local candidate is not uploaded. The
public video link is intentionally a placeholder: `<VIDEO_URL>` (add a URL
only after upload is authorized; voice-asset rights remain unresolved).

**Deployment status:** the immutable candidate passed hosted validation on
Azure Container Apps. A fresh read-only check on 2026-10-26 confirmed no
ingress configuration and the expected immutable image digest. No Foundry
runtime setting or model deployment was found; the recorded run made zero
model calls. The resource group contains five MatchPulse application and
monitoring resources plus two separately authorized Foundry development
resources. The Foundry account and project are not part of the submitted
MatchPulse runtime and are not deployed by MatchPulse Bicep. Hosted-agent
inventory was unavailable after the optional Preview returned 403; no hosted
agent is claimed. The current checkout contains later local changes that are
not in the deployed image.

**Quick links:** [Quick start](#quick-start) ·
[Architecture diagram](docs/ARCHITECTURE.md) ·
[Reproducibility limits](docs/REPRODUCIBILITY.md) ·
[Deployment and validation record](submission/TESTING_INSTRUCTIONS.md)

## What works now

- Strict synthetic event API with idempotency and ordering checks.
- Real-time match state for passes, shots, goals, tackles, pressure, and
  possession.
- Specialized deterministic processing stages: event interpretation,
  evidence validation, personalization, and localization.
- Evidence attached to every insight (source event IDs, inputs, formula,
  confidence).
- Distinct analyst, fan, and broadcaster experiences.
- English, Spanish, and French deterministic storytelling.
- WebSocket overlays, automated recaps, and a polished browser demo.
- Visual Studio solution, seeded synthetic match generator, tests, CI, Docker,
  and an Azure Container Apps Bicep template.

## Who it helps

- **Broadcast production teams** can use concise overlays to explain a
  synthetic match moment without building a second editorial pipeline.
- **Streaming platforms** can present the same accepted event stream as
  consistent, timed match context.
- **Club analysts** can inspect source IDs, calculation inputs, formulas,
  confidence, and deeper detail.
- **Fan companion apps** can offer a simpler, personalized view in English,
  Spanish, or French.
- **Multilingual editorial teams** can reuse evidence-grounded moments across
  the supported languages while keeping the source evidence attached.

These are intended use cases demonstrated with synthetic data, not claims of
an existing customer deployment or live sports-data integration.

## Quick start

Run the published image - no build, no setup, no credential:

```bash
docker run --rm -p 127.0.0.1:8080:8080 \
  ghcr.io/ofayese/matchpulse-live@sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226
```

Then open `http://127.0.0.1:8080/demo`, select an audience, and click
**Start synthetic demo**. This immutable published image is associated with
source commit
`335781f928011f99a644083d80bfe4dfc480b1a6`; its OCI revision/source labels
were verified against that source. Its recorded attestation identifier is
`59336499`. Hosted validation passed. Fresh read-only Azure state confirms
the configured image digest and no ingress configuration; no public endpoint
is enabled.
For details and limitations, see
[`submission/TESTING_INSTRUCTIONS.md`](submission/TESTING_INSTRUCTIONS.md).
The current checkout contains additional application and infrastructure
code, tests, scripts, and documentation changed after that source revision;
none of those post-deployment local changes are part of this image.

Or run it from source:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'

python -m pytest -q
python -m uvicorn matchpulse.service:app --host 127.0.0.1 --port 8080
```

In a second terminal, stream a match:

```bash
matchpulse-synthetic --url http://127.0.0.1:8080 --delay 0.15 --events 50
```

Then open `http://127.0.0.1:8080/demo`, select an audience, and click
**Start synthetic demo**.

With Docker:

```bash
docker compose -f compose.challenge.yml up --build
```

## Optional narration tooling

The application does not require narration tooling. The final submission narration was generated with ElevenLabs (stock voice Lily, `eleven_multilingual_v2`) during an active paid Starter subscription; no voice cloning was used and only generated audio is distributed in the video. See [`docs/ELEVENLABS_NARRATION.md`](docs/ELEVENLABS_NARRATION.md). Cloud TTS output is not byte-deterministic; the approved hashes are recorded there.

A superseded local Kokoro development path is documented in [`docs/LOCAL_TTS_PROVENANCE.md`](docs/LOCAL_TTS_PROVENANCE.md) and [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md). Its voice-asset rights remain unresolved, so it is not used for the final video. FFmpeg and FFprobe must be installed separately; model and voice assets are not stored in Git.

The complete validation gate:

```bash
python -m compileall src
python -m ruff check src tests scripts
python -m pytest -q
python -m pytest --cov=matchpulse --cov-report=term-missing --cov-fail-under=80
python scripts/preflight.py
python scripts/validate_solution.py
```

`scripts/bootstrap.sh` (Linux/macOS) and `scripts/bootstrap.ps1` (Windows) run
all of the above in one step.

## Visual Studio

`MatchPulse.Live.sln` organizes the solution into `src`,
`MatchPulse.Live.Api`, `tests`, `MatchPulse.Live.Tests`, `infrastructure`,
`MatchPulse.Live.Azure`, `build`, `MatchPulse.Live.Build`, `documentation`, and
`MatchPulse.Live.Docs`, with **Debug**, **Release**, and **ChallengeDemo**
configurations.

See [`README-VISUAL-STUDIO.md`](README-VISUAL-STUDIO.md) for the exact
interpreter setup, the required workload, and the command-line fallback.

## API quick check

```bash
curl -s http://127.0.0.1:8080/health/live
curl -s http://127.0.0.1:8080/health/ready
curl -s http://127.0.0.1:8080/v1/profiles
matchpulse-synthetic --jsonl --events 5 > data/demo-match.jsonl
```

Key routes:

| Route | Purpose |
|---|---|
| `POST /v1/events` | Ingest one strict synthetic event and return personalized insights |
| `POST /v1/events/batch` | Ingest up to 500 ordered events |
| `GET /v1/matches/{id}/state` | Current explainable match state |
| `GET /v1/matches/{id}/recap?profile_id=fan-en` | Automated profile-specific recap |
| `GET /v1/matches/{id}/variants?locale=es` | One authoritative moment presented to every audience |
| `POST /v1/demo/runs` | Start a bounded, seeded, synthetic-only demo run |
| `GET /v1/demo/runs/{run_id}` | Demo run lifecycle state |
| `WS /ws/matches/{id}?profile_id=fan-en` | Timed, machine-readable live overlay stream |
| `GET /health/live`, `GET /health/ready` | Liveness and readiness probes |
| `GET /demo` | Live overlay demo page |

## Microsoft Foundry mode — ROADMAP — NOT IN CURRENT SUBMISSION

The checkout contains a guarded optional copy-edit adapter, but the validated
deployed image ran with Foundry off and made zero model calls. No Foundry model
use is claimed for the current submission. With no Foundry configuration the
service reports `"foundry_mode": "disabled"` on `/health/ready` and every
insight comes from the deterministic pipeline.

`foundry_mode` reports one of four truthful states:

| State | Meaning |
|---|---|
| `disabled` | No Foundry configuration; the deterministic pipeline is the only output |
| `configured-unverified` | Configured, but no model call has succeeded yet |
| `verified` | A model call completed and passed every guard |
| `degraded-fallback` | A call failed or a rewrite was rejected; the deterministic narrative is used |

To enable the optional rewrite, set environment variables (see
[`.env.example`](.env.example)):

| Variable | Required | Notes |
|---|---|---|
| `FOUNDRY_ENDPOINT` | Yes | Azure OpenAI / Foundry endpoint |
| `FOUNDRY_DEPLOYMENT` | Yes | Deployment name |
| `FOUNDRY_AUTH_MODE` | No | `managed_identity` (preferred) or `api_key` |
| `FOUNDRY_API_KEY` | Only for `api_key` | Runtime secret, never committed |
| `FOUNDRY_API_VERSION` | No | Defaults to `2024-10-21` |
| `FOUNDRY_TIMEOUT_SECONDS` | No | Defaults to `1.4` |
| `FOUNDRY_MAX_CONCURRENCY` | No | Maximum concurrent model calls, default `1`; excess concurrent calls fall back deterministically |
| `FOUNDRY_CALL_BUDGET` | No | Per-process outbound call budget, default `20`; resets on process restart and is not a durable billing limit |

The model adapter makes one attempt per rewrite (no automatic retries), uses a
1.4-second default timeout, caps each response at 128 tokens, and sends no
prompt payload larger than 4 KiB. Oversized prompts and exhausted call budgets
use the deterministic text. These controls limit one process; restarts reset
the call count. They are not a hard Azure spend limit.

The model is a constrained copy editor, not the source of facts. It cannot
create match state, alter evidence, or introduce a number that is not in the
grounded input. On a timeout, invalid JSON, service error, unsupported claim,
or schema mismatch, the service uses the deterministic narrative. The rewrite
is validated in a fixed order - markup, identifiers, names, causality, then
numbers - and the rewritten numbers must form a subsequence of the source
numbers.

## Deployment status and operating limits

The Azure Container Apps candidate is identified by source revision
`335781f928011f99a644083d80bfe4dfc480b1a6`, image digest
`ghcr.io/ofayese/matchpulse-live@sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226`,
and recorded attestation ID `59336499`. Hosted validation passed. A fresh
read-only Azure check on 2026-10-26 confirmed that the configured image digest
is unchanged and the app has no ingress configuration. No Foundry runtime
setting or model deployment was found; the recorded run made zero model
calls. Foundry runtime is disabled in the submitted MatchPulse deployment,
and the demonstrated workflow makes zero model calls. The separately
authorized Foundry account and project are development resources, not
MatchPulse runtime dependencies; they are not deployed by MatchPulse Bicep,
and the approved video does not demonstrate Foundry usage. These facts
describe that immutable image, not the newer files in this checkout.

| Area | Current evidence and limit |
|---|---|
| Health | `/health/live` and `/health/ready` expose liveness/readiness; readiness reports `synthetic_only: true`, and the container template defines probes. |
| Security evidence | Fresh read-only Azure state showed no ingress configuration; the API rejects non-synthetic data; the Bicep template has no secret parameter and its validation guard checks for hardcoded subscription/tenant IDs and secret literals. This is evidence of scoped controls, not a production security certification. |
| Data boundary | The app is synthetic-only. Do not connect real match or player data. |
| Scale and state | The configured replica range is 0–1. State and WebSocket subscribers are in process; restarts clear state, and multi-replica fan-out is unsupported. |
| Replay and recovery | No Event Hubs consumer, durable checkpoint, or replay store is deployed. A process restart loses in-memory match state; safe recovery requires an approved immutable-image rollback and validation, not an unreviewed redeployment. |
| Logs and spend | Log Analytics retention is 30 days with a 0.023 GB/day ingestion cap. The cap can overshoot; read-only budget results show a $25 monthly resource-group alert and a separate $50 annual subscription alert. Month-to-date spend read back as $0 USD; neither budget is a hard limit. |
| Telemetry | Application Insights is provisioned, but custom application telemetry is not verified for the deployed image. |
| Exposure | The current Azure app has no ingress configuration. The local Docker quick start binds only to loopback. |

This is a validated challenge candidate, not a production-ready public service.
Keep ingress disabled unless a separately approved change includes access
controls, load/state design, observability verification, cost monitoring, and
recovery testing.

## Roadmap

Every item below is future work, not functionality included in the current
submission:

- **ROADMAP — NOT IN CURRENT SUBMISSION** — richer play-style, counterattack,
  and player-pattern analysis.
- **ROADMAP — NOT IN CURRENT SUBMISSION** — Event Hubs ingestion, durable
  state, and replay.
- **ROADMAP — NOT IN CURRENT SUBMISSION** — multi-replica WebSocket fan-out,
  shared state, and multi-region operation.
- **ROADMAP — NOT IN CURRENT SUBMISSION** — dynamic model tools or
  model-directed actions.
- **ROADMAP — NOT IN CURRENT SUBMISSION** — user authentication and persisted
  preferences.
- **ROADMAP — NOT IN CURRENT SUBMISSION** — languages beyond English,
  Spanish, and French.
- **ROADMAP — NOT IN CURRENT SUBMISSION** — AKS deployment.
- **ROADMAP — NOT IN CURRENT SUBMISSION** — Foundry-powered inference in the
  deployed experience; current deployed runtime is off with zero calls.
- **ROADMAP — NOT IN CURRENT SUBMISSION** — autonomous or multi-agent
  orchestration; current processing stages are deterministic components.

## Challenge artifacts

- [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) - architecture diagram,
  repeatable application commands, media limitations, and provenance.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - architecture, reliability,
  and security design notes.
- [`docs/CHALLENGE_ALIGNMENT.md`](docs/CHALLENGE_ALIGNMENT.md) - requirement
  and judging-criteria trace.
- [`docs/AZURE_DEPLOYMENT.md`](docs/AZURE_DEPLOYMENT.md) - validated
  infrastructure commands, Foundry identity, and cleanup.
- [`docs/GITHUB_PUBLICATION.md`](docs/GITHUB_PUBLICATION.md) - publication
  layout, CI, and manual configuration steps.
- [`submission/`](submission) - pitch, project description, 120-second demo
  script, testing instructions, and registration/submission checklists.
- [`infra/`](infra) - Azure Container Apps Bicep template.

## Safety and scope boundary

`CHALLENGE_SYNTHETIC_ONLY=true` is mandatory. The Pydantic schema accepts
only `source="synthetic"`, and the API refuses to ingest when the challenge
safety gate is disabled. Do not include real match footage, real player data,
EA responses, club credentials, or Premier League marks in this repository or
in any demo video.

## License

Apache-2.0. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
