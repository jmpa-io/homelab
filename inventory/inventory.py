from dataclasses import dataclass, field
from typing import Dict, Any
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
    host.bridge = deepcopy(host.bridge) # Ensure a unique bridge for a host.
    for attr in ("ipv4", "ipv4_with_cidr", "subnet", "subnet_with_cidr"):
      setattr(host.bridge, attr, getattr(host.bridge, attr).format(id=host_id))

    # Assign IPs to services, using bridge.
    host.services = deepcopy(host.services) # Ensure a unique list of services for a host.
    for s in host.services:
      s.ipv4 = f"{host.bridge.ipv4_prefix}.{host_id}.{s.container_id}"
      s.ipv4_cidr = host.bridge.ipv4_cidr
      s.ipv4_with_cidr = f"{s.ipv4}/{host.bridge.ipv4_cidr}"

    # Setup static_records for the 'nginx_reverse_proxy' service.
    proxy = next((s for s in host.services if s.is_proxy), None)
    if proxy:
      proxy.static_records = [
        {
          "subdomain": s.name,
          "forward_to_ipv4_with_port": f"{s.ipv4}:{s.default_port}"
        }
        for s in host.services
        if (
          not s.is_proxy
          and s.default_port
          and s.add_to_proxy_static_records
        )
      ]

    # Add host, using an ansible-appropriate name.
    self.hosts[host.name.replace("-", "_")] = host

    # Build or update the global service map.
    # NOTE: This must be run AFTER adding the host to the 'hosts' dictionary.
    self.build_global_service_map()

    # Increment internal host counter.
    self._next_id += 1

  def add_hosts(self, *hosts: Host):
    """ Adds multiple hosts to the inventory. """
    for host in hosts:
        self.add_host(host)

  def build_global_service_map(self):
    service_map = {}
    for host in self.hosts.values():
      for service in host.services:
        if not service.is_proxy:
          continue
        for record in service.static_records:
          service_map.setdefault(record['subdomain'], []).append(record['forward_to_ipv4_with_port'])
    self.vars['common']['global_service_map'] = service_map

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
