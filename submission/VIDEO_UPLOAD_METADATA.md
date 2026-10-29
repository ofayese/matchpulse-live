> **UPDATE 2026-10-27 — SUPERSEDING NOTE:** The human-approved ElevenLabs Lily V1 video (`f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`) is now the sole active submission video, with `VOICE_RIGHTS_CONCLUSION=ELEVENLABS_PAID_COMMERCIAL_LICENSE` and `THIRD_PARTY_RIGHTS_DECLARATION=YES`. Any Kokoro / `bf_emma` / `RIGHTS_UNRESOLVED` / `PENDING_RIGHTS_REMEDIATION` / rights-remediation blocker language below is **historical** (`KOKORO_VOICE_RIGHTS_CONCLUSION=RIGHTS_UNRESOLVED`, `SUPERSEDED_FOR_RIGHTS_CERTAINTY`) and no longer blocks the active video. Commit, push, YouTube upload, and challenge submission remain separately gated; see `submission/VOICE_RIGHTS_DECISION.md` and the top-level authorization packets.

# Video upload metadata (preparation only — not an upload)

Status: **DRAFT / YOUTUBE UNLISTED RECORDED AS ENTRANT CHOICE / NO EXECUTABLE
UPLOAD AUTHORIZATION**. The local portal worksheet records YouTube Unlisted
as the entrant's choice. Rights, live portal requirements, and the intended
channel remain unresolved; no one-time upload authorization is recorded as
granted. No file in this repository has been uploaded, staged, committed, or
pushed as part of producing this document.

## Approved file

- **Exact approved filename:** `submission/matchpulse-submission-hosted-elevenlabs-lily-v1-candidate.mp4`
- **SHA-256:** `f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`
- **Duration:** 115.0 seconds (01:55.0)
- **Container / codecs:** MP4, H.264 (yuv420p) video / AAC audio, 1920×1080, ~30 fps, 48 kHz stereo
- **File size:** 7,255,648 bytes
- Source approval record: `submission/FINAL_VIDEO_APPROVAL.md`; machine-readable manifest: `submission/FINAL_VIDEO_MANIFEST.json`.

Any destination-side integrity check must be performed against the SHA-256
above before relying on an uploaded copy. If an uploaded file's hash does not
match, stop and do not rely on, replace, or re-upload it without fresh,
explicit authorization.

## Title

`MatchPulse Live | Synthetic Football Match Insights Demo`

## Short description (for portals/fields with a short-summary limit, target ≤150 characters)

MatchPulse Live turns synthetic football events into evidence-linked insights for fans, analysts, and
broadcasters — hosted on Azure Container Apps.

## Full description

MatchPulse Live is a synthetic-data prototype for evidence-linked football storytelling. This 115-second
demonstration shows a hosted validation on Azure Container Apps using only seeded, fictional synthetic match
events (the fictional clubs "Northbridge City" and "Harbor United"); no real match feed, league, broadcast
graphic, club crest, or player data is used, and nothing in this video implies endorsement by Microsoft, any
league, or any club.

The application's local pipeline interprets incoming event sequences, attaches source event IDs and
calculation details to each derived match moment, and renders that same verified moment differently for
three audiences: fans get an immediate, plain-language headline; analysts get the calculation, inputs, and
evidence identifiers behind it; and broadcasters get a presentation-ready framing of the same fact. The same
grounded moment is rendered in English, Spanish, and French, with evidence staying attached across every
language and audience variant — this is evidence-grounded match recap, not free-form generation.

The pipeline is defensive about event delivery: replaying the same accepted event is acknowledged
idempotently and does not duplicate goals, insights, or state, and an out-of-order event is rejected (HTTP
409) rather than corrupting match state, so a producer can safely retry without side effects.

An optional, guarded Microsoft Foundry adapter can rewrite narrative copy without changing the underlying
facts. The recorded run made **zero model calls**; a fresh read-only check found no Foundry runtime setting
or model deployment. Deterministic template-based rendering is the always-available fallback path used here
end-to-end.

Foundry runtime is disabled in the submitted MatchPulse deployment, and the
demonstrated workflow makes zero model calls. The approved video does not
demonstrate Foundry usage. The separately user-authorized Foundry account and
project are not part of the submitted MatchPulse runtime and are not deployed
by MatchPulse Bicep.

The demo was deployed and verified on Azure Container Apps. A fresh read-only check on 2026-10-26
confirmed that the app has no ingress configuration and uses the expected immutable image digest. The
recorded demonstration — rather than a public hosted URL — is being shared.

Repository (code, architecture docs, and reproduction instructions): https://github.com/ofayese/matchpulse-live
(the repository link is a placeholder/reference for judges and viewers; it is not itself a claim that the
repository is the video host).

