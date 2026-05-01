# Complete *arr Media Suite + Observability Stack

This directory contains the complete implementation of:
- **Media Suite**: Sonarr, Radarr, Lidarr, Readarr, Prowlarr, Bazarr, qBittorrent, Jellyseerr, Tautulli
- **Observability Stack**: Prometheus, Grafana, Loki, Tempo, OpenTelemetry Collector
- **Multi-cluster Federation**: Thanos for Prometheus federation

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         K3s Cluster                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Media Namespace                        │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  Sonarr → TV Shows                                        │  │
│  │  Radarr → Movies                                          │  │
│  │  Lidarr → Music                                           │  │
│  │  Readarr → Books                                          │  │
│  │  Prowlarr → Indexer Management                           │  │
│  │  Bazarr → Subtitles                                       │  │
│  │  qBittorrent → Download Client                           │  │
│  │  Jellyseerr → Request Management                         │  │
│  │  Tautulli → Jellyfin Statistics                          │  │
│  │  Jellyfin (External) → Media Server                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ↓                                      │
│                    ServiceMonitors                               │
│                           ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Observability Namespace                      │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  Prometheus Operator → Metrics Collection                │  │
│  │  Grafana → Visualization (Metrics + Logs + Traces)       │  │
│  │  Loki → Log Aggregation                                  │  │
│  │  Promtail → Log Collection (DaemonSet)                   │  │
│  │  Tempo → Distributed Tracing                             │  │
│  │  OpenTelemetry Collector → Trace/Metric/Log Collection   │  │
│  │  Thanos Sidecar → Multi-cluster Federation               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                           ↓
                    NFS Storage
         ┌──────────────────────────────────┐
         │  jmpa-nas-1 (192.168.1.100)      │
         ├──────────────────────────────────┤
         │  /volume1/media/movies (5Ti)     │
         │  /volume1/media/tv (3Ti)         │
         │  /volume1/media/music (2Ti)      │
         │  /volume1/media/books (500Gi)    │
         │  /volume1/media/downloads (2Ti)  │
         │  /volume2 (10Ti)                 │
         │  /volume4/k3s-storage (dynamic)  │
         └──────────────────────────────────┘
```

## Deployment

### Prerequisites

1. K3s cluster deployed (3 masters + 6 workers)
2. NFS storage configured on jmpa-nas-1
3. MetalLB installed for LoadBalancer services
4. ArgoCD installed

### Deploy Everything

```bash
# Deploy complete stack via Ansible
ansible-playbook playbooks/deploy-k3s-gitops.yml

# Or deploy components individually:

# 1. Deploy observability stack
ansible-playbook services/vms/k3s/deploy-observability.yml

# 2. Deploy media suite
ansible-playbook services/vms/k3s/deploy-media-suite.yml
```

### Deploy via ArgoCD (GitOps)

```bash
# Apply ArgoCD applications
kubectl apply -f argocd/applications/arr-suite.yml

# ArgoCD will automatically sync and deploy:
# - Complete *arr suite
# - Observability stack
# - ServiceMonitors for all applications
```

## Media Suite Services

### Sonarr (TV Shows)
- **Port**: 8989
- **URL**: `http://sonarr.media.svc.cluster.local:8989`
- **Purpose**: TV show management and automation
- **Volumes**: `/tv`, `/downloads`

### Radarr (Movies)
- **Port**: 7878
- **URL**: `http://radarr.media.svc.cluster.local:7878`
- **Purpose**: Movie management and automation
- **Volumes**: `/movies`, `/downloads`

### Lidarr (Music)
- **Port**: 8686
- **URL**: `http://lidarr.media.svc.cluster.local:8686`
- **Purpose**: Music management and automation
- **Volumes**: `/music`, `/downloads`

### Readarr (Books)
- **Port**: 8787
- **URL**: `http://readarr.media.svc.cluster.local:8787`
- **Purpose**: Book management and automation
- **Volumes**: `/books`, `/downloads`

### Prowlarr (Indexer Manager)
- **Port**: 9696
- **URL**: `http://prowlarr.media.svc.cluster.local:9696`
- **Purpose**: Centralized indexer management for all *arr apps
- **Configuration**: Add indexers here, sync to other *arr apps

### Bazarr (Subtitles)
- **Port**: 6767
- **URL**: `http://bazarr.media.svc.cluster.local:6767`
- **Purpose**: Subtitle management for movies and TV shows
- **Volumes**: `/movies`, `/tv`

### qBittorrent (Download Client)
- **Port**: 8080 (Web UI), 6881 (Torrent)
- **Type**: LoadBalancer
- **Purpose**: Torrent download client
- **Volumes**: `/downloads`
- **Default Credentials**: admin/adminadmin (CHANGE THIS!)

