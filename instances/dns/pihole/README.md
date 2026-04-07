# Pi-hole Role

This role installs and configures Pi-hole on the Raspberry Pi 2B running Raspbian.

## What It Does

1. **Installation**: Installs Pi-hole directly on Raspbian using the official installer
2. **Configuration**: Auto-generates DNS records from inventory (single source of truth)

## Features

- ✅ Unattended Pi-hole installation
- ✅ Automatic DNS record generation from inventory
- ✅ A records for all services (FQDN + short hostname)
- ✅ CNAME records for Proxmox hosts
- ✅ Idempotent operations with backups
- ✅ Automatic service restart when DNS changes

## Usage

This role runs automatically when deploying the DNS host:

```bash
# Deploy DNS (includes Pi-hole installation and configuration)
ansible-playbook playbook.yml -i inventory.json --limit dns

# Update DNS configuration only (after adding services)
ansible-playbook playbook.yml -i inventory.json --tags dns
```

## Adding New Services

To add a new service with automatic DNS records:

1. Edit [`inventory/main.py`](../../../inventory/main.py)
2. Add service to `community_services` list:

```python
CommunityScriptService(
    name='my_service',
    vmid=160,
    hostname='myservice',
    port='8080',
    protocol=Protocol.HTTP,
)
```

3. Re-run the playbook - DNS records are automatically created

## Variables

See [`vars/main.yml`](vars/main.yml) for configuration options:

- `pihole_password`: Web interface password (optional)
- `pihole_interface`: Network interface (default: eth0)
- `pihole_ipv4_address`: Static IP address
- `pihole_query_logging`: Enable query logging (default: true)
- `pihole_install_web_interface`: Install web UI (default: true)

## Files Generated

- `/etc/pihole/custom.list` - A records for all services
- `/etc/dnsmasq.d/05-pihole-custom-cname.conf` - CNAME records
- `/etc/pihole/setupVars.conf` - Pi-hole configuration

## DNS Records Format

### A Records
```
10.0.1.40 prometheus.jmpa.lab
10.0.1.40 prometheus
```

### CNAME Records
```
cname=prometheus,prometheus.jmpa.lab
```

## Architecture

Pi-hole runs directly on the Raspberry Pi 2B (Raspbian), NOT as an LXC container. This is because:

- DNS server is a physical device
- NFS mounts are configured on Raspbian
- Tailscale VPN is configured on Raspbian
- Simplifies network configuration

## Troubleshooting

### Check Pi-hole Status
```bash
pihole status
```

### View DNS Records
```bash
cat /etc/pihole/custom.list
cat /etc/dnsmasq.d/05-pihole-custom-cname.conf
```

### Test DNS Resolution
```bash
dig @localhost prometheus.jmpa.lab
nslookup prometheus.jmpa.lab localhost
```

### Restart Pi-hole
```bash
pihole restartdns
```

## Related Files

- [`inventory/service.py`](../../../inventory/service.py) - Service class with IP calculation
- [`inventory/main.py`](../../../inventory/main.py) - Service registry
- [`playbook.yml`](../../../playbook.yml) - Main playbook