This project was built for a hackathon/challenge submission. It is an independent entrant project; no
Microsoft affiliation, sponsorship, partnership, or endorsement is claimed or implied, and any challenge or
platform name referenced is used only to describe the context the project was built for.

## YouTube Unlisted draft (recorded choice; upload not authorized)

The local portal worksheet records YouTube **Unlisted** as the entrant's
choice. That choice is not evidence that the live portal accepts this host,
and it is not authorization to upload the approved hash. All rights, portal,
destination, account, and one-time authorization gates must be cleared first.

**Draft description (for review only; not authorized for upload):**

> MatchPulse Live transforms synthetic football events into explainable, audience-specific match intelligence for broadcast and streaming experiences.
>
> The demonstration shows a synthetic match between Northbridge City and Harbor United, including deterministic match-state updates, duplicate-event idempotency, out-of-order event rejection, evidence-grounded recaps, and tailored fan, analyst, and broadcaster experiences in English, Spanish, and French.
>
> The validated challenge deployment runs on Azure Container Apps using an immutable container image. A fresh read-only check found no ingress configuration, Foundry runtime setting, or model deployment; the recorded run made zero model calls and used deterministic fallback.
>
> Foundry runtime is disabled in the submitted MatchPulse deployment, and the demonstrated workflow makes zero model calls. The approved video does not demonstrate Foundry usage.
>
> Repository: https://github.com/ofayese/matchpulse-live
>
> This project uses synthetic demonstration data. It is not affiliated with or endorsed by the Premier League or any represented club.
>
> Built for the Inside the Game: Developer Hackathon.

**Requested YouTube settings (not yet set or verified):**

| Setting | Requested value |
|---|---|
| Visibility | Unlisted; never Public |
| Audience | No, it is not made for kids |
| Allow embedding | Yes |
| Publish to subscriptions feed | No, if the interface offers this option for Unlisted uploads |
| Category | Science & Technology |
| License | Standard YouTube License unless the entrant explicitly selects another supported license |
| Language | English |

The recorded host choice does not identify the intended channel or
signed-in account. Current YouTube upload settings and live challenge-portal
video requirements remain unverified; no executable one-time upload
authorization is recorded.

## Tags

MatchPulse Live, football analytics, soccer analytics, synthetic data,
explainable AI, Azure Container Apps, Microsoft Azure, sports technology,
broadcast technology, streaming experience, developer hackathon, Inside the
Game

## Thumbnail text

No approved thumbnail was found in the submission tree. If an authorized
upload later proceeds, allow YouTube to choose a temporary frame; do not
generate or upload an unreviewed thumbnail. A separately reviewed thumbnail
may be prepared later.

## Captions (English)

- **Source file:** `submission/final-support/MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt`
- **Validation result:** Do not upload this SRT with the approved V2 video. It
  does not match the V2 conversational narration: the V2 narration begins
  “Here’s MatchPulse Live” and includes revised spoken wording, while this SRT
  starts with the superseded “MatchPulse Live runs on Azure Container Apps.”
- **Upload instruction:** Leave custom captions unattached and allow
  YouTube-generated captions if available. Prepare a new human-reviewed
  English caption file as a separate follow-up; do not alter or regenerate
  the approved video.

## Visibility recommendation

**Recorded entrant choice: Unlisted / link-only.** Reconfirm it before any
later upload; no upload is currently authorized. Never set the video to
Public. Unlisted does not by itself prove that judges can access the video;
signed-out playback must be verified after any separately authorized upload.
The live portal has not been confirmed to accept Unlisted links.

---

## Host comparison: YouTube (Unlisted) vs. Microsoft Stream (shareable/public) vs. another unauthenticated host

All limits below marked "verify live" must be re-checked against each provider's current live documentation
or upload UI before relying on them — none are guessed in this table as if they were current confirmed facts.

