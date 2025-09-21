from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from enum import Enum

@dataclass
class Protocol(Enum):
  HTTP = "http"
  HTTPS = "https"

@dataclass
class Service:
  name: str
  container_id: int
  default_port: Optional[str] = None
  protocol: Optional[Protocol] = None
  add_to_proxy_static_records: bool = True

  # These values are populated when this Service is added to an Inventory.
  ipv4: str = field(init=False, default='')  # eg. '10.0.1.1'
  ipv4_cidr: str = field(init=False, default='')  # eg. '24'
  ipv4_with_cidr: str = field(init=False, default='')  # eg. '10.0.1.1/24'

  # NOTE: this section below is specific to the 'nginx_reverse_proxy' service.
  @property
  def is_proxy(self) -> bool:
    return self.name == 'nginx_reverse_proxy'

  # - The 'static_records' variable is populated when this Service is added to an Inventory.
  static_records: List[Dict[str, str]] = field(default_factory=list)

  # ---

  def to_dict(self) -> dict:
    return asdict(self)
