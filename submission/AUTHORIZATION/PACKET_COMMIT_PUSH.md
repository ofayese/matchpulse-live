# Packet: repository commit and push

## 2026-10-27 supersession — Lily promotion (read first)

The human-approved ElevenLabs Lily V1 video is the sole active submission video
(`f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`,
`VOICE_RIGHTS_CONCLUSION=ELEVENLABS_PAID_COMMERCIAL_LICENSE`,
`THIRD_PARTY_RIGHTS_DECLARATION=YES`). The Kokoro `RIGHTS_UNRESOLVED`
statements below are historical: they applied to the superseded Kokoro
candidate and no longer block Commit A/B/C for rights reasons. No commit or
push is authorized yet; no file is staged.

**Branch:** the checkout is a detached HEAD at `origin/main` (`335781f`). The commands below create a topic branch; use
`submission/lily-final` unless told otherwise. Pushing to `main` is not requested. Re-verify remote branch rules at authorization time.

**Commit B update:** the docs now also contain the ElevenLabs final-video notice; `THIRD_PARTY_NOTICES.md` and `docs\LOCAL_TTS_PROVENANCE.md` already
carry it. Commit B title is `Add local narration tooling, third-party notices and TTS provenance`. In Commit B, stage `pyproject.toml` **not at all** (its only needed hunk moves to Commit C).

### Commit C — ElevenLabs final-narration tooling

**Commit title:** `Add ElevenLabs final narration tooling and provenance`

0. `.env.example` (placeholder `ELEVENLABS_API_KEY=<SET_LOCALLY>` only)
1. `docs\ELEVENLABS_NARRATION.md`
2. `scripts\matchpulse_elevenlabs_tts.py`
3. `scripts\matchpulse_elevenlabs_render.py`
4. `tests\test_elevenlabs_tts.py`
5. `tests\test_elevenlabs_render.py`
6. `pyproject.toml` — only the `narration = [elevenlabs, python-dotenv]` extra hunk (`git add -p`); the Pillow and pytest-version dev-dependency hunks are unrelated and excluded unless the maintainer separately reviews them.

```powershell
git add -- docs\ELEVENLABS_NARRATION.md scripts\matchpulse_elevenlabs_tts.py scripts\matchpulse_elevenlabs_render.py tests\test_elevenlabs_tts.py tests\test_elevenlabs_render.py
git add -p -- pyproject.toml   # accept only the narration extra
git diff --cached --check
git diff --cached --name-only
git commit -m "Add ElevenLabs final narration tooling and provenance" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

Still excluded from every commit: all generated media (the Lily and archived Kokoro MP4/WAV), `submission\FINAL_VIDEO_*`, `SUBMISSION_READINESS.md`,
the Lily manifest, ignored audit logs, `.env`, `.foundry\`, `.kilo\`, `srv.pid`, `scripts\archive_media_reorganize.py`, the portal worksheet, the
authorization packets, `submission\COMMIT_PLAN.md`, the unrelated `.fake` line, and `src\matchpulse\` plus paired tests (not part of the deployed-image-equivalent
set; see exclusions below). Verify that the deployed-image claims in Commit A docs describe the deployed image (`335781f`) and not uncommitted source changes.

The original 2026-10-26 packet follows.

---

**Status: preparation only — no staging, commit, push, or pull request is
authorized.** The task requests preparation of this packet; publication
gates are not satisfied and exact branch/commit targets are not yet known.
No repository or Azure action has been authorized for execution now.
The Commit A and Commit B lists below are separate, exact candidate
allowlists; all other paths are excluded. The canonical full worktree
classification is in `submission\COMMIT_PLAN.md`.

## Current facts and release position

- Repository: `https://github.com/ofayese/matchpulse-live`
- Observed `HEAD`: `335781f928011f99a644083d80bfe4dfc480b1a6`, detached at
  `origin/main`; re-fetch and verify before any future branch operation.
