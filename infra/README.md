# Azure deployment

`infra/main.bicep` creates Azure Container Apps, Log
Analytics, and Application Insights. It does **not** create a Foundry
project or model deployment: those are usually managed in a separate AI
project and depend on an entrant-selected model and region.

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
  --resource-group <approved-resource-group> \
  --template-file infra/main.bicep \
  --parameters prefix=matchpulse \
  --parameters image=ghcr.io/OWNER/matchpulse-live@sha256:<digest>
```

`main.parameters.example.json` holds the same non-secret parameter set.

## Foundry

The template accepts a `foundryRuntimeMode` parameter (`off` by default,
`validate` to opt in) plus `foundryEndpoint`, `foundryDeployment`, and
`foundryAuthMode` (only effective in `validate` mode). The preferred mode is `managed_identity`: the Container App
gets a system-assigned identity and the service acquires a token through
`DefaultAzureCredential`. There is **no secret parameter** in the template.
In `off` mode there is no Foundry endpoint, deployment name, API key, or
model inference, and therefore no public Foundry spend.

A local API key remains available for hackathon testing only, supplied at
runtime through `FOUNDRY_API_KEY` and never committed.

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
