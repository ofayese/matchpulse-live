# Authorization packet — approved video upload

**Status: ready for authorization. No upload has been performed or is authorized until the user gives the exact wording below.**

## Exact artifact

- File: `submission\matchpulse-submission-hosted-elevenlabs-lily-v1-candidate.mp4`
- SHA-256: `f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`
- Size / duration: 7,301,914 bytes / 115.0 s; H.264 1920×1080 30 fps, AAC stereo 48 kHz
- Narration: ElevenLabs Starter, stock voice Lily, `eleven_multilingual_v2`, no cloning, no Beta service, generated during the active paid subscription
- Rights: `VOICE_RIGHTS_CONCLUSION=ELEVENLABS_PAID_COMMERCIAL_LICENSE`, `THIRD_PARTY_RIGHTS_DECLARATION=YES` (see [`VOICE_RIGHTS_DECISION.md`](VOICE_RIGHTS_DECISION.md))
- Human review: video and voice approved
- The superseded Kokoro candidate is archived, NOT FOR SUBMISSION, and must never be uploaded.

## Metadata

- Title: `MatchPulse Live | Synthetic Football Match Insights Demo`
- Visibility: **Unlisted** (do not make Public)
- Audience: Not made for kids
- Category: Science & Technology
- Embedding: Enabled
- License: Standard YouTube License (unless the user changes it)
- Language: English

Description:

```text
MatchPulse Live transforms synthetic football events into explainable, audience-specific match intelligence for broadcast and streaming experiences.

This demonstration follows a synthetic match between Northbridge City and Harbor United. MatchPulse validates incoming events, maintains deterministic match state, handles duplicates idempotently, rejects out-of-order updates safely, and produces evidence-grounded experiences for fans, analysts, and broadcasters.

The same accepted event evidence supports English, Spanish, and French views. The submitted Azure Container Apps deployment uses deterministic fallback with Foundry runtime disabled and zero model calls.

Repository:
https://github.com/ofayese/matchpulse-live

The narration was produced with a commercially licensed ElevenLabs stock voice during an active paid subscription. No voice cloning was used.

This project uses synthetic demonstration data. MatchPulse Live is not affiliated with or endorsed by the Premier League or any represented club.

Built for the Inside the Game: Developer Hackathon.
```

Tags: MatchPulse Live; football analytics; soccer analytics; synthetic data; explainable AI; Azure Container Apps; Microsoft Azure; sports technology; broadcast technology; streaming experience; ElevenLabs; Inside the Game; developer hackathon.

## Gates (all must pass; stop on any failure)

1. Pre-upload hash: recompute SHA-256 and require the value above.
2. Media validation: ffprobe matches the specification; full ffmpeg decode succeeds.
3. YouTube channel confirmed by the user.
4. Visibility Unlisted confirmed.
5. Not made for kids confirmed.
6. Embedding enabled confirmed.
7. Signed-out playback check from the Unlisted URL.
8. 1080p availability check (allow processing time).
9. Audio/video synchronization check.
10. Copyright and restriction check shows no claims or restrictions.
11. Caption decision: optional SRT `submission\final-support\MATCHPULSE_CAPTIONS_SUBMISSION_HOSTED.srt`; the user decides. Verify any upload matches the Lily narration timing.
12. Thumbnail decision: default or user-supplied, user decides.
13. Final URL capture and record in the portal worksheet.
14. Update `PORTAL_SUBMISSION_WORKSHEET.md` with the verified URL.

Required disclosure: Foundry runtime is disabled in the submitted MatchPulse deployment and the workflow makes zero model calls. The video does not demonstrate Foundry usage.

## Authorization wording

> `AUTHORIZE_YOUTUBE_UPLOAD_UNLISTED_LILY_V1` — upload the exact file above to my confirmed YouTube channel as Unlisted with the metadata above.

This packet does **not** authorize challenge submission, repository push, Public visibility, or any media change. Do not alter, remux, or replace the video.

Extended detail: [`AUTHORIZATION/PACKET_VIDEO_UPLOAD.md`](AUTHORIZATION/PACKET_VIDEO_UPLOAD.md).
