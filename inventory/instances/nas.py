from dataclasses import dataclass, field
from typing import List

from .instance import Instance


@dataclass
class NAS(Instance):
  """Network Attached Storage instance."""
  name: str = field(default='jmpa-nas-{id}', init=True)

  def to_dict(self) -> dict:
    """Convert NAS instance to dictionary for Ansible consumption."""
    nas = {
      'name': self.name,
      'ipv4': self.ipv4,
      'ipv4_cidr': self.ipv4_cidr,
      'ipv4_with_cidr': self.ipv4_with_cidr,
      'wifi_device_name': self.wifi_device_name,
    }

    # Add host services
    nas.update(self.get_host_services())

    return {
      'ansible_host': self.ansible_host,
      'nas': nas,
    }
