# Optional ElevenLabs narration

## Purpose and boundary

ElevenLabs is an optional, local narration-authoring path for MatchPulse
submission media. It is not a dependency of the deployed MatchPulse runtime,
does not add provider calls to event processing, and does not change the
immutable deployed image or Azure configuration.

The existing conversational script and media pipeline remain authoritative:

- `submission/final-support/MATCHPULSE_NARRATION_CONVERSATIONAL_V2.json`
  contains the ten approved thought units.
- `scripts/matchpulse_conversational_tts.py` owns the existing timing and
  assembly conventions.
- `scripts/record_matchpulse_hosted_submission.py` owns visual-source checks,
  remuxing, and final media validation.
- `scripts/matchpulse_elevenlabs_tts.py` provides optional account/model
  preflight, stock-voice discovery, and bounded audition synthesis.

Do not add a competing timing, mastering, or remux implementation; reuse the
existing pipeline.

## Rights and provider policy

The final submission narration was generated with ElevenLabs under an active
paid Starter plan, using the stock voice Lily and the stable model
`eleven_multilingual_v2`, which provides the commercial-license path for that
output. The path is conditional on the terms, use policy, and voice
restrictions in force at generation time and on the entrant's own rights to
the script and visuals. It is not a blanket clearance and does not extend to
any other TTS provider's output.

Use only stock/premade voices and stable, non-Beta text-to-speech models.
Voice cloning, community voices with separate or unclear terms, Beta
services, voice changer, speech-to-speech cloning, dubbing, music, and
telephony are outside this workflow.

The currently tested stable model is `eleven_multilingual_v2`; confirm it is
still listed as generally available and compatible before each generation.
The pinned British stock-voice candidates from the onboarding work are:

| Candidate | Voice ID |
|---|---|
| Daniel - Steady Broadcaster | `onwK4e9ZLuTAKqWW03F9` |
| George - Warm, Captivating Storyteller | `JBFqnCBsd6RMkjVDRZzb` |
| Alice - Clear, Engaging Educator | `Xb7hH8MSUJpSbSDYk0k2` |
| Lily - Velvety Actress | `pFZP5JQG7iQjIQuC4Bku` |

Lily was the human-selected and human-approved production voice. For any new
generation, re-query the voice against the authenticated account and review
category, metadata, model compatibility, access, and restrictions first.

Final status:

```text
ELEVENLABS_PLAN=STARTER
ELEVENLABS_COMMERCIAL_LICENSE=YES
ELEVENLABS_STOCK_VOICE=YES
ELEVENLABS_VOICE_NAME=Lily
ELEVENLABS_VOICE_CLONING_USED=NO
ELEVENLABS_BETA_SERVICE_USED=NO
ELEVENLABS_FULL_GENERATION_EXECUTED=YES
```

## Onboarding and authentication

The official CLI onboarding command is:

```powershell
npx -y @elevenlabs/cli@latest onboard init
```

Review every proposed file and configuration change before accepting it.
The `-y` flag approves execution of the named npm package only; it does not
approve generated files, deployment, uploads, or Git operations. Do not
install the CLI globally or run unrelated lifecycle/deployment scripts.

Install the optional Python integration with:

```powershell
python -m pip install -e ".[narration]"
```

Supply `ELEVENLABS_API_KEY` through the process environment or an ignored,
operator-controlled local secret mechanism. `.env.example` contains only a
placeholder. Never commit `.env`, print or log the key, include it in
arguments, manifests, screenshots, audit records, or browser code, or expose
provider request headers and raw error bodies. If a key is exposed, stop and
revoke it through the account owner.

## Audition and human selection

Verify the active paid Starter plan, remaining generation budget, stable
model availability, and each pinned voice's current account availability,
premade category, British-English metadata, model compatibility, and
displayed restrictions before synthesis. Do not infer an accent from a voice
name. Fail closed if eligibility cannot be verified.

Auditions must use the same approved synthetic script and comparable voice
settings. Keep raw and normalized review samples in an operating-system
temporary directory outside the repository and `submission`; do not upload
or commit them. Validate response type, nonempty audio, full decode, duration,
sample rate, channels, loudness, true peak, and SHA-256. Retain failed samples
with a clear noncompliant label rather than overwriting evidence.

Assess pronunciation by listening, including “MatchPulse,” “Azure Container
Apps,” “Northbridge City,” “Harbor United,” “analyst,” “broadcaster,”
“deterministic,” and “Foundry.” Automated metadata cannot establish
pronunciation quality. Do not choose a production voice automatically; wait
for an explicit human voice-and-variant selection.