- Candidate image:
  `ghcr.io/ofayese/matchpulse-live@sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226`,
  built from source revision `335781f928011f99a644083d80bfe4dfc480b1a6`.
- The current worktree contains later uncommitted changes. Those changes are
  **not** in the immutable published image and must not be described as
  deployed or validated by it.
- Foundry runtime is disabled in the submitted MatchPulse deployment, and
  the demonstrated workflow makes zero model calls. The approved video does
  not demonstrate Foundry usage. Fresh read-only Azure state confirms the
  expected immutable image digest, no active ingress configuration or active
  revision FQDN, no Foundry runtime setting, and no model deployment.
  Hosted-agent inventory is unavailable after the optional Preview 403; this
  remains a nonblocking optional-integration warning.
- The fresh resource-group inventory contains seven resources: five
  MatchPulse application/monitoring resources plus two separately authorized
  Foundry development resources. The user confirmed both were intentionally
  created through the Visual Studio Code Foundry extension toolkit. They are
  not deployed by MatchPulse Bicep and are not dependencies of the submitted
  MatchPulse runtime. A 72-hour Activity Log read showed 32 successful
  `List Keys` operations and corresponding starts, plus writes for nine
  project connections. All share the same sanitized caller fingerprint as
  the account/project creator and connection writes, consistent with the
  user-confirmed extension activity. Caller object ID, application ID, and
  user-agent were not returned; see
  `submission\AZURE_AI_SECURITY_REVIEW.md` for the event-by-event sanitized
  correlations and residual attribution gap. No key or connection
  credential value was retrieved. Current conclusion:
  `AZURE_COUNT_RECONCILED=YES` and
  `KEY_LIST_ACTIVITY_CONCLUSION=KEY_LIST_ACTIVITY_ATTRIBUTED_EXPECTED_TOOLING`.
  Keep the resources unchanged through submission; current recommendation:
  `RETAIN_PENDING_POST_SUBMISSION_REVIEW`.
- Current month-to-date resource-group spend is $0 USD. The `$25` monthly
  resource-group budget has `$0` actual and `$0` forecast, actual alerts at
  50/80/100%, and forecast alerts at 90/100%. The separate `$50` annual
  subscription budget has `$0` actual and a 100% actual alert; no annual
  forecast was returned. The `$15` operational stop threshold is not an
  Azure-enforced limit. The cost query returned only the workspace at $0, so
  it does not itemize account/project usage or prove future use is free.
