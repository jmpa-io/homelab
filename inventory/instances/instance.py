"""Base classes for homelab instance types.

Class hierarchy:
Instance (Base)
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
        ipv4: IPv4 address
        ipv4_cidr: CIDR notation (e.g., 24)
        device_name: Network interface name (e.g., eth0)
        name: Instance name template (e.g., 'server-{id}')
        host_services: List of services running on the instance
        ansible_host: Ansible connection address
        ipv4_with_cidr: Full CIDR (e.g., 192.168.1.1/24)
    """
    ipv4: str
    ipv4_cidr: str
    device_name: str
    name: str = 'jmpa-instance-{id}'
    host_services: List[HostService] = field(default_factory=list)
    ansible_host: str = field(init=False)
    ipv4_with_cidr: str = field(init=False)

    def __post_init__(self):
        """Set up network fields and deep copy host services."""
        self.host_services = deepcopy(self.host_services)
        self.ansible_host = self.ipv4
        self.ipv4_with_cidr = f'{self.ipv4}/{self.ipv4_cidr}'

    @abstractmethod
    def to_dict(self) -> dict:
        """Convert instance to Ansible inventory dictionary format."""
        pass

    def get_host_services(self) -> Dict[str, Any]:
        """Get host services as {'host_services': [service_dict, ...]}."""
        return {
            "host_services": [s.to_dict() for s in self.host_services]
        }

    def _base_dict(self) -> dict:
        """Get base instance configuration."""
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
