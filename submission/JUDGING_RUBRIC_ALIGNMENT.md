# MatchPulse Live — judging rubric alignment

The five judging categories below are equally weighted at **20% each**. This
guide maps claims to the current repository and the approved demonstration.
It distinguishes the current source from the already-deployed image: local
checkout changes made after deployment are not in that image.

## Approved demonstration and deployment boundary

- **Approved local video (not committed or uploaded):**
  `matchpulse-submission-hosted-elevenlabs-lily-v1-candidate.mp4`
- **SHA-256:** `f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`
- **Duration:** 115 seconds. Human decision: APPROVED; upload and challenge
  submission remain separate, pending actions.
- **Public video URL:** `<VIDEO_URL>`; not available before separate upload authorization.
- **Local-only approval evidence:** `FINAL_VIDEO_APPROVAL.md`,
  `FINAL_VIDEO_MANIFEST.json`, and the hosted English captions are excluded
  from the proposed public repository allowlist.
- **Deployed image:** `ghcr.io/ofayese/matchpulse-live@sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226`,
  recorded as associated with source revision
  `335781f928011f99a644083d80bfe4dfc480b1a6`. The digest is immutable; the
  current local source edits are not included in it. See
  [`docs/AZURE_DEPLOYMENT.md`](../docs/AZURE_DEPLOYMENT.md) and
  [`submission/PROJECT_DESCRIPTION.md`](PROJECT_DESCRIPTION.md).
- The existing Azure Container Apps deployment was observed with public
  ingress disabled and Foundry runtime off; the approved run made zero model
  calls. This document does not imply a publicly reachable hosted demo.

## 1. Technological Implementation — 20%

1. **Verifiable evidence**
   - Strict event models allow only `source="synthetic"`; `/v1/events` and
     `/v1/events/batch` accept validated events over HTTP.
   - `MatchAccumulator` updates process-local match state under a lock.
     Repeated event IDs are acknowledged without applying them again;
     sequence numbers less than or equal to the last accepted sequence are
     rejected. The behavior is covered by API and pipeline tests.
   - Generated insights retain source event IDs, calculation inputs,
     formulas, and confidence. The evidence check confirms referenced events
     were accepted; recaps expose evidence event IDs.
   - The service exposes HTTP APIs and profile-targeted WebSocket overlays.
     When Foundry is not configured, narrative output is deterministic.
   - The deployed ACA image is digest-pinned. Read-only deployment evidence
     records ingress disabled, Foundry off, no model deployment, and a
     single-replica maximum appropriate to process-local state.
2. **Repository refs**
   - [`src/matchpulse/models.py`](../src/matchpulse/models.py):
     `MatchEvent`, `Evidence`, strict synthetic source and event fields.
   - [`src/matchpulse/synthetic.py`](../src/matchpulse/synthetic.py):
     seeded synthetic event generation and HTTP streaming.
   - [`src/matchpulse/state.py`](../src/matchpulse/state.py):
     `MatchAccumulator.apply`, accepted-event store, duplicate handling,
     sequence guard, and derived evidence.
   - [`src/matchpulse/agents.py`](../src/matchpulse/agents.py):
     evidence validation and evidence-carrying recap.
   - [`src/matchpulse/service.py`](../src/matchpulse/service.py):
     HTTP ingestion, recap/variant endpoints, WebSocket delivery, and demo
     routes.
   - [`tests/test_pipeline.py`](../tests/test_pipeline.py),
     [`tests/test_api.py`](../tests/test_api.py): duplicate idempotency,
     out-of-order rejection, recap evidence, and WebSocket output.
   - [`infra/main.bicep`](../infra/main.bicep),
     [`docs/AZURE_DEPLOYMENT.md`](../docs/AZURE_DEPLOYMENT.md): digest image
     parameter, ACA health probes and operating boundary.
3. **Approved demo refs**
   - Video `00:00–00:18`: ACA context, synthetic-only disclosure, and
     evidence-linked moments.
   - `00:18–00:54`: accepted synthetic goal, replayed duplicate does not
     change the score, and out-of-order event rejection.
   - `01:27–01:39`: recap cites accepted event evidence.
   - `01:39–01:48`: Foundry/model calls disabled and deterministic fallback.
   - The SRT and approval record remain local-only and are not commit inputs.
