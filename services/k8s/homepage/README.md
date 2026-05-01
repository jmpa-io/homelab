# Homepage Dashboard

Homepage is a modern, fully static, fast, secure, and customizable application dashboard with integrations for over 100 services.

## Features

- **Service Integration**: Widgets for all your services (*arr suite, Jellyfin, Kubernetes, etc.)
- **Kubernetes Native**: Runs in K3s with cluster resource monitoring
- **API Integration**: Real-time stats from services
- **Customizable**: Easy YAML configuration
- **Dark Mode**: Beautiful dark theme
- **Fast**: Static site, loads instantly

## Deployment

### Via Ansible

```bash
# Deploy Homepage
ansible-playbook services/vms/k3s/deploy-homepage.yml

# Or as part of complete stack
ansible-playbook playbooks/deploy-k3s-gitops.yml
```

### Via ArgoCD

```bash
# Apply ArgoCD application
kubectl apply -f argocd/applications/homepage.yml
```

## Configuration

### Services

All services are pre-configured in [`services.yaml`](services.yaml:1):

**Infrastructure**:
- Proxmox Cluster
- Pi-hole (DNS/Ad-blocking)
- Synology NAS

**Kubernetes**:
- Kubernetes Dashboard
- ArgoCD
- Grafana
- Prometheus

**Media Management**:
- Jellyfin
- Jellyseerr
- Tautulli

**Media Automation** (*arr Suite):
- Prowlarr (Indexer manager)
- Sonarr (TV shows)
- Radarr (Movies)
- Lidarr (Music)
- Readarr (Books)
- Bazarr (Subtitles)

**Download Clients**:
- Deluge

**Monitoring**:
- Uptime Kuma
- Loki
- Tempo
- OpenTelemetry Collector

**Automation**:
- GitHub Actions
- n8n

### Widgets

Configured in [`widgets.yaml`](widgets.yaml:1):
- Search (Google)
- Kubernetes cluster stats
- System resources
- Weather (Melbourne)
- Date/time

### Settings

Configured in [`settings.yaml`](settings.yaml:1):
- Dark theme (slate color)
- Custom layout per section
- Quick launch shortcuts
- Header links to GitHub/Docs

## API Keys

Homepage needs API keys to display service widgets. Update the secret:

```bash
# Edit secret
kubectl edit secret homepage -n homepage

# Or create from file
kubectl create secret generic homepage \
  --from-literal=HOMEPAGE_VAR_SONARR_API_KEY="your-key" \
  --from-literal=HOMEPAGE_VAR_RADARR_API_KEY="your-key" \
  --from-literal=HOMEPAGE_VAR_PROWLARR_API_KEY="your-key" \
  --from-literal=HOMEPAGE_VAR_LIDARR_API_KEY="your-key" \
  --from-literal=HOMEPAGE_VAR_READARR_API_KEY="your-key" \
  --from-literal=HOMEPAGE_VAR_BAZARR_API_KEY="your-key" \
  --from-literal=HOMEPAGE_VAR_JELLYFIN_API_KEY="your-key" \
  --from-literal=HOMEPAGE_VAR_JELLYSEERR_API_KEY="your-key" \
  --from-literal=HOMEPAGE_VAR_TAUTULLI_API_KEY="your-key" \
  --from-literal=HOMEPAGE_VAR_GRAFANA_PASS="your-password" \
  --from-literal=HOMEPAGE_VAR_ARGOCD_PASS="your-password" \
  --from-literal=HOMEPAGE_VAR_PIHOLE_API_KEY="your-key" \
  --from-literal=HOMEPAGE_VAR_PROXMOX_PASS="your-password" \
  --from-literal=HOMEPAGE_VAR_SYNOLOGY_PASS="your-password" \
  --from-literal=HOMEPAGE_VAR_DELUGE_PASS="deluge" \
  --from-literal=HOMEPAGE_VAR_N8N_API_KEY="your-key" \
  -n homepage \
  --dry-run=client -o yaml | kubectl apply -f -
```

