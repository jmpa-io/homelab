# *arr Suite for K3s

Complete media automation stack (Sonarr, Radarr, Prowlarr) running on K3s with NFS storage.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         NAS (jmpa-nas-1)                     │
│  /volume1/media/movies  ←→  PV: nfs-media-movies            │
│  /volume1/media/tv      ←→  PV: nfs-media-tv                │
│  /volume1/downloads     ←→  PV: nfs-media-downloads         │
└─────────────────────────────────────────────────────────────┘
                              ↓ NFS Mount
┌─────────────────────────────────────────────────────────────┐
│                    K3s Cluster (media namespace)             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Radarr   │  │ Sonarr   │  │ Prowlarr │                  │
│  │ (Movies) │  │ (TV)     │  │ (Indexer)│                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
│       ↓              ↓              ↓                        │
│  Config: nfs-storage (dynamic PVCs)                         │
│  Media:  nfs-media-* (static PVs from NAS)                  │
└─────────────────────────────────────────────────────────────┘
```

## Storage Strategy

### Two Types of Storage

1. **Dynamic Storage** (nfs-storage class)
   - For application configs and databases
   - Automatically provisioned
   - Path: `/volume4/k3s-storage/<pvc-name>`

2. **Static Media Storage** (nfs-media class)
   - For movies, TV shows, downloads
   - Pre-created PersistentVolumes
   - Direct NAS paths: `/volume1/media/*`

## Deployment

### Automated (Recommended)

The media volumes are automatically deployed as part of the K3s setup:

```bash
# Deploy everything including media volumes
ansible-playbook playbooks/deploy-k3s-gitops.yml
```

### Manual Deployment

```bash
# 1. Deploy media volumes first
ansible-playbook services/vms/k3s/deploy-media-volumes.yml

# 2. Deploy *arr apps via ArgoCD
kubectl apply -f argocd/applications/arr-suite.yml

# Or deploy directly
kubectl apply -f services/k8s/arr-suite/
```

## Applications

### Radarr (Movies)
- **Port**: 7878
- **Volumes**:
  - Config: Dynamic PVC (1Gi)
  - Movies: `/volume1/media/movies` (5Ti)
  - Downloads: `/volume1/downloads` (2Ti)

### Sonarr (TV Shows)
- **Port**: 8989
- **Volumes**:
  - Config: Dynamic PVC (1Gi)
  - TV: `/volume1/media/tv` (5Ti)
  - Downloads: `/volume1/downloads` (2Ti)

### Prowlarr (Indexer Manager)
- **Port**: 9696
- **Volumes**:
  - Config: Dynamic PVC (500Mi)

## Access

All services are exposed via MetalLB LoadBalancer:

```bash
# Get service IPs
kubectl get svc -n media

# Access URLs
# Radarr:   http://<RADARR-IP>:7878
# Sonarr:   http://<SONARR-IP>:8989
# Prowlarr: http://<PROWLARR-IP>:9696
```

## Configuration

### Initial Setup

1. **Access each service** via LoadBalancer IP
2. **Complete setup wizard** for each app
3. **Configure Prowlarr** with your indexers
4. **Link Prowlarr to Sonarr/Radarr**:
   - Settings → Apps → Add Application
   - Use internal K8s service names:
     - Sonarr: `http://sonarr.media.svc.cluster.local:8989`
     - Radarr: `http://radarr.media.svc.cluster.local:7878`

### Download Client Setup

Add your download client (qBittorrent, Transmission, etc.):

```yaml
# Example: qBittorrent
Settings → Download Clients → Add → qBittorrent
Host: qbittorrent.media.svc.cluster.local
Port: 8080
Category: radarr (or sonarr)
```

### Path Mappings

**Important**: Use consistent paths across all apps:

```
Movies:    /movies
TV Shows:  /tv
Downloads: /downloads
```

These paths are already configured in the deployments.

## Storage Verification

### Check PersistentVolumes

```bash
# List all media PVs
kubectl get pv | grep nfs-media

# Should show:
# nfs-media-movies     5Ti   RWX   Retain   Bound
# nfs-media-tv         5Ti   RWX   Retain   Bound
# nfs-media-downloads  2Ti   RWX   Retain   Bound
# nfs-media-root       10Ti  RWX   Retain   Bound
```

### Check PersistentVolumeClaims

```bash
# List all media PVCs
kubectl get pvc -n media

# Should show all claims as Bound
```

### Test NFS Mount

```bash
# Create a test pod
kubectl run -it --rm nfs-test --image=busybox --namespace=media -- sh

# Inside the pod, mount and test
mount | grep nfs
ls -la /movies
ls -la /tv
ls -la /downloads
```

## Troubleshooting

### PVC Stuck in Pending

```bash
# Check PV status
kubectl describe pv nfs-media-movies

# Check PVC status
kubectl describe pvc media-movies -n media

# Common issues:
# 1. NFS server not accessible
# 2. NFS path doesn't exist on NAS
# 3. Permissions issue
```

### Can't Access Media Files

```bash
# Check pod logs
kubectl logs -n media deployment/radarr

# Check NFS mount inside pod
kubectl exec -it -n media deployment/radarr -- ls -la /movies

# Verify NFS server
showmount -e <NAS-IP>
```

### Permission Denied

The containers run as PUID=1000, PGID=1000. Ensure NAS directories have correct permissions:

```bash
# On Proxmox host (with NAS mounted)
sudo chown -R 1000:1000 /mnt/nfs/jmpa-nas-1/volume1/media
sudo chmod -R 755 /mnt/nfs/jmpa-nas-1/volume1/media
```

## Scaling

### Add More Storage

Edit [`services/vms/k3s/vars/main.yml`](../../vms/k3s/vars/main.yml):

```yaml
nfs_storage:
  media:
    anime:  # Add new volume
      path: "/volume1/media/anime"
      pv_name: "nfs-media-anime"
      capacity: "2Ti"
```

Then redeploy:
```bash
ansible-playbook services/vms/k3s/deploy-media-volumes.yml
```

### Add More Apps

Create new deployment files:
- `bazarr.yml` (Subtitles)
- `lidarr.yml` (Music)
- `readarr.yml` (Books)
- `qbittorrent.yml` (Download client)

## Backup

### Config Backups

Configs are stored in dynamic PVCs on `/volume4/k3s-storage`:

```bash
# Backup all configs
kubectl get pvc -n media -o json > media-pvcs-backup.json

# Or use Velero for automated backups
```

### Media Backups

Media files are on your NAS. Use your NAS backup solution (Synology Hyper Backup, etc.).

## Monitoring

### Resource Usage

```bash
# Check pod resource usage
kubectl top pods -n media

# Check PVC usage
kubectl exec -it -n media deployment/radarr -- df -h
```

### Prometheus Metrics

The *arr apps expose Prometheus metrics. Add to your Prometheus config:

```yaml
- job_name: 'arr-suite'
  kubernetes_sd_configs:
    - role: pod
      namespaces:
        names:
          - media
```

## Security

### Network Policies (Optional)

Restrict network access:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: arr-suite-policy
  namespace: media
spec:
  podSelector:
    matchLabels:
      app: radarr
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: media
  egress:
  - to:
    - namespaceSelector: {}
```

### API Keys

Store API keys in Kubernetes Secrets:

```bash
kubectl create secret generic radarr-api-key \
  -n media \
  --from-literal=api-key=<YOUR-API-KEY>
```

## Resources

- [Radarr Documentation](https://wiki.servarr.com/radarr)
- [Sonarr Documentation](https://wiki.servarr.com/sonarr)
- [Prowlarr Documentation](https://wiki.servarr.com/prowlarr)
- [LinuxServer.io Images](https://docs.linuxserver.io/)
- Your K3s setup: [`services/vms/k3s/`](../../vms/k3s/)
- Media volumes config: [`services/vms/k3s/vars/main.yml`](../../vms/k3s/vars/main.yml)
