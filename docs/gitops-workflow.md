# GitOps Workflow

Complete GitOps workflow for the homelab infrastructure.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub Repository                        │
│                     (Source of Truth)                           │
└────────────┬────────────────────────────────────┬───────────────┘
             │                                    │
             │ Push to main                       │ Push to main
             │ (Infrastructure)                   │ (Applications)
             ↓                                    ↓
┌────────────────────────────┐      ┌────────────────────────────┐
│  GitHub Actions Runners    │      │        ArgoCD              │
│  (Self-hosted on K3s)      │      │  (Running on K3s)          │
│                            │      │                            │
│  Workflows:                │      │  Watches:                  │
│  • deploy-proxmox-ha.yml   │      │  • services/k8s/*          │
│  • deploy-k3s-cluster.yml  │      │  • argocd/applications/*   │
│  • deploy-proxmox-services │      │                            │
└────────────┬───────────────┘      └────────────┬───────────────┘
             │                                    │
             │ Ansible Playbooks                  │ kubectl apply
             ↓                                    ↓
┌────────────────────────────┐      ┌────────────────────────────┐
│    Proxmox Cluster         │      │      K3s Cluster           │
│                            │      │                            │
│  • HA Configuration        │      │  • Applications            │
│  • LXC Containers          │      │  • Services                │
│  • VMs (including K3s)     │      │  • Ingress                 │
│  • Network Configuration   │      │  • Storage                 │
└────────────────────────────┘      └────────────────────────────┘
```

## Workflow Components

### 1. GitHub Repository (Source of Truth)

All infrastructure and application configurations are stored in Git:

```
homelab/
├── .github/workflows/          # GitHub Actions workflows
│   ├── deploy-proxmox-ha.yml
│   ├── deploy-k3s-cluster.yml
│   └── deploy-proxmox-services.yml
├── argocd/                     # ArgoCD applications
│   ├── applications/
│   └── README.md
├── services/
│   ├── k8s/                    # Kubernetes applications (ArgoCD)
│   ├── lxc/                    # LXC services (Ansible)
│   └── vms/                    # VM configurations (Ansible)
├── instances/                  # Ansible roles
└── playbooks/                  # Ansible playbooks
```

### 2. GitHub Actions (Infrastructure Deployment)

**Purpose**: Deploy infrastructure changes to Proxmox using Ansible

**Triggers**:
- Push to `main` branch
- Manual workflow dispatch
- Path-based triggers (only run when relevant files change)

**Workflows**:

#### [`deploy-proxmox-ha.yml`](.github/workflows/deploy-proxmox-ha.yml)
- Configures Proxmox HA
- Adds VMs/containers to HA groups
- Runs on self-hosted runners

#### [`deploy-k3s-cluster.yml`](.github/workflows/deploy-k3s-cluster.yml)
- Creates K3s VMs on Proxmox
- Installs K3s with HA control plane
- Deploys ArgoCD
- Configures storage classes

#### [`deploy-proxmox-services.yml`](.github/workflows/deploy-proxmox-services.yml)
- Deploys LXC containers
- Configures services (nginx, prometheus, grafana)
- Updates configurations

### 3. ArgoCD (Application Deployment)

**Purpose**: Deploy applications to K3s cluster using GitOps

**How it works**:
1. ArgoCD watches `services/k8s/` directories
2. Detects changes automatically (polls every 3 minutes)
3. Syncs changes to K3s cluster
4. Self-heals if manual changes are made

**Applications**:
- [`example-app.yml`](argocd/applications/example-app.yml)
- [`kubernetes-dashboard.yml`](argocd/applications/kubernetes-dashboard.yml)
- [`homepage.yml`](argocd/applications/homepage.yml)

## Deployment Workflows

### Deploying Infrastructure Changes

#### Scenario 1: Update Proxmox HA Configuration

```bash
# 1. Edit HA configuration
vim instances/proxmox-hosts/ha/vars/main.yml

# 2. Commit and push
git add instances/proxmox-hosts/ha/vars/main.yml
git commit -m "Update HA configuration"
git push origin main

# 3. GitHub Actions automatically:
#    - Runs deploy-proxmox-ha.yml workflow
#    - Executes Ansible playbook on self-hosted runners
#    - Updates Proxmox HA configuration
```

#### Scenario 2: Deploy K3s Cluster

```bash
# 1. Update K3s configuration (if needed)
vim services/vms/k3s/main.yml

# 2. Commit and push
git add services/vms/k3s/main.yml
git commit -m "Update K3s configuration"
git push origin main

# 3. GitHub Actions automatically:
#    - Runs deploy-k3s-cluster.yml workflow
#    - Creates VMs on Proxmox
#    - Installs K3s
#    - Deploys ArgoCD
```

#### Scenario 3: Deploy LXC Service

```bash
# 1. Update service configuration
vim services/lxc/nginx-reverse-proxy/main.yml

# 2. Commit and push
git add services/lxc/nginx-reverse-proxy/main.yml
git commit -m "Update nginx configuration"
git push origin main

# 3. GitHub Actions automatically:
#    - Runs deploy-proxmox-services.yml workflow
#    - Updates LXC container
#    - Restarts services
```

### Deploying Application Changes

#### Scenario 1: Deploy New Application

```bash
# 1. Create application manifests
mkdir -p services/k8s/my-app
cat > services/k8s/my-app/deployment.yml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: app
        image: nginx:latest
EOF

# 2. Create ArgoCD Application
cat > argocd/applications/my-app.yml <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/jmpa-io/homelab.git
    targetRevision: HEAD
    path: services/k8s/my-app
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
EOF

# 3. Commit and push
git add services/k8s/my-app/ argocd/applications/my-app.yml
git commit -m "Add my-app"
git push origin main

# 4. Deploy ArgoCD Application
kubectl apply -f argocd/applications/my-app.yml

# 5. ArgoCD automatically:
#    - Detects new application
#    - Syncs manifests to cluster
#    - Creates deployment
```

#### Scenario 2: Update Existing Application

```bash
# 1. Update application manifest
vim services/k8s/my-app/deployment.yml
# Change image version, replicas, etc.

# 2. Commit and push
git add services/k8s/my-app/deployment.yml
git commit -m "Update my-app to v2.0"
git push origin main

# 3. ArgoCD automatically:
#    - Detects changes in Git
#    - Syncs changes to cluster
#    - Performs rolling update
```

## Manual Operations

### Trigger Workflows Manually

```bash
# Via GitHub UI:
# 1. Go to Actions tab
# 2. Select workflow
# 3. Click "Run workflow"

# Via GitHub CLI:
gh workflow run deploy-k3s-cluster.yml

# With inputs:
gh workflow run deploy-k3s-cluster.yml \
  -f skip_vm_creation=true \
  -f deploy_argocd=true
```

### Manual ArgoCD Sync

```bash
# Sync via kubectl
kubectl patch application my-app -n argocd \
  --type merge \
  --patch '{"operation": {"sync": {}}}'

# Sync via ArgoCD CLI
argocd app sync my-app

# Sync all applications
argocd app sync --all
```

## Monitoring and Observability

### GitHub Actions

Monitor workflow runs:
```bash
# Via GitHub UI
# Go to Actions tab → Select workflow → View runs

# Via GitHub CLI
gh run list --workflow=deploy-k3s-cluster.yml
gh run view <run-id>
gh run watch <run-id>
```

### ArgoCD

Monitor application status:
```bash
# List applications
kubectl get applications -n argocd
argocd app list

# Get application details
kubectl describe application my-app -n argocd
argocd app get my-app

# View sync history
argocd app history my-app

# Watch application
argocd app get my-app --watch
```

### Prometheus/Grafana

Both GitHub Actions runners and ArgoCD expose Prometheus metrics:

```yaml
# Prometheus scrape configs
- job_name: 'actions-runner-controller'
  kubernetes_sd_configs:
    - role: pod
      namespaces:
        names: [actions-runner-system]

- job_name: 'argocd-metrics'
  static_configs:
    - targets: ['argocd-metrics.argocd.svc.cluster.local:8082']
```

Import Grafana dashboards:
- ArgoCD: [Dashboard 14584](https://grafana.com/grafana/dashboards/14584)
- GitHub Runners: [Dashboard 17626](https://grafana.com/grafana/dashboards/17626)

## Rollback Procedures

### Rollback Infrastructure Changes

```bash
# 1. Revert Git commit
git revert <commit-hash>
git push origin main

# 2. GitHub Actions automatically re-deploys previous state

# Or manually:
git checkout <previous-commit> -- path/to/file
git commit -m "Rollback to previous version"
git push origin main
```

### Rollback Application Changes

```bash
# Via ArgoCD CLI
argocd app history my-app
argocd app rollback my-app <revision-number>

# Via Git
git revert <commit-hash>
git push origin main
# ArgoCD automatically syncs the rollback
```

## Security Best Practices

1. **Secrets Management**
   - Store secrets in GitHub Secrets (for workflows)
   - Use Kubernetes Secrets (for applications)
   - Consider Sealed Secrets or External Secrets Operator

2. **Access Control**
   - Use GitHub branch protection rules
   - Require pull request reviews
   - Use ArgoCD RBAC for application access

3. **Audit Trail**
   - All changes tracked in Git history
   - GitHub Actions logs retained
   - ArgoCD sync history available

4. **Network Security**
   - Self-hosted runners isolated in K3s
   - ArgoCD uses TLS
   - Proxmox API over HTTPS

## Troubleshooting

### GitHub Actions Workflow Fails

```bash
# View workflow logs
gh run view <run-id> --log

# Check runner status
kubectl get pods -n actions-runner-system
kubectl logs -n actions-runner-system <runner-pod>

# Re-run workflow
gh run rerun <run-id>
```

### ArgoCD Sync Fails

```bash
# Check application status
argocd app get my-app

# View sync errors
kubectl describe application my-app -n argocd

# Check ArgoCD logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller

# Force refresh
argocd app get my-app --refresh

# Manual sync
argocd app sync my-app --force
```

### Ansible Playbook Fails

```bash
# Check connectivity
ansible proxmox_hosts -m ping

# Run playbook in check mode
ansible-playbook playbooks/setup-ha.yml --check

# Run with verbose output
ansible-playbook playbooks/setup-ha.yml -vvv

# Run specific tasks
ansible-playbook playbooks/setup-ha.yml --tags ha_groups
```

## Getting Started

### Initial Setup

1. **Deploy K3s cluster**:
   ```bash
   # Via GitHub Actions
   gh workflow run deploy-k3s-cluster.yml

   # Or manually
   ansible-playbook playbooks/deploy-k3s-gitops.yml
   ```

2. **Access ArgoCD**:
   ```bash
   # Get ArgoCD URL
   kubectl -n argocd get svc argocd-server

   # Get admin password
   kubectl -n argocd get secret argocd-initial-admin-secret \
     -o jsonpath='{.data.password}' | base64 -d
   ```

3. **Deploy applications**:
   ```bash
   # Deploy all ArgoCD applications
   kubectl apply -f argocd/applications/

   # Verify
   argocd app list
   ```

4. **Configure GitHub runners**:
   ```bash
   # Create GitHub PAT secret
   kubectl create secret generic controller-manager \
     -n actions-runner-system \
     --from-literal=github_token=<YOUR_PAT>

   # Deploy runners
   kubectl apply -f services/k8s/github-actions-runner/deployment.yml
   ```

### Daily Operations

1. **Make infrastructure changes** → Push to Git → GitHub Actions deploys
2. **Make application changes** → Push to Git → ArgoCD syncs
3. **Monitor** via Grafana dashboards
4. **Review** sync status in ArgoCD UI

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [GitOps Principles](https://opengitops.dev/)
- [Ansible Documentation](https://docs.ansible.com/)
- [K3s Documentation](https://docs.k3s.io/)
