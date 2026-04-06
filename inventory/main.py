#!/usr/bin/env python3
import json

from ssm import SSMClient
from env import read_env_var

from instances import VPS, NAS, DNS
from instances.proxmox_host import ProxmoxHost, ProxmoxHostBridge
from service import LXCService, HostService, Protocol
from inventory import Inventory

from k8s_inventory import K8sInventory


def main():

  # Setup client for AWS SSM Parameter Store.
  ssm_client = SSMClient(read_env_var('AWS_REGION', None, True))

  # Setup inventory variables & config.
  common_subnet_ipv4 = ssm_client.get_parameter('/homelab/subnet')
  default_cidr = read_env_var('DEFAULT_CIDR', 24, False, int)
  inventory_vars = {
    # 'ansible_ssh_pass': ssm_client.get_parameter('/homelab/ssh-password'),  # Commented out - using SSH keys instead
    'ansible_become_pass': ssm_client.get_parameter('/homelab/root-password'),
    'ansible_python_interpreter': read_env_var('ANSIBLE_PYTHON_INTERPRETER', '/usr/bin/python3'),
    'common': {
      'internet_gateway': {
        "ipv4": ssm_client.get_parameter('/homelab/internet-gateway')
      },
      'subnet': {
        'ipv4': common_subnet_ipv4,
        'ipv4_cidr': default_cidr,
        'ipv4_with_cidr': f'{common_subnet_ipv4}/{default_cidr}',
      },
      'dns': {
        'domain': read_env_var('DOMAIN', 'jmpa.lab'),
      },
    },
    'proxmox': {
      'api_token': ssm_client.get_parameter('/homelab/proxmox/api-token'),
      'default_ui_port': read_env_var('PROXMOX_DEFAULT_UI_PORT', '8006'),
    },
    'tailscale': {
      'auth_key': ssm_client.get_parameter('/homelab/tailscale/auth-key'),
    },
    'ssl': {
      'private_key': ssm_client.get_parameter('/homelab/ssl/private-key'),
      'cert': ssm_client.get_parameter('/homelab/ssl/cert'),
    },
    'ssh': {
      'public_key': ssm_client.get_parameter('/homelab/ssh/public-key'),
    },
  }

  #
  # Setup services.
  #

  nginx_reverse_proxy = LXCService(
    name='nginx_reverse_proxy',
    container_id=read_env_var('NGINX_REVERSE_PROXY_CONTAINER_ID', '5'),
  )

  tailscale_gateway = LXCService(
    name='tailscale_gateway',
    container_id=read_env_var('TAILSCALE_GATEWAY_CONTAINER_ID', '15'),
  )

  prometheus = LXCService(
    name='prometheus',
    container_id=read_env_var('PROMETHEUS_CONTAINER_ID', '40'),
    default_port=read_env_var('PROMETHEUS_PORT', '9090'),
    protocol=Protocol.HTTP,
    add_to_proxy_static_records=False,
  )

  grafana = LXCService(
    name='grafana',
    container_id=read_env_var('GRAFANA_CONTAINER_ID', '45'),
    default_port=read_env_var('GRAFANA_PORT', '3000'),
    protocol=Protocol.HTTP,
  )

  #
  # Setup bridge.
  #

  bridge = ProxmoxHostBridge(
    name=read_env_var('HOST_BRIDGE_NAME', 'vmbr0'),
    ipv4_prefix=read_env_var('HOST_BRIDGE_IPV4_PREFIX', '10.0'),
    ipv4_suffix=read_env_var('HOST_BRIDGE_IPV4_SUFFIX', '1'),
    ipv4_cidr=default_cidr,
  )

  #
  # Setup host services.
  #
  collector = HostService(
    name='collector',
    metrics_port=read_env_var('HOST_OTELCOL_METRICS_PORT', '8889'),
  )
  dnsmasq_exporter = HostService(
    name='dnsmasq_exporter',
    metrics_port=read_env_var("HOST_DNSMASQ_EXPORTER_METRICS_PORT", '9153'),
  )

  #
  # Setup k3s config.
  #

  kube_inventory = K8sInventory(
    version=read_env_var('K3S_VERSION', 'v1.30.2+k3s1'),
    ansible_user=read_env_var('K3S_ANSIBLE_USER', 'debian'),
    ansible_ssh_private_key=inventory_vars['ssl']['private_key'],
    ansible_python_interpreter=inventory_vars['ansible_python_interpreter'],
    token=inventory_vars['proxmox']['api_token'],
    # Masters.
    masters_per_host=read_env_var('K3S_MASTERS_PER_HOST', 1, value_type=int),
    masters_ips_start_range=read_env_var('K3S_MASTERS_START_RANGE', 60, value_type=int),
    masters_ips_end_range=read_env_var('K3S_MASTERS_END_RANGE', 69, value_type=int),
    # Nodes.
    nodes_per_host=read_env_var('K3S_NODES_PER_HOST', 2, value_type=int),
    nodes_ips_start_range=read_env_var('K3S_NODES_START_RANGE', 70, value_type=int),
    nodes_ips_end_range=read_env_var('K3S_NODES_END_RANGE', 79, value_type=int),
  )

  #
  # Setup inventory.
  #

  inventory = Inventory(vars=inventory_vars, kube_inventory=kube_inventory)

  # Add Proxmox hosts.
  inventory.add_instances(
    ProxmoxHost(
      ipv4=ssm_client.get_parameter('/homelab/jmpa-server-1/ipv4-address'),
      ipv4_cidr=default_cidr,
      device_name=ssm_client.get_parameter('/homelab/jmpa-server-1/device-name'),
      bridge=bridge,
      host_services=[
        collector,
        dnsmasq_exporter,
      ],
      lxc_services=[
        nginx_reverse_proxy,
        tailscale_gateway,
        prometheus,
        grafana,
      ],
    ),
    ProxmoxHost(
      ipv4=ssm_client.get_parameter('/homelab/jmpa-server-2/ipv4-address'),
      ipv4_cidr=default_cidr,
      device_name=ssm_client.get_parameter('/homelab/jmpa-server-2/device-name'),
      bridge=bridge,
      host_services=[
        collector,
        dnsmasq_exporter,
      ],
      lxc_services=[
        nginx_reverse_proxy,
        tailscale_gateway,
        prometheus,
        grafana,
      ],
    ),
    ProxmoxHost(
      ipv4=ssm_client.get_parameter('/homelab/jmpa-server-3/ipv4-address'),
      ipv4_cidr=default_cidr,
      device_name=ssm_client.get_parameter('/homelab/jmpa-server-3/device-name'),
      bridge=bridge,
      host_services=[
        collector,
        dnsmasq_exporter,
      ],
      lxc_services=[
        nginx_reverse_proxy,
        tailscale_gateway,
        prometheus,
        grafana,
      ],
    ),
  )

  # Add NAS instance.
  inventory.add_instances(
    NAS(
      ipv4=ssm_client.get_parameter('/homelab/jmpa-nas-1/ipv4-address'),
      ipv4_cidr=default_cidr,
      device_name=ssm_client.get_parameter('/homelab/jmpa-nas-1/device-name'),
      ansible_port=read_env_var('NAS_SSH_PORT', '9222', value_type=int),
      host_services=[
        collector,
      ],
    )
  )

  # Add DNS instance.
  inventory.add_instances(
    DNS(
      ipv4=ssm_client.get_parameter('/homelab/jmpa-dns-1/ipv4-address'),
      ipv4_cidr=default_cidr,
      device_name=ssm_client.get_parameter('/homelab/jmpa-dns-1/device-name'),
      host_services=[
        collector,
      ],
    )
  )

  # Add VPS instance (example - uncomment when ready to use).
  # inventory.add_instances(
  #   VPS(
  #     ipv4=ssm_client.get_parameter('/homelab/jmpa-vps-1/ipv4-address'),
  #     ipv4_cidr=default_cidr,
  #     device_name=ssm_client.get_parameter('/homelab/jmpa-vps-1/device-name'),
  #     host_services=[
  #       collector,
  #     ],
  #   )
  # )

  # Print inventory as JSON.
  print(json.dumps(inventory.to_dict(), indent=2))


if __name__ == '__main__':
  main()
