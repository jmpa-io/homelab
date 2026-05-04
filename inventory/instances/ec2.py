"""EC2 instance type.

An EC2 instance is treated as a first-class fleet member alongside the
on-premises Proxmox hosts. Unlike ProxmoxHost it has no hypervisor, so it
cannot run LXC containers or K8s VMs — but it can run native services,
join the k3s cluster as a worker, and participate in DNS and Tailscale.

Class Hierarchy:
Instance
└── EC2
"""

from dataclasses import dataclass, field
from typing import Optional

from .instance import Instance


@dataclass
class EC2(Instance):
  """AWS EC2 instance as a fleet member.

  Attributes:
      ipv4:          Public IPv4 address (sourced from SSM after provisioning).
      ipv4_cidr:     CIDR prefix (typically 32 for a single public IP).
      device_name:   Primary network interface name (typically 'eth0').
      name:          Instance name template.
      region:        AWS region the instance lives in.
      instance_id:   EC2 instance ID (sourced from SSM, used for tagging/mgmt).
      ssh_key_name:  Name of the EC2 key pair used for SSH access.
      ansible_user:  SSH user (default 'admin' for Debian AMIs, 'ubuntu' for Ubuntu).
  """
  name: str = 'jmpa-ec2-{id}'
  region: str = 'ap-southeast-2'
  instance_id: Optional[str] = None
  ssh_key_name: Optional[str] = None

  def to_dict(self) -> dict:
    """Convert EC2 instance to dictionary for Ansible inventory."""
    base = self._base_dict()
    ec2_data = base.pop('instance')

    # Add EC2-specific metadata.
    ec2_data['region'] = self.region
    if self.instance_id:
      ec2_data['instance_id'] = self.instance_id
    if self.ssh_key_name:
      ec2_data['ssh_key_name'] = self.ssh_key_name

    base['ec2'] = ec2_data
    return base
