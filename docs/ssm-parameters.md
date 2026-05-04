# AWS SSM Parameter Store Configuration

All secrets are stored in AWS SSM Parameter Store and retrieved by the
Python inventory script at `inventory/main.py`. Nothing sensitive is
committed to Git.

---

## Required Parameters

These must exist before `make print-inventory` will succeed. Everything else is optional — add as you bring each service online.

### Network

```bash
/homelab/subnet                        # LAN subnet base IP (e.g. 10.0.0.0)
/homelab/internet-gateway              # Router IP (e.g. 10.0.0.1)
```

### SSH & Auth

```bash
/homelab/ssh-password                  # Password for the 'me' user (sudo password on all hosts)
/homelab/ssh/public-key                # SSH public key  (run: make upload-ssh-keys)
/homelab/ssh/private-key               # SSH private key (run: make upload-ssh-keys)
```

### Proxmox

```bash
/homelab/proxmox/api-token             # Format: user@realm!tokenid=secret
```

### Proxmox Hosts

```bash
/homelab/jmpa-server-1/ipv4-address
/homelab/jmpa-server-1/device-name
/homelab/jmpa-server-2/ipv4-address
/homelab/jmpa-server-2/device-name
/homelab/jmpa-server-3/ipv4-address
/homelab/jmpa-server-3/device-name
```

### NAS

```bash
/homelab/jmpa-nas-1/ipv4-address
/homelab/jmpa-nas-1/device-name
```

### DNS (Pi-hole)

```bash
/homelab/jmpa-dns-1/ipv4-address
/homelab/jmpa-dns-1/device-name
```

---

## Optional Parameters

These are only read when deploying specific services. Missing values are handled gracefully — the relevant service will fail or degrade, nothing else breaks.

### k3s (add before running `make deploy-k3s`)

```bash
/homelab/k3s/token                     # Cluster join token — generate once:
                                       # openssl rand -hex 32
```

### Tailscale (add before deploying tailscale-gateway LXC)

```bash
/homelab/tailscale/auth-key            # Tailscale auth key (reusable, ephemeral)
```

### SSL (add before deploying nginx with SSL, or run: make cert)

```bash
/homelab/ssl/private-key
/homelab/ssl/cert
```

### Grafana (add before deploying Grafana LXC)

```bash
/homelab/grafana/admin-password
```

### GitHub (add before deploying GitHub Actions runners)

```bash
/tokens/github                         # GitHub Personal Access Token (repo scope)
```

### Homepage dashboard widgets (add as you bring each service online)

Missing values show a widget error on the dashboard — nothing else breaks.

```bash
/homelab/proxmox/password
/homelab/pihole/api-key                # Settings → API in Pi-hole UI
/homelab/nas/password
/homelab/argocd/admin-password         # Populated automatically by deploy-gitops.yml
/homelab/jellyfin/api-key
/homelab/jellyseerr/api-key
/homelab/tautulli/api-key
/homelab/prowlarr/api-key
/homelab/sonarr/api-key
/homelab/radarr/api-key
/homelab/lidarr/api-key
/homelab/readarr/api-key
/homelab/bazarr/api-key
/homelab/deluge/password
/homelab/n8n/api-key
/homelab/tailscale/api-key             # Tailscale API key (for Homepage widget only)
```

### VPS (written automatically by `make provision-vps`)

```bash
/homelab/jmpa-vps-1/ipv4-address
/homelab/jmpa-vps-1/device-name
```

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
/tokens/github                         # GitHub Personal Access Token (repo scope)
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

### Media Services (optional — only needed for Homepage dashboard widgets)

These are only read when deploying `deploy-homepage.yml`. Missing values
cause that widget to show an error on the dashboard — nothing else breaks.
Add them as you bring each service online.

```bash
/homelab/argocd/admin-password         # populated automatically by deploy-gitops.yml
/homelab/proxmox/password
/homelab/pihole/api-key                # Settings → API in Pi-hole UI
/homelab/nas/password
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
/homelab/tailscale/api-key             # Tailscale API key (for Homepage widget)
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