### Jellyseerr (Request Management)
- **Port**: 5055
- **Type**: LoadBalancer
- **Purpose**: Media request management for Jellyfin
- **Integration**: Connects to Jellyfin, Sonarr, Radarr

### Tautulli (Statistics)
- **Port**: 8181
- **URL**: `http://tautulli.media.svc.cluster.local:8181`
- **Purpose**: Jellyfin statistics and monitoring

### Jellyfin (External)
- **Type**: ExternalName Service
- **Host**: `jellyfin.jmpa.lab` (configure in [`vars/main.yml`](../vms/k3s/vars/main.yml:45))
- **Port**: 8096
- **Purpose**: Media server (running outside K3s)

## Observability Stack

### Prometheus Operator
- **Components**: Prometheus, Alertmanager, Node Exporter, Kube State Metrics
- **Retention**: 30 days
- **Storage**: 100Gi (NFS)
- **Replicas**: 2 (HA)
- **Thanos**: Enabled for multi-cluster federation

### Grafana
- **Port**: 80 (LoadBalancer)
- **Default Credentials**: admin/changeme (CHANGE THIS!)
- **Datasources**: Prometheus, Loki, Tempo
- **Dashboards**: Pre-configured for Kubernetes, Node Exporter, Loki, Prometheus

### Loki (Log Aggregation)
- **Port**: 3100
- **Retention**: 31 days (744h)
- **Storage**: 50Gi (NFS)
- **Integration**: Grafana datasource

### Promtail (Log Collection)
- **Type**: DaemonSet (runs on all nodes)
- **Purpose**: Collects logs from all pods and sends to Loki
- **Configuration**: Automatic Kubernetes pod discovery

### Tempo (Distributed Tracing)
- **Port**: 3100 (HTTP), 4317 (OTLP gRPC), 4318 (OTLP HTTP)
- **Storage**: 50Gi (NFS)
- **Protocols**: OTLP, Jaeger, Zipkin, OpenCensus
- **Integration**: Grafana datasource

### OpenTelemetry Collector
- **Replicas**: 2
- **Receivers**: OTLP, Jaeger, Zipkin, Prometheus
- **Exporters**: Tempo (traces), Prometheus (metrics), Loki (logs)
- **Purpose**: Unified telemetry collection and forwarding

## ServiceMonitors

All media applications have ServiceMonitors configured for Prometheus scraping:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: <app-name>
  namespace: media
spec:
  selector:
    matchLabels:
      app: <app-name>
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

View metrics in Grafana or Prometheus:
- Prometheus: `http://<grafana-lb-ip>/prometheus`
- Grafana: `http://<grafana-lb-ip>`

## Multi-Cluster Federation

### Thanos Architecture

Thanos is configured as a sidecar to Prometheus for multi-cluster federation:

```
┌─────────────────────────────────────────────────────────────┐
│                    On-Prem K3s Cluster                       │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Prometheus + Thanos Sidecar                       │    │
│  │  ↓                                                  │    │
│  │  S3-Compatible Object Storage (MinIO/AWS S3)       │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                           ↕
┌─────────────────────────────────────────────────────────────┐
│                    Cloud K3s Cluster                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Prometheus + Thanos Sidecar                       │    │
│  │  ↓                                                  │    │
│  │  S3-Compatible Object Storage (MinIO/AWS S3)       │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                           ↕
                  ┌─────────────────┐
                  │  Thanos Query   │
                  │  (Global View)  │
                  └─────────────────┘
```

### Setup Multi-Cluster Federation

1. **Configure Object Storage** (edit [`thanos-objstore-secret.yml`](../k8s/observability/thanos-objstore-secret.yml:1)):
   ```yaml
   type: S3
   config:
     bucket: "thanos"
     endpoint: "s3.amazonaws.com"  # Or MinIO
     access_key: "YOUR_ACCESS_KEY"
     secret_key: "YOUR_SECRET_KEY"
   ```

2. **Deploy Thanos Query** (for global view):
   ```bash
   # Deploy Thanos Query to aggregate metrics from all clusters
   helm install thanos bitnami/thanos \
     --namespace observability \
     --set query.enabled=true \
     --set query.stores={thanos-sidecar-1:10901,thanos-sidecar-2:10901}
   ```

3. **Configure Submariner** (for multi-cluster networking):
   ```bash
   # Install Submariner for secure cross-cluster communication
   subctl deploy-broker --kubeconfig ~/.kube/config
   subctl join broker-info.subm --kubeconfig ~/.kube/config-cloud
   ```

## Configuration

### Update NFS Server IP

Edit [`services/vms/k3s/vars/main.yml`](../vms/k3s/vars/main.yml:23):
```yaml
nfs_storage:
  server: "192.168.1.100"  # Change to your jmpa-nas-1 IP
```

### Update Jellyfin External Host

