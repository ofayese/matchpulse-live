> **UPDATE 2026-10-27 — SUPERSEDING NOTE:** The human-approved ElevenLabs Lily V1 video (`f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`) is now the sole active submission video, with `VOICE_RIGHTS_CONCLUSION=ELEVENLABS_PAID_COMMERCIAL_LICENSE` and `THIRD_PARTY_RIGHTS_DECLARATION=YES`. Any Kokoro / `bf_emma` / `RIGHTS_UNRESOLVED` / `PENDING_RIGHTS_REMEDIATION` / rights-remediation blocker language below is **historical** (`KOKORO_VOICE_RIGHTS_CONCLUSION=RIGHTS_UNRESOLVED`, `SUPERSEDED_FOR_RIGHTS_CERTAINTY`) and no longer blocks the active video. Commit, push, YouTube upload, and challenge submission remain separately gated; see `submission/VOICE_RIGHTS_DECISION.md` and the top-level authorization packets.

# MatchPulse Live — authorization packets

**Preparation only — none of these actions has been executed or authorized by
this document.** The packets are independent. Authorization for one does not
authorize either of the others. No staging, commit, push, video upload,
challenge submission, or Azure change is performed by this task.

## Packet A — repository commits and push

### Current facts

- Repository: `ofayese/matchpulse-live`
- Remote `origin`: `https://github.com/ofayese/matchpulse-live.git`
- Current `HEAD`: `335781f928011f99a644083d80bfe4dfc480b1a6`
- Current branch: detached `HEAD`; no branch name or upstream tracking branch.
- Proposed push target: `origin/<AUTHORIZED_TOPIC_BRANCH>` — the branch name
  must be selected and created only after separate authorization and
  rechecking `origin/main`. Do not push to `main` by default.
- GitHub state recorded in `submission/COMMIT_PLAN.md`: no open PRs found;
  `main` reported unprotected; classic branch-protection endpoint returned
  404 and rulesets query returned no entries. This is not a guarantee of
  current protection state. Recheck before any later push; require explicit
  human review regardless.
- No files are staged. No commit, push, PR, or Azure operation was performed.

### Exact proposed allowlists from `submission/COMMIT_PLAN.md`

These are two separate proposed commits, not a merged scope.

**Commit A — `Finalize Azure recovery configuration and challenge documentation`**

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

**Commit B — `Add reproducible local Kokoro narration tooling`**

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
12. `.gitignore` — approved generated-media/local-state hunk only; exclude
    the unrelated `.fake` line.

The exact lists are copied from the current proposed allowlists in
`submission/COMMIT_PLAN.md` (22 paths in A, 12 in B; 34 total). They are not
permission to stage or publish anything. The portal worksheet and user-input
checklist remain local-only; the historical registration checklist is also
excluded from these commits.
No third commit is proposed. The canonical current path classification is in
`submission/COMMIT_PLAN.md`; do not use stale exclusions from this packet.

**Commit stop:** voice-asset and promotional-use rights remain
`RIGHTS_UNRESOLVED`. The user required unresolved video-distribution rights to
be reported as a blocker before commit authorization. Therefore neither A nor
B is ready for commit authorization, despite passing local tests; no path is
staged or committed.

### Exact exclusions from the plan

Every path not named in the two allowlists above is excluded. The canonical
44-visible-tracked/33-visible-untracked/1-hidden-tracked classification is in
`submission/COMMIT_PLAN.md`. Exclusions include `.gitignore` (mixed with the
unrelated `.fake` line), the local Azure deployment plan, all runtime source
changes and paired tests, workflow tests, the skip-worktree-hidden portal worksheet, user-input
checklist, this authorization packet, local configuration, temporary archive
tools, and generated media/support/audit artifacts. The approved MP4, archived
visual source, narration WAVs/manifests, and model/voice assets are not commit
inputs. No model or voice binaries were present in visible status.

### Test, scan, and release gates as currently known (2026-10-26)

- Full pytest passed (189 passed, 1 optional real-attestation test skipped);
  Ruff, `git diff --check`, solution validation, JSON parsing, and all 34
  guardrails against the freshly built Bicep template passed.
- Trivy scans of the exact 34-file A/B allowlist returned no vulnerability,
  misconfiguration, license, or secret findings. The immutable deployed image
  scan returned no HIGH or CRITICAL vulnerability findings. The repository
  has no dependency lock, so these results do not prove a hash-pinned
  dependency environment.
