"""DNS server with zone management support.

Class Hierarchy:
Instance
└── DNS
"""

from dataclasses import dataclass, field
from typing import List, Dict
from copy import deepcopy

from .instance import Instance


@dataclass
class DNSZone:
    """DNS zone configuration.

    Attributes:
        name: Zone name (e.g., example.com)
        type: Zone type (master/slave)
        records: DNS records
        allow_transfer: IPs allowed to transfer
        also_notify: Secondary DNS servers
        forwarders: Upstream DNS servers
    """
    name: str  # e.g., "example.com"
    type: str = "master"  # master or slave
    records: List[Dict[str, str]] = field(default_factory=list)
    allow_transfer: List[str] = field(default_factory=list)
    also_notify: List[str] = field(default_factory=list)
    forwarders: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Deep copy lists to avoid sharing."""
        self.records = deepcopy(self.records)
        self.allow_transfer = deepcopy(self.allow_transfer)
        self.also_notify = deepcopy(self.also_notify)
        self.forwarders = deepcopy(self.forwarders)


@dataclass
class DNS(Instance):
    """DNS server instance.

    Attributes:
        name: Instance name (default: 'dns-{id}')
        zones: DNS zones to manage
        recursion: Allow recursive queries
        forwarders: Upstream DNS servers
        allow_query: Networks allowed to query
        allow_recursion: Networks allowed recursion
        )
    """
    name: str = field(default='dns-{id}')  # Changed from jmpa-dns-{id}
    zones: List[DNSZone] = field(default_factory=list)
    recursion: bool = True
    forwarders: List[str] = field(default_factory=lambda: ["1.1.1.1", "8.8.8.8"])
    allow_query: List[str] = field(default_factory=lambda: ["localhost", "localnets"])
    allow_recursion: List[str] = field(default_factory=lambda: ["localhost", "localnets"])

    def __post_init__(self):
        """Initialize DNS server.

        Calls parent initialization and deep copies all lists
        to avoid sharing between instances.
        """
        super().__post_init__()  # Initialize network and host services
        self.zones = deepcopy(self.zones)
        self.forwarders = deepcopy(self.forwarders)
        self.allow_query = deepcopy(self.allow_query)
        self.allow_recursion = deepcopy(self.allow_recursion)

    def to_dict(self) -> dict:
        """Convert DNS instance to dictionary with DNS-specific config."""
        base = self._base_dict()
        # Add DNS-specific configuration
        base['instance']['config'] = {
            'recursion': self.recursion,
            'forwarders': self.forwarders,
            'allow_query': self.allow_query,
            'allow_recursion': self.allow_recursion,
            'zones': [
                {
                    'name': zone.name,
                    'type': zone.type,
                    'records': zone.records,
                    'allow_transfer': zone.allow_transfer,
                    'also_notify': zone.also_notify,
                    'forwarders': zone.forwarders,
                }
                for zone in self.zones
            ]
        }
        # Rename 'instance' key to 'dns' for DNS-specific configuration
        base['dns'] = base.pop('instance')
        return base
