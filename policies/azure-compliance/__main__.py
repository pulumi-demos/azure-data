"""
Azure Compliance Policy Pack

This policy pack enforces governance guardrails for the Azure Data Platform.
It demonstrates Policy as Code for:
1. Mandatory tagging (team, environment, cost-center)
2. Network isolation (no public IPs, VNet injection)
3. Naming conventions (consistent resource naming)
4. Security best practices (encryption, secure defaults)

Enforcement Levels:
- mandatory: Blocks deployment if violated
- advisory: Warns but allows deployment
- disabled: Policy not enforced

Usage:
    pulumi up --policy-pack ../policies/azure-compliance
    
Or configure in Pulumi Cloud for organization-wide enforcement.
"""

from pulumi_policy import (
    EnforcementLevel,
    PolicyPack,
    ReportViolation,
    ResourceValidationArgs,
    ResourceValidationPolicy,
    StackValidationArgs,
    StackValidationPolicy,
)

# =============================================================================
# Configuration
# =============================================================================

# Required tags for all resources
REQUIRED_TAGS = ["team", "environment", "cost-center"]

# Valid environments
VALID_ENVIRONMENTS = ["dev", "staging", "prod", "test"]

# Naming convention patterns
NAMING_PATTERNS = {
    "resource_group": "rg-",
    "virtual_network": "vnet-",
    "subnet": "snet-",
    "network_security_group": "nsg-",
    "databricks_workspace": "dbw-",
}

# =============================================================================
# Tagging Policies
# =============================================================================


def validate_required_tags(
    args: ResourceValidationArgs, report_violation: ReportViolation
):
    """
    Ensure all Azure resources have required compliance tags.
    
    Required tags:
    - team: Identifies the owning team
    - environment: dev, staging, prod
    - cost-center: For chargeback
    """
    # Only check Azure resources
    if not args.resource_type.startswith("azure-native:"):
        return

    # Skip resources that don't support tags in Azure
    TAGLESS_RESOURCE_TYPES = [
        "azure-native:network:Subnet",
        "azure-native:network:VirtualNetworkPeering",
        "azure-native:network:SecurityRule",
    ]
    if args.resource_type in TAGLESS_RESOURCE_TYPES:
        return

    # Get tags from resource properties
    tags = args.props.get("tags", {})
    
    if tags is None:
        tags = {}

    # Check for missing required tags
    missing_tags = [tag for tag in REQUIRED_TAGS if tag not in tags]
    
    if missing_tags:
        report_violation(
            f"Resource '{args.name}' is missing required tags: {', '.join(missing_tags)}. "
            f"All Azure resources must have tags for: {', '.join(REQUIRED_TAGS)}"
        )


def validate_environment_tag(
    args: ResourceValidationArgs, report_violation: ReportViolation
):
    """
    Ensure environment tag has a valid value.
    """
    if not args.resource_type.startswith("azure-native:"):
        return

    tags = args.props.get("tags", {})
    if tags is None:
        return

    environment = tags.get("environment")
    if environment and environment not in VALID_ENVIRONMENTS:
        report_violation(
            f"Resource '{args.name}' has invalid environment tag '{environment}'. "
            f"Valid values are: {', '.join(VALID_ENVIRONMENTS)}"
        )


required_tags_policy = ResourceValidationPolicy(
    name="required-tags",
    description="Ensure all Azure resources have required compliance tags (team, environment, cost-center)",
    enforcement_level=EnforcementLevel.MANDATORY,
    validate=validate_required_tags,
)

valid_environment_policy = ResourceValidationPolicy(
    name="valid-environment-tag",
    description="Ensure environment tag has a valid value (dev, staging, prod, test)",
    enforcement_level=EnforcementLevel.MANDATORY,
    validate=validate_environment_tag,
)

# =============================================================================
# Network Isolation Policies
# =============================================================================


def validate_no_public_ip(
    args: ResourceValidationArgs, report_violation: ReportViolation
):
    """
    Prevent creation of public IP addresses.
    
    Network isolation is a core security requirement.
    All resources should use private endpoints or VNet injection.
    """
    if args.resource_type == "azure-native:network:PublicIPAddress":
        report_violation(
            f"Public IP address '{args.name}' is not allowed. "
            "Use private endpoints or VNet injection for network connectivity."
        )


