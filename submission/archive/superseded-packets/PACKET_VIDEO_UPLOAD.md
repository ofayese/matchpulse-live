> **UPDATE 2026-10-27 — SUPERSEDING NOTE:** The human-approved ElevenLabs Lily V1 video (`f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`) is now the sole active submission video, with `VOICE_RIGHTS_CONCLUSION=ELEVENLABS_PAID_COMMERCIAL_LICENSE` and `THIRD_PARTY_RIGHTS_DECLARATION=YES`. Any Kokoro / `bf_emma` / `RIGHTS_UNRESOLVED` / `PENDING_RIGHTS_REMEDIATION` / rights-remediation blocker language below is **historical** (`KOKORO_VOICE_RIGHTS_CONCLUSION=RIGHTS_UNRESOLVED`, `SUPERSEDED_FOR_RIGHTS_CERTAINTY`) and no longer blocks the active video. Commit, push, YouTube upload, and challenge submission remain separately gated; see `submission/VOICE_RIGHTS_DECISION.md` and the top-level authorization packets.

# Packet: approved video upload

**Status: blocked — YouTube Unlisted is recorded as the entrant's
host/visibility choice, but no executable one-time upload authorization has
been supplied.** This packet has not entered the portal or upload destination,
created a public link, or altered the approved media.

## Asset identity and positioning

- Exact local candidate:
  `submission\matchpulse-submission-hosted-elevenlabs-lily-v1-candidate.mp4`
- Expected SHA-256:
  `f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`
- Recorded approval details: 7,255,648 bytes, 115 seconds, MP4/H.264,
  1920×1080 at 30 fps, AAC 48 kHz stereo.
- Recorded visual-stream MD5: `c85bef1de55944edebd4f4d003c70b59`.
- Draft title: `MatchPulse Live | Synthetic Football Match Insights Demo`.
- Captions candidate:
  `submission\final-support\MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt`.
- The SRT is stale and does not match the approved V2 conversational
  narration; do not upload it. Allow YouTube-generated captions if available.
- No thumbnail is approved. Allow a temporary YouTube-selected frame; do not
  generate or upload an unreviewed thumbnail.
- Video state: `VIDEO_UPLOADED=NO`; resulting URL:
  `[USER INPUT REQUIRED]`.
- Host/visibility: the local portal worksheet records YouTube Unlisted as
  the entrant's choice. Portal acceptance, intended channel, and signed-in
  account have not been confirmed; upload authorization is not granted.

## Provisional YouTube metadata and settings (only if later selected)

- **Title:** `MatchPulse Live | Synthetic Football Match Insights Demo`
- **Visibility:** Unlisted, never Public.
- **Audience:** No, it is not made for kids.
- **Embedding:** Allow.
- **Subscriptions feed:** Do not publish, if the interface offers this
  setting for an Unlisted upload.
- **Category:** Science & Technology.
- **License:** Standard YouTube License unless the entrant explicitly selects
  another supported license.
- **Language:** English.
- **Tags:** MatchPulse Live; football analytics; soccer analytics; synthetic
  data; explainable AI; Azure Container Apps; Microsoft Azure; sports
  technology; broadcast technology; streaming experience; developer
  hackathon; Inside the Game.
- **Description:** Use the exact user-supplied, reviewed draft in
  `submission\VIDEO_UPLOAD_METADATA.md`; re-check it against current field
  limits and ensure the synthetic-data, Azure, Foundry/model, repository, and
  non-affiliation disclosures remain accurate.

**Exact provisional YouTube description (review only; not upload authorization):**

> MatchPulse Live transforms synthetic football events into explainable, audience-specific match intelligence for broadcast and streaming experiences.
>
> The demonstration shows a synthetic match between Northbridge City and Harbor United, including deterministic match-state updates, duplicate-event idempotency, out-of-order event rejection, evidence-grounded recaps, and tailored fan, analyst, and broadcaster experiences in English, Spanish, and French.
>
> The validated challenge deployment runs on Azure Container Apps using an immutable container image. A fresh read-only check found no ingress configuration, Foundry runtime setting, or model deployment; the recorded run made zero model calls and used deterministic fallback.
>
> Repository: https://github.com/ofayese/matchpulse-live
>
> This project uses synthetic demonstration data. It is not affiliated with or endorsed by the Premier League or any represented club.
>
> Built for the Inside the Game: Developer Hackathon.

