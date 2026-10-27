# Local TTS Provenance and Rights Review

## Final submission narration: ElevenLabs (active)

Kokoro was used during local development. Publication of a Kokoro-narrated final video was superseded because voice/output rights remain unresolved (`KOKORO_VOICE_RIGHTS_CONCLUSION=RIGHTS_UNRESOLVED`, historical, below). The active final narration was generated through an ElevenLabs Starter (paid) subscription on 2026-10-27 UTC with the stock/premade voice Lily (`pFZP5JQG7iQjIQuC4Bku`) and the `eleven_multilingual_v2` model; no voice cloning was used. The final MP4 distributes generated audio only; no ElevenLabs or Kokoro model or voice weights are committed. The generation tooling (`scripts/matchpulse_elevenlabs_render.py`, `scripts/matchpulse_elevenlabs_tts.py`) is reproducible subject to account entitlement, but cloud TTS output is not deterministic, so exact audio bytes may not be reproduced; the approved WAV (`0f5402de527d1725c5fb8ed7a4ef97f384c7af405468e8ee4e33f002fc100ded`) and MP4 (`f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`) hashes are recorded in `docs/ELEVENLABS_NARRATION.md`. ElevenLabs terms do not retroactively apply to Kokoro.

The sections below are the preserved historical Kokoro review.

## Kokoro primary-source rights determination (2026-10-26; historical, superseded)

`VOICE_RIGHTS_CONCLUSION=RIGHTS_UNRESOLVED`.

