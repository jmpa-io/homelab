"""DNS server instance type.

Class Hierarchy:
Instance
└── DNS
"""

from dataclasses import dataclass

from .instance import Instance


@dataclass
class DNS(Instance):
    """DNS server instance (Raspberry Pi running Pi-hole)."""
    name: str = 'jmpa-dns-{id}'

    def to_dict(self) -> dict:
        """Convert to dictionary with 'dns' key instead of 'instance'."""
        base = self._base_dict()
        base['dns'] = base.pop('instance')
        return base
