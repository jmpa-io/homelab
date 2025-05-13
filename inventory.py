#!/usr/bin/env python3
import json
import os
import boto3
from typing import Callable, Optional, Dict

# SSMClient is a class to encapsulate the boto3 SSM client functionality.
class SSMClient:
  def __init__(self, region: str):
    self.client = boto3.client('ssm', region_name=region)

  def get_parameter(self, name: str, with_decryption: bool = True) -> Optional[str]:
    try:
      response = self.client.get_parameter(Name=name, WithDecryption=with_decryption)
      return response['Parameter']['Value']
    except self.client.exceptions.ParameterNotFound:
      print(f"Parameter '{name}' not found.")
      return None
    except Exception as e:
      print(f"Failed to retrieve Parameter '{name}': {e}")
      return None

# read_env_var reads an environment variable, defaults to a specified value if
# not found, validates the value, and casts it to the required type.
def read_env_var(name: str, default_value: Optional[str] = None, required: bool = False, value_type: Callable = str) -> Optional[str]:

  value = os.environ.get(name, default_value)

  # Check if the required env var is missing.
  if required and value is None:
      raise ValueError(f"Environment variable '{name}' is required but not set.")

  # If the value exists, try casting it to the specific type.
  if value is not None:
      try:
        return value_type(value)
      except ValueError:
        raise ValueError(f"Environment variable '{name}' must be of type {value_type.__name__}.")

  return value

# generate_inventory generates an Ansible inventory, based on the given
# configuration dictionary.
def generate_inventory(config: Dict) -> Dict:

    # Setup basic structure.
    inventory = {
        "_meta": {
            "hostvars": {}
        },
        "all": {
            "vars": {

                "ansible_ssh_pass": config['ansible_ssh_pass'],
                "ansible_become_pass": config['ansible_become_pass'],
                "ansible_python_interpreter": config['ansible_python_interpreter'],

                "common": {
                    "subnet": {
                        "ipv4": config['host_subnet_ipv4'],
                        "ipv4_cidr": config['default_cidr'],
                        "ipv4_with_cidr": f"{config['host_subnet_ipv4']}/{config['default_cidr']}",
                    },

                    "dns": {
                        "domain": config['dns_domain'],
                    },
                },

                "proxmox": {
                    "api_token": config['proxmox_api_token'],
                },

                "tailscale": {
                    "oauth_private_key": config['tailscale_oauth_private_key'],
                },

                "ssl": {
                    "private_key": config['ssl_private_key'],
                    "cert": config['ssl_cert'],
                },
            },

            # Populate hosts.
            "hosts": [f"jmpa_server_{i}" for i in range(1, config['server_count'] + 1)],
        }
    }

    # Populate variables for hosts.
    inventory['_meta']['hostvars'] = {
      f"jmpa_server_{i}": {

        "ansible_host": config["hosts"][f"jmpa_server_{i}"]["ansible_host"],

        "host": {
            "name": f"jmpa-server-{i}",

            "ipv4": config["hosts"][f"jmpa_server_{i}"]["ansible_host"],
            "ipv4_cidr": config["hosts"][f"jmpa_server_{i}"]["ansible_host_cidr"],
            "ipv4_with_cidr": f"{config['hosts'][f'jmpa_server_{i}']['ansible_host']}/{config["hosts"][f"jmpa_server_{i}"]["ansible_host_cidr"]}",

            "wifi_device_name": config["hosts"][f"jmpa_server_{i}"]["host_wifi_device_name"],

            "bridge": {
                "name": config['host_bridge_name'],

                "ipv4": f"{config['host_bridge_ipv4_prefix']}.{i}.{config['host_bridge_ipv4_suffix']}",
                "ipv4_cidr": config['default_cidr'],
                "ipv4_with_cidr": f"{config['host_bridge_ipv4_prefix']}.{i}.{config['host_bridge_ipv4_suffix']}/{config['default_cidr']}",
                "subnet": f"{config['host_bridge_ipv4_prefix']}.{i}.0",

                "default_ipv4_prefix": config['host_bridge_ipv4_prefix'],
                "default_ipv4_suffix": config['host_bridge_ipv4_suffix'],
            },

            "collector": {
              "metrics_port": config['host_otelcol_metrics_port'],
            },
        },

        "services": {
            "nginx_reverse_proxy": {
                "container_id": config['nginx_reverse_proxy_container_id'],

                "ipv4": f"{config['host_bridge_ipv4_prefix']}.{i}.{config['nginx_reverse_proxy_container_id']}",
                "ipv4_cidr": config['default_cidr'],
                "ipv4_with_cidr": f"{config['host_bridge_ipv4_prefix']}.{i}.{config['nginx_reverse_proxy_container_id']}/{config['default_cidr']}",

                "static_records": [
                    {
                        "subdomain": "proxmox",
                        "forward_to_ipv4_with_port": f"{config['hosts'][f"jmpa_server_{i}"]['ansible_host']}:{config['host_proxmox_ui_port']}",
                    },
                    *config["nginx_reverse_proxy_static_records"].get(f"jmpa_server_{i}", {}).get("static_records", []),
                ],
            },

            "tailscale_gateway": {
                "container_id": config['tailscale_gateway_container_id'],

                "ipv4": f"{config['host_bridge_ipv4_prefix']}.{i}.{config['tailscale_gateway_container_id']}",
                "ipv4_cidr": config['default_cidr'],
                "ipv4_with_cidr": f"{config['host_bridge_ipv4_prefix']}.{i}.{config['tailscale_gateway_container_id']}/{config['default_cidr']}",
            },

            "prometheus": {
                "container_id": config['prometheus_container_id'],

                "ipv4": f"{config['host_bridge_ipv4_prefix']}.{i}.{config['prometheus_container_id']}",
                "ipv4_cidr": config['default_cidr'],
                "ipv4_with_cidr": f"{config['host_bridge_ipv4_prefix']}.{i}.{config['prometheus_container_id']}/{config['default_cidr']}",
            },
        },

      } for i in range(1, config['server_count'] + 1)
    }

    return inventory

