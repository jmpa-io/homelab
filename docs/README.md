# Homelab Infrastructure Guide

Complete guide for the jmpa.io homelab - Proxmox VE, NAS, DNS, K3s, and automated deployments.

---

## Quick Start

```bash
# Install dependencies
pip install -r inventory/requirements.txt
ansible-galaxy install -r requirements.yml

# Deploy everything
cd inventory && python3 main.py > ../inventory.json && cd ..
ansible-playbook playbook.yml -i inventory.json
```

---

## Architecture

### Network Layout
- **10.0.1.0/24** - Proxmox Host 1 (vmbr0)
- **10.0.2.0/24** - Proxmox Host 2 (vmbr1)
- **10.0.3.0/24** - Proxmox Host 3 (vmbr2)

### VMID to IP Mapping
**Pattern:** `10.0.{bridge_num}.{last_2_digits_of_vmid}`

Examples:
- VMID 111 on vmbr0 → **10.0.1.11**
- VMID 269 on vmbr1 → **10.0.2.69**

### NAS Volumes (Auto-Discovered)
- **Volume 1:** Future use (music)
- **Volume 2:** Large storage (movies, photos)
- **Volume 3:** Backups (1TB)
- **Volume 4:** SSD high-speed operations

---

## Infrastructure Components

### 1. Proxmox VE Hosts (3x)
- Base system + networking
- NFS client (auto-discovers NAS volumes)
- OpenTelemetry collector
- Tailscale VPN

### 2. NAS (Terramaster)
- Volumes auto-discovered via `showmount -e`
- Mounted at `/mnt/nfs/<nas-name>/<volume-name>`
- Vendor-agnostic NFS implementation

### 3. DNS (Raspberry Pi 2B)
- **Pi-hole installed directly on Raspbian** (not LXC)
- DNS records auto-generated from inventory
- Raspbian optimized (GUI removed, minimal disk usage)
- OpenTelemetry collector (ARM)
- Tailscale VPN

### 4. K3s Kubernetes (Automated)
- **3 masters** (HA with embedded etcd)
- **6 workers** (2 per Proxmox host)
- NFS storage class (NAS Volume 4)

---

## Deployment

### Deploy Specific Components

```bash
# Proxmox hosts only
ansible-playbook playbook.yml -i inventory.json --tags proxmox

# NAS only
ansible-playbook playbook.yml -i inventory.json --tags nas

# DNS only (includes Pi-hole installation)
ansible-playbook playbook.yml -i inventory.json --tags dns
```

**Note:** Pi-hole is installed directly on the Raspberry Pi DNS server, not as an LXC container.

### Deploy K3s Cluster

```bash
# 1. Create VM templates (one-time)
ansible-playbook playbooks/proxmox-templates/debian-12-nocloud-amd64/main.yml -i inventory.json

# 2. Uncomment k3s in playbook.yml (line 83)
# - import_playbook: services/vms/k3s/main.yml

# 3. Deploy cluster
ansible-playbook playbook.yml -i inventory.json

# 4. Configure storage
ansible-playbook services/vms/k3s/configure-storage.yml -i inventory.json

# 5. Use cluster
export KUBECONFIG=services/vms/k3s/kubeconfig.yaml
kubectl get nodes
```

---

## Service Deployment

### Pi-hole DNS Server

Pi-hole is installed directly on the Raspberry Pi 2B DNS server (not as an LXC container).

**Installation:**
```bash
# Pi-hole is installed automatically when running the main playbook
ansible-playbook playbook.yml -i inventory.json --tags dns
```

**Access:** `http://<dns-ip>/admin`

**Features:**
- Installed directly on Raspbian (Raspberry Pi 2B)
- Automatic DNS record generation from inventory
- Service hostnames auto-configured (e.g., `prometheus.jmpa.lab`)
- Updates automatically when services are deployed
- Single source of truth: [`inventory/main.py`](../inventory/main.py)

**Add New Service to DNS:**
1. Edit [`inventory/main.py`](../inventory/main.py)
2. Add to `community_services` list
3. Re-run playbook - DNS updates automatically

**Guides:**
- [Pi-hole Installation](../instances/dns/pihole-install/README.md)
- [Pi-hole Configuration](../instances/dns/pihole-config/README.md)

### Ollama (Self-Hosted AI)

```bash
ansible-playbook services/proxmox-community-scripts/ollama.yml -i inventory.json
```

Access: `http://ollama.jmpa.lab:11434` or `http://10.0.1.50:11434` (if VMID 150)

### GitHub Actions Runners

```bash
export GITHUB_REPO="jmpa-io/homelab"
export GITHUB_TOKEN="<token>"
ansible-playbook services/proxmox-community-scripts/github-runner.yml -i inventory.json
```

### Proxmox Backup Server

```bash
ansible-playbook services/proxmox-community-scripts/proxmox-backup-server.yml \
  -i inventory.json \
  -e "pbs_password=<password>"
```

Access: `https://pbs.jmpa.lab:8007` or `https://10.0.1.00:8007` (if VMID 100)

