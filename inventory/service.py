from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict
from enum import Enum

@dataclass
class Protocol(Enum):
  HTTP = "http"
  HTTPS = "https"

@dataclass
class Service:
  """Base class for all services."""
  name: str

  def to_dict(self) -> dict:
    return asdict(self)

@dataclass
class HostService(Service):
  """Service running directly on the host (e.g., collectors/exporters)."""
  metrics_port: str

@dataclass
class LXCService(Service):
  """Service running in an LXC container."""
  container_id: int
  default_port: str = ''
  protocol: Protocol = field(default_factory=lambda: Protocol.HTTP)
  add_to_proxy_static_records: bool = True

  # These values are populated when this Service is added to an Inventory.
  ipv4: str = field(init=False, default='')  # eg. '10.0.1.1'
  ipv4_cidr: str = field(init=False, default='')  # eg. '24'
  ipv4_with_cidr: str = field(init=False, default='')  # eg. '10.0.1.1/24'

  # Static records for proxy services - populated by inventory logic
  static_records: List[Dict[str, str]] = field(default_factory=list, init=False)

