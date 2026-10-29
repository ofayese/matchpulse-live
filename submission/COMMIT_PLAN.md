> **UPDATE 2026-10-27 — SUPERSEDING NOTE:** The human-approved ElevenLabs Lily V1 video (`f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`) is now the sole active submission video, with `VOICE_RIGHTS_CONCLUSION=ELEVENLABS_PAID_COMMERCIAL_LICENSE` and `THIRD_PARTY_RIGHTS_DECLARATION=YES`. Any Kokoro / `bf_emma` / `RIGHTS_UNRESOLVED` / `PENDING_RIGHTS_REMEDIATION` / rights-remediation blocker language below is **historical** (`KOKORO_VOICE_RIGHTS_CONCLUSION=RIGHTS_UNRESOLVED`, `SUPERSEDED_FOR_RIGHTS_CERTAINTY`) and no longer blocks the active video. Commit, push, YouTube upload, and challenge submission remain separately gated; see `submission/VOICE_RIGHTS_DECISION.md` and the top-level authorization packets.

# Proposed commit plan

**Inventory snapshot:** 2026-10-26, refreshed for packet completion. This is
a planning document only: no files were staged, committed, pushed, or deleted.
The final census is **44 modified tracked paths, 33 visible untracked files
(including this plan and the three authorization packets), and one
skip-worktree-hidden tracked edit**. The earlier census counted 30 visible
untracked files before the three packet files were created. Ignored files are
not commit inputs. No paths are staged. Recheck status and index flags before
any future commit.

## Repository and publication state

- Repository: `ofayese/matchpulse-live`; `origin` fetch/push URL is
  `https://github.com/ofayese/matchpulse-live.git`.
- `HEAD` is detached at `origin/main` (`335781f`); there is no current branch
  name or upstream tracking branch. The default branch is `main`.
- No open pull requests were returned by GitHub.
- GitHub reports `main` as `protected: false`; the classic branch-protection
  endpoint returned 404 and the rulesets query returned no entries. Do not
  assume branch protection or required PR checks.
- `git diff --check` reported no whitespace errors. Git did emit CRLF-to-LF
  normalization warnings for several modified Python files.

## Proposed allowlists

These are mutually exclusive candidate sets, not instructions to stage or
commit. Review the full diff and the gates below before any future submission.

### A — Azure recovery and challenge-facing documentation

1. `README.md`
2. `docs/ARCHITECTURE.md`
3. `docs/AZURE_COST_PLAN.md`
4. `docs/AZURE_DEPLOYMENT.md`
5. `docs/AZURE_MODEL_PLAN.md`
6. `docs/AZURE_PROVIDER_AND_RBAC_PLAN.md`
7. `docs/CHALLENGE_ALIGNMENT.md`
8. `docs/REPRODUCIBILITY.md`
9. `infra/main.bicep`
10. `infra/main.parameters.example.json`
11. `infra/validate_template.py`
12. `scripts/hardened_smoke_test.py`
13. `scripts/preflight.py`
14. `scripts/smoke_test.py`
15. `scripts/validate_attestation_verification.py`
16. `scripts/validate_solution.py`
17. `submission/PROJECT_DESCRIPTION.md`
18. `submission/TESTING_INSTRUCTIONS.md`
19. `submission/JUDGING_RUBRIC_ALIGNMENT.md`
20. `tests/test_attestation_validation.py`
21. `tests/test_hardened_smoke.py`
22. `tests/test_solution_layout.py`

**Diff summary:** Bicep adds an option to reuse existing monitoring and
Container Apps foundation resources; example parameters and template
validation are updated. Preflight, smoke, attestation, and solution checks are
adjusted. Architecture, reproducibility, Azure cost/deployment/model/provider/
RBAC, and challenge-alignment documents, the README, and three public
submission documents are refreshed. The historical registration checklist is
excluded as local audit material.
The three listed tests cover the smoke and solution-layout validation changes.

**Public-release gates:** The refreshed redacted scan found no actual
subscription/tenant/resource identifiers, local paths or usernames, email
addresses, tokens, connection secrets, or private endpoints in the proposed
files. Retain the public source SHA, immutable image digest, and attestation
record where they are needed as verifiable provenance; use placeholders for
operational identities not needed by readers. Before any public commit,
re-review the exact diffs and deployment-status claims; do not imply that
these checkout changes are deployed. Do not run Azure mutations or a
deployment as part of this review.

### B — local narration tooling

