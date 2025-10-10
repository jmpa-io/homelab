from dataclasses import dataclass, field
from typing import List

from .container_instance import ContainerInstance


@dataclass
class VPS(ContainerInstance):
  """Virtual Private Server instance."""
  name: str = field(default='jmpa-vps-{id}', init=True)

  def to_dict(self) -> dict:
    """Convert VPS instance to dictionary for Ansible consumption."""
    vps = {
      'name': self.name,
      'ipv4': self.ipv4,
      'ipv4_cidr': self.ipv4_cidr,
      'ipv4_with_cidr': self.ipv4_with_cidr,
      'wifi_device_name': self.wifi_device_name,
    }

    # Add host services.
    vps.update(self.get_host_services())

    # Add container services.
    services = self.get_container_services()

    return {
      'ansible_host': self.ansible_host,
      'vps': vps,
      'services': services,
    }
