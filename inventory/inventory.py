from dataclasses import dataclass, field
from typing import Dict, List, Any
from copy import deepcopy

from host import Host

@dataclass
class Inventory:
  hosts: Dict[str, Host] = field(default_factory=dict)
  vars: Dict[str, Any] = field(default_factory=dict)

  # Internal host counter.
  _next_id: int = field(default=1, init=False, repr=False)

  def add_host(self, host: Host):
    """ Adds a single host to the inventory. """
    host_id = self._next_id

    # Setup name of host.
    host.name = host.name.format(id=host_id)

    # Setup bridge.
    host.bridge = deepcopy(host.bridge) # Clone bridge to ensure each host has its own instance.
    host.bridge.ipv4             = host.bridge.ipv4.format(id=host_id)
    host.bridge.ipv4_with_cidr   = host.bridge.ipv4_with_cidr.format(id=host_id)
    host.bridge.subnet           = host.bridge.subnet.format(id=host_id)
    host.bridge.subnet_with_cidr = host.bridge.subnet_with_cidr.format(id=host_id)

    # Assign IPs to services, using bridge.
    host.services = deepcopy(host.services)
    for s in host.services:
      s.ipv4 = f"{host.bridge.ipv4_prefix}.{host_id}.{s.container_id}"
      s.ipv4_cidr = host.bridge.ipv4_cidr
      s.ipv4_with_cidr = f"{s.ipv4}/{host.bridge.ipv4_cidr}"

    # Setup static_records for the nginx-reverse-proxy service.
    proxy = None
    static_records: List[Dict[str,str]] = []
    for s in host.services:
      if s.name == "nginx-reverse-proxy":
        proxy = s
      else:
        if s.default_port is None:
          continue

        static_records.append({
          "subdomain": s.name,
          "forward_to_ipv4_with_port": f"{s.ipv4}:{s.default_port}"
        })

    if proxy:
      proxy.static_records = static_records

    # Add host, using an ansible-appropriate name.
    self.hosts[host.name.replace("-", "_")] = host

    # Increment internal host counter.
    self._next_id += 1

  def add_hosts(self, *hosts: Host):
    """ Adds multiple hosts to the inventory. """
    for host in hosts:
        self.add_host(host)

  def to_dict(self):
    return {
      "_meta": {
        "hostvars": {name: h.to_dict() for name, h in self.hosts.items()},
      },
      "all": {
        "vars": self.vars,
        "hosts": list(self.hosts.keys()),
      },
    }
