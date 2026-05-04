from dataclasses import dataclass


@dataclass
class K8sInventory:
  """Cluster-level K3s configuration — connection/auth details for Ansible to reach the VMs."""
  version: str
  ansible_user: str
  # Path to the SSH private key file on the controller machine.
  # The key content is fetched from SSM but must be written to disk before
  # Ansible runs. Use `make setup-k3s-ssh` to write it to the expected path.
  ansible_ssh_private_key_file: str
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