## Render requirements

A new full render requires a human-selected eligible stock voice and variant.
Use the unchanged ten thought units and their approved visual windows. The
planned narration targets approximately 113 seconds of speech on a 115-second
timeline, with at least 500 ms of closing silence. Master to 48 kHz stereo,
approximately -16 LUFS integrated and approximately -2 dBTP, without
clipping or unnatural time stretching.

Use the hosted visual source as the video input and copy the video stream;
do not re-encode or use a previously narrated candidate as the source.
Require a collision-free output path, matching source/script hashes, full
audio/video decode, expected video-stream MD5, technical checks, and human
review before any promotion.

YouTube upload, challenge entry, and any final publication require separate
human authorization. This document and a voice audition do not grant that
authorization.

## Safe disablement

This integration is local authoring tooling, not a production TTS service.
Disable further synthesis by removing `ELEVENLABS_API_KEY` from the process
environment and not invoking the audition tool. Revoke the account key only
if it is exposed or the account owner directs revocation. Do not alter the
MatchPulse runtime, Azure resources, or deployed image to disable this
optional tooling.

## Documentation sources

Recheck current provider requirements before each authorized generation:

- <https://elevenlabs.io/pricing>
- <https://elevenlabs.io/terms>
- <https://elevenlabs.io/use-policy>
- <https://elevenlabs.io/service-specific-terms>
- <https://elevenlabs.io/docs/api-reference/authentication>
- <https://elevenlabs.io/docs/eleven-api/quickstart>
- <https://elevenlabs.io/docs/help-center/legal/can-i-publish-the-content-i-generate-on-the-platform>

## Lily V1 final video (human-approved)

The human reviewer approved the complete video and voice ("The video is good, and the voice matches").
A full narration was generated on 2026-10-27 UTC with the stock ElevenLabs voice Lily (`pFZP5JQG7iQjIQuC4Bku`),
variant `MEASURED_CONVERSATIONAL`, stable model `eleven_multilingual_v2`, using `scripts/matchpulse_elevenlabs_render.py`.

- TTS_PROVIDER=ELEVENLABS
- ELEVENLABS_PLAN=STARTER
- ELEVENLABS_COMMERCIAL_LICENSE=YES
- ELEVENLABS_VOICE_NAME=Lily
- ELEVENLABS_VOICE_ID=pFZP5JQG7iQjIQuC4Bku
- ELEVENLABS_VARIANT=MEASURED_CONVERSATIONAL
- ELEVENLABS_STOCK_VOICE=YES
- ELEVENLABS_VOICE_CLONING_USED=NO
- ELEVENLABS_BETA_SERVICE_USED=NO
- ELEVENLABS_GENERATION_DURING_PAID_SUBSCRIPTION=YES
- VOICE_RIGHTS_CONCLUSION=ELEVENLABS_PAID_COMMERCIAL_LICENSE
- THIRD_PARTY_RIGHTS_DECLARATION=YES
- HUMAN_ELEVENLABS_REVIEW_COMPLETED=YES
- A separate, superseded local Kokoro candidate is documented only in the provenance record; ElevenLabs terms do not apply to it

Approved artifacts (Git-ignored media):

| Artifact | Path | SHA-256 |
|---|---|---|
| Final MP4 | `submission/matchpulse-submission-hosted-elevenlabs-lily-v1-candidate.mp4` | `f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786` |
| Narration WAV | `submission/final-support/matchpulse-hosted-narration-elevenlabs-lily-v1.wav` | `0f5402de527d1725c5fb8ed7a4ef97f384c7af405468e8ee4e33f002fc100ded` |
| Generation manifest | `submission/final-support/matchpulse-hosted-narration-elevenlabs-lily-v1.manifest.json` | `9f037d0dbe369ce87577b48aab9b81b2e5fdc16283b9700d326e35ca26b491f8` |

The manifest is a frozen pre-approval generation record and still reads `PENDING_HUMAN_APPROVAL`; approval is recorded in
`submission/FINAL_VIDEO_APPROVAL.md`. The video stream was copied from the hosted visual source (no re-encode). Speed was raised from
0.98 up to 1.12 on units that did not fit their windows; no wording changed and no pronunciation aliases were used. The render script's
default output paths are the pre-promotion top-level locations; the WAV and manifest were moved to `submission/final-support/`.
Cloud TTS is not byte-deterministic, so regeneration is subject to account entitlement and will not reproduce these exact bytes; the hashes above identify the approved assets.
