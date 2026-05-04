# homelab

Personal homelab infrastructure — Proxmox cluster + K3s + ArgoCD, managed via Ansible and a Python dynamic inventory backed by AWS SSM.

---

## Before you do anything — populate SSM

The dynamic inventory reads all secrets and host IPs from AWS SSM Parameter Store.
**Nothing will work until these exist.** Run `make print-inventory` to see exactly which ones are missing — each missing parameter prints the `aws ssm put-parameter` command to fix it.

See **[docs/ssm-parameters.md](docs/ssm-parameters.md)** for the complete list. The short version of what you need before `make deploy-k3s`:

```bash
# Set your region first
export AWS_REGION=ap-southeast-2
export AWS_PROFILE=your-profile   # or set AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY

# SSH keys (or run: make upload-ssh-keys)
aws ssm put-parameter --name "/homelab/ssh-password"              --value "<me user password>"  --type SecureString
aws ssm put-parameter --name "/homelab/ssh/public-key"            --value "$(cat ~/.ssh/id_ed25519.pub)" --type String
aws ssm put-parameter --name "/homelab/ssh/private-key"           --value "$(cat ~/.ssh/id_ed25519)"     --type SecureString

# SSL cert (or run: make cert)
aws ssm put-parameter --name "/homelab/ssl/private-key"           --value "$(cat ~/.ssl/private/self-signed.key)" --type SecureString
aws ssm put-parameter --name "/homelab/ssl/cert"                  --value "$(cat ~/.ssl/certs/self-signed.crt)"   --type SecureString

# Network
aws ssm put-parameter --name "/homelab/subnet"                    --value "10.0.0.0"           --type String
aws ssm put-parameter --name "/homelab/internet-gateway"          --value "<router-ip>"        --type String

# Proxmox
aws ssm put-parameter --name "/homelab/proxmox/api-token"         --value "me@pam!tokenid=secret" --type SecureString

# Hosts
aws ssm put-parameter --name "/homelab/jmpa-server-1/ipv4-address" --value "<ip>" --type String
aws ssm put-parameter --name "/homelab/jmpa-server-1/device-name"  --value "jmpa-server-1" --type String
aws ssm put-parameter --name "/homelab/jmpa-server-2/ipv4-address" --value "<ip>" --type String
aws ssm put-parameter --name "/homelab/jmpa-server-2/device-name"  --value "jmpa-server-2" --type String
aws ssm put-parameter --name "/homelab/jmpa-server-3/ipv4-address" --value "<ip>" --type String
aws ssm put-parameter --name "/homelab/jmpa-server-3/device-name"  --value "jmpa-server-3" --type String

# NAS
aws ssm put-parameter --name "/homelab/jmpa-nas-1/ipv4-address"   --value "<ip>" --type String
aws ssm put-parameter --name "/homelab/jmpa-nas-1/device-name"    --value "jmpa-nas-1" --type String

# DNS (Pi-hole)
aws ssm put-parameter --name "/homelab/jmpa-dns-1/ipv4-address"   --value "<ip>" --type String
aws ssm put-parameter --name "/homelab/jmpa-dns-1/device-name"    --value "jmpa-dns-1" --type String

# Tailscale
aws ssm put-parameter --name "/homelab/tailscale/auth-key"        --value "<tskey-auth-...>" --type SecureString

# Grafana
aws ssm put-parameter --name "/homelab/grafana/admin-password"    --value "<password>" --type SecureString

# k3s join token (generate once, never changes)
aws ssm put-parameter --name "/homelab/k3s/token"                 --value "$(openssl rand -hex 32)" --type SecureString
```

Once those are in place:
```bash
make print-inventory   # should output valid JSON — no errors
```

---

## Deploying k3s

