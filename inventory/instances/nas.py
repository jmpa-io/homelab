"""NAS (Network Attached Storage) instance type.

Class Hierarchy:
Instance
└── NAS
"""

from dataclasses import dataclass

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
        ansible_user: SSH user for Ansible connections (defaults to instance name)
    """
    name: str = 'jmpa-nas-{id}'
    ansible_port: int = 9222

    def __post_init__(self):
        """Initialize NAS instance and set ansible_user to instance name."""
        super().__post_init__()
        # Set ansible_user to the resolved instance name.
        self.ansible_user = self.name

    def to_dict(self) -> dict:
        """Convert to dictionary with 'nas' key instead of 'instance'."""
        base = self._base_dict()
        base['nas'] = base.pop('instance')
        return base