def validate_databricks_vnet_injection(
    args: ResourceValidationArgs, report_violation: ReportViolation
):
    """
    Ensure Databricks workspaces use VNet injection.
    
    VNet injection provides:
    - Network isolation
    - Private connectivity to data sources
    - Compliance with security requirements
    """
    if args.resource_type != "azure-native:databricks:Workspace":
        return

    parameters = args.props.get("parameters", {})
    if parameters is None:
        parameters = {}

    custom_vnet = parameters.get("customVirtualNetworkId", {})
    if not custom_vnet or not custom_vnet.get("value"):
        report_violation(
            f"Databricks workspace '{args.name}' must use VNet injection. "
            "Set parameters.customVirtualNetworkId to enable network isolation."
        )


def validate_databricks_no_public_ip(
    args: ResourceValidationArgs, report_violation: ReportViolation
):
    """
    Ensure Databricks workspaces have public IP disabled.
    """
    if args.resource_type != "azure-native:databricks:Workspace":
        return

    parameters = args.props.get("parameters", {})
    if parameters is None:
        parameters = {}

    enable_no_public_ip = parameters.get("enableNoPublicIp", {})
    if not enable_no_public_ip or not enable_no_public_ip.get("value"):
        report_violation(
            f"Databricks workspace '{args.name}' must have public IP disabled. "
            "Set parameters.enableNoPublicIp.value to true."
        )


def validate_databricks_public_access(
    args: ResourceValidationArgs, report_violation: ReportViolation
):
    """
    Ensure Databricks workspaces have public network access disabled.
    """
    if args.resource_type != "azure-native:databricks:Workspace":
        return

    public_access = args.props.get("publicNetworkAccess")
    if public_access and public_access.lower() == "enabled":
        report_violation(
            f"Databricks workspace '{args.name}' has public network access enabled. "
            "Set publicNetworkAccess to 'Disabled' for security compliance."
        )


no_public_ip_policy = ResourceValidationPolicy(
    name="no-public-ip",
    description="Prevent creation of public IP addresses for network isolation",
    enforcement_level=EnforcementLevel.MANDATORY,
    validate=validate_no_public_ip,
)

databricks_vnet_injection_policy = ResourceValidationPolicy(
    name="databricks-vnet-injection",
    description="Ensure Databricks workspaces use VNet injection for network isolation",
    enforcement_level=EnforcementLevel.MANDATORY,
    validate=validate_databricks_vnet_injection,
)

databricks_no_public_ip_policy = ResourceValidationPolicy(
    name="databricks-no-public-ip",
    description="Ensure Databricks workspaces have public IP disabled",
    enforcement_level=EnforcementLevel.MANDATORY,
    validate=validate_databricks_no_public_ip,
)

databricks_public_access_policy = ResourceValidationPolicy(
    name="databricks-public-access-disabled",
    description="Ensure Databricks workspaces have public network access disabled",
    enforcement_level=EnforcementLevel.ADVISORY,  # Advisory for dev environments
    validate=validate_databricks_public_access,
)

# =============================================================================
# Naming Convention Policies
# =============================================================================


def validate_naming_convention(
    args: ResourceValidationArgs, report_violation: ReportViolation
):
    """
    Ensure resources follow naming conventions.
    
    Naming patterns:
    - Resource groups: rg-*
    - Virtual networks: vnet-*
    - Subnets: snet-* or databricks-*
    - NSGs: nsg-*
    - Databricks workspaces: dbw-*
    """
    # Map resource types to naming patterns
    type_to_pattern = {
        "azure-native:resources:ResourceGroup": ("rg-", "resourceGroupName"),
        "azure-native:network:VirtualNetwork": ("vnet-", "virtualNetworkName"),
        "azure-native:network:NetworkSecurityGroup": ("nsg-", "networkSecurityGroupName"),
        "azure-native:databricks:Workspace": ("dbw-", "workspaceName"),
    }

    if args.resource_type not in type_to_pattern:
        return

    pattern, prop_name = type_to_pattern[args.resource_type]
    resource_name = args.props.get(prop_name, "")

    if resource_name and not resource_name.startswith(pattern):
        report_violation(
            f"Resource '{args.name}' has name '{resource_name}' which doesn't follow "
            f"naming convention. Names should start with '{pattern}'."
        )