| Criterion | YouTube — Unlisted | Microsoft Stream (on SharePoint/OneDrive) — shareable/public link | Another unauthenticated-playback host (generic, e.g. a direct-file/object-storage or similar public host) |
|---|---|---|---|
| **Account prerequisite** | Requires a Google Account with YouTube channel access (standard consumer account; no org license needed). | Requires a Microsoft 365 tenant/license with Stream (on SharePoint) enabled; typically an organizational account, not a free personal signup. | Varies by host; may need only an account on that specific host, or none at all for drop-in storage — verify live per chosen host. |
| **Access / login for playback** | Unlisted videos play for *anyone with the link*, no Google sign-in required to view. | Depends on the sharing link type: an org "Anyone" link can allow unauthenticated viewing, but many tenants restrict Stream sharing to authenticated/organizational users by policy — **must verify live**, do not assume anonymous playback works. | Depends entirely on host configuration (public bucket/object vs. authenticated share) — **must verify live** that the specific link is unauthenticated-readable. |
| **File size / duration limits** | Historically generous (multi-GB, long-duration) for verified accounts; exact current limits must be verified live in YouTube's current help documentation before relying on them. | Subject to the tenant's OneDrive/SharePoint storage quota and any organization-specific Stream file-size policy; verify live against the current tenant and Stream documentation. | Entirely host-dependent (e.g., some object-storage hosts have per-object size caps or require multipart upload for large files) — verify live. |
| **Codec compatibility** | Broad transcoding support; MP4/H.264+AAC (this file's format) is a well-supported ingest format, but YouTube re-encodes on upload — verify live that current ingest requirements have not changed. | SharePoint/Stream generally accepts common MP4/H.264 uploads and transcodes for streaming; exact current supported codec/container list must be verified live. | No transcoding guarantee on a generic unauthenticated host — the exact bytes (and thus this file's container/codec) are typically served as-is, so compatibility is more predictable, but player/browser codec support on the *viewer* side must still be verified live. |
| **URL stability / replace behavior** | A given unlisted video's URL (video ID) is stable as long as the video isn't deleted; re-uploading a revised file creates a *new* URL unless using YouTube's own "replace video" feature in YouTube Studio (where available), which preserves the URL/ID — verify live that replace is available for the account type in use. | Replacing the file in the same SharePoint/OneDrive location can preserve the sharing link in many tenant configurations, but behavior depends on tenant settings and whether it's a direct file link vs. a Stream-specific player link — verify live. | Typically the most predictable: overwriting the same object/key at the same path preserves the same URL on most object-storage-style hosts, but this must be verified live for the specific host chosen. |
| **Captions** | Native support for uploading/attaching an SRT/VTT caption track per video, with language and default-track selection. | Native support for caption files varies by Stream version/tenant; some configurations support auto-generated or uploaded transcripts — verify live. | No native captions mechanism on a generic host; captions would need to be either burned in, hosted and linked externally, or delivered as a separate downloadable file alongside the video. |
| **Judge suitability** | High: near-universal reviewer familiarity, no login needed for unlisted playback (once verified), native captions, stable embeddable player. | Medium: works well if judges are inside or have access to the tenant/organization, but anonymous-link policy risk makes it less reliable for external judges unless explicitly verified. | Variable: can be very reviewer-friendly (simple MP4 download/stream link, no login) if the host serves the exact file unauthenticated, but lacks the native caption/visibility/channel conventions judges may expect — verify per host. |

### Primary-portal rule status (provisional — must be rechecked live)

The primary challenge/submission portal's own video-hosting rule could not be independently verified in this
working session. Direct fetches returned only the client-side shell with a hidden 404 state, not usable rules
or form content. Earlier local notes restated a public-video-URL expectation, but that is not primary-source
confirmation and must not be treated as an official requirement.

#### 2026-10-26 re-verification attempt (passive fetch only, portal not entered)

A fresh attempt was made in this session to independently verify the official portal's video-hosting
rules via passive, read-only fetches (no sign-in, no form interaction, no browser session was opened
against the portal). Findings:

- `https://aka.ms/insidethegame` redirects to
  `https://innovationstudio.microsoft.com/hackathons/insidethegamedeveloperhackathon` (confirmed from
  `submission/REGISTRATION_AND_SUBMISSION_CHECKLIST.md:20`).
- A direct fetch of that URL, of a guessed `/rules` sub-path, of a guessed `/api/hackathons/...` endpoint,
  and of `robots.txt`/`sitemap.xml` on the same host all returned an **identical** client-side
  single-page-app shell with a hidden `<div id="errorWrapper">404 Error — The page you are looking for
  cannot be found.</div>` and no server-rendered rules text. This indicates the site serves the same
  JavaScript-rendered shell for every path tried (consistent with a pure client-side-routed SPA whose
  content requires in-browser script execution), not that a specific sub-path is uniquely missing.
- The Wayback Machine CDX API
  (`web.archive.org/cdx/search/cdx?url=innovationstudio.microsoft.com/hackathons/insidethegamedeveloperhackathon*`)
  returned zero archived snapshots for this URL at the time of this check.
- General web search (Bing, Google, DuckDuckGo) for the hackathon name and portal URL did not surface any
  cached rules page, official rules PDF, or third-party mirror containing the portal's actual
  video/upload rules text.

**Classification: `REQUIREMENT_NOT_FOUND`.** No usable official rules content
was reachable, so no video-hosting requirement could be found in the
accessible primary sources. This classification does not establish that the
portal has no video requirement. The worksheet records YouTube Unlisted as
the entrant's choice, but that is not evidence the portal accepts it. The
authenticated portal was not entered.

---

