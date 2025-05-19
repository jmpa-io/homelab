from dataclasses import dataclass, field

@dataclass
class Bridge:
    name: str                                   # eg. 'vmbr0'
    ipv4_prefix: str                            # eg. '10.0'
    ipv4_suffix: str                            # eg. '1'
    ipv4: str = field(init=False)               # eg. '10.0.1.1'
    ipv4_cidr: str                              # eg. '24'
    ipv4_with_cidr: str = field(init=False)     # eg. '10.0.1.1/24'
    subnet: str = field(init=False)             # eg. '10.0.1.0'
    subnet_with_cidr: str = field(init=False)   # eg. '10.0.1.0/24'

    def __post_init__(self):

      # PLEASE NOTE:
      # The '{{id}' here is a placeholder for the id of the host, like the '1'
      # found in 'jmpa-server-1'. This value is populated when this Bridge is
      # added to a Host, and that Host is added to an Inventory.

      self.ipv4 = f"{self.ipv4_prefix}.{{id}}.{self.ipv4_suffix}"
      self.ipv4_with_cidr = f"{self.ipv4}/{self.ipv4_cidr}"
      self.subnet = f"{self.ipv4_prefix}.{{id}}.0"
      self.subnet_with_cidr = f"{self.subnet}/{self.ipv4_cidr}"