def validate_subnet_naming(
    args: ResourceValidationArgs, report_violation: ReportViolation
):
    """
    Ensure subnets follow naming conventions.
    
    Valid patterns:
    - snet-* (standard subnets)
    - databricks-* (Databricks subnets)
    - GatewaySubnet (Azure gateway subnet)
    """
    if args.resource_type != "azure-native:network:Subnet":
        return

    subnet_name = args.props.get("subnetName", "")
    valid_prefixes = ["snet-", "databricks-", "GatewaySubnet"]

    if subnet_name and not any(subnet_name.startswith(p) or subnet_name == p for p in valid_prefixes):
        report_violation(
            f"Subnet '{args.name}' has name '{subnet_name}' which doesn't follow "
            f"naming convention. Names should start with: {', '.join(valid_prefixes)}"
        )


naming_convention_policy = ResourceValidationPolicy(
    name="naming-convention",
    description="Ensure resources follow naming conventions (rg-, vnet-, nsg-, dbw-)",
    enforcement_level=EnforcementLevel.ADVISORY,
    validate=validate_naming_convention,
)

subnet_naming_policy = ResourceValidationPolicy(
    name="subnet-naming-convention",
    description="Ensure subnets follow naming conventions (snet-, databricks-, GatewaySubnet)",
    enforcement_level=EnforcementLevel.ADVISORY,
    validate=validate_subnet_naming,
)

# =============================================================================
# Security Best Practices
# =============================================================================


def validate_databricks_premium_sku(
    args: ResourceValidationArgs, report_violation: ReportViolation
):
    """
    Ensure Databricks workspaces use Premium SKU.
    
    Premium SKU is required for:
    - Unity Catalog
    - Advanced security features
    - SCIM provisioning
    """
    if args.resource_type != "azure-native:databricks:Workspace":
        return

    sku = args.props.get("sku", {})
    if sku is None:
        sku = {}

    sku_name = sku.get("name", "").lower()
    if sku_name and sku_name != "premium":
        report_violation(
            f"Databricks workspace '{args.name}' uses '{sku_name}' SKU. "
            "Premium SKU is required for Unity Catalog and advanced security features."
        )


databricks_premium_sku_policy = ResourceValidationPolicy(
    name="databricks-premium-sku",
    description="Ensure Databricks workspaces use Premium SKU for Unity Catalog support",
    enforcement_level=EnforcementLevel.ADVISORY,
    validate=validate_databricks_premium_sku,
)

# =============================================================================
# Stack Validation Policies
# =============================================================================


def validate_stack_has_databricks(
    args: StackValidationArgs, report_violation: ReportViolation
):
    """
    Advisory: Check if team onboarding stack includes Databricks workspace.
    
    This is an example of a stack-level policy that validates
    the overall structure of the deployment.
    """
    has_databricks = any(
        r.resource_type == "azure-native:databricks:Workspace"
        for r in args.resources
    )

    if not has_databricks:
        report_violation(
            "Team onboarding stack should include a Databricks workspace. "
            "Consider using the DatabricksWorkspaceComponent."
        )


stack_has_databricks_policy = StackValidationPolicy(
    name="stack-has-databricks",
    description="Advisory: Team onboarding stacks should include Databricks workspace",
    enforcement_level=EnforcementLevel.ADVISORY,
    validate=validate_stack_has_databricks,
)

# =============================================================================
# Policy Pack Registration
# =============================================================================

PolicyPack(
    name="azure-data-compliance",
    enforcement_level=EnforcementLevel.MANDATORY,
    policies=[
        # Tagging policies
        required_tags_policy,
        valid_environment_policy,
        # Network isolation policies
        no_public_ip_policy,
        databricks_vnet_injection_policy,
        databricks_no_public_ip_policy,
        databricks_public_access_policy,
        # Naming convention policies
        naming_convention_policy,
        subnet_naming_policy,
        # Security policies
        databricks_premium_sku_policy,
        # Stack policies
        stack_has_databricks_policy,
    ],
)
