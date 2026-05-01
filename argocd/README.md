# ArgoCD Applications

This directory contains ArgoCD Application manifests for GitOps-based deployment to the K3s cluster.

## Architecture

```
GitHub Repository (Source of Truth)
         ↓
    ArgoCD (Watches Git)
         ↓
   K3s Cluster (Deployment Target)
```

## Directory Structure

```
argocd/
├── applications/          # Application manifests
│   ├── example-app.yml
│   ├── kubernetes-dashboard.yml
│   └── homepage.yml
└── README.md
```

## How It Works

1. **Developers push changes** to `services/k8s/` directories in Git
2. **ArgoCD detects changes** automatically (polls every 3 minutes by default)
3. **ArgoCD syncs** the changes to the K3s cluster
4. **Applications are updated** automatically with self-healing

## Deploying Applications

### Option 1: Via ArgoCD UI

1. Access ArgoCD UI: `https://<argocd-loadbalancer-ip>`
2. Login with username `admin` and the password from:
   ```bash
   kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
   ```
3. Click **+ NEW APP**
4. Fill in the details or use the YAML editor

### Option 2: Via kubectl

```bash
# Deploy a single application
kubectl apply -f argocd/applications/example-app.yml

# Deploy all applications
kubectl apply -f argocd/applications/

# Check application status
kubectl get applications -n argocd

# Get detailed status
kubectl describe application example-app -n argocd
```

### Option 3: Via ArgoCD CLI

```bash
# Install ArgoCD CLI
curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x argocd
sudo mv argocd /usr/local/bin/

# Login
argocd login <argocd-server-ip> --username admin --password <password>

# Create application
argocd app create example-app \
  --repo https://github.com/jmpa-io/homelab.git \
  --path services/k8s/argocd-example \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace default \
  --sync-policy automated \
  --auto-prune \
  --self-heal

# List applications
argocd app list

# Sync application manually
argocd app sync example-app

# Get application details
argocd app get example-app
```

## Application Configuration

### Basic Application Structure

```yaml
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
    namespace: my-namespace

  syncPolicy:
    automated:
      prune: true      # Delete resources not in Git
      selfHeal: true   # Auto-sync on drift
```

### Sync Policies

**Automated Sync** (Recommended):
```yaml
syncPolicy:
  automated:
    prune: true       # Remove resources deleted from Git
    selfHeal: true    # Revert manual changes
```

**Manual Sync**:
```yaml
syncPolicy: {}  # No automated sync, manual only
```

### Sync Options

```yaml
syncPolicy:
  syncOptions:
    - CreateNamespace=true     # Auto-create namespace
    - PruneLast=true          # Delete resources last
    - ApplyOutOfSyncOnly=true # Only sync out-of-sync resources
```

## Managing Applications

### Check Application Status

```bash
# List all applications
kubectl get applications -n argocd

# Get application details
kubectl describe application example-app -n argocd

# Watch application sync status
kubectl get application example-app -n argocd -w
```

### Manual Sync

```bash
# Sync via kubectl
kubectl patch application example-app -n argocd \
  --type merge \
  --patch '{"operation": {"initiatedBy": {"username": "admin"}, "sync": {}}}'

# Or use ArgoCD CLI
argocd app sync example-app
```

### Rollback

```bash
# View history
argocd app history example-app

# Rollback to previous version
argocd app rollback example-app <revision-number>
```

### Delete Application

```bash
# Delete application (keeps resources in cluster)
kubectl delete application example-app -n argocd

# Delete application and all resources
argocd app delete example-app --cascade
```

## Projects

ArgoCD Projects provide logical grouping and RBAC for applications.

### Create a Project

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: homelab
  namespace: argocd
spec:
  description: Homelab applications

  # Source repositories
  sourceRepos:
    - https://github.com/jmpa-io/homelab.git

  # Destination clusters and namespaces
  destinations:
    - namespace: '*'
      server: https://kubernetes.default.svc

  # Allowed resource types
  clusterResourceWhitelist:
    - group: '*'
      kind: '*'
