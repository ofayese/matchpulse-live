# Validation report - 2026-10-20

> **HISTORICAL VALIDATION REPORT.** This report records the validation state
> for the release and image identified below (2026-10-20). It is retained for
> provenance and does not describe the current branch validation state. See
> [Current validation](#current-validation-2026-10-29) at the end of this file.
> The submitted release is scoped to source SHA
> `335781f928011f99a644083d80bfe4dfc480b1a6` and image digest
> `sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226`.

## Verified in this workspace (historical, 2026-10-20)

- Python source, tests, and preflight compiled successfully on Python 3.14.8.
  Python 3.12 is the reference interpreter (CI pins 3.12 and the container image
  runs `/usr/bin/python3.12`, verified as 3.12.3); 3.12 is not installed on the
  validation machine.
- Test suite: **101 passed, 0 failed**. The original bundle baseline was 9 passed,
  0 failed, and the Visual Studio conversion baseline was 44 passed, 0 failed;
  no test was skipped or weakened.
- Coverage: **88.84%** total, above the 80% gate.
- Static analysis: `ruff check src tests scripts` - **All checks passed**.
- Submission preflight: required files present, source compiles, no secrets or
  forbidden files, synthetic-only gate documented, solution configurations
  present.
- Visual Studio solution: `MatchPulse.Live.sln` parses under MSBuild 18.9.15
  (Debug, Release, and ChallengeDemo). 55 solution items, all resolving to real
  files, all repository-relative.
- Live smoke test: 52 synthetic events accepted; final state `finished`.
- API and WebSocket smoke test: **PASS (0 failed checks)** against a local
  uvicorn instance and against the Compose container.
- Localization and personalization: the same evidence produced four distinct
  outputs across English and French, and across fan, analyst, and broadcaster
  personas, all sharing one evidence event id.
- Foundry guard: valid rewrite applied; timeout, invalid JSON, service error,
  schema mismatch, and unsupported-number cases all fall back to the
  deterministic narrative; no secret value appeared in a warning, log record, or
  response.
- Foundry concurrency and budget: the provider is asynchronous, bounds its own
  concurrency, enforces a process-wide call budget, performs zero retries, and
  reports one of four truthful states - `disabled`, `configured-unverified`,
  `verified`, `degraded-fallback`.
- Demo runs: unique `demo-<uuid12>` match identifiers, deterministic synthetic
  generation, a 24-event cap, a 20 second cooldown, one concurrent run, and a
  wait for a WebSocket subscriber before emission.
- Variant comparison: one authoritative moment is presented to every audience
  with the same insight id, evidence event ids, and statistics.
- Telemetry: opt-in and allowlist-only. With no exporter configuration the
  application behaves exactly as before, exporter failures are non-fatal, and
  no arbitrary identifier is ever used as a metric dimension.
- Browser demo: dynamic content is built with `createElement` and
  `textContent`; there is no `innerHTML`, `outerHTML`, `insertAdjacentHTML`, or
  `document.write` anywhere in the page.
- Container image `matchpulse-preflight:local`
  (`sha256:0af07f9f07bd69154bcc6dbb5444f525e65721b4c846d8c401220f9e9fe0b4a9`):
  non-root uid `10001:10001`, `linux/amd64`, 4 layers, CPython 3.12.3, and a
  successful import probe for `fastapi`, `pydantic`, `uvicorn`, `httpx`, and
  `matchpulse`.
- Vulnerability gate: Trivy `0.76.0` (database updated 2026-10-20) scanned the
  built image with `--scanners vuln --severity HIGH,CRITICAL --exit-code 1`
  and no ignore flags. Result: **0 HIGH, 0 CRITICAL** (26 findings in total:
  22 MEDIUM, 4 LOW). The same blocking gate now runs in
  `.github/workflows/challenge-ci.yml` and in
  `.github/workflows/publish-container.yml` before any registry login or push.
- Bicep: `az bicep build` and `az bicep lint` both exited 0. The compiled
  template contains no hardcoded subscription id, no hardcoded tenant id, and
  no secret literal. Four non-blocking warning codes remain (`BCP187`,
  `BCP081`, `BCP318`, `BCP422`).
- Remote CI: the `challenge-ci` workflow was dispatched for the exact commit
  `59dccafac618d9d2f3f0c1dc1d491ddec4ae537b` (run `39470530806`) and passed.
  The push to `main` for the published commit
  `e8289265dc1920a2f313a9ec45ebf748591a3071` also passed (run `39475810224`).
- Infrastructure validation: `azure-deploy` failed for the published commit
  because the workflow referenced an action repository that does not exist.
  The workflow now installs the pinned Bicep CLI `0.48.1` explicitly, and the
  runs for the follow-up commit `c1177ca` passed - `azure-deploy` run
  `39476696692` and `challenge-ci` run `39476696757`.
- Container publication (SUPERSEDED RELEASE DIGEST - retained for historical
  provenance only; the current approved digest is
  `sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226`):
  `publish-container.yml` run `39475822157` published
  `ghcr.io/ofayese/matchpulse-live:sha-e8289265dc1920a2f313a9ec45ebf748591a3071`
  with digest
  `sha256:67546291cf1fc9aa236327a1d53230e8caa589ce0f72c758b28c6a6effee4d90`.
  The blocking Trivy gate ran before the login and push step and passed. The
  image was pulled back anonymously with a credential-free Docker
  configuration, re-scanned at 0 HIGH and 0 CRITICAL, and passed the smoke
  test with 0 failed checks as a hardened container (`linux/amd64`, user
  `10001:10001`, read-only root filesystem, 32M `/tmp`, all capabilities
  dropped, `no-new-privileges`, health `healthy`).

## Not verified here

- Native Visual Studio Python project validation. No Visual Studio installation
  exists on this machine, so the Python development workload is absent. The
  solution uses solution folders and solution items, which every Visual Studio
  edition can open. **VISUAL STUDIO PYTHON WORKLOAD REQUIRED.**
- Azure resource deployment. An Azure account and subscription are available,
  but no resource group, region, resource name set, image source, or Foundry
  deployment has been approved, so nothing was deployed.
- A live Microsoft Foundry call. No endpoint, deployment, or credential was
  supplied, so only the guarded fallback path was exercised.
- Event Hubs is NOT part of the deployed baseline: no consumer, checkpoint store, or processed-message trace exists.
- Public WebSocket behavior over Azure ingress.
- A hosted public demo URL and a public demo video. The remote `challenge-ci`
  workflow was verified for the audited commit; the hosted demo and the video
  are still outstanding.

## Reproduction

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
python -m compileall src
python -m ruff check src tests scripts
python -m pytest -q
python -m pytest --cov=matchpulse --cov-report=term-missing --cov-fail-under=80
python scripts/preflight.py
python scripts/validate_solution.py
docker compose -f compose.challenge.yml up --build -d
python scripts/smoke_test.py --url http://127.0.0.1:8080
```

For final submission, run the GitHub workflow and Azure checks in
`submission/REGISTRATION_AND_SUBMISSION_CHECKLIST.md`, then update this report
with links and evidence.

## Current validation - 2026-10-29

This validation applies to current source HEAD
`067fa190ebaf64fdbefa5fd0bdb741f1015f7c4a`; it does not change the submitted
release scope. The approved submitted image remains
`ghcr.io/ofayese/matchpulse-live@sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226`,
built from source revision
`335781f928011f99a644083d80bfe4dfc480b1a6`, an ancestor of current HEAD.

| Gate | Result |
| --- | --- |
| Python | 3.12.0 |
| Tests | 208 passed, 2 skipped, 0 failed (5.13 seconds) |
| Coverage | 90.50% (80% required) |
| Compile, Ruff, preflight, solution validation | PASS |
| Current-source image: hardened runtime and smoke | PASS |
| Approved immutable image: exact digest, hardened runtime and smoke | PASS |
| Live duplicate event | PASS on both images: HTTP 202, duplicate true, no new insights or event-count/state-sequence change |
| Live out-of-order event | PASS on both images: HTTP 409, state unchanged |
| Live non-synthetic event | PASS on both images: HTTP 422 |
| Readiness after negative event checks | PASS on both images |
| `MANIFEST.sha256` | PASS_HISTORICAL: all 66 entries match the Git blobs at the manifest's last-change commit `68409d3`; it is not a manifest of current HEAD |
| Trivy filesystem and image scans; pip-audit | PASS; no HIGH/CRITICAL image findings and no known audited dependency vulnerabilities |
| Gitleaks | Test-fixture literals in `tests/test_foundry_provider.py` and `tests/test_local_tts.py` remain triaged but unsuppressed; no allowlist was added |
| Azure | Read-only Foundry account query returned 0 model deployments; Container App retained the approved digest, synthetic-only mode and disabled ingress |

The test export and its temporary directory were outside the repository. No
application behavior, approved image, Azure resource, media, or publication
state was changed. Documentation corrections in this cleanup only reconcile
the current Foundry mode wording and label earlier validation and image
evidence as historical.