Edit [`services/vms/k3s/vars/main.yml`](../vms/k3s/vars/main.yml:45):
```yaml
media:
  jellyfin:
    external_host: "jellyfin.jmpa.lab"  # Change to your Jellyfin hostname/IP
```

### Update MetalLB IP Range

Edit [`services/vms/k3s/vars/main.yml`](../vms/k3s/vars/main.yml:42):
```yaml
metallb:
  ip_range: "192.168.1.200-192.168.1.250"  # Change to match your network
```

## Initial Setup

### 1. Configure Prowlarr
1. Access Prowlarr UI
2. Add indexers (Settings → Indexers)
3. Sync to Sonarr, Radarr, Lidarr, Readarr (Settings → Apps)

### 2. Configure Download Client
1. Access each *arr app
2. Add qBittorrent as download client (Settings → Download Clients)
   - Host: `qbittorrent.media.svc.cluster.local`
   - Port: `8080`

### 3. Configure Jellyseerr
1. Access Jellyseerr UI
2. Connect to Jellyfin (Settings → Jellyfin)
   - URL: `http://jellyfin.jmpa.lab:8096`
3. Connect to Sonarr and Radarr (Settings → Services)

### 4. Configure Tautulli
1. Access Tautulli UI
2. Connect to Jellyfin (Settings → Jellyfin)
   - URL: `http://jellyfin.jmpa.lab:8096`

### 5. Access Grafana
1. Get LoadBalancer IP: `kubectl get svc -n observability prometheus-operator-grafana`
2. Login with admin/changeme (CHANGE PASSWORD!)
3. Explore dashboards for metrics, logs, and traces

## Monitoring

### View Metrics in Prometheus
```bash
# Port-forward Prometheus
kubectl port-forward -n observability svc/prometheus-prometheus 9090:9090

# Access: http://localhost:9090
```

### View Logs in Loki
```bash
# Query logs via Grafana or LogCLI
logcli query '{namespace="media"}' --addr=http://loki.observability.svc.cluster.local:3100
```

### View Traces in Tempo
```bash
# Access via Grafana Explore → Tempo datasource
# Or port-forward Tempo
kubectl port-forward -n observability svc/tempo 3100:3100
```

## Troubleshooting

### Check Pod Status
```bash
# Media namespace
kubectl get pods -n media

# Observability namespace
kubectl get pods -n observability
```

### Check ServiceMonitors
```bash
kubectl get servicemonitors -n media
kubectl get servicemonitors -n observability
```

### Check PVC Status
```bash
kubectl get pvc -n media
kubectl get pvc -n observability
```

### View Logs
```bash
# Media app logs
kubectl logs -n media deployment/sonarr

# Observability logs
kubectl logs -n observability statefulset/prometheus-prometheus-operator-prometheus
```

### Check NFS Mounts
```bash
# Exec into pod and check mounts
kubectl exec -n media deployment/sonarr -- df -h
```

## Security Considerations

1. **Change Default Passwords**:
   - Grafana: admin/changeme
   - qBittorrent: admin/adminadmin
   - ArgoCD: (set in [`vars/main.yml`](../vms/k3s/vars/main.yml:10))

2. **Configure Network Policies**:
   - Restrict traffic between namespaces
   - Allow only necessary communication

3. **Enable TLS**:
   - Configure Ingress with TLS certificates
   - Use cert-manager for automatic certificate management

4. **Secure Secrets**:
   - Use Sealed Secrets or External Secrets Operator
   - Never commit secrets to Git

## Performance Tuning

### Resource Limits
All deployments have resource requests and limits configured. Adjust based on your workload:

```yaml
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 1000m
    memory: 1Gi
```

### Storage Performance
- NFS mount options optimized for performance (rsize/wsize=1048576)
- Consider using local storage for high-IOPS workloads

### Prometheus Retention
- Default: 30 days
- Adjust in [`prometheus-operator-values.yml`](../k8s/observability/prometheus-operator-values.yml:15)

## Next Steps

1. **Configure DNS**: Add LoadBalancer IPs to Pi-hole (see [`docs/dns-integration.md`](../../docs/dns-integration.md:1))
2. **Setup Ingress**: Configure Ingress resources for external access
3. **Enable Multi-Cluster**: Deploy to cloud K3s cluster and configure Thanos/Submariner
4. **Custom Dashboards**: Create Grafana dashboards for media suite metrics
5. **Alerting**: Configure Alertmanager rules for critical alerts

## Resources

- [Prometheus Operator Documentation](https://prometheus-operator.dev/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/)
- [Tempo Documentation](https://grafana.com/docs/tempo/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Thanos Documentation](https://thanos.io/tip/thanos/getting-started.md/)
- [Submariner Documentation](https://submariner.io/getting-started/)
- [Servarr Wiki](https://wiki.servarr.com/)
