# Proposed Azure OpenAI plan

**Proposal only. No account or model deployment exists.** The proposed account
name and endpoint below are placeholders for a later approved operation; check
global name availability before use.

## Resource type

Use an Azure OpenAI resource: `Microsoft.CognitiveServices/accounts`,
`kind: OpenAI`, `sku: S0`. The application adapter calls the Azure OpenAI
`/openai/deployments/{deployment}/chat/completions` route and uses the
`https://cognitiveservices.azure.com/.default` managed-identity scope. This is
the smallest change and the most direct fit. A unified Microsoft Foundry
`AIServices` account supports Azure OpenAI models too, but its platform/project
surface is unnecessary for this single-model adapter. The application still
uses Microsoft Foundry model services; choosing the Azure OpenAI resource kind
does not require a Foundry project.

## Account and endpoint

- Proposed account name: `matchpulseitg2026` (availability unverified).
- Subscription: `Subscription 1`, `13b00900-43c4-4cdc-aba3-4a8bb13e61cc`.
- Resource group: `rg-matchpulse-insidethegame-dev`.
- Region: `eastus2`; fallback `eastus` only after a new quota/availability check.
- Proposed endpoint format: `https://matchpulseitg2026.openai.azure.com/`.
- Status: **PROPOSED - NOT DEPLOYED**. It is stored only in the what-if
  evidence parameters and not committed to application configuration.
- Public network: enabled for the public HTTPS Container App to reach the
  service. No private endpoint or VNet is included.
- No key is stored. Default content filtering remains enabled; no custom filter
  is proposed. Do not send real match or personal data; challenge data is
  synthetic.

## Model deployment

- Model: GPT-4o-mini, version `2024-07-18`.
- Deployment name/alias: `matchpulse-narrative`.
- Type: Standard pay-as-you-go, not provisioned throughput.
- Capacity: 1 unit = 1,000 TPM for older chat models per the current quota
  guidance; this is the smallest supported unit and is sufficient for the
  bounded challenge usage. Subscription quota observed at 200,000 TPM allocated
  and 0 used, so the planned deployment would consume 1,000 TPM, subject to
  confirming model/version capacity again before creation.
- Expected token cost uses regional observed rates: $0.165/1M input tokens and
  $0.66/1M output tokens. Quota is a throughput limit, not a spending limit.

## Commands for a separately approved deployment (not run)

```bash
az cognitiveservices account create \
  --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc \
  --resource-group rg-matchpulse-insidethegame-dev \
  --name matchpulseitg2026 \
  --location eastus2 \
  --kind OpenAI \
  --sku S0 \
  --custom-domain matchpulseitg2026

az cognitiveservices account deployment create \
  --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc \
  --resource-group rg-matchpulse-insidethegame-dev \
  --name matchpulseitg2026 \
  --deployment-name matchpulse-narrative \
  --model-name gpt-4o-mini \
  --model-version 2024-07-18 \
  --model-format OpenAI \
  --sku-name Standard \
  --sku-capacity 1
```

Then read the actual endpoint with
`az cognitiveservices account show --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --resource-group rg-matchpulse-insidethegame-dev --name matchpulseitg2026 --query properties.endpoint -o tsv`.
No command in this document has been executed.

Sources: [Foundry resource types](https://learn.microsoft.com/azure/ai-foundry/concepts/architecture),
[Azure OpenAI endpoint format](https://learn.microsoft.com/azure/ai-foundry/model-inference/concepts/endpoints),
[quota and capacity units](https://learn.microsoft.com/azure/foundry/openai/how-to/quota),
[model deployment automation](https://learn.microsoft.com/azure/foundry/openai/how-to/automate-quota-deployments),
[account CLI](https://learn.microsoft.com/cli/azure/cognitiveservices/account),
[deployment CLI](https://learn.microsoft.com/cli/azure/cognitiveservices/account/deployment).
