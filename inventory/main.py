#!/usr/bin/env python3
import json

from ssm import SSMClient
from env import read_env_var

from instances import VPS, NAS, DNS, EC2
from instances.proxmox_host import ProxmoxHost, ProxmoxHostBridge
from service import LXCService, HostService, Protocol, CommunityScriptService
from inventory import Inventory

from k8s_inventory import K8sInventory
from k8s_services import (
  MediaSuite, K8sServices, ObservabilityConfig,
  ArgoCDConfig, KubernetesDashboardConfig, MetalLBConfig,
  NFSStorageConfig, GitHubRunnerConfig,
)
from homepage_config import HomepageConfig


def main():

  # Setup client for AWS SSM Parameter Store.
  ssm_client = SSMClient(read_env_var('AWS_REGION', None, True))

  # Setup inventory variables & config.
  common_subnet_ipv4  = ssm_client.require_parameter('/homelab/subnet')
  default_cidr        = read_env_var('DEFAULT_CIDR', '24')  # Keep as str — Instance.ipv4_cidr is typed str
  domain              = read_env_var('DOMAIN', 'jmpa.lab')

  # Fetch shared secrets once — reused in both inventory_vars and k8s_services.
  ssh_password        = ssm_client.require_parameter('/homelab/ssh-password')
  github_token        = ssm_client.require_parameter('/homelab/github/token')
  grafana_admin_pass  = ssm_client.require_parameter('/homelab/grafana/admin-password')

  inventory_vars = {
    'ansible_become_pass': ssh_password,
    'ansible_python_interpreter': read_env_var('ANSIBLE_PYTHON_INTERPRETER', '/usr/bin/python3'),
    # Fallback password for hosts that don't support SSH keys (e.g. NAS).
    'ansible_ssh_pass_fallback': ssh_password,
    'common': {
      'internet_gateway': {
        'ipv4': ssm_client.require_parameter('/homelab/internet-gateway'),
      },
      'subnet': {
        'ipv4': common_subnet_ipv4,
        'ipv4_cidr': default_cidr,
        'ipv4_with_cidr': f'{common_subnet_ipv4}/{default_cidr}',
      },
      'dns': {
        'domain': domain,
      },
    },
    'proxmox': {
      'api_token': ssm_client.require_parameter('/homelab/proxmox/api-token'),
      'default_ui_port': read_env_var('PROXMOX_DEFAULT_UI_PORT', '8006'),
    },
    'tailscale': {
      'auth_key': ssm_client.require_parameter('/homelab/tailscale/auth-key'),
    },
    'ssl': {
      'private_key': ssm_client.require_parameter('/homelab/ssl/private-key'),
      'cert': ssm_client.require_parameter('/homelab/ssl/cert'),
    },
    'ssh': {
      'public_key': ssm_client.require_parameter('/homelab/ssh/public-key'),
      'private_key': ssm_client.require_parameter('/homelab/ssh/private-key'),
    },
    'github': {
      'token': github_token,
    },
  }

  #
  # Setup LXC services.
  #

  nginx_reverse_proxy = LXCService(
    name='nginx_reverse_proxy',
    container_id=read_env_var('NGINX_REVERSE_PROXY_CONTAINER_ID', 5, value_type=int),
  )

  tailscale_gateway = LXCService(
    name='tailscale_gateway',
    container_id=read_env_var('TAILSCALE_GATEWAY_CONTAINER_ID', 15, value_type=int),
  )

  prometheus = LXCService(
    name='prometheus',
    container_id=read_env_var('PROMETHEUS_CONTAINER_ID', 40, value_type=int),
    default_port=read_env_var('PROMETHEUS_PORT', '9090'),
    protocol=Protocol.HTTP,
    add_to_proxy_static_records=False,
  )

  grafana = LXCService(
    name='grafana',
    container_id=read_env_var('GRAFANA_CONTAINER_ID', 45, value_type=int),
    default_port=read_env_var('GRAFANA_PORT', '3000'),
    protocol=Protocol.HTTP,
  )

  loki = LXCService(
    name='loki',
    container_id=read_env_var('LOKI_CONTAINER_ID', 50, value_type=int),
    default_port=read_env_var('LOKI_PORT', '3100'),
    protocol=Protocol.HTTP,
    add_to_proxy_static_records=False,
  )

  tempo = LXCService(
    name='tempo',
    container_id=read_env_var('TEMPO_CONTAINER_ID', 55, value_type=int),
    default_port=read_env_var('TEMPO_PORT', '3200'),
    protocol=Protocol.HTTP,
    add_to_proxy_static_records=False,
  )

  #
  # Setup community script services (for DNS records).
  #

  community_services = [
    CommunityScriptService(
      name='proxmox_backup_server',
      vmid=read_env_var('PBS_VMID', 100, value_type=int),
      hostname=read_env_var('PBS_HOSTNAME', 'pbs'),
      port='8007',
      protocol=Protocol.HTTPS,
    ),
    CommunityScriptService(
      name='prometheus_community',
      vmid=read_env_var('PROMETHEUS_VMID', 140, value_type=int),
      hostname=read_env_var('PROMETHEUS_HOSTNAME', 'prometheus'),
      port='9090',
      protocol=Protocol.HTTP,
    ),
    CommunityScriptService(
      name='grafana_community',
      vmid=read_env_var('GRAFANA_VMID', 145, value_type=int),
      hostname=read_env_var('GRAFANA_HOSTNAME', 'grafana'),
      port='3000',
      protocol=Protocol.HTTP,
    ),
    CommunityScriptService(
      name='ollama',
      vmid=read_env_var('OLLAMA_VMID', 150, value_type=int),
      hostname=read_env_var('OLLAMA_HOSTNAME', 'ollama'),
      port='11434',
      protocol=Protocol.HTTP,
    ),
    CommunityScriptService(
      name='uptime_kuma',
      vmid=read_env_var('UPTIME_KUMA_VMID', 155, value_type=int),
      hostname=read_env_var('UPTIME_KUMA_HOSTNAME', 'uptime-kuma'),
      port='3001',
      protocol=Protocol.HTTP,
    ),
    CommunityScriptService(
      name='speedtest',
      vmid=read_env_var('SPEEDTEST_VMID', 160, value_type=int),
      hostname=read_env_var('SPEEDTEST_HOSTNAME', 'speedtest'),
      port='80',
      protocol=Protocol.HTTP,
    ),
    CommunityScriptService(
      name='n8n',
      vmid=read_env_var('N8N_VMID', 165, value_type=int),
      hostname=read_env_var('N8N_HOSTNAME', 'n8n'),
      port='5678',
      protocol=Protocol.HTTP,
    ),
    # GitHub runner: outbound-only connection to GitHub, no DNS record needed.
    CommunityScriptService(
      name='github_runner',
      vmid=read_env_var('GITHUB_RUNNER_VMID_BASE', 180, value_type=int),
      hostname=read_env_var('GITHUB_RUNNER_HOSTNAME', 'github-runner'),
      port='22',
      protocol=Protocol.SSH,
      add_to_dns=False,
    ),
  ]

  # Add community services to inventory vars for DNS configuration.
  inventory_vars['community_services'] = [
    {
      'name': svc.name,
      'vmid': svc.vmid,
      'hostname': svc.hostname,
      'ipv4': svc.ipv4,
      'port': svc.port,
      'protocol': svc.protocol.value,
      'dns_record': svc.to_dns_record(domain),
    }
    for svc in community_services if svc.add_to_dns
  ]

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

  # LXC services shared across all Proxmox hosts.
  shared_lxc_services = [
    nginx_reverse_proxy,
    tailscale_gateway,
    prometheus,
    grafana,
    loki,
    tempo,
  ]

  #
  # Setup k3s config.
  #

  kube_inventory = K8sInventory(
    version=read_env_var('K3S_VERSION', 'v1.30.2+k3s1'),
    ansible_user=read_env_var('K3S_ANSIBLE_USER', 'debian'),
    ansible_ssh_private_key=inventory_vars['ssh']['private_key'],
    ansible_python_interpreter=inventory_vars['ansible_python_interpreter'],
    # Dedicated k3s cluster join token — stored separately from the Proxmox API token.
    token=ssm_client.require_parameter('/homelab/k3s/token'),
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

  # Add Proxmox hosts — all three share the same bridge, host services, and
  # LXC services. Only the per-host SSM paths differ.
  for server_name in ['jmpa-server-1', 'jmpa-server-2', 'jmpa-server-3']:
    inventory.add_instances(ProxmoxHost(
      ipv4=ssm_client.require_parameter(f'/homelab/{server_name}/ipv4-address'),
      ipv4_cidr=default_cidr,
      device_name=ssm_client.require_parameter(f'/homelab/{server_name}/device-name'),
      bridge=bridge,
      host_services=[collector],
      lxc_services=shared_lxc_services,
    ))

  # Add NAS instance.
  nas = NAS(
    ipv4=ssm_client.require_parameter('/homelab/jmpa-nas-1/ipv4-address'),
    ipv4_cidr=default_cidr,
    device_name=ssm_client.require_parameter('/homelab/jmpa-nas-1/device-name'),
    ansible_port=read_env_var('NAS_SSH_PORT', '9222', value_type=int),
    host_services=[collector],
  )
  inventory.add_instances(nas)

  # Add DNS instance.
  inventory.add_instances(DNS(
    ipv4=ssm_client.require_parameter('/homelab/jmpa-dns-1/ipv4-address'),
    ipv4_cidr=default_cidr,
    device_name=ssm_client.require_parameter('/homelab/jmpa-dns-1/device-name'),
    host_services=[collector],
  ))

  # Add VPS instance (uncomment when ready to use).
  # inventory.add_instances(VPS(
  #   ipv4=ssm_client.require_parameter('/homelab/jmpa-vps-1/ipv4-address'),
  #   ipv4_cidr=default_cidr,
  #   device_name=ssm_client.require_parameter('/homelab/jmpa-vps-1/device-name'),
  #   host_services=[collector],
  # ))

  # Add EC2 instance(s).
  # Uncomment after running: make provision-ec2
  # The Terraform module stores the public IP and instance ID in SSM automatically.
  #
  # ec2_public_ip = ssm_client.get_parameter('/homelab/ec2/jmpa-ec2-1/public-ip')
  # if ec2_public_ip:
  #   inventory.add_instances(EC2(
  #     ipv4=ec2_public_ip,
  #     ipv4_cidr='32',                # single public IP
  #     device_name='eth0',
  #     region=read_env_var('AWS_REGION', 'ap-southeast-2'),
  #     instance_id=ssm_client.get_parameter('/homelab/ec2/jmpa-ec2-1/instance-id'),
  #     ssh_key_name=read_env_var('EC2_SSH_KEY_NAME', 'homelab'),
  #     ansible_user='admin',          # Debian AMI; use 'ubuntu' for Ubuntu AMIs
  #     host_services=[collector],
  #   ))

  #
  # Setup K8s services configuration.
  #

  # Homepage secrets — all sourced from SSM, will raise at inventory generation
  # time if any are missing (via _require() in HomepageConfig.to_dict()).
  homepage_config = HomepageConfig(
    proxmox_user=read_env_var('PROXMOX_USER', 'root@pam'),
    proxmox_pass=ssm_client.get_parameter('/homelab/proxmox/password'),
    pihole_api_key=ssm_client.get_parameter('/homelab/pihole/api-key'),
    nas_user=read_env_var('NAS_USER', 'admin'),
    nas_pass=ssm_client.get_parameter('/homelab/nas/password'),
    argocd_pass=ssm_client.get_parameter('/homelab/argocd/admin-password'),
    grafana_pass=grafana_admin_pass,           # reuse — already fetched above
    jellyfin_api_key=ssm_client.get_parameter('/homelab/jellyfin/api-key'),
    jellyseerr_api_key=ssm_client.get_parameter('/homelab/jellyseerr/api-key'),
    tautulli_api_key=ssm_client.get_parameter('/homelab/tautulli/api-key'),
    prowlarr_api_key=ssm_client.get_parameter('/homelab/prowlarr/api-key'),
    sonarr_api_key=ssm_client.get_parameter('/homelab/sonarr/api-key'),
    radarr_api_key=ssm_client.get_parameter('/homelab/radarr/api-key'),
    lidarr_api_key=ssm_client.get_parameter('/homelab/lidarr/api-key'),
    readarr_api_key=ssm_client.get_parameter('/homelab/readarr/api-key'),
    bazarr_api_key=ssm_client.get_parameter('/homelab/bazarr/api-key'),
    deluge_pass=ssm_client.get_parameter('/homelab/deluge/password'),
    n8n_api_key=ssm_client.get_parameter('/homelab/n8n/api-key'),
    github_token=github_token,                 # reuse — already fetched above
    tailscale_api_key=ssm_client.get_parameter('/homelab/tailscale/api-key'),
  )

  # Jellyfin host is derived from the NAS instance name + domain so it stays
  # consistent with the rest of the inventory rather than being hardcoded.
  jellyfin_host = f'{nas.name}.{domain}'

  k8s_services = K8sServices(
    argocd=ArgoCDConfig(),
    kubernetes_dashboard=KubernetesDashboardConfig(),
    metallb=MetalLBConfig(
      ip_range=read_env_var('K3S_METALLB_IP_RANGE', '10.0.0.200-10.0.0.250'),
    ),
    nfs_storage=NFSStorageConfig(
      server=ssm_client.require_parameter('/homelab/jmpa-nas-1/ipv4-address'),
    ),
    github_runner=GitHubRunnerConfig(),
    observability=ObservabilityConfig(
      grafana_pass=grafana_admin_pass,         # reuse — already fetched above
    ),
    media=MediaSuite(
      jellyfin_host=jellyfin_host,
      jellyfin_port=8096,
    ),
    homepage=homepage_config,
  )

  # Add K8s services to inventory vars.
  inventory_vars['k8s_services'] = k8s_services.to_dict()

  # Print inventory as JSON.
  print(json.dumps(inventory.to_dict(), indent=2))


if __name__ == '__main__':
  main()
