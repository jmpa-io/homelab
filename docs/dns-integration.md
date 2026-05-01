# DNS Integration with K3s

## Overview

You have Pi-hole DNS servers running externally. Here's how to integrate them with K3s:

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Pi-hole DNS (jmpa-dns-1) - External to K3s                  │
│ • Handles all homelab DNS queries                           │
│ • Custom records for services                               │
│ • Ad blocking                                               │
└────────────────┬────────────────────────────────────────────┘
                 │ DNS Queries
┌────────────────┴────────────────────────────────────────────┐
│ K3s Cluster                                                  │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ CoreDNS (K3s built-in)                               │   │
│ │ • Internal cluster DNS (*.svc.cluster.local)         │   │
│ │ • Forwards external queries to Pi-hole               │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ ExternalDNS (Optional)                               │   │
│ │ • Auto-creates DNS records in Pi-hole                │   │
│ │ • Syncs LoadBalancer IPs to DNS                      │   │
│ └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## Recommendation: Keep DNS External ✅

**YES, keep Pi-hole external to K3s!**

### Why External DNS is Better

1. **Reliability**: DNS works even if K3s is down
2. **Simplicity**: No need to manage DNS in K8s
3. **Ad Blocking**: Pi-hole features work for entire network
4. **Existing Setup**: You already have it configured
5. **Separation of Concerns**: DNS is infrastructure, not application

### K3s DNS Configuration

K3s uses CoreDNS internally for:
- **Cluster DNS**: `*.svc.cluster.local` (e.g., `radarr.media.svc.cluster.local`)
- **Pod DNS**: `<pod-ip>.default.pod.cluster.local`

For external queries, CoreDNS forwards to your Pi-hole.

## Configuration

### 1. Configure K3s to Use Pi-hole

K3s VMs should use Pi-hole as their DNS server:

```yaml
# In cloud-init or /etc/resolv.conf on K3s VMs
nameserver <PIHOLE-IP>  # Your jmpa-dns-1 IP
search jmpa.lab
```

This is likely already configured via your Proxmox network setup.

### 2. CoreDNS Configuration (Automatic)

K3s CoreDNS automatically forwards external queries to the host's DNS (Pi-hole).

**Verify**:
```bash
# On K3s master
kubectl -n kube-system get configmap coredns -o yaml
```

**Default CoreDNS config** (no changes needed):
```yaml
.:53 {
    errors
    health
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
      pods insecure
      fallthrough in-addr.arpa ip6.arpa
    }
    hosts /etc/coredns/NodeHosts {
      ttl 60
      reload 15s
      fallthrough
    }
    prometheus :9153
    forward . /etc/resolv.conf  # Forwards to Pi-hole
    cache 30
    loop
    reload
    loadbalance
}
```

### 3. Add K3s Services to Pi-hole

#### Option A: Manual (Simple)

Add custom DNS records in Pi-hole UI:
```
# /etc/pihole/custom.list
<LOADBALANCER-IP> radarr.jmpa.lab
<LOADBALANCER-IP> sonarr.jmpa.lab
<LOADBALANCER-IP> argocd.jmpa.lab
<LOADBALANCER-IP> grafana.jmpa.lab
```

#### Option B: Automated with ExternalDNS (Advanced)

Deploy ExternalDNS to automatically sync LoadBalancer IPs to Pi-hole:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: external-dns
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: external-dns
  template:
    metadata:
      labels:
        app: external-dns
    spec:
      containers:
      - name: external-dns
        image: registry.k8s.io/external-dns/external-dns:v0.14.0
        args:
        - --source=service
        - --source=ingress
        - --provider=pihole
        - --pihole-server=http://<PIHOLE-IP>
        - --pihole-password=<PIHOLE-PASSWORD>
        - --domain-filter=jmpa.lab
        - --txt-owner-id=k3s-cluster
