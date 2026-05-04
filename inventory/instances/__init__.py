"""
Homelab Instances Package
========================

Class Hierarchy
--------------
Instance (Base)
├── NAS
├── DNS
├── EC2
└── ContainerInstance
    ├── ProxmoxHost  (on-prem bare metal)
    └── VPS          (cloud KVM VPS running Proxmox, same capabilities)

Instance Types
-------------
- ProxmoxHost: Physical servers running Proxmox VE.
  Naming: jmpa-server-{id} (e.g. jmpa-server-1)
  Bridge: 10.0.{host_id}.0/24 (host_id = 1, 2, 3)

- VPS: Cloud KVM VPS running Proxmox VE, connected via Tailscale.
  Treated identically to ProxmoxHost in the inventory.
  Naming: jmpa-vps-{id} (e.g. jmpa-vps-1)
  Bridge: 10.0.{host_id}.0/24 (host_id = 4, 5, ... — offset by 3 from ProxmoxHosts)

- NAS: Network Attached Storage.
  Naming: jmpa-nas-{id}

- DNS: DNS server (Raspberry Pi running Pi-hole).
  Naming: jmpa-dns-{id}

- EC2: AWS EC2 instance (not Proxmox — plain Linux).
  Naming: jmpa-ec2-{id}
"""

from .proxmox_host import ProxmoxHost
from .vps import VPS
from .nas import NAS
from .dns import DNS
from .ec2 import EC2

__all__ = ["ProxmoxHost", "VPS", "NAS", "DNS", "EC2"]