1. `pyproject.toml`
2. `THIRD_PARTY_NOTICES.md`
3. `docs/LOCAL_TTS_PROVENANCE.md`
4. `scripts/matchpulse_conversational_tts.py`
5. `scripts/matchpulse_kokoro_v2.py`
6. `scripts/matchpulse_local_tts.py`
7. `scripts/record_matchpulse_demo.py`
8. `scripts/record_matchpulse_hosted_submission.py`
9. `tests/test_conversational_tts.py`
10. `tests/test_kokoro_v2_narration.py`
11. `tests/test_local_tts.py`
12. `.gitignore` — approved generated-media, local-audit, local-TTS, and
    local-Azure ignore-rule hunk only; exclude the separate `.fake` line.

**Diff summary:** Adds local Kokoro TTS, conversational narration and v2
orchestration and recording tools, the Pillow dependency needed by recording,
tests for those tools, and notices/provenance describing dependencies and
unresolved asset/voice rights. The hosted recorder requires an explicit Azure
Container Apps hostname. The shared recorder also requires an explicit
allowlist for sibling directories, rejects workspace-root files, and reports
counts rather than local directory names. `scripts/record_matchpulse_demo.py`
is included only because the approved hosted recorder imports it. The
`.gitignore` entry is limited to approved generated/local asset rules; the
unrelated `.fake` rule is a separate excluded hunk.

**Rights gate:** The notices explicitly say voice-asset and promotional-use
rights remain unresolved. These disclosures do not authorize distribution or
public use of voice assets. Never include model/voice binaries or generated
audio/video in this commit.

No C allowlist is proposed now. Any possible trace-related commit remains
deferred until a trace is identified and independently qualifies.

## Complete path classification

Every modified tracked path and every untracked file observed in the inventory
is listed below. “A” and “B” refer only to the proposed allowlists above; all
other paths are excluded from both.

### Modified tracked paths (44)

| Path | Classification |
|---|---|
| `.gitignore` | B, approved ignore-rule hunk only: generated media, local audit artifacts, local TTS assets, and local Azure state. Exclude the separate unrelated `.fake` line and do not alter it. |
| `README.md` | A |
| `docs/ARCHITECTURE.md` | A, after verifying claims and placeholder-safety. |
| `docs/AZURE_CHALLENGE_DEPLOYMENT_PLAN.md` | Exclude: local Azure plan/operational record. Do not publish its environment-specific details as-is. |
| `docs/AZURE_COST_PLAN.md` | A |
| `docs/AZURE_DEPLOYMENT.md` | A |
| `docs/AZURE_MODEL_PLAN.md` | A, only after the public-identifier scrub described above. |
| `docs/AZURE_PROVIDER_AND_RBAC_PLAN.md` | A, only after the public-identifier scrub described above. |
| `docs/CHALLENGE_ALIGNMENT.md` | A |
| `infra/main.bicep` | A |
| `infra/main.parameters.example.json` | A |
| `infra/validate_template.py` | A |
| `pyproject.toml` | B: Pillow supports the included recording helpers; no new runtime service dependency. |
| `scripts/hardened_smoke_test.py` | A |
| `scripts/preflight.py` | A; heuristic secret-pattern scan flagged code-shaped connection-string/credential patterns. Review without exposing values before any public commit. |
| `scripts/smoke_test.py` | A |
| `scripts/validate_attestation_verification.py` | A |
| `scripts/validate_solution.py` | A |
| `src/matchpulse/agents.py` | Exclude: runtime/application change outside this two-commit scope. |
| `src/matchpulse/demo.py` | Exclude: runtime/application change outside this two-commit scope. |
| `src/matchpulse/foundry.py` | Exclude: runtime/application change outside this two-commit scope. |
| `src/matchpulse/localization.py` | Exclude: runtime/application change outside this two-commit scope. |
| `src/matchpulse/models.py` | Exclude: runtime/application change outside this two-commit scope. |
| `src/matchpulse/service.py` | Exclude: runtime/application change outside this two-commit scope. |
| `src/matchpulse/state.py` | Exclude: runtime/application change outside this two-commit scope. |
| `src/matchpulse/synthetic.py` | Exclude: runtime/application change outside this two-commit scope. |
| `src/matchpulse/telemetry.py` | Exclude: runtime/application change outside this two-commit scope. |
| `submission/PROJECT_DESCRIPTION.md` | A |
| `submission/REGISTRATION_AND_SUBMISSION_CHECKLIST.md` | Exclude: historical local audit checklist; preserve and do not publish its worktree edit. |
| `submission/TESTING_INSTRUCTIONS.md` | A |
| `tests/test_api.py` | Exclude: paired with out-of-scope application/runtime changes. |
| `tests/test_attestation_validation.py` | A: the local username was removed and the optional real-attestation path is environment-configured. |
| `tests/test_demo_runs.py` | Exclude: paired with out-of-scope application/runtime changes. |
| `tests/test_foundry_guard.py` | Exclude: paired with out-of-scope application/runtime changes. |
| `tests/test_foundry_provider.py` | Exclude: paired with out-of-scope application/runtime changes. |
| `tests/test_hardened_smoke.py` | A |
| `tests/test_localization.py` | Exclude: paired with out-of-scope application/runtime changes. |
| `tests/test_personalization.py` | Exclude: paired with out-of-scope application/runtime changes. |
| `tests/test_pipeline.py` | Exclude: paired with out-of-scope application/runtime changes. |
| `tests/test_solution_layout.py` | A |
| `tests/test_telemetry.py` | Exclude: paired with out-of-scope application/runtime changes. |
| `tests/test_variants.py` | Exclude: paired with out-of-scope application/runtime changes. |
| `tests/test_workflow_policy.py` | Exclude: workflow-policy changes are outside A/B; review separately. |
| `tests/test_workflow_security.py` | Exclude: workflow-security changes are outside A/B; review separately. |

