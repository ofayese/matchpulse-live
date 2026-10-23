# MatchPulse Live challenge deployment plan

**Planning document only.** None of the commands in this document were run.
The resource-group authorization confirmation has been supplied by the user.
Billable deployment still requires a separate explicit approval using the
request in the evidence packet.

## Approved planning envelope

- Subscription `Subscription 1` (`13b00900-43c4-4cdc-aba3-4a8bb13e61cc`)
- Resource group `rg-matchpulse-insidethegame-dev`, East US 2; fallback East US
  only after fresh quota/capacity and cost review
- Azure OpenAI account kind `OpenAI`, SKU `S0`, proposed name
  `matchpulseitg2026` (check global name availability before creation)
- GPT-4o-mini `2024-07-18`, deployment alias `matchpulse-narrative`, Standard
  capacity 1 (1K TPM); observed regional quota 200K TPM, zero current use
- Consumption ACA, 0.5 vCPU, 1 GiB, 0–1 replica, system identity, public
  HTTPS, port 8080, synthetic-only
- Immutable image `ghcr.io/ofayese/matchpulse-live@sha256:1bb9df336d95a5549f7384e023c5954710c662f59d6fb9b9ac2d72ed3ee0c96c`, accepted attestation ID `58474240`
- Workspace Analytics retention 30 days; Log Analytics daily quota 0.023 GB
- App model limit: 20 calls per process, one concurrent request, 4 KiB UTF-8
  payload ceiling, 128 output tokens, 1.4 second timeout, no retries. Process
  restarts reset the call budget; manually track 80 total calls maximum for
  the seven-day operating plan.
- **Artifact gate:** the provided pinned GHCR digest predates the new 4 KiB
  prompt and 128 output-token source controls. Those controls are not in that
  image. Do not deploy it while representing those limits as enforced. A new
  immutable image and attestation from reviewed source are required; the
  accepted digest must not be republished or silently substituted.
- Expected seven-day constrained plan $1.261386 before free allowances and
  cap overshoot. Existing $25/month budget is an alert, not a hard stop.
- Cleanup target November 11, 2026, 12:15 AM Pacific, after the judging window;
  verify official dates before deployment.

## Ordered deployment sequence

### 1. Confirm identity, subscription, resource group and authorization

```bash
az account show --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc -o table
az group show --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --name rg-matchpulse-insidethegame-dev -o json
az resource list --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --resource-group rg-matchpulse-insidethegame-dev -o table
```

Stop unless the RG is still empty, unlocked, and the user-confirmed
authorization remains valid. Never alter its owner tag to match the login.

### 2. Register only required providers

```bash
az provider register --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --namespace Microsoft.OperationalInsights
az provider register --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --namespace Microsoft.Insights
az provider show --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --namespace Microsoft.OperationalInsights --query registrationState -o tsv
az provider show --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --namespace Microsoft.Insights --query registrationState -o tsv
```

`Microsoft.ManagedIdentity` is not separately needed for the system-assigned
identity embedded in the Container App. Microsoft.App and
Microsoft.CognitiveServices were already registered. Event Hubs and ACR remain
excluded.

### 3. Create the proposed Azure OpenAI account and model deployment

```bash
az cognitiveservices account create \
  --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc \
  --resource-group rg-matchpulse-insidethegame-dev \
  --name matchpulseitg2026 --location eastus2 --kind OpenAI --sku S0 \
  --custom-domain matchpulseitg2026

az cognitiveservices account deployment create \
  --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc \
  --resource-group rg-matchpulse-insidethegame-dev --name matchpulseitg2026 \
  --deployment-name matchpulse-narrative --model-name gpt-4o-mini \
  --model-version 2024-07-18 --model-format OpenAI \
  --sku-name Standard --sku-capacity 1
```

Read the real endpoint; do not rely on the proposal until this succeeds:

```bash
az cognitiveservices account show \
  --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc \
  --resource-group rg-matchpulse-insidethegame-dev --name matchpulseitg2026 \
  --query properties.endpoint -o tsv
```

### 4. Run a final model-enabled what-if, inspect it, then deploy after approval

Create a private parameter JSON from the actual endpoint and the exact image
digest. Keep `foundryRuntimeMode=validate`, `foundryAuthMode=managed_identity`,
`monitoringEnabled=true`, `logRetentionDays=30`, `logDailyQuotaGb="0.023"`,
`foundryCallBudget=20`, `minReplicas=0`, and `maxReplicas=1`.

