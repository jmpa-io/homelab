"""NAS (Network Attached Storage) instance type.

Class Hierarchy:
Instance
└── NAS
"""

from dataclasses import dataclass, field
from typing import List

from .instance import Instance


@dataclass
class NAS(Instance):
    """Network Attached Storage instance.

    Attributes:
        ipv4: IPv4 address
        ipv4_cidr: CIDR notation
        device_name: Network interface name
        name: Instance name template
        host_services: List of host services
        ansible_port: SSH port for Ansible connections
        ansible_user: SSH user (defaults to instance name)

    Note:
        NAS volumes are auto-discovered via NFS exports (showmount -e)
        rather than being hardcoded in the inventory.
    """
    name: str = 'jmpa-nas-{id}'
    ansible_port: int = 9222

    def get_ansible_user(self) -> str:
        """Return the resolved instance name as the ansible_user."""
        return self.name

    def to_dict(self) -> dict:
        """Convert to dictionary with 'nas' key instead of 'instance'."""
        base = self._base_dict()
        nas_data = base.pop('instance')
        base['nas'] = nas_data
        return base
