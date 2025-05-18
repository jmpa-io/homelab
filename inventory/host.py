from dataclasses import dataclass, field, asdict
from typing import List, Optional

from bridge import Bridge
from service import Service

@dataclass
class Host:
  ansible_host: str = field(init=False)
  ipv4: str
  ipv4_cidr: str
  ipv4_with_cidr: str = field(init=False)
  wifi_device_name: str
  bridge: Bridge
  name: Optional[str] = "jmpa-server-{id}"
  services: List[Service] = field(default_factory=list)

  def __post_init__(self):
    self.ansible_host = self.ipv4
    self.ipv4_with_cidr = f"{self.ipv4}/{self.ipv4_cidr}"

  def add_service(self, svc: Service) -> None:
    if svc.name not in {s.name for s in self.services}:
        self.services.append(svc)

  def to_dict(self):
    return asdict(self)