### Visible untracked files (33 after adding the three authorization packets)

| Path | Classification |
|---|---|
| `.foundry/.deployment.json` | Exclude: local Foundry configuration. |
| `.kilo/kilo.jsonc` | Exclude: local tool configuration. |
| `THIRD_PARTY_NOTICES.md` | B |
| `docs/LOCAL_TTS_PROVENANCE.md` | B |
| `docs/REPRODUCIBILITY.md` | A: includes the clean-clone narration limitation. |
| `scripts/archive_media_reorganize.py` | Exclude: temporary/archive media utility. |
| `scripts/matchpulse_conversational_tts.py` | B |
| `scripts/matchpulse_kokoro_v2.py` | B |
| `scripts/matchpulse_local_tts.py` | B |
| `scripts/record_matchpulse_demo.py` | B: required support dependency imported by the approved hosted recorder; workspace sibling names are explicitly allowlisted and never emitted. |
| `scripts/record_matchpulse_hosted_submission.py` | B: requires an explicit allowed ACA hostname; no private hostname is embedded. |
| `srv.pid` | Exclude: local process artifact. |
| `submission/AUTHORIZATION_PACKETS.md` | Exclude: local authorization package. |
| `submission/COMMIT_PLAN.md` | Exclude: planning deliverable. |
| `submission/JUDGING_RUBRIC_ALIGNMENT.md` | A: public-facing rubric alignment with evidence and limitations. |
| `submission/AUTHORIZATION/PACKET_COMMIT_PUSH.md` | Exclude: local, authorization-gated action packet. |
| `submission/AUTHORIZATION/PACKET_VIDEO_UPLOAD.md` | Exclude: local, rights- and authorization-gated action packet. |
| `submission/AUTHORIZATION/PACKET_CHALLENGE_SUBMISSION.md` | Exclude: local portal-action packet; contains no entrant declarations or answers. |
| `submission/AUTHORIZATION_PACKET_COMMIT_PUSH.md` | Exclude: local authorization summary. |
| `submission/AUTHORIZATION_PACKET_VIDEO_UPLOAD.md` | Exclude: local authorization summary. |
| `submission/AUTHORIZATION_PACKET_CHALLENGE_SUBMISSION.md` | Exclude: local portal-action summary. |
| `submission/VIDEO_UPLOAD_METADATA.md` | Exclude: local upload-preparation package. |
| `submission/archive/ARCHIVE_INDEX.md` | Exclude: local archive/review record. |
| `submission/archive/inventory_report.json` | Exclude: media inventory/audit manifest. |
| `submission/archive/manifests/MATCHPULSE_VIDEO_MANIFEST.json` | Exclude: local video manifest. |
| `submission/archive/scripts/MATCHPULSE_CAPTIONS_SUBMISSION.srt` | Exclude: local media support. |
| `submission/archive/scripts/MATCHPULSE_CAPTIONS_TECHNICAL.srt` | Exclude: local media support. |
| `submission/archive/scripts/MATCHPULSE_NARRATION_CONVERSATIONAL.json` | Exclude: local narration support. |
| `submission/final-support/MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt` | Exclude: local final-media support. |
| `submission/final-support/MATCHPULSE_NARRATION_CONVERSATIONAL_V2.json` | Exclude: local final-media support; clean clones need it supplied separately. |
| `submission/final-support/MATCHPULSE_PLAYWRIGHT_RECORDING_PLAN.md` | Exclude: local recording review package. |
| `submission/final-support/MATCHPULSE_SHOT_LISTS.md` | Exclude: local recording review package. |
| `submission/final-support/MATCHPULSE_VIDEO_SCRIPTS.md` | Exclude: local recording review package. |
| `tests/test_conversational_tts.py` | B |
| `tests/test_kokoro_v2_narration.py` | B |
| `tests/test_local_tts.py` | B |