**Post-Setup:**
1. Create datastore → NAS Volume 3
2. Configure retention (7 daily, 4 weekly, 3 monthly)

### Prometheus + Grafana Monitoring

```bash
# Deploy Prometheus
ansible-playbook services/proxmox-community-scripts/prometheus.yml -i inventory.json

# Deploy Grafana
ansible-playbook services/proxmox-community-scripts/grafana.yml -i inventory.json
```

Access:
- Prometheus: `http://prometheus.jmpa.lab:9090`
- Grafana: `http://grafana.jmpa.lab:3000`

**Auto-configured to scrape:**
- OpenTelemetry collectors (all hosts)
- Proxmox hosts
- DNS server

---

## GitHub Actions Workflows

Located in `.github/workflows/`:

- **deploy-homelab.yml** - Full infrastructure deployment
- **deploy-ollama.yml** - Deploy Ollama
- **deploy-github-runners.yml** - Deploy runners
- **validate.yml** - Lint and security scan

**Required Secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `GH_RUNNER_TOKEN`

---

## Key Features

### NAS Volume Auto-Discovery
Volumes are automatically discovered using `showmount -e` instead of hardcoding. No manual configuration needed when adding/removing volumes.

**Implementation:** [`instances/proxmox-hosts/nfs-client/tasks/main.yml`](../instances/proxmox-hosts/nfs-client/tasks/main.yml)

### Static IP Calculation
Container IPs are automatically calculated from VMID:

**Formula:** `10.0.{bridge_num + 1}.{last_2_digits_of_vmid}`

**Implementation:** [`roles/proxmox-community-script/tasks/main.yml`](../roles/proxmox-community-script/tasks/main.yml)

### K3s Fully Automated
- Creates VMs
- Installs k3s (HA with embedded etcd)
- Configures NFS storage
- Exports kubeconfig

**Implementation:** [`services/vms/k3s/main.yml`](../services/vms/k3s/main.yml)

### Pi-hole DNS Auto-Configuration
DNS records are automatically generated from the inventory:
- Services defined in [`inventory/main.py`](../inventory/main.py) are automatically added to Pi-hole
- IPs calculated from VMIDs
- No manual DNS configuration needed
- Single unified role handles installation and configuration

**Implementation:** [`instances/dns/pihole/`](../instances/dns/pihole/)

---

## Monitoring

### OpenTelemetry Collectors
Deployed on all hosts, exporting to:
- Prometheus (port 8889)
- OTLP (port 4317)

### Metrics Collected
- System metrics (CPU, memory, disk, network)
- Proxmox-specific metrics
- Pi-hole DNS metrics

---

## Troubleshooting

### NAS Volumes Not Mounting
```bash
# Check NFS exports
showmount -e <nas-ip>

# Verify mount
mount | grep nfs
```

### Static IP Not Applied
```bash
# Check container network config
pct config <vmid> | grep net0

# Manually set if needed
pct set <vmid> -net0 name=eth0,bridge=vmbr0,ip=10.0.1.X/24,gw=10.0.1.1
```

### K3s Cluster Issues
```bash
# Check node status
export KUBECONFIG=services/vms/k3s/kubeconfig.yaml
kubectl get nodes

# Check logs on master
ssh debian@10.0.1.60
sudo journalctl -u k3s -f
```

### Pi-hole DNS Not Resolving
```bash
# Check Pi-hole status
pihole status

# Check custom DNS records
cat /etc/pihole/custom.list

# Restart Pi-hole
pihole restartdns

# Test DNS resolution
nslookup prometheus.jmpa.lab
```

---

## Maintenance

**Weekly:**
- Review backup logs
- Check disk space on NAS

**Monthly:**
- Update Proxmox VE
- Update container templates
- Test backup restoration

**Update Commands:**
```bash
# Update Proxmox
ansible-playbook playbook.yml -i inventory.json --tags proxmox-update

# Update all containers
for ct in $(pct list | awk 'NR>1 {print $1}'); do
  pct exec $ct -- apt update && pct exec $ct -- apt upgrade -y
done
```

---

## High Availability

### Secondary Pi-hole DNS
For DNS redundancy, you can add a second Raspberry Pi as a secondary DNS server. Both Pi-holes will automatically receive identical configurations from the inventory.

See [`secondary-pihole-setup.md`](secondary-pihole-setup.md) for complete setup instructions.

**Benefits:**
- DNS continues if primary Pi-hole fails
- Load distribution across both servers
- Maintenance windows without DNS downtime
- Identical configuration via Ansible

---

## Additional Resources

- [Architecture Diagram](architecture.png)
- [Secondary Pi-hole Setup Guide](secondary-pihole-setup.md)
- [Proxmox Community Scripts](https://community-scripts.github.io/ProxmoxVE/)
- [References](references.md)
- [Gravity Sync](https://github.com/vmstan/gravity-sync) - Pi-hole configuration sync

---

**Maintained by:** Jordan Cleal (@jmpa-io)