### Getting API Keys

**Sonarr/Radarr/Lidarr/Readarr/Prowlarr/Bazarr**:
1. Go to Settings → General
2. Copy API Key

**Jellyfin**:
1. Dashboard → API Keys
2. Create new key

**Jellyseerr**:
1. Settings → General
2. Copy API Key

**Tautulli**:
1. Settings → Web Interface
2. Copy API Key

**Pi-hole**:
1. Settings → API
2. Show API token

**Grafana**:
1. Configuration → API Keys
2. Create new key with Viewer role

## Access

Get the LoadBalancer IP:

```bash
kubectl get svc -n homepage homepage
```

Access Homepage at: `http://<LOADBALANCER_IP>`

## Customization

### Add New Service

Edit [`services.yaml`](services.yaml:1):

```yaml
- My Services:
    - New Service:
        icon: service-icon.png
        href: http://service.example.com
        description: My new service
        widget:
          type: service-type
          url: http://service.example.com
          key: {{HOMEPAGE_VAR_SERVICE_API_KEY}}
```

### Change Layout

Edit [`settings.yaml`](settings.yaml:1):

```yaml
layout:
  My Services:
    style: row  # or column
    columns: 3  # number of columns
```

### Add Bookmarks

Edit [`deployment.yml`](deployment.yml:1) ConfigMap:

```yaml
bookmarks.yaml: |
  - My Links:
      - GitHub:
          - icon: github
            href: https://github.com
```

## Kubernetes Integration

Homepage has full Kubernetes integration:

- **Cluster Stats**: CPU, memory, node count
- **Pod Stats**: Per-namespace resource usage
- **Service Discovery**: Automatic service detection
- **Ingress**: Shows ingress routes

Configured via ServiceAccount with ClusterRole for read access.

## Monitoring

Homepage is monitored by Prometheus via ServiceMonitor:

```bash
# Check metrics
kubectl port-forward -n homepage svc/homepage 3000:80
curl http://localhost:3000/metrics
```

View in Grafana:
- Dashboard → Explore → Prometheus
- Query: `up{job="homepage"}`

## Troubleshooting

### Service Widget Not Working

1. **Check API key**:
```bash
kubectl get secret homepage -n homepage -o yaml
```

2. **Check service connectivity**:
```bash
kubectl run -it --rm debug --image=nicolaka/netshoot --restart=Never -- \
  curl http://sonarr.media.svc.cluster.local:8989/api/v3/system/status
```

3. **Check Homepage logs**:
```bash
kubectl logs -n homepage deployment/homepage
```

### Kubernetes Widget Not Working

1. **Check ServiceAccount**:
```bash
kubectl get sa homepage -n homepage
kubectl get clusterrolebinding homepage
```

2. **Check permissions**:
```bash
kubectl auth can-i get pods --as=system:serviceaccount:homepage:homepage
```

### LoadBalancer Pending

```bash
# Check MetalLB
kubectl get pods -n metallb-system

# Check IP pool
kubectl get ipaddresspool -n metallb-system
```

## Resources

- [Homepage Documentation](https://gethomepage.dev/)
- [Service Widgets](https://gethomepage.dev/en/widgets/)
- [Kubernetes Integration](https://gethomepage.dev/en/configs/kubernetes/)
- [Configuration Examples](https://github.com/gethomepage/homepage/tree/main/docs)

## Next Steps

1. **Get LoadBalancer IP**: `kubectl get svc -n homepage homepage`
2. **Access Homepage**: `http://<IP>`
3. **Update API keys**: `kubectl edit secret homepage -n homepage`
4. **Customize**: Edit [`services.yaml`](services.yaml:1), [`widgets.yaml`](widgets.yaml:1), [`settings.yaml`](settings.yaml:1)
5. **Add to DNS**: Add LoadBalancer IP to Pi-hole as `homepage.jmpa.lab`
