# K3s Cluster Deployment Guide

Complete guide for deploying a highly available K3s cluster across your 3 Proxmox hosts.

## Overview

Your setup will create:
- **3 K3s master nodes** (1 per Proxmox host) - HA control plane
- **6 K3s worker nodes** (2 per Proxmox host) - Workload distribution
- **Total: 9 VMs** distributed across your cluster

### Architecture

```
Proxmox Host 1 (jmpa-server-1)
├── k3s-master-1-1 (10.0.1.60)
├── k3s-node-1-1 (10.0.1.70)
└── k3s-node-1-2 (10.0.1.71)

Proxmox Host 2 (jmpa-server-2)
├── k3s-master-2-1 (10.0.2.60)
├── k3s-node-2-1 (10.0.2.70)
└── k3s-node-2-2 (10.0.2.71)

Proxmox Host 3 (jmpa-server-3)
├── k3s-master-3-1 (10.0.3.60)
├── k3s-node-3-1 (10.0.3.70)
└── k3s-node-3-2 (10.0.3.71)
```

## Prerequisites

### 1. VM Template

You need a Debian 12 cloud-init template on each Proxmox host:

```bash
# Create VM template (VMID 10001, 10002, 10003 for each host)
ansible-playbook playbooks/proxmox-templates/debian-12-nocloud-amd64/main.yml
```

This creates template VMs that K3s VMs will be cloned from.

### 2. Environment Variables

Your configuration is already set in [`inventory/main.py`](inventory/main.py:191):

```python
K3S_VERSION=v1.30.2+k3s1          # K3s version
K3S_ANSIBLE_USER=debian            # SSH user for VMs
K3S_MASTERS_PER_HOST=1             # 1 master per Proxmox host
K3S_MASTERS_START_RANGE=60         # Master IPs: 10.0.X.60
K3S_NODES_PER_HOST=2               # 2 workers per Proxmox host
K3S_NODES_START_RANGE=70           # Worker IPs: 10.0.X.70-71
```

### 3. NFS Storage on NAS

Ensure your NAS has NFS exports configured for K3s persistent storage:

```bash
# On your NAS, create the directory
mkdir -p /volume4/k3s-storage
chmod 755 /volume4/k3s-storage

# Add to /etc/exports
/volume4/k3s-storage 10.0.0.0/16(rw,sync,no_subtree_check,no_root_squash)

# Reload exports
exportfs -ra
```

## Deployment Steps

### Step 1: Deploy K3s Cluster

```bash
# Deploy the entire K3s cluster (VMs + K3s installation)
ansible-playbook services/vms/k3s/main.yml

# This will:
# 1. Create 9 VMs (3 masters + 6 workers) across your Proxmox hosts
# 2. Install K3s on all nodes
# 3. Configure HA control plane
# 4. Save kubeconfig to services/vms/k3s/kubeconfig.yaml
```

**Expected time**: 10-15 minutes

### Step 2: Configure Storage

```bash
# Deploy NFS storage class for persistent volumes
ansible-playbook services/vms/k3s/configure-storage.yml

# This configures:
# - NFS client provisioner
# - Storage class (nfs-storage) as default
# - Connects to your NAS Volume 4
```

### Step 3: Verify Cluster

```bash
# Set kubeconfig
export KUBECONFIG=services/vms/k3s/kubeconfig.yaml

# Check nodes
kubectl get nodes -o wide

# Expected output:
# NAME              STATUS   ROLES                       AGE   VERSION
# k3s-master-1-1    Ready    control-plane,etcd,master   5m    v1.30.2+k3s1
# k3s-master-2-1    Ready    control-plane,etcd,master   4m    v1.30.2+k3s1
# k3s-master-3-1    Ready    control-plane,etcd,master   3m    v1.30.2+k3s1
# k3s-node-1-1      Ready    worker                      2m    v1.30.2+k3s1
# k3s-node-1-2      Ready    worker                      2m    v1.30.2+k3s1
# k3s-node-2-1      Ready    worker                      2m    v1.30.2+k3s1
# k3s-node-2-2      Ready    worker                      2m    v1.30.2+k3s1
# k3s-node-3-1      Ready    worker                      2m    v1.30.2+k3s1
# k3s-node-3-2      Ready    worker                      2m    v1.30.2+k3s1

# Check storage class
kubectl get storageclass

# Test storage
kubectl create -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: test-pvc
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 1Gi
EOF

kubectl get pvc
kubectl delete pvc test-pvc
```

## What Gets Deployed

### K3s Configuration

The playbook configures K3s with:

✅ **HA Control Plane** - 3 masters with embedded etcd
✅ **Traefik disabled** - You'll deploy your own ingress
✅ **ServiceLB disabled** - You'll use MetalLB instead
✅ **TLS SANs** - Proper certificate configuration
✅ **Kubeconfig** - Saved locally for kubectl access

### Network Configuration

- **Pod CIDR**: 10.42.0.0/16 (K3s default)
- **Service CIDR**: 10.43.0.0/16 (K3s default)
- **Node IPs**: 10.0.X.60-79 (your bridge network)