```bash
# 1. Generate the full inventory
make create-inventory

# 2. Deploy VMs, install k3s, install MetalLB
make deploy-k3s

# 3. Configure MetalLB IP pool
ansible-playbook services/vms/k3s/deploy-metallb.yml -i dist/inventory.json --extra-vars "root_playbook_directory=$PWD"

# 4. Configure NFS storage
make configure-k3s-storage

# 5. Deploy services (in order)
ansible-playbook services/vms/k3s/deploy-gitops.yml      -i dist/inventory.json --extra-vars "root_playbook_directory=$PWD"  # ArgoCD
ansible-playbook services/vms/k3s/deploy-dashboard.yml   -i dist/inventory.json --extra-vars "root_playbook_directory=$PWD"  # K8s Dashboard
make deploy-k3s-media-volumes
ansible-playbook services/vms/k3s/deploy-media-suite.yml  -i dist/inventory.json --extra-vars "root_playbook_directory=$PWD"
ansible-playbook services/vms/k3s/deploy-homepage.yml     -i dist/inventory.json --extra-vars "root_playbook_directory=$PWD"

# Or run the whole chain in one go:
ansible-playbook playbooks/deploy-k3s-gitops.yml -i dist/inventory.json --extra-vars "root_playbook_directory=$PWD"
```

---

## Deploying the VM template (prerequisite for k3s VMs)

k3s VMs are cloned from a Debian 12 cloud-init template. Create it on each Proxmox host first:

```bash
ansible-playbook playbooks/proxmox-templates/debian-12-nocloud-amd64/main.yml \
  -i dist/inventory.json \
  --extra-vars "root_playbook_directory=$PWD"
```

This creates a template at VMID `10001` / `10002` / `10003` on each host.

---

## Deploying base host config (DNS + Proxmox nodes)

```bash
make run-playbook
```

---

## Deploying LXC observability stack

Prometheus, Grafana, Loki and Tempo run as LXC containers on Proxmox — not inside K3s.

```bash
ansible-playbook services/lxc/prometheus/main.yml           -i dist/inventory.json --extra-vars "root_playbook_directory=$PWD"
ansible-playbook services/lxc/grafana/main.yml              -i dist/inventory.json --extra-vars "root_playbook_directory=$PWD"
ansible-playbook services/lxc/loki/main.yml                 -i dist/inventory.json --extra-vars "root_playbook_directory=$PWD"
ansible-playbook services/lxc/tempo/main.yml                -i dist/inventory.json --extra-vars "root_playbook_directory=$PWD"
ansible-playbook services/lxc/nginx-reverse-proxy/main.yml  -i dist/inventory.json --extra-vars "root_playbook_directory=$PWD"
```

---

## Deploying community scripts (PBS, Ollama, etc.)

```bash
make deploy-pbs           # Proxmox Backup Server
make deploy-ollama        # Ollama (LLM runtime)
make deploy-uptime-kuma   # Uptime Kuma
make deploy-speedtest     # LibreSpeed
make deploy-n8n           # n8n workflow automation
```

---

## Provisioning a cloud VPS (optional)

A cheap KVM VPS (~€4/month on Hetzner) can join the fleet as `jmpa-vps-1` — a fourth Proxmox node connected via Tailscale with its own subnet (`10.0.4.x`).

```bash
# 1. Provision a fresh Debian 12 VPS at your cloud provider
# 2. Bootstrap Proxmox + Tailscale on it
make provision-vps VPS_IP=<your-vps-ip>

# 3. Uncomment the jmpa-vps-1 block in inventory/main.py
# 4. Verify it appears in the inventory
make print-inventory | jq '.vps_hosts'
```

---

## Rotating the Kubernetes Dashboard token

The dashboard token is short-lived (8h on first deploy). Rotate it any time:

```bash
make rotate-dashboard-token                       # default: 24h
make rotate-dashboard-token DASHBOARD_TOKEN_DURATION=8h   # shorter
```

Retrieves the new token from SSM:
```bash
aws ssm get-parameter --name /homelab/k3s/dashboard-token --with-decryption --query Parameter.Value --output text
```

