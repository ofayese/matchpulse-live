# GitHub publication

This repository is published as a standalone public challenge repository. It is
deliberately separate from the private program repository: no private history,
no parent configuration, and no unrelated files are included.

---

## Published location

| Property | Value |
| -------- | ----- |
| Owner | `ofayese` |
| Repository | `matchpulse-live` |
| URL | <https://github.com/ofayese/matchpulse-live> |
| Visibility | Public |
| Default branch | `main` |
| License | Apache-2.0 (`LICENSE`, attribution in `NOTICE`) |

---

## Repository layout

```text
matchpulse-live/
├── MatchPulse.Live.sln      # Visual Studio solution (solution folders + items)
├── README.md
├── README-VISUAL-STUDIO.md
├── LICENSE  NOTICE  SECURITY.md  CONTRIBUTING.md  CODE_OF_CONDUCT.md
├── pyproject.toml  Dockerfile  compose.challenge.yml
├── .gitignore  .dockerignore  .env.example
├── src/matchpulse/          # FastAPI application package
├── tests/                   # pytest suite
├── scripts/                 # preflight, solution validation, smoke test, bootstrap
├── data/demo-match.jsonl    # seeded synthetic match
├── docs/                    # architecture, challenge alignment, deployment, publication
├── submission/              # pitch, project description, demo script, checklist
├── infra/                   # Bicep template, parameters example, validation scripts
└── .github/workflows/       # challenge-ci.yml, release-attest.yml, azure-deploy.yml
```

The repository contains exactly one root commit. It does not contain the
parent program's history.

---

## Continuous integration

`.github/workflows/challenge-ci.yml` runs on every pull request targeting
`main` and on every push to `main`.

| Control | Value |
| ------- | ----- |
| Permissions | `permissions: contents: read` |
| Interpreter | Python 3.12 |
| Dependency install | `python -m pip install -e '.[dev]'` |
| Byte-compile | `python -m compileall src` |
| Lint | `python -m ruff check src tests scripts` |
| Tests | `python -m pytest -q` |
| Coverage | `python -m pytest --cov=matchpulse --cov-report=term-missing --cov-fail-under=80` |
| Preflight | `python scripts/preflight.py` |
| Solution validation | `python scripts/validate_solution.py` |
| Container build | `docker build -t matchpulse-live:ci .` |
| Vulnerability gate | Trivy `0.76.0`, `--severity HIGH,CRITICAL --exit-code 1` |
| Compose validation | `docker compose -f compose.challenge.yml config` |

The workflow stores no plaintext secret and uses no secret at all.

`.github/workflows/azure-deploy.yml` validates the Bicep template on pull
requests that touch `infra/`. Its deployment job is inert (`if: false`) until
the Azure configuration described in `docs/AZURE_DEPLOYMENT.md` exists.

### Release and attestation workflow

`.github/workflows/release-attest.yml` is the only workflow that publishes a
container image and the only workflow that creates a release attestation. It
runs only on `workflow_dispatch` and only on the `remediation/pebble-removal`
branch.

| Control | Value |
| ------- | ----- |
| Trigger | `workflow_dispatch` on `remediation/pebble-removal` |
| Permissions | `contents: read`, `packages: write`, `id-token: write`, `attestations: write` |
| Authentication | The repository `GITHUB_TOKEN` only, and only after the scan passes |
| Vulnerability gate | Trivy pinned by digest, `--severity HIGH,CRITICAL --exit-code 1 --ignore-unfixed=false --ignorefile /dev/null` |
| Tag | `ghcr.io/ofayese/matchpulse-live:<full-commit-sha>` |
| Published refs | The immutable full-SHA tag only |
| Attestation | `actions/attest` v4, SLSA build provenance, signed by GitHub in the same run |
| Final approval | The protected `release-attestation` environment |

The release commit is the commit that carries the workflow file itself, so the
source tree, the OCI revision label, the immutable tag and the attestation
source identity are always the same commit. Nothing is taken from a workflow
input, a tag, or a mutable image reference.

The order of operations is fixed and fail-closed:

1. The exact workflow and source commit is checked out, and the checkout is
   re-verified against the dispatched commit with a clean working tree.
2. Every source gate runs: byte-compile, Ruff, pytest, coverage, preflight,
   solution validation, Bicep build and lint, and Compose validation.
3. The image is built locally with `push: false` and loaded into the runner.
4. That exact image is scanned with Trivy and
   `--severity HIGH,CRITICAL --exit-code 1 --ignore-unfixed=false
   --ignorefile /dev/null`. No ignore file, skip file, skip directory, VEX
   document or ignore-unfixed mode is used, and no severity is downgraded.
5. Only after the scan passes does the workflow log in to GHCR and push the
   scanned image under the immutable full-SHA tag.
6. The immutable digest is resolved from the registry.
7. `actions/attest` v4 signs the SLSA build provenance of that digest with
   the GitHub OIDC identity and pushes the attestation to the registry.
8. The attestation is verified publicly against the Sigstore trusted root,
   the exact signer workflow, the exact signer commit, the exact source ref
   and the exact source commit.
9. The published digest is pulled anonymously with a credential-free Docker
   configuration, and the application package inside the published image is
   compared byte for byte with the checked out source.
10. The published digest is scanned again with the same unsuppressed gate.
11. The published digest is started with the release hardening applied
    (no network, non-root user, read-only root filesystem, no capabilities,
    bounded process and memory limits) and is exercised from inside the
    container.
12. The final digest, the attestation identifier and the verification output
    are handed to the independent auditor as run evidence.
13. The protected `release-attestation` environment gates the final approval.
    The job re-verifies the approved digest and its attestation before the
    release is recorded, so the human approval is always given after the
    independent final-digest audit.

There is no hand written attestation, no self authored JSON predicate and no
post-hoc assertion in this repository. The attestation is produced by
`actions/attest` itself for the digest that the same run published.

GitHub recommends `GITHUB_TOKEN` for registry workflows associated with the
repository, so no long-lived registry credential is stored on a developer
machine, in a Windows environment variable, in a `.env` file, or in a release
script.

### Published image

| Property | Value |
| -------- | ----- |
| Tag | `ghcr.io/ofayese/matchpulse-live:sha-68409d3b82159164c7efb5172213cc3ce55cbe70` |
| Digest | `sha256:90ce4db3a1d61b62aa12c4009def817643f8378bf7c49c15a2f771af469b5268` |
| Immutable reference | `ghcr.io/ofayese/matchpulse-live@sha256:90ce4db3a1d61b62aa12c4009def817643f8378bf7c49c15a2f771af469b5268` |
| Source commit | `68409d3b82159164c7efb5172213cc3ce55cbe70` |
| Publication run | `39506525775` |
| Platform | `linux/amd64` |
| Runtime user | `10001:10001` |
| Entry point | `/usr/bin/python3.12 -m uvicorn` |

This image was published with the build step's provenance generation disabled,
so the registry carries **no build provenance attestation** for it and the
image carries no OCI revision label. The digest, the source binding and the
runtime behaviour were verified independently: the image was pulled back with
a Docker configuration that contains no credential at all, the application
package inside it is byte identical to the source commit, it was re-scanned
with the blocking Trivy gate, and it passed the hardened smoke test with 0
failed checks. The `release-attest` workflow above replaces this image with an
attested one that carries its own build provenance.

The earlier publication
`ghcr.io/ofayese/matchpulse-live:sha-e8289265dc1920a2f313a9ec45ebf748591a3071`
(digest `sha256:67546291cf1fc9aa236327a1d53230e8caa589ce0f72c758b28c6a6effee4d90`)
is superseded.

```bash
docker run --rm -p 8080:8080 \
  ghcr.io/ofayese/matchpulse-live@sha256:90ce4db3a1d61b62aa12c4009def817643f8378bf7c49c15a2f771af469b5268
```

---

## Branch protection

**Branch protection is not enabled by this repository's contents.** It must be
configured manually in the GitHub repository settings under
`Settings` → `Branches` → `Branch protection rules`.

