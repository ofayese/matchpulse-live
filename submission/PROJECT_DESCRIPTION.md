# Project description

## MatchPulse Live

**Core positioning:** MatchPulse Live transforms synthetic football events into explainable, audience-specific match intelligence for broadcast and streaming experiences.

MatchPulse Live is a synthetic-data prototype for evidence-linked football storytelling. Its local pipeline interprets event sequences, derives match moments, records source event IDs and calculation details, and renders the same grounded moment for fans, analysts, and broadcasters in English, Spanish, and French.

The source includes an optional guarded Microsoft Foundry adapter, but
Foundry is disabled in the submitted runtime and the demonstrated workflow
makes zero model calls. The immutable Azure Container Apps image was
read-only verified with ingress disabled. No hosted-agent deployment is
claimed. The approved video does not demonstrate Foundry usage.

The baseline uses HTTP event ingestion. It does not include an active Event Hubs consumer. State is held in process memory, and multi-replica WebSocket fan-out is not supported without a managed backplane.

**Public repository:** <https://github.com/ofayese/matchpulse-live>

**Current published image candidate:** `ghcr.io/ofayese/matchpulse-live@sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226` (source revision `335781f928011f99a644083d80bfe4dfc480b1a6`).

The image is tied to that source revision, not to later checkout changes.
Application and infrastructure changes in the current checkout have not been
built into or deployed as this image.

**Hosted demo:** Deployed and validated on Azure Container Apps. A fresh read-only check confirmed that no ingress configuration is present, so no public endpoint is enabled. Specific Azure resource identifiers are omitted from this public description.

**Demo video:** [Watch the 115-second MatchPulse Live demo](https://www.youtube.com/watch?v=O5gHkl_UFHc). It uses the human-approved ElevenLabs stock voice Lily narration, generated during an active paid Starter subscription; no cloning or Beta service was used. The YouTube video is Unlisted and available by URL.

**Challenge project:** [Innovation Studio project 127196](https://innovationstudio.microsoft.com/hackathons/insidethegamedeveloperhackathon/project/127196). The project is saved and listed under the entrant's projects; organizer confirmation of entry status and any separate final-submit requirement is pending. The portal player is under support review and is not currently playable.

**Technologies present in the repository:** Python, FastAPI, Docker, Azure Container Apps, Bicep, GitHub Actions, GitHub Container Registry, GitHub artifact attestations, optional guarded Microsoft Foundry adapter, optional Application Insights configuration.
