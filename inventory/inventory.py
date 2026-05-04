from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union
from copy import deepcopy

from instances.proxmox_host import ProxmoxHost
from instances.nas import NAS
from instances.vps import VPS
from instances.dns import DNS
from instances.ec2 import EC2
from k8s_inventory import K8sInventory


# Types that have a Proxmox bridge and can host LXC containers / k3s VMs.
_PROXMOX_TYPES = (ProxmoxHost, VPS)


@dataclass
class Inventory:
  # Instance config - can be ProxmoxHost, NAS, VPS, DNS, EC2, etc.
  instances: Dict[str, Union[ProxmoxHost, NAS, VPS, DNS, EC2]] = field(default_factory=dict)
  vars: Dict[str, Any] = field(default_factory=dict)

  # Kubernetes config.
  kube_inventory: Optional[K8sInventory] = None

  # Internal instance counter.
  _next_id_per_type: Dict[str, int] = field(default_factory=lambda: {
    'ProxmoxHost': 1,
    'VPS': 1,
    'NAS': 1,
    'DNS': 1,
    'EC2': 1,
  }, init=False, repr=False)

  def add_instance(self, instance: Union[ProxmoxHost, NAS, VPS, DNS, EC2]):
    """Adds a single instance to the inventory."""
    instance_type = type(instance).__name__
    instance_id = self._next_id_per_type[instance_type]

    # The bridge host_id determines which /24 subnet the host gets.
    # ProxmoxHosts use host_id 1, 2, 3 (their instance counter directly).
    # VPS nodes are offset by 3 so their subnets (10.0.4.x, 10.0.5.x...)
    # never collide with on-prem server subnets (10.0.1.x, 10.0.2.x, 10.0.3.x).
    if isinstance(instance, VPS):
      bridge_host_id = instance_id + 3
    else:
      bridge_host_id = instance_id

    # Setup name using the per-type counter (jmpa-vps-1, jmpa-vps-2 etc.).
    instance.name = instance.name.format(id=instance_id)

    # Bridge setup — both ProxmoxHost and VPS have a bridge.
    # Bridge IPs use bridge_host_id so subnets are always unique.
    if isinstance(instance, _PROXMOX_TYPES):
        instance.bridge = deepcopy(instance.bridge)
        for attr in ('ipv4', 'ipv4_with_cidr', 'subnet', 'subnet_with_cidr'):
            setattr(instance.bridge, attr, getattr(instance.bridge, attr).format(id=bridge_host_id))

    # LXC service IP assignment — both ProxmoxHost and VPS run LXC.
    if hasattr(instance, 'lxc_services') and instance.lxc_services:
        instance.lxc_services = deepcopy(instance.lxc_services)
        for s in instance.lxc_services:
            if isinstance(instance, _PROXMOX_TYPES):
                s.ipv4 = f'{instance.bridge.ipv4_prefix}.{bridge_host_id}.{s.container_id}'
                s.ipv4_cidr = instance.bridge.ipv4_cidr
                s.ipv4_with_cidr = f'{s.ipv4}/{instance.bridge.ipv4_cidr}'

    # Proxy static records — both ProxmoxHost and VPS run nginx_reverse_proxy.
    if isinstance(instance, _PROXMOX_TYPES) and hasattr(instance, 'lxc_services'):
        self._setup_proxy_static_records(instance)

    # Add instance, using an ansible-appropriate name.
    self.instances[instance.name.replace('-', '_')] = instance

    # Build or update the global service map.
    self.build_global_service_map()

    # Build or update the global k8s configuration.
    # Pass bridge_host_id so k3s IPs land on the correct subnet.
    self.build_global_kube_configuration()

    # Increment internal instance counter.
    self._next_id_per_type[instance_type] += 1


  def add_instances(self, *instances: Union[ProxmoxHost, NAS, VPS, DNS, EC2]):
    """Adds multiple instances to the inventory."""
    for instance in instances:
      self.add_instance(instance)

  def _setup_proxy_static_records(self, instance):
    """Setup static records for proxy services on a host instance."""
    proxy_services = [s for s in instance.lxc_services if self._is_proxy_service(s)]
    for proxy in proxy_services:
      proxy.static_records = [
        {
          'subdomain': s.name,
          'forward_to_ipv4_with_port': f'{s.ipv4}:{s.default_port}',
          'protocol': s.protocol.value,
        }
        for s in instance.lxc_services
        if (not self._is_proxy_service(s) and s.default_port and s.add_to_proxy_static_records and s.protocol)
      ]

  def _is_proxy_service(self, service):
    """Determine if a service should act as a reverse proxy."""
    return service.name == 'nginx_reverse_proxy'

  def build_global_service_map(self):
    """Builds a global service map from all proxy services' static records."""
    service_map = {}
    for instance in self.instances.values():
      if isinstance(instance, _PROXMOX_TYPES):
        proxy_services = [s for s in instance.lxc_services if self._is_proxy_service(s)]
        for proxy in proxy_services:
          self._add_proxy_records_to_service_map(proxy, service_map)
    self.vars['common']['global_service_map'] = service_map

  def _add_proxy_records_to_service_map(self, proxy_service, service_map):
    """Adds static records from a proxy service to the service map."""
    for record in proxy_service.static_records:
      service_entry = service_map.setdefault(record['subdomain'], {
        'backends': [],
        'protocol': record['protocol'],
      })
      service_entry['backends'].append(record['forward_to_ipv4_with_port'])

  def build_global_kube_configuration(self):
    if not self.kube_inventory:
      return

    for name, instance in self.instances.items():
      if isinstance(instance, _PROXMOX_TYPES):
        masters = []
        nodes = []
        # Derive the bridge host_id from the bridge IP (e.g. '10.0.4.1' → 4).
        # This is reliable regardless of the instance name numbering scheme —
        # VPS instances have name suffix '1' but bridge host_id '4'.
        bridge_host_id = int(instance.bridge.ipv4.split('.')[2])
        prefix = f'{instance.bridge.ipv4_prefix}.{bridge_host_id}'
        for j in range(self.kube_inventory.masters_per_host):
          ip_suffix = self.kube_inventory.masters_ips_start_range + j
          if ip_suffix > self.kube_inventory.masters_ips_end_range:
            break
          masters.append(f'{prefix}.{ip_suffix}')

        for j in range(self.kube_inventory.nodes_per_host):
          ip_suffix = self.kube_inventory.nodes_ips_start_range + j
          if ip_suffix > self.kube_inventory.nodes_ips_end_range:
            break
          nodes.append(f'{prefix}.{ip_suffix}')

        instance.k8s_masters = masters
        instance.k8s_nodes = nodes

  def to_dict(self):
    """
    Generates the Ansible dynamic inventory as a dictionary.
    """
    proxmox_instances = {name: inst for name, inst in self.instances.items() if isinstance(inst, ProxmoxHost)}
    vps_instances     = {name: inst for name, inst in self.instances.items() if isinstance(inst, VPS)}
    nas_instances     = {name: inst for name, inst in self.instances.items() if isinstance(inst, NAS)}
    dns_instances     = {name: inst for name, inst in self.instances.items() if isinstance(inst, DNS)}
    ec2_instances     = {name: inst for name, inst in self.instances.items() if isinstance(inst, EC2)}

    # All Proxmox-capable hosts (on-prem + VPS) — used by most playbooks.
    all_proxmox_capable = {**proxmox_instances, **vps_instances}

    # Build hostvars for all instances.
    hostvars = {name: inst.to_dict() for name, inst in self.instances.items()}

    out = {
        '_meta': {'hostvars': hostvars},
        'all': {
            'hosts': list(self.instances.keys()),
            'vars': self.vars
        },
        # proxmox_hosts includes BOTH on-prem ProxmoxHosts and VPS nodes
        # so that all existing LXC/VM/k3s playbooks work unchanged.
        'proxmox_hosts': {
            'hosts': list(all_proxmox_capable.keys())
        },
        # vps_hosts is the VPS-only subset — for VPS-specific plays
        # (e.g. provision-cloud-proxmox, Tailscale management).
        'vps_hosts': {
            'hosts': list(vps_instances.keys())
        },
        'nas': {
            'hosts': list(nas_instances.keys()),
            'vars': {
                'ansible_ssh_pass': self.vars.get('ansible_ssh_pass_fallback')
            }
        },
        'dns': {
            'hosts': list(dns_instances.keys())
        },
        'ec2_hosts': {
            'hosts': list(ec2_instances.keys())
        },
    }

    # Return early when there is no given kube_inventory.
    if not self.kube_inventory:
      return out

    # Collect k3s IPs from all Proxmox-capable hosts (on-prem + VPS).
    master_ips = []
    node_ips = []
    for instance in self.instances.values():
      if isinstance(instance, _PROXMOX_TYPES):
        master_ips.extend(instance.k8s_masters)
        node_ips.extend(instance.k8s_nodes)

    # Add k3s values to the default inventory.
    out['all']['vars']['common']['k3s'] = {
      'version': self.kube_inventory.version,
      'masters_ips_start_range': self.kube_inventory.masters_ips_start_range,
      'nodes_ips_start_range': self.kube_inventory.nodes_ips_start_range,
    }

    # Setup k3s inventory.
    out['k3s_cluster'] = {
      'vars': {
        'k3s_version': self.kube_inventory.version,
        'ansible_user': self.kube_inventory.ansible_user,
        'ansible_ssh_private_key_file': self.kube_inventory.ansible_ssh_private_key_file,
        'ansible_python_interpreter': self.kube_inventory.ansible_python_interpreter,
        'github': self.vars.get('github', {}),
        'k8s_services': self.vars.get('k8s_services', {}),
      },
      'children': {},
    }

    if master_ips:
      out['k3s_cluster']['vars']['api_endpoint'] = master_ips[0]

    if master_ips:
      out['k3s_cluster']['children']['k3s_masters'] = {
        'hosts': {ip: {} for ip in master_ips},
      }

    if node_ips:
      out['k3s_cluster']['children']['k3s_nodes'] = {
        'hosts': {ip: {} for ip in node_ips},
      }

    return out