## Post-Deployment Setup

### 1. Deploy MetalLB (LoadBalancer)

MetalLB is already configured in the playbook. Configure IP pool:

```bash
# Create MetalLB IP address pool
kubectl apply -f - <<EOF
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: default-pool
  namespace: metallb-system
spec:
  addresses:
    - 10.0.1.200-10.0.1.250  # Adjust to your network
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: default
  namespace: metallb-system
spec:
  ipAddressPools:
    - default-pool
EOF
```

### 2. Deploy Ingress Controller

Choose Traefik or nginx-ingress:

```bash
# Option A: Traefik (recommended)
helm repo add traefik https://traefik.github.io/charts
helm install traefik traefik/traefik \
  --namespace traefik \
  --create-namespace \
  --set service.type=LoadBalancer

# Option B: nginx-ingress
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer
```

### 3. Deploy Cert-Manager (SSL Certificates)

```bash
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true
```

### 4. Deploy ArgoCD (GitOps)

```bash
# Use your existing script
./bin/install-argocd.sh

# Or manually:
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

## Accessing the Cluster

### From Your Local Machine

```bash
# Copy kubeconfig
cp services/vms/k3s/kubeconfig.yaml ~/.kube/config-homelab

# Set environment variable
export KUBECONFIG=~/.kube/config-homelab

# Or merge with existing config
KUBECONFIG=~/.kube/config:services/vms/k3s/kubeconfig.yaml kubectl config view --flatten > ~/.kube/config
```

### From Proxmox Hosts

```bash
# SSH to any master node
ssh debian@10.0.1.60

# Use kubectl
sudo kubectl get nodes
```

## Scaling the Cluster

### Add More Worker Nodes

Edit [`inventory/main.py`](inventory/main.py:202):

```python
nodes_per_host=3  # Change from 2 to 3
```

Then re-run:

```bash
ansible-playbook services/vms/k3s/main.yml
```

### Add More Master Nodes

Edit [`inventory/main.py`](inventory/main.py:198):

```python
masters_per_host=2  # Change from 1 to 2 (must be odd number total)
```

## Troubleshooting

### VMs Not Starting

```bash
# Check VM status on Proxmox
ansible proxmox_hosts -m shell -a "qm list | grep k3s"

# Check VM console
# In Proxmox UI: VM > Console
```

### K3s Not Installing

```bash
# SSH to a master node
ssh debian@10.0.1.60

# Check K3s status
sudo systemctl status k3s

# Check logs
sudo journalctl -u k3s -f

# Reinstall K3s
curl -sfL https://get.k3s.io | sh -
```

### Nodes Not Joining

```bash
# On master, get token
sudo cat /var/lib/rancher/k3s/server/node-token

# On worker, check agent status
sudo systemctl status k3s-agent
sudo journalctl -u k3s-agent -f

# Verify connectivity
ping 10.0.1.60  # Master IP
curl -k https://10.0.1.60:6443  # API server
```

### Storage Issues

```bash
# Check NFS provisioner
kubectl get pods -n nfs-provisioner
kubectl logs -n nfs-provisioner -l app=nfs-client-provisioner

# Test NFS mount from a node
ssh debian@10.0.1.70
sudo mount -t nfs <NAS_IP>:/volume4/k3s-storage /mnt
ls /mnt
sudo umount /mnt
```

## Maintenance

### Update K3s Version

Edit [`inventory/main.py`](inventory/main.py:192):

```python
K3S_VERSION='v1.31.0+k3s1'  # New version
```

Then upgrade:

```bash
# Upgrade masters first (one at a time)
ansible k3s_masters -m shell -a "curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.31.0+k3s1 sh -" --serial 1

# Upgrade workers
ansible k3s_nodes -m shell -a "curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.31.0+k3s1 sh -" --serial 2
```

### Backup Cluster

```bash
# Backup etcd (on any master)
ssh debian@10.0.1.60
sudo k3s etcd-snapshot save --name backup-$(date +%Y%m%d-%H%M%S)

# Snapshots stored in: /var/lib/rancher/k3s/server/db/snapshots/
```

### Destroy Cluster

```bash
# Delete all VMs
ansible proxmox_hosts -m shell -a "for vm in \$(qm list | grep k3s | awk '{print \$1}'); do qm stop \$vm; qm destroy \$vm; done"

# Or manually in Proxmox UI
```

## Next Steps

1. ✅ Deploy K3s cluster
2. ✅ Configure storage
3. ✅ Deploy MetalLB
4. ✅ Deploy ingress controller
5. ✅ Deploy cert-manager
6. ✅ Deploy ArgoCD
7. ✅ Migrate services from LXC to K3s (see [migration guide](./MIGRATION.md))

## Resources

- [K3s Documentation](https://docs.k3s.io/)
- [MetalLB Documentation](https://metallb.universe.tf/)
- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- Your existing K3s services: [`services/k8s/`](../../services/k8s/)