```bash
az deployment group what-if \
  --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc \
  --resource-group rg-matchpulse-insidethegame-dev \
  --name matchpulse-final-approved-preview \
  --template-file infra/main.bicep \
  --parameters @approved.parameters.json \
  --result-format FullResourcePayloads
```

Review for exactly the four template resources: workspace (with inline
`workspaceCapping`), App Insights component, Container Apps environment, and
Container App. Verify the endpoint, alias, digest, 0.023 cap, 30-day retention,
identity, 0–1 replica, HTTPS port 8080, synthetic-only setting, and no
unrelated resources. The separate Azure OpenAI account and model deployment
are intentionally outside this Bicep template and preview.

Only after a second explicit deployment approval:

```bash
az deployment group create \
  --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc \
  --resource-group rg-matchpulse-insidethegame-dev \
  --name matchpulse-challenge \
  --template-file infra/main.bicep \
  --parameters @approved.parameters.json
```

PowerShell uses the same Azure CLI commands; quote the parameter file argument
as `--parameters "@approved.parameters.json"`.

### 5. Assign the narrow role and validate the app

```bash
APP_PRINCIPAL=$(az containerapp show --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --resource-group rg-matchpulse-insidethegame-dev --name matchpulse-api-lhm35ehteauty --query identity.principalId -o tsv)
MODEL_SCOPE=/subscriptions/13b00900-43c4-4cdc-aba3-4a8bb13e61cc/resourceGroups/rg-matchpulse-insidethegame-dev/providers/Microsoft.CognitiveServices/accounts/matchpulseitg2026
az role assignment create --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --assignee-object-id "$APP_PRINCIPAL" --assignee-principal-type ServicePrincipal --role "Cognitive Services OpenAI User" --scope "$MODEL_SCOPE"
```

Wait for RBAC propagation. Then verify health and a synthetic model request:

```bash
curl -fsS https://<app-fqdn>/health/live
curl -fsS https://<app-fqdn>/health/ready
curl -fsS -X POST https://<app-fqdn>/v1/events -H 'Content-Type: application/json' -d '{"match_id":"challenge-smoke","sequence":1,"clock_ms":1000,"event_type":"shot","team_id":"Northbridge-FC","player_id":"NB-9","outcome":"on_target","speed_kmh":101,"source":"synthetic"}'
```

Also verify a signed-out browser demo, WebSocket connection, deterministic
fallback, App Insights workspace linkage, Container Apps system/console logs,
replica count no greater than one, and daily actual/forecast cost. Health checks
do not call the model. No background or recursive model calls are implemented.

### 6. Monitor and clean up

Review Cost Management daily during the deployment and judging window. Stop
demonstrations and disable ingress if model calls or logs spike, if more than
one replica appears, or if the forecast approaches $25. The Azure budget and
daily quota can alert/limit telemetry but are not guaranteed spending stops.

After judging, preserve the resource group, owner tag, and budget. Remove only
these challenge resources in dependency order:

```bash
az containerapp ingress disable --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --resource-group rg-matchpulse-insidethegame-dev --name matchpulse-api-lhm35ehteauty
az role assignment delete --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --ids <exact-role-assignment-id>
az cognitiveservices account deployment delete --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --resource-group rg-matchpulse-insidethegame-dev --name matchpulseitg2026 --deployment-name matchpulse-narrative
az cognitiveservices account delete --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --resource-group rg-matchpulse-insidethegame-dev --name matchpulseitg2026
az containerapp delete --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --resource-group rg-matchpulse-insidethegame-dev --name matchpulse-api-lhm35ehteauty --yes
az containerapp env delete --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --resource-group rg-matchpulse-insidethegame-dev --name matchpulse-env-lhm35ehteauty --yes
az monitor app-insights component delete --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --resource-group rg-matchpulse-insidethegame-dev --app matchpulse-appi-lhm35ehteauty
az monitor log-analytics workspace delete --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --resource-group rg-matchpulse-insidethegame-dev --workspace-name matchpulse-logs-lhm35ehteauty --yes
az resource list --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --resource-group rg-matchpulse-insidethegame-dev -o table
```

Do not delete the resource group. Confirm no challenge resource remains and
review Cost Management after usage data catches up. No cleanup operation is
authorized by this planning document.
