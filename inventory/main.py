import json

from bridge import Bridge
from host import Host
from service import Service
from inventory import Inventory

def main():

  # Setup services.
  tailscale = Service("tailscale", 15, 101)
  prometheus = Service("prometheus", 40, 9090)
  grafana = Service("grafana", 45, 3000)

  # Setup bridge.
  bridge = Bridge(
    name="vmbr0",
    ipv4_prefix="10.0",
    ipv4_suffix="1",
    ipv4_cidr="24"
  )

  # Setup inventory.
  inventory = Inventory()
  inventory.add_hosts(
    Host(
      ipv4="192.168.1.158",
      ipv4_cidr="24",
      wifi_device_name="wlx1",
      bridge=bridge,
      services=[
        tailscale,
        prometheus,
      ],
    ),

    Host(
      ipv4="192.168.1.146",
      ipv4_cidr="24",
      wifi_device_name="wlx2",
      bridge=bridge,
      services=[
        tailscale,
        prometheus,
        grafana,
      ],
    ),

    Host(
      ipv4="192.168.1.180",
      ipv4_cidr="24",
      wifi_device_name="wlx3",
      bridge=bridge,
      services=[
        tailscale,
        prometheus,
        grafana,
      ],
    )
  )

  # Print inventory as JSON.
  print(json.dumps(inventory.to_dict(), indent=2))

if __name__ == "__main__":
    main()
