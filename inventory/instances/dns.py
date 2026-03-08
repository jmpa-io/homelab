"""DNS server instance type.

Class Hierarchy:
Instance
└── DNS
"""

from dataclasses import dataclass

from .instance import Instance


@dataclass
class DNS(Instance):
    """DNS server instance.

    Attributes:
        ipv4: IPv4 address
        ipv4_cidr: CIDR notation
        device_name: Network interface name
        name: Instance name template
    """
    name: str = 'jmpa-dns-{id}'

    def to_dict(self) -> dict:
        """Convert to dictionary with 'dns' key instead of 'instance'."""
        base = self._base_dict()
        base['dns'] = base.pop('instance')
        return base
