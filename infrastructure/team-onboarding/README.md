# Team Onboarding Golden Path

This stack implements the "one-click onboarding" pattern for new teams on the Azure Data Platform.

## What Gets Created

For each team, this stack provisions:

1. **Resource Group** - Team-specific resource container
2. **Spoke VNet** - Network isolation with Databricks subnets
3. **VNet Peering** - Connectivity to hub for shared services
4. **Databricks Workspace** - Premium SKU with VNet injection
5. **Service Principal** - Entra ID app registration for Databricks access

## Key Concepts Demonstrated

### 1. Stack References

The stack references the hub-network stack to get the hub VNet ID for peering:

```python
hub_stack = StackReference("demo/hub-network/dev")
hub_vnet_id = hub_stack.get_output("vnetId")
```

### 2. Subscription as Parameter

Each team's subscription comes from their ESC environment:

```yaml
# Pulumi.team-alpha.yaml
environment:
  - azure-data/spoke-team-alpha  # Contains subscription ID
```

### 3. Compliance Tagging

All resources get mandatory tags for governance:

```python
base_tags = {
    "team": team_name,
    "environment": environment,
    "cost-center": cost_center,
    "managed-by": "pulumi",
}
```

### 4. Entra ID Integration

Creates app registration and service principal for Databricks access.

## Usage

### Onboard Team Alpha

```bash
cd infrastructure/team-onboarding
pulumi stack init team-alpha
pulumi up
```

### Onboard Team Beta

```bash
pulumi stack init team-beta
pulumi up
```

### Onboard a New Team

1. Create ESC environment: `spoke-team-<name>.yaml`
2. Create stack config: `Pulumi.team-<name>.yaml`
3. Run: `pulumi stack init team-<name> && pulumi up`

## Outputs

| Output | Description |
|--------|-------------|
| `workspaceUrl` | Databricks workspace URL |
| `workspaceId` | Databricks workspace ID |
| `vnetId` | Spoke VNet ID |
| `servicePrincipalClientId` | App registration client ID |
| `servicePrincipalPassword` | Service principal secret (hidden) |

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
