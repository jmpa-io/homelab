from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict


class Protocol(Enum):
  HTTP = 'http'
  HTTPS = 'https'
  SSH = 'ssh'


@dataclass
class Service:
  """Base service class."""
  name: str


@dataclass
class HostService(Service):
  """Service running directly on a host (not in a container)."""
  metrics_port: str = ''

  def to_dict(self) -> Dict[str, str]:
    """Convert service to dictionary for Ansible inventory."""
    return {
      'name': self.name,
      'metrics_port': self.metrics_port,
    }


@dataclass
class LXCService(Service):
  """Service running in an LXC container."""
  container_id: int
  default_port: str = ''
  protocol: Protocol = field(default_factory=lambda: Protocol.HTTP)
  add_to_proxy_static_records: bool = True
  # Set by Inventory.add_instance() after bridge assignment.
  ipv4: str = field(init=False, default='')
  ipv4_cidr: str = field(init=False, default='')
  ipv4_with_cidr: str = field(init=False, default='')
  static_records: List[Dict[str, str]] = field(default_factory=list, init=False)

  def __post_init__(self):
    self.static_records = [
      {
        'name': self.name,
        'port': self.default_port,
        'protocol': self.protocol.value,
      }
    ]

  def to_dict(self) -> Dict[str, any]:
    """Convert service to dictionary for Ansible inventory."""
    return {
      'name': self.name,
      'container_id': self.container_id,
      'default_port': self.default_port,
      'protocol': self.protocol.value,
      'add_to_proxy_static_records': self.add_to_proxy_static_records,
      'ipv4': self.ipv4,
      'ipv4_cidr': self.ipv4_cidr,
      'ipv4_with_cidr': self.ipv4_with_cidr,
      'static_records': self.static_records,
    }


@dataclass
class CommunityScriptService(Service):
  """Service deployed via Proxmox VE Community Script.

  These services are LXC containers deployed using community scripts.
  Their IPs are automatically calculated from VMID and bridge.
  """
  vmid: int
  hostname: str
  bridge: str = 'vmbr0'
  port: str = ''
  protocol: Protocol = field(default_factory=lambda: Protocol.HTTP)
  add_to_dns: bool = True
  ipv4: str = field(init=False, default='')

  def __post_init__(self):
    """Calculate IP address from VMID and bridge."""
    # Validate VMID range to prevent IP collisions
    if self.vmid > 999:
      raise ValueError(
        f"VMID {self.vmid} exceeds maximum of 999. "
        f"VMIDs above 999 cause IP address collisions in the last octet."
      )

    # Extract bridge number (e.g., 'vmbr0' -> 0)
    bridge_num = int(self.bridge.replace('vmbr', ''))
    # Calculate third octet (bridge_num + 1)
    third_octet = bridge_num + 1
    # Get last 2 digits of VMID for fourth octet
    fourth_octet = str(self.vmid)[-2:].zfill(2)
    # Build IP: 10.0.{third_octet}.{fourth_octet}
    self.ipv4 = f'10.0.{third_octet}.{fourth_octet}'

  def to_dns_record(self, domain: str = 'jmpa.lab') -> Dict[str, str]:
    """Generate DNS record for Pi-hole custom.list format.

    Returns:
      Dict with 'ip' and 'hostname' keys for DNS record.
    """
    return {
      'ip': self.ipv4,
      'hostname': f'{self.hostname}.{domain}',
      'short_hostname': self.hostname,
    }
