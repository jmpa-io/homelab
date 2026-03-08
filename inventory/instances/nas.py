"""NAS (Network Attached Storage) instance type.

Class Hierarchy:
Instance
└── NAS
"""

from dataclasses import dataclass, field

from .instance import Instance


@dataclass
class NAS(Instance):
    """Network Attached Storage instance.

    Attributes:
        name: Instance name template (default: 'nas-{id}')
        ipv4: IPv4 address
        ipv4_cidr: CIDR notation
        device_name: Network interface name
        host_services: List of host services
    """
    name: str = field(default='nas-{id}')  # Changed from jmpa-nas-{id}

    def to_dict(self) -> dict:
        """Convert to dictionary with 'nas' key instead of 'instance'."""
        base = self._base_dict()
        base['nas'] = base.pop('instance')
        return base
