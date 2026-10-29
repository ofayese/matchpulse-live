> **UPDATE 2026-10-27 — SUPERSEDING NOTE:** The human-approved ElevenLabs Lily V1 video (`f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`) is now the sole active submission video, with `VOICE_RIGHTS_CONCLUSION=ELEVENLABS_PAID_COMMERCIAL_LICENSE` and `THIRD_PARTY_RIGHTS_DECLARATION=YES`. Any Kokoro / `bf_emma` / `RIGHTS_UNRESOLVED` / `PENDING_RIGHTS_REMEDIATION` / rights-remediation blocker language below is **historical** (`KOKORO_VOICE_RIGHTS_CONCLUSION=RIGHTS_UNRESOLVED`, `SUPERSEDED_FOR_RIGHTS_CERTAINTY`) and no longer blocks the active video. Commit, push, YouTube upload, and challenge submission remain separately gated; see `submission/VOICE_RIGHTS_DECISION.md` and the top-level authorization packets.

# Packet: challenge portal submission

**Status: preparation only — the requested single submission is conditional
on successful finalization; no portal has been entered and no submission has
been made.** This packet is not a substitute for the live portal or the
entrant's personal review of every field.

## Verified project positioning for a truthful entry

**Core positioning:** MatchPulse Live transforms synthetic football events
into explainable, audience-specific match intelligence for broadcast and
streaming experiences.

**Core description:** MatchPulse Live is a synthetic-data prototype for
evidence-linked football storytelling. A deterministic pipeline turns seeded
football events into grounded match moments and audience-specific narratives
in English, Spanish, and French. It does not use live external match data and
is not an autonomous or multi-agent system.

The immutable published image
`ghcr.io/ofayese/matchpulse-live@sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226`
was built from source revision
`335781f928011f99a644083d80bfe4dfc480b1a6`. Azure Container Apps was used
for validation. A fresh read-only Azure check confirmed the expected immutable
image digest and no ingress configuration, Foundry runtime setting, or model
deployment. Foundry runtime is disabled in the submitted MatchPulse
deployment, and the demonstrated workflow makes zero model calls. The
separately user-authorized Foundry account and project are development
resources, not part of the submitted MatchPulse runtime and not deployed by
MatchPulse Bicep. The approved video does not demonstrate Foundry usage.
The project has nine remote-tool connection registrations. Read-only
Activity Log evidence and the user's confirmation attribute the account,
project, connections, and repeated key-list activity to expected VS Code
Foundry extension/toolkit activity; identity/app/user-agent fields not
surfaced by the Activity Log remain an attribution limitation. No key or
connection credential values were retrieved. Hosted-agent inventory could
not be verified because the optional Preview returned 403; this is a
nonblocking optional-integration warning, and no hosted agent is claimed.
The current uncommitted worktree changes are not in the deployed image and
must not be represented as deployed or tested by that image.

Do not claim active Foundry inference, multi-agent/autonomous behavior, live
match data, a currently reachable public Azure endpoint, user adoption, or
measured impact without new evidence.

## Portal-only facts and declarations

