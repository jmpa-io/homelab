"""ContainerInstance extends NetworkedInstance to support LXC containers.

Class Hierarchy:
Instance
└── NetworkedInstance
    └── ContainerInstance
        └── ProxmoxHost
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from copy import deepcopy

from .instance import NetworkedInstance
from service import Service


@dataclass
class ContainerInstance(NetworkedInstance):
    """Instance that supports LXC container services.

    Attributes:
        name: Instance name template
        ipv4: IPv4 address
        ipv4_cidr: CIDR notation
        device_name: Network interface name
        lxc_services: List of LXC container services
    """
    # Required fields from NetworkedInstance must come first
    ipv4: str
    ipv4_cidr: str
    device_name: str
    # Optional fields with defaults
    name: str = field(default='server-{id}')
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
        base = super().to_dict()
        base['services'] = self.get_container_services()
        return base