- Independent security review flagged absolute output paths in the V2
  narration CLI; outputs and collision errors now contain basenames only, and
  a regression test checks that the local output directory is not disclosed.
  It also questioned ingress claims against older notes; a fresh ARM GET
  confirmed `ingress: null`, and public deployment claims were aligned to that
  response.
- The current Bicep source built successfully with the Bicep MCP compiler;
  the freshly compiled template passed all 34 infrastructure guardrails.
  The separate checked-in `infra/main.json` is an older compiled artifact and
  is not an A/B input.
- The repository-wide preflight is not rerun because it reads ignored
  historical audit content. The earlier clean-clone release rehearsal passed
  preflight; no audit-log contents were read in this session.
- The approved video SHA-256, sole top-level MP4, FFprobe metadata, full
  decode, video-stream MD5, loudness, true peak, and Git-ignore checks passed.
  The hash was identical before and after validation.
- Fresh read-only Azure responses confirm the app uses the expected immutable
  image, has no ingress configuration, and has no Foundry runtime setting;
  model deployment list is empty and direct resource-group role assignments
  are empty. The resource group contains seven resources, including a
  Cognitive Services account and project, not the earlier expected five.
  Month-to-date spend is $0 USD; budget readback shows the $25 monthly
  resource-group and $50 annual subscription alerts. Hosted-agent inventory
  remains unverified after the optional Preview returned 403.
- No files were staged, committed, or pushed. The approved video was not
  uploaded, the challenge was not submitted, and Azure was not mutated.
- The `bf_emma` voice rights remain `RIGHTS_UNRESOLVED`; this blocks commit
  authorization and upload authorization under the user's stated gate.
- This packet authorizes no Azure mutation, deployment, image rebuild,
  media/model inclusion, PR creation, or branch-protection bypass.

### Rollback

- Before a future commit: if a reviewed check fails, stop and unstage only
  those reviewed paths with `git restore --staged -- <paths>`; preserve the
  worktree.
- After an authorized push: use a reviewed revert commit/PR on the topic
  branch. Do not reset shared history or force-push. Keep A and B independent
  so B can be reverted without changing A.
- No rollback is needed now; no repository publication action was executed.

### One-time authorization (not granted)

To authorize a future action, the maintainer must supply a specific branch
name, reviewed commit(s), exact allowlist, test/scan results, and push target,
then explicitly authorize **only** the stated commit/push action. A general
approval or approval of Packets B/C does not authorize Packet A.

- Authorization: **[USER INPUT REQUIRED — NOT AUTHORIZED]**
- Authorized branch / exact commits / push target: **[USER INPUT REQUIRED]**
- Authorizing maintainer and time: **[USER INPUT REQUIRED]**

## Packet B — video upload

### Exact asset and metadata

- **Exact filename:** `matchpulse-submission-hosted-elevenlabs-lily-v1-candidate.mp4`
- **Exact SHA-256:** `f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`
- **Size/duration:** 7,255,648 bytes; 115.0 seconds.
- **Format:** MP4/H.264 1920×1080 30 fps; AAC 48 kHz stereo.
- **Metadata reference:** local approval and manifest:
  `submission/FINAL_VIDEO_APPROVAL.md` and
  `submission/FINAL_VIDEO_MANIFEST.json`.
- **Draft title:** `MatchPulse Live | Synthetic Football Match Insights Demo`
- **Repository reference:** https://github.com/ofayese/matchpulse-live
- **Destination:** `<UPLOAD_DESTINATION — ENTRANT TO VERIFY>`
- **Resulting video URL:** `<VIDEO_URL>`
- **Visibility:** `<VISIBILITY — VERIFY ON LIVE PORTAL AND DESTINATION>`
- **Captions:** English SRT reference:
  `submission/final-support/MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt`.
  It is local only; determine whether a separate captions upload is required.
- **Thumbnail:** none approved/prepared. Confirm whether required and obtain
  separate entrant approval; do not invent or upload one.
- **Current state:** `VIDEO_UPLOADED=NO`.

The local review notes restate that a public video URL is expected and do not
name one required hosting platform. The local portal worksheet records
YouTube Unlisted as the entrant's choice, but that choice is not evidence of
portal acceptance. The official portal was not independently retrieved as
rendered content; the fetch returned an SPA shell with a 404 error view.
Entrant must inspect the live portal and destination requirements before any
upload; do not infer the portal accepts the recorded choice.

