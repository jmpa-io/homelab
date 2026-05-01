# Kubernetes Dashboard

Web-based UI for managing your K3s cluster.

## Deployment

The Kubernetes Dashboard is automatically deployed as part of the K3s GitOps setup.

### Automated Deployment (Recommended)

```bash
# Deploy entire K3s stack including Dashboard
ansible-playbook playbooks/deploy-k3s-gitops.yml

# Or deploy just the Dashboard
ansible-playbook services/vms/k3s/deploy-dashboard.yml
```

### Manual Deployment

```bash
# Install Dashboard
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v3.0.0-alpha0/charts/kubernetes-dashboard.yaml

# Create admin user
kubectl apply -f services/k8s/kubernetes-dashboard/admin-user.yml

# Patch service for LoadBalancer
kubectl -n kubernetes-dashboard patch svc kubernetes-dashboard-web -p '{"spec":{"type":"LoadBalancer"}}'

# Get access token
kubectl -n kubernetes-dashboard create token admin-user
```

## Access

### Via LoadBalancer (Recommended)

After deployment, the Dashboard is accessible via MetalLB LoadBalancer:

```bash
# Get LoadBalancer IP
kubectl -n kubernetes-dashboard get svc kubernetes-dashboard-web

# Access at: http://<LOADBALANCER-IP>:8000
```

Credentials are saved to `services/vms/k3s/dashboard-credentials.txt` after deployment.

### Via Port Forward

```bash
# Forward port to localhost
kubectl -n kubernetes-dashboard port-forward svc/kubernetes-dashboard-web 8000:8000

# Access at: http://localhost:8000
```

### Via Ingress (Optional)

If you prefer using an Ingress (requires Traefik or another ingress controller):

```bash
kubectl apply -f services/k8s/kubernetes-dashboard/ingress.yml
```

Access at: `http://k8s-dashboard.jmpa.lab`

## Authentication

The Dashboard uses token-based authentication.

### Get Access Token

```bash
# Create a token (valid for 1 hour by default)
kubectl -n kubernetes-dashboard create token admin-user

# Create a long-lived token (10 years)
kubectl -n kubernetes-dashboard create token admin-user --duration=87600h
```

### Token is saved automatically

After running the Ansible playbook, the token is saved to:
- `services/vms/k3s/dashboard-credentials.txt`

## Features

- **Cluster Overview**: View cluster resources and health
- **Workload Management**: Deploy and manage applications
- **Service Discovery**: View services and ingresses
- **Storage Management**: Manage persistent volumes
- **Configuration**: View and edit ConfigMaps and Secrets
- **RBAC**: Manage roles and permissions
- **Logs**: View container logs
- **Shell Access**: Execute commands in containers
- **Metrics**: View resource usage (requires metrics-server)

## Configuration

Dashboard configuration is centralized in [`services/vms/k3s/vars/main.yml`](../../vms/k3s/vars/main.yml):

```yaml
kubernetes_dashboard:
  version: "v3.0.0-alpha0"
  namespace: "kubernetes-dashboard"
  service_type: "LoadBalancer"
```

## Security

### Admin User

The default deployment creates an admin user with cluster-admin privileges. For production:

1. **Create limited users** with specific permissions
2. **Use RBAC** to restrict access
3. **Enable audit logging**
4. **Use HTTPS** (configure TLS)

### Example: Read-Only User

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: readonly-user
  namespace: kubernetes-dashboard
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: readonly-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: view
subjects:
- kind: ServiceAccount
  name: readonly-user
  namespace: kubernetes-dashboard
```

Get token:
```bash
kubectl -n kubernetes-dashboard create token readonly-user
```

## Troubleshooting

### Dashboard not accessible

```bash
# Check pod status
kubectl -n kubernetes-dashboard get pods

# Check service
kubectl -n kubernetes-dashboard get svc

# Check logs
kubectl -n kubernetes-dashboard logs -l app.kubernetes.io/name=kubernetes-dashboard
```

### Token expired

```bash
# Create new token
kubectl -n kubernetes-dashboard create token admin-user
```

### LoadBalancer pending

```bash
# Check MetalLB status
kubectl -n metallb-system get pods

# Check MetalLB configuration
kubectl -n metallb-system get ipaddresspool
```

### Can't login with token

1. Ensure you're copying the entire token (no spaces)
2. Token might be expired - create a new one
3. Check browser console for errors
4. Try incognito/private browsing mode

## Monitoring

### Dashboard Metrics

The Dashboard exposes metrics for Prometheus:

```yaml
# Add to Prometheus scrape config
- job_name: 'kubernetes-dashboard'
  kubernetes_sd_configs:
    - role: pod
      namespaces:
        names:
          - kubernetes-dashboard
  relabel_configs:
    - source_labels: [__meta_kubernetes_pod_label_app_kubernetes_io_name]
      action: keep
      regex: kubernetes-dashboard
```

### Grafana Dashboard

Import Grafana dashboard for Kubernetes Dashboard metrics (if available).

## Upgrading

```bash
# Update version in vars/main.yml
vim services/vms/k3s/vars/main.yml

# Redeploy
ansible-playbook services/vms/k3s/deploy-dashboard.yml
```

## Uninstalling

```bash
# Delete Dashboard
kubectl delete namespace kubernetes-dashboard

# Or via Ansible (if you create a cleanup playbook)
ansible-playbook services/vms/k3s/cleanup-dashboard.yml
```

## Alternative: Lens Desktop

For a desktop application alternative, consider [Lens](https://k8slens.dev/):

```bash
# Install Lens
# Download from: https://k8slens.dev/

# Add your cluster
# File → Add Cluster → Paste kubeconfig from services/vms/k3s/kubeconfig.yaml
```

## Resources

- [Kubernetes Dashboard Documentation](https://kubernetes.io/docs/tasks/access-application-cluster/web-ui-dashboard/)
- [Dashboard GitHub Repository](https://github.com/kubernetes/dashboard)
- [Dashboard Releases](https://github.com/kubernetes/dashboard/releases)
- Your K3s setup: [`services/vms/k3s/`](../../vms/k3s/)
