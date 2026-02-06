# Azure Compliance Policy Pack

Python-based policy pack that enforces governance guardrails for the Azure Data Platform.

## Policies Included

### Tagging Policies (Mandatory)

| Policy | Description |
|--------|-------------|
| `required-tags` | All Azure resources must have: team, environment, cost-center |
| `valid-environment-tag` | Environment tag must be: dev, staging, prod, test |

### Network Isolation Policies (Mandatory)

| Policy | Description |
|--------|-------------|
| `no-public-ip` | Prevents creation of public IP addresses |
| `databricks-vnet-injection` | Databricks must use VNet injection |
| `databricks-no-public-ip` | Databricks must have public IP disabled |
| `databricks-public-access-disabled` | Databricks public network access disabled (advisory) |

### Naming Convention Policies (Advisory)

| Policy | Description |
|--------|-------------|
| `naming-convention` | Resources must follow naming patterns (rg-, vnet-, nsg-, dbw-) |
| `subnet-naming-convention` | Subnets must follow patterns (snet-, databricks-, GatewaySubnet) |

### Security Policies (Advisory)

| Policy | Description |
|--------|-------------|
| `databricks-premium-sku` | Databricks should use Premium SKU for Unity Catalog |

## Usage

### Local Testing

```bash
cd infrastructure/team-onboarding
pulumi preview --policy-pack ../../policies/azure-compliance
```

### Organization-Wide Enforcement

1. Publish the policy pack:
   ```bash
   cd policies/azure-compliance
   pulumi policy publish
   ```

2. Enable in Pulumi Cloud:
   - Go to Organization Settings > Policy Packs
   - Enable the policy pack for your organization
   - Set enforcement level (advisory or mandatory)

## Enforcement Levels

- **mandatory**: Blocks deployment if violated
- **advisory**: Warns but allows deployment
- **disabled**: Policy not enforced

## Example Violations

### Missing Tags

```
Policy violation: required-tags
Resource 'my-rg' is missing required tags: team, cost-center.
All Azure resources must have tags for: team, environment, cost-center
```

### Public IP Creation

```
Policy violation: no-public-ip
Public IP address 'my-pip' is not allowed.
Use private endpoints or VNet injection for network connectivity.
```

### Databricks Without VNet Injection

```
Policy violation: databricks-vnet-injection
Databricks workspace 'my-workspace' must use VNet injection.
Set parameters.customVirtualNetworkId to enable network isolation.
```

## Customization

Edit `__main__.py` to:
- Add new policies
- Change enforcement levels
- Modify validation logic
- Add organization-specific rules

## Four-Eyes Principle

This policy pack supports the four-eyes principle:
1. Developer creates PR with infrastructure changes
2. Policy pack runs during `pulumi preview` in CI
3. Second developer reviews policy results in PR
4. Merge triggers deployment only if policies pass