### Rights, disclosure, and verification gate

**Rights status: `RIGHTS_UNRESOLVED`.** The `bf_emma` voice asset's separate
license and public promotional-use rights have not been verified. This blocks
public distribution. The file's local human approval is not rights clearance.
Do not upload or distribute until authoritative rights evidence is reviewed
and the entrant makes a documented rights decision.

Required disclosures: seeded synthetic football data, no live external match
data, Azure Container Apps validation with a fresh read-only check on
2026-10-26 confirming no ingress configuration,
Foundry runtime off in the deployed configuration, zero recorded model calls,
and local Kokoro-82M `bf_emma` narration. Do not claim the video demonstrates
an active Foundry model or a public hosted endpoint.

After rights clearance and a separate upload authorization, verify before
reporting completion:

1. Recompute SHA-256 locally and select only the exact file above.
2. Confirm the destination, visibility, title, file/codec limits, and caption
   requirements against the live portal and destination.
3. Upload only with the one-time authorization below; do not change the
   approved video.
4. Open the resulting URL from a signed-out/private session; confirm access,
   full playback, correct audio/video, captions if required, title,
   visibility, and disclosures. Record the actual URL only after this check.
5. A platform may transcode the uploaded media; verify the hosted rendition
   plays correctly rather than claiming its bytes match the local file.

### One-time authorization (not granted)

Upload authorization must identify the exact filename and hash, destination,
visibility, final metadata, caption/thumbnail treatment, and the rights
clearance. It cannot override `RIGHTS_UNRESOLVED`; no upload is allowed while
that blocker remains.

- Rights resolution/evidence: **[USER INPUT REQUIRED]**
- Destination and visibility: YouTube Unlisted is recorded in the portal
  worksheet; reconfirm it, verify portal acceptance, and confirm the target
  channel/account before authorization.
- Approved title/metadata/captions/thumbnail: **[USER INPUT REQUIRED]**
- One-time upload authorization: **[USER INPUT REQUIRED — NOT AUTHORIZED]**
- Authorizing entrant and time: **[USER INPUT REQUIRED]**

## Packet C — challenge portal submission

### Draft entry fields

- **Project title:** MatchPulse Live
- **Category:** **[USER INPUT REQUIRED]** — select only after reviewing the
  live portal's exact options. Do not claim a multi-agent or Foundry-use
  category based on this project.
- **Public repository:** https://github.com/ofayese/matchpulse-live
- **Video URL:** `<VIDEO_URL>` — pending an authorized upload and verified
  playback.
- **Video destination/platform:** not independently verified. Local review
  restates a public video URL and no single specified platform; entrant must
  verify against the rendered live form. Do not represent this as a formal
  organizer decision.
- **Portal text limits:** none verified. The fetch returned the SPA shell,
  not the actual form. Draft versions below are convenience variants, not
  claims about portal limits.

### Description drafts

The following variants fit within the indicated character budgets. Counts
include spaces and punctuation; line breaks are excluded. Verify actual live
portal limits and recount after any edits.

**200-character version (≤200):**

> MatchPulse Live turns seeded synthetic football events into evidence-linked match insights, tailored for fans, analysts, and broadcasters in English, Spanish, and French.

**500-character version (≤500):**

> MatchPulse Live turns seeded synthetic football events into evidence-linked insights for fans, analysts, and broadcasters in English, Spanish, and French. Its deterministic pipeline preserves event evidence and adapts explanations by audience and language. Validated on Azure Container Apps; a fresh read-only check found no ingress configuration, Foundry runtime setting, or model deployment. The recorded run made zero model calls. No live match feed; not autonomous or multi-agent.

**1,000-character version (≤1,000):**

> MatchPulse Live turns seeded synthetic football events into evidence-linked match insights for fans, analysts, and broadcasters in English, Spanish, and French. Its deterministic pipeline derives match moments, retains source-event IDs and calculation details, validates evidence, and adapts narratives by audience and language. The project was validated on Azure Container Apps; a fresh read-only check found no ingress configuration, Foundry runtime setting, or model deployment. The recorded model-call count is zero. The optional guarded Foundry adapter is not evidence of a model call. This prototype uses no live external match feed and is not an autonomous or multi-agent system. Judges can run the immutable published container image locally with Docker; see the repository's testing instructions. The current uncommitted checkout changes are not included in that deployed image.

