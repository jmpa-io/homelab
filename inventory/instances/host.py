from dataclasses import dataclass, field
from typing import List

from .container_instance import ContainerInstance

@dataclass
class HostBridge:
  name: str  # eg. 'vmbr0'
  ipv4_prefix: str  # eg. '10.0'
  ipv4_suffix: str  # eg. '1'
  ipv4: str = field(init=False)  # eg. '10.0.1.1'
  ipv4_cidr: str  # eg. '24'
  ipv4_with_cidr: str = field(init=False)  # eg. '10.0.1.1/24'
  subnet: str = field(init=False)  # eg. '10.0.1.0'
  subnet_with_cidr: str = field(init=False)  # eg. '10.0.1.0/24'

  def __post_init__(self):
    # PLEASE NOTE:
    # The '{{id}' here is a placeholder for the id of the host, like the '1'
    # found in 'jmpa-server-1'. This value is populated when this Bridge is
    # added to a Host, and that Host is added to an Inventory.

    self.ipv4 = f'{self.ipv4_prefix}.{{id}}.{self.ipv4_suffix}'
    self.ipv4_with_cidr = f'{self.ipv4}/{self.ipv4_cidr}'
    self.subnet = f'{self.ipv4_prefix}.{{id}}.0'
    self.subnet_with_cidr = f'{self.subnet}/{self.ipv4_cidr}'

@dataclass
class Host(ContainerInstance):
  """Proxmox host instance."""
  bridge: HostBridge
  name: str = field(default='jmpa-server-{id}', init=True)

  # These values are populated when this host is added to an Inventory.
  k8s_masters: List[str] = field(default_factory=list)
  k8s_nodes: List[str] = field(default_factory=list)

  def to_dict(self) -> dict:
    """
    Returns the formatted dictionary output as per the new structure.
    """
    host = {
      'name': self.name,
      'ipv4': self.ipv4,
      'ipv4_cidr': self.ipv4_cidr,
      'ipv4_with_cidr': self.ipv4_with_cidr,
      'wifi_device_name': self.wifi_device_name,
      'bridge': {
        'name': self.bridge.name,
        'ipv4': self.bridge.ipv4,
        'ipv4_cidr': self.bridge.ipv4_cidr,
        'ipv4_with_cidr': self.bridge.ipv4_with_cidr,
        'subnet': self.bridge.subnet,
        'default_ipv4_prefix': self.bridge.ipv4_prefix,
        'default_ipv4_suffix': self.bridge.ipv4_suffix,
      },
    }

    # Add host services
    host.update(self.get_host_services())

    # Add container services
    services = self.get_container_services()

    out = {
      'ansible_host': self.ansible_host,
      'host': host,
      'services': services,
    }
    if self.k8s_masters or self.k8s_nodes:
      k3s_dict: dict[str, list[str]] = {}
      if self.k8s_masters:
        k3s_dict['masters'] = self.k8s_masters
      if self.k8s_nodes:
        k3s_dict['nodes'] = self.k8s_nodes
      out['k3s'] = k3s_dict
    return out
