# Azure deployment

This document describes the Bicep template and deployment procedures. A
fresh read-only Azure extension check on 2026-10-26 confirmed the deployed
Container App exists and has provisioning state `Succeeded`. Its ingress
configuration is absent (`null`), and its configured image remains pinned to
the immutable digest below. The app is configured for 0–1 replicas. The
direct resource-group RBAC query returned no assignments.

The fresh resource-group inventory returned seven ARM resources:
the five previously observed app/monitoring resources plus an unexpected
Cognitive Services account and its child Foundry project. The account and
project were explicitly created after the Container App deployment: ARM
system data dates the account to 2026-10-26T14:28:12Z and the project to
2026-10-26T14:28:19Z; Activity Log records successful account and project
write operations at 14:28:32Z and 14:28:21Z, respectively. The project
connection metadata includes remote-tool registrations; credential values
were not read. Neither resource is an Azure-managed Container Apps
dependency, is present in this Bicep, or is required by the deployed app.
This is reconciled as
`AZURE_COUNT_RECONCILED_UNEXPECTED_RESOURCES`, not as an Azure-managed
Container Apps dependency or query-scope difference. The extra resources are
not represented as harmless; owner/security review and a separate
remediation decision remain outstanding. The writes postdate the Container
App's 2026-10-25 ingress-restriction activity. No resource was modified or
deleted.

Foundry model-deployment inventory returned no deployments. The Container
App environment contains only the expected Application Insights
connection-string and synthetic-only setting names; no Foundry runtime
setting is present. A recorded run had zero model calls. Hosted Agents
Preview returned the optional
`Microsoft.CognitiveServices/accounts/AIServices/agents/read` 403, so the
hosted-agent inventory was not verified. MatchPulse has no runtime dependency
on Hosted Agents Preview and remains usable through its deterministic
pipeline. No RBAC grant was added to suppress this warning.

Read-only Cost Management and budget reads on 2026-10-26 returned $0 USD
month-to-date spend, a $25 monthly resource-group budget ($0 actual, $0
forecast), and a separate $50 annual subscription budget ($0 actual; no
annual forecast returned). Alert thresholds do not stop spending; the $15
operational stop threshold is not Azure-enforced. The workspace reports
30-day default retention and a 0.023 GB/day cap. The linked Application
Insights resource and its core telemetry tables report 90-day retention.
The resource-ID-filtered month-to-date cost query returned no rows for the
additional account or project; this does not establish zero future or
usage-based cost.
The refreshed cost/retention/security evidence is recorded in the local
authorization packet; no Azure resource, role assignment, budget, ingress, or
image was changed during finalization.

The previously recorded deployed image digest is
`ghcr.io/ofayese/matchpulse-live@sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226`,
recorded as associated with source commit
`335781f928011f99a644083d80bfe4dfc480b1a6`. The read-only check verified the
deployed digest; it did not independently revalidate the artifact attestation.

---

## Status legend

| Marker | Meaning |
| ------ | ------- |
| **Validated locally** | The exact command was executed successfully on the development machine. |
| **Current deployed state** | A read-only observation of the existing Azure deployment; not a deployment instruction. |
| **Requires Azure authentication** | The command needs an authenticated `az` session and an approved subscription. |
| **Creates billable resources** | The command provisions resources that cost money. |
| **Optional** | Not required for the challenge to run. |

---

## What the template creates

`infra/main.bicep` provisions, in one resource-group-scoped deployment:

| Resource | Purpose |
| -------- | ------- |
| `Microsoft.OperationalInsights/workspaces` | Log Analytics workspace for Container Apps logs |
| `Microsoft.Insights/components` | Application Insights, linked to the workspace |
| `Microsoft.App/managedEnvironments` | Container Apps environment |
| `Microsoft.App/containerApps` | The MatchPulse Live service, system-assigned managed identity, template-defined HTTPS-only ingress settings, and liveness/readiness/startup probes. The current deployed app has no ingress configuration. |

