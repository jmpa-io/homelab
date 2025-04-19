#!/usr/bin/env python3
import json
import os
import boto3
from typing import Callable, Optional

# SSMClient is a class to encapsulate the boto3 SSM client functionality.
class SSMClient:
  def __init__(self, region: str):
    self.client = boto3.client('ssm', region_name=region)

  def get_parameter(self, name: str, with_decrption: bool = True) -> Optional[str]:
    try:
      response = self.client.get_parameter(Name=name, WithDecryption=with_decrption)
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
def generate_inventory(config: dict) -> dict:

    # Setup basic structure.
    inventory = {
        "_meta": {
            "hostvars": {}
        },
        "all": {
            "vars": {
                # general.
                "domain": config['domain'],

                # aws.
                "aws_region": config['aws_region'],

                # networking - host.
                "host_default_subnet_ipv4": config['host_default_subnet_ipv4'],
                "host_default_subnet_ipv4_cidr": config['host_default_subnet_ipv4_cidr'],
                "host_default_subnet_ipv4_with_cidr": f"{config['host_default_subnet_ipv4']}/{config['host_default_subnet_ipv4_cidr']}",

                # ansible.
                "ansible_ssh_pass": config['ansible_ssh_pass'],
                "ansible_become_pass": config['ansible_become_pass'],
                "ansible_python_interpreter": "/usr/bin/python3.11",

                # proxmox.
                "proxmox_api_token": config['proxmox_api_token'],

                # tailscale.
                "tailscale_oauth_private_key": config['tailscale_oauth_private_key'],

                # ssl.
                "ssl_private_key": config['ssl_private_key'],
                "ssl_cert": config['ssl_cert'],

            },
            "hosts": [],
        },
        "all_servers": {
            "hosts": [],
        }
    }

    # Populate hosts.
    inventory['all']['hosts'] = [f"jmpa_server_{i}" for i in range(1, config['server_count'] + 1)]
    inventory['all_servers']['hosts'] = inventory['all']['hosts']

    # Populate variables for hosts.
    inventory['_meta']['hostvars'] = {
      f"jmpa_server_{i}": {

        # ansible.
        "ansible_host": config["hosts"][f"jmpa_server_{i}"]["ansible_host"],

        # host.
        "host_name": f"jmpa-server-{i}",
        "host_ipv4": config["hosts"][f"jmpa_server_{i}"]["ansible_host"],
        "host_ipv4_cidr": config["hosts"][f"jmpa_server_{i}"]["ansible_host_cidr"],
        "host_ipv4_with_cidr": f"{config['hosts'][f'jmpa_server_{i}']['ansible_host']}/{config["hosts"][f"jmpa_server_{i}"]["ansible_host_cidr"]}",

        "host_bridge_name": config['host_bridge_name'],

        "host_bridge_ipv4": f"{config['host_bridge_default_ipv4_prefix']}.{i}.1",
        "host_bridge_ipv4_cidr": config['host_bridge_default_ipv4_cidr'],
        "host_bridge_subnet": f"{config['host_bridge_default_ipv4_prefix']}.{i}.0",
        "host_bridge_ipv4_with_cidr": f"{config['host_bridge_default_ipv4_prefix']}.{i}.1/{config['host_bridge_default_ipv4_cidr']}",
        "host_bridge_default_ipv4_prefix": config['host_bridge_default_ipv4_prefix'],
        "host_bridge_default_ipv4_cidr": config['host_bridge_default_ipv4_cidr'],

        "host_wifi_device_name": config["hosts"][f"jmpa_server_{i}"]["host_wifi_device_name"],

        # tailscale.
        "tailscale_gateway_ipv4": f"{config['host_bridge_default_ipv4_prefix']}.{i}.15",
        "tailscale_gateway_ipv4_cidr": f"{config['host_bridge_default_ipv4_cidr']}",
        "tailscale_gateway_ipv4_with_cidr": f"{config['host_bridge_default_ipv4_prefix']}.{i}.15/{config['host_bridge_default_ipv4_cidr']}",

      } for i in range(1, config['server_count'] + 1)
    }

    return inventory

def main():

  # Setup ssm client.
  aws_region = read_env_var("AWS_REGION", None, True, str)
  ssm_client = SSMClient(aws_region)

  # Setup config.
  config = {

    # general.
    "server_count": read_env_var("SERVER_COUNT", 3, False, int),
    "domain": read_env_var("DOMAIN", "jmpa.lab", False, str),

    # aws.
    "aws_region": aws_region,

    # networking - host.
    "host_default_subnet_ipv4": ssm_client.get_parameter("/homelab/subnet"),
    "host_default_subnet_ipv4_cidr": ssm_client.get_parameter("/homelab/subnet/cidr"),

    "host_bridge_name": read_env_var("HOST_BRIDGE_NAME", "vmbr0", False, str),
    "host_bridge_default_ipv4_prefix": read_env_var("HOST_BRIDGE_DEFAULT_IPV4_PREFIX", "10.0", False, str),
    "host_bridge_default_ipv4_cidr": read_env_var("HOST_BRIDGE_DEFAULT_IPV4_CIDR", 24, False, str),

    # ansible.
    "ansible_ssh_pass": ssm_client.get_parameter("/homelab/ssh-password"),
    "ansible_become_pass": ssm_client.get_parameter("/homelab/root-password"),

    # proxmox.
    "proxmox_api_token": ssm_client.get_parameter("/homelab/proxmox/api-token"),

    # tailscale.
    "tailscale_oauth_private_key": ssm_client.get_parameter("/homelab/tailscale/oauth-tokens/ansible/client-token"),

    # ssl.
    "ssl_private_key": ssm_client.get_parameter("/homelab/ssl/private-key"),
    "ssl_cert": ssm_client.get_parameter("/homelab/ssl/cert"),

  }
  config['hosts'] = {
    f"jmpa_server_{i}": {

      # ansible.
      "ansible_host": ssm_client.get_parameter(f"/homelab/jmpa-server-{i}/ipv4-address"),
      "ansible_host_cidr": ssm_client.get_parameter(f"/homelab/jmpa-server-{i}/ipv4-address/cidr"),

      # networking - host.
      "host_wifi_device_name": ssm_client.get_parameter(f"/homelab/jmpa-server-{i}/wifi-device-name"),
    } for i in range(1, config['server_count'] + 1)
  }

  # Setup inventory.
  inventory = generate_inventory(config)

  # Print inventory.
  print(json.dumps(inventory, indent=2))


if __name__ == "__main__":
  main()
