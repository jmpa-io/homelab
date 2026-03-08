"""
Homelab Instances Package
========================

This package defines all instance types supported in the homelab inventory system.
Each instance type represents a different kind of server or service host in the
infrastructure.

Class Hierarchy
--------------
Instance (Base)
├── NAS (Network Attached Storage)
├── DNS (Domain Name Server)
└── ContainerInstance
    └── ProxmoxHost

Instance Types
-------------
- ProxmoxHost: Physical servers running Proxmox VE, supporting both LXC containers
  and VMs. These are the main compute nodes in the homelab.
  Naming pattern: server-{id} (e.g., server-1, server-2)

- NAS: Network Attached Storage servers that provide centralized storage services.
  These run services directly on the host without containers.
  Naming pattern: nas-{id} (e.g., nas-1, nas-2)

- DNS: DNS servers that manage domain name resolution for the homelab. These
  handle both forward and reverse zones.
  Naming pattern: dns-{id} (e.g., dns-1, dns-2)

Common Features
-------------
All instances include:
- IP address management and CIDR notation
- Network device configuration
- Host service support
- Ansible inventory integration

Usage Example
------------
```python
from instances import ProxmoxHost, NAS, DNS
from instances.proxmox_host import ProxmoxHostBridge

# Create a Proxmox host (becomes server-1).
host = ProxmoxHost(
    ipv4='192.168.1.10',
    ipv4_cidr='24',
    device_name='eth0',
    bridge=ProxmoxHostBridge(
        name='vmbr0',
        ipv4_prefix='10.0',
        ipv4_suffix='1',
        ipv4_cidr='24'
    )
)

# Create a NAS instance (becomes nas-1).
nas = NAS(
    ipv4='192.168.1.20',
    ipv4_cidr='24',
    device_name='eth0'
)

# Create a DNS instance (becomes dns-1).
dns = DNS(
    ipv4='192.168.1.53',
    ipv4_cidr='24',
    device_name='eth0'
)
```
"""

from .proxmox_host import ProxmoxHost
from .vps import VPS
from .nas import NAS
from .dns import DNS

__all__ = ["ProxmoxHost", "VPS", "NAS", "DNS"]
