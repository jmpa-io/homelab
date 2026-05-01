# AWS SSM Parameter Store Configuration

This document lists all required AWS SSM Parameter Store parameters for the homelab infrastructure.

## Overview

All secrets are stored in AWS SSM Parameter Store and retrieved by the Python inventory script. This provides:
- Centralized secret management
- Encryption at rest
- Access control via IAM
- Audit logging
- No secrets in Git

## Required Parameters

### Infrastructure

```bash
# Proxmox
/homelab/proxmox/password              # Proxmox root@pam password
/homelab/proxmox/api-token             # Proxmox API token (format: user@realm!tokenid=secret)

# Pi-hole
/homelab/pihole/api-key                # Pi-hole API key (from Settings > API)

# NAS (Terramaster)
/homelab/nas/password                  # NAS admin password

# Tailscale
/homelab/tailscale/auth-key            # Tailscale auth key

# SSH
/homelab/ssh-password                  # User 'me' password for sudo
/homelab/ssh/public-key                # SSH public key for key-based auth

# SSL
/homelab/ssl/private-key               # SSL private key
/homelab/ssl/cert                      # SSL certificate

# Network
/homelab/subnet                        # Common subnet (e.g., 10.0.0.0)
/homelab/internet-gateway              # Internet gateway IP
```

### Proxmox Hosts

```bash
# Server 1
/homelab/jmpa-server-1/ipv4-address    # e.g., 10.0.0.10
/homelab/jmpa-server-1/device-name     # e.g., jmpa-server-1

# Server 2
/homelab/jmpa-server-2/ipv4-address    # e.g., 10.0.0.11
/homelab/jmpa-server-2/device-name     # e.g., jmpa-server-2

# Server 3
/homelab/jmpa-server-3/ipv4-address    # e.g., 10.0.0.12
/homelab/jmpa-server-3/device-name     # e.g., jmpa-server-3
```

### NAS & DNS

```bash
# NAS
/homelab/jmpa-nas-1/ipv4-address       # NAS IP address
/homelab/jmpa-nas-1/device-name        # e.g., jmpa-nas-1

# DNS (Pi-hole)
/homelab/jmpa-dns-1/ipv4-address       # Pi-hole IP address
/homelab/jmpa-dns-1/device-name        # e.g., jmpa-dns-1
```

### Kubernetes Services

```bash
# ArgoCD
/homelab/argocd/admin-password         # ArgoCD admin password

# Grafana
/homelab/grafana/admin-password        # Grafana admin password

# Jellyfin
/homelab/jellyfin/api-key              # Jellyfin API key (Settings > API Keys)

# Jellyseerr
/homelab/jellyseerr/api-key            # Jellyseerr API key (Settings > General)

# Tautulli
/homelab/tautulli/api-key              # Tautulli API key (Settings > Web Interface)

# Prowlarr
/homelab/prowlarr/api-key              # Prowlarr API key (Settings > General)

# Sonarr
/homelab/sonarr/api-key                # Sonarr API key (Settings > General)

# Radarr
/homelab/radarr/api-key                # Radarr API key (Settings > General)

# Lidarr
/homelab/lidarr/api-key                # Lidarr API key (Settings > General)

# Readarr
/homelab/readarr/api-key               # Readarr API key (Settings > General)

# Bazarr
/homelab/bazarr/api-key                # Bazarr API key (Settings > General)

# Deluge
/homelab/deluge/password               # Deluge web UI password

# n8n
/homelab/n8n/api-key                   # n8n API key
```

## Creating Parameters

### Using AWS CLI

```bash
# Example: Create Proxmox password
aws ssm put-parameter \
  --name "/homelab/proxmox/password" \
  --value "your-secure-password" \
  --type "SecureString" \
  --description "Proxmox root@pam password" \
  --region us-east-1

# Example: Create API key
aws ssm put-parameter \
  --name "/homelab/sonarr/api-key" \
  --value "abc123def456..." \
  --type "SecureString" \
  --description "Sonarr API key" \
  --region us-east-1
```

### Using AWS Console

