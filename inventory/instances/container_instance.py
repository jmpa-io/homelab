from dataclasses import dataclass, field
from typing import List, Dict, Any

from .instance import Instance
from service import Service


@dataclass(kw_only=True)
class ContainerInstance(Instance):
    """Instance that supports LXC container services."""
    lxc_services: List[Service] = field(default_factory=list)

    def get_container_services(self) -> Dict[str, Any]:
        return { s.name: s.to_dict() for s in self.lxc_services }
