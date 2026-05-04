"""DNS server instance type.

Class Hierarchy:
Instance
└── DNS
"""

from dataclasses import dataclass

from .instance import Instance


@dataclass
class DNS(Instance):
    """DNS server instance (Raspberry Pi running Pi-hole).

    Attributes:
        ipv4: IPv4 address
        ipv4_cidr: CIDR notation
        device_name: Network interface name
        name: Instance name template
        ansible_user: SSH user — 'pi' for Raspberry Pi OS Lite,
                      override via DNS_ANSIBLE_USER env var if needed.
    """
    name: str = 'jmpa-dns-{id}'
    # Raspberry Pi OS default user. Override with DNS_ANSIBLE_USER env var.
    ansible_user: str = 'pi'

    def to_dict(self) -> dict:
        """Convert to dictionary with 'dns' key instead of 'instance'."""
        base = self._base_dict()
        base['dns'] = base.pop('instance')
        return base
