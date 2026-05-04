"""ContainerInstance extends Instance to support LXC containers.

Class Hierarchy:
Instance
└── ContainerInstance
    ├── ProxmoxHost  (on-prem bare metal)
    └── VPS          (cloud KVM VPS running Proxmox)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from copy import deepcopy

from .instance import Instance
from service import Service


@dataclass
class ContainerInstance(Instance):
    """Instance that supports LXC container services.

    Attributes:
        name: Instance name template
        ipv4: IPv4 address
        ipv4_cidr: CIDR notation
        device_name: Network interface name
        lxc_services: List of LXC container services
    """
    lxc_services: List[Service] = field(default_factory=list)

    def __post_init__(self):
        """Initialize network config and deep copy services."""
        super().__post_init__()  # Initialize network and host services
        self.lxc_services = deepcopy(self.lxc_services)

    def get_container_services(self) -> Dict[str, Any]:
        """Get container services mapped by name."""
        return {s.name: s.to_dict() for s in self.lxc_services}

    def to_dict(self) -> dict:
        """Convert to dictionary with instance and service configs."""
        base = self._base_dict()
        base['services'] = self.get_container_services()
        return base
