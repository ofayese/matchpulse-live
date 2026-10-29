# Authorization packet — Lily V2 video upload

**Status: BLOCKED — preparation only. No upload has been authorized or performed.**

## Candidate artifact

- Local file: `.local-artifacts\video-review\matchpulse-submission-hosted-elevenlabs-lily-v2-candidate.mp4`
- SHA-256: `8dc7e848e6adad1fe342cf019e682802f41d49cec6d8a606bdaa4bd780a9825b`
- Size / duration: 7,048,251 bytes / 115.000 seconds
- Format: H.264, 1920×1080, 30 fps; AAC stereo, 48 kHz
- Full decode: passed
- Human full-video playback approval: pending
- Voice-rights declaration: pending in the V2 manifest; **do not upload until resolved**

The approved V2 WAV and clean visual master are unchanged. Do not treat the historical V1 YouTube listing below as this candidate's upload destination or as proof of playback availability.

## Historical listing and destination

- Previously recorded V1 listing: <https://www.youtube.com/watch?v=O5gHkl_UFHc>
- Recorded visibility: Unlisted
- Recorded channel: `@iwadev`
- Signed-out playback was pending in the repository record. The listing is historical V1 only; confirm the destination channel and access settings before any V2 upload.

No challenge-required video-hosting destination has been confirmed. The official challenge deadline, October 27, 2026 at 11:59 PM Pacific, has passed. This packet does not authorize portal entry or challenge submission.

## Proposed metadata (draft; confirm before upload)

- Title: `MatchPulse Live | Synthetic Football Match Insights Demo`
- Visibility: Unlisted
- Audience: Not made for kids
- Category: Science & Technology
- Embedding: Enabled
- License: Standard YouTube License
- Language: English

Description:

```text
MatchPulse Live turns seeded synthetic football events into explainable, audience-specific match intelligence for fan, analyst, and broadcaster views.

This demonstration follows the fictional match between Northbridge City and Harbor United. It shows evidence-linked insights, duplicate-event suppression, out-of-order-event rejection, localized views, and a final 2–1 recap.

The deployed application uses deterministic fallback with Foundry disabled and zero model calls. No live external match data is used.

Repository:
https://github.com/ofayese/matchpulse-live

Narration uses an ElevenLabs premade stock voice. Publication rights remain subject to the pending rights review.
```

Proposed tags: MatchPulse Live; football analytics; soccer analytics; synthetic data; explainable AI; Azure Container Apps; Microsoft Azure; sports technology; broadcast technology; streaming experience.

## Required gates before any upload

1. Complete full playback and receive `APPROVE_MATCHPULSE_LILY_V2_FINAL_VIDEO`.
2. Resolve and document the outstanding voice-rights declaration for this exact narration.
3. Confirm the hosting destination, YouTube channel, and metadata with the user.
4. Recompute the candidate SHA-256 and repeat media/decode validation immediately before upload.
5. Receive a separate explicit upload authorization naming this exact V2 file and destination.
6. If uploaded, verify visibility, signed-out playback, 1080p processing, audio/video sync, and rights/restrictions; record the resulting URL without entering or submitting the challenge portal.

Only after all gates pass, a separate authorization could use:

> `AUTHORIZE_YOUTUBE_UPLOAD_UNLISTED_LILY_V2` — upload the exact Lily V2 candidate above to my confirmed channel as Unlisted with the confirmed metadata.

That wording is **not authorization now**. No staging, commit, push, Azure action, portal modification, video upload, or challenge submission has occurred.
