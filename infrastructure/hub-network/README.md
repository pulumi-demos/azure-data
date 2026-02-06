# Hub Network Infrastructure

This stack creates or references the central hub network for the Azure Data Platform hub/spoke architecture.

## Features

- **Hub VNet**: Central network for shared services
- **Shared Services Subnet**: For private endpoints, DNS, etc.
- **Gateway Subnet**: Reserved for VPN/ExpressRoute
- **NSG**: Network security rules for hub traffic
- **Bicep Migration Pattern**: Can reference existing resources

## Usage

### Create New Hub Network

```bash
cd infrastructure/hub-network
pulumi stack init dev
pulumi config env add azure-data/azure-base
pulumi up
```

### Reference Existing Bicep-Deployed Network

If your hub network was deployed via Bicep/ARM and you want to reference it:

```bash
pulumi config set useExisting true
pulumi config set existingResourceGroupName "rg-hub-network-prod"
pulumi config set existingVnetName "vnet-hub-prod"
pulumi up
```

## Outputs

| Output | Description |
|--------|-------------|
| `resourceGroupName` | Hub resource group name |
| `vnetId` | Hub VNet resource ID (for spoke peering) |
| `vnetName` | Hub VNet name |
| `sharedServicesSubnetId` | Shared services subnet ID |
| `location` | Azure region |
| `mode` | "created" or "existing" |

## Stack References

Spoke stacks can reference hub outputs:

```python
hub_stack = pulumi.StackReference("demo/hub-network/dev")
hub_vnet_id = hub_stack.get_output("vnetId")
```
