"""Base classes for homelab instance types.

Class hierarchy:
Instance (Base)
└── NetworkedInstance
    ├── NAS
    ├── DNS
    └── ContainerInstance
        └── ProxmoxHost
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from abc import ABC, abstractmethod
from copy import deepcopy

from service import HostService


@dataclass
class Instance(ABC):
    """Base class for all instance types.

    Attributes:
        name: Instance name for identification
        host_services: List of services running on the instance
    """
    name: str = field(init=False)  # Set by child classes
    host_services: List[HostService] = field(default_factory=list)

    def __post_init__(self):
        """Deep copy host services to avoid sharing between instances."""
        self.host_services = deepcopy(self.host_services)

    @abstractmethod
    def to_dict(self) -> dict:
        """Convert instance to Ansible inventory dictionary format."""
        pass

    def get_host_services(self) -> Dict[str, Any]:
        """Get host services as {'host_services': [service_dict, ...]}."""
        return {
            "host_services": [s.to_dict() for s in self.host_services]
        }


@dataclass
class NetworkedInstance(Instance):
    """Base class for instances that require network configuration.

    This class extends Instance to add common networking functionality
    used by most instance types. It handles IP address management,
    CIDR notation, and Ansible host configuration.

    Attributes:
        name: Instance name template (e.g., 'server-{id}')
        ipv4: IPv4 address of the instance
        ipv4_cidr: CIDR notation number (e.g., 24 for /24)
        device_name: Name of the network interface (e.g., eth0, wlan0)
        ansible_host: Ansible connection address (derived from ipv4)
        ipv4_with_cidr: Full CIDR notation (e.g., 192.168.1.1/24)
    """
    name: str  # Template like 'server-{id}' - will be formatted by inventory
    ipv4: str
    ipv4_cidr: str
    device_name: str
    ansible_host: str = field(init=False)
    ipv4_with_cidr: str = field(init=False)

    def __post_init__(self):
        """Set up network fields and initialize parent."""
        super().__post_init__()  # Initialize host services
        self.ansible_host = self.ipv4
        self.ipv4_with_cidr = f'{self.ipv4}/{self.ipv4_cidr}'

    def to_dict(self) -> dict:
        """Convert to standard network configuration format."""
        base = {
            'name': self.name,
            'ipv4': self.ipv4,
            'ipv4_cidr': self.ipv4_cidr,
            'ipv4_with_cidr': self.ipv4_with_cidr,
            'device_name': self.device_name,
        }
        base.update(self.get_host_services())
        return {
            'ansible_host': self.ansible_host,
            'instance': base,
        }