- The official [Kokoro repository](https://github.com/hexgrad/kokoro)
  publishes an Apache-2.0 LICENSE, and its linked
  [Kokoro-82M model card](https://huggingface.co/hexgrad/Kokoro-82M)
  declares `apache-2.0` and describes Apache-licensed weights.
- The upstream Hugging Face repository lists `voices/bf_emma.pt` and
  `VOICES.md` identifies `bf_emma`; this is not the separately repackaged
  `voices-v1.0.bin` used locally. The
  [official ONNX v1.0 release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0)
  describes the ONNX variants as optimized from `taylorchu/kokoro-onnx`
  v0.2.0. Its software repository is MIT-licensed, but the release gives no
  explicit license for the converted ONNX or voice archive assets.
- The release describes `voices-v1.0.bin` as an NPZ-style style-vector
  archive and points to the upstream voice names. Its GitHub release API
  metadata reports `digest: null`; no asset license, archive digest, or
  voice-specific grant was found.
- The model card states that training used permissive/non-copyrighted audio
  and acknowledges Koniwa `tnc` (CC BY 3.0) and SIWIS (CC BY 4.0), but does
  not map those sources to `bf_emma` or document speaker consent,
  voice-likeness rights, or generated-output terms.
- No primary source reviewed explicitly permits or prohibits distribution of
  generated audio, or specifically clears prize-bearing promotional use or
  YouTube publication. The absence of such terms is not a grant. No
  generated-audio attribution requirement was identified; Apache/MIT notice
  duties apply when redistributing the materials covered by those licenses.
- The submission distributes generated audio embedded in the approved MP4,
  not model/voice weights. Do not redistribute local weight files. The
  exact approved MP4 remains local. ElevenLabs Starter onboarding and bounded
  short auditions have since been completed, but production voice selection,
  full narration, remux, and publication remain pending. These auditions do
  not change the Kokoro rights conclusion.

  Detailed answers and the authorization-gated ElevenLabs alternative are in
  [`submission/VOICE_RIGHTS_DECISION.md`](../submission/VOICE_RIGHTS_DECISION.md).

**Decision: RIGHTS_UNRESOLVED**

The project’s local audio path is Kokoro-82M through a Dockerized TTS service, using model `kokoro-v1.0`, voice `bf_emma`, and language code `b`. The approved local candidate is a 115-second hackathon demo video. Its approval record says it has not been uploaded; this review does not establish permission to publish it or use it commercially/promotively. The code/model licenses are favorable, but the rights for the voice assets and the voice-specific training data are not established. Do not treat the candidate as rights-cleared for public promotion until those gaps are resolved.

## Independent re-verification (2026-10-26)

A follow-up primary-source check on 2026-10-26 re-queried the sources below directly (no weights downloaded) and found no change to the conclusion:

- **Hugging Face model API** (`https://huggingface.co/api/models/hexgrad/Kokoro-82M`): `cardData.license` = `apache-2.0`, confirmed current as of `lastModified: 2025-04-10T18:12:48.000Z`; `siblings` lists `voices/bf_emma.pt` among the per-voice files in the Apache-2.0-declared Hugging Face model repository. `https://huggingface.co/hexgrad/Kokoro-82M/blob/main/LICENSE` re-confirmed HTTP 404 -- that Hugging Face repository has no separate LICENSE file. The official Kokoro GitHub source repository separately contains an Apache-2.0 LICENSE.
- **`VOICES.md`** (British English table, `lang_code='b'`): `bf_emma` row re-confirmed as Target Quality B, Training Duration HH hours (10-99h), Overall Grade B-, SHA256 `d0a423de` -- matching the full LFS-pointer hash cited in Section 4.
- **Model card body**: re-confirms "This is an Apache-licensed model... We welcome the deployment of the model in real use cases" (a general deployment invitation, not a voice-specific or promotional-recording grant), and the Creative Commons Attribution table listing Koniwa `tnc` (<1h, CC BY 3.0) and SIWIS (<11h, CC BY 4.0) as contributions "Added to Training Set After v0.19 / 22 Nov 2024" -- before the v1.0 training cutoff, but the card does not map either corpus to the `bf_emma` voice specifically.
- **GitHub Releases API** (`model-files-v1.0` tag), re-queried directly: all v1.0 assets (`kokoro-v1.0.onnx` 325,532,387 bytes; `kokoro-v1.0.fp16.onnx`; `kokoro-v1.0.fp16-gpu.onnx`; `kokoro-v1.0.int8.onnx`; `voices-v1.0.bin` 28,214,398 bytes, uploaded by `github-actions[bot]`) report `"digest": null` -- reconfirming no SHA-256 is published for any v1.0 asset, including the voice archive. The release body re-confirms, verbatim, that the ONNX files are "optimized ... version[s] from taylorchu/kokoro-onnx" (release `v0.2.0`) and that `voices-v1.0.bin` is "npz (numpy) key value pairs of style vectors contains the following voices (26)" pointing to `VOICES.md` for names/languages -- no asset-specific license or voice-rights statement appears anywhere in this release body.
- **Service LICENSE at the pinned commit**, fetched raw: re-confirmed standard MIT text, copyright "Le Tu Hao", covering the service source code only -- it does not purport to license the ONNX/voice assets the service loads.

No new voice-specific license, publicity/likeness grant, or commercial/promotional-use permission for `bf_emma` or `voices-v1.0.bin` was found. **This re-verification does not change the decision: RIGHTS_UNRESOLVED.**

## What the project pins and obtains

The checked-in scripts and tests name `kokoro-v1.0` and `bf_emma`; they do not pin a model-asset or voice-asset SHA-256, nor an exact `kokoro-onnx` package version. The service source commit is recorded in project documentation. Its dependency requirement is `kokoro-onnx>=0.5.0`, so the exact resolved package depends on the image/build environment. The service instructions identify the `model-files-v1.0` release and require the model and voice files to be supplied separately. They are not committed to this project. Asset preparation is manual; the service mounts the files and loads the engine for local inference. This is not an automatic download by the application.

## Component findings

### 1. Kokoro-82M upstream model

- **Source URL:** [Hugging Face model](https://huggingface.co/hexgrad/Kokoro-82M)
- **Release / revision:** The model card describes Kokoro v1.0 (released January 2025); the project refers to the semantic name `kokoro-v1.0`, not an immutable Hugging Face revision.
- **Filename:** Upstream checkpoint `kokoro-v1_0.pth`. The local service consumes its ONNX conversion instead.
- **SHA-256:** Upstream model card documents `496dba118d1a58f5f3db2efc88dbdc216e0483fc89fe6e47ee1f2c53f18ad1e4` for that checkpoint. This does **not** authenticate the converted ONNX asset.
- **Declared license / scope:** Apache-2.0, declared in the Hugging Face model card YAML frontmatter (`license: apache-2.0`) and confirmed via the Hugging Face model API (`cardData.license` = `apache-2.0`); the card body also states "This is an Apache-licensed model." The Hugging Face model repository has no standalone `LICENSE` file (`https://huggingface.co/hexgrad/Kokoro-82M/blob/main/LICENSE` returns 404); the official Kokoro GitHub source repository has a separate Apache-2.0 LICENSE. The model-card declaration covers its upstream model material, including listed per-voice `.pt` files, but does not establish terms for each converted/repackaged asset or grant voice likeness/publicity rights.
- **Attribution:** Follow Apache-2.0 notice and license conditions when redistributing covered materials; preserve notices and indicate material changes as required. The license does not by itself specify a credit requirement for an audio-only output.
- **Redistribution / project status:** The original checkpoint is not committed or redistributed by this project; the local service uses the ONNX file. The source requires obtaining local assets separately.
- **Downloaded on demand?:** Not by the application. The project’s service setup requires the user to provide model files before running it.
- **Intended use:** Local synthesis for the hackathon demo video. Apache-2.0 permits broad use of covered model material subject to its terms, but does not clear the unresolved voice-asset rights.
- **Per-voice upstream file (new finding):** The same Hugging Face repository also hosts each voice as an individual file under `voices/`, including `voices/bf_emma.pt`. Fetching only the Git LFS pointer (no weight download) for that path returns `oid sha256:d0a423deabf4a52b4f49318c51742c54e21bb89bbbe9a12141e7758ddb5da701`, size 523420 bytes. This **full SHA-256 matches** the abbreviated checksum `d0a423de` published in `VOICES.md` for `bf_emma`, confirming the upstream per-voice file's identity and that it is part of the Apache-2.0-declared repository. This does **not** by itself establish voice-likeness/publicity rights, and it is a different artifact/format from the `voices-v1.0.bin` archive the project actually uses (see Section 4).
- **Evidence:** [Model card](https://huggingface.co/hexgrad/Kokoro-82M) · [model API metadata (`cardData.license`)](https://huggingface.co/api/models/hexgrad/Kokoro-82M) · [`voices/bf_emma.pt` LFS pointer](https://huggingface.co/hexgrad/Kokoro-82M/raw/main/voices/bf_emma.pt) · [`VOICES.md`](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md).
- **Residual uncertainty:** The upstream checkpoint hash is not the ONNX hash; the project does not pin the conversion output or an immutable model-card revision. The verified `bf_emma.pt` hash authenticates the upstream per-voice file only, not the third-party `voices-v1.0.bin` repackaging the project operationally depends on.

### 2. `kokoro-onnx` conversion/runtime code

- **Source URL:** [thewh1teagle/kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx)
- **Exact version:** The local service dependency is `kokoro-onnx>=0.5.0`; no exact package version or lockfile resolution is recorded in the reviewed project setup.
- **Asset filename / SHA-256:** Not applicable to the library source code. The project does not provide a verified hash for its resolved package artifact.
- **Declared license / scope:** MIT for the repository’s software code ([license](https://github.com/thewh1teagle/kokoro-onnx/blob/main/LICENSE)). This code license is not proof of rights in separately released model weights or voice embeddings.
- **Attribution:** MIT requires retaining its copyright and permission notice when distributing covered software.
- **Redistribution / project status:** The service installs/uses the package as a dependency; the project does not separately vendor the library source. The exact installed version and container image digest are not pinned here.
- **Downloaded on demand?:** Package installation occurs as part of the service image/build process, not a TTS request. Exact package acquisition depends on the build environment.
- **Intended use:** Local model inference for the demo.
- **Evidence:** [Repository](https://github.com/thewh1teagle/kokoro-onnx) · [MIT license](https://github.com/thewh1teagle/kokoro-onnx/blob/main/LICENSE) · [service requirements at pinned commit](https://github.com/letuhao/local-tts-service/blob/82fae01c1e9f9e213eb71ae02602311b42c5bc68/requirements.txt).
- **Residual uncertainty:** Package resolution is not reproducible from an exact version/digest in the project, and the software license does not resolve data/voice rights.

### 3. Converted ONNX model file

- **Source URL:** [ONNX `model-files-v1.0` release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0)
- **Exact release / filename:** Tag `model-files-v1.0`; `kokoro-v1.0.onnx` (325,532,387 bytes per GitHub release-asset metadata).
- **Conversion provenance chain (new finding):** The `model-files-v1.0` release body states the three ONNX variants are "optimized" versions "from [taylorchu/kokoro-onnx](https://github.com/taylorchu/kokoro-onnx/releases/tag/v0.2.0)" -- i.e. `hexgrad/Kokoro-82M` (original PyTorch weights, Apache-2.0) was converted to ONNX by a third party, `taylorchu/kokoro-onnx` (release `v0.2.0`), and then republished under `thewh1teagle/kokoro-onnx`'s `model-files-v1.0` tag. Neither intermediate release page restates an asset-specific license for the converted binary; both repositories carry MIT licenses for their *code*, not an explicit redistribution grant for the converted weights.
- **SHA-256:** **Not verified.** The v1.0 GitHub release asset metadata has no SHA-256 digest, and the project has no pinned value. The upstream model checkpoint hash above is not a substitute. The distinct `model-files-v1.1` release has an API-reported digest for a file with the same filename, but that digest is not evidence for the v1.0 file and is not attributed to this project.
- **Declared license / scope:** The v1.0 release asset does not independently declare an asset-specific license in its metadata. The upstream model card declares Apache-2.0 for Kokoro model material; whether that declaration and its terms fully cover this converted binary should be confirmed with the rights holder if redistribution is intended.
- **Attribution:** No separate asset-level attribution terms were verified. Follow applicable upstream model terms; do not infer a complete asset grant from the MIT license of conversion software.
- **Redistribution / project status:** Not committed to this project. The upstream service instructions direct users to obtain the model file separately; the local Docker setup mounts it.
- **Downloaded on demand?:** Manual/setup-time acquisition, not an application-triggered download. The app uses a locally provided file at inference time.
- **Intended use:** Local synthesis in the hackathon demo. Public distribution of the binary is not cleared.
- **Evidence:** [v1.0 release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0) · [v1.0 release API metadata](https://api.github.com/repos/thewh1teagle/kokoro-onnx/releases/tags/model-files-v1.0) · [v1.1 release API metadata for comparison only](https://api.github.com/repos/thewh1teagle/kokoro-onnx/releases/tags/model-files-v1.1).
- **Residual uncertainty:** No v1.0 file digest, explicit asset-specific terms, or voice-specific rights statement was verified.

### 4. Voice archive and `bf_emma`

- **Source URL:** [ONNX `model-files-v1.0` release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0) supplies `voices-v1.0.bin`; [upstream voice list](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md) documents voice identifiers.
- **Exact release / filename:** `model-files-v1.0`; archive `voices-v1.0.bin`. The project requests voice identifier `bf_emma` (British English).
- **SHA-256:** Archive SHA-256 **not verified**: v1.0 release metadata reports no digest (`"digest": null` in the GitHub Releases API response, confirmed by direct query), and the project has no pinned archive hash. `VOICES.md` lists only the abbreviated checksum `d0a423de` for `bf_emma`; that is not a full SHA-256 and does not authenticate the complete `.bin` archive. A digest reported for a same-named archive in a later release must not be substituted for the v1.0 archive. **Cross-reference (new finding):** the upstream `hexgrad/Kokoro-82M` repository separately hosts the same voice as `voices/bf_emma.pt`, whose Git LFS pointer gives full SHA-256 `d0a423deabf4a52b4f49318c51742c54e21bb89bbbe9a12141e7758ddb5da701` -- consistent with the abbreviated `d0a423de` in `VOICES.md`. That full hash authenticates the **upstream per-voice `.pt` file only**; it is a different file/format than the `voices-v1.0.bin` npz-style archive that `kokoro-onnx`/this project's service actually loads, and it is not evidence for that archive's integrity or for any third-party repackaging/transformation step.
- **Declared license / scope:** The upstream `voices/bf_emma.pt` file sits inside the `hexgrad/Kokoro-82M` repository, which declares `license: apache-2.0` in its card metadata (see Section 1); on its face this covers copyright in that specific upstream file. No separately verified license or permission was found for the third-party-repackaged `voices-v1.0.bin` archive, for voice likeness, or for commercial/promotional output of synthesized speech. A software/model copyright license (Apache-2.0 or MIT) does not establish personality, publicity, or likeness rights in the underlying speaker's voice, nor rights to use a synthesized recording of that voice in public-facing promotional material -- those remain unresolved regardless of the file-level copyright license.
- **Attribution:** No voice-specific attribution requirement or sufficient license terms were found. Attribution alone would not resolve the missing grant.
- **Redistribution / project status:** Not committed to this project. The service instructions require the user to supply the archive; the local setup mounts it. Do not redistribute the archive/embedding until the applicable terms are confirmed.
- **Downloaded on demand?:** The application does not fetch it; it is supplied separately during local setup.
- **Intended use:** `bf_emma` produces the demo video narration. The video approval record identifies it as a British English female voice. Hackathon/public promotional use is not verified as authorized.
- **Evidence:** [voice list](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md) · [v1.0 release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0) · [v1.0 release API metadata](https://api.github.com/repos/thewh1teagle/kokoro-onnx/releases/tags/model-files-v1.0).
- **Residual uncertainty:** The voice list gives a grade, language, estimated duration, and abbreviated checksum, but does not identify a named source dataset/license or grant for `bf_emma`. The voice-specific training corpus and terms, voice/likeness permissions, and generated-audio promotional-use rights remain unresolved. Verifying the upstream `bf_emma.pt` hash narrows -- but does not close -- the gap: it confirms *which* embedding is used and that the specific upstream file is part of an Apache-2.0-declared repository, but it does not confirm the integrity of the project's actual third-party-repackaged `.bin` asset, nor does it supply the missing voice-likeness/publicity and promotional-use rights.

### 5. Voice training data

- **Source URL:** [Kokoro model card](https://huggingface.co/hexgrad/Kokoro-82M) and [voice list](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md).
- **Dataset/version and filename:** The model card describes the aggregate training data; no voice-specific corpus name/file is mapped to `bf_emma` in the reviewed material.
- **SHA-256:** Not verified / not applicable to a voice-specific dataset file; none is pinned by the project.
- **Declared terms / scope:** The model card describes the training audio as permissive/non-copyrighted and names public-domain, Apache/MIT-licensed, and synthetic sources. It also notes CC BY Koniwa (under one hour) and SIWIS (under eleven hours) contributions. This is the model author’s description, not an independent audit or a per-voice provenance/rights record.
- **Attribution / redistribution:** Dataset-level obligations for the particular `bf_emma` source and any applicable attribution were not determined. Model weights and voice-embedding distribution rights do not establish each source dataset’s terms.
- **Committed / downloaded:** No training dataset is committed or downloaded by this project’s TTS path.
- **Intended use:** The project uses only the prebuilt voice embedding for local speech synthesis; it does not train the voice.
- **Evidence:** [model card](https://huggingface.co/hexgrad/Kokoro-82M) · [voice list](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md).
- **Residual uncertainty:** No source-to-voice mapping or `bf_emma`-specific dataset license/consent record was verified.

### 6. Dockerized local TTS service

- **Source URL:** [service repository at source commit](https://github.com/letuhao/local-tts-service/tree/82fae01c1e9f9e213eb71ae02602311b42c5bc68) · [README at commit](https://github.com/letuhao/local-tts-service/blob/82fae01c1e9f9e213eb71ae02602311b42c5bc68/README.md) · [license at commit](https://github.com/letuhao/local-tts-service/blob/82fae01c1e9f9e213eb71ae02602311b42c5bc68/LICENSE).
- **Exact commit / release:** `82fae01c1e9f9e213eb71ae02602311b42c5bc68`.
- **Asset filename / SHA-256:** Service source/Docker configuration; no exact image digest pinned by the project. Model and voice asset hashes are addressed separately above.
- **Declared license / scope:** MIT for the service source. Does not license the ONNX weights or voice assets.
- **Attribution:** Preserve the MIT notice when redistributing covered service code.
- **Redistribution / project status:** The demo uses a locally built Docker service. The TTS source describes local use; project notes say the image/assets are not committed or pushed. No public image digest is established in the reviewed files.
- **Downloaded on demand?:** Docker dependencies are acquired at image-build time; model/voice assets must be supplied separately. Synthesis requests are sent to a loopback-only local endpoint by the project adapter.
- **Intended use:** Local serving for demo-video narration, not a remotely exposed public endpoint.
- **Evidence:** [service source](https://github.com/letuhao/local-tts-service/tree/82fae01c1e9f9e213eb71ae02602311b42c5bc68) · [service license](https://github.com/letuhao/local-tts-service/blob/82fae01c1e9f9e213eb71ae02602311b42c5bc68/LICENSE) · [service requirements](https://github.com/letuhao/local-tts-service/blob/82fae01c1e9f9e213eb71ae02602311b42c5bc68/requirements.txt).
- **Residual uncertainty:** Exact Docker image and dependency resolutions are not pinned; the service license does not resolve the separately sourced speech assets.

## Intended use and final decision

The intended use is a locally generated voiceover in a hackathon demonstration video, with possible public or promotional presentation. The code and upstream model declarations support technical use of the software/model under their respective terms. This review additionally verified (without downloading model weights) that the full SHA-256 of the upstream `voices/bf_emma.pt` file in the Apache-2.0-declared `hexgrad/Kokoro-82M` repository matches `VOICES.md`'s abbreviated checksum, confirming that specific upstream file's identity and file-level copyright license. That verification does **not** extend to: the third-party-repackaged `voices-v1.0.bin` archive the project's service actually loads (its hash remains unverified), the voice-specific training-data provenance/consent, voice-likeness/publicity rights of the underlying speaker, or permission for a generated voice recording in promotional/commercial materials. The release metadata does not verify the exact v1.0 binary hashes used by this project, and the project does not pin them. The video approval record says the candidate has not been uploaded; that does not resolve rights.

### Separate use, redistribution, and output conclusions

- **Using the upstream Kokoro-82M model:** its repository metadata declares Apache-2.0 for repository material, including the separately hosted `voices/bf_emma.pt` file. The project uses a third-party ONNX conversion, whose v1.0 asset-specific grant and hash are not established here.
- **Redistributing model/voice weights:** not cleared for the v1.0 ONNX conversion or `voices-v1.0.bin`; their release metadata has no digest and no explicit asset-specific terms. This project does not commit or redistribute those binaries.
- **Distributing generated audio:** the reviewed model card, voice list, conversion release, and local-service license provide neither an explicit generated-output restriction nor an explicit grant clearing public/promotional output. That silence is not permission. The video carries generated narration, not model/voice binaries, but its public YouTube distribution is **not cleared** because the voice-specific asset/data provenance, likeness/publicity rights, and output-use scope remain unresolved.
- **Attribution:** preserve Apache-2.0/MIT notices for covered materials when applicable. No voice-specific attribution term was found; attribution alone would not supply the missing rights.
- **Training data:** the card acknowledges Koniwa and SIWIS contributions under CC BY, but no reviewed primary source maps those datasets to `bf_emma` or documents voice-specific consent/likeness rights.

**RIGHTS_UNRESOLVED** — the voice-specific asset/data and output-use rights needed to clear the intended public hackathon/promotional use remain undocumented. Obtain written confirmation or use a voice with explicit, traceable rights before publishing or commercially promoting the recording. Do not redistribute the voice archive or model binaries without verifying their applicable terms.

**Fastest safe fallback:** keep this approved file local and do not upload it. If public video distribution is still needed, obtain written rights-holder confirmation for this exact voice/archive/output use, or separately authorize a new narration using original human-authored narration or a voice whose asset, dataset, and output-use rights are explicitly documented. Do not rerender or replace the approved candidate without separate authorization and a new human review.

## Project evidence

- [`scripts/matchpulse_local_tts.py`](../scripts/matchpulse_local_tts.py)
- [`scripts/matchpulse_conversational_tts.py`](../scripts/matchpulse_conversational_tts.py)
- [`scripts/matchpulse_kokoro_v2.py`](../scripts/matchpulse_kokoro_v2.py)
- [`tests/test_local_tts.py`](../tests/test_local_tts.py)
- [`README.md`](../README.md)
- [`submission/SUBMISSION_READINESS.md`](../submission/SUBMISSION_READINESS.md)
- [`submission/FINAL_VIDEO_APPROVAL.md`](../submission/FINAL_VIDEO_APPROVAL.md)
