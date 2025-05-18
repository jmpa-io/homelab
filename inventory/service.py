from dataclasses import dataclass

@dataclass
class Service:
  name: str
  container_id: int
  port: int
  ipv4: str
  ipv4_cidr: str