4. **Current strengths**
   - Concrete, testable event contract and deterministic rule-based state
     transitions; duplicate retry and ordering behavior are visible in the
     approved demo.
   - Insight-to-event lineage is represented in the API data, not only in
     narrative copy.
   - HTTP, WebSocket, profile variants, health endpoints, and an immutable
     deployed image are present and documented.
5. **Residual weaknesses**
   - State and event history are in memory; restart loses them. Replay means
     re-sending a synthetic event/stream, not durable replay from persisted
     checkpoints.
   - Only one replica is supported; shared WebSocket fan-out, durable
     checkpoints, and production-scale reliability have not been established.
   - ACA ingress was disabled after the recorded deployment validation, but a
     fresh state read was unavailable during finalization. The deployed image corresponds to an
     earlier source revision, not the current edited checkout.
   - No real match feed or production SLO claim is supported by this evidence.
6. **Safe submission wording**
   - “A synthetic-event prototype with deterministic, process-local match
     state, duplicate idempotency, monotonic sequence checks, and
     evidence-linked insights delivered through HTTP and WebSocket APIs.”
   - “The approved 115-second demo shows duplicate replay handling,
     out-of-order rejection, and a recap that cites accepted event evidence.”
   - “The deployed Azure Container Apps candidate is pinned to an immutable
     image digest; a fresh read-only check found no ingress configuration,
     Foundry runtime setting, or model deployment.”
7. **Claims to avoid**
   - Durable/event-sourced replay, persistent state, multi-replica support,
     end-to-end production readiness, measured production SLOs, or a publicly
     available live endpoint.
   - Event Hubs ingestion, AKS deployment, real-time external match data,
     real-world prediction accuracy, or active Foundry inference.
   - That the deployed image contains uncommitted or post-deployment local
     changes.

## 2. Agentic Design & Innovation — 20%

1. **Verifiable evidence**
   - The source coordinates deterministic processing components: the code
     classes are named `SupervisorAgent`, `InterpretationAgent`,
     `ExplainabilityAgent`, and `PersonalizationAgent`. Localization is
     rendered from curated catalogs. These are implementation names and
     sequential application logic—not autonomous agents.
   - There is no autonomous model/tool planning in the deployed configuration.
     Foundry is disabled there and the approved run records zero model calls.
2. **Repository refs**
   - [`src/matchpulse/agents.py`](../src/matchpulse/agents.py): the exact
     class names and `SupervisorAgent.process` orchestration.
   - [`src/matchpulse/state.py`](../src/matchpulse/state.py): deterministic
     event interpretation and signal derivation.
   - [`src/matchpulse/localization.py`](../src/matchpulse/localization.py):
     deterministic language/persona render catalogs.
   - [`src/matchpulse/foundry.py`](../src/matchpulse/foundry.py) and
     [`infra/main.bicep`](../infra/main.bicep): optional guarded adapter in
     source versus Foundry-off deployed configuration.
3. **Approved demo refs**
   - Video `00:18–00:28` and `00:46–01:27`: evidence-linked output,
     audience variants, and localization without changing match facts.
   - Video `01:39–01:48`: explicitly states Foundry and model calls are
     disabled and output remains deterministic.
   - The approved captions and local approval record are the references for
     what the recording actually demonstrates; neither is included in the
     proposed public commit.
4. **Current strengths**
   - A clear, auditable sequence links interpretation, evidence validation,
     profile personalization, and localization.
   - The same evidence-bearing moment is transformed for distinct audiences
     while keeping match facts and event lineage.
   - The design avoids model dependency in the deployed run; a deterministic
     path remains authoritative.
5. **Residual weaknesses**
   - The implementation is a specialized processing pipeline /
     agentic-inspired orchestration, not an autonomous multi-agent system.
   - It does not demonstrate model-led planning, dynamic tool selection,
     agent-to-agent negotiation, or active Foundry operation.
6. **Safe submission wording**
   - “MatchPulse uses a specialized processing pipeline (agentic-inspired
     orchestration) for event interpretation, evidence validation,
     personalization, and localization.”
   - “The source uses the class identifiers `SupervisorAgent`,
     `InterpretationAgent`, `ExplainabilityAgent`, and
     `PersonalizationAgent`; they execute deterministic application code.
     No autonomous model/tool planning is enabled in the deployed run.”
7. **Claims to avoid**
   - “Multi-agent system,” “autonomous agents,” agentic decision-making,
     model-selected tools, or a Foundry-powered live workflow.
   - Treating class names or handoff telemetry as proof of independent
     autonomous agents.

