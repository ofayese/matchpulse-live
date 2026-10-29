# Voice rights determination

## Active ElevenLabs Lily candidate

```text
TTS_PROVIDER=ELEVENLABS
ELEVENLABS_PLAN=STARTER
ELEVENLABS_COMMERCIAL_LICENSE=YES
ELEVENLABS_GENERATION_DURING_PAID_SUBSCRIPTION=YES
ELEVENLABS_STOCK_VOICE=YES
ELEVENLABS_VOICE_NAME=Lily
ELEVENLABS_VOICE_ID=pFZP5JQG7iQjIQuC4Bku
ELEVENLABS_MODEL=eleven_multilingual_v2
ELEVENLABS_VARIANT=MEASURED_CONVERSATIONAL
ELEVENLABS_VOICE_CLONING_USED=NO
ELEVENLABS_BETA_SERVICE_USED=NO
VOICE_RIGHTS_CONCLUSION=ELEVENLABS_PAID_COMMERCIAL_LICENSE
THIRD_PARTY_RIGHTS_DECLARATION=YES
```

**Active file:** `submission\matchpulse-submission-hosted-elevenlabs-lily-v1-candidate.mp4`  
**SHA-256:** `f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`  
**Narration WAV SHA-256:** `0f5402de527d1725c5fb8ed7a4ef97f384c7af405468e8ee4e33f002fc100ded`

**Human approval:** The reviewer watched the complete video and confirmed
"The video is good, and the voice matches" (`APPROVE_ELEVENLABS_LILY_V1`;
`HUMAN_ELEVENLABS_REVIEW_COMPLETED=YES`, `HUMAN_VIDEO_REVIEW_COMPLETED=YES`).

**Basis (checked against local records):** the full narration was generated
on 2026-10-27 UTC during an active ElevenLabs Starter (paid) subscription;
Lily is a stock/premade voice with the ID above; the stable
`eleven_multilingual_v2` model was used; no voice cloning, community voice, or
Beta service was used; the entrant owns or has rights to the narration text and
original MatchPulse visuals; only generated audio is distributed (no
ElevenLabs or Kokoro weights); no prohibited use is implicated. The applicable
ElevenLabs Terms of Service, Prohibited Use Policy, and commercial-use
documentation should be re-read by the entrant before final declaration.
The generation manifest (`submission\final-support\matchpulse-hosted-narration-elevenlabs-lily-v1.manifest.json`,
SHA-256 `9f037d0dbe369ce87577b48aab9b81b2e5fdc16283b9700d326e35ca26b491f8`)
is a frozen pre-approval record and still shows `PENDING_HUMAN_APPROVAL`;
the approval is recorded here and in `FINAL_VIDEO_APPROVAL.md`.

These terms apply only to the ElevenLabs-generated narration. They do **not**
apply retroactively to Kokoro or `bf_emma`.

## Historical Kokoro candidate

```text
KOKORO_VOICE_RIGHTS_CONCLUSION=RIGHTS_UNRESOLVED
KOKORO_CANDIDATE_STATUS=SUPERSEDED_FOR_RIGHTS_CERTAINTY
```

