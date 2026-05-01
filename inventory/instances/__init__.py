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
├── EC2 (AWS EC2 instance)
└── ContainerInstance
    ├── VPS
    └── ProxmoxHost

Instance Types
-------------
- ProxmoxHost: Physical servers running Proxmox VE, supporting both LXC containers
  and VMs. These are the main compute nodes in the homelab.
  Naming pattern: jmpa-server-{id} (e.g., jmpa-server-1)

- NAS: Network Attached Storage servers that provide centralized storage services.
  Naming pattern: jmpa-nas-{id}

- DNS: DNS servers that manage domain name resolution for the homelab.
  Naming pattern: jmpa-dns-{id}

- EC2: AWS EC2 instances that join the fleet as cloud members. Cannot run LXC
  containers or Proxmox VMs, but can run native services and join k3s as workers.
  Naming pattern: jmpa-ec2-{id}
"""

from .proxmox_host import ProxmoxHost
from .vps import VPS
from .nas import NAS
from .dns import DNS
from .ec2 import EC2

__all__ = ["ProxmoxHost", "VPS", "NAS", "DNS", "EC2"]