## 3. Real-World Impact & Applicability — 20%

1. **Verifiable evidence**
   - The product concept addresses live football storytelling for fans,
     analysts, and broadcasters. Synthetic events produce recognizable
     statistics and moments; outputs include rationale and source event IDs.
   - Profile-specific recaps and the en/es/fr render catalogs demonstrate
     potential for audience-specific presentation.
2. **Repository refs**
   - [`src/matchpulse/synthetic.py`](../src/matchpulse/synthetic.py):
     fictional teams/players and seeded event patterns.
   - [`src/matchpulse/state.py`](../src/matchpulse/state.py):
     goal, shot-speed, pass-quality, pressing, possession, and tackle rules.
   - [`src/matchpulse/service.py`](../src/matchpulse/service.py):
     profiles, recaps, variants, and delivery APIs.
   - [`src/matchpulse/localization.py`](../src/matchpulse/localization.py):
     English, Spanish, and French templates.
   - [`submission/PROJECT_DESCRIPTION.md`](PROJECT_DESCRIPTION.md):
     synthetic prototype and deployment limitations.
3. **Approved demo refs**
   - Video `00:00–00:08`: synthetic match disclosure.
   - `00:46–01:27`: fan, analyst, broadcaster, Spanish, and French
     presentations; the same facts persist across variants.
   - `01:27–01:39`: evidence-citing match recap.
4. **Current strengths**
   - Demonstrates a plausible broadcast/second-screen use case with
     explainable event-derived output and several audience presentations.
   - Synthetic-only scope allows the judging demo to exercise match moments
     without claiming real match access.
   - Multilingual, profile-specific recaps broaden the prototype's intended
     audience.
5. **Residual weaknesses**
   - All match data is seeded and synthetic; there is no licensed live feed,
     real-world validation, editorial review workflow, or evidence of adoption.
   - Player/team patterns and play-style/counterattack intelligence are not
     current functionality. The app is not validated for production
     broadcast use.
6. **Safe submission wording**
   - “A prototype illustrating how synthetic, evidence-linked match events
     could support fan, analyst, and broadcaster experiences.”
   - “The demo shows localized and profile-specific recaps; integrating
     licensed live data and validating with editorial users remain future
     work.”
7. **Claims to avoid**
   - Live match coverage, professional club/league use, user adoption,
     measured business impact, player scouting/assessment, or validated
     performance on real games.
   - Any suggestion that fictional teams, players, statistics, or events are
     real.

## 4. User Experience & Presentation — 20%

1. **Verifiable evidence**
   - The demo UI supports synthetic runs/replay and profile selection. Fan,
     analyst, and broadcaster outputs differ in length/detail; English,
     Spanish, and French catalogs preserve the same underlying evidence.
   - HTTP responses, recaps, and WebSocket overlays carry machine-readable
     event evidence. Deterministic output is available with Foundry disabled.
2. **Repository refs**
   - [`src/matchpulse/service.py`](../src/matchpulse/service.py): `/demo`,
     `/v1/profiles`, `/v1/matches/{match_id}/recap`,
     `/v1/matches/{match_id}/variants`, `/v1/events`, and
     `/ws/matches/{match_id}`.
   - [`src/matchpulse/agents.py`](../src/matchpulse/agents.py):
     profile-specific rendering and recap generation.
   - [`src/matchpulse/localization.py`](../src/matchpulse/localization.py):
     curated language/persona text.
   - [`tests/test_variants.py`](../tests/test_variants.py),
     [`tests/test_localization.py`](../tests/test_localization.py), and
     [`tests/test_api.py`](../tests/test_api.py): variant, localization,
     recap, and WebSocket checks.
3. **Approved demo refs**
   - Video `00:46–01:20`: fan, analyst, broadcaster, Spanish, and French.
   - `01:20–01:39`: localized recap and accepted-event evidence.
   - The approved 115-second video is the presentation reference; the exact
     filename, hash, and review status are recorded above.
4. **Current strengths**
   - The approved short demo communicates synthetic-data scope, profile
     differences, duplicate/out-of-order handling, evidence lineage, recap,
     and the Foundry-off boundary.
   - API and WebSocket output can be inspected as structured data, not just
     rendered copy.
5. **Residual weaknesses**
   - The demo is a fixed, 115-second recording; it is not proof that the
     hosted app is publicly interactive.
   - Source changes after deployment are absent from the pinned image.
     Persistent user preferences and multi-replica delivery are not provided.
