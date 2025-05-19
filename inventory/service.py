from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

@dataclass
class Service:
  name: str
  container_id: int
  default_port: Optional[str] = None

  # These values are populated when this service is added to an inventory.
  ipv4: str = field(init=False, default="")             # eg. '10.0.1.1'
  ipv4_cidr: str = field(init=False, default="")        # eg. '24'
  ipv4_with_cidr: str = field(init=False, default="")   # eg. '10.0.1.1/24'

  # NOTE: This section is specific 'nginx-reverse-proxy' and is populated when
  # this service is add to an inventory.
  static_records: List[Dict[str, str]] = field(default_factory=list)

  def to_dict(self) -> dict:
    return asdict(self)