```

## Best Practices

1. **Use Automated Sync** - Enable `automated`, `prune`, and `selfHeal` for true GitOps
2. **Namespace per Application** - Isolate applications in their own namespaces
3. **Use Projects** - Group related applications in ArgoCD Projects
4. **Health Checks** - Define custom health checks for CRDs
5. **Ignore Differences** - Ignore fields that change frequently (e.g., replicas with HPA)
6. **Resource Hooks** - Use PreSync/PostSync hooks for migrations
7. **Secrets Management** - Use Sealed Secrets or External Secrets Operator
8. **Monitoring** - Monitor ArgoCD metrics in Prometheus/Grafana

## Monitoring

### ArgoCD Metrics

ArgoCD exposes Prometheus metrics:

```yaml
# Add to Prometheus scrape config
- job_name: 'argocd-metrics'
  static_configs:
    - targets:
      - 'argocd-metrics.argocd.svc.cluster.local:8082'
```

### Grafana Dashboard

Import ArgoCD dashboard: [Dashboard ID 14584](https://grafana.com/grafana/dashboards/14584)

### Notifications

Configure notifications for sync events:

```bash
# Install ArgoCD Notifications
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj-labs/argocd-notifications/stable/manifests/install.yaml

# Configure Slack notifications (example)
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-notifications-cm
  namespace: argocd
data:
  service.slack: |
    token: $slack-token
  trigger.on-sync-succeeded: |
    - when: app.status.operationState.phase in ['Succeeded']
      send: [app-sync-succeeded]
EOF
```

## Troubleshooting

### Application Stuck in Progressing

```bash
# Check application status
kubectl describe application example-app -n argocd

# Check ArgoCD logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller

# Force refresh
argocd app get example-app --refresh
```

### Sync Fails

```bash
# View sync errors
argocd app get example-app

# Check resource events
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# Validate manifests locally
kubectl apply --dry-run=client -f services/k8s/my-app/
```

### Out of Sync

```bash
# Compare Git vs Cluster
argocd app diff example-app

# Show what will be synced
argocd app sync example-app --dry-run

# Force sync
argocd app sync example-app --force
```

## Adding New Applications

1. **Create Kubernetes manifests** in `services/k8s/<app-name>/`
2. **Create ArgoCD Application** in `argocd/applications/<app-name>.yml`
3. **Apply the Application**:
   ```bash
   kubectl apply -f argocd/applications/<app-name>.yml
   ```
4. **Verify deployment**:
   ```bash
   argocd app get <app-name>
   kubectl get all -n <namespace>
   ```

## Example: Deploying a New App

```bash
# 1. Create app manifests
mkdir -p services/k8s/my-new-app
cat > services/k8s/my-new-app/deployment.yml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-new-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-new-app
  template:
    metadata:
      labels:
        app: my-new-app
    spec:
      containers:
      - name: app
        image: nginx:latest
        ports:
        - containerPort: 80
EOF

# 2. Create ArgoCD Application
cat > argocd/applications/my-new-app.yml <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-new-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/jmpa-io/homelab.git
    targetRevision: HEAD
    path: services/k8s/my-new-app
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
EOF

# 3. Commit and push
git add services/k8s/my-new-app/ argocd/applications/my-new-app.yml
git commit -m "Add my-new-app"
git push

# 4. Deploy via ArgoCD
kubectl apply -f argocd/applications/my-new-app.yml

# 5. Watch deployment
argocd app get my-new-app --watch
```

## Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [ArgoCD Best Practices](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/)
- [GitOps Principles](https://opengitops.dev/)
- Your K3s setup: [`services/vms/k3s/`](../services/vms/k3s/)
- GitHub Actions workflows: [`.github/workflows/`](../.github/workflows/)
