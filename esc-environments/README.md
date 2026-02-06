# ESC Environments for Azure Data Platform

This directory contains Pulumi ESC (Environments, Secrets, and Configuration) definitions for the Azure Data & Analytics platform.

## Environment Hierarchy

```
azure-base                    # Base Azure OIDC credentials
    │
    └── hub-network           # Hub VNet references (existing Bicep resources)
            │
            └── spoke-template    # Template for spoke subscriptions
                    │
                    ├── spoke-team-alpha  # Team Alpha's spoke
                    └── spoke-team-beta   # Team Beta's spoke
```

## Key Concepts Demonstrated

### 1. OIDC Authentication (No Static Secrets)

The `azure-base` environment uses Azure OIDC for authentication:
- Short-lived tokens (no stored secrets)
- Federated credentials via Azure AD
- Automatic token refresh

### 2. Referencing Existing Resources (Bicep Migration)

The `hub-network` environment shows how to reference existing infrastructure:
- Hub VNet deployed via Bicep/ARM
- Exposed as ESC values for Pulumi consumption
- No need to re-deploy existing resources

### 3. Subscription as Parameter (Multi-Subscription)

The `spoke-template` and team-specific environments demonstrate:
- Each team gets their own subscription
- Network CIDR allocation per team
- Inherited credentials with subscription override

## Usage

### Creating ESC Environments

```bash
# Create the environments in Pulumi Cloud
pulumi env init demo/azure-data/azure-base -f ./azure-base.yaml
pulumi env init demo/azure-data/hub-network -f ./hub-network.yaml
pulumi env init demo/azure-data/spoke-template -f ./spoke-template.yaml
pulumi env init demo/azure-data/spoke-team-alpha -f ./spoke-team-alpha.yaml
```

### Linking to Stacks

```bash
# In your Pulumi project directory
pulumi config env add azure-data/spoke-team-alpha

# Verify configuration
pulumi config
```

### Using with Azure CLI

```bash
# Run Azure CLI commands with ESC credentials
pulumi env run demo/azure-data/spoke-team-alpha -- az account show
```

## Onboarding a New Team

1. Copy `spoke-template.yaml` to `spoke-team-<name>.yaml`
2. Update the values:
   - `teamName`: Team identifier
   - `subscriptionId`: Team's Azure subscription
   - `network.cidr`: Unique CIDR allocation
   - `costCenter`: Chargeback code
3. Create the environment:
   ```bash
   pulumi env init demo/azure-data/spoke-team-<name>
   pulumi env edit demo/azure-data/spoke-team-<name> --file ./spoke-team-<name>.yaml
   ```
4. Team can now use the environment in their stacks

## Security Considerations

- **No static secrets**: All authentication uses OIDC
- **Least privilege**: Each team's service principal has access only to their subscription
- **Audit trail**: All environment access is logged in Pulumi Cloud
- **Version control**: Environment definitions are stored in Git

## Cost Allocation

Each spoke environment includes a `costCenter` value that is:
- Applied as a tag to all resources
- Used for chargeback reporting
- Required for compliance
