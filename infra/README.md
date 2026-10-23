# Azure deployment

`infra/main.bicep` creates Azure Container Apps, Log Analytics, and
Application Insights. It does **not** create the Azure OpenAI account or model
deployment; those require a separate approved operation.

## Validate first

```bash
az bicep build --file infra/main.bicep
```

or run the guard script, which also asserts that the compiled template has no
hardcoded subscription id, tenant id, or secret literal:

```bash
bash infra/validate.sh
powershell -ExecutionPolicy Bypass -File infra\validate.ps1
```

## Deploy

> Creating these resources is billable. Use an explicitly approved
> subscription and resource group.

```bash
az deployment group create \
  --subscription <approved-subscription-id> \
  --resource-group <approved-resource-group> \
  --template-file infra/main.bicep \
  --parameters prefix=matchpulse \
  --parameters @infra/main.parameters.example.json
```

`main.parameters.example.json` holds the non-secret parameter set and accepted
immutable image digest. Review the values and endpoint before deployment.

## Foundry

The template accepts `foundryRuntimeMode` (`off` by default, `validate` to opt
in), `foundryEndpoint`, `foundryDeployment`, and `foundryAuthMode`. Azure
OpenAI is recommended because the application adapter uses the Azure OpenAI
chat-completions route. The endpoint must come from the approved created
account; never commit a proposed endpoint as active. The Container App uses a
system-assigned identity and requests a token through `DefaultAzureCredential`.
No key parameter exists. In `off` mode there is no model inference.

A local API key remains available for hackathon testing only, supplied at
runtime through `FOUNDRY_API_KEY` and never committed.

The workspace uses `workspaceCapping.dailyQuotaGb` with the supported 0.023
GB/day minimum. Cap overshoot may be billed, and reaching the cap can pause log
ingestion. Container Apps console and system logs are routed to the workspace;
HTTP diagnostic categories remain disabled. The app adapter makes one model
request attempt, times out at 1.4 seconds by default, limits output to 128
tokens and prompt payload to 4 KiB, then uses deterministic fallback. Its
per-process call budget resets on restart. These controls are not a hard billing
stop.

## After deployment

```bash
curl -fsS "$APP_URL/health/live"
curl -fsS "$APP_URL/health/ready"
python -m matchpulse.synthetic --url "$APP_URL" --delay .2 --events 50
```

Capture the Container App revision, the Application Insights request chart for the architecture portion of the demo. The current
MVP ingests over HTTP. Event Hubs is NOT part of the deployed baseline.

Full guidance, including cleanup, is in
[`../docs/AZURE_DEPLOYMENT.md`](../docs/AZURE_DEPLOYMENT.md).
