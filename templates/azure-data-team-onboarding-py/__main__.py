"""${PROJECT} - ${DESCRIPTION}"""

import pulumi
from pulumi import Config, StackReference, export
import pulumi_pulumi_resource_databricks_workspace as dbw
import pulumi_azuread as azuread

# =============================================================================
# Configuration
# =============================================================================

config = Config()

team_name = config.require("teamName")
environment = config.get("environment") or "dev"
cost_center = config.get("costCenter") or "unassigned"
spoke_cidr = config.require("spokeCidr")
hub_stack_ref_name = config.get("hubStackRef") or "demo/azure-data-hub-network/dev"

azure_config = Config("azure-native")
subscription_id = azure_config.require("subscriptionId")

# =============================================================================
# Stack Reference - Hub VNet
# =============================================================================

hub_stack = StackReference(hub_stack_ref_name)
hub_vnet_id = hub_stack.get_output("vnetId")
location = hub_stack.get_output("location").apply(lambda loc: loc or "westeurope")

# =============================================================================
# Databricks Workspace (via published component)
# =============================================================================

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
# Entra ID Service Principal
# =============================================================================

current_client = azuread.get_client_config()
app_registration = azuread.Application(
    "databricks-app",
    display_name=f"sp-dbw-{team_name}-{environment}",
    owners=[current_client.object_id],
)

service_principal = azuread.ServicePrincipal(
    "databricks-sp",
    client_id=app_registration.client_id,
)

sp_password = azuread.ApplicationPassword(
    "databricks-sp-password",
    application_id=app_registration.id,
    display_name=f"Databricks access for {team_name}",
    end_date_relative="8760h",  # 1 year
)

# =============================================================================
# Outputs
# =============================================================================

export("workspaceUrl", workspace.workspace_url)
export("workspaceId", workspace.workspace_id)
export("resourceGroupName", workspace.resource_group_name)
export("managedResourceGroupName", workspace.managed_resource_group_name)
export("vnetId", workspace.network_config.apply(lambda nc: nc.vnet_id))
export("privateSubnetId", workspace.network_config.apply(lambda nc: nc.private_subnet_id))
export("publicSubnetId", workspace.network_config.apply(lambda nc: nc.public_subnet_id))
export("servicePrincipalId", service_principal.id)
export("servicePrincipalClientId", app_registration.client_id)
export("servicePrincipalPassword", pulumi.Output.secret(sp_password.value))
export("teamName", team_name)
export("environment", environment)
export("costCenter", cost_center)
export("location", location)
