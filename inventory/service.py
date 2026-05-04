from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any


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
  # Populated by Inventory._setup_proxy_static_records() for the nginx service.
  # Schema: [{subdomain, forward_to_ipv4_with_port, protocol}, ...]
  # Left empty here — the schema used by the proxy differs from per-service
  # metadata, so we do not initialise it with a conflicting shape.
  static_records: List[Dict[str, Any]] = field(default_factory=list, init=False)

  def to_dict(self) -> Dict[str, Any]:
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

  Community scripts always run on proxmox_hosts[0] (host 1), so their IPs
  are always in the 10.0.1.x subnet. IPs are assigned explicitly from the
  dedicated community-scripts range (10.0.1.100–10.0.1.199) to avoid
  collisions with Ansible-managed LXC services (10.0.1.1–10.0.1.79) and
  k3s VMs (10.0.1.60–10.0.1.79).

  The ipv4 field MUST be explicitly set — there is no automatic derivation
  from vmid (the old formula caused multiple critical IP collisions).
  """
  vmid: int
  hostname: str
  ipv4: str          # Explicit IP — must be in 10.0.1.100-10.0.1.199
  bridge: str = 'vmbr0'
  port: str = ''
  protocol: Protocol = field(default_factory=lambda: Protocol.HTTP)
  add_to_dns: bool = True

  def __post_init__(self):
    """Validate the explicitly-set IP is in the correct reserved range."""
    try:
      last_octet = int(self.ipv4.split('.')[-1])
    except (ValueError, IndexError):
      raise ValueError(f"CommunityScriptService '{self.name}': invalid ipv4 '{self.ipv4}'")
    if not (100 <= last_octet <= 199):
      raise ValueError(
        f"CommunityScriptService '{self.name}': IP {self.ipv4} last octet {last_octet} "
        f"is outside the reserved community-scripts range (.100–.199). "
        f"Use 10.0.1.100–10.0.1.199 to avoid collisions with LXC (.1–.79) "
        f"and k3s VMs (.60–.79)."
      )

  def to_dns_record(self, domain: str = 'jmpa.lab') -> Dict[str, str]:
    """Generate DNS record for Pi-hole custom.list format."""
    return {
      'ip': self.ipv4,
      'hostname': f'{self.hostname}.{domain}',
      'short_hostname': self.hostname,
    }