The video presents MatchPulse Live as a synthetic-data prototype for
evidence-linked football storytelling. It uses a deterministic pipeline, not
an autonomous or multi-agent system, and no live external match feed. The
deployed immutable image is revision
`335781f928011f99a644083d80bfe4dfc480b1a6`; the current uncommitted worktree
is not in that image. Fresh read-only Azure state confirmed the expected image
digest and no ingress configuration, Foundry runtime setting, or model
deployment; the recorded run made zero model calls. Do not claim the current
worktree is deployed or a verified live public demo.

The separately user-authorized Foundry account and project are development
resources, not part of the submitted MatchPulse runtime and not deployed by
MatchPulse Bicep. Foundry runtime is disabled in the submitted MatchPulse
deployment, and the demonstrated workflow makes zero model calls. The
approved video does not demonstrate Foundry usage.

## Rights and destination gates — not cleared

**Voice-asset and promotional/distribution rights for `bf_emma` are
`RIGHTS_UNRESOLVED`.** Local video approval is not proof of licensing or
permission to publish. This is a hard stop; do not upload or distribute the
file until authoritative rights evidence is reviewed and an explicit
rights-holder/entrant decision is documented. Do not replace this state with
an inferred approval.

The exact upload destination, platform requirements, visibility, portal
rules, and current caption/thumbnail requirements have not been independently
verified. Do not assume a platform or treat a stale checklist as current.

### Official portal source check (2026-10-26)

- The challenge's official short URL, [aka.ms/insidethegame](https://aka.ms/insidethegame), redirects to the Microsoft Innovation Studio challenge page: [primary challenge page](https://innovationstudio.microsoft.com/hackathons/insidethegamedeveloperhackathon).
- Passive fetch of the official page returned only its JavaScript SPA shell; the rules and form fields were not available. Guessed rules/API paths returned the same shell, and no archive snapshot was found.
- No Devpost page for this challenge was confirmed; Devpost search was blocked (403). The challenge is hosted on Innovation Studio, so generic Devpost guidance was not substituted for its rules.
- **Classification: `REQUIREMENT_NOT_FOUND` in accessible official materials.** YouTube Unlisted/Vimeo acceptance, unauthenticated playback, embedding, duration/size/codec, captions/thumbnail, live-app URL, category, character limits, and legal declarations remain unverified. This is not evidence that the live portal has no such requirements.

### YouTube primary-source behavior (platform only; not challenge acceptance)

