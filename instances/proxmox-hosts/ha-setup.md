# Proxmox High Availability (HA) Setup Guide

This guide covers setting up High Availability for your Proxmox cluster to ensure automatic failover of VMs and containers.

## Contents

* [Prerequisites](#prerequisites)
* [Understanding Proxmox HA](#understanding-proxmox-ha)
* [Configuring HA](#configuring-ha)
* [Adding VMs/Containers to HA](#adding-vmscontainers-to-ha)
* [Testing HA Failover](#testing-ha-failover)
* [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)

## Prerequisites

Before setting up HA, ensure:

1. **Cluster is properly configured** - All 3 nodes (jmpa-server-1, jmpa-server-2, jmpa-server-3) are in the same cluster
2. **Shared storage** - You need shared storage accessible by all nodes:
   - NFS storage from your NAS (jmpa-nas-1)
   - Ceph storage (if configured)
   - iSCSI storage
   - Or other shared storage solutions
3. **Quorum** - With 3 nodes, you have proper quorum (minimum 2 nodes must be online)
4. **Network connectivity** - All nodes can communicate with each other
5. **Time synchronization** - All nodes have synchronized time (chrony is already installed)

## Understanding Proxmox HA

Proxmox HA uses:
- **Corosync** - Cluster communication layer (already configured when you joined the cluster)
- **HA Manager** - Monitors and manages HA resources
- **Fencing** - Ensures failed nodes don't cause split-brain scenarios
- **Quorum** - Requires majority of nodes to be online (2 out of 3 in your case)

### HA States

- **started** - VM/CT should be running
- **stopped** - VM/CT should be stopped
- **ignored** - HA manager ignores this resource
- **disabled** - HA is disabled for this resource

### Fencing Modes

- **hardware** - Uses hardware watchdog (recommended for production)
- **software** - Uses software watchdog (simpler, less reliable)

## Configuring HA

### Step 1: Verify Cluster Status

```bash
# Check cluster status
pvecm status

# Expected output should show:
# - Quorum information
# - All 3 nodes listed
# - Cluster name: homelab (or your cluster name)

# Check corosync status
systemctl status corosync

# Check pve-ha-lrm (Local Resource Manager)
systemctl status pve-ha-lrm

# Check pve-ha-crm (Cluster Resource Manager)
systemctl status pve-ha-crm
```

### Step 2: Configure Shared Storage

Your VMs/containers must be on shared storage for HA to work. Based on your setup, you have a NAS (jmpa-nas-1).

#### Option A: NFS Storage (Recommended for your setup)

On your NAS, ensure NFS exports are configured. Then on each Proxmox node:

```bash
# Add NFS storage via Proxmox UI:
# Datacenter > Storage > Add > NFS

# Or via CLI on one node (it will sync to all nodes):
pvesm add nfs nas-nfs \
  --server <NAS_IP> \
  --export /path/to/export \
  --content images,rootdir \
  --nodes jmpa-server-1,jmpa-server-2,jmpa-server-3
```

#### Option B: Ceph Storage (For advanced setups)

If you want to use Ceph (requires additional setup):

```bash
# Install Ceph on all nodes
pveceph install

# Initialize Ceph on first node
pveceph init --network <cluster_network>

# Create monitors on all nodes
pveceph mon create

# Create OSDs (one per disk you want to use)
pveceph osd create /dev/sdX
```

### Step 3: Configure Fencing

For production environments, configure hardware watchdog. For testing, software watchdog is sufficient:

```bash
# On each Proxmox node:

# Check if hardware watchdog is available
lsmod | grep watchdog

# If available, load the module
echo "softdog" >> /etc/modules
modprobe softdog

# Configure watchdog in HA
# Edit /etc/pve/ha/manager_status (this is managed by Proxmox)
# The HA manager will automatically use the watchdog
```

### Step 4: Configure HA Groups (Optional)

HA groups allow you to control which nodes can run specific VMs:

```bash
# Via Proxmox UI:
# Datacenter > HA > Groups > Create

# Or via CLI:
ha-manager groupadd preferred_nodes \
  --nodes "jmpa-server-1:2,jmpa-server-2:1,jmpa-server-3:1" \
  --comment "Prefer server-1, fallback to others"

# The numbers after colons are priorities (higher = preferred)
```

## Adding VMs/Containers to HA

### Via Proxmox Web UI

1. Navigate to **Datacenter > HA > Resources**
2. Click **Add**
3. Select the VM/Container ID
4. Configure:
   - **State**: `started` (VM should always be running)
   - **Group**: Select HA group (optional)
   - **Max Restart**: `3` (attempts before giving up)
   - **Max Relocate**: `3` (migration attempts)
5. Click **Add**

### Via CLI

```bash
# Add a VM to HA
ha-manager add vm:100 \
  --state started \
  --max_restart 3 \
  --max_relocate 3

# Add a container to HA
ha-manager add ct:5 \
  --state started \
  --max_restart 3 \
  --max_relocate 3

# Add with specific group
ha-manager add vm:100 \
  --state started \
  --group preferred_nodes

# List HA resources
ha-manager config

# Remove from HA
ha-manager remove vm:100
```

### Recommended VMs/Containers for HA

Based on your [`inventory/main.py`](inventory/main.py:1), consider adding these to HA:

```bash
# Critical services that should always be available:

# Nginx Reverse Proxy (Container ID: 5)
ha-manager add ct:5 --state started --max_restart 3

# Tailscale Gateway (Container ID: 15)
ha-manager add ct:15 --state started --max_restart 3

# Prometheus (Container ID: 40)
ha-manager add ct:40 --state started --max_restart 3

# Grafana (Container ID: 45)
ha-manager add ct:45 --state started --max_restart 3

# Proxmox Backup Server (VMID: 100)
ha-manager add vm:100 --state started --max_restart 3

# Uptime Kuma (VMID: 155)
ha-manager add vm:155 --state started --max_restart 3
```

## Testing HA Failover

### Test 1: Graceful Node Shutdown

```bash
# On one of your nodes (e.g., jmpa-server-2):
shutdown -h now

# Watch the HA manager migrate VMs to other nodes:
# On remaining nodes:
watch -n 2 'ha-manager status'

# Check VM locations:
pvesh get /cluster/resources --type vm
```

### Test 2: Simulated Node Failure

```bash
# On one node, stop cluster services (simulates crash):
systemctl stop pve-cluster
systemctl stop corosync

# Watch HA manager fence the node and restart VMs elsewhere
# On another node:
ha-manager status
pvecm status
```

### Test 3: Network Partition

```bash
# Temporarily block cluster communication:
iptables -A INPUT -p udp --dport 5404:5405 -j DROP
iptables -A OUTPUT -p udp --dport 5404:5405 -j DROP

# Watch quorum behavior
pvecm status

# Restore (IMPORTANT - don't forget this):
iptables -D INPUT -p udp --dport 5404:5405 -j DROP
iptables -D OUTPUT -p udp --dport 5404:5405 -j DROP
```

## Monitoring and Troubleshooting

### Check HA Status

```bash
# View HA manager status
ha-manager status

# View HA configuration
ha-manager config

# Check cluster quorum
pvecm status

# View HA logs
journalctl -u pve-ha-lrm -f
journalctl -u pve-ha-crm -f

# Check corosync logs
journalctl -u corosync -f
```

### Common Issues

#### Issue: "no quorum" Error

**Cause**: Less than 2 nodes are online in your 3-node cluster.

**Solution**:
```bash
# Check which nodes are online
pvecm status

# If you need to temporarily work with 1 node (DANGEROUS):
pvecm expected 1

# Restore normal quorum when nodes are back:
pvecm expected 2
```

#### Issue: VM Won't Migrate

**Cause**: VM is on local storage, not shared storage.

**Solution**:
```bash
# Check VM storage
qm config <VMID>

# Migrate VM to shared storage
qm move-disk <VMID> <disk> <target-storage> --delete

# Example:
qm move-disk 100 scsi0 nas-nfs --delete
```

#### Issue: HA Manager Not Starting VMs

**Cause**: Fencing not configured or watchdog issues.

**Solution**:
```bash
# Check watchdog
systemctl status watchdog-mux

# Restart HA services
systemctl restart pve-ha-lrm
systemctl restart pve-ha-crm

# Check HA manager logs
journalctl -u pve-ha-crm -n 100
```

#### Issue: Split-Brain Scenario

**Cause**: Network partition causing multiple nodes to think they have quorum.

**Solution**:
```bash
# Stop cluster services on the minority partition
systemctl stop pve-ha-lrm
systemctl stop pve-ha-crm
systemctl stop corosync
systemctl stop pve-cluster

# Fix network issues
# Restart services
systemctl start pve-cluster
systemctl start corosync
systemctl start pve-ha-crm
systemctl start pve-ha-lrm
```

### Monitoring with Prometheus/Grafana

Your setup already includes Prometheus and Grafana. Add these metrics:

```yaml
# Add to Prometheus config for HA monitoring:
- job_name: 'proxmox-ha'
  static_configs:
    - targets:
      - 'jmpa-server-1:8006'
      - 'jmpa-server-2:8006'
      - 'jmpa-server-3:8006'
  metrics_path: '/api2/json/cluster/ha/status'
```

## Best Practices

1. **Always use shared storage** for HA-enabled VMs/containers
2. **Test failover regularly** to ensure HA works when needed
3. **Monitor quorum status** - set up alerts for quorum loss
4. **Keep nodes synchronized** - ensure time sync (chrony) is working
5. **Document your HA groups** - know which VMs run where
6. **Plan maintenance windows** - use `ha-manager set vm:100 --state stopped` before maintenance
7. **Backup regularly** - HA doesn't replace backups (you have PBS configured)
8. **Use hardware watchdog** in production for reliable fencing
9. **Monitor HA logs** - integrate with your monitoring stack
10. **Keep cluster size odd** - 3 nodes is ideal for quorum

## Quick Reference Commands

```bash
# HA Management
ha-manager add vm:100 --state started          # Add VM to HA
ha-manager remove vm:100                       # Remove from HA
ha-manager set vm:100 --state stopped          # Stop HA VM
ha-manager migrate vm:100 jmpa-server-2        # Migrate to specific node
ha-manager status                              # View HA status
ha-manager config                              # View HA config

# Cluster Management
pvecm status                                   # Cluster status
pvecm nodes                                    # List nodes
pvecm expected 2                               # Set expected votes

# Resource Management
pvesh get /cluster/resources --type vm         # List all VMs
pvesh get /cluster/ha/resources                # List HA resources
pvesh get /cluster/ha/status/current           # Current HA status

# Service Management
systemctl status pve-ha-lrm                    # Local Resource Manager
systemctl status pve-ha-crm                    # Cluster Resource Manager
systemctl status corosync                      # Cluster communication
systemctl status pve-cluster                   # Cluster filesystem
```

## Next Steps

1. **Configure shared storage** (NFS from your NAS)
2. **Test HA with a non-critical VM** first
3. **Add critical services to HA** one by one
4. **Set up monitoring alerts** for HA events
5. **Document your HA configuration** and failover procedures
6. **Schedule regular HA testing** (monthly recommended)

## Additional Resources

- [Proxmox HA Documentation](https://pve.proxmox.com/wiki/High_Availability)
- [Proxmox Cluster Manager](https://pve.proxmox.com/wiki/Cluster_Manager)
- [Corosync Documentation](https://clusterlabs.org/corosync.html)
- Your existing setup docs: [`./setup.md`](./setup.md)