The live portal's current rules, categories, text limits, required fields,
deadline/time zone, and hosting requirements are **not verified** by this
packet. The official entry point [aka.ms/insidethegame](https://aka.ms/insidethegame)
redirects to the Microsoft Innovation Studio challenge page
([primary challenge page](https://innovationstudio.microsoft.com/hackathons/insidethegamedeveloperhackathon)).
Passive fetch returned only the JavaScript SPA shell; no rules/form text was
available. No Devpost page for this challenge was confirmed (search returned
403), so generic Devpost guidance was not substituted. Verify current rules
directly in the live portal before preparing a final entry.

YouTube's [official privacy guidance](https://support.google.com/youtube/answer/157177?hl=en)
says Unlisted videos can be watched by anyone with the link without a Google
Account. Its [upload guidance](https://support.google.com/youtube/answer/57407?hl=en)
documents platform fields and limits, and its
[duration/size guidance](https://support.google.com/youtube/answer/71673?hl=en)
sets a default 15-minute duration and a maximum of 256 GB or 12 hours,
whichever is less. These sources establish YouTube behavior only; they do not
establish that this challenge accepts YouTube Unlisted, what playback or
embedding the judges require, or any challenge-specific media limits.
`VIDEO_URL_REQUIREMENT_UNRESOLVED` remains in force.

The entrant-supplied values are recorded in
`submission/FINAL_USER_INPUT_CHECKLIST.md`, a local file excluded by Git
configuration. Treat those values as **portal-only**: never stage, commit,
push, or copy them into public documentation. The entrant must personally
review current portal wording and confirm each answer directly in the portal.
No additional legal declarations are inferred:

- Portal-only values supplied; live declarations still need review:
  `submission/FINAL_USER_INPUT_CHECKLIST.md`

| Field | Supplied value / status | Handling |
|---|---|---|
| Entrant type | `INDIVIDUAL` | Prepared |
| Display and legal name | Supplied | Portal-only; local ignored checklist |
| Project name | `MatchPulse Live` | Prepared |
| Team and members | `NOT_APPLICABLE` | Confirm individual entry is accepted |
| Contact email | Supplied | Portal-only; local ignored checklist |
| Country/region | Supplied | Portal-only; local ignored checklist |
| Age of majority / eligibility | Entrant confirmed `YES` | Portal-only; recheck exact rules and declarations |
| Microsoft/sponsor affiliation | Entrant confirmed `NO` | Portal-only |
| Original work | Entrant confirmed `YES` | Portal-only; confirm exact declaration wording |
| Terms/privacy acceptance | Entrant supplied `YES` for both | Portal-only; personally review current terms before any portal acceptance |
| Video destination/visibility | `YOUTUBE_UNLISTED` / `UNLISTED` | Entrant choice; portal acceptance and target channel unverified; no upload authorization |
| Repository | `https://github.com/ofayese/matchpulse-live` | Verify public access before submission |
| Third-party-rights declaration | `PENDING_RIGHTS_REMEDIATION` | Do not attest until rights are cleared |
- Exact current category selected from verified portal choices:
  `[USER INPUT REQUIRED]`
- Required text limits and fields confirmed:
  `[USER INPUT REQUIRED]`
- Entrant-supplied deadline: October 27, 2026 at 11:59 PM Pacific. This
  has not been independently confirmed from the live portal; verify it there
  before relying on it.
- Eligibility and rights requirements personally reviewed:
  `[USER INPUT REQUIRED]`

Unknowns remain unknown. This packet does not clear any rules or legal gate.

## Submission material fields

- Project title: `MatchPulse Live`
- Public repository: `https://github.com/ofayese/matchpulse-live`
- Reviewed public source revision for entry:
  `[USER INPUT REQUIRED — VERIFY IN LIVE REPOSITORY]`
- Video URL: `[USER INPUT REQUIRED — VIDEO NOT UPLOADED]`
- Video rights: `RIGHTS_UNRESOLVED`; public distribution is blocked pending
  authoritative clearance and a documented decision.
- Category: `[USER INPUT REQUIRED — VERIFY LIVE PORTAL OPTIONS]`
- Public demo URL, if requested: `[USER INPUT REQUIRED]`. No ingress
  configuration is present, so do not submit a public endpoint.
- Testing instructions should identify the immutable published image and
  revision, not imply current checkout changes are included.

### Suggested description (recount against live limits before use)

> MatchPulse Live is a synthetic-data prototype for evidence-linked football storytelling. A deterministic pipeline turns seeded events into grounded match moments and audience-specific narratives in English, Spanish, and French. It uses no live external match feed and is not an autonomous or multi-agent system. The immutable image validated on Azure Container Apps was built from source revision 335781f928011f99a644083d80bfe4dfc480b1a6; a fresh read-only check found no ingress configuration, Foundry runtime setting, or model deployment, and the recorded run made zero model calls. Current uncommitted worktree changes are not included in that image.

> Foundry runtime is disabled in the submitted MatchPulse deployment, and
> the demonstrated workflow makes zero model calls. The approved video does
> not demonstrate Foundry usage.

Use only if it fits the live portal's verified limit and remains accurate at
submission time. Do not add an unverified category, link, deadline claim, or
legal declaration to make it fit.

## Prerequisites and exact future actions

No browser or portal actions were performed for this task. Before any future
submission:

1. Verify the portal URL, active challenge, rules, eligibility requirements,
   allowed categories, required fields, exact text limits, deadline/time zone,
   public repository requirements, and video destination/format.
2. Resolve `RIGHTS_UNRESOLVED` using authoritative voice-asset and
   promotional-use evidence. This packet cannot waive rights. Keep the video
   URL blank until Packet Video Upload has completed its separately
   authorized process and signed-out playback verification.
3. Confirm the public repository and exact source revision to be evaluated.
   Distinguish that revision from the immutable deployed image and from
   uncommitted current worktree changes.
4. Confirm all links work from a signed-out session. A fresh ARM read on
   2026-10-26 returned no Container App ingress configuration; do not claim a
   currently reachable public Azure demo.
5. Entrant personally reviews every portal field and completes all
   identity/legal declarations directly in the portal, with no answers copied
   into repository files.
6. Obtain a separate one-time written authorization specifying the verified
   challenge, exact project/revision, final fields/links, and submitting
   entrant. A general approval is not enough.
7. Only after the above, open the live portal, enter the approved values,
   review the complete final preview, and use the portal's final submit
   control once. Save the confirmation privately and verify the final entry
   and links without changing its claims.

Stop before login or data entry if portal/rules are unverified, any required
field is unknown, any identity/legal declaration is unanswered by the
entrant, video rights remain unresolved, any link is not verified, a claim is
unsupported, or explicit one-time authorization is absent.

## Rollback and stop gates

Portal submission may be final and cannot be assumed reversible. If an
authorized submission contains an error, stop further edits; consult the
portal's current edit/withdrawal process and contact the organizer if needed.
Do not withdraw, edit, or resubmit without the entrant's explicit direction.
Keep any confirmation or personal record outside this repository.

## Conditional one-time authorization and remaining gates

- This task requests preparation for a possible final challenge submission;
  it does not authorize portal entry or submission. Execution gates remain
  unmet.
- Current rules, deadline/time zone, category, and field limits verified:
  `[USER INPUT REQUIRED]`
- Rights resolution and video upload/playback verified:
  `[USER INPUT REQUIRED — RIGHTS CURRENTLY UNRESOLVED]`
- Public repository/revision and all links reviewed:
  `[USER INPUT REQUIRED]`
- Entrant-supplied identity, eligibility, and declaration values are
  recorded in the local ignored checklist. The entrant must review the live
  wording and confirm truthful answers directly in the portal; legal name,
  email, and country remain portal-only and are not recorded in this packet
  or public repository files.
- Exact final entry reviewed and approved by entrant:
  `[USER INPUT REQUIRED]`
- Authorization execution gate: **not satisfied while rights, official portal
  requirements, final links, and final preview remain unverified**.

Suggested exact wording only after all portal, rights, link, and declaration
gates pass:

> I authorize exactly one final submission for the verified Inside the Game:
> Developer Hackathon entry “MatchPulse Live”, using the exact reviewed
> project description, category, repository revision, video URL, disclosures,
> and declarations shown in the portal preview. I personally confirm that I
> reviewed and truthfully completed all identity, eligibility, rights, terms,
> and privacy fields. This does not authorize a second submission, repository
> change, video upload, or Azure change.

This template grants no current authorization. Do not submit while voice
rights, the live portal requirements, or any required field remains
unverified.

## Entrant-input reconciliation — 2026-10-26

`ENTRANT_INPUTS_INCORPORATED=YES`: all 18 supplied field/value pairs were
checked against the ignored local file
`submission/FINAL_USER_INPUT_CHECKLIST.md`. The checklist, not this packet or
either proposed commit, holds the legal name, contact email, and country.
This packet records the supplied non-sensitive choices and statuses:

- `ENTRANT_TYPE=INDIVIDUAL`; `PROJECT_NAME=MatchPulse Live`;
  `TEAM_NAME=NOT_APPLICABLE`; `TEAM_MEMBERS=NOT_APPLICABLE`.
- Display/legal name, contact email, and country/region: supplied and kept
  portal-only in the ignored checklist.
- Age-of-majority and eligibility confirmations: supplied `YES`; affiliation:
  supplied `NO`; original-work declaration: supplied `YES`.
- Terms and privacy acceptance: supplied `YES` for each; personally review
  the current wording before any portal acceptance.
- `VIDEO_HOST=YOUTUBE_UNLISTED`; `VIDEO_VISIBILITY=UNLISTED`;
  repository: `https://github.com/ofayese/matchpulse-live`.
- `THIRD_PARTY_RIGHTS_DECLARATION=PENDING_RIGHTS_REMEDIATION`; do not attest
  to third-party rights while `RIGHTS_UNRESOLVED` remains.

The video URL, live category, current text limits, channel, host acceptance,
and exact legal wording remain unverified. The entrant-provided deadline is
not an independent portal readback. No portal fields were entered, and no
challenge was submitted.