- Log Analytics reports 30-day default retention and a 0.023 GB/day quota.
  Linked workspace-based Application Insights reports 90 days, and direct
  ARM table-list results show its core telemetry tables at 90-day retention.
  Those tables are therefore currently retained 90 days; the workspace
  default remains 30 days for tables using it. Microsoft Learn documents
  workspace-based storage/billing and workspace/table retention
  ([Application Insights](https://learn.microsoft.com/en-us/azure/azure-monitor/app/create-workspace-resource);
  [Log Analytics](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/data-retention-configure)).
  The enabled Smart Detection action group was explicitly written on
  2026-10-24 and is not in Bicep. A failure-anomaly alert-rule creation
  attempt failed because `Microsoft.AlertsManagement` was not registered.
- The Container App is `Succeeded`/running, synthetic-only, uses a
  SystemAssigned identity, and is limited to 0–1 replicas. Its only app secret
  reference is the expected Application Insights connection string; no value
  was retrieved. Direct resource-group role assignments remain zero.
- Core positioning: a synthetic-data prototype for evidence-linked football
  storytelling, using a deterministic processing pipeline—not an autonomous
  or multi-agent system—and no live external match feed.
- `bf_emma` voice-asset/promotional-use rights remain
  **`RIGHTS_UNRESOLVED`**. Do not change that gate to cleared. No authorization
  or independent rights decision is supplied here.

## Exact candidate commit allowlists

These lists are mutually exclusive. Stage only the paths in the specific
commit being separately authorized; never use `git add -A`, `git add .`, or a
whole-directory add.

### Commit A — Azure recovery and challenge-facing documentation

**Commit title:** `Finalize Azure recovery configuration and challenge documentation`

1. `README.md`
2. `docs\ARCHITECTURE.md`
3. `docs\AZURE_COST_PLAN.md`
4. `docs\AZURE_DEPLOYMENT.md`
5. `docs\AZURE_MODEL_PLAN.md`
6. `docs\AZURE_PROVIDER_AND_RBAC_PLAN.md`
7. `docs\CHALLENGE_ALIGNMENT.md`
8. `docs\REPRODUCIBILITY.md`
9. `infra\main.bicep`
10. `infra\main.parameters.example.json`
11. `infra\validate_template.py`
12. `scripts\hardened_smoke_test.py`
13. `scripts\preflight.py`
14. `scripts\smoke_test.py`
15. `scripts\validate_attestation_verification.py`
16. `scripts\validate_solution.py`
17. `submission\PROJECT_DESCRIPTION.md`
18. `submission\TESTING_INSTRUCTIONS.md`
19. `submission\JUDGING_RUBRIC_ALIGNMENT.md`
20. `tests\test_attestation_validation.py`
21. `tests\test_hardened_smoke.py`
22. `tests\test_solution_layout.py`

### Commit B — local narration tooling and rights disclosures

**Commit title:** `Add reproducible local Kokoro narration tooling`

1. `pyproject.toml`
2. `THIRD_PARTY_NOTICES.md`
3. `docs\LOCAL_TTS_PROVENANCE.md`
4. `scripts\matchpulse_conversational_tts.py`
5. `scripts\matchpulse_kokoro_v2.py`
6. `scripts\matchpulse_local_tts.py`
7. `scripts\record_matchpulse_demo.py`
8. `scripts\record_matchpulse_hosted_submission.py`
9. `tests\test_conversational_tts.py`
10. `tests\test_kokoro_v2_narration.py`
11. `tests\test_local_tts.py`
12. `.gitignore` — only the approved generated-media, local-audit, local-TTS,
    and local-Azure ignore-rule hunk; exclude the separate `.fake` line.

## Exact exclusions

Every path not named in the relevant allowlist is excluded. Explicit
exclusions include:

- The unrelated `.fake` line in `.gitignore`; stage only the approved ignore
  rules listed for Commit B, using a reviewed hunk-specific patch.
- `docs\AZURE_CHALLENGE_DEPLOYMENT_PLAN.md`; all changed
  `src\matchpulse\` application files; and their paired API/runtime tests.
- Workflow-policy/security tests and all unrelated existing modifications.
- `.foundry\`, `.kilo\`, `.azure\`, `srv.pid`, local portal worksheet
  `submission\PORTAL_SUBMISSION_WORKSHEET.md` (skip-worktree), and the local
  user-input worksheet.
- All media, generated audio/video, captions, manifests, archives, audit
  files, model/voice weights, other binaries, and local-only approval and
  recording materials.
- `submission\COMMIT_PLAN.md`, this packet, the other authorization packets,
  `submission\AUTHORIZATION_PACKETS.md`, and upload-preparation materials.

The local portal worksheet's index flag must remain unchanged. Do not stage
it, clear skip-worktree, or use a command that sweeps in unrelated paths.
`submission\COMMIT_PLAN.md` includes the path-by-path classification of all
44 observed modified tracked paths, 33 visible untracked paths after packet
creation, and the hidden tracked worksheet.

## Prerequisites and stop gates

Before any future staging:

1. Obtain separate, explicit maintainer authorization naming Commit A and/or
   Commit B, exact paths, branch, and whether push is included. A general
   approval is insufficient.
2. Keep unresolved rights unresolved. Under the recorded publication gate,
   `RIGHTS_UNRESOLVED` blocks authorization for both proposed commits; it
   must not be treated as waived by these packets. Obtain authoritative
   evidence and a documented entrant/rights-holder decision before seeking
   fresh authorization.
3. Recheck the current working-tree and index inventory, including
   skip-worktree flags, and compare each staged path against this exact list.
4. Review all public-facing diffs for factual accuracy and privacy-safe
   placeholders. Verify deployed-image claims against the immutable image
   revision and recorded evidence; do not imply current worktree changes are
   deployed.
5. Re-run suitable tests and fresh secret/security checks on the exact
   proposed changes immediately before staging. Preparation checks on
   2026-10-26 passed 189 tests (one optional attestation test skipped), Ruff,
   `git diff --check`, solution validation, JSON parsing, all 34 compiled
   Bicep guardrails, Trivy scans of the exact allowlist, and read-only media
   validation. These results do not authorize staging or replace a final
   pre-staging review.
6. Verify current remote branch rules and intended target. Do not assume the
   earlier observation of an unprotected `main` is still current. Require
   human review regardless.

Stop without staging if any prerequisite is missing, a path is unexpected,
the index is already staged unexpectedly, a check fails, rights remain
unresolved, or any claim cannot be supported. Do not continue to Commit B
after an A failure without a new scope review.

## Commands for a separately authorized future execution

The following are **not executed by this task**. Replace each bracketed
placeholder only after the corresponding separate authorization. Run in
PowerShell from the repository root.

First confirm the remote base and inventory:

```powershell
git status --short --untracked-files=all
git diff --name-only
git diff --cached --name-only
git fetch origin main
$head = git rev-parse HEAD
$main = git rev-parse origin/main
if ($LASTEXITCODE -ne 0 -or $head -ne $main) { throw "HEAD is not the freshly fetched origin/main; stop and prepare a clean authorized branch." }
git switch --create "<AUTHORIZED_TOPIC_BRANCH>"
```

For Commit A, after its own authorization and review:

```powershell
git add -- README.md docs\ARCHITECTURE.md docs\AZURE_COST_PLAN.md docs\AZURE_DEPLOYMENT.md docs\AZURE_MODEL_PLAN.md docs\AZURE_PROVIDER_AND_RBAC_PLAN.md docs\CHALLENGE_ALIGNMENT.md docs\REPRODUCIBILITY.md infra\main.bicep infra\main.parameters.example.json infra\validate_template.py scripts\hardened_smoke_test.py scripts\preflight.py scripts\smoke_test.py scripts\validate_attestation_verification.py scripts\validate_solution.py submission\PROJECT_DESCRIPTION.md submission\TESTING_INSTRUCTIONS.md submission\JUDGING_RUBRIC_ALIGNMENT.md tests\test_attestation_validation.py tests\test_hardened_smoke.py tests\test_solution_layout.py
git diff --cached --check
git diff --cached --name-only
git diff --cached
git commit -m "Finalize Azure recovery configuration and challenge documentation"
```

For Commit B, only after a separate authorization and a clean A review:

```powershell
git add -- pyproject.toml THIRD_PARTY_NOTICES.md docs\LOCAL_TTS_PROVENANCE.md scripts\matchpulse_conversational_tts.py scripts\matchpulse_kokoro_v2.py scripts\matchpulse_local_tts.py scripts\record_matchpulse_demo.py scripts\record_matchpulse_hosted_submission.py tests\test_conversational_tts.py tests\test_kokoro_v2_narration.py tests\test_local_tts.py
# Stage only the reviewed non-.fake .gitignore hunk; do not add the whole file.
git add -p -- .gitignore
git diff --cached --check
git diff --cached --name-only
git diff --cached
git commit -m "Add reproducible local Kokoro narration tooling"
```

Push is a separate gated action; do not push unless the authorization
explicitly names the reviewed commit hashes, remote, and branch:

```powershell
git status --short --untracked-files=all
git log -2 --oneline
git push --set-upstream origin "<AUTHORIZED_TOPIC_BRANCH>"
```

Do not force-push, push to `main`, create a PR, or infer authorization from a
successful commit. A PR requires its own explicit authorization.

## Rollback and one-time authorization

- Before commit, stop and unstage only the exact reviewed paths with
  `git restore --staged -- <authorized-paths>`; preserve all worktree changes.
- After an authorized local commit but before push, do not amend or reset
  without a fresh decision. Preserve the commit and request review.
- After an authorized push, use a separately reviewed revert commit/PR; do
  not rewrite shared history or force-push. Keep A and B independent.
- No rollback is needed now: no index, commit, push, or remote state was
  changed.

**Conditional authorization and remaining execution gates:**

- User's request: prepare commit/push packets only; no execution
  authorization was supplied. The gate remains unmet.
- Authorized commit (`A`, `B`, or both) and exact reviewed paths:
  `[CONFIRM AGAINST FINAL REVIEWED DIFF]`
- Rights evidence and explicit rights-holder/entrant decision:
  `[USER INPUT REQUIRED — RIGHTS CURRENTLY UNRESOLVED]`
- Topic branch, exact commit hash(es), remote, and push target:
  `[NOT YET KNOWN — MUST BE VERIFIED AFTER AUTHORIZED STAGING/COMMIT]`
- Authorizing maintainer and timestamp: `[USER INPUT REQUIRED — NOT
  AUTHORIZED]`; personal identity details must not be copied into this
  repository.

An authorization must explicitly name the commits, branch, remote, and push
target. Suggested exact wording after every prerequisite has passed:

> I authorize staging and committing only Commit [A/B] from the reviewed
> allowlist in `submission\COMMIT_PLAN.md`, with the reviewed commit message
> and diff, on topic branch `[BRANCH]` based on the freshly verified
> `origin/main`. I authorize pushing commit `[COMMIT_SHA]` to
> `origin/[BRANCH]`. This does not authorize a pull request, merge, upload,
> challenge submission, or Azure change.

Use this template to confirm exact hashes and branch details only after all
gates pass. If both commits are authorized, name each separately and
authorize their order. No action should be executed while the conditional
finalization gates remain unsatisfied.

## Final continuation readback — 2026-10-26

- The exact 22-path Commit A list and 12-path Commit B list still exist and
  match the exact 34-file Trivy scan copy. The value-only privacy/secret scan
  passed; no portal-only values, local paths, media, model/voice weights,
  `.azure` state, or local audit evidence are in either list. The unrelated
  `.fake` `.gitignore` line remains excluded; do not stage the whole file.
- Final checks passed: pytest (189 passed, one optional real-attestation test
  skipped), Ruff, `git diff --check`, solution validation, six JSON parses,
  fresh Bicep build, and all 34 infrastructure guardrails. Trivy findings
  lists are empty for the exact allowlist and for HIGH/CRITICAL vulnerabilities
  in the immutable deployed image.
- Fresh Azure readback continues to show no ingress configuration and the
  approved immutable image. The current worktree's application and
  infrastructure changes are not represented by that image; public
  documentation must continue to say so. The resource group contains two
  separately user-authorized Foundry development resources; they are outside
  the submitted runtime and not deployed by MatchPulse Bicep. They remain
  unchanged pending the separately scheduled post-submission security/cost
  review.
- `COMMIT_A_ALLOWLIST_READY=YES` and `COMMIT_B_ALLOWLIST_READY=YES` mean only
  that their exact paths are present and scan-safe. They are **not** ready
  for execution authorization while the required `RIGHTS_UNRESOLVED` gate
  remains. Do not stage, commit, or push.
- The approved video remains unchanged and local; no upload, portal entry,
  challenge submission, or Azure mutation occurred.
