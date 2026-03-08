"""NAS (Network Attached Storage) instance type.

Class Hierarchy:
Instance
└── NAS
"""

from dataclasses import dataclass, field

from .instance import Instance
from ..env import read_env_var


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
    """
    name: str = 'jmpa-nas-{id}'
    ansible_port: int = field(default_factory=lambda: int(read_env_var('NAS_SSH_PORT', default_value='9222')))

    def to_dict(self) -> dict:
        """Convert to dictionary with 'nas' key instead of 'instance'."""
        base = self._base_dict()
        base['nas'] = base.pop('instance')
        base['ansible_port'] = self.ansible_port
        base['ansible_user'] = base['nas']['name']
        return base
