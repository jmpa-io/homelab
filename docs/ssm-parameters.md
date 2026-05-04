# AWS SSM Parameter Store Configuration

All secrets are stored in AWS SSM Parameter Store and retrieved by the
Python inventory script at `inventory/main.py`. Nothing sensitive is
committed to Git.

---

## Required Parameters

Run `make print-inventory` after setting these up. If any are missing,
the inventory will fail immediately with a message telling you exactly
which path to create.

### Network

```bash
/homelab/subnet                        # LAN subnet base IP (e.g. 10.0.0.0)
/homelab/internet-gateway              # Router IP (e.g. 10.0.0.1)
```

### SSH & Auth

```bash
/homelab/ssh-password                  # Password for the 'me' user (sudo)
/homelab/ssh/public-key                # SSH public key  (run: make upload-ssh-keys)
/homelab/ssh/private-key               # SSH private key (run: make upload-ssh-keys)
```

### SSL

```bash
/homelab/ssl/private-key               # Self-signed private key (run: make cert)
/homelab/ssl/cert                      # Self-signed certificate  (run: make cert)
```

### Proxmox

```bash
/homelab/proxmox/api-token             # Format: user@realm!tokenid=secret
/homelab/proxmox/password              # Proxmox root@pam password (for Homepage widget)
```

### Proxmox Hosts

```bash
/homelab/jmpa-server-1/ipv4-address    # e.g. 10.0.0.10
/homelab/jmpa-server-1/device-name     # e.g. jmpa-server-1
/homelab/jmpa-server-2/ipv4-address
/homelab/jmpa-server-2/device-name
/homelab/jmpa-server-3/ipv4-address
/homelab/jmpa-server-3/device-name
```

### NAS

```bash
/homelab/jmpa-nas-1/ipv4-address
/homelab/jmpa-nas-1/device-name
/homelab/nas/password                  # NAS admin password (for Homepage widget)
```

### DNS (Pi-hole)

```bash
/homelab/jmpa-dns-1/ipv4-address
/homelab/jmpa-dns-1/device-name
/homelab/pihole/api-key                # Settings → API in Pi-hole UI
```

### Tailscale

```bash
/homelab/tailscale/auth-key            # Tailscale auth key (reusable, ephemeral)
/homelab/tailscale/api-key             # Tailscale API key (for Homepage widget)
```

### GitHub

```bash
/homelab/github/token                  # GitHub Personal Access Token (repo scope)
```

### k3s

```bash
/homelab/k3s/token                     # Cluster join token — generate once:
                                       # openssl rand -hex 32
```

### Observability

```bash
/homelab/grafana/admin-password        # Grafana admin password
```

### Media Services (for Homepage dashboard)

```bash
/homelab/argocd/admin-password
/homelab/jellyfin/api-key              # Settings → API Keys
/homelab/jellyseerr/api-key            # Settings → General
/homelab/tautulli/api-key              # Settings → Web Interface
/homelab/prowlarr/api-key              # Settings → General
/homelab/sonarr/api-key                # Settings → General
/homelab/radarr/api-key                # Settings → General
/homelab/lidarr/api-key                # Settings → General
/homelab/readarr/api-key               # Settings → General
/homelab/bazarr/api-key                # Settings → General
/homelab/deluge/password               # Deluge web UI password
/homelab/n8n/api-key                   # n8n API key
```

### VPS (optional — only needed after `make provision-vps`)

```bash
/homelab/jmpa-vps-1/ipv4-address       # Written automatically by provision-vps.yml
/homelab/jmpa-vps-1/device-name        # Written automatically by provision-vps.yml
```

---

## Creating Parameters

```bash
# Quickest way — use the Makefile targets where available:
make upload-ssh-keys    # uploads ~/.ssh/id_ed25519 + .pub
make cert               # generates and uploads self-signed cert + key

# For everything else:
aws ssm put-parameter \
  --name "/homelab/<path>" \
  --value "<value>" \
  --type SecureString \
  --overwrite \
  --region "$AWS_REGION"
```

---

## Retrieving Parameters

```bash
# Retrieve a single value
aws ssm get-parameter \
  --name "/homelab/proxmox/api-token" \
  --with-decryption \
  --query "Parameter.Value" \
  --output text

# List all homelab parameters
aws ssm get-parameters-by-path \
  --path "/homelab" \
  --recursive \
  --with-decryption \
  --query "Parameters[*].{Name:Name,Value:Value}"

# Verify inventory generates correctly (best pre-flight check)
make print-inventory
```

---

## IAM Permissions

The AWS user or role running the inventory script needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath",
        "ssm:PutParameter"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/homelab/*"
    },
    {
      "Effect": "Allow",
      "Action": ["kms:Decrypt", "kms:GenerateDataKey"],
      "Resource": "*"
    }
  ]
}
```

---

## Environment Variables

```bash
export AWS_REGION=ap-southeast-2   # or your region
export AWS_PROFILE=homelab         # recommended — use a named profile
```

Or with explicit keys (less preferred):
```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
```

---

## Validation

```bash
# Test that all required parameters are present
make print-inventory

# If any are missing you'll see:
# ValueError: Required SSM parameter not found: /homelab/xxx
# Run: aws ssm put-parameter --name "/homelab/xxx" ...
```