6. **Safe submission wording**
   - “The approved 115-second demo presents the synthetic workflow, audience
     variants, localized copy, evidence-grounded recap, and duplicate and
     out-of-order handling.”
   - “A local/API demo UI and HTTP/WebSocket interfaces are implemented;
     public ACA ingress was disabled after the recorded validation.”
7. **Claims to avoid**
   - Public interactive access, accessibility certification, user-tested
     usability, real-time public service availability, or that every current
     checkout change appears in the recording or deployed image.

## 5. Adherence to Hackathon Category — 20%

1. **Verifiable evidence**
   - The prototype accepts synthetic football events, derives match moments,
     attaches accepted-event evidence, and renders audience-specific
     real-time style output and recaps—the behaviors shown in the approved
     demo.
   - Synthetic-only model and data boundaries are explicit in code, the
     video, and the submission description.
2. **Repository refs**
   - [`docs/CHALLENGE_ALIGNMENT.md`](../docs/CHALLENGE_ALIGNMENT.md):
     requirement-to-evidence trace and category cautions.
   - [`src/matchpulse/models.py`](../src/matchpulse/models.py),
     [`src/matchpulse/synthetic.py`](../src/matchpulse/synthetic.py), and
     [`src/matchpulse/service.py`](../src/matchpulse/service.py): synthetic
     contract, generator, ingestion, and presentation interfaces.
   - [`tests/test_api.py`](../tests/test_api.py) and
     [`tests/test_pipeline.py`](../tests/test_pipeline.py): synthetic-source
     rejection, ordering/idempotency, evidence, and recap checks.
3. **Approved demo refs**
   - Video `00:00–00:46`: synthetic-only match and duplicate/out-of-order
     behavior.
   - `00:46–01:39`: profile variants, languages, and evidence-grounded
     recap.
   - `01:39–01:55`: Foundry-off disclosure and synthetic/no-external-data
     closing disclosure.
4. **Current strengths**
   - The demonstrated solution aligns its event pipeline, evidence trail,
     real-time presentation concept, and audience customization to the
     sports-data storytelling problem.
   - The submission describes the limitations rather than representing
     synthetic data or optional integrations as live capabilities.
5. **Residual weaknesses**
   - Alignment is demonstrated with synthetic fixtures, not an operational
     sports data partnership or live match stream.
   - A category-specific fit does not itself establish eligibility,
     originality, judging outcome, or satisfaction of portal requirements.
6. **Safe submission wording**
   - “The submission demonstrates a synthetic-data sports storytelling
     prototype: event ingestion, evidence-linked interpretation,
     audience-specific rendering, localization, and recap.”
   - “The approved video shows the implemented behavior; see the repository
     and tests for verifiable detail.”
7. **Claims to avoid**
   - Official endorsement, league affiliation, category eligibility
     guarantees, access to real match feeds, completed portal submission,
     or judging results.

## Conservative self-assessment — not a judge prediction

The following internal estimate uses a 1–5 scale and the five equally weighted
categories in the task brief. It is intentionally conservative because the
live portal rules/category are unavailable, the video is not public, and the
solution is a synthetic-data prototype without durable state or deployed
Foundry inference.

| Category | Estimate (/5) | Basis for the conservative estimate |
|---|---:|---|
| Technological implementation | 3.5 | Strong tests, deterministic evidence lineage, immutable deployment, and scoped security controls; no durable state or public endpoint. |
| Agentic design and innovation | 2.5 | Clear specialized pipeline and deterministic fallback; no autonomous agents or deployed model-driven workflow. |
| Real-world impact and applicability | 3.0 | Credible target users and use cases; no measured adoption or external impact evidence. |
| User experience and presentation | 3.5 | Three audiences, three languages, WebSocket/demo UI, and approved narration; video is not uploaded and captions need a reviewed V2 file. |
| Category adherence | 3.5 | Synthetic football-event transformation is aligned with the stated challenge; exact live category and portal rules remain unverified. |

Weighted estimate: **3.2/5 (64/100)**. Treat this only as a planning
self-assessment, not an expected score or guarantee of eligibility.

## Roadmap — NOT IN CURRENT SUBMISSION

These are unimplemented future directions, not current submission claims.
Planning estimates are rough person-weeks for one experienced engineer,
including focused tests but excluding procurement, legal review, and
organization approval.

