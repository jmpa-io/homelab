# NAS Instance Configuration

Configuration for Terramaster NAS.

## Roles

- **base** - System packages and configuration
- **tailscale** - VPN connectivity

## NFS Exports

Volumes are auto-discovered by Proxmox hosts using `showmount -e`:
- Volume 1: Future use
- Volume 2: Large storage
- Volume 3: Backups (1TB)
- Volume 4: SSD storage (K3s)

## Usage

```bash
# Deploy NAS configuration
ansible-playbook playbook.yml -i inventory/main.py --limit nas
```
