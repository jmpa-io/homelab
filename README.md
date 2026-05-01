# Homelab Infrastructure

Complete GitOps-based homelab infrastructure running on Proxmox with K3s and ArgoCD.

![Architecture](docs/architecture.png)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Repository (Source of Truth)           │
└────────────┬────────────────────────────────────┬───────────────┘
             │                                    │
             │ Infrastructure (Ansible)           │ Applications (GitOps)
             ↓                                    ↓
┌────────────────────────────┐      ┌────────────────────────────┐
│  GitHub Actions Runners    │      │        ArgoCD              │
│  (Self-hosted on K3s)      │      │  (Running on K3s)          │
└────────────┬───────────────┘      └────────────┬───────────────┘
             │                                    │
             │ Ansible Playbooks                  │ kubectl apply
             ↓                                    ↓
┌────────────────────────────┐      ┌────────────────────────────┐
│    Proxmox Cluster         │      │      K3s Cluster           │
│  • 3 nodes (HA)            │      │  • 3 masters + 6 workers   │
│  • LXC containers          │      │  • MetalLB LoadBalancer    │
│  • VMs                     │      │  • NFS storage             │
│  • Shared storage (NFS)    │      │  • Auto-scaling runners    │
└────────────────────────────┘      └────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- 3 Proxmox VE hosts (already configured)
- NAS with NFS exports
- GitHub account with repository access
- Ansible installed locally

### 1. Deploy K3s Cluster

```bash
# Deploy K3s cluster with ArgoCD and Kubernetes Dashboard
ansible-playbook playbooks/deploy-k3s-gitops.yml

# Credentials are saved to:
# - services/vms/k3s/argocd-credentials.txt
# - services/vms/k3s/dashboard-credentials.txt
```

### 2. Setup GitHub Self-Hosted Runners

```bash
# Create GitHub PAT secret
kubectl create secret generic controller-manager \
  -n actions-runner-system \
  --from-literal=github_token=<YOUR_GITHUB_PAT>

# Deploy runners
kubectl apply -f services/k8s/github-actions-runner/deployment.yml

# Verify runners
kubectl get runners -n actions-runner-system
```

### 3. Deploy Applications via ArgoCD

```bash
# Deploy all applications
kubectl apply -f argocd/applications/

# Check status
argocd app list
```

### 4. Configure Proxmox HA

```bash
# Setup High Availability
ansible-playbook playbooks/setup-ha.yml

# Verify HA status
ansible proxmox_hosts -m shell -a "ha-manager status" --limit jmpa-server-1
```

## 📁 Repository Structure

```
homelab/
├── .github/workflows/          # GitHub Actions workflows
│   ├── deploy-proxmox-ha.yml          # Deploy Proxmox HA
│   ├── deploy-k3s-cluster.yml         # Deploy K3s cluster
│   └── deploy-proxmox-services.yml    # Deploy LXC services
│
├── argocd/                     # ArgoCD applications (GitOps)
│   ├── applications/                  # Application manifests
│   │   ├── example-app.yml
│   │   ├── kubernetes-dashboard.yml
│   │   └── homepage.yml
│   └── README.md
│
├── docs/                       # Documentation
│   ├── architecture.png
│   ├── gitops-workflow.md            # Complete GitOps guide
│   └── references.md
│
├── instances/                  # Ansible roles for instances
│   ├── proxmox-hosts/
│   │   ├── ha/                       # HA configuration role
│   │   ├── networking-and-dns/       # Network configuration
│   │   ├── opentelemetry-collector/  # Observability
│   │   ├── ha-setup.md              # HA setup guide
│   │   ├── README.md
│   │   └── setup.md
│   ├── dns/                          # Pi-hole DNS servers
│   ├── nas/                          # NAS configuration
│   └── vps/                          # VPS configuration
│
├── inventory/                  # Dynamic inventory (Python)
│   ├── main.py                       # Main inventory script
│   ├── instances/                    # Instance definitions
│   └── requirements.txt
│
├── playbooks/                  # Ansible playbooks
│   ├── deploy-k3s-gitops.yml        # Deploy K3s + ArgoCD
│   ├── setup-ha.yml                 # Setup Proxmox HA
│   ├── update-all.yml               # Update all hosts
│   └── cleanup-all.yml              # Cleanup resources
│
├── services/                   # Service configurations
│   ├── k8s/                          # Kubernetes services (ArgoCD)
│   │   ├── github-actions-runner/   # Self-hosted runners
│   │   ├── kubernetes-dashboard/    # K8s dashboard
│   │   ├── homepage/                # Homepage dashboard
│   │   └── nfs-storage-class.yaml
│   ├── lxc/                          # LXC services (Ansible)
│   │   ├── nginx-reverse-proxy/
│   │   ├── prometheus/
│   │   └── grafana/
│   └── vms/                          # VM configurations
│       └── k3s/                      # K3s cluster VMs
│
├── roles/                      # Reusable Ansible roles
│   ├── create-lxc/
│   ├── create-vm/
│   └── cleanup/
│
├── ansible.cfg                 # Ansible configuration (optimized)
├── playbook.yml               # Main playbook
├── requirements.yml           # Ansible Galaxy requirements
└── README.md                  # This file
```

## 🔄 GitOps Workflow

### Infrastructure Changes (via GitHub Actions)

```bash
# 1. Make changes to infrastructure code
vim instances/proxmox-hosts/ha/vars/main.yml

# 2. Commit and push
git add .
git commit -m "Update HA configuration"
git push origin main

# 3. GitHub Actions automatically deploys changes
# Monitor: https://github.com/jmpa-io/homelab/actions
```

### Application Changes (via ArgoCD)

