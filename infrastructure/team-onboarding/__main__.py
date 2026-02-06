"""
Team Onboarding Golden Path Stack

This stack demonstrates the "one-click onboarding" pattern for new teams.
It provisions a complete, compliant Databricks workspace with:
- Network isolation (VNet injection)
- Hub/spoke connectivity (peering to central hub)
- Compliance tagging (team, environment, cost-center)
- Entra ID service principal for Databricks access

Key Concepts Demonstrated:
1. Stack References - Get hub VNet ID from hub-network stack
2. Subscription as Parameter - Target subscription comes from ESC environment
3. Component Usage - Uses DatabricksWorkspaceComponent (when published)
4. Entra ID Integration - Creates app registration for service principal

For demo purposes, this stack includes inline resource creation that mirrors
what the DatabricksWorkspaceComponent does. In production, you would use:

    from pulumi_databricks_workspace import DatabricksWorkspaceComponent
    
    workspace = DatabricksWorkspaceComponent("workspace",
        team_name=team_name,
        location=location,
        subscription_id=subscription_id,
        spoke_cidr=spoke_cidr,
        hub_vnet_id=hub_vnet_id,
        environment=environment,
        cost_center=cost_center,
    )
"""

import pulumi
from pulumi import Config, StackReference, export, Output
import pulumi_azure_native as azure_native
from pulumi_azure_native import resources, network, databricks
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
hub_stack_ref_name = config.get("hubStackRef") or "demo/hub-network/dev"

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
# Compliance Tags
# =============================================================================

# These tags are mandatory for all resources
# They enable cost allocation, ownership tracking, and compliance reporting
base_tags = {
    "team": team_name,
    "environment": environment,
    "cost-center": cost_center,
    "managed-by": "pulumi",
    "project": "azure-data-platform",
    "onboarding-stack": "team-onboarding",
}

# =============================================================================
# Resource Group
# =============================================================================

resource_group = resources.ResourceGroup(
    "team-rg",
    resource_group_name=f"rg-{team_name}-{environment}",
    location=location,
    tags=base_tags,
)

# =============================================================================
# Spoke VNet with Databricks Subnets
# =============================================================================

# Calculate subnet CIDRs from spoke CIDR
# Private subnet: first /24 block (e.g., 10.1.0.0/24)
# Public subnet: second /24 block (e.g., 10.1.1.0/24)
def calculate_subnets(cidr: str) -> dict:
    parts = cidr.split("/")
    octets = parts[0].split(".")
    return {
        "private": f"{octets[0]}.{octets[1]}.0.0/24",
        "public": f"{octets[0]}.{octets[1]}.1.0/24",
    }

subnet_cidrs = Output.from_input(spoke_cidr).apply(calculate_subnets)

# NSG for Databricks private subnet
private_nsg = network.NetworkSecurityGroup(
    "private-nsg",
    network_security_group_name=f"nsg-dbw-private-{team_name}-{environment}",
    resource_group_name=resource_group.name,
    location=location,
    tags=base_tags,
)

# NSG for Databricks public subnet
public_nsg = network.NetworkSecurityGroup(
    "public-nsg",
    network_security_group_name=f"nsg-dbw-public-{team_name}-{environment}",
    resource_group_name=resource_group.name,
    location=location,
    tags=base_tags,
)

# Spoke VNet
spoke_vnet = network.VirtualNetwork(
    "spoke-vnet",
    virtual_network_name=f"vnet-{team_name}-{environment}",
    resource_group_name=resource_group.name,
    location=location,
    address_space=network.AddressSpaceArgs(
        address_prefixes=[spoke_cidr],
    ),
    tags=base_tags,
)

# Databricks private subnet (worker nodes)
private_subnet = network.Subnet(
    "private-subnet",
    subnet_name="databricks-private",
    resource_group_name=resource_group.name,
    virtual_network_name=spoke_vnet.name,
    address_prefix=subnet_cidrs.apply(lambda s: s["private"]),
    network_security_group=network.SubResourceArgs(id=private_nsg.id),
    delegations=[
        network.DelegationArgs(
            name="databricks-delegation",
            service_name="Microsoft.Databricks/workspaces",
        ),
    ],
    opts=pulumi.ResourceOptions(depends_on=[spoke_vnet, private_nsg]),
)

