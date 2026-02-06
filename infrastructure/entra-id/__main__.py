"""
Entra ID (Azure AD) Management Stack

This stack demonstrates Entra ID integration for the Azure Data Platform:
1. App Registration for Databricks service principal
2. Service Principal creation
3. Federated credentials for OIDC (Pulumi Deployments)
4. Role assignments for Azure resources

Key Concepts:
- App Registrations vs Service Principals
- Federated credentials for passwordless auth
- RBAC role assignments
- Secret management best practices
"""

import pulumi
from pulumi import Config, export, Output
import pulumi_azuread as azuread

# =============================================================================
# Configuration
# =============================================================================

config = Config()
environment = config.get("environment") or "dev"

# Azure AD configuration
azuread_config = Config("azuread")

# =============================================================================
# App Registration for Databricks Access
# =============================================================================

# Create an app registration for Databricks service principal
# This is the identity that will be used to access Databricks APIs
databricks_app = azuread.Application(
    "databricks-platform-app",
    display_name=f"sp-databricks-platform-{environment}",
    description="Service principal for Azure Data Platform Databricks access",
    # Sign-in audience
    sign_in_audience="AzureADMyOrg",
    # API permissions (optional - add as needed)
    # required_resource_accesses=[
    #     azuread.ApplicationRequiredResourceAccessArgs(
    #         resource_app_id="2ff814a6-3304-4ab8-85cb-cd0e6f879c1d",  # Azure Databricks
    #         resource_accesses=[
    #             azuread.ApplicationRequiredResourceAccessResourceAccessArgs(
    #                 id="...",
    #                 type="Scope",
    #             ),
    #         ],
    #     ),
    # ],
    # Tags for organization
    tags=[
        f"environment:{environment}",
        "managed-by:pulumi",
        "project:azure-data-platform",
    ],
)

# Create service principal from app registration
databricks_sp = azuread.ServicePrincipal(
    "databricks-platform-sp",
    client_id=databricks_app.client_id,
    description="Service principal for Azure Data Platform Databricks access",
    tags=[
        f"environment:{environment}",
        "managed-by:pulumi",
    ],
)

# =============================================================================
# Federated Credentials for OIDC (Pulumi Deployments)
# =============================================================================

# Create federated credential for Pulumi Deployments
# This enables passwordless authentication from Pulumi Cloud
pulumi_federated_credential = azuread.ApplicationFederatedIdentityCredential(
    "pulumi-deployments-credential",
    application_id=databricks_app.id,
    display_name="pulumi-deployments",
    description="Federated credential for Pulumi Deployments OIDC",
    # Pulumi Cloud OIDC issuer
    issuer="https://api.pulumi.com/oidc",
    # Subject format: pulumi:deploy:org:<org>:project:<project>:stack:<stack>
    subject=f"pulumi:deploy:org:demo:project:azure-data-team-onboarding:stack:*",
    audiences=["api://AzureADTokenExchange"],
)

# =============================================================================
# App Registration for CI/CD Pipeline
# =============================================================================

# Separate app registration for Azure DevOps pipeline
# This follows the principle of least privilege
pipeline_app = azuread.Application(
    "pipeline-app",
    display_name=f"sp-pipeline-{environment}",
    description="Service principal for Azure DevOps pipeline",
    sign_in_audience="AzureADMyOrg",
    tags=[
        f"environment:{environment}",
        "managed-by:pulumi",
        "project:azure-data-platform",
        "purpose:ci-cd",
    ],
)

pipeline_sp = azuread.ServicePrincipal(
    "pipeline-sp",
    client_id=pipeline_app.client_id,
    description="Service principal for Azure DevOps pipeline",
    tags=[
        f"environment:{environment}",
        "managed-by:pulumi",
    ],
)

# Federated credential for Azure DevOps
# This enables passwordless auth from Azure DevOps
azdo_federated_credential = azuread.ApplicationFederatedIdentityCredential(
    "azdo-credential",
    application_id=pipeline_app.id,
    display_name="azure-devops",
    description="Federated credential for Azure DevOps OIDC",
    # Azure DevOps OIDC issuer (replace with your org)
    issuer="https://vstoken.dev.azure.com/YOUR_AZDO_ORG_ID",
    # Subject format varies by Azure DevOps configuration
    subject="sc://YOUR_AZDO_ORG/YOUR_PROJECT/YOUR_SERVICE_CONNECTION",
    audiences=["api://AzureADTokenExchange"],
)

# =============================================================================
# Client Secret (Alternative to Federated Credentials)
# =============================================================================

# For scenarios where federated credentials aren't supported,
# create a client secret with rotation
# NOTE: Prefer federated credentials when possible
databricks_app_password = azuread.ApplicationPassword(
    "databricks-app-password",
    application_id=databricks_app.id,
    display_name=f"Databricks access - {environment}",
    # Rotate annually
    end_date_relative="8760h",  # 1 year
)

# =============================================================================
# Group for Databricks Admins
# =============================================================================

# Create a security group for Databricks administrators
databricks_admins_group = azuread.Group(
    "databricks-admins",
    display_name=f"grp-databricks-admins-{environment}",
    description="Administrators for Databricks workspaces",
    security_enabled=True,
    # Add the service principal as a member
    members=[databricks_sp.object_id],
)

# =============================================================================
# Outputs
# =============================================================================

# Databricks app registration
export("databricksAppId", databricks_app.id)
export("databricksAppClientId", databricks_app.client_id)
export("databricksSpId", databricks_sp.id)
export("databricksSpObjectId", databricks_sp.object_id)

# Pipeline app registration
export("pipelineAppId", pipeline_app.id)
export("pipelineAppClientId", pipeline_app.client_id)
export("pipelineSpId", pipeline_sp.id)

# Group
export("databricksAdminsGroupId", databricks_admins_group.id)

# Secret (marked as secret in Pulumi state)
export("databricksAppPassword", pulumi.Output.secret(databricks_app_password.value))

# Instructions for ESC configuration
export("escConfigInstructions", Output.concat(
    "Add to your ESC environment:\n",
    "  azure:\n",
    "    clientId: ", databricks_app.client_id, "\n",
    "    # Use federated credentials - no secret needed!\n",
))
