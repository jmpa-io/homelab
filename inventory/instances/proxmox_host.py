"""Proxmox server with network bridging and K8s support.

Class Hierarchy:
Instance
└── ContainerInstance
    └── ProxmoxHost
"""

from dataclasses import dataclass, field
from typing import List
from copy import deepcopy

from .container_instance import ContainerInstance
from service import Service


@dataclass
class ProxmoxHostBridge:
    """Network bridge configuration for Proxmox hosts.

    Attributes:
        name: Bridge name (e.g., 'vmbr0')
        ipv4_prefix: First octets (e.g., '10.0')
        ipv4_suffix: Last octet (e.g., '1')
        ipv4_cidr: CIDR notation (e.g., '24')
        ipv4: Bridge IP with {id}
        ipv4_with_cidr: CIDR with {id}
        subnet: Network with {id}
        subnet_with_cidr: Subnet with {id}
    """
    name: str  # eg. 'vmbr0'
    ipv4_prefix: str  # eg. '10.0'
    ipv4_suffix: str  # eg. '1'
    ipv4: str = field(init=False)  # eg. '10.0.1.1'
    ipv4_cidr: str  # eg. '24'
    ipv4_with_cidr: str = field(init=False)  # eg. '10.0.1.1/24'
    subnet: str = field(init=False)  # eg. '10.0.1.0'
    subnet_with_cidr: str = field(init=False)  # eg. '10.0.1.0/24'

    def __post_init__(self):
        """Set up bridge network with {id} placeholders."""
        self.ipv4 = f'{self.ipv4_prefix}.{{id}}.{self.ipv4_suffix}'
        self.ipv4_with_cidr = f'{self.ipv4}/{self.ipv4_cidr}'
        self.subnet = f'{self.ipv4_prefix}.{{id}}.0'
        self.subnet_with_cidr = f'{self.subnet}/{self.ipv4_cidr}'


@dataclass
class ProxmoxHost(ContainerInstance):
    """Proxmox server with LXC and K8s support.

    Attributes:
        ipv4: IPv4 address
        ipv4_cidr: CIDR notation
        device_name: Network interface name
        name: Instance name template
        bridge: Network bridge config
        lxc_services: LXC container services
        k8s_masters: K8s master node IPs
        k8s_nodes: K8s worker node IPs
    """
    bridge: ProxmoxHostBridge
    name: str = 'jmpa-server-{id}'
    lxc_services: List[Service] = field(default_factory=list)
    k8s_masters: List[str] = field(default_factory=list)
    k8s_nodes: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize Proxmox host.

        Calls parent initialization and deep copies bridge configuration
        to avoid sharing between instances.
        """
        super().__post_init__()  # Initialize network, host services, and container services
        self.bridge = deepcopy(self.bridge)  # Ensure unique bridge per host
        self.k8s_masters = deepcopy(self.k8s_masters)  # Ensure unique lists
        self.k8s_nodes = deepcopy(self.k8s_nodes)

    def to_dict(self) -> dict:
        """Convert Proxmox host instance to dictionary.

        Extends the ContainerInstance dictionary with Proxmox-specific
        configuration including bridge details and Kubernetes nodes.

        Returns:
            dict: Full host configuration for Ansible inventory
                {
                    'ansible_host': '192.168.1.10',
                    'host': {
                        'name': 'server-1',
                        'ipv4': '192.168.1.10',
                        'bridge': {
                            'name': 'vmbr0',
                            'ipv4': '10.0.1.1',
                            ...
                        },
                        ...
                    },
                    'services': { ... },
                    'k3s': {
                        'masters': [...],
                        'nodes': [...]
                    }
                }
        """
        base = super().to_dict()

        # Add bridge configuration
        base['instance']['bridge'] = {
            'name': self.bridge.name,
            'ipv4': self.bridge.ipv4,
            'ipv4_cidr': self.bridge.ipv4_cidr,
            'ipv4_with_cidr': self.bridge.ipv4_with_cidr,
            'subnet': self.bridge.subnet,
            'default_ipv4_prefix': self.bridge.ipv4_prefix,
            'default_ipv4_suffix': self.bridge.ipv4_suffix,
        }

        # Add k3s configuration if present
        if self.k8s_masters or self.k8s_nodes:
            k3s_dict = {}
            if self.k8s_masters:
                k3s_dict['masters'] = self.k8s_masters
            if self.k8s_nodes:
                k3s_dict['nodes'] = self.k8s_nodes
            base['k3s'] = k3s_dict

        # Rename 'instance' key to 'host' for host-specific configuration
        base['host'] = base.pop('instance')
        return base