# Databricks public subnet (NAT connectivity)
public_subnet = network.Subnet(
    "public-subnet",
    subnet_name="databricks-public",
    resource_group_name=resource_group.name,
    virtual_network_name=spoke_vnet.name,
    address_prefix=subnet_cidrs.apply(lambda s: s["public"]),
    network_security_group=network.SubResourceArgs(id=public_nsg.id),
    delegations=[
        network.DelegationArgs(
            name="databricks-delegation",
            service_name="Microsoft.Databricks/workspaces",
        ),
    ],
    opts=pulumi.ResourceOptions(depends_on=[spoke_vnet, public_nsg, private_subnet]),
)

# =============================================================================
# VNet Peering to Hub
# =============================================================================

# Peer spoke to hub for shared services connectivity
spoke_to_hub_peering = network.VirtualNetworkPeering(
    "spoke-to-hub-peering",
    virtual_network_peering_name="spoke-to-hub",
    resource_group_name=resource_group.name,
    virtual_network_name=spoke_vnet.name,
    remote_virtual_network=network.SubResourceArgs(id=hub_vnet_id),
    allow_virtual_network_access=True,
    allow_forwarded_traffic=True,
    allow_gateway_transit=False,
    use_remote_gateways=False,
    opts=pulumi.ResourceOptions(depends_on=[spoke_vnet]),
)

# =============================================================================
# Databricks Workspace
# =============================================================================

# Managed resource group for Databricks
managed_rg_name = f"rg-dbw-managed-{team_name}-{environment}"
managed_rg_id = Output.concat(
    "/subscriptions/", subscription_id,
    "/resourceGroups/", managed_rg_name
)

# Databricks workspace with VNet injection
workspace = databricks.Workspace(
    "databricks-workspace",
    workspace_name=f"dbw-{team_name}-{environment}",
    resource_group_name=resource_group.name,
    location=location,
    managed_resource_group_id=managed_rg_id,
    sku=databricks.SkuArgs(name="premium"),
    public_network_access=databricks.PublicNetworkAccess.DISABLED,
    parameters=databricks.WorkspaceCustomParametersArgs(
        custom_virtual_network_id=databricks.WorkspaceCustomStringParameterArgs(
            value=spoke_vnet.id,
        ),
        custom_private_subnet_name=databricks.WorkspaceCustomStringParameterArgs(
            value="databricks-private",
        ),
        custom_public_subnet_name=databricks.WorkspaceCustomStringParameterArgs(
            value="databricks-public",
        ),
        enable_no_public_ip=databricks.WorkspaceCustomBooleanParameterArgs(
            value=True,
        ),
    ),
    tags=base_tags,
    opts=pulumi.ResourceOptions(depends_on=[private_subnet, public_subnet]),
)

# =============================================================================
# Entra ID / App Registration (Service Principal)
# =============================================================================

# Create an app registration for Databricks access
# This demonstrates Entra ID integration for service principal management
app_registration = azuread.Application(
    "databricks-app",
    display_name=f"sp-databricks-{team_name}-{environment}",
    owners=[],  # Will be set to current user in real deployment
)

# Create service principal from app registration
service_principal = azuread.ServicePrincipal(
    "databricks-sp",
    client_id=app_registration.client_id,
)

# Create a client secret for the service principal
# In production, consider using federated credentials instead
sp_password = azuread.ApplicationPassword(
    "databricks-sp-password",
    application_id=app_registration.id,
    display_name=f"Databricks access for {team_name}",
    end_date_relative="8760h",  # 1 year
)

# =============================================================================
# Outputs
# =============================================================================

# Workspace outputs
export("workspaceUrl", workspace.workspace_url)
export("workspaceId", workspace.workspace_id)
export("workspaceName", workspace.name)

# Resource group outputs
export("resourceGroupName", resource_group.name)
export("managedResourceGroupName", managed_rg_name)

# Network outputs
export("vnetId", spoke_vnet.id)
export("vnetName", spoke_vnet.name)
export("privateSubnetId", private_subnet.id)
export("publicSubnetId", public_subnet.id)

# Service principal outputs (for Databricks access)
export("servicePrincipalId", service_principal.id)
export("servicePrincipalClientId", app_registration.client_id)
# Note: Password is a secret, access via `pulumi stack output --show-secrets`
export("servicePrincipalPassword", pulumi.Output.secret(sp_password.value))

# Metadata
export("teamName", team_name)
export("environment", environment)
export("costCenter", cost_center)
export("location", location)
