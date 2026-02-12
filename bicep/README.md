# Bicep Templates

Pre-existing infrastructure deployed via Bicep, representing legacy resources
that can be referenced from Pulumi using the migration pattern.

All resources are free or effectively free at demo scale.

## Prerequisites

```bash
az login
az account set --subscription <subscription-id>
```

## Hub Network

Creates the central hub VNet with shared-services and gateway subnets.

```bash
az group create -n rg-hub-network-dev -l westeurope
az deployment group create \
  -g rg-hub-network-dev \
  -f bicep/hub-network.bicep \
  --parameters environment=dev
```

To reference from Pulumi (hub-network stack):

```bash
cd infrastructure/hub-network
pulumi config set useExisting true
pulumi config set existingResourceGroupName rg-hub-network-dev
pulumi config set existingVnetName vnet-hub-dev
```

## Shared Services

Creates centralized platform services: Key Vault, Log Analytics, and a
managed identity with Key Vault Secrets Reader role.

```bash
az group create -n rg-shared-services-dev -l westeurope
az deployment group create \
  -g rg-shared-services-dev \
  -f bicep/shared-services.bicep \
  --parameters environment=dev prefix=demo
```

### Outputs

After deployment, retrieve outputs for use in other stacks:

```bash
az deployment group show \
  -g rg-shared-services-dev \
  -n shared-services \
  --query properties.outputs
```

## Cleanup

```bash
az group delete -n rg-hub-network-dev --yes --no-wait
az group delete -n rg-shared-services-dev --yes --no-wait
```
