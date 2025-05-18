from dataclasses import dataclass, field
from typing import Dict
from copy import deepcopy

from host import Host

@dataclass
class Inventory:
  hosts: Dict[str, Host] = field(default_factory=dict)

  # Internal host counter.
  _next_id: int = field(default=1, init=False, repr=False)

  def add_host(self, host: Host):
    """ Adds a single host to the inventory. """

    # Clone bridge to ensure each host has its own instance.
    host.bridge = deepcopy(host.bridge)

    # Add the id of the host to specific values.
    host.name                    = host.name.format(id=self._next_id)
    host.bridge.ipv4             = host.bridge.ipv4.format(id=self._next_id)
    host.bridge.ipv4_with_cidr   = host.bridge.ipv4_with_cidr.format(id=self._next_id)
    host.bridge.subnet           = host.bridge.subnet.format(id=self._next_id)
    host.bridge.subnet_with_cidr = host.bridge.subnet_with_cidr.format(id=self._next_id)

    # Add host under an 'Ansible appropriate' name.
    self.hosts[host.name.replace("-", "_")] = host

    # Increment internal host counter.
    self._next_id += 1

  def add_hosts(self, *hosts: Host):
    """ Adds multiple hosts to the inventory. """
    for host in hosts:
        self.add_host(host)

  def to_dict(self):
    return {
      "hosts": {name: h.to_dict() for name, h in self.hosts.items()}
    }
