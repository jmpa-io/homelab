#!/usr/bin/env python3
import json

from ssm import SSMClient
from env import read_env_var

from bridge import Bridge
from host import Collector, Host
from service import Service
from inventory import Inventory

def main():

  # Setup client for AWS SSM Parameter Store.
  ssm_client = SSMClient(read_env_var("AWS_REGION", None, True))

  # Setup inventory variables & config.
  common_subnet_ipv4= ssm_client.get_parameter("/homelab/subnet")
  default_cidr = read_env_var("DEFAULT_CIDR", 24, False, int)
  inventory_vars = {

    "ansible_ssh_pass": ssm_client.get_parameter("/homelab/ssh-password"),
    "ansible_become_pass": ssm_client.get_parameter("/homelab/root-password"),
    "ansible_python_interpreter": read_env_var("ANSIBLE_PYTHON_INTERPRETER", "/usr/bin/python3.11"),

    "common": {
      "subnet": {
        "ipv4": common_subnet_ipv4,
        "ipv4_cidr": default_cidr,
        "ipv4_with_cidr": f"{common_subnet_ipv4}/{default_cidr}",
      },

      "dns": {
        "domain": read_env_var("DOMAIN", "jmpa.lab"),
      }
    },

    "proxmox": {
      "api_token": ssm_client.get_parameter("/homelab/proxmox/api-token"),
    },

    "tailscale": {
      "oauth_private_key": ssm_client.get_parameter("/homelab/tailscale/oauth-tokens/ansible/client-token"),
    },

    "ssl": {
      "private_key": ssm_client.get_parameter("/homelab/ssl/private-key"),
      "cert": ssm_client.get_parameter("/homelab/ssl/cert"),
    }
  }

  #
  # Setup services.
  #

  nginx_reverse_proxy = Service(
    name="nginx-reverse-proxy",
    container_id=read_env_var("NGINX_REVERSE_PROXY_CONTAINER_ID", "5"),
  )

  tailscale_gateway = Service(
    name="tailscale-gateway",
    container_id=read_env_var("TAILSCALE_GATEWAY_CONTAINER_ID", "15"),
  )

  prometheus = Service(
    name="prometheus",
    container_id=read_env_var("PROMETHEUS_CONTAINER_ID", "40"),
    default_port=read_env_var("PROMETHEUS_PORT", "9090"),
  )

  grafana = Service(
    name="grafana",
    container_id=read_env_var("GRAFANA_CONTAINER_ID", "45"),
    default_port=read_env_var("GRAFANA_PORT", "3000"),
  )

  #
  # Setup bridge.
  #

  bridge = Bridge(
    name=read_env_var("HOST_BRIDGE_NAME", "vmbr0"),
    ipv4_prefix=read_env_var("HOST_BRIDGE_IPV4_PREFIX", "10.0"),
    ipv4_suffix=read_env_var("HOST_BRIDGE_IPV4_SUFFIX", "1"),
    ipv4_cidr=default_cidr,
  )

  #
  # Setup collector.
  #

  collector = Collector(
    metrics_port=read_env_var("HOST_OTELCOL_METRICS_PORT", "8889"),
  )

  #
  # Setup inventory.
  #

  inventory = Inventory(vars=inventory_vars)
  inventory.add_hosts(
    Host(
      ipv4=ssm_client.get_parameter("/homelab/jmpa-server-1/ipv4-address"),
      ipv4_cidr=default_cidr,
      wifi_device_name=ssm_client.get_parameter("/homelab/jmpa-server-1/wifi-device-name"),
      bridge=bridge,
      collector=collector,
      services=[
        nginx_reverse_proxy,
        tailscale_gateway,

        prometheus,
      ],
    ),

    Host(
      ipv4=ssm_client.get_parameter("/homelab/jmpa-server-2/ipv4-address"),
      ipv4_cidr=default_cidr,
      wifi_device_name=ssm_client.get_parameter("/homelab/jmpa-server-2/wifi-device-name"),
      bridge=bridge,
      collector=collector,
      services=[
        nginx_reverse_proxy,
        tailscale_gateway,

        prometheus,
        grafana,
      ],
    ),

    Host(
      ipv4=ssm_client.get_parameter("/homelab/jmpa-server-3/ipv4-address"),
      ipv4_cidr=default_cidr,
      wifi_device_name=ssm_client.get_parameter("/homelab/jmpa-server-3/wifi-device-name"),
      bridge=bridge,
      collector=collector,
      services=[
        nginx_reverse_proxy,
        tailscale_gateway,

        prometheus,
        grafana,
      ],
    )
  )

  # Print inventory as JSON.
  print(json.dumps(inventory.to_dict(), indent=2))

if __name__ == "__main__":
    main()
