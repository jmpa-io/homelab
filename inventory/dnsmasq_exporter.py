from dataclasses import dataclass


@dataclass
class DnsmasqExporter:
  metrics_port: str
