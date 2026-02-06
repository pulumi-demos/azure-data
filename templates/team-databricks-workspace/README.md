# Team Databricks Workspace Template

A no-code Pulumi template for provisioning compliant Databricks workspaces.

## Features

- **No-Code Deployment**: YAML-based, no programming required
- **Compliant by Default**: VNet injection, no public IP, compliance tags
- **Hub/Spoke Ready**: Automatic peering to central hub
- **New Project Wizard**: Works with Pulumi Cloud's New Project Wizard

## Usage

### Option 1: Pulumi Cloud New Project Wizard

1. Go to Pulumi Cloud > New Project
2. Select "Team Databricks Workspace" template
3. Fill in the configuration:
   - Team Name
   - Environment
   - Cost Center
   - Network CIDR
4. Click "Create Project"

### Option 2: CLI

```bash
pulumi new https://github.com/pulumi-demos/azure-data/templates/team-databricks-workspace
```

### Option 3: Git-Based Deployment

1. Fork/clone this repository
2. Navigate to `templates/team-databricks-workspace`
3. Configure your stack:
   ```bash
   pulumi stack init my-team-dev
   pulumi config set teamName my-team
   pulumi config set environment dev
   pulumi config set costCenter CC-12345
   pulumi config set spokeCidr "10.1.0.0/16"
   ```
4. Deploy:
   ```bash
   pulumi up
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

## What Gets Created

1. **Resource Group**: `rg-{teamName}-{environment}`
2. **Spoke VNet**: `vnet-{teamName}-{environment}`
3. **Subnets**: `databricks-private`, `databricks-public`
4. **NSGs**: Network security groups for each subnet
5. **VNet Peering**: Connection to hub network
6. **Databricks Workspace**: `dbw-{teamName}-{environment}`

## Outputs

| Output | Description |
|--------|-------------|
| `workspaceUrl` | Databricks workspace URL |
| `workspaceId` | Databricks workspace ID |
| `resourceGroupName` | Resource group name |
| `vnetId` | Spoke VNet ID |

## One-Click Onboarding

This template enables the "one-click onboarding" vision:

1. **Before**: 1-2 quarters to onboard a new team
2. **After**: ~30 minutes with this template

Teams simply:
1. Select the template
2. Fill in their team details
3. Click deploy

All compliance, networking, and security is handled automatically.

## Customization

To customize this template for your organization:

1. Fork the repository
2. Modify `Main.yaml` to add/remove resources
3. Update `Pulumi.yaml` template metadata
4. Publish to your organization's template registry