**Full version (use only if accepted by the live portal):**

> MatchPulse Live is a synthetic-data prototype for evidence-linked football storytelling. It processes seeded football events into match moments, preserves source-event IDs and calculation details, validates that insights are grounded in event evidence, and renders audience-specific narratives for fans, analysts, and broadcasters in English, Spanish, and French.
>
> The solution was validated on Azure Container Apps. A fresh read-only check found no ingress configuration, Foundry runtime setting, or model deployment; the recorded model-call count is zero. The optional guarded Foundry adapter does not mean a model was used. The demonstration uses synthetic events, not live external match data. The implemented flow is a specialized deterministic processing pipeline, not an autonomous or multi-agent system. Match state is in process memory, and Event Hubs has no active consumer in the submitted baseline.
>
> The immutable published container image can be run locally with Docker; see `submission/TESTING_INSTRUCTIONS.md` in the public repository for the command and expected behavior. The working checkout contains later changes that are not included in that image. The approved 115-second video is local and not uploaded; its URL remains `<VIDEO_URL>`. Its local Kokoro-82M `bf_emma` narration has unresolved separate voice-asset and promotional-use rights, so the video must not be publicly distributed until that issue is resolved.
>
> Repository: https://github.com/ofayese/matchpulse-live

### Technology, agentic-design, impact, and category statements

- **Technology:** Python, FastAPI, Docker, Azure Container Apps, Bicep,
  GitHub Actions, GitHub Container Registry, artifact attestations, and an
  optional guarded Microsoft Foundry adapter. Only claim technologies
  demonstrably present in the reviewed release.
- **Implementation:** Deterministic event processing, source-evidence
  validation, audience personalization, and multilingual rendering.
- **Agentic design:** The implemented stages are specialized deterministic
  components, not autonomous agents or a multi-agent system. Do not claim
  “multi-agent,” autonomous planning, or a deployed Foundry model call.
- **Impact/applicability:** The intended use is clearer, evidence-linked
  match storytelling across fan, analyst, and broadcaster views and multiple
  languages. No user adoption, measured impact, or production outcome is
  established here.
- **Category adherence:** Local project notes refer to the judging themes
  technological implementation, agentic design and innovation, real-world
  impact and applicability, user experience and presentation, and category
  adherence. They do not verify the current portal's category options or
  weights. Entrant must inspect and select the exact supported category.

### Synthetic, Azure, Foundry, and model-call disclosures

- The demo uses seeded synthetic football events; no live external match data
  is used.
- Azure Container Apps was used for a validation deployment. A fresh
  read-only check found no ingress configuration; do not present it as a
  verified working public demo.
- Microsoft Foundry runtime was off in the deployed configuration and the
  recorded model-call count is zero.
- The video narration uses local Dockerized Kokoro-82M `bf_emma`. This is
  distinct from Foundry use. Its separate voice-asset and promotional-use
  rights are `RIGHTS_UNRESOLVED`, blocking public video distribution.

### Testing instructions for reviewers

With Docker installed, run the published immutable image:

```bash
docker run --rm -p 8080:8080 ghcr.io/ofayese/matchpulse-live@sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226
```

Open `http://127.0.0.1:8080/demo` on the same machine. For source-based
instructions, see `submission/TESTING_INSTRUCTIONS.md`. Fresh read-only Azure
state confirms that no ingress configuration is present.
The current checkout changes are not included in the immutable image; do not
describe this as a verified live public hosted demo. Confirm that the image and
instructions remain accessible before providing them to reviewers.

### Entrant/legal declarations — never prefilled

For every declaration the live portal actually asks, the entrant must read
the wording and personally provide the answer. This packet stores no personal
data and checks no legal boxes.

- Entrant identity and authorized representative: **[USER INPUT REQUIRED]**
- Age and age eligibility, if requested: **[USER INPUT REQUIRED]**
- Country/residence eligibility, if requested: **[USER INPUT REQUIRED]**
- Employer/employee status and conflicts of interest, if requested:
  **[USER INPUT REQUIRED]**
- Entry type, team/entity name, participant identities, participant
  eligibility, and each participant's consent: **[USER INPUT REQUIRED]**
- Authority of a representative to submit for the team/entity:
  **[USER INPUT REQUIRED]**
