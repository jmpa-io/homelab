from dataclasses import dataclass, field
from typing import List

from bridge import Bridge
from collector import Collector
from service import Service

@dataclass
class Host:

  # Proxmox.
  ansible_host: str = field(init=False)
  ipv4: str
  ipv4_cidr: str
  ipv4_with_cidr: str = field(init=False)
  wifi_device_name: str
  bridge: Bridge
  collector: Collector
  name: str = "jmpa-server-{id}"
  services: List[Service] = field(default_factory=list)

  # These values are populated when this host is added to an Inventory.
  k8s_masters: List[str] = field(default_factory=list)
  k8s_nodes: List[str] = field(default_factory=list)

  def __post_init__(self):
    self.ansible_host = self.ipv4
    self.ipv4_with_cidr = f"{self.ipv4}/{self.ipv4_cidr}"

  def to_dict(self) -> dict:
    """
    Returns the formatted dictionary output as per the new structure.
    """

    host = {
      "name": self.name,
      "ipv4": self.ipv4,
      "ipv4_cidr": self.ipv4_cidr,
      "ipv4_with_cidr": f"{self.ipv4}/{self.ipv4_cidr}",
      "wifi_device_name": self.wifi_device_name,
        "bridge": {
          "name": self.bridge.name,
          "ipv4": self.bridge.ipv4,
          "ipv4_cidr": self.bridge.ipv4_cidr,
          "ipv4_with_cidr": self.bridge.ipv4_with_cidr,
          "subnet": self.bridge.subnet,
          "default_ipv4_prefix": self.bridge.ipv4_prefix,
          "default_ipv4_suffix": self.bridge.ipv4_suffix,
        },
        "collector": {
          "metrics_port": self.collector.metrics_port,
        }
    }

    services = {
      s.name: {
        "container_id": s.container_id,
        **({"default_port": s.default_port} if s.default_port is not None else {}),
        "ipv4": s.ipv4,
        "ipv4_cidr": s.ipv4_cidr,
        "ipv4_with_cidr": s.ipv4_with_cidr,
        **({"static_records": s.static_records} if s.static_records else {})}
      for s in self.services
    }

    out = {
      "ansible_host": self.ansible_host,
      "host": host,
      "services": services,
    }

    if self.k8s_masters or self.k8s_nodes:
      out["k3s"] = {}
      if self.k8s_masters:
        out["k3s"]["masters"] = self.k8s_masters
      if self.k8s_nodes:
        out["k3s"]["nodes"] = self.k8s_nodes

    return out