Ignored local artifacts are not visible untracked paths and are not part of
either allowlist. These include `submission/FINAL_USER_INPUT_CHECKLIST.md`
(excluded by local `.git/info/exclude`); the approved MP4; historical and
candidate MP4/WAV media; local approval, verification, readiness, and
narration-manifest files; and any model/voice weights or other binaries.
The preserved hosted visual source remains local and is required for
exact-video reproduction. No model/voice binaries appear in the visible
status inventory. The tracked `.gitignore` change is excluded because it
mixes intended generated-media rules with the unrelated `.fake` line. Keep the
skip-worktree portal worksheet, local Azure plan, `.azure` and other local
tool configuration, generated media, weights, audit artifacts, packet
documents, and unrelated runtime/workflow edits outside both commits. Root
audit/checksum files, if present but unchanged, are also out of scope; do not
add them.

### Locally hidden tracked edit (1)

| Path | Classification |
|---|---|
| `submission/PORTAL_SUBMISSION_WORKSHEET.md` | Modified locally but marked skip-worktree; exclude and preserve. Do not clear the index flag or stage it. |

## Recorded validation evidence and proposed messages

The worktree totals above include excluded runtime changes; no staged diff or
commit statistics exist. Final read-only verification on 2026-10-26 passed:

- Full pytest: 189 passed, 1 optional real-attestation test skipped. Ruff,
  `git diff --check`, solution validation, and JSON parsing passed.
- Current Bicep compiled successfully; all 34 infrastructure guardrails
  passed against the freshly compiled template. The older `infra/main.json`
  is not a proposed commit input.
- Trivy scanned the exact 34-file A/B allowlist after refreshing its copy;
  no vulnerability, misconfiguration, license, or secret findings were
  returned. The immutable deployed-image scan found no HIGH or CRITICAL
  vulnerabilities. These scans do not establish a hash-pinned dependency
  environment.
- A redacted identifier/privacy-pattern pass found only scanner-rule source,
  negative-test strings, and GUID-shaped solution-layout fixtures; all matched
  text was suppressed. It found no actual subscription/tenant identifiers,
  local paths or usernames, email addresses, tokens, connection secrets, or
  private endpoints in the proposed files.
- Independent security review identified absolute local output paths in the
  V2 narration CLI. The CLI now emits basenames only, collision errors omit
  the output directory, and the focused regression test verifies this. No
  unresolved finding from that review is known.
- A fresh ARM GET confirms the Container App is running the exact immutable
  image digest, has `configuration.ingress: null`, no runtime configuration,
  synthetic-only mode, 0–1 replica limits, and liveness/readiness/startup
  probes. The model deployment list and direct resource-group role-assignment
  list are empty.
- **`AZURE_COUNT_RECONCILED=YES`** — the fresh resource-group inventory
  returned seven resources: five MatchPulse application/monitoring resources
  and two separately user-authorized Foundry development resources. The user
  confirmed the account and project were intentionally created via the Visual
  Studio Code Foundry extension toolkit. Fresh Activity Log caller
  fingerprints for resource creation, nine connection writes, and the 32
  successful key-list calls match the ARM creator field, consistent with
  that confirmation. Caller object ID, application ID, user-agent, and
  interactive/automated classification were not returned; the attribution
  limitation and sanitized event-level record are in
  `submission\AZURE_AI_SECURITY_REVIEW.md`. No key or connection credential
  values were retrieved. These Foundry resources are not in MatchPulse Bicep
  and are not dependencies of the submitted runtime. Current review
  conclusion: `KEY_LIST_ACTIVITY_ATTRIBUTED_EXPECTED_TOOLING`; keep both
  resources unchanged until the separate post-submission review.
- Fresh cost readback reported $0 USD month-to-date for the resource group;
  the resource-group query returned only the workspace at $0, so it does not
  itemize separate account/project charges or guarantee future usage is free;
  resource-ID-filtered month-to-date queries for the account and project
  returned no rows.
  The $25 monthly resource-group budget is current, with $0 actual and $0
  forecast; actual alerts are 50%, 80%, and 100%, and forecast alerts are
  90% and 100%. The separate $50 annual subscription budget has $0 actual
  and a 100% actual alert; no annual forecast was returned. The $15
  operational stop threshold is not an Azure-enforced limit.
- The Log Analytics workspace is at 30-day default retention with a 0.023
  GB/day ingestion quota. The linked workspace-based Application Insights
  resource reports 90 days; an ARM table-list read confirmed the core
  Application Insights tables (`AppTraces`, `AppRequests`, `AppDependencies`,
  `AppEvents`, `AppExceptions`, `AppMetrics`, `AppPageViews`,
  `AppBrowserTimings`, `AppAvailabilityResults`, `AppPerformanceCounters`,
  and `AppSystemEvents`) each currently report 90-day retention and
  `totalRetentionInDays=90`. Therefore the verified App Insights telemetry
  table retention is 90 days; the workspace's 30-day default remains the
  workspace-level setting for tables that use it. Microsoft Learn confirms
  workspace-based telemetry is stored/billed through Log Analytics and
  retention is configurable at workspace/table level. The Smart Detection
  action group is enabled and was explicitly written on 2026-10-24, not
  listed in Bicep.
  A separate failure-anomaly alert-rule creation attempt failed because
  `Microsoft.AlertsManagement` was not registered; no provider registration
  or alert change was attempted.
