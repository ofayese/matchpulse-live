# Authorization packet — final challenge submission

**Status: preparation only. No portal entry or challenge submission is authorized.** `CHALLENGE_SUBMISSION_READY=NO` until every requirement below passes.

## Entry fields

- Project: MatchPulse Live
- Entrant type: Individual
- Display name: Olaolu Fayese
- Team: Not applicable
- Country: United States
- Repository: https://github.com/ofayese/matchpulse-live
- Video URL: `<VERIFIED_YOUTUBE_URL_REQUIRED>`
- Core positioning: MatchPulse Live transforms synthetic football events into explainable, audience-specific match intelligence for broadcast and streaming experiences.

Legal name, contact, and eligibility values are portal-only and are not recorded in the repository.

## Final video

- `submission\matchpulse-submission-hosted-elevenlabs-lily-v1-candidate.mp4`, SHA-256 `f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`; not yet uploaded.
- Third-party declaration: `THIRD_PARTY_RIGHTS_DECLARATION=YES`; narration is ElevenLabs Starter stock voice Lily, generated during the paid subscription, no cloning, no Beta service (`ELEVENLABS_PAID_COMMERCIAL_LICENSE`). Kokoro is superseded and not part of the submission.

## Requirements before submission

- Repository pushed and publicly verified at the final revision.
- Final YouTube URL verified and signed-out playback verified.
- Portal preview verified.
- All entrant and legal declarations completed by the user in the portal.
- Third-party rights declaration reviewed personally.
- Azure facts: public ingress disabled; MatchPulse Foundry runtime off; zero model calls; deployed image digest unchanged. The resource group holds seven resources (five MatchPulse, two user-authorized Foundry development resources with no MatchPulse runtime dependency; the Hosted Agents Preview 403 is a nonblocking optional-integration warning).
- Current portal requirements and deadline (October 27, 2026, 11:59 PM Pacific) rechecked.

## Authorization wording

> `AUTHORIZE_CHALLENGE_SUBMISSION_MATCHPULSE_LIVE` — submit with the verified repository and YouTube URL after I have reviewed the portal preview.

Do not enter, attest, or submit without this separate explicit authorization. Details: [`AUTHORIZATION/PACKET_CHALLENGE_SUBMISSION.md`](AUTHORIZATION/PACKET_CHALLENGE_SUBMISSION.md).

## Verified YouTube URL
https://www.youtube.com/watch?v=O5gHkl_UFHc (Unlisted, @iwadev). Human signed-out playback spot-check still pending.

- Challenge submission attempt (2026-10-27): AUTHORIZE_CHALLENGE_SUBMISSION_MATCHPULSE_LILY received. Portal (Microsoft Innovation Studio) requires Microsoft account sign-in; browser session unauthenticated, sign-in not completed. No draft opened, no form entered, NOT SUBMITTED. Video/repo unchanged. Next: user completes portal sign-in in the open browser tab, then re-issue.

[2026-10-27T18:15:31Z] PORTAL: Innovation Studio project created (ID 127196, https://innovationstudio.microsoft.com/hackathons/insidethegamedeveloperhackathon/project/127196). Title, tagline, 12 keywords, description (repo + YouTube links), challenge 'The Synthetic Match Insights Engine for Premier League Studio', Writing Code=Yes, code repo link saved. Portal video field accepts file upload only (Azure Video Indexer); NOT used (no second upload authorized). No separate Submit step found; project page is the entry. Git index/repo/Azure unchanged.


[2026-10-27T18:23:26Z] PORTAL MEDIA: Approved Lily MP4 (sha256 f06bb7df...b786, verified before upload) uploaded once to project 127196 video field; portal reports 'Video is being processed' (Azure Video Indexer). Cover image (title card + frame crop from approved video, synthetic-data label, alt text) saved and displayed. No separate Submit/Publish action exists (Manage menu: Change log/Clone/Delete only); project page is the entry. Caveat: YouTube demo is Unlisted while rules ask for a public URL; user instructed not to make Public. No new project, no duplicate upload, no Azure or git changes.

[2026-10-27T19:22:00Z] EXECUTION RESULT (premium image): new premium image (sha256 01DF24BC...DB22B506, 1152x768) uploaded with accessible alt text, saved; old title card removed. Portal video (count 1) not yet playable; card still shows default placeholder. No separate Submit action exists; PROJECT_SAVE_IS_SUBMISSION per official rules, no explicit confirmation badge. YouTube remains Unlisted. No Azure/git/index changes.

[2026-10-27T19:55:00Z] EXECUTION RESULT (portal video repair): failed portal video removed (diagnosis PORTAL_TRANSCODE_OUTPUT_MISSING); one derivative (sha256 02CDB90D1AFC38F24725CB6A3EE663B93732DCB0B613B79EE8B54703BCC69C3B, validated H.264 High L4.1 yuv420p CFR30 AAC-LC 48k stereo faststart, 115.000 s) uploaded once at ~19:43Z; still 'No compatible source' at ~10 min. Master f06bb7df...b786 unchanged. No third upload; support escalation required (not sent at that point). Premium image attached.

[2026-10-27T20:51:00Z] SUPPORT REQUEST: Authorized single support request submitted via Innovation Studio Help & Feedback → Report a problem, concerning project 127196. Portal confirmation: “Feedback submitted successfully! Thank you for submitting your feedback. There is no further action required.” No ticket/case ID, follow-up channel, or response time was provided. Project still exists; video still does not play; premium image, repository and YouTube links remain. No further uploads or project changes.

[2026-10-27T21:04:00Z] DUPLICATE PREVENTION: The prior 20:51Z support request is the one authorized private request and already covers the same issue. No new request or follow-up was sent. Challenge-entry status remains unconfirmed pending support confirmation; no separate final Submit action was observed. Screenshot count 0; case ID and response channel/time not provided.
