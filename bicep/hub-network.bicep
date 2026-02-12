// Hub Network Infrastructure — Bicep
//
// This deploys the same hub network resources that the Pulumi hub-network stack
// creates, representing a "legacy" deployment that can be referenced by Pulumi
// using the useExisting migration pattern.
//
// All resources are free-tier (resource group, VNet, subnets, NSG).
//
// Deploy:
//   az group create -n rg-hub-network-dev -l westeurope
//   az deployment group create -g rg-hub-network-dev -f hub-network.bicep

@description('Azure region for all resources')
param location string = 'westeurope'

@description('Environment name for tagging')
@allowed(['dev', 'staging', 'prod', 'test'])
param environment string = 'dev'

@description('Address space for the hub VNet')
param addressSpace string = '10.0.0.0/16'

// --- Tags ---
var tags = {
  environment: environment
  'managed-by': 'bicep'
  project: 'azure-data-platform'
  component: 'hub-network'
}

// --- Network Security Group ---
resource sharedServicesNsg 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: 'nsg-shared-services-${environment}'
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'AllowSpokeInbound'
        properties: {
          priority: 100
          direction: 'Inbound'
          access: 'Allow'
          protocol: '*'
          sourceAddressPrefix: '10.0.0.0/8'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '*'
        }
      }
      {
        name: 'DenyAllInbound'
        properties: {
          priority: 4096
          direction: 'Inbound'
          access: 'Deny'
          protocol: '*'
          sourceAddressPrefix: '*'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '*'
        }
      }
    ]
  }
}

// --- Hub Virtual Network ---
resource hubVnet 'Microsoft.Network/virtualNetworks@2023-11-01' = {
  name: 'vnet-hub-${environment}'
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [addressSpace]
    }
    subnets: [
      {
        name: 'snet-shared-services'
        properties: {
          addressPrefix: '10.0.1.0/24'
          networkSecurityGroup: {
            id: sharedServicesNsg.id
          }
        }
      }
      {
        name: 'GatewaySubnet'
        properties: {
          addressPrefix: '10.0.255.0/24'
        }
      }
    ]
  }
}

// --- Outputs ---
output vnetId string = hubVnet.id
output vnetName string = hubVnet.name
output sharedServicesSubnetId string = hubVnet.properties.subnets[0].id
output gatewaySubnetId string = hubVnet.properties.subnets[1].id
output nsgId string = sharedServicesNsg.id