```bash
# 1. Make changes to application manifests
vim services/k8s/my-app/deployment.yml

# 2. Commit and push
git add .
git commit -m "Update my-app to v2.0"
git push origin main

# 3. ArgoCD automatically syncs changes (within 3 minutes)
# Monitor: https://<argocd-ip>
```

See [`docs/gitops-workflow.md`](docs/gitops-workflow.md) for complete workflow documentation.

## 🛠️ Infrastructure Components

### Proxmox Cluster

- **3 nodes**: jmpa-server-1, jmpa-server-2, jmpa-server-3
- **High Availability**: Automatic VM/container failover
- **Shared Storage**: NFS from jmpa-nas-1
- **Networking**: Bridge networking with VLAN support

### K3s Cluster

- **Control Plane**: 3 masters (HA with embedded etcd)
- **Workers**: 6 workers (2 per Proxmox host)
- **Load Balancer**: MetalLB for LoadBalancer services
- **Storage**: NFS storage class for persistent volumes
- **Ingress**: Traefik (disabled, using MetalLB)

### LXC Services

- **nginx-reverse-proxy** (CT:5): Reverse proxy for services
- **tailscale-gateway** (CT:15): VPN gateway
- **prometheus** (CT:40): Metrics collection
- **grafana** (CT:45): Metrics visualization

### Monitoring Stack

- **Prometheus**: Metrics collection from all services
- **Grafana**: Dashboards for visualization
- **OpenTelemetry**: Distributed tracing
- **ArgoCD Metrics**: Application deployment metrics

## 📚 Documentation

### Getting Started
- [**GitOps Workflow**](docs/gitops-workflow.md) - Complete GitOps guide
- [**Proxmox Setup**](instances/proxmox-hosts/setup.md) - Initial Proxmox setup
- [**HA Setup**](instances/proxmox-hosts/ha-setup.md) - High Availability guide

### Components
- [**Proxmox HA Role**](instances/proxmox-hosts/ha/README.md) - HA Ansible role
- [**GitHub Actions Runners**](services/k8s/github-actions-runner/README.md) - Self-hosted runners
- [**ArgoCD Applications**](argocd/README.md) - Application deployment

### Operations
- [**Ansible Roles**](roles/README.md) - Reusable roles
- [**Services**](services/README.md) - Service configurations
- [**Inventory**](inventory/README.md) - Dynamic inventory

## 🔧 Common Operations

### Deploy Infrastructure

```bash
# Deploy K3s cluster
ansible-playbook playbooks/deploy-k3s-gitops.yml

# Setup Proxmox HA
ansible-playbook playbooks/setup-ha.yml

# Update all hosts
ansible-playbook playbooks/update-all.yml

# Deploy specific service
ansible-playbook services/lxc/nginx-reverse-proxy/main.yml
```

### Manage Applications

```bash
# Deploy application via ArgoCD
kubectl apply -f argocd/applications/my-app.yml

# Sync application
argocd app sync my-app

# View application status
argocd app get my-app

# Rollback application
argocd app rollback my-app <revision>
```

### Monitor Services

```bash
# Check cluster status
pvecm status

# Check HA status
ha-manager status

# Check K3s nodes
kubectl get nodes

# Check ArgoCD applications
argocd app list

# Check GitHub runners
kubectl get runners -n actions-runner-system
```

### Troubleshooting

```bash
# Check Ansible connectivity
ansible all -m ping

# Check Proxmox cluster
ansible proxmox_hosts -m shell -a "pvecm status"

# Check K3s cluster
ansible k3s_masters -m shell -a "kubectl get nodes" --limit jmpa-server-1-k3s-master-1

# View ArgoCD logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller

# View runner logs
kubectl logs -n actions-runner-system -l app=homelab-runners
```

## 🔐 Security

### Secrets Management

- **GitHub Secrets**: Store sensitive data for workflows
- **Kubernetes Secrets**: Store credentials for applications
- **Ansible Vault**: Encrypt sensitive Ansible variables (recommended)

### Access Control

- **GitHub**: Branch protection, required reviews
- **ArgoCD**: RBAC for application access
- **Proxmox**: User permissions and API tokens
- **K3s**: RBAC for service accounts

### Network Security

- **Tailscale**: Secure VPN access
- **Firewall**: UFW on all hosts
- **TLS**: HTTPS for all web services
- **Network Policies**: Kubernetes network isolation (optional)

## 🎯 Roadmap

- [x] Proxmox cluster setup
- [x] High Availability configuration
- [x] K3s cluster deployment
- [x] ArgoCD GitOps setup
- [x] GitHub Actions self-hosted runners
- [x] Monitoring stack (Prometheus/Grafana)
- [ ] Sealed Secrets for secret management
- [ ] Cert-manager for automatic TLS certificates
- [ ] Backup automation with Proxmox Backup Server
- [ ] Disaster recovery procedures
- [ ] Multi-cluster federation

## 🤝 Contributing

This is a personal homelab, but feel free to:
- Open issues for bugs or suggestions
- Submit pull requests for improvements
- Use this as inspiration for your own homelab

## 📝 License

See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Proxmox VE](https://www.proxmox.com/)
- [K3s](https://k3s.io/)
- [ArgoCD](https://argo-cd.readthedocs.io/)
- [actions-runner-controller](https://github.com/actions/actions-runner-controller)
- [Ansible](https://www.ansible.com/)

## 📞 Support

For questions or issues:
1. Check the [documentation](docs/)
2. Review [existing issues](https://github.com/jmpa-io/homelab/issues)
3. Open a new issue with details

---

**Status**: ✅ Production Ready

**Last Updated**: 2026-04-23

**Maintained By**: [@jmpa-io](https://github.com/jmpa-io)
