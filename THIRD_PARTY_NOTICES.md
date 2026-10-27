# Third-Party Notices — Local TTS and Final-Video Narration

## Active final-video narration — ElevenLabs

| Component | Status |
|---|---|
| ElevenLabs text-to-speech service, **Starter** (paid) plan | The final submission narration was generated on 2026-10-27 UTC during an active paid subscription. Model: stable `eleven_multilingual_v2`. Voice: stock/premade **Lily**, voice ID `pFZP5JQG7iQjIQuC4Bku`. No voice cloning, no community voice, no Beta service. |
| Distribution | Generated audio only, embedded in the submission MP4. No ElevenLabs model or voice weights are redistributed. |
| Basis | `VOICE_RIGHTS_CONCLUSION=ELEVENLABS_PAID_COMMERCIAL_LICENSE`; commercial use of content generated on paid plans under the [ElevenLabs Terms of Service](https://elevenlabs.io/terms-of-use), [Prohibited Use Policy](https://elevenlabs.io/use-policy), and [publishing guidance](https://elevenlabs.io/docs/help-center/legal/can-i-publish-the-content-i-generate-on-the-platform). The entrant should re-read the current terms before the final declaration. |

These terms apply only to the ElevenLabs-generated narration and do not apply to Kokoro or `bf_emma`.

## Historical Kokoro development notice (superseded, unresolved)

**Kokoro rights status: RIGHTS_UNRESOLVED** (`KOKORO_CANDIDATE_STATUS=SUPERSEDED_FOR_RIGHTS_CERTAINTY`). The Kokoro candidate is archived and not part of the submission. The permissive licenses for the Kokoro model and software do not establish the license or promotional-use rights for the separately distributed voice assets. Do not treat this notice as clearance to redistribute the model/voice files or publish a promotional recording using `bf_emma`.

| Component | Declared license / status | Source and use |
|---|---|---|
| Kokoro-82M model and upstream `voices/bf_emma.pt` | Apache-2.0 declared by the official Kokoro GitHub repository and Hugging Face model card. The upstream model repo lists `voices/bf_emma.pt`; this does not establish speaker/likeness rights or license the separate repackaged archive used by the local service. | [Official Kokoro repository and LICENSE](https://github.com/hexgrad/kokoro) · [model card](https://huggingface.co/hexgrad/Kokoro-82M) · [voice list](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md). |
| `kokoro-onnx` software | MIT, as declared by its repository. The service specifies `kokoro-onnx>=0.5.0`, not an exact version. | [Repository](https://github.com/thewh1teagle/kokoro-onnx) · [MIT license](https://github.com/thewh1teagle/kokoro-onnx/blob/main/LICENSE). |
| Local TTS service | MIT at source commit `82fae01c1e9f9e213eb71ae02602311b42c5bc68`. | [Source at commit](https://github.com/letuhao/local-tts-service/tree/82fae01c1e9f9e213eb71ae02602311b42c5bc68) · [license at commit](https://github.com/letuhao/local-tts-service/blob/82fae01c1e9f9e213eb71ae02602311b42c5bc68/LICENSE). |
| ONNX model `kokoro-v1.0.onnx`, voice archive `voices-v1.0.bin`, and generated `bf_emma` audio | The conversion release describes the ONNX binary as optimized from `taylorchu/kokoro-onnx` v0.2.0, but gives no explicit asset-specific license. The voice archive release provides no license or published digest. No primary source expressly grants public or promotional distribution of generated `bf_emma` audio, including YouTube. **Rights unresolved; do not redistribute these binaries or publish the current audio pending documented clearance.** | [ONNX v1.0 release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0) · [release API metadata](https://api.github.com/repos/thewh1teagle/kokoro-onnx/releases/tags/model-files-v1.0) · [`bf_emma` voice list](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md). |

For redistribution of Apache-2.0 or MIT **code/model materials where those licenses apply**, retain the applicable license and copyright notices and follow the relevant license terms. No such notice substitutes for permission to redistribute the ONNX/voice binaries. The v1.0 release API did not report asset digests; the project does not pin their SHA-256 values. No model or voice binaries are committed by this project; the service instructions call for obtaining assets separately. The local hackathon video use is not cleared by the code licenses alone.

An independent re-verification against primary sources (Hugging Face model API/card, `VOICES.md`, the GitHub Releases API for `model-files-v1.0`, and upstream repository licenses) was performed on 2026-10-26. The Hugging Face model repository's `/LICENSE` path returns 404; the separate official Kokoro GitHub source repository has an Apache-2.0 LICENSE. The v1.0 release asset API reports `"digest": null` for assets. See the "Independent re-verification (2026-10-26)" section of `docs/LOCAL_TTS_PROVENANCE.md` for the queried endpoints and details.

## Final generated-audio determination (2026-10-26)

`VOICE_RIGHTS_CONCLUSION=RIGHTS_UNRESOLVED` and
`THIRD_PARTY_RIGHTS_DECLARATION=PENDING_RIGHTS_REMEDIATION`. The official
Kokoro model card says training used permissive/non-copyrighted data and
discloses Koniwa `tnc` (CC BY 3.0) and SIWIS (CC BY 4.0), but does not map
those corpora or any source speaker to `bf_emma`. It provides no explicit
generated-audio distribution, promotional, prize-bearing, YouTube, or
output-attribution terms. Apache-2.0 applies to the upstream model material
as declared; it is not itself proof of the separate voice archive's terms,
speaker/likeness permission, or generated-output rights.

The approved MatchPulse MP4 carries generated audio only and no model or
voice weights are part of the MatchPulse package. The package does not
include `.onnx`, `.bin`, `.pt`, or `.pth` assets. Do not redistribute
weights from the local setup. See
[`submission/VOICE_RIGHTS_DECISION.md`](submission/VOICE_RIGHTS_DECISION.md)
for the question-by-question determination and the authorization-gated
ElevenLabs Starter alternative. CLI onboarding and bounded short auditions
are complete, but production voice selection, full narration, and
publication remain pending.
