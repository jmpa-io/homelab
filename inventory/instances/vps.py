from dataclasses import dataclass
from .container_instance import ContainerInstance


@dataclass
class VPS(ContainerInstance):
  """Virtual Private Server instance."""

  name: str = 'jmpa-vps-{id}'
  # Generic VPS default — most Debian/Ubuntu cloud images use 'debian' or
  # 'ubuntu'. Override via ansible_user= when constructing in main.py.
  ansible_user: str = 'debian'

  def to_dict(self) -> dict:
    """Convert VPS instance to dictionary for Ansible consumption."""
    base = self._base_dict()
    vps_data = base.pop('instance')
    base['vps'] = vps_data
    # Include container services (LXC services running on this VPS).
    base['services'] = self.get_container_services()
    return base
