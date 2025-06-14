from dataclasses import dataclass


@dataclass
class K8sInventory:
  version: str
  ansible_user: str
  ansible_ssh_private_key: str
  ansible_python_interpreter: str
  token: str

  # Masters.
  masters_per_host: int
  masters_ips_start_range: int
  masters_ips_end_range: int

  # Nodes.
  nodes_per_host: int
  nodes_ips_start_range: int
  nodes_ips_end_range: int