Recommended rules for `main`:

- Require a pull request before merging.
- Require status checks to pass: `Validate (Python 3.12)` and `Container build`.
- Require branches to be up to date before merging.
- Do not allow force pushes.
- Do not allow deletions.

This has **not** been verified through the GitHub API and is therefore
recorded as a manual step rather than a completed action.

---

## Required environment variables

The challenge runs with **no** environment variables. The variables below are
optional and are only needed for the optional Microsoft Foundry enrichment.

| Variable | Purpose | Where it belongs |
| -------- | ------- | ---------------- |
| `CHALLENGE_SYNTHETIC_ONLY` | Must remain `true`; ingestion is refused otherwise | Runtime environment |
| `FOUNDRY_ENDPOINT` | Azure OpenAI / Foundry endpoint | Runtime environment or GitHub environment variable |
| `FOUNDRY_DEPLOYMENT` | Deployed model name | Runtime environment or GitHub environment variable |
| `FOUNDRY_API_VERSION` | API version, default `2024-10-21` | Runtime environment |
| `FOUNDRY_TIMEOUT_SECONDS` | Timeout before the deterministic fallback, default `1.4` | Runtime environment |
| `FOUNDRY_AUTH_MODE` | `managed_identity` or `api_key` | Runtime environment |
| `FOUNDRY_AZURE_SCOPE` | Token scope for managed identity | Runtime environment |
| `FOUNDRY_MAX_CONCURRENCY` | Maximum concurrent model calls, default `4` | Runtime environment |
| `FOUNDRY_CALL_BUDGET` | Process-wide model call budget, default `60` | Runtime environment |
| `FOUNDRY_API_KEY` | Runtime secret for the local API-key path only | **Never** committed |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Enables optional telemetry; the app works normally without it | Runtime environment or GitHub environment variable |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Alternative OpenTelemetry exporter endpoint | Runtime environment |

The deployed Azure baseline sets **none** of the `FOUNDRY_*` variables, so the
Foundry runtime mode is `off`: the deterministic pipeline is authoritative, no
model inference runs, and anonymous public use creates no Foundry spend.

The telemetry exporter is optional. When no telemetry configuration is present
the application behaves exactly as it does with telemetry disabled, and it
records only allowlisted aggregate signals (route template, method, status,
duration, accepted/rejected/duplicate event counts, insight count, Foundry
attempt/success/fallback/rejection counts, Foundry latency, and WebSocket
connect/disconnect/send/drop counts). Request bodies, response bodies, prompts,
model output, evidence text, authorization data, cookies, client IPs, tokens
and arbitrary match or event identifiers are never exported.

For the optional Azure deployment workflow, the GitHub `azure-production`
environment additionally needs `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`,
`AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP`, `CONTAINER_APP_NAME`,
`IMAGE_REFERENCE` (the immutable `ghcr.io/...@sha256:...` digest),
`FOUNDRY_ENDPOINT`, and `FOUNDRY_DEPLOYMENT`. These are stored as **GitHub
environment variables**, not as secrets in the workflow file, and the workflow
authenticates with OIDC rather than a client secret. No Azure Container
Registry is used; the approved public GHCR digest is the image source.

---

## No-secret policy

- `.env`, `.env.*`, publish profiles, connection strings, API keys, Azure
  client secrets, GitHub tokens, and private keys are never committed.
- `.gitignore` excludes `.env`, `.env.*` (with `!.env.example`), `.vs/`,
  `*.suo`, `*.user`, `.venv/`, caches, and logs.
- `.env.example` contains placeholders only.
- `scripts/preflight.py` scans every tracked file for GitHub tokens, Azure
  storage keys, private keys, Azure client secrets, assigned Foundry keys,
  publish-profile credentials, user-profile absolute paths, and private
  repository references, and fails the build on a match.
- GitHub's own secret scanning and push protection apply on the remote
  repository.

---

## Reproducing the published state

```bash
git clone https://github.com/ofayese/matchpulse-live.git
cd matchpulse-live
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
python -m pytest -q
python scripts/preflight.py
```