---

## Common make targets

```
make print-inventory          Print the full Ansible inventory as JSON
make validate                 Run structural checks (YAML, Python, IP collisions, etc.)
make lint                     Run all linters (shellcheck, hadolint, actionlint, yamllint, ansible-lint)
make run-playbook             Run the main playbook (DNS + Proxmox base config)
make deploy-k3s               Deploy the k3s cluster
make upload-ssh-keys          Upload ~/.ssh/id_ed25519 + .pub to SSM
make cert                     Generate and upload self-signed SSL cert to SSM
make ping-inventory           Ping all hosts
make ping-hosts               Ping Proxmox hosts only
make ping-nas                 Ping NAS
make docker                   Run this project inside Docker
```

---

## Structure

```
.
├── inventory/              Python dynamic inventory — reads all config from AWS SSM
│   ├── main.py             Entry point — run directly or via make print-inventory
│   ├── instances/          Instance type definitions (ProxmoxHost, VPS, NAS, DNS, EC2)
│   ├── k8s_services.py     K8s service configuration (ArgoCD, MetalLB, media suite, etc.)
│   └── homepage_config.py  Homepage dashboard secrets
│
├── instances/              Ansible roles for base host configuration
│   ├── proxmox-hosts/      Proxmox node setup (networking, tailscale, NFS, HA, etc.)
│   └── dns/                Pi-hole DNS setup
│
├── roles/                  Reusable Ansible roles
│   ├── create-vm/          Clone a VM from template on Proxmox
│   ├── create-lxc/         Create an LXC container on Proxmox
│   ├── create-vm-template/ Build the Debian 12 cloud-init template
│   ├── copy-file-to-lxc/   Push a file into an LXC via pct push
│   └── execute-script-in-lxc/  Run a script inside an LXC via pct exec
│
├── services/
│   ├── vms/k3s/            k3s cluster playbooks (deploy, configure, service deploys)
│   ├── lxc/                LXC service playbooks (prometheus, grafana, loki, tempo, nginx)
│   ├── k8s/                Kubernetes manifests (arr-suite, homepage, dashboard, ArgoCD apps)
│   ├── ec2/                EC2 fleet member configuration
│   └── vps/                Cloud VPS provisioning (Proxmox on KVM VPS)
│
├── playbooks/              Orchestration playbooks
│   ├── deploy-k3s-gitops.yml   Full k3s + services deployment chain
│   └── setup-ha.yml            Proxmox HA configuration
│
├── argocd/applications/    ArgoCD Application manifests
├── terraform/ec2/          Terraform for optional EC2 instance
├── scripts/validate.py     Structural validation (run via make validate)
├── docs/                   Documentation
│   ├── ssm-parameters.md   Complete SSM parameter reference
│   └── ip-allocations.md   Full IP address allocation map
└── Makefile                All the things
```

---

## IP addressing

All IPs follow a consistent scheme. See **[docs/ip-allocations.md](docs/ip-allocations.md)** for the full map. Summary:

| Range | Purpose |
|---|---|
| `10.0.1.x` | jmpa-server-1 bridge subnet |
| `10.0.2.x` | jmpa-server-2 bridge subnet |
| `10.0.3.x` | jmpa-server-3 bridge subnet |
| `10.0.4.x` | jmpa-vps-1 bridge subnet |
| `10.0.{n}.5` | nginx-reverse-proxy LXC |
| `10.0.{n}.15` | tailscale-gateway LXC |
| `10.0.{n}.40–55` | observability LXC (prometheus/grafana/loki/tempo) |
| `10.0.{n}.60–69` | k3s master VMs |
| `10.0.{n}.70–79` | k3s worker VMs |
| `10.0.1.100–199` | community scripts (PBS, Ollama, n8n, etc.) |
| `<LAN>.200–250` | MetalLB LoadBalancer pool (k3s services) |
