# Azure provider registration and managed-identity RBAC plan

No provider registration or role assignment was performed.

## Providers

Use the explicit subscription in every registration/verification command.

| Namespace | Required? | Current state | Reason / cost | Scope |
| --- | --- | --- | --- | --- |
| `Microsoft.App` | Yes | Registered in prior readback | Container Apps; registration itself has no direct meter | Subscription |
| `Microsoft.CognitiveServices` | Yes | Registered in prior readback | Azure OpenAI account/model; registration itself has no direct meter | Subscription |
| `Microsoft.OperationalInsights` | Yes | Not registered in prior readback | Log Analytics workspace; no direct charge from registration, later workspace ingestion is billable | Subscription |
| `Microsoft.Insights` | Yes | Not registered in prior readback | Application Insights and ACA Azure Monitor logging; no direct registration cost | Subscription |
| `Microsoft.ManagedIdentity` | No | Not registered in prior readback | Only needed for standalone user-assigned identity resources; the app uses a system-assigned identity created as part of `Microsoft.App/containerApps` | N/A |
| `Microsoft.EventHub` | No | Not registered in prior readback | Event Hubs excluded | N/A |
| `Microsoft.ContainerRegistry` | No | Not registered in prior readback | GHCR digest is used; ACR excluded | N/A |

The two currently unregistered required namespaces are subscription-wide
operations and need explicit billable deployment approval even though
registration itself does not deploy a metered service. Registration can take a
few minutes or longer; verify state before provisioning.

```bash
az provider register --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --namespace Microsoft.OperationalInsights
az provider register --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --namespace Microsoft.Insights
az provider show --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --namespace Microsoft.OperationalInsights --query registrationState -o tsv
az provider show --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc --namespace Microsoft.Insights --query registrationState -o tsv
```

There is no practical rollback for provider registration; it can be
unregistered, but doing so can disrupt existing resources/services. Do not
unregister automatically during cleanup.

## Model access role

After the Container App identity and Azure OpenAI account exist, assign
`Cognitive Services OpenAI User` only at this account scope:

```bash
az role assignment create \
  --subscription 13b00900-43c4-4cdc-aba3-4a8bb13e61cc \
  --assignee-object-id <container-app-principal-id> \
  --assignee-principal-type ServicePrincipal \
  --role "Cognitive Services OpenAI User" \
  --scope /subscriptions/13b00900-43c4-4cdc-aba3-4a8bb13e61cc/resourceGroups/rg-matchpulse-insidethegame-dev/providers/Microsoft.CognitiveServices/accounts/matchpulseitg2026
```

Verify the exact role and scope, wait for propagation, then test from the app.
Remove only that assignment by exact assignment ID during cleanup. No
subscription-wide role is planned.

Microsoft documents system-assigned identities as properties of supported
compute resource types such as `Microsoft.App/containerApps`; standalone
`Microsoft.ManagedIdentity/userAssignedIdentities` resources are a separate
resource type. Therefore separate `Microsoft.ManagedIdentity` registration is
not required for this architecture. See [supported resource types](https://learn.microsoft.com/entra/identity/managed-identities-azure-resources/managed-identities-status)
and [Container Apps identities](https://learn.microsoft.com/azure/container-apps/managed-identity).