- Fresh ARM state confirms the Container App is `Succeeded`/running with the
  expected immutable digest, `configuration.ingress: null`, empty active
  revision FQDN, no Foundry runtime configuration, synthetic-only mode,
  SystemAssigned identity, and 0–1 replica limits. Its only secret reference
  is the expected Application Insights connection string; no value was
  retrieved. Direct resource-group RBAC assignments remain zero.
- Video SHA-256, sole top-level MP4 status, FFprobe metadata, full decode,
  video-stream MD5, loudness, true peak, and Git-ignore state matched the
  approval record. Its SHA-256 was unchanged before and after read-only
  validation.
- A fresh clean clone at the recorded source revision with the exact 34-file
  A/B overlay installed `.[dev]`, passed pytest (189 passed, four skipped:
  optional attestation plus three excluded-input narration checks), Ruff,
  preflight, solution validation, and the seeded synthetic scenario/replay.
  Uvicorn then started on loopback and `scripts/smoke_test.py` passed all 11
  API/WebSocket checks. The first rehearsal was placed under the operating
  system temp directory, which caused a path-guard fixture to treat the
  repository as an approved temp output; the corrected clone outside that
  directory passed without changing application code. Level 2 TTS asset
  acquisition/build and repeatable narration generation were not proven
  because model/voice assets remain external and are not committed. Exact
  final MP4 reproduction also depends on the excluded hosted visual source.
  No claim of clean-clone narration or byte-for-byte video reproducibility is
  made.
- The audit file was preserved; this continuation uses fresh Azure and local
  validation results and does not copy historical audit content. The
  repository-wide preflight was not rerun against the original worktree
  because its rule scans ignored historical evidence; the clean-clone
  preflight passed.
- No files were staged, committed, or pushed. No video was uploaded, no
  challenge was submitted, and Azure was not mutated.

Current publication blockers are unresolved `bf_emma` generated-audio
rights, confirmation of the intended YouTube channel, and separate commit/
push, video-upload, and final challenge-submission authorizations. The live
portal host requirement is still a prerequisite to the upload authorization,
not evidence that Unlisted is accepted. Portal-only entrant values remain in
the locally ignored checklist; no live portal field or legal declaration was
entered or submitted. The Foundry resources are authorized and are not a
submission blocker; their separate cost/security review is post-submission.

## Post-submission Foundry review — not authorized for execution

Recommendation:
`AZURE_REMEDIATION_RECOMMENDATION=RETAIN_PENDING_POST_SUBMISSION_REVIEW`.
After challenge submission, separately review cost and security and decide
whether to `RETAIN_AND_SECURE`, `QUARANTINE_THEN_DELETE`, or
`IMMEDIATE_DELETE`. Assess public network access, local authentication,
unused remote-tool connections, dedicated budget controls, and dependency/
data retention. Prefer separate resource-group ownership or a separate Bicep
module for future Foundry development. No access change, credential
operation, deployment, agent creation, or deletion is authorized during
submission finalization.

**Commit A title:** `Finalize Azure recovery configuration and challenge documentation`

**Commit A body:** Add a controlled Bicep path for reusing existing monitoring
and Container Apps foundations, update the example parameters and deployment
validation, and align challenge-facing documentation with the verified
deployment state and its limits. These source and documentation changes are
not deployed in the immutable challenge image. No Azure mutation,
redeployment, image rebuild, or media inclusion.

**Commit B title:** `Add reproducible local Kokoro narration tooling`

**Commit B body:** Add local Kokoro narration utilities and focused tests,
with provenance and third-party notices that explicitly retain unresolved
voice-asset and promotional-use rights. Include only the approved ignore-rule
hunk and recorder support dependency. No model/voice binaries or generated
audio/video included; this commit does not grant rights to publish a recording.

**Commit A risks and rollback:** Public deployment claims must remain tied to
the immutable image. The separately authorized Foundry account/project and
their registered connections are not covered by this Bicep and are not
required by the deployed app; their separate cost/security review is
post-submission. A Bicep recovery-path regression could affect
existing-foundation deployments. Use a reviewed revert commit/PR for any
later authorized rollback; do not reset shared history or force-push.