The material below is the preserved historical analysis. The Kokoro candidate
is archived under `submission\archive\`, NOT FOR SUBMISSION.

# Kokoro `bf_emma` rights determination (historical)

**Decision:** `VOICE_RIGHTS_CONCLUSION=RIGHTS_UNRESOLVED` (historical; superseded by the active conclusion above)  
**Declaration:** `THIRD_PARTY_RIGHTS_DECLARATION=PENDING_RIGHTS_REMEDIATION` (historical)  
**Review date:** 2026-10-26  
**Archived file:** `submission\archive\videos\matchpulse-submission-hosted-kokoro-conversational-v2-candidate.mp4`  
**SHA-256:** `b89c016d8d0c790ae42b3a761d6ec7f709cfa988159649c4cf0e07eb8906dcbf`

The approved candidate contains generated narration using Kokoro-82M,
`kokoro-v1.0`, and voice `bf_emma`. It contains generated audio only, not
model or voice weights. The exact local voice archive is the ONNX release
asset `voices-v1.0.bin`. No reviewed primary authority explicitly grants
public distribution of this voice's generated audio or clears its use in a
prize-bearing promotional hackathon entry. The video remains local and
unmodified.

## Required questions

| # | Question | Determination from primary evidence |
|---|---|---|
| 1 | Under what license are the official Kokoro-82M model weights distributed? | The official Kokoro repository and the official Hugging Face model card declare Apache License 2.0 for Kokoro's model weights. This supports use and redistribution of the covered upstream model material subject to Apache-2.0 conditions; it is not an output/voice-likeness grant. |
| 2 | What license covers the ONNX conversion used locally? | The `kokoro-onnx` software repository is MIT-licensed. Its `model-files-v1.0` release says the ONNX binaries are optimized versions from `taylorchu/kokoro-onnx` v0.2.0, but neither conversion release gives an explicit asset-specific license for the ONNX binary. The software MIT license does not itself license converted weights. The upstream Kokoro weights are Apache-2.0; whether those terms and required notices are correctly carried through this specific distributed conversion is not stated by the asset release. |
| 3 | What primary source establishes the license for `voices-v1.0.bin`? | None found. The official v1.0 release describes the file as an NPZ-style archive of style vectors, but provides no asset-specific license or rights statement. GitHub release API metadata reports no digest (`digest: null`). |
| 4 | Is `bf_emma` explicitly included among those licensed voice assets? | The upstream Apache-declared Hugging Face repository lists `voices/bf_emma.pt`, and its official `VOICES.md` lists the `bf_emma` British-English voice. That is evidence about the upstream per-voice file in that repository. It is not an explicit license grant for the separate repackaged `voices-v1.0.bin` archive actually used locally, nor a voice-specific publicity/likeness grant. |
| 5 | Are there separate terms for the underlying speaker or training data? | The model card says training used permissive/non-copyrighted audio, and discloses Koniwa `tnc` (CC BY 3.0) and SIWIS (CC BY 4.0) contributions. It does not map those corpora to `bf_emma`, identify this voice's source speaker, or document speaker consent, voice-likeness, or voice-specific dataset terms. Those rights remain unresolved. |
| 6 | Is use of `bf_emma` permitted for a public, prize-bearing hackathon entry? | Not established. The model/repository license and voice list do not expressly clear this voice's generated narration for public promotional or prize-bearing use. |
| 7 | May generated audio be distributed publicly? | No explicit output grant or prohibition was found in the cited model card, voice list, ONNX release, or conversion-software license. Silence does not establish permission. Public distribution is not cleared. |
| 8 | May generated audio be published on YouTube? | Not established by the primary sources reviewed. No cited Kokoro authority expressly authorizes YouTube publication of generated `bf_emma` audio. Platform upload capability is not a rights grant. |
| 9 | Is attribution required in the video, description, repository, or notices? | No primary source reviewed requires attribution for generated audio as such. Apache-2.0 notice and license conditions apply when redistributing covered Apache materials; MIT notice applies when redistributing covered conversion software. The training card's CC BY dataset acknowledgements do not map the data to `bf_emma` or specify an output-credit requirement. Attribution alone would not resolve missing rights. |
| 10 | Are model or voice weights prohibited from redistribution? | Not categorically for the upstream Kokoro model/voice files covered by its Apache-2.0 declaration: that license permits redistribution subject to its conditions. For the exact ONNX conversion and `voices-v1.0.bin` release assets, no explicit asset-specific grant was found, so redistribution of those binaries is not cleared here. This review does not conclude that an express prohibition exists. |
| 11 | Does the final MatchPulse package distribute weights, or only generated audio? | The approved MP4 carries generated audio only. The MatchPulse source/package does not include `.onnx`, `.bin`, `.pt`, or `.pth` weights. Do not add any weights to the submission. |
| 12 | Is any material evidence missing? | Yes: a direct license/rights statement for the exact ONNX and `voices-v1.0.bin` assets; a verified voice-archive digest and complete transformation/provenance record; `bf_emma` source-speaker and voice-specific dataset/consent/likeness terms; and an explicit license or permission for generated-output distribution, promotional/prize-bearing use, and YouTube publication. |

## Primary sources checked

- [Official Kokoro repository](https://github.com/hexgrad/kokoro) and its
  [Apache-2.0 LICENSE](https://github.com/hexgrad/kokoro/blob/main/LICENSE).
- [Official Kokoro-82M model card](https://huggingface.co/hexgrad/Kokoro-82M)
  and [model API metadata](https://huggingface.co/api/models/hexgrad/Kokoro-82M):
  card metadata declares `apache-2.0`; its body describes Apache-licensed
  weights, training data, and the disclosed CC BY contributions.
- Official [`VOICES.md`](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md)
  and upstream [`voices/bf_emma.pt`](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/voices/bf_emma.pt).
- [`kokoro-onnx` repository](https://github.com/thewh1teagle/kokoro-onnx),
  its [MIT software LICENSE](https://github.com/thewh1teagle/kokoro-onnx/blob/main/LICENSE),
  and the [official `model-files-v1.0` release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0).
  The release states that its ONNX variants are optimized from the
  [`taylorchu/kokoro-onnx` v0.2.0 release](https://github.com/taylorchu/kokoro-onnx/releases/tag/v0.2.0);
  it describes `voices-v1.0.bin` contents but does not state an asset license.
- [Official v1.0 release API metadata](https://api.github.com/repos/thewh1teagle/kokoro-onnx/releases/tags/model-files-v1.0):
  checked the asset metadata; no SHA-256 digest is published for the archive.

The local Docker TTS service is not used as evidence for model or asset
licensing. Its code license covers its code, not independently distributed
model/voice assets or generated-output rights.

## Unexecuted fallback — ElevenLabs Starter

ElevenLabs CLI onboarding and a limited set of British stock-voice auditions
were completed using an active Starter subscription. The available local
auditions do not cover all four documented candidates, and a production
voice/variant has not been selected. No full narration, candidate video, or
remux was generated; no upload or challenge submission occurred. The short
auditions are local review material only and do not change the Kokoro rights
conclusion. Revalidate current paid-plan eligibility and applicable terms
before generating any remaining auditions. Do not use the Free plan. A human
voice selection and separate authorization are required before full
synthesis or remux.

ElevenLabs' official [pricing page](https://elevenlabs.io/pricing) currently
lists Starter as a paid plan with a Commercial License. Its official
[publishing guidance](https://elevenlabs.io/docs/help-center/legal/can-i-publish-the-content-i-generate-on-the-platform.md)
says paid-plan outputs generated during the subscription can be used
commercially, subject to the Terms of Service, Prohibited Use Policy,
service-specific terms, and the user's own necessary IP rights; it excludes
Beta Services and says attribution depends on the agreement. This supports
the fallback plan only conditionally; it is not blanket clearance for every
voice or for an unreviewed output.

1. **Rights preflight:** Before paying or generating, review the live Starter
   plan, current non-beta Text-to-Speech terms, service-specific terms,
   prohibited-use policy, and the selected voice's individual terms. Use
   only a built-in stock British-English voice (no voice clone, Voice Design,
   Voice Library voice with unclear terms, or Beta feature) whose current
   terms permit this exact public promotional/prize-bearing use. Record the
   voice name/ID, date, subscription plan/status, terms URLs/version, and
   receipt locally. If any condition is unclear, stop and do not generate.
2. **Preserve the script:** Use the existing ten-unit script
   `submission\final-support\MATCHPULSE_NARRATION_CONVERSATIONAL_V2.json`
   unchanged (SHA-256
   `9930d8b267fc881f48d43537d1b3a999e003e9024e27c04b316a9fc3c7d3c3e2`).
   Generate speech for units 1–10 using each unit's
   `revised_spoken_text` and existing `spoken_segments`/pause sequence.
   Generate while Starter is active and signed in; retain only the necessary
   account-side evidence and never place credentials/API keys in the
   repository or audit log. Do not use any output created on Free.
3. **Create new local candidates, never overwrite:**
   - Audio:
     `submission\final-support\matchpulse-hosted-narration-elevenlabs-starter-british-v1.wav`
   - Manifest/rights record:
     `submission\final-support\matchpulse-hosted-narration-elevenlabs-starter-british-v1.manifest.json`
   - Video candidate:
     `submission\final-support\matchpulse-submission-hosted-elevenlabs-starter-british-v1-candidate.mp4`
   Refuse to overwrite any existing path. Keep the approved V2 MP4 and its
   SHA-256 untouched.
4. **Align the ten units:** Assemble the ten recordings against the existing
   115-second visual timeline using the ten unit boundaries and cue mapping
   in the script. Fit pauses/speed without changing the words; if a unit
   cannot fit naturally, stop for separate script/edit approval. Produce a
   48 kHz stereo WAV with the full 115-second timeline. Do not attach the
   known-stale SRT; make any captions from the final spoken words and review
   them independently.
5. **Audio-only remux after authorization:** Use the approved V2 video as
   input and copy only its encoded video stream; map the new WAV as audio and
   encode AAC at 48 kHz stereo. Example PowerShell command (not executed):

   ```powershell
   ffmpeg -hide_banner -loglevel error -nostdin -n `
     -i .\submission\matchpulse-submission-hosted-kokoro-conversational-v2-candidate.mp4 `
     -i .\submission\final-support\matchpulse-hosted-narration-elevenlabs-starter-british-v1.wav `
     -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k `
     -ar 48000 -ac 2 -t 115 -movflags +faststart `
     .\submission\final-support\matchpulse-submission-hosted-elevenlabs-starter-british-v1-candidate.mp4
   ```

