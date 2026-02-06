# Azure DevOps Pipeline Configuration

This directory contains Azure DevOps pipeline configuration for the Azure Data Platform.

## Four-Eyes Principle Implementation

The pipeline implements the four-eyes principle for infrastructure changes:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Developer 1   │     │   Developer 2   │     │    Pipeline     │
│   Creates PR    │────▶│   Reviews PR    │────▶│   Deploys       │
│                 │     │   Approves      │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
   PR Created              PR Approved            Merge to main
   Preview runs            Changes verified       `pulumi up` runs
```

## Pipeline Stages

### 1. Preview Stage (PR)

- Triggered on pull request
- Runs `pulumi preview`
- Shows what changes will be made
- Generates review checklist

### 2. Policy Check Stage (All)

- Runs in parallel with preview
- Executes policy pack
- Blocks if mandatory policies fail
- Reports advisory violations

### 3. Deploy Stage (Main)

- Triggered on merge to main
- Requires environment approval
- Runs `pulumi up`
- Uses Pulumi Deployments

## Setup Instructions

### 1. Create Service Connection

In Azure DevOps:
1. Project Settings > Service connections
2. New service connection > Pulumi
3. Enter Pulumi access token

### 2. Configure Variables

In the pipeline:
```yaml
variables:
  - name: PULUMI_ORG
    value: 'your-org'
  - name: PULUMI_PROJECT
    value: 'team-onboarding'
  - name: PULUMI_STACK
    value: 'team-alpha'
```

### 3. Set Up Environment Approval

In Azure DevOps:
1. Pipelines > Environments
2. Create "production" environment
3. Add approval check
4. Require specific approvers

### 4. Configure Branch Policies

In Azure DevOps:
1. Repos > Branches > main
2. Branch policies
3. Require PR
4. Require build validation
5. Require minimum reviewers (2)

## Pulumi Deployments Integration

The pipeline uses Pulumi Deployments for:
- Centralized deployment management
- Audit trail in Pulumi Cloud
- Consistent deployment environment
- Secret management via ESC

To enable:
1. Set `useDeployments: true` in Pulumi task
2. Configure deployment settings in Pulumi Cloud
3. Link ESC environment for credentials

## Security Considerations

- **No static secrets**: Uses ESC with Azure OIDC
- **Least privilege**: Service principal has minimal permissions
- **Audit trail**: All deployments logged in Pulumi Cloud
- **Approval gates**: Environment requires manual approval
- **Policy enforcement**: Mandatory policies block non-compliant changes