**Commit B risks and rollback:** Voice rights remain unresolved, so no
recording is cleared for public distribution; optional local narration assets
remain external and uncommitted. The recorder allowlist and privacy behavior
must remain intact. If a later authorized change needs rollback, use a
reviewed revert commit/PR; do not reset shared history or force-push.

**Per-commit verification:** Commit A is covered by the full 189-test suite,
Ruff, whitespace check, JSON validation, and freshly compiled 34-guardrail
infrastructure validation. Commit B is covered by the same suite, including
the narration privacy regression; both exact allowlists were included in the
fresh Trivy filesystem scan. Re-run these checks against the final staged
diff before any separately authorized commit.

**Authorization state:** Neither proposed commit is authorized or ready while
the user-required voice-rights gate remains `RIGHTS_UNRESOLVED`. These
allowlists are preparation only.

## Future branch, review, and rollback notes

Do not stage, commit, push, open a PR, upload media, submit the challenge, or
change Azure under this plan. Before any later commit, confirm the published
image/source revision relationship; move from detached HEAD to a separately
authorized topic branch based on a freshly fetched `origin/main`; verify the
exact allowlist; sanitize public docs; run focused tests and fresh secret
scanning; and inspect the staged diff. Since no branch protection was
detected in the earlier recorded check, recheck it and require explicit human
review rather than relying on GitHub enforcement.

If a future pre-commit review fails, stop and unstage only the reviewed paths
with `git restore --staged -- <paths>`; do not discard worktree changes. If an
authorized later commit needs rollback, use a new reviewed revert commit/PR;
do not reset shared history or force-push. A/B should remain separate so
narration tooling can be reverted independently. No rollback action is
currently needed because this task only adds this plan.

## Final continuation: Azure inventory and publication gates — 2026-10-26

### Fresh seven-resource inventory

The resource-group list and direct ARM reads returned seven resources. These
resource identifiers are retained in this local preparation material and
excluded from both proposed commits. The first five are MatchPulse
application/monitoring resources; the final two are separately user-
authorized Foundry development resources. The project is a child of the AI
Services account, not a Container Apps dependency. Their creation was
confirmed as intentional by the user.

1. **`matchpulse-logs-lhm35ehteauty`**
   - Type: `Microsoft.OperationalInsights/workspaces`; location: `eastus2`;
     state: `Succeeded`.
   - ID:
     `/subscriptions/13b00900-43c4-4cdc-aba3-4a8bb13e61cc/resourceGroups/rg-matchpulse-insidethegame-dev/providers/Microsoft.OperationalInsights/workspaces/matchpulse-logs-lhm35ehteauty`
   - Created `2026-10-24T19:05:45.5814754Z`; changed
     `2026-10-24T19:05:57.7557742Z`. Parent: resource group.
   - Expected: yes. Azure-auto-created: no; part of the Bicep deployment.
     Billable: yes, ingestion/storage based. Bicep-referenced: yes.
     Required: application logs/monitoring. Disposition: retain.
2. **`matchpulse-appi-lhm35ehteauty`**
   - Type: `Microsoft.Insights/components`; location: `eastus2`;
     state: `Succeeded`.
   - ID:
     `/subscriptions/13b00900-43c4-4cdc-aba3-4a8bb13e61cc/resourceGroups/rg-matchpulse-insidethegame-dev/providers/microsoft.insights/components/matchpulse-appi-lhm35ehteauty`
   - Created `2026-10-24T19:06:08.4842212Z`; changed timestamp was not
     exposed by the direct GET. Parent: resource group; linked to the workspace.
   - Expected: yes. Azure-auto-created: no; part of the Bicep deployment.
     Billable: telemetry is charged through Log Analytics usage.
     Bicep-referenced: yes. Required: monitoring, not core request processing.
     Disposition: retain.
3. **`matchpulse-env-lhm35ehteauty`**
   - Type: `Microsoft.App/managedEnvironments`; location: `East US 2`;
     state: `Succeeded`.
   - ID:
     `/subscriptions/13b00900-43c4-4cdc-aba3-4a8bb13e61cc/resourceGroups/rg-matchpulse-insidethegame-dev/providers/Microsoft.App/managedEnvironments/matchpulse-env-lhm35ehteauty`
   - Created and changed `2026-10-24T19:06:08.0181742Z`. Parent: resource
     group; dependency of the Container App.
   - Expected: yes. Azure-auto-created: no; part of the Bicep deployment.
     Billable: no separate environment charge was established; app workload
     and monitoring may incur charges. Bicep-referenced: yes. Required: yes,
     to host the app. Disposition: retain.