6. **Technical verification:** Confirm the source and new candidate's
   encoded video-stream MD5 both equal
   `c85bef1de55944edebd4f4d003c70b59`; candidate duration is 115 seconds;
   video is H.264 1920x1080/30 fps; audio is AAC 48 kHz stereo; full decode
   passes; integrated loudness is near -16 LUFS and true peak no higher than
   the approved-media ceiling; new candidate SHA-256 is recorded. Confirm
   the original approved MP4 still has SHA-256
   `b89c016d8d0c790ae42b3a761d6ec7f709cfa988159649c4cf0e07eb8906dcbf`.
7. **Human review and release gate:** Listen to the complete new narration
   and video, check all ten units for pronunciation, pacing, clipping,
   timing, intelligibility, and factual accuracy, and review captions if
   used. Obtain entrant approval and separately re-check rights/terms,
   challenge host acceptance, channel, and upload authorization. Only then
   may the new candidate replace the old one as the proposed upload file;
   never describe it as the already-approved V2 candidate. Do not upload
   under this plan.

## Current gate

Keep `RIGHTS_UNRESOLVED` and
`THIRD_PARTY_RIGHTS_DECLARATION=PENDING_RIGHTS_REMEDIATION`. Paid-plan
onboarding is complete, but the existing short auditions cover only a subset
of four documented candidates. No production voice has been selected and no
full narration or remux has been generated. These steps do not clear rights;
revalidate eligibility before any remaining auditions and reassess only
after the selected voice, applicable terms, generated output, technical
review, and human approval are documented.
