from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from copy import deepcopy

from host import Host
from k8s import KubeConfig

@dataclass
class Inventory:

  # Proxmox host config.
  hosts: Dict[str, Host] = field(default_factory=dict)
  vars: Dict[str, Any] = field(default_factory=dict)

  # Kubernetes config.
  kubeconfig: Optional[KubeConfig] = None

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

    # Build or update the global k8s configuration.
    # NOTE: This must be run AFTER adding the host to the 'hosts' dictionary.
    self.build_global_kube_configuration()

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

  def build_global_kube_configuration(self):
    if not self.kubeconfig:
        return

    for i, (name, host) in enumerate(self.hosts.items(), start=1):
      masters = []; nodes = []
      prefix = f"{host.bridge.ipv4_prefix}.{i}"
      for j in range(self.kubeconfig.masters_per_host):
        id = self.kubeconfig.masters_ips_start_range + j
        if id > self.kubeconfig.masters_ips_end_range:
          break
        masters.append(f"{prefix}.{id}")

      for j in range(self.kubeconfig.nodes_per_host):
        id = self.kubeconfig.nodes_ips_start_range + j
        if id > self.kubeconfig.nodes_ips_end_range:
          break
        nodes.append(f"{prefix}.{id}")

      host.k8s_masters = masters
      host.k8s_nodes = nodes


  def _get_k8s_host_entry(self, host_obj: Host) -> Dict[str, Any]:
      """Helper to create a standard K8s host entry dictionary from a Host object."""
      return {
          "ansible_user": "debian",
          "ansible_ssh_private_key_file": "~/.ssh/id_ed25519"
      }


  def to_dict(self):
    out = {
      "_meta": {
        "hostvars": {name: h.to_dict() for name, h in self.hosts.items()},
      },
      "all": {
        "vars": self.vars,
        "hosts": list(self.hosts.keys()),
      },
    }

    # Add k8s config, only if more than one master or node is given.
    if self.kubeconfig:
      # out["all"]["vars"]["common"]["k3s"] = {
      #   "masters_ips_start_range": self.kubeconfig.masters_ips_start_range,
      #   "nodes_ips_start_range": self.kubeconfig.nodes_ips_start_range,
      # }
      #
      # out["k3s_cluster"] = {
      #   "vars": {
      #     "k3s_version": self.kubeconfig.version,
      #   },
      #   "children": {},
      # }
      #
      # all_masters = [ip for h in self.hosts.values() for ip in h.k8s_masters]
      # if all_masters:
      #   out["k3s_cluster"]["children"]["server"] = {
      #     "hosts": all_masters,
      #   }
      #
      # all_nodes = [ip for h in self.hosts.values() for ip in h.k8s_nodes]
      # if all_nodes:
      #   out["k3s_cluster"]["children"]["agent"] = {
      #     "hosts": all_nodes,
      #   }

      out["all"]["vars"].setdefault("common", {})["k3s"] = {
          "masters_ips_start_range": self.kubeconfig.masters_ips_start_range,
          "nodes_ips_start_range": self.kubeconfig.nodes_ips_start_range,
      }

      k3s_cluster_dict = {
          "vars": {
              "k3s_version": self.kubeconfig.version,
              "ansible_user": "debian",
              "ansible_ssh_private_key_file": "~/.ssh/id_ed25519",
              "ansible_python_interpreter": "/usr/bin/python3.11",
          },
          "children": {},
      }

      server_hosts_dict = {}
      for host_name, host_obj in self.hosts.items(): # Iterate over hosts to get the object
          for ip in host_obj.k8s_masters:
              server_hosts_dict[ip] = {
                "api_endpoint": host_obj.ansible_host,
              }

      if server_hosts_dict:
          k3s_cluster_dict["children"]["server"] = {
              "hosts": server_hosts_dict,
          }

      agent_hosts_dict = {}
      for host_name, host_obj in self.hosts.items(): # Iterate over hosts to get the object
          for ip in host_obj.k8s_nodes:
              agent_hosts_dict[ip] = {
                "api_endpoint": host_obj.ansible_host,
              }

      if agent_hosts_dict:
          k3s_cluster_dict["children"]["agent"] = {
              "hosts": agent_hosts_dict,
          }

      out["k3s_cluster"] = k3s_cluster_dict

    return out