| Roadmap item | Value | Major components | Dependencies | Estimate | Main risk |
|---|---|---|---|---:|---|
| Play-style classification | Add tactical context to evidence-backed moments. | Event-feature definitions, deterministic classifier, evaluation fixtures. | Stable event taxonomy and analyst-reviewed synthetic labels. | 2–4 weeks | Labels may encode subjective tactics or perform poorly on sparse sequences. |
| Counterattack detection | Surface rapid possession transitions for broadcasters and analysts. | Possession-change tracking, transition window, forward-progress rules, evidence links. | Reliable event ordering and possession semantics. | 2–3 weeks | Missing events can create false transitions. |
| Player-performance analytics | Explain player contributions across a match. | Per-player aggregates, minutes/context normalization, evidence-linked summaries. | Stable player IDs, agreed metric definitions, representative synthetic data. | 3–5 weeks | Small samples and biased metrics can misrepresent performance; real data adds licensing risk. |
| Event Hubs consumer | Decouple event ingestion and support burst buffering. | Consumer group, schema validation, retry/dead-letter policy, operational metrics. | Approved identity/network design, event schema, capacity and cost review. | 3–5 weeks | Duplicate delivery and poison messages can corrupt downstream state without idempotency. |
| Durable replay | Rebuild match state deterministically after restart. | Versioned event log, snapshots/checkpoints, replay runner, migration tests. | Durable storage decision, event versioning, retention policy. | 3–6 weeks | Schema evolution can make historical replays diverge. |
| WebSocket backplane | Deliver consistent overlays across replicas. | Managed pub/sub or SignalR, subscription routing, backpressure controls. | Multi-replica deployment and shared match-state strategy. | 2–4 weeks | Ordering, reconnect storms, and fan-out costs. |
| Durable match state | Preserve accepted events and match state across restarts. | Transactional persistence, idempotency keys, snapshots, migrations. | Data classification, retention policy, managed database selection. | 3–6 weeks | Partial writes or concurrent updates can create inconsistent state. |
| Multi-region failover | Improve regional recovery and availability. | Regional app instances, health routing, state replication, failover exercises. | Durable state, tested recovery objectives, budget and network design. | 4–8 weeks | Split-brain writes and unbounded cross-region cost. |
| Dynamic analytics tools | Add policy-bounded selection of specialized analytics. | Tool registry, typed inputs/outputs, allowlist, timeout and evidence gates. | Stable tool contracts, threat model, audit requirements. | 3–5 weeks | Unsafe or unsupported tool output could introduce ungrounded claims. |
| Foundry-enabled workflows | Evaluate optional grounded copy-edit or analysis workflows. | Approved model deployment, managed identity, prompt boundaries, evaluation and fallback. | Explicit authorization, rights/privacy review, quota and cost controls. | 3–6 weeks | Hallucinations, data exposure, or cost can outweigh editorial value. |
| Authentication and preferences | Support user-specific settings and consent. | Identity integration, authorization, preference store, deletion/consent flows. | Privacy/legal review, threat model, persistence decision. | 4–7 weeks | Personal data handling and account recovery expand security obligations. |
| More languages | Reach additional editorial audiences. | Reviewed catalogs, locale formatting, terminology and accessibility checks. | Native-language reviewers and maintained translation resources. | 2–4 weeks per language | Literal translations can distort football terminology or tone. |
| Generative translation | Accelerate multilingual drafting while preserving facts. | Translation model/service, terminology constraints, evidence-preservation checks, human review. | Rights-cleared provider, supported language evaluation, deterministic fallback. | 3–6 weeks | Hallucination, cultural nuance, and inconsistent terminology. |
| AKS scale-out | Support a larger orchestration footprint if operationally justified. | Kubernetes manifests, autoscaling, ingress/security, observability, release operations. | Proven multi-replica state/backplane need and staffed operations. | 6–10 weeks | Added platform complexity and cost without demonstrated workload need. |
| Visible handoff/evidence trace | Let reviewers inspect sanitized processing stages beside an insight. | Shared evidence ID, runtime mode, grounding status, actual-code stage status/duration, accessible `<details>` UI. | Stable evidence contracts, privacy review, API/UI regression plan. | 1–3 weeks | Trace can leak sensitive data or become inconsistent with the actual pipeline. |

No estimate is a commitment or evidence that the feature exists. The visible
handoff/evidence trace is explicitly deferred; see the decision in
[`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md).