```

**Note**: ExternalDNS Pi-hole provider is experimental. Manual is more reliable.

## DNS Resolution Flow

### Internal K8s Service

```
Pod → CoreDNS → Cluster DNS
radarr.media.svc.cluster.local → 10.43.x.x (ClusterIP)
```

### External Service (Jellyfin)

```
Pod → CoreDNS → Pi-hole → Jellyfin IP
jellyfin.jmpa.lab → <JELLYFIN-IP>
```

### LoadBalancer Service

```
External Client → Pi-hole → LoadBalancer IP → K3s Service
radarr.jmpa.lab → <METALLB-IP> → radarr pod
```

## Testing DNS

### From K3s Pod

```bash
# Test internal DNS
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup radarr.media.svc.cluster.local

# Test external DNS (via Pi-hole)
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup google.com

# Test custom domain
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup jellyfin.jmpa.lab
```

### From External Client

```bash
# Test LoadBalancer service
nslookup radarr.jmpa.lab

# Should return MetalLB IP
```

## Recommended Setup

### 1. Keep Pi-hole External ✅
- Runs on Raspberry Pi or LXC
- Handles all homelab DNS
- Provides ad blocking

### 2. Use CoreDNS in K3s ✅
- Handles cluster-internal DNS
- Forwards external queries to Pi-hole
- No configuration needed (automatic)

### 3. Manual DNS Records ✅
- Add LoadBalancer IPs to Pi-hole manually
- Simple, reliable, no dependencies
- Update when services change

### 4. Optional: ExternalDNS ⚠️
- Automates DNS record creation
- Requires Pi-hole API access
- More complex, experimental

## DNS Records to Add

After deploying services, add these to Pi-hole:

```bash
# Get LoadBalancer IPs
kubectl get svc -A | grep LoadBalancer

# Add to Pi-hole custom.list:
<IP> argocd.jmpa.lab
<IP> grafana.jmpa.lab
<IP> prometheus.jmpa.lab
<IP> dashboard.jmpa.lab
<IP> radarr.jmpa.lab
<IP> sonarr.jmpa.lab
<IP> prowlarr.jmpa.lab
<IP> lidarr.jmpa.lab
<IP> bazarr.jmpa.lab
<IP> qbittorrent.jmpa.lab
<IP> jellyseerr.jmpa.lab
```

## Multi-Cluster DNS

When you add cloud K3s cluster:

### Option 1: Separate DNS Zones
```
on-prem.jmpa.lab → Pi-hole (on-prem)
cloud.jmpa.lab → Cloud DNS
```

### Option 2: Unified DNS with Submariner
```
Submariner provides cross-cluster service discovery
Services accessible via: <service>.<namespace>.svc.clusterset.local
```

## Troubleshooting

### Pods Can't Resolve External DNS

```bash
# Check CoreDNS is running
kubectl get pods -n kube-system -l k8s-app=kube-dns

# Check CoreDNS logs
kubectl logs -n kube-system -l k8s-app=kube-dns

# Check pod's resolv.conf
kubectl exec -it <pod> -- cat /etc/resolv.conf

# Should show:
# nameserver 10.43.0.10  (CoreDNS ClusterIP)
# search <namespace>.svc.cluster.local svc.cluster.local cluster.local jmpa.lab
```

### Can't Resolve Custom Domains

```bash
# Verify Pi-hole is accessible from K3s nodes
# SSH to K3s node
nslookup jellyfin.jmpa.lab <PIHOLE-IP>

# If fails, check Pi-hole configuration
```

### LoadBalancer Services Not Resolving

```bash
# Verify MetalLB assigned IP
kubectl get svc -n media radarr

# Add IP to Pi-hole manually
# Or check ExternalDNS logs if using it
```

## Summary

**Recommended Configuration**:
1. ✅ Keep Pi-hole external (Raspberry Pi/LXC)
2. ✅ K3s VMs use Pi-hole as DNS server
3. ✅ CoreDNS handles internal cluster DNS
4. ✅ Manually add LoadBalancer IPs to Pi-hole
5. ⚠️ Optional: ExternalDNS for automation

**This gives you**:
- Reliable DNS (works even if K3s is down)
- Ad blocking for entire network
- Simple management
- No additional complexity

**You don't need**:
- DNS inside K3s cluster
- Complex DNS synchronization
- Additional DNS servers
