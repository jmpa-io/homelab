# Secondary Pi-hole Setup Guide

This guide explains how to add a second Raspberry Pi as a secondary DNS server for high availability.

## Architecture

```
Primary DNS:   Raspberry Pi 2B (10.0.0.2) - dns
Secondary DNS: Raspberry Pi 2B (10.0.0.3) - dns2
```

Both Pi-holes will:
- Run the same configuration
- Have identical DNS records (auto-synced from inventory)
- Provide failover if one goes down

## Setup Steps

### 1. Add Secondary DNS to Inventory

Edit [`inventory/main.py`](../inventory/main.py) and add the second DNS host:

```python
# DNS Servers
dns_primary = DNS(
    hostname='dns',
    ipv4='10.0.0.2',
    user='pi',
    ssh_key_path='~/.ssh/id_rsa',
)

dns_secondary = DNS(
    hostname='dns2',
    ipv4='10.0.0.3',
    user='pi',
    ssh_key_path='~/.ssh/id_rsa',
)

# Add both to inventory
inventory_vars['dns'] = [dns_primary, dns_secondary]
```

### 2. Configure AWS SSM Parameters

Add the secondary DNS to your AWS SSM parameters:

```bash
# Add dns2 host
aws ssm put-parameter \
  --name "/homelab/hosts/dns2/ipv4" \
  --value "10.0.0.3" \
  --type "String"

aws ssm put-parameter \
  --name "/homelab/hosts/dns2/user" \
  --value "pi" \
  --type "String"
```

### 3. Deploy Secondary Pi-hole

The same playbook works for both DNS servers:

```bash
# Deploy both DNS servers
ansible-playbook playbook.yml -i inventory.json --limit dns

# Or deploy only secondary
ansible-playbook playbook.yml -i inventory.json --limit dns2
```

### 4. Configure Network Clients

Update your DHCP server or client configurations to use both DNS servers:

```
Primary DNS:   10.0.0.2
Secondary DNS: 10.0.0.3
```

**On Proxmox hosts**, this is already configured in [`instances/proxmox-hosts/networking-and-dns/templates/etc/network/interfaces.j2`](../instances/proxmox-hosts/networking-and-dns/templates/etc/network/interfaces.j2):

```
dns-nameservers 10.0.0.2 10.0.0.3
```

### 5. Verify Both Pi-holes

```bash
# Test primary
dig @10.0.0.2 prometheus.jmpa.lab

# Test secondary
dig @10.0.0.3 prometheus.jmpa.lab

# Both should return the same result
```

## Configuration Sync

Both Pi-holes will automatically have identical DNS records because they're generated from the same inventory source.

### Automatic Sync (via Ansible)
Every time you run the playbook, both Pi-holes get updated:

```bash
# Update DNS records on both Pi-holes
ansible-playbook playbook.yml -i inventory.json --limit dns
```

### Manual Sync (Gravity Sync) - Optional

For syncing Pi-hole settings (blocklists, whitelist, etc.), you can optionally set up [Gravity Sync](https://github.com/vmstan/gravity-sync):

```bash
# On secondary Pi-hole
curl -sSL https://raw.githubusercontent.com/vmstan/gs-install/main/gs-install.sh | bash

# Configure to sync from primary
gravity-sync config
# Primary: 10.0.0.2
# Secondary: 10.0.0.3

# Run sync
gravity-sync pull
```

## High Availability Behavior

### Normal Operation
- Clients query primary DNS (10.0.0.2)
- If no response within ~2 seconds, query secondary (10.0.0.3)

### Primary Failure
- All queries automatically go to secondary
- No manual intervention needed
- DNS resolution continues uninterrupted

### Secondary Failure
- All queries go to primary
- No impact on DNS resolution

### Both Failure
- Clients fall back to upstream DNS (if configured)
- Or DNS resolution fails

## Monitoring

Both Pi-holes export metrics to Prometheus via OpenTelemetry:

```yaml
# Prometheus query
pihole_queries_total{instance="dns"}
pihole_queries_total{instance="dns2"}
```

## Maintenance

### Update Both Pi-holes

```bash
# Update all infrastructure including both DNS servers
ansible-playbook playbooks/update-all.yml -i inventory.json

# Or update only DNS servers
ansible-playbook playbooks/update-all.yml -i inventory.json --limit dns
```

### Add New Service

When you add a service to [`inventory/main.py`](../inventory/main.py), both Pi-holes automatically get the DNS record:

```python
# Add service
CommunityScriptService(
    name='new_service',
    vmid=170,
    hostname='newservice',
    port='8080',
    protocol=Protocol.HTTP,
)

# Deploy - both Pi-holes updated
ansible-playbook playbook.yml -i inventory.json --limit dns
```

## Troubleshooting

### Check Pi-hole Status

```bash
# Primary
ssh pi@10.0.0.2 'pihole status'

# Secondary
ssh pi@10.0.0.3 'pihole status'
```

### Compare DNS Records

```bash
# Primary
ssh pi@10.0.0.2 'cat /etc/pihole/custom.list'

# Secondary
ssh pi@10.0.0.3 'cat /etc/pihole/custom.list'

# Should be identical
```

### Test Failover

```bash
# Stop primary Pi-hole
ssh pi@10.0.0.2 'sudo systemctl stop pihole-FTL'

# Test DNS still works via secondary
dig @10.0.0.3 prometheus.jmpa.lab

# Restart primary
ssh pi@10.0.0.2 'sudo systemctl start pihole-FTL'
```

## Network Configuration

### Router/DHCP Server
Configure your router to advertise both DNS servers:
- Primary DNS: 10.0.0.2
- Secondary DNS: 10.0.0.3

### Static Configuration
For hosts with static IPs, configure both DNS servers in `/etc/resolv.conf`:

```
nameserver 10.0.0.2
nameserver 10.0.0.3
```

## Benefits

✅ **High Availability** - DNS continues if one Pi-hole fails
✅ **Load Distribution** - Clients can query either server
✅ **Maintenance Window** - Update one Pi-hole while other serves DNS
✅ **Identical Configuration** - Both auto-configured from inventory
✅ **Simple Management** - Same playbook manages both

## Cost

- **Hardware**: ~$35 for Raspberry Pi 2B
- **Power**: ~2.5W per Pi-hole (~$3/year)
- **Maintenance**: Automated via Ansible

## Future Enhancements

1. **Geographic Distribution** - Place Pi-holes in different locations
2. **Load Balancing** - Use DNS load balancing for query distribution
3. **Anycast DNS** - Advanced setup with same IP on both (requires routing)
4. **Automated Failover Testing** - Periodic health checks and alerts

---

**Related Documentation:**
- [Main README](README.md)
- [Pi-hole Role](../instances/dns/pihole/README.md)
- [Implementation Summary](implementation-summary.md)
