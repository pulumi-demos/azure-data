# Azure Data Platform - Project Simplify Demo

A comprehensive demo for the Internal Developer Platform (IDP) initiative, showcasing how Pulumi enables reusable infrastructure components, multi-subscription management, and governance guardrails for the Data & Analytics platform.

## Demo Overview

This demo addresses the five key agenda items for Project Simplify:

| # | Agenda Item | Demo Component |
|---|-------------|----------------|
| 1 | **Reusable Infrastructure Components** | C# multi-language component in `components/databricks-workspace` |
| 2 | **Databricks Workspace Provisioning** | Compliance + network isolation baked into component |
| 3 | **Multi-Subscription Management** | Hub/spoke architecture with subscription-as-parameter |
| 4 | **Governance Guardrails** | Python policy pack + Azure DevOps four-eyes approval |
| 5 | **Bicep Migration** | Pattern for referencing existing VNets/resources |

## Repository Structure

```
azure-data/
├── components/                          # Reusable multi-language components
│   └── databricks-workspace/            # C# component (generates Python/TS/Go/C# SDKs)
│       ├── DatabricksWorkspaceComponent.cs
│       ├── Program.cs
│       └── PulumiPlugin.yaml
│
├── infrastructure/                      # Pulumi stacks
│   ├── hub-network/                     # Central hub VNet (+ Bicep reference pattern)
│   ├── team-onboarding/                 # Golden path for team provisioning
│   └── entra-id/                        # Entra ID / App Registration management
│
├── esc-environments/                    # ESC environment definitions
│   ├── azure-base.yaml                  # OIDC credentials (no static secrets)
│   ├── hub-network.yaml                 # Hub VNet references
│   ├── spoke-template.yaml              # Template for spoke subscriptions
│   ├── spoke-team-alpha.yaml            # Team Alpha configuration
│   └── spoke-team-beta.yaml             # Team Beta configuration
│
├── policies/                            # Policy as Code
│   └── azure-compliance/                # Python policy pack
│       └── __main__.py                  # Tagging, network, naming policies
│
├── templates/                           # No-code deployment templates
│   └── team-databricks-workspace/       # YAML template for New Project Wizard
│
└── .azuredevops/                        # CI/CD configuration
    └── azure-pipelines.yml              # Four-eyes approval flow
```

## Key Concepts Demonstrated

### 1. Multi-Language Components

The `databricks-workspace` component is written in C# and automatically generates SDKs for:
- Python (for data teams)
- TypeScript
- Go
- C#

```python
# Teams write 10 lines instead of 200+
from pulumi_databricks_workspace import DatabricksWorkspaceComponent

workspace = DatabricksWorkspaceComponent("analytics",
    team_name="data-science",
    location="westeurope",
    subscription_id=config.require("subscription_id"),
    spoke_cidr="10.1.0.0/16",
    hub_vnet_id=hub_outputs["vnet_id"],
)
```

### 2. ESC Environments (OIDC, No Static Secrets)

```yaml
# azure-base.yaml - Short-lived tokens via OIDC
values:
  azure:
    clientId: "YOUR_CLIENT_ID"
    tenantId: "YOUR_TENANT_ID"
    subscriptionId: "YOUR_DEFAULT_SUBSCRIPTION_ID"
    login:
      fn::open::azure-login:
        clientId: ${azure.clientId}
        tenantId: ${azure.tenantId}
        subscriptionId: ${azure.subscriptionId}
        oidc: true
```

### 3. Stack References (Hub/Spoke)

```python
# Get hub VNet ID from another stack
hub_stack = StackReference("demo/azure-data-hub-network/dev")
hub_vnet_id = hub_stack.get_output("vnetId")
```

### 4. Subscription as Parameter

```yaml
# Each team gets their own subscription via ESC
# spoke-team-alpha.yaml
values:
  spoke:
    subscriptionId: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    network:
      cidr: "10.1.0.0/16"
```

### 5. Policy as Code (Python)

```python
# Mandatory tagging policy
def validate_required_tags(args, report_violation):
    tags = args.props.get("tags", {})
    missing = [t for t in ["team", "environment", "cost-center"] if t not in tags]
    if missing:
        report_violation(f"Missing required tags: {missing}")
```

### 6. Four-Eyes Principle (Azure DevOps)

```
Developer 1 → Creates PR → Preview runs
Developer 2 → Reviews PR → Approves
Pipeline    → Merges     → Deploys
```

## Running the Demo

### Prerequisites

- Pulumi CLI installed
- Azure subscription with appropriate permissions
- Pulumi Cloud account

### Quick Start

```bash
# Clone the repository
git clone https://github.com/pulumi-demos/azure-data.git
cd azure-data

# Set up hub network first
cd infrastructure/hub-network
pulumi stack init dev
pulumi config env add azure-data/azure-base
pulumi up

# Then onboard a team
cd ../team-onboarding
pulumi stack init team-alpha
pulumi up
```

### Cost Estimate

| Resource | Cost | Notes |
|----------|------|-------|
| Resource Groups | Free | Containers only |
| VNets + Subnets | Free | No data transfer |
| NSGs | Free | Rules only |
| Databricks Workspace | ~$0.07/DBU | Pay-per-use |
| Entra ID | Free | App registrations |

**Tip**: Run `pulumi destroy` after demo to avoid ongoing costs.

## Support

- Pulumi Documentation: https://pulumi.com/docs
- ESC Documentation: https://pulumi.com/docs/esc
- Azure Native Provider: https://pulumi.com/registry/packages/azure-native
