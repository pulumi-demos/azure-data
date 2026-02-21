# Shared Services Infrastructure

Pulumi Python stack for centralized platform services. Migrated from `bicep/shared-services.bicep`.

## Resources

| Resource | Type | Purpose |
|----------|------|---------|
| Log Analytics Workspace | `operationalinsights.Workspace` | Centralized monitoring (free tier: 500 MB/day) |
| Key Vault | `keyvault.Vault` | Secrets management with RBAC authorization |
| Managed Identity | `managedidentity.UserAssignedIdentity` | Workload authentication |
| Role Assignment | `authorization.RoleAssignment` | Key Vault Secrets Reader for identity |
| Diagnostic Settings | `insights.DiagnosticSetting` | Key Vault audit logs to Log Analytics |

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `location` | `westeurope` | Azure region for all resources |
| `environment` | `dev` | Environment name (dev, staging, prod, test) |
| `prefix` | `demo` | Short name for uniqueness (3-5 chars) |

## Outputs

- `logAnalyticsWorkspaceId` / `logAnalyticsWorkspaceName`
- `keyVaultId` / `keyVaultName` / `keyVaultUri`
- `platformIdentityId` / `platformIdentityClientId` / `platformIdentityPrincipalId`
- `resourceGroupName` / `resourceGroupId`

## Usage

```bash
cd infrastructure/shared-services
pulumi stack select dev
pulumi up
```

## Migration Notes

This stack was migrated from `bicep/shared-services.bicep`. Key differences:

- Tags updated from `managed-by: bicep` to `managed-by: pulumi`
- Resource names follow the same naming convention as the original Bicep template
- All outputs preserved for compatibility with downstream consumers
