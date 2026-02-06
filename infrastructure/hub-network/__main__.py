"""
Hub Network Infrastructure Stack

This stack creates the central hub network for the Azure Data Platform.
It demonstrates:
1. Creating hub VNet infrastructure
2. Pattern for referencing existing Bicep-deployed resources
3. Exporting outputs for spoke stacks to consume via stack references

Architecture:
- Hub VNet with shared services subnet
- NSG for network security
- Outputs for spoke peering
"""

import pulumi
from pulumi import Config, export, Output
import pulumi_azure_native as azure_native
from pulumi_azure_native import resources, network

# Configuration
config = Config()
location = config.require("location")
address_space = config.require("addressSpace")
environment = config.get("environment") or "dev"

# Check if we should use existing resources (Bicep migration pattern)
use_existing = config.get_bool("useExisting") or False
existing_rg_name = config.get("existingResourceGroupName")
existing_vnet_name = config.get("existingVnetName")

# Standard tags for all resources
tags = {
    "environment": environment,
    "managed-by": "pulumi",
    "project": "azure-data-platform",
    "component": "hub-network",
}


def create_hub_network():
    """Create new hub network infrastructure."""
    
    # Resource Group
    resource_group = resources.ResourceGroup(
        "hub-rg",
        resource_group_name=f"rg-hub-network-{environment}",
        location=location,
        tags=tags,
    )

    # Network Security Group for shared services
    shared_services_nsg = network.NetworkSecurityGroup(
        "shared-services-nsg",
        network_security_group_name=f"nsg-shared-services-{environment}",
        resource_group_name=resource_group.name,
        location=location,
        security_rules=[
            # Allow inbound from spoke VNets (will be updated as spokes are added)
            network.SecurityRuleArgs(
                name="AllowSpokeInbound",
                priority=100,
                direction=network.SecurityRuleDirection.INBOUND,
                access=network.SecurityRuleAccess.ALLOW,
                protocol="*",
                source_address_prefix="10.0.0.0/8",  # All private networks
                source_port_range="*",
                destination_address_prefix="*",
                destination_port_range="*",
            ),
            # Deny all other inbound
            network.SecurityRuleArgs(
                name="DenyAllInbound",
                priority=4096,
                direction=network.SecurityRuleDirection.INBOUND,
                access=network.SecurityRuleAccess.DENY,
                protocol="*",
                source_address_prefix="*",
                source_port_range="*",
                destination_address_prefix="*",
                destination_port_range="*",
            ),
        ],
        tags=tags,
    )

    # Hub Virtual Network
    hub_vnet = network.VirtualNetwork(
        "hub-vnet",
        virtual_network_name=f"vnet-hub-{environment}",
        resource_group_name=resource_group.name,
        location=location,
        address_space=network.AddressSpaceArgs(
            address_prefixes=[address_space],
        ),
        tags=tags,
    )

    # Shared Services Subnet (for private endpoints, DNS, etc.)
    shared_services_subnet = network.Subnet(
        "shared-services-subnet",
        subnet_name="snet-shared-services",
        resource_group_name=resource_group.name,
        virtual_network_name=hub_vnet.name,
        address_prefix="10.0.1.0/24",
        network_security_group=network.SubResourceArgs(
            id=shared_services_nsg.id,
        ),
    )

    # Gateway Subnet (for VPN/ExpressRoute if needed)
    gateway_subnet = network.Subnet(
        "gateway-subnet",
        subnet_name="GatewaySubnet",  # Must be named exactly "GatewaySubnet"
        resource_group_name=resource_group.name,
        virtual_network_name=hub_vnet.name,
        address_prefix="10.0.255.0/24",
    )

    return {
        "resource_group": resource_group,
        "vnet": hub_vnet,
        "shared_services_subnet": shared_services_subnet,
        "nsg": shared_services_nsg,
    }


def reference_existing_network():
    """
    Reference existing hub network deployed via Bicep/ARM.
    
    This pattern is useful during migration:
    1. Hub network already exists (deployed via Bicep)
    2. We reference it in Pulumi without re-creating
    3. Spoke stacks can still use stack references to get hub VNet ID
    
    Note: This uses get_* functions which are read-only lookups.
    """
    
    # Look up existing resource group
    existing_rg = resources.get_resource_group(
        resource_group_name=existing_rg_name,
    )
    
    # Look up existing VNet
    existing_vnet = network.get_virtual_network(
        resource_group_name=existing_rg_name,
        virtual_network_name=existing_vnet_name,
    )
    
    # Look up existing subnet
    existing_subnet = network.get_subnet(
        resource_group_name=existing_rg_name,
        virtual_network_name=existing_vnet_name,
        subnet_name="snet-shared-services",
    )
    
    return {
        "resource_group_name": existing_rg.name,
        "resource_group_id": existing_rg.id,
        "vnet_name": existing_vnet.name,
        "vnet_id": existing_vnet.id,
        "shared_services_subnet_id": existing_subnet.id,
    }


# Main logic: create new or reference existing
if use_existing and existing_rg_name and existing_vnet_name:
    # Migration pattern: reference existing Bicep-deployed resources
    pulumi.log.info("Using existing hub network (Bicep migration pattern)")
    existing = reference_existing_network()
    
    export("resourceGroupName", existing["resource_group_name"])
    export("resourceGroupId", existing["resource_group_id"])
    export("vnetName", existing["vnet_name"])
    export("vnetId", existing["vnet_id"])
    export("sharedServicesSubnetId", existing["shared_services_subnet_id"])
    export("mode", "existing")
else:
    # Create new hub network
    pulumi.log.info("Creating new hub network infrastructure")
    hub = create_hub_network()
    
    export("resourceGroupName", hub["resource_group"].name)
    export("resourceGroupId", hub["resource_group"].id)
    export("vnetName", hub["vnet"].name)
    export("vnetId", hub["vnet"].id)
    export("sharedServicesSubnetId", hub["shared_services_subnet"].id)
    export("nsgId", hub["nsg"].id)
    export("mode", "created")

# Always export location for spoke stacks
export("location", location)
export("addressSpace", address_space)
