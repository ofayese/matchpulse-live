# Azure deployment

Everything in this document has been **validated locally** unless it is
explicitly marked otherwise. Nothing here has been deployed to a live Azure
subscription as part of the published repository.

---

## Status legend

| Marker | Meaning |
| ------ | ------- |
| **Validated locally** | The exact command was executed successfully on the development machine. |
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
| `Microsoft.App/containerApps` | The MatchPulse Live service, system-assigned managed identity, HTTPS-only ingress, liveness/readiness/startup probes |

Monitoring defaults are enabled with 30-day workspace retention and a 0.023
GB/day Log Analytics cap. The cap may overshoot and bill excess data, and it
stops ingestion after the cap; it is not a hard spending limit. HTTP diagnostic
categories are not enabled.


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
for the proposed, ordered provider, Azure OpenAI, what-if, deployment, RBAC,
validation, cost-review, and cleanup commands. Resource creation is billable
and requires the exact resource-group authorization and a separate explicit
deployment approval. The commands in the plan have not been executed.

### Parameters

| Parameter | Required | Notes |
| --------- | -------- | ----- |
| `prefix` | No | Lowercase prefix for resource names; hyphens are stripped automatically |
| `location` | No | Defaults to the resource group location |
| `image` | **Yes** | `ghcr.io/ofayese/matchpulse-live@sha256:1bb9df336d95a5549f7384e023c5954710c662f59d6fb9b9ac2d72ed3ee0c96c` (attestation 58474240) |
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
reports `"foundry_mode": "deterministic-fallback"` on `/health/ready` and
produces every insight from the deterministic pipeline.

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