4. **`Application Insights Smart Detection`**
   - Type: `microsoft.insights/actiongroups`; location: `Global`;
     current state: `enabled=true` (the GET did not return a provisioning
     state).
   - ID:
     `/subscriptions/13b00900-43c4-4cdc-aba3-4a8bb13e61cc/resourceGroups/rg-matchpulse-insidethegame-dev/providers/microsoft.insights/actiongroups/Application Insights Smart Detection`
   - Activity Log records a successful `Created` write at
     `2026-10-24T19:16:09.9772495Z` and a successful later write at
     `2026-10-24T19:26:10.153842Z`. Parent: resource group.
   - Expected: yes, as a Smart Detection monitoring resource. Whether Azure
     created it automatically is not proven: the Activity Log shows an
     explicit create/update operation, but its caller was not resolved.
     Billable: no separate charge was identified or itemized. Bicep-referenced:
     no. Required: not by MatchPulse; required only for its Smart Detection
     alert path. Disposition: retain unchanged; do not treat it as an
     application dependency or delete it without separate authorization.
5. **`matchpulse-api-lhm35ehteauty`**
   - Type: `Microsoft.App/containerApps`; location: `East US 2`;
     state: `Succeeded` / `Running`.
   - ID:
     `/subscriptions/13b00900-43c4-4cdc-aba3-4a8bb13e61cc/resourceGroups/rg-matchpulse-insidethegame-dev/providers/Microsoft.App/containerApps/matchpulse-api-lhm35ehteauty`
   - Created `2026-10-25T03:20:27.9023606`; changed
     `2026-10-25T18:20:11.0659713`. Parent: resource group; uses the managed
     environment above.
   - Expected: yes. Azure-auto-created: no; part of the deployment.
     Billable: yes; the latest replica metric had one replica in every
     one-minute bucket from 21:04–21:18 UTC on 2026-10-26. Bicep-referenced:
     yes. Required: yes. Disposition: retain unchanged. Current ingress is
     null, active revision FQDN is empty, the immutable image is unchanged,
     identity is SystemAssigned, synthetic-only is true, and Foundry runtime
     configuration is absent.
6. **`matchpulse-live-public-resource`**
   - Type: `Microsoft.CognitiveServices/accounts` (`AIServices`, SKU `S0`);
     location: `eastus2`; state: `Succeeded`.
   - ID:
     `/subscriptions/13b00900-43c4-4cdc-aba3-4a8bb13e61cc/resourceGroups/rg-matchpulse-insidethegame-dev/providers/Microsoft.CognitiveServices/accounts/matchpulse-live-public-resource`
   - Created and last modified `2026-10-26T14:28:12Z`. Parent: resource
     group.
   - Expected: yes, as a separately authorized Foundry development resource.
     Azure-auto-created: no; ARM system data and Activity Log record explicit
     user creation after deployment and after ingress restriction.
     Billable: potentially, if AI services are used; the resource-filtered
     month-to-date cost query returned no rows, which is not proof of future
     zero cost. Bicep-referenced: no. Required: no; no model deployment was
     found.      Disposition: retain unchanged pending post-submission review. Current
     public network access is enabled, local authentication
     is enabled, and the network ACL default is `Allow`. The Activity Log
     included 32 successful `List Keys` operations and their corresponding
     starts; no key values were retrieved.
7. **`matchpulse-live-public-resource/matchpulse-live-public`**
   - Type: `Microsoft.CognitiveServices/accounts/projects`;
     location: `eastus2`; state: `Succeeded`.
   - ID:
     `/subscriptions/13b00900-43c4-4cdc-aba3-4a8bb13e61cc/resourceGroups/rg-matchpulse-insidethegame-dev/providers/Microsoft.CognitiveServices/accounts/matchpulse-live-public-resource/projects/matchpulse-live-public`
   - Created and last modified `2026-10-26T14:28:19.7875634Z`. Parent:
     the separately authorized AI Services account above.
   - Expected: yes, as a separately authorized Foundry development project.
     Azure-auto-created: no; ARM system data and Activity Log record explicit
     user creation. Billable: no separate project meter
     was observed; usage may bill to the parent account. Bicep-referenced:
     no. Required: no. Disposition: retain unchanged pending post-submission
     review. Project metadata lists nine remote-tool
     connections (one OAuth2, eight with unknown authentication metadata);
     no connection secret was read.

The two separately authorized Foundry development resources were absent from
the earlier five-resource application/monitoring inventory because that
inventory preceded their creation. The user confirms they were intentionally
created through the VS Code Foundry extension toolkit. A fresh resource-group
list and Resource Graph query independently returned seven. Their separate
account/project cost queries returned no rows; the resource-group cost query
returned only the workspace at $0 USD. This does not prove that the
account/project are free or harmless. Final conclusion:
`AZURE_COUNT_RECONCILED=YES`. Activity Log attribution conclusion:
`KEY_LIST_ACTIVITY_ATTRIBUTED_EXPECTED_TOOLING`; caller object ID,
application ID, user-agent, and explicit interactive/automated classification
were not returned, as detailed in
`submission\AZURE_AI_SECURITY_REVIEW.md`. No Azure resource was modified or
deleted. The Hosted Agents Preview 403 remains
`NONBLOCKING_OPTIONAL_INTEGRATION_WARNING`; no RBAC was assigned.

