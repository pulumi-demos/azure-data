"""
Team Onboarding Golden Path Stack

This stack demonstrates the "one-click onboarding" pattern for new teams.
It uses the published DatabricksWorkspaceComponent to provision a complete,
compliant Databricks workspace with:
- Network isolation (VNet injection)
- Hub/spoke connectivity (peering to central hub)
- Compliance tagging (team, environment, cost-center)
- Entra ID service principal for Databricks access

Key Concepts Demonstrated:
1. Component Abstraction - ~150 lines of infra replaced by a single component
2. Stack References - Get hub VNet ID from hub-network stack
3. Subscription as Parameter - Target subscription comes from ESC environment
4. Entra ID Integration - Creates app registration for service principal
"""

import pulumi
from pulumi import Config, StackReference, export
import pulumi_demos_azure_data_databricks_workspace as dbw
import pulumi_demos_azure_data_team_entra as entra
import pulumi_azuread as azuread

# =============================================================================
# Configuration
# =============================================================================

config = Config()

# Team configuration (from ESC environment or stack config)
team_name = config.require("teamName")
environment = config.get("environment") or "dev"
cost_center = config.get("costCenter") or "unassigned"
spoke_cidr = config.require("spokeCidr")

# Hub stack reference for peering
hub_stack_ref_name = config.get("hubStackRef") or "demo/azure-data-hub-network/dev"

# Azure configuration (from ESC environment)
azure_config = Config("azure-native")
subscription_id = azure_config.require("subscriptionId")
location = config.get("location") or "westeurope"

# =============================================================================
# Stack Reference - Get Hub VNet ID
# =============================================================================

# This demonstrates cross-stack references
# The hub-network stack exports vnetId which we use for peering
hub_stack = StackReference(hub_stack_ref_name)
hub_vnet_id = hub_stack.get_output("vnetId")
hub_location = hub_stack.get_output("location")

# Use hub location if not specified
location = hub_location.apply(lambda loc: loc if loc else "westeurope")

# =============================================================================
# Databricks Workspace (via published component)
# =============================================================================

# The DatabricksWorkspaceComponent encapsulates:
# - Resource group, spoke VNet with Databricks subnets and NSGs
# - VNet peering to hub for shared services connectivity
# - Databricks workspace with VNet injection and no public IP
# - Compliance tags applied to all resources
workspace = dbw.DatabricksWorkspaceComponent("workspace",
    team_name=team_name,
    location=location,
    subscription_id=subscription_id,
    spoke_cidr=spoke_cidr,
    hub_vnet_id=hub_vnet_id,
    environment=environment,
    cost_center=cost_center,
    tags={
        "project": "azure-data-platform",
        "onboarding-stack": "team-onboarding",
    },
)

# =============================================================================
# Entra ID / App Registration (via published component)
# =============================================================================

# The TeamEntraComponent encapsulates:
# - Entra ID Application (app registration)
# - Service Principal bound to the application
# - Client secret with configurable rotation
current_client = azuread.get_client_config()
identity = entra.TeamEntraComponent("identity",
    team_name=team_name,
    environment=environment,
    owners=[current_client.object_id],
)

# =============================================================================
# Outputs
# =============================================================================

# Workspace outputs (from component)
export("workspaceUrl", workspace.workspace_url)
export("workspaceId", workspace.workspace_id)

# Resource group outputs (from component)
export("resourceGroupName", workspace.resource_group_name)
export("managedResourceGroupName", workspace.managed_resource_group_name)

# Network outputs (from component)
export("vnetId", workspace.network_config.apply(lambda nc: nc.vnet_id))
export("privateSubnetId", workspace.network_config.apply(lambda nc: nc.private_subnet_id))
export("publicSubnetId", workspace.network_config.apply(lambda nc: nc.public_subnet_id))

# Service principal outputs (from component)
export("servicePrincipalId", identity.service_principal_id)
export("servicePrincipalClientId", identity.client_id)
# Note: Password is a secret, access via `pulumi stack output --show-secrets`
export("servicePrincipalPassword", identity.service_principal_password)

# Metadata
export("teamName", team_name)
export("environment", environment)
export("costCenter", cost_center)
export("location", location)