Monitoring defaults are enabled with 30-day workspace retention and a 0.023
GB/day Log Analytics cap. In the current linked workspace, the Application
Insights core telemetry tables were read back at 90-day retention; table
retention can differ from the workspace default. Workspace-based
Application Insights telemetry is stored and billed through Log Analytics,
with retention configured at workspace/table scope
([Microsoft Learn](https://learn.microsoft.com/en-us/azure/azure-monitor/app/create-workspace-resource),
[retention settings](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/data-retention-configure)).
The cap may overshoot and bill excess data, and it stops ingestion after the
cap; it is not a hard spending limit. HTTP diagnostic categories are not
enabled.


Event Hubs is NOT part of the deployed baseline: no consumer, checkpoint store, or processed-message trace exists. HTTP ingestion
(`POST /v1/events`) remains the supported ingestion path.

---

## Prerequisites

- Azure CLI 2.x with Bicep: `az bicep install`
- An authenticated session: `az login`
- An explicitly selected subscription: `az account set --subscription <id>`
- An existing resource group in the target region
- A container image published to GHCR or Azure Container Registry

---

## 1. Validate the template

**Validated locally**

```bash
az bicep build --file infra/main.bicep
```

or, with the built-in guard script:

```bash
bash infra/validate.sh          # Linux / macOS
powershell -ExecutionPolicy Bypass -File infra\validate.ps1   # Windows
```

The guard script compiles the template and then asserts that the compiled ARM
JSON contains no hardcoded subscription id, no hardcoded tenant id, and no
secret literal.

**Requires Azure authentication**

```bash
az account show
az account list --output table
```

**Requires Azure authentication** — non-deploying validation against an
approved resource group:

```bash
az deployment group validate \
  --resource-group <approved-resource-group> \
  --template-file infra/main.bicep \
  --parameters image=<approved-image-reference>
```

---

## 2. Deployment sequence

See [`AZURE_CHALLENGE_DEPLOYMENT_PLAN.md`](AZURE_CHALLENGE_DEPLOYMENT_PLAN.md)
for the historical pre-deployment sequence and its commands. That plan is not
a description of current resource state or authorization to repeat deployment.
Any future resource mutation requires a separate explicit approval.

### Parameters

| Parameter | Required | Notes |
| --------- | -------- | ----- |
| `prefix` | No | Lowercase prefix for resource names; hyphens are stripped automatically |
| `location` | No | Defaults to the resource group location |
| `image` | **Yes** | `ghcr.io/ofayese/matchpulse-live@sha256:f413c32f671b191a4b3c63c8bed9c7b318ccdc60633bf222d5cba0049feaa226` (recorded source association `335781f928011f99a644083d80bfe4dfc480b1a6`; artifact attestation was not independently revalidated during the publication review) |
| `foundryRuntimeMode` | No | `off` (default) or `validate`; `off` means no endpoint, no deployment, no key and no model inference |
| `foundryEndpoint` | No | Only used when `foundryRuntimeMode` is `validate`; leave empty otherwise |
| `foundryDeployment` | No | Only used when `foundryRuntimeMode` is `validate`; leave empty otherwise |
| `foundryAuthMode` | No | `managed_identity` (default) or `disabled` |
| `monitoringEnabled` | No | Enables Application Insights and Log Analytics, default `true` |
| `logRetentionDays` | No | 30 days; minimum workspace default, not an ingestion cost control |
| `logDailyQuotaGb` | No | Allowed values `0.023`, `0.05`, `0.1`, `1`; default minimum `0.023` GB/day |
| `foundryCallBudget` | No | 1-20 calls per process, default 20; resets on process restart |
| `minReplicas` / `maxReplicas` | No | 0-1 / 1-1; one replica is the maximum until durable state exists |
| `concurrentRequestsPerReplica` | No | 1-200, default 50 |

There is **no secret parameter**. The Foundry API key is not accepted by the
template; managed identity is used instead.

### Outputs

`appUrl`, `appName`, `managedIdentityPrincipalId`, `imageReference`,
`minReplicas`, `maxReplicas`, `foundryRuntimeMode`, `foundryConfigured`,
`monitoringEnabled`, `applicationInsightsName`, `logAnalyticsWorkspace`.
No output exposes a secret.

---

## 3. Azure OpenAI access

**Preferred: managed identity**

The Container App receives a system-assigned managed identity. The service
reads `FOUNDRY_AUTH_MODE=managed_identity` and acquires a token through
`DefaultAzureCredential` (`azure-identity`, optional extra). Grant the
identity `Cognitive Services OpenAI User` on the exact Azure OpenAI account
scope, not the subscription.

```bash
az role assignment create \
  --assignee-object-id <managed-identity-principal-id> \
  --assignee-principal-type ServicePrincipal \
  --role "Cognitive Services OpenAI User" \
  --scope /subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.CognitiveServices/accounts/<azure-openai-account>
```

**Local only: API key**

`FOUNDRY_API_KEY` is supported for local hackathon testing. Supply it
through the runtime environment and never commit it.

Foundry is **never required**. With no Foundry configuration the service
reports `"foundry_mode": "disabled"` on `/health/ready` and
produces every insight from the deterministic pipeline.

`foundry_mode` reports one of four states: `disabled` (Foundry is
intentionally off), `configured-unverified` (configuration exists but no model
call has succeeded yet), `verified` (a model call completed and passed every
guard), and `degraded-fallback` (a configured provider failed or a rewrite was
rejected, so the deterministic narrative is used).

---

## 4. GitHub Actions deployment

`.github/workflows/azure-deploy.yml` is prepared but **inert**: the `deploy`
job has `if: false` and only becomes active when all of the following exist:

1. A protected GitHub environment named `azure-production`.
2. Environment variables: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`,
   `AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP`, `ACR_NAME` (or an approved
   GHCR image reference), `CONTAINER_APP_NAME`, `FOUNDRY_ENDPOINT`,
   `FOUNDRY_DEPLOYMENT`, `IMAGE_REFERENCE`.
3. An OIDC subject claim mapping the `azure-production` environment to an Azure
   app registration with a least-privilege role on the target resource group.
4. A change of the `deploy` job's `if:` condition from `false` to `true`.

The workflow uses `permissions: id-token: write` and `azure/login@v2` with a
client id, tenant id, and subscription id. **No `AZURE_CLIENT_SECRET` is used
or requested.** The Bicep validation job runs on every pull request that
touches `infra/`.

---

## 5. Cleanup

Preserve the resource group, owner tag, and budget. Disable ingress and remove
only the approved challenge resources using the commands in
[`AZURE_CHALLENGE_DEPLOYMENT_PLAN.md`](AZURE_CHALLENGE_DEPLOYMENT_PLAN.md).
The app-only cleanup command is:

```bash
az containerapp delete --name <app-name> --resource-group <approved-resource-group> --yes
```

Log Analytics and Application Insights can be removed individually after the
app and environment:

```bash
az monitor log-analytics workspace delete --workspace-name <workspace-name> --resource-group <approved-resource-group> --yes
az monitor application-insights component delete --app <insights-name> --resource-group <approved-resource-group>
```

---

## 6. Verification after deployment

```bash
curl -fsS https://<app-fqdn>/health/live
curl -fsS https://<app-fqdn>/health/ready
```

`/health/ready` reports `synthetic_only: true` and the active
`foundry_mode`. The demo page is served from `/demo`.
