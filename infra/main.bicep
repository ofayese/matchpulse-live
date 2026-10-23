targetScope = 'resourceGroup'

@description('Lowercase prefix used for globally scoped resource names. Hyphens are removed automatically.')
@minLength(3)
@maxLength(18)
param prefix string = 'matchpulse'

@description('Location for all resources. Defaults to the resource group location.')
param location string = resourceGroup().location

@description('The deployed image must be pinned to an immutable digest, for example ghcr.io/OWNER/REPO@sha256:DIGEST.')
param image string

@description('Foundry runtime mode. off keeps the deterministic pipeline authoritative with no model inference at all.')
@allowed([
  'off'
  'validate'
])
param foundryRuntimeMode string = 'off'

@description('Optional Microsoft Foundry / Azure OpenAI endpoint. Only used when foundryRuntimeMode is validate.')
param foundryEndpoint string = ''

@description('Optional Foundry deployment name. Only used when foundryRuntimeMode is validate.')
param foundryDeployment string = ''

@description('Foundry authentication mode. managed_identity is preferred and needs no stored secret.')
@allowed([
  'managed_identity'
  'disabled'
])
param foundryAuthMode string = 'managed_identity'

@description('Enable Application Insights and the Log Analytics workspace used for bounded cost-controlled monitoring.')
param monitoringEnabled bool = true

@description('Workspace Analytics retention in days. 30 days is the minimum workspace default; shorter retention does not reduce ingestion charges.')
@allowed([30])
param logRetentionDays int = 30

@description('Log Analytics daily ingestion cap in GB. Azure supports 0.023 GB minimum; cap overshoot can still be billed.')
// Bicep parameters are scalar strings/integers; the allow-listed string is
// converted to the REST API's numeric (double) quota value with json().
@allowed([
  '0.023'
  '0.05'
  '0.1'
  '1'
])
param logDailyQuotaGb string = '0.023'

@description('Maximum outbound Foundry calls per app process. This resets on process restart and is not a durable billing limit.')
@minValue(1)
@maxValue(20)
param foundryCallBudget int = 20

@description('Minimum container replica count. Zero keeps the workload scale to zero.')
@minValue(0)
@maxValue(1)
param minReplicas int = 0

@description('Maximum container replica count. One replica is the supported maximum until durable state exists.')
@minValue(1)
@maxValue(1)
param maxReplicas int = 1

@description('HTTP concurrency per replica used by the Container Apps scaling rule.')
@minValue(1)
@maxValue(200)
param concurrentRequestsPerReplica int = 50

var namePrefix = replace(toLower(prefix), '-', '')
var suffix = uniqueString(resourceGroup().id)
var workspaceName = '${namePrefix}-logs-${suffix}'
var environmentName = '${namePrefix}-env-${suffix}'
var appName = '${namePrefix}-api-${suffix}'
var insightsName = '${namePrefix}-appi-${suffix}'

resource logs 'Microsoft.OperationalInsights/workspaces@2025-02-01' = if (monitoringEnabled) {
  name: workspaceName
  location: location
  properties: {
    retentionInDays: logRetentionDays
    workspaceCapping: {
      dailyQuotaGb: json(logDailyQuotaGb)
    }
    features: { enableLogAccessUsingOnlyResourcePermissions: true }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    sku: { name: 'PerGB2018' }
  }
}

resource insights 'Microsoft.Insights/components@2020-02-02' = if (monitoringEnabled) {
  name: insightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logs.id
    IngestionMode: 'Basic'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: environmentName
  location: location
  properties: {
    // No workload profiles: this is the Consumption plan.
    zoneRedundant: false
    appLogsConfiguration: monitoringEnabled ? {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs!.properties.customerId
        sharedKey: logs!.listKeys().primarySharedKey
      }
    } : {
      destination: 'none'
    }
  }
}

// No Event Hubs resource is declared. The HTTP ingestion path remains the
// supported path until a real consumer, checkpoint and processed-message
// trace exist.
var insightsSecret = monitoringEnabled ? [
  {
    name: 'applicationinsights-connection-string'
    value: insights!.properties.ConnectionString
  }
] : []

var baseEnv = concat([
  {
    name: 'CHALLENGE_SYNTHETIC_ONLY'
    value: 'true'
  }
], monitoringEnabled ? [
  {
    name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
    secretRef: 'applicationinsights-connection-string'
  }
] : [])

// Foundry is off by default: no endpoint, no deployment name, no API key and
// therefore no model inference and no public spend.
var foundryEnabled = foundryRuntimeMode == 'validate' && !empty(foundryEndpoint) && !empty(foundryDeployment)

var foundryEnv = foundryEnabled ? [
  {
    name: 'FOUNDRY_ENDPOINT'
    value: foundryEndpoint
  }
  {
    name: 'FOUNDRY_DEPLOYMENT'
    value: foundryDeployment
  }
  {
    name: 'FOUNDRY_AUTH_MODE'
    value: foundryAuthMode
  }
  {
    name: 'FOUNDRY_AZURE_SCOPE'
    value: 'https://cognitiveservices.azure.com/.default'
  }
  {
    name: 'FOUNDRY_CALL_BUDGET'
    value: string(foundryCallBudget)
  }
  {
    name: 'FOUNDRY_MAX_CONCURRENCY'
    value: '1'
  }
  {
    name: 'FOUNDRY_TIMEOUT_SECONDS'
    value: '1.4'
  }
] : []

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      activeRevisionsMode: 'Single'
      secrets: insightsSecret
      ingress: {
        external: true
        targetPort: 8080
        transport: 'httpsOnly'
        allowInsecure: false
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
      }
    }
    template: {
      containers: [
        {
          name: 'matchpulse'
          image: image
          env: concat(baseEnv, foundryEnv)
          resources: { cpu: json('0.5'), memory: '1Gi' }
          probes: [
            {
              type: 'Liveness'
              httpGet: { path: '/health/live', port: 8080 }
              initialDelaySeconds: 10
              periodSeconds: 20
              failureThreshold: 3
            }
            {
              type: 'Readiness'
              httpGet: { path: '/health/ready', port: 8080 }
              initialDelaySeconds: 5
              periodSeconds: 10
              failureThreshold: 3
            }
            {
              type: 'Startup'
              httpGet: { path: '/health/live', port: 8080 }
              initialDelaySeconds: 5
              periodSeconds: 10
              failureThreshold: 12
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-concurrency'
            http: { metadata: { concurrentRequests: '${concurrentRequestsPerReplica}' } }
          }
        ]
      }
    }
  }
}

output appUrl string = 'https://${app.properties.configuration.ingress.fqdn}'
output appName string = app.name
output managedIdentityPrincipalId string = app.identity.principalId
output imageReference string = image
output minReplicas int = minReplicas
output maxReplicas int = maxReplicas
output foundryRuntimeMode string = foundryRuntimeMode
output foundryConfigured bool = foundryEnabled
output monitoringEnabled bool = monitoringEnabled
output applicationInsightsName string = monitoringEnabled ? insights.name : ''
output logAnalyticsWorkspace string = monitoringEnabled ? logs.name : ''