- [YouTube privacy settings](https://support.google.com/youtube/answer/157177?hl=en):
  an Unlisted video can be viewed and reshared by anyone with its link, without
  a Google Account. It is not listed in search unless someone adds it to a
  public playlist. This supports a signed-out playback check but does not show
  that the challenge accepts Unlisted links.
- [Upload video details](https://support.google.com/youtube/answer/57407?hl=en):
  YouTube documents title (100-character) and description (5,000-character)
  limits and exposes audience, tags, category, captions, and distribution
  settings during upload. These are YouTube limits/settings, not challenge
  portal field limits or requirements.
- [Upload length and size](https://support.google.com/youtube/answer/71673?hl=en):
  the default video-length limit is 15 minutes; the maximum upload size is
  256 GB or 12 hours, whichever is less. The approved 115-second, 7,255,648-byte
  file is below these YouTube platform limits. This does not verify challenge
  limits or destination eligibility.
- [Recommended upload encoding](https://support.google.com/youtube/answer/1722171?hl=en):
  YouTube's published recommendations list MP4, H.264, AAC audio, stereo,
  48 kHz, and common 30 fps as compatible encoding choices. The frozen file's
  recorded container/codecs/sample rate/frame rate match these listed
  parameters; this is not a challenge-specific codec requirement.
- [Embedding controls](https://support.google.com/youtube/answer/171780?hl=en):
  YouTube documents an embedding control in Studio. If upload is separately
  authorized, verify embedding is allowed on the resulting video.
- [Captions](https://support.google.com/youtube/answer/2734796?hl=en):
  YouTube supports uploading, typing, or auto-syncing captions and may provide
  automatic captions. The stale SRT remains excluded; automatic captions, if
  available, must be checked for accuracy and are not evidence of a challenge
  caption requirement.
- [Custom thumbnails](https://support.google.com/youtube/answer/72431?hl=en):
  YouTube offers generated suggestions or custom thumbnails for eligible
  accounts. No custom thumbnail is approved; do not create or upload one.
- [Audience setting](https://support.google.com/youtube/answer/9527654?hl=en):
  YouTube requires creators to set each video's audience accurately. The
  provisional “No, it is not made for kids” setting must be confirmed as
  accurate by the authorized uploader; it is not a legal or portal finding.

Prerequisites before asking for upload authorization:

1. Obtain and review authoritative evidence covering the voice/model asset,
   its terms, and public promotional use of this exact recording; record the
   decision without exposing private documents in this packet.
2. Verify the live challenge portal's current accepted destination, URL
   requirements, deadline/time zone, file size/format/duration limits, and
   caption/thumbnail requirements. Verify the chosen destination's current
   terms, account access, visibility options, and signed-out accessibility.
3. The local portal worksheet records YouTube Unlisted as the entrant's
   choice; reconfirm it and separately authorize one upload of this exact
   hash. No executable one-time authorization is currently recorded. Confirm
   the intended channel/account, visibility, final metadata, and disclosures
   before any authorized action.
4. Recompute local hash and metadata using the commands below. A mismatch
   means stop; do not rename, edit, regenerate, or upload a substitute under
   this authorization.
5. Obtain a separate one-time written authorization naming the exact hash,
   destination, visibility, and metadata. Rights clearance is a prerequisite,
   not something that authorization can waive.

Any unknown remains `[USER INPUT REQUIRED]`. The packet does not assert that
the live portal or host rules have been verified.

## Exact pre-upload checks

The exact approved video was read-only validated on 2026-10-26: SHA-256,
container/stream metadata, full decode, stream MD5, loudness, true peak,
sole top-level MP4 status, and Git-ignore state matched the approval record.
The current continuation repeated those checks without rewriting the file:
SHA-256 remains
`f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`,
encoded video-stream MD5 remains `c85bef1de55944edebd4f4d003c70b59`,
duration is 115 seconds, loudness is -16.02 LUFS, and true peak is -1.95 dBTP.
Repeat the checks immediately before any separately authorized upload:

```powershell
$video = "submission\matchpulse-submission-hosted-elevenlabs-lily-v1-candidate.mp4"
$expected = "f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786"
$actual = (Get-FileHash -Algorithm SHA256 $video).Hash.ToLowerInvariant()
if ($actual -ne $expected) { throw "Approved video hash mismatch; stop without uploading." }
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels -of json $video
```

Required human actions after separate authorization:

1. Open only the entrant-verified destination and confirm the account,
   privacy/visibility setting, title, and requirements match the approved
   authorization.
2. Select only the exact candidate file above. Do not edit, transcode,
   substitute, or upload other media.
3. Do not upload the known-stale SRT. Allow automatic captions if available;
   prepare accurate V2 captions as a later, separately reviewed follow-up.
   Do not create or upload a thumbnail without separate approval; use a
   temporary platform-selected frame if the interface permits it.
4. After processing, capture the actual resulting URL and verify in a
   signed-out/private session: access, complete playback, correct audio and
   video, availability of the 1080p rendition, captions if required, title,
   visibility, and disclosures. Platform transcoding may change hosted bytes;
   verify playback, do not claim hosted hash equality.
5. Record `VIDEO_UPLOADED=YES` only after the URL is accessible and all
   required checks pass. This packet currently records `NO`.

## Stop and rollback

Stop before selecting/uploading if rights remain unresolved, the hash differs,
the destination or portal rules are unclear, the chosen visibility is not
explicitly approved, a required disclosure is missing, or the entrant's
authorization does not identify this exact asset and destination.

An upload may be publicly visible immediately and may not be fully reversible
(copies, caches, or platform processing may persist). If an authorized upload
is incorrect or exposed unexpectedly, use the host's unpublish/delete
control immediately, verify the public link is unavailable, preserve the
incident details, and contact the entrant/organizer as appropriate. Do not
re-upload or change visibility without fresh authorization. Deletion cannot
be represented as erasure of third-party copies.

## Conditional one-time authorization and remaining gates

- Entrant's one-time authorization for exactly one upload of this hash:
  **[USER INPUT REQUIRED — NOT AUTHORIZED]**
- Rights evidence reviewed and rights-holder/entrant decision:
  `[USER INPUT REQUIRED — RIGHTS CURRENTLY UNRESOLVED]`
- Exact SHA-256:
  `f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`
- Destination/platform and target account:
  YouTube Unlisted is the recorded choice; portal acceptance and
  `[USER INPUT REQUIRED]` target channel/account remain unverified.
- Visibility, title, captions, thumbnail, and final disclosures:
  YouTube Unlisted is the recorded choice; title/description are drafts,
  stale SRT/custom thumbnail excluded, and final confirmation is required.
- Intended YouTube channel/account and authenticated session verified:
  `[USER INPUT REQUIRED]`
- Portal and host requirements checked, with date/time:
  `[USER INPUT REQUIRED]`
- Authenticated session safe and upload-capable:
  `[USER INPUT REQUIRED]`
- Authorization execution gate: **not satisfied**. Rights, portal, host,
  target channel, and explicit one-time authorization are unresolved. No
  action is authorized for execution until all conditions pass.

Suggested exact wording after all rights, portal, destination, and
authentication gates pass:

> I authorize exactly one upload of
> `submission\matchpulse-submission-hosted-elevenlabs-lily-v1-candidate.mp4`
> with SHA-256
> `f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`
> to `[VERIFIED YOUTUBE CHANNEL]` as Unlisted, using the reviewed title,
> description, tags, audience setting, category, and other settings in this
> packet. Do not upload the stale SRT or a custom thumbnail; use automatic
> captions or a temporary platform-selected frame if available. I authorize no other video
> upload, no Public visibility, no challenge submission, and no repository
> commit or push.

This wording is a template, not current authorization. Rights remain
`RIGHTS_UNRESOLVED`; no upload is permitted until that gate is independently
cleared and the channel and live requirements are verified.

## Final continuation status — 2026-10-26

- The approved MP4 was revalidated read-only: exact filename and SHA-256
  `f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`,
  115 seconds, H.264 1920x1080 at 30 fps, AAC 48 kHz stereo, full decode,
  encoded video-stream MD5 `c85bef1de55944edebd4f4d003c70b59`, -16.02 LUFS,
  and -1.95 dBTP. It remains the only top-level submission MP4 and is still
  Git-ignored.
- **`YOUTUBE_UNLISTED_VERIFIED_ACCEPTED=NO`**;
  `VIDEO_URL_REQUIREMENT_UNRESOLVED`. The user's recorded Unlisted choice is
  not proof of portal acceptance. The official portal's accessible page
  remains a JavaScript shell; do not substitute generic Devpost guidance.
- Intended YouTube channel/account has not been confirmed. If a future
  separately authorized upload is allowed, confirm Unlisted, not made for
  kids, embedding enabled, Science & Technology category, the exact title,
  description, and tags above. Do not upload the stale SRT or an unreviewed
  thumbnail; allow generated captions and a platform-selected frame only if
  the entrant approves that treatment.
- Signed-out playback, complete playback, and the 1080p rendition can only be
  verified after a separately authorized upload. No upload was performed or
  authorized here. Keep `VIDEO_UPLOADED=NO`.
- `RIGHTS_UNRESOLVED` remains a hard stop; no public distribution of the
  generated `bf_emma` audio is cleared by the software/model license
  evidence. Keep `THIRD_PARTY_RIGHTS_DECLARATION=PENDING_RIGHTS_REMEDIATION`.