1. Go to AWS Systems Manager > Parameter Store
2. Click "Create parameter"
3. Name: `/homelab/service/key`
4. Type: `SecureString`
5. KMS key: Use default or custom
6. Value: Your secret
7. Click "Create parameter"

### Bulk Creation Script

```bash
#!/bin/bash
# create-ssm-parameters.sh

REGION="us-east-1"

# Function to create parameter
create_param() {
  local name=$1
  local value=$2
  local desc=$3

  aws ssm put-parameter \
    --name "$name" \
    --value "$value" \
    --type "SecureString" \
    --description "$desc" \
    --region "$REGION" \
    --overwrite
}

# Infrastructure
create_param "/homelab/proxmox/password" "changeme" "Proxmox password"
create_param "/homelab/pihole/api-key" "changeme" "Pi-hole API key"
create_param "/homelab/nas/password" "changeme" "NAS password"

# K8s Services
create_param "/homelab/argocd/admin-password" "changeme" "ArgoCD admin password"
create_param "/homelab/grafana/admin-password" "changeme" "Grafana admin password"
create_param "/homelab/sonarr/api-key" "changeme" "Sonarr API key"
create_param "/homelab/radarr/api-key" "changeme" "Radarr API key"
# ... add all others

echo "Parameters created. Update values in AWS Console."
```

## Retrieving Parameters

### In Python (Inventory Script)

```python
from ssm import SSMClient

ssm_client = SSMClient('us-east-1')
password = ssm_client.get_parameter('/homelab/proxmox/password')
```

### Using AWS CLI

```bash
# Get parameter value
aws ssm get-parameter \
  --name "/homelab/proxmox/password" \
  --with-decryption \
  --region us-east-1 \
  --query "Parameter.Value" \
  --output text

# List all homelab parameters
aws ssm get-parameters-by-path \
  --path "/homelab" \
  --recursive \
  --region us-east-1
```

## IAM Permissions

The user/role running the inventory script needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "arn:aws:ssm:us-east-1:*:parameter/homelab/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt"
      ],
      "Resource": "arn:aws:kms:us-east-1:*:key/*"
    }
  ]
}
```

## Environment Variables

Set these before running the inventory:

```bash
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key

# Or use AWS profiles
export AWS_PROFILE=homelab
```

## Security Best Practices

1. **Use SecureString**: Always use `SecureString` type for sensitive data
2. **KMS Encryption**: Use a custom KMS key for additional control
3. **IAM Policies**: Grant least-privilege access
4. **Rotation**: Rotate secrets regularly
5. **Audit**: Enable CloudTrail for parameter access logging
6. **Backup**: Export parameters for disaster recovery (encrypted)

## Validation

Test parameter retrieval:

```bash
# Test inventory script
cd inventory
python3 main.py | jq '.all.vars.k8s_services.homepage.secrets'

# Should show all Homepage secrets populated from SSM
```

## Troubleshooting

### Parameter Not Found

```bash
# Check if parameter exists
aws ssm describe-parameters \
  --parameter-filters "Key=Name,Values=/homelab/proxmox/password" \
  --region us-east-1
```

### Access Denied

```bash
# Check IAM permissions
aws sts get-caller-identity
aws iam get-user
```

### Wrong Region

```bash
# Ensure AWS_REGION is set
echo $AWS_REGION

# Or specify in command
aws ssm get-parameter --name "/homelab/proxmox/password" --region us-east-1
```

## Migration from Other Secret Stores

### From Ansible Vault

```bash
# Decrypt vault
ansible-vault decrypt secrets.yml

# Extract and create SSM parameters
# (manual or scripted)
```

### From Environment Variables

```bash
# Convert .env to SSM
while IFS='=' read -r key value; do
  aws ssm put-parameter \
    --name "/homelab/${key,,}" \
    --value "$value" \
    --type "SecureString"
done < .env
```

## Next Steps

1. Create all required parameters in SSM
2. Set AWS credentials/profile
3. Run inventory script: `cd inventory && python3 main.py`
4. Deploy Homepage: `ansible-playbook services/vms/k3s/deploy-homepage.yml`
5. Verify secrets in K8s: `kubectl get secret homepage -n homepage -o yaml`
