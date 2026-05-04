"""VPS instance type — a cloud KVM VPS running Proxmox VE.

A VPS is treated as a first-class fleet member identical to an on-prem
ProxmoxHost. It gets its own bridge subnet (10.0.{host_id}.x), runs the
same LXC services, and is connected to the on-prem cluster via Tailscale.

The public IP (eth0) is used for SSH/Tailscale. The bridge (vmbr0) creates
an internal subnet for LXC containers, exactly like on-prem nodes.

Class Hierarchy:
Instance
└── ContainerInstance
    └── VPS
"""

from dataclasses import dataclass, field
from typing import List
from copy import deepcopy

from .container_instance import ContainerInstance
from .proxmox_host import ProxmoxHostBridge
from service import Service


@dataclass
class VPS(ContainerInstance):
  """Cloud VPS running Proxmox VE.

  Treated identically to a ProxmoxHost in the inventory — same bridge
  subnet scheme, same LXC service support, same Ansible group membership.
  Connected to the on-prem homelab via Tailscale.

  Naming: jmpa-vps-{id} (e.g. jmpa-vps-1)
  Subnet: 10.0.{host_id}.x — host_id is auto-assigned by inventory
          starting at 4 (after the 3 on-prem ProxmoxHosts).
  """
  bridge: ProxmoxHostBridge = field(default_factory=lambda: ProxmoxHostBridge(
    name='vmbr0',
    ipv4_prefix='10.0',
    ipv4_suffix='1',
    ipv4_cidr='24',
  ))
  name: str = 'jmpa-vps-{id}'
  # Cloud provider / datacenter name for documentation purposes.
  provider: str = 'hetzner'
  k8s_masters: List[str] = field(default_factory=list)
  k8s_nodes: List[str] = field(default_factory=list)

  def __post_init__(self):
    """Initialise VPS — deep copy bridge so each VPS has its own instance."""
    super().__post_init__()
    self.bridge = deepcopy(self.bridge)
    self.k8s_masters = deepcopy(self.k8s_masters)
    self.k8s_nodes = deepcopy(self.k8s_nodes)

  def to_dict(self) -> dict:
    """Convert VPS instance to dictionary for Ansible consumption.

    Returns a structure identical to ProxmoxHost.to_dict() so playbooks
    can treat VPS and ProxmoxHost hosts interchangeably.
    """
    base = self._base_dict()

    # Add bridge configuration — identical schema to ProxmoxHost.
    base['instance']['bridge'] = {
      'name': self.bridge.name,
      'ipv4': self.bridge.ipv4,
      'ipv4_cidr': self.bridge.ipv4_cidr,
      'ipv4_with_cidr': self.bridge.ipv4_with_cidr,
      'subnet': self.bridge.subnet,
      'subnet_with_cidr': self.bridge.subnet_with_cidr,
      'default_ipv4_prefix': self.bridge.ipv4_prefix,
      'default_ipv4_suffix': self.bridge.ipv4_suffix,
    }

    # Add provider metadata.
    base['instance']['provider'] = self.provider

    # Add k3s configuration if present.
    if self.k8s_masters or self.k8s_nodes:
      k3s_dict = {}
      if self.k8s_masters:
        k3s_dict['masters'] = self.k8s_masters
      if self.k8s_nodes:
        k3s_dict['nodes'] = self.k8s_nodes
      base['k3s'] = k3s_dict

    # LXC services.
    base['services'] = self.get_container_services()

    # Rename 'instance' key to 'host' — same as ProxmoxHost so playbooks
    # reference {{ host.bridge }}, {{ host.ipv4 }} etc. consistently.
    base['host'] = base.pop('instance')
    return base
