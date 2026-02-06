# Entra ID (Azure AD) Management

This stack manages Entra ID resources for the Azure Data Platform.

## What Gets Created

1. **Databricks App Registration** - Identity for Databricks access
2. **Pipeline App Registration** - Identity for CI/CD pipeline
3. **Service Principals** - For both app registrations
4. **Federated Credentials** - OIDC auth for Pulumi and Azure DevOps
5. **Security Group** - For Databricks administrators

## Key Concepts

### App Registration vs Service Principal

- **App Registration**: The identity definition (like a template)
- **Service Principal**: The instance of that identity in your tenant

### Federated Credentials (OIDC)

Instead of storing secrets, use federated credentials:
- Pulumi Deployments authenticates via OIDC
- Azure DevOps authenticates via OIDC
- No secrets to rotate or leak

## Usage

```bash
cd infrastructure/entra-id
pulumi stack init dev
pulumi config env add azure-data/azure-base
pulumi up
```

## Outputs

| Output | Description |
|--------|-------------|
| `databricksAppClientId` | Client ID for Databricks SP |
| `pipelineAppClientId` | Client ID for pipeline SP |
| `databricksAdminsGroupId` | Security group ID |

## ESC Integration

After deployment, update your ESC environment:

```yaml
values:
  azure:
    clientId: <databricksAppClientId output>
    # Federated credentials - no secret needed!
```
