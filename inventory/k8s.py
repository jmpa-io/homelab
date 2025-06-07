from dataclasses import dataclass

@dataclass
class KubeConfig:
  version: str

  masters_per_host: int
  masters_ips_start_range: int
  masters_ips_end_range: int

  nodes_per_host: int
  nodes_ips_start_range: int
  nodes_ips_end_range: int


