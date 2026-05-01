# GitHub Actions Self-Hosted Runners on K3s

Deploy scalable, auto-healing GitHub Actions runners on your K3s cluster using [actions-runner-controller](https://github.com/actions/actions-runner-controller).

## Why K3s over LXC?

✅ **Auto-scaling** - Automatically scale runners based on job queue
✅ **Auto-healing** - Kubernetes restarts failed runners automatically
✅ **Ephemeral runners** - Fresh, clean environment for each job
✅ **Resource management** - Better CPU/memory limits and requests
✅ **Easy deployment** - Single YAML file to deploy multiple runners
✅ **GitOps ready** - Can be managed with ArgoCD
✅ **Monitoring** - Integrates with your existing Prometheus/Grafana stack

## Prerequisites

1. **K3s cluster** - You already have this configured
2. **NFS storage** - You have this from your NAS
3. **GitHub Personal Access Token (PAT)** with appropriate permissions:
   - For **organization runners**: `admin:org` scope
   - For **repository runners**: `repo` scope
4. **Helm** installed on your local machine

## Installation

### Step 1: Install actions-runner-controller

```bash
# Add Helm repository
helm repo add actions-runner-controller https://actions-runner-controller.github.io/actions-runner-controller
helm repo update

# Create namespace
kubectl create namespace actions-runner-system

# Create GitHub PAT secret
kubectl create secret generic controller-manager \
  -n actions-runner-system \
  --from-literal=github_token=YOUR_GITHUB_PAT

# Install the controller
helm install actions-runner-controller \
  actions-runner-controller/actions-runner-controller \
  --namespace actions-runner-system \
  --set authSecret.create=false \
  --set authSecret.name=controller-manager \
  --set syncPeriod=1m
```

### Step 2: Deploy Runners

Edit [`deployment.yml`](deployment.yml) and update:

1. **Line 48**: Change `repository: jmpa-io/homelab` to your GitHub org or repo
2. **Line 32**: Add your GitHub PAT (or use the kubectl command above)

Then deploy:

```bash
# Deploy runners
kubectl apply -f services/k8s/github-actions-runner/deployment.yml

# Check runner pods
kubectl get pods -n actions-runner-system

# Check runner status
kubectl get runners -n actions-runner-system

# View logs
kubectl logs -n actions-runner-system -l app=homelab-runners -f
```

### Step 3: Verify in GitHub

1. Go to your GitHub repository/organization
2. Navigate to **Settings** → **Actions** → **Runners**
3. You should see your runners listed with labels: `self-hosted`, `k3s`, `homelab`, `linux`, `x64`

## Configuration Options

### Organization vs Repository Runners

**Organization runners** (recommended for multiple repos):
```yaml
spec:
  template:
    spec:
      organization: jmpa-io  # Your GitHub org
```

**Repository runners** (for single repo):
```yaml
spec:
  template:
    spec:
      repository: jmpa-io/homelab  # Your GitHub repo
```

### Scaling Configuration

The deployment includes auto-scaling based on job queue:

```yaml
minReplicas: 1      # Minimum runners (saves resources)
maxReplicas: 10     # Maximum runners (adjust based on needs)
scaleUpThreshold: 0.75    # Scale up when 75% busy
scaleDownThreshold: 0.25  # Scale down when 25% busy
```

### Resource Limits

Adjust based on your workload:

```yaml
resources:
  limits:
    cpu: "2"          # Maximum CPU per runner
    memory: "4Gi"     # Maximum memory per runner
  requests:
    cpu: "500m"       # Guaranteed CPU
    memory: "1Gi"     # Guaranteed memory
```

### Persistent Caching (Optional)

For faster builds, enable NFS-backed persistent caching:

1. Uncomment the PVC sections in [`deployment.yml`](deployment.yml)
2. Uncomment the volume mounts in the RunnerDeployment
3. Apply the changes

This caches:
- `_work` directory (build artifacts, dependencies)
- Docker layer cache (faster image builds)

## Using Runners in GitHub Actions

In your workflow files (`.github/workflows/*.yml`):

```yaml
name: CI

on: [push, pull_request]

jobs:
  build:
    # Use your self-hosted runners
    runs-on: [self-hosted, k3s, homelab]

    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: |
          echo "Running on self-hosted K3s runner!"
          # Your build commands here
```

### Available Labels

- `self-hosted` - All self-hosted runners
- `k3s` - Runs on K3s cluster
- `homelab` - Your homelab runners
- `linux` - Linux OS
- `x64` - x86_64 architecture

## Monitoring

### Check Runner Status

```bash
# List all runners
kubectl get runners -n actions-runner-system

# Get runner details
kubectl describe runner <runner-name> -n actions-runner-system

# View runner logs
kubectl logs -n actions-runner-system -l app=homelab-runners -f

# Check autoscaler status
kubectl get hra -n actions-runner-system
kubectl describe hra homelab-runners-autoscaler -n actions-runner-system
```

### Prometheus Metrics

The controller exposes metrics for Prometheus. Add to your Prometheus config:

```yaml
- job_name: 'actions-runner-controller'
  kubernetes_sd_configs:
    - role: pod
      namespaces:
        names:
          - actions-runner-system
  relabel_configs:
    - source_labels: [__meta_kubernetes_pod_label_app_kubernetes_io_name]
      action: keep
      regex: actions-runner-controller
```

### Grafana Dashboard

Import dashboard ID: [17626](https://grafana.com/grafana/dashboards/17626) for actions-runner-controller metrics.

## Troubleshooting

### Runners not appearing in GitHub

```bash
# Check controller logs
kubectl logs -n actions-runner-system -l app.kubernetes.io/name=actions-runner-controller

# Check runner pod logs
kubectl logs -n actions-runner-system -l app=homelab-runners

# Verify secret
kubectl get secret controller-manager -n actions-runner-system -o yaml
```

### Runners stuck in pending

```bash
# Check pod status
kubectl describe pod -n actions-runner-system <pod-name>

# Common issues:
# - Insufficient resources (check node capacity)
# - Image pull errors (check network)
# - PVC not bound (check storage class)
```

### Scaling not working

```bash
# Check HRA status
kubectl describe hra homelab-runners-autoscaler -n actions-runner-system

# Check controller logs for scaling events
kubectl logs -n actions-runner-system -l app.kubernetes.io/name=actions-runner-controller | grep -i scale
```

## Maintenance

### Update runners

```bash
# Update the deployment
kubectl apply -f services/k8s/github-actions-runner/deployment.yml

# Restart runners (they'll be recreated)
kubectl rollout restart deployment -n actions-runner-system
```

### Scale manually

```bash
# Scale to specific number
kubectl scale runnerdeployment homelab-runners -n actions-runner-system --replicas=5

# Scale to zero (maintenance mode)
kubectl scale runnerdeployment homelab-runners -n actions-runner-system --replicas=0
```

### Clean up

```bash
# Remove runners
kubectl delete -f services/k8s/github-actions-runner/deployment.yml

# Uninstall controller
helm uninstall actions-runner-controller -n actions-runner-system

# Delete namespace
kubectl delete namespace actions-runner-system
```

## Security Best Practices

1. **Use GitHub App authentication** instead of PAT (more secure, better rate limits)
2. **Enable ephemeral runners** (already configured) - fresh environment per job
3. **Use resource limits** to prevent resource exhaustion
4. **Network policies** - restrict runner network access if needed
5. **Secrets management** - use Kubernetes secrets, never commit tokens
6. **Regular updates** - keep controller and runner images updated

## Comparison: K3s vs LXC

| Feature | K3s (Recommended) | LXC |
|---------|-------------------|-----|
| Auto-scaling | ✅ Yes | ❌ Manual |
| Auto-healing | ✅ Yes | ❌ Manual |
| Ephemeral runners | ✅ Easy | ⚠️ Complex |
| Resource limits | ✅ Native | ⚠️ Manual |
| Monitoring | ✅ Prometheus | ⚠️ Custom |
| Deployment | ✅ Single YAML | ⚠️ Multiple steps |
| Maintenance | ✅ Easy updates | ⚠️ Manual updates |
| Persistent storage | ✅ NFS PVCs | ✅ Direct mount |
| Docker-in-Docker | ✅ Supported | ✅ Supported |
| Setup complexity | ⚠️ Initial setup | ✅ Simple |

## Alternative: LXC Deployment

If you still want to use LXC, you already have [`services/proxmox-community-scripts/github-runner.yml`](../../proxmox-community-scripts/github-runner.yml) configured.

Deploy with:
```bash
ansible-playbook services/proxmox-community-scripts/github-runner.yml \
  -e GITHUB_URL=https://github.com/jmpa-io \
  -e GITHUB_TOKEN=your_token_here
```

## Next Steps

1. ✅ Install actions-runner-controller
2. ✅ Deploy runners with your GitHub org/repo
3. ✅ Test with a simple workflow
4. ✅ Enable persistent caching for faster builds
5. ✅ Set up Prometheus monitoring
6. ✅ Configure auto-scaling based on your needs

## Resources

- [actions-runner-controller Documentation](https://github.com/actions/actions-runner-controller)
- [GitHub Actions Self-Hosted Runners](https://docs.github.com/en/actions/hosting-your-own-runners)
- [K3s Documentation](https://docs.k3s.io/)
- Your K3s setup: [`services/vms/k3s/`](../../vms/k3s/)
