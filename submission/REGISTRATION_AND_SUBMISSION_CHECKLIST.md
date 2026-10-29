# Historical registration and submission checklist

This is a historical planning record, not an active execution checklist. Its
dated tasks include actions that are now stale, including creating a Foundry
deployment and enabling public access. Do not execute them as current
instructions. The existing Azure Container Apps deployment was validated and
its public ingress was disabled after validation; Foundry was off with zero model calls in
the deployed configuration. The approved video remains local and unuploaded;
the challenge portal remains unsubmitted. The separate voice-asset license
and the required upload destination are unresolved.

## Historical readiness snapshot — October 26, 2026

The registration confirmation supplied for this task is timestamped October 20, 2026 at 1:29 PM Eastern (the client timezone), before the 3:00 PM Eastern equivalent of the official 12:00 PM Pacific registration deadline. Registration is confirmed for this gate. Azure Container Apps deployment succeeded and was validated live (container app `<CONTAINER_APP_NAME>` in resource group `<RESOURCE_GROUP>`, active revision `<AZURE_REVISION>`); public ingress was disabled after validation to enforce cost containment. A fresh ingress readback was unavailable during finalization. In the deployed configuration, Microsoft Foundry runtime was disabled and model call count was zero. Final video is approved locally (`matchpulse-submission-hosted-elevenlabs-lily-v1-candidate.mp4`, SHA-256: `f06bb7dfe48b48c642044a6b09cd29cf857edb6f1bed6a95be90a1718ec2b786`, duration 115.0s, local Dockerized Kokoro-82M `bf_emma` narration) with browser TTS completely removed; video is not yet uploaded (`VIDEO_UPLOADED=NO`). The challenge portal has not been submitted (`CHALLENGE_SUBMITTED=NO`).

## Tuesday, October 20, 2026 - registration

Official registration closes at **12:00 PM Pacific / 3:00 PM Eastern (Washington, DC)**. Do not wait until evening.

- [ ] Visit `https://aka.ms/insidethegame` and click **Register**.
- [ ] Confirm individual, team (maximum four individuals), or organization entry.
- [ ] If entering as a team/organization, name one authorized representative.
- [ ] Confirm every participant meets the eligibility rules and has no conflict.
- [ ] Save the confirmation email/screenshot outside the public repository.
- [ ] Use project title: **MatchPulse Live**.
- [ ] Use `submission/PITCH.md` as the working elevator pitch.
- [ ] Select target categories only after the implemented/deployed proof supports them.

## October 20-24 - make the proof real

- [ ] Add this package to a new challenge branch or clean public repository.
- [ ] Run tests and preflight on Windows and in GitHub Actions.
- [ ] Create a Microsoft Foundry project/model deployment and configure the guarded adapter.
- [ ] Deploy the container to Azure Container Apps.
- [ ] Confirm the public demo has no login restriction and remains free to test.
- [ ] Add an on-page synthetic feed trigger if judges will not run a CLI.
- [ ] Measure and record deterministic and Foundry-path latency.
- [ ] Capture Application Insights requests/errors and the active Azure revision.

## October 25-26 - submission package

- [ ] Make the GitHub repository public.
- [ ] Verify no secrets, `.env`, private logs, real player data, or unrelated files exist in history.
- [ ] Confirm the final repository license and ownership.
- [ ] Record the demo from the exact public commit.
- [ ] Keep the final video <= 1:55 and add English captions.
- [ ] Upload to the challenge-required destination after it is identified and its current requirements are verified.
- [ ] Add final public repository, demo, and video URLs to the project description/testing instructions.
- [ ] Run `python scripts/preflight.py` and archive the output.

## Tuesday, October 27 - submit

The official challenge deadline supplied for this task is **October 27, 2026
at 11:59 PM Pacific Time**. The internal completion target is **tomorrow
afternoon (October 27, Pacific Time)**; this earlier target does not replace
the official deadline. Verify the live portal status before any authorized
submission.

- [ ] Complete every required field on the Projects page.
- [ ] Paste the pitch and description; name Microsoft/Azure technologies actually demonstrated.
- [ ] Add the public GitHub URL.
- [ ] Add the public video URL.
- [ ] Add the hosted demo/test-build URL and concise testing instructions.
- [ ] Confirm all submission materials are in English (multilingual product output is fine).
- [ ] Confirm the project is newly built, original, and has not won another contest.
- [ ] Recheck video for third-party marks, copyrighted music, and private data.
- [ ] Submit, reopen the project page, and verify all links from a private browser window.
- [ ] Save the confirmation and final URLs.

## Final category honesty check

- Do not claim **Best Multi-Agent System** based on this implementation: the processing stages are deterministic components, not an autonomous or multi-agent system.
- Do not claim **Best Use of Microsoft Foundry** from the adapter alone; the validated deployment had Foundry off and zero model calls.
- If selecting **Best Azure Cloud Native Integration** or **Best Enterprise Solution**, use only the evidence that the immutable candidate passed hosted validation and disclose disabled ingress, in-memory state, and the telemetry limits.
- Confirm the exact category options and wording in the live portal; these prize labels are not a substitute for portal verification.