def main():

  # Setup client for AWS SSM Parameter Store.
  ssm_client = SSMClient(read_env_var("AWS_REGION", None, True))

  # Setup config.
  config = {

    # General.
    "server_count": read_env_var("SERVER_COUNT", 3, False, int),

    # Ansible.
    "ansible_ssh_pass": ssm_client.get_parameter("/homelab/ssh-password"),
    "ansible_become_pass": ssm_client.get_parameter("/homelab/root-password"),
    "ansible_python_interpreter": read_env_var("ANSIBLE_PYTHON_INTERPRETER", "/usr/bin/python3.11"),

    # Proxmox.
    "proxmox_api_token": ssm_client.get_parameter("/homelab/proxmox/api-token"),

    # Tailscale.
    "tailscale_oauth_private_key": ssm_client.get_parameter("/homelab/tailscale/oauth-tokens/ansible/client-token"),

    # SSL.
    "ssl_private_key": ssm_client.get_parameter("/homelab/ssl/private-key"),
    "ssl_cert": ssm_client.get_parameter("/homelab/ssl/cert"),

    # DNS.
    "dns_domain": read_env_var("DOMAIN", "jmpa.lab"),

    # Networking.
    "default_cidr": read_env_var("DEFAULT_CIDR", 24, False, int),

    #
    # Host (aka. the Proxmox node).
    #

    # Subnet.
    "host_subnet_ipv4": ssm_client.get_parameter("/homelab/subnet"),

    # Bridge.
    "host_bridge_name": read_env_var("HOST_BRIDGE_NAME", "vmbr0"),
    "host_bridge_ipv4_prefix": read_env_var("HOST_BRIDGE_IPV4_PREFIX", "10.0"),
    "host_bridge_ipv4_suffix": read_env_var("HOST_BRIDGE_IPV4_SUFFIX", "1"),

    # Proxmox UI.
    "host_proxmox_ui_port": read_env_var("HOST_PROXMOX_UI_PORT", "8006"),

    # Open Telemetry Collector.
    "host_otelcol_metrics_port": read_env_var("HOST_OTELCOL_METRICS_PORT", "8889"),

    #
    # LXC Containers.
    #

    # Nginx (reverse-proxy).
    "nginx_reverse_proxy_container_id": read_env_var("NGINX_REVERSE_PROXY_CONTAINER_ID", "4"),

    # Tailscale (gateway).
    "tailscale_gateway_container_id": read_env_var("TAILSCALE_GATEWAY_CONTAINER_ID", "15"),

    # Prometheus.
    "prometheus_container_id": read_env_var("PROMETHEUS_CONTAINER_ID", "40"),
    "prometheus_port": read_env_var("PROMETHEUS_PORT", "9090"),

    # Grafana.
    "grafana_container_id": read_env_var("GRAFANA_CONTAINER_ID", "45"),
    "grafana_port": read_env_var("GRAFANA_PORT", "3000"),

  }

  # Setup config - hosts.
  config['hosts'] = {
    f"jmpa_server_{i}": {

      "ansible_host": ssm_client.get_parameter(f"/homelab/jmpa-server-{i}/ipv4-address"),
      "ansible_host_cidr": config['default_cidr'],

      "host_wifi_device_name": ssm_client.get_parameter(f"/homelab/jmpa-server-{i}/wifi-device-name"),

    } for i in range(1, config['server_count'] + 1)
  }

  # Setup config - nginx-reverse-proxy | static records.
  config["nginx_reverse_proxy_static_records"] = {
    "jmpa_server_1": {
      "static_records": [
        { "subdomain": "homepage", "forward_to_ipv4_with_port": "10.0.1.2:3000" },
        { "subdomain": "uptimekuma", "forward_to_ipv4_with_port": "10.0.1.20:3001" },
        { "subdomain": "myspeed", "forward_to_ipv4_with_port": "10.0.1.30:5326" },
      ],
    },
    "jmpa_server_2": {
      "static_records": [
        { "subdomain": "grafana", "forward_to_ipv4_with_port": "10.0.2.5:3000" },
        { "subdomain": "code", "forward_to_ipv4_with_port": "10.0.2.30:8680" },
      ],
    },
    "jmpa_server_3": {
      "static_records": [
        { "subdomain": "grafana", "forward_to_ipv4_with_port": "10.0.2.5:3000" },
      ],
    },
  }

  # Setup inventory.
  inventory = generate_inventory(config)

  # Print inventory.
  print(json.dumps(inventory, indent=2))


if __name__ == "__main__":
  main()
