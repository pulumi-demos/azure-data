# Team Onboarding Golden Path Template

A Python Pulumi template for one-click onboarding of new teams to the Azure Data Platform.
Uses two published components to provision a compliant Databricks workspace with Entra ID identity.

## What Gets Created

For each team, this template provisions:

1. **Resource Group** - Team-specific resource container
2. **Spoke VNet** - Network isolation with Databricks subnets
3. **VNet Peering** - Connectivity to hub for shared services
4. **Databricks Workspace** - Premium SKU with VNet injection
5. **Service Principal** - Entra ID app registration for Databricks access

## Usage

### Option 1: Pulumi Cloud New Project Wizard

1. Go to Pulumi Cloud > New Project
2. Select "Azure Data Team Onboarding" template
3. Fill in the configuration (team name, environment, CIDR, etc.)
4. Click "Create Project"

### Option 2: CLI

```bash
pulumi new https://github.com/pulumi-demos/azure-data/tree/main/templates/azure-data-team-onboarding
```

### Option 3: Local

```bash
mkdir my-team && cd my-team
pulumi new /path/to/azure-data/templates/azure-data-team-onboarding
```

## Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `teamName` | Your team identifier | my-team |
| `environment` | Environment (dev/staging/prod) | dev |
| `costCenter` | Cost center for chargeback | CC-UNASSIGNED |
| `spokeCidr` | Network CIDR for spoke VNet | 10.1.0.0/16 |
| `location` | Azure region | westeurope |
| `hubStackRef` | Hub network stack reference | demo/azure-data-hub-network/dev |
| `azure-native:subscriptionId` | Azure subscription ID for the spoke | _(required)_ |

## Outputs

| Output | Description |
|--------|-------------|
| `workspaceUrl` | Databricks workspace URL |
| `workspaceId` | Databricks workspace ID |
| `resourceGroupName` | Resource group name |
| `managedResourceGroupName` | Managed resource group name |
| `vnetId` | Spoke VNet ID |
| `privateSubnetId` | Databricks private subnet ID |
| `publicSubnetId` | Databricks public subnet ID |
| `servicePrincipalId` | Service principal ID |
| `servicePrincipalClientId` | App registration client ID |
| `servicePrincipalPassword` | Service principal secret (hidden) |

## Components Used

This template consumes two reusable Pulumi components:

- **[azure-data-databricks-workspace](https://github.com/pulumi-demos/azure-data-databricks-workspace)** - VNet-injected Databricks workspace with hub/spoke peering
- **[azure-data-team-entra](https://github.com/pulumi-demos/azure-data-team-entra)** - Entra ID app registration, service principal, and client secret

## Auth Note

This template creates both Azure ARM resources (via `azure-native`) and Entra ID resources
(via `azuread`). If your OIDC service principal lacks Entra ID directory permissions, configure
the `azuread` provider to use Azure CLI auth in your stack config:

```yaml
azuread:useCli: "true"
azuread:useOidc: "false"
```

## Time-to-Market Impact

| Before | After |
|--------|-------|
| 1-2 quarters | ~30 minutes |
| Manual VNet setup | Automatic |
| Copy-paste configs | Golden path |
| Ad-hoc compliance | Built-in tags |

## Cost Estimate

| Resource | Cost |
|----------|------|
| Resource Group | Free |
| VNet + Subnets | Free |
| NSGs | Free |
| Databricks Workspace | ~$0.07/DBU |
| Service Principal | Free |

**Tip**: Destroy after demo with `pulumi destroy`
