from dataclasses import dataclass, field
from typing import List, Dict, Any
from abc import ABC, abstractmethod

from service import Service, HostService


@dataclass
class Instance(ABC):
    """Base class for all instance types."""
    ansible_host: str = field(init=False)
    ipv4: str
    ipv4_cidr: str
    ipv4_with_cidr: str = field(init=False)
    wifi_device_name: str
    
    # Host services that run directly on the instance
    host_services: List[HostService]

    def __post_init__(self):
        self.ansible_host = self.ipv4
        self.ipv4_with_cidr = f'{self.ipv4}/{self.ipv4_cidr}'

    @abstractmethod
    def to_dict(self) -> dict:
        """Convert instance to dictionary for Ansible consumption."""
        pass

    def get_host_services(self) -> Dict[str, Any]:
        """Get host services as a list under 'host_services'."""
        return {
            "host_services": [s.to_dict() for s in self.host_services]
        }