## Playback and verification checklist (run after any future, authorized upload)

1. **Pre-upload integrity:** Confirm local file SHA-256 is exactly
   `f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786` immediately before upload.
2. **Post-upload integrity (where the host exposes a hash/checksum or allows re-download):** Re-download or
   use the host's integrity feature and confirm the hash still matches; if the host has no exposed hash,
   instead re-download and spot-check duration (115.0s) and resolution (1920×1080) as the closest practical
   substitute.
3. **Unauthenticated playback check:** Open the resulting URL in a private/incognito browser window with no
   active session on the host, from a different network if possible, and confirm the video plays without any
   sign-in prompt (if the chosen visibility is meant to allow unauthenticated viewing).
4. **Visibility check:** Confirm the video does not appear in the host's own public search/browse/discovery
   surfaces if "unlisted"/link-only was selected, and confirm it is NOT set to private in a way that would
   block a judge or reviewer who only has the link.
5. **Caption check:** Do not attach the available stale SRT. If YouTube
   automatic captions are available, confirm they are generated and readable;
   a corrected human-reviewed V2 caption file is a separate follow-up.
6. **Thumbnail check:** No custom thumbnail is approved. Allow a temporary
   YouTube-selected frame; do not generate or upload an unreviewed thumbnail.
7. **Title/description check:** Confirm the title and description were accepted without truncation against
   the destination's live character limits (verify limits live — do not assume this document's text fits
   every destination unmodified).
8. **Replace/versioning check:** If this candidate is later superseded, confirm whether the destination's
   "replace" feature preserves the existing URL or whether a new URL will be issued, and update the portal
   submission worksheet (`submission/PORTAL_SUBMISSION_WORKSHEET.md`) accordingly.
9. **Repository link check:** Confirm the repository URL in the description
   (https://github.com/ofayese/matchpulse-live) resolves and is not a private/placeholder link at the time of
   judge review.
10. **No-secrets check:** Re-confirm (per `submission/IP_DATA_AND_SAFETY_REVIEW.md` and
    `submission/FINAL_VIDEO_APPROVAL.md`) that no secrets, local file paths, or private identifiers are visible
    anywhere in the uploaded video stream, title, description, tags, or thumbnail.

---

## Recommendation

**YouTube Unlisted is recorded as the entrant's choice, but no upload is
authorized.** All of the following require independent live verification,
reconfirmation, and explicit one-time authorization before execution:

1. The live challenge/submission portal's rules (re-checked in a browser, not from this document) in fact
   permit — or at minimum do not exclude — a YouTube-hosted Unlisted video for the required "public video
   URL" field.
2. Unauthenticated/unlisted playback is independently confirmed to work for the account and sharing settings
   actually used (per the playback and verification checklist above), not merely assumed because it is
   "typical" YouTube Unlisted behavior.
3. The user (entrant) has an eligible account (a Google Account with YouTube access, able to accept this
   file's size/duration/codec without unexpected rejection) and has verified current file-size/duration/codec
   limits live.
4. The intended YouTube channel is confirmed by the entrant, the active account is authenticated safely,
   and the authorization still names this exact file and hash.

If any of the above cannot be verified, stop without uploading. A change to another host requires a new
entrant selection and separately reviewed authorization.

## Blockers (must be resolved before any upload occurs)

- **Target channel and authorization unresolved** — YouTube Unlisted is
  recorded as the entrant's choice, but the active channel/account and an
  executable one-time upload authorization have not been confirmed.
- **Portal requirements unavailable** — Passive reads returned only the portal SPA shell; the live form has
  not confirmed that an Unlisted YouTube URL is accepted or established its current field/media limits.
- **Voice rights resolved for the active video** — narration is ElevenLabs stock voice Lily generated under the paid Starter commercial-license path. The superseded Kokoro candidate is archived and never uploaded. The entrant still personally confirms the portal IP declarations.
- **Entrant fields** — all supplied values are incorporated into the local
  ignored `submission/FINAL_USER_INPUT_CHECKLIST.md`. Legal name, contact
  email, and country remain portal-only and are not copied into this packet
  or public documentation. The entrant must still review live portal wording
  and confirm each answer there. Third-party-rights status is
  `PENDING_RIGHTS_REMEDIATION`.
- **Captions** — the available SRT is from superseded wording and does not match the approved V2 narration.
  Do not upload it; allow YouTube-generated captions if available. Human-reviewed V2 captions are a follow-up.
- **Thumbnail** — none was approved; allow a temporary YouTube-selected frame if upload is later authorized.

This document is metadata preparation only. **No upload, staging, commit, or push was performed in producing
it**, and none should be performed until the blockers above are explicitly
resolved and the user explicitly authorizes upload to the chosen destination
and exact hash. No current authorization exists.
