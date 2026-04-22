# Services

Playbooks for deploying homelab services.

## Structure

- **`proxmox-community-scripts/`** - Automated LXC deployments (recommended)
- **`lxc/`** - Manual LXC container services
- **`k8s/`** - Kubernetes services
- **`vms/`** - Virtual machine services (K3s cluster)

## Quick Start

```bash
# Deploy Prometheus
ansible-playbook services/proxmox-community-scripts/prometheus.yml -i inventory/main.py

# Deploy Grafana
ansible-playbook services/proxmox-community-scripts/grafana.yml -i inventory/main.py

# Deploy Ollama
ansible-playbook services/proxmox-community-scripts/ollama.yml -i inventory/main.py
```

Services deployed via community scripts automatically get DNS records in Pi-hole.
