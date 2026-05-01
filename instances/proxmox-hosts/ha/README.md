# Proxmox High Availability Ansible Role

This role configures High Availability for Proxmox VE clusters.

## Requirements

- Proxmox cluster with at least 3 nodes (for proper quorum)
- Shared storage (NFS, Ceph, or iSCSI) configured and accessible by all nodes
- VMs/Containers must be on shared storage to be HA-enabled

## Role Variables

See [`vars/main.yml`](vars/main.yml) for configuration options.

### HA Groups

Define HA groups to control which nodes can run specific VMs:

```yaml
ha_groups:
  - name: preferred_nodes
    nodes: "jmpa-server-1:3,jmpa-server-2:2,jmpa-server-3:1"
    comment: "Prefer server-1, fallback to others"
```

The numbers after colons are priorities (higher = preferred).

### HA VMs

Define VMs to add to HA:

```yaml
ha_vms:
  - vmid: 100
    state: started
    max_restart: 3
    max_relocate: 3
    group: preferred_nodes  # Optional
```

### HA Containers

Define containers to add to HA:

```yaml
ha_containers:
  - ctid: 5
    state: started
    max_restart: 3
    max_relocate: 3
```

## Usage

### Include in your playbook

```yaml
- name: Configure Proxmox HA
  hosts: proxmox_hosts
  become: true
  roles:
    - role: "{{ playbook_dir }}/instances/proxmox-hosts/ha"
```

### Or use tasks directly

```yaml
- name: Configure Proxmox HA
  hosts: proxmox_hosts
  become: true
  tasks:
    - name: Include HA tasks
      ansible.builtin.include_tasks:
        file: "{{ playbook_dir }}/instances/proxmox-hosts/ha/tasks/main.yml"
```

## What This Role Does

1. ✅ Verifies cluster is properly configured
2. ✅ Installs HA packages (pve-ha-manager, corosync, pacemaker)
3. ✅ Configures watchdog for fencing
4. ✅ Ensures HA services are running
5. ✅ Verifies shared storage is available
6. ✅ Creates HA groups (if defined)
7. ✅ Adds VMs to HA (if defined)
8. ✅ Adds containers to HA (if defined)
9. ✅ Displays HA configuration and status

## Example Playbook

See [`playbooks/setup-ha.yml`](../../../playbooks/setup-ha.yml) for a complete example.

## Testing HA

After running this role, test HA failover:

```bash
# On one node, simulate failure
systemctl stop pve-cluster

# On another node, watch HA migrate resources
watch -n 2 'ha-manager status'
```

## Monitoring

Check HA status:

```bash
# View HA status
ha-manager status

# View HA configuration
ha-manager config

# Check cluster quorum
pvecm status

# View HA logs
journalctl -u pve-ha-lrm -f
journalctl -u pve-ha-crm -f
```

## Related Documentation

- [HA Setup Guide](../ha-setup.md) - Comprehensive HA setup documentation
- [Proxmox Setup](../setup.md) - Initial Proxmox cluster setup