### Post-submission review — not authorized for execution

The user confirms the Foundry account and project were intentionally created
through the Visual Studio Code extension toolkit. Activity Log caller
fingerprint and timing are consistent with that confirmation, although
caller object ID, application ID, user-agent, and interactive/automated
classification were not returned. Attribute the 32 successful `List Keys`
operations to expected tooling activity; do not treat them as suspected
unauthorized access. No key values were retrieved.

After challenge submission, conduct a separate cost/security review. Consider
retaining and securing the resources, restricting public network access and
local authentication, removing unused remote-tool connections, adding
explicit budget controls, and placing the resources under separate Bicep
ownership or in a separate resource group. Delete the account/project only
if that review establishes they are no longer needed and a separate
authorization is obtained. Do not change or delete resources during
submission finalization.

### Final cost, verification, and allowlist state

- Read-only budget evidence: `$25` monthly at resource-group scope, `$0`
  actual and `$0` forecast, actual alert thresholds 50/80/100%, forecast
  thresholds 90/100%; `$50` annual at subscription scope, `$0` actual and no
  forecast returned. Exact budget names were not returned by the available
  authorized reads; Azure Resource Graph returned no budget rows and the
  local Azure CLI list command failed while loading an extension because of
  local file permission. No budget name is guessed. The `$15` operational
  threshold is not enforced by Azure. Log Analytics quota/retention are
  0.023 GB/day and 30 days; core Application Insights tables are 90 days.
- Current replica count: one, based on the latest 15 one-minute `Replicas`
  metric buckets. Maximum configured replicas: one.
- All 22 Commit A and 12 Commit B paths exist; the exact 34-file scan copy
  matches those lists. The local ignored checklist and skip-worktree portal
  worksheet, all audit material, `.azure` state, model/voice weights, media,
  and local paths are excluded. The `.fake` `.gitignore` line is a separate
  excluded hunk. The exact value-only privacy/secret scan passed. Trivy's
  exact allowlist and immutable-image findings lists are empty.
- Fresh Bicep build succeeded with no diagnostics; all 34 infrastructure
  guardrails passed. Six JSON files parsed. Solution validation, pytest
  (189 passed, one optional real-attestation test skipped), Ruff, and
  `git diff --check` passed. The independent clean clone passed Level 1
  application reproduction; Level 2 TTS assets/build and Level 3 exact video
  reproduction remain unproven as documented in `docs/REPRODUCIBILITY.md`.
- Approved video remains frozen at SHA-256
  `f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`;
  115 seconds, H.264 1920x1080/30 fps, AAC 48 kHz stereo, full decode,
  stream MD5 `c85bef1de55944edebd4f4d003c70b59`, loudness -16.02 LUFS, and
  true peak -1.95 dBTP. It is the only top-level submission MP4 and remains
  Git-ignored.
- All supplied entrant field/value pairs are present in the local ignored
  `submission/FINAL_USER_INPUT_CHECKLIST.md`; no legal name, contact email,
  or country value is copied into this plan or either proposed commit.
  YouTube Unlisted remains an entrant choice only:
  `VIDEO_URL_REQUIREMENT_UNRESOLVED`.
- `COMMIT_A_ALLOWLIST_READY=YES` and `COMMIT_B_ALLOWLIST_READY=YES` mean the
  exact path sets are present and scan-safe, not that commit/push is
  authorized. Rights remain `RIGHTS_UNRESOLVED`, so
  `THIRD_PARTY_RIGHTS_DECLARATION=PENDING_RIGHTS_REMEDIATION`. No file was
  staged, committed, or pushed; no video was uploaded; no challenge was
  submitted; Azure was not mutated.

**Current disposition: `MATCHPULSE READY — RIGHTS REMEDIATION REQUIRED`.**
Azure inventory is reconciled and the Foundry account/project are
user-authorized, separate development resources.
`MATCHPULSE_RUNTIME_DEPENDENCY=NO`.
`AZURE_REMEDIATION_RECOMMENDATION=RETAIN_PENDING_POST_SUBMISSION_REVIEW`.
Keep them unchanged until the post-submission cost/security review.
Publication remains blocked by
`RIGHTS_UNRESOLVED`, the unconfirmed YouTube channel/host requirements, and
the separate commit/push, upload, and final-submission authorizations.
`submission\AZURE_AI_SECURITY_REVIEW.md` and
`submission\VOICE_RIGHTS_DECISION.md` contain the bounded evidence and
remaining decisions.
