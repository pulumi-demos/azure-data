"""
Shared Services Infrastructure Stack

Migrated from: bicep/shared-services.bicep

Deploys centralized platform services that teams consume:
- Key Vault for secrets management
- Log Analytics for monitoring
- Managed Identity for workload authentication

All resources are free or effectively free at demo scale.
"""

from pulumi import Config, export, Output
from pulumi_azure_native import (
    resources,
    operationalinsights,
    keyvault,
    managedidentity,
    authorization,
    insights,
)

# Configuration
config = Config()
azure_config = Config("azure-native")

location = config.get("location") or azure_config.get("location") or "westeurope"
environment = config.get("environment") or "dev"
prefix = config.get("prefix") or "demo"

# Standard tags for all resources (matching Bicep template)
tags = {
    "environment": environment,
    "managed-by": "pulumi",
    "project": "shared",
    "component": "shared-services",
}

# Resource Group
resource_group = resources.ResourceGroup(
    "shared-services-rg",
    resource_group_name=f"rg-shared-services-{environment}",
    location=location,
    tags=tags,
)

# Log Analytics Workspace (free tier: 500 MB/day ingestion)
log_analytics = operationalinsights.Workspace(
    "log-analytics",
    workspace_name=f"log-{prefix}-platform-{environment}",
    resource_group_name=resource_group.name,
    location=location,
    sku=operationalinsights.WorkspaceSkuArgs(
        name=operationalinsights.WorkspaceSkuNameEnum.PER_GB2018,
    ),
    retention_in_days=30,
    tags=tags,
)

# Key Vault (no cost until you store secrets / perform operations)
# Get current tenant ID from Azure subscription
client_config = authorization.get_client_config()

key_vault = keyvault.Vault(
    "key-vault",
    vault_name=f"kv-{prefix}-plat-{environment}",
    resource_group_name=resource_group.name,
    location=location,
    properties=keyvault.VaultPropertiesArgs(
        sku=keyvault.SkuArgs(
            family=keyvault.SkuFamily.A,
            name=keyvault.SkuName.STANDARD,
        ),
        tenant_id=client_config.tenant_id,
        enable_rbac_authorization=True,
        enable_soft_delete=True,
        soft_delete_retention_in_days=7,
        enable_purge_protection=False,  # Keep false for easy demo cleanup
        network_acls=keyvault.NetworkRuleSetArgs(
            default_action=keyvault.NetworkRuleAction.ALLOW,
            bypass=keyvault.NetworkRuleBypassOptions.AZURE_SERVICES,
        ),
    ),
    tags=tags,
)

# User-Assigned Managed Identity (free)
platform_identity = managedidentity.UserAssignedIdentity(
    "platform-identity",
    resource_name_=f"id-{prefix}-platform-{environment}",
    resource_group_name=resource_group.name,
    location=location,
    tags=tags,
)

# Grant the managed identity Key Vault Secrets Reader (built-in role)
# Role ID: 4633458b-17de-408a-b874-0445c86b69e6
KEY_VAULT_SECRETS_READER_ROLE_ID = "4633458b-17de-408a-b874-0445c86b69e6"

kv_secrets_reader_assignment = authorization.RoleAssignment(
    "kv-secrets-reader-assignment",
    # Scope to the Key Vault
    scope=key_vault.id,
    role_definition_id=Output.concat(
        "/subscriptions/",
        client_config.subscription_id,
        "/providers/Microsoft.Authorization/roleDefinitions/",
        KEY_VAULT_SECRETS_READER_ROLE_ID,
    ),
    principal_id=platform_identity.principal_id,
    principal_type=authorization.PrincipalType.SERVICE_PRINCIPAL,
)

# Diagnostic Settings: send Key Vault logs to Log Analytics
kv_diagnostics = insights.DiagnosticSetting(
    "kv-diagnostics",
    name="send-to-log-analytics",
    resource_uri=key_vault.id,
    workspace_id=log_analytics.id,
    logs=[
        insights.LogSettingsArgs(
            category_group="audit",
            enabled=True,
        ),
    ],
    metrics=[
        insights.MetricSettingsArgs(
            category="AllMetrics",
            enabled=True,
        ),
    ],
)

# Outputs (matching Bicep template outputs)
export("logAnalyticsWorkspaceId", log_analytics.id)
export("logAnalyticsWorkspaceName", log_analytics.name)
export("keyVaultId", key_vault.id)
export("keyVaultName", key_vault.name)
export("keyVaultUri", key_vault.properties.apply(lambda p: p.vault_uri if p else ""))
export("platformIdentityId", platform_identity.id)
export("platformIdentityClientId", platform_identity.client_id)
export("platformIdentityPrincipalId", platform_identity.principal_id)

# Additional useful outputs
export("resourceGroupName", resource_group.name)
export("resourceGroupId", resource_group.id)
export("location", location)
export("environment", environment)
