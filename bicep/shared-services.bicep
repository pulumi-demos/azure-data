// Shared Services Infrastructure — Bicep
//
// Deploys centralized platform services that teams consume: Key Vault for
// secrets management, Log Analytics for monitoring, and a managed identity
// for workload authentication. Represents the kind of pre-existing shared
// infra a data platform team would migrate to Pulumi.
//
// All resources are free or effectively free at demo scale.
//
// Deploy:
//   az group create -n rg-shared-services-dev -l westeurope
//   az deployment group create -g rg-shared-services-dev -f shared-services.bicep

@description('Azure region for all resources')
param location string = 'westeurope'

@description('Environment name')
@allowed(['dev', 'staging', 'prod', 'test'])
param environment string = 'dev'

@description('Short name for uniqueness (3-5 chars, lowercase)')
@minLength(3)
@maxLength(5)
param prefix string = 'demo'

// --- Tags ---
var tags = {
  environment: environment
  'managed-by': 'bicep'
  project: 'shared'
  component: 'shared-services'
}

// --- Log Analytics Workspace (free tier: 500 MB/day ingestion) ---
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-${prefix}-platform-${environment}'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018' // free up to 500 MB/day with 5 GB retention
    }
    retentionInDays: 30
  }
}

// --- Key Vault (no cost until you store secrets / perform operations) ---
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'kv-${prefix}-plat-${environment}'
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enablePurgeProtection: false // keep false for easy demo cleanup
    networkAcls: {
      defaultAction: 'Allow' // tighten in prod
      bypass: 'AzureServices'
    }
  }
}

// --- User-Assigned Managed Identity (free) ---
resource platformIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-${prefix}-platform-${environment}'
  location: location
  tags: tags
}

// Grant the managed identity Key Vault Secrets Reader (built-in role)
// Role ID: 4633458b-17de-408a-b874-0445c86b69e6
resource kvSecretsReaderAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, platformIdentity.id, '4633458b-17de-408a-b874-0445c86b69e6')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: platformIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// --- Diagnostic Settings: send Key Vault logs to Log Analytics ---
resource kvDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'send-to-log-analytics'
  scope: keyVault
  properties: {
    workspaceId: logAnalytics.id
    logs: [
      {
        categoryGroup: 'audit'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

// --- Outputs ---
output logAnalyticsWorkspaceId string = logAnalytics.id
output logAnalyticsWorkspaceName string = logAnalytics.name
output keyVaultId string = keyVault.id
output keyVaultName string = keyVault.name
output keyVaultUri string = keyVault.properties.vaultUri
output platformIdentityId string = platformIdentity.id
output platformIdentityClientId string = platformIdentity.properties.clientId
output platformIdentityPrincipalId string = platformIdentity.properties.principalId