- Contributor list, contribution permissions, and authorization to submit:
  **[USER INPUT REQUIRED]**
- Compliance with eligibility rules and absence of conflicts:
  **[USER INPUT REQUIRED]**
- Originality/new-project representation and prior-contest/prize history:
  **[USER INPUT REQUIRED]**
- Rights to code, third-party materials, voice, music, graphics, and all
  submitted media: **[USER INPUT REQUIRED]**; `bf_emma` rights remain
  `RIGHTS_UNRESOLVED` and block public distribution.
- Terms, rules, privacy notice, code of conduct, and any license or rights
  grant: **[USER INPUT REQUIRED]**
- Any publicity, marketing, or media-release consent:
  **[USER INPUT REQUIRED]**
- Final source revision and any required public-release commitment:
  **[USER INPUT REQUIRED]**
- Exact deadline, category, required fields, and final submission status:
  **[USER INPUT REQUIRED]**; confirm in the live portal.
- Final truthful review of every submitted statement and checkbox:
  **[USER INPUT REQUIRED]**

### One-time authorization (not granted)

Challenge submission requires its own fresh authorization after the live form
is verified, all blocking entrant fields are complete, rights are resolved,
the public repository/revision is reviewed, and any video URL is verified.
This packet does not grant that authorization.

- Required fields and final entry reviewed by entrant: **[USER INPUT REQUIRED]**
- Rights blocker resolved: **[USER INPUT REQUIRED — CURRENTLY NO]**
- One-time portal submission authorization: **[USER INPUT REQUIRED — NOT AUTHORIZED]**
- Authorizing entrant and time: **[USER INPUT REQUIRED]**

Until these conditions are met, the final entry is **not ready for submission**.

## Superseding final continuation status — 2026-10-26

- All 18 supplied entrant field/value pairs were verified in the local,
  Git-ignored `submission/FINAL_USER_INPUT_CHECKLIST.md`. Legal name, contact
  email, and country remain portal-only; they are intentionally not duplicated
  in this packet or either proposed commit. The user-supplied deadline is
  October 27, 2026 at 11:59 PM Pacific; the live portal has not independently
  confirmed it.
- The approved video remains local, frozen at SHA-256
  `f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`.
  `YOUTUBE_UNLISTED_VERIFIED_ACCEPTED=NO` and
  `VIDEO_URL_REQUIREMENT_UNRESOLVED`; no intended channel/account is
  confirmed, and no upload or challenge submission is authorized.
- Voice rights remain `RIGHTS_UNRESOLVED`, so
  `THIRD_PARTY_RIGHTS_DECLARATION=PENDING_RIGHTS_REMEDIATION`. Keep the
  approved video local pending written rights-holder confirmation or a
  separately authorized, reviewed narration replacement.
- A fresh seven-resource inventory confirms the two additional resources are
  the user-authorized AI Services account and child Foundry project, not
  Container Apps dependencies or part of the submitted runtime. The user
  attributed them to the Visual Studio Code Foundry extension toolkit;
  Activity Log caller fingerprints for creation, connection writes, and
  repeated key-list activity are consistent, with app ID/user-agent/object ID
  unavailable. Retain them unchanged through submission pending a separate
  post-submission cost/security review. The current app has ingress null and retains the
  approved immutable image. The Hosted Agents Preview 403 is a nonblocking
  optional integration warning; no RBAC was assigned.
- Commit A and Commit B allowlists each pass file-existence and exact-scan
  checks (`COMMIT_A_ALLOWLIST_READY=YES`,
  `COMMIT_B_ALLOWLIST_READY=YES`), but this indicates preparation only;
  unresolved rights and other publication gates block execution.
- Final local tests, lint, solution validation, Bicep build and all 34
  guardrails, JSON parsing, exact allowlist Trivy scan, immutable-image
  HIGH/CRITICAL scan, and approved-video integrity checks passed. No files
  were staged, committed, or pushed; no video was uploaded; no challenge was
  submitted; and Azure was not modified.

**Current overall status: `MATCHPULSE READY — RIGHTS REMEDIATION REQUIRED`.**
The remaining publication gates are authoritative rights resolution or
separately authorized narration remediation, intended-channel/host
confirmation, and separate commit/push, upload, and final challenge
authorizations. The Foundry cost/security review is post-submission; it does
not block publication. No packet is execution authorization.
