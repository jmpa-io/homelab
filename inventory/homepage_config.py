"""Homepage configuration for inventory."""
from dataclasses import dataclass
from typing import Optional, Dict

from k8s_services import _require


@dataclass
class HomepageConfig:
    """Homepage dashboard configuration."""

    namespace: str = "homepage"

    # Secrets (from SSM/environment)
    proxmox_user: str = "root@pam"
    proxmox_pass: Optional[str] = None

    pihole_api_key: Optional[str] = None

    nas_user: str = "admin"
    nas_pass: Optional[str] = None

    argocd_pass: Optional[str] = None
    grafana_pass: Optional[str] = None

    jellyfin_api_key: Optional[str] = None
    jellyseerr_api_key: Optional[str] = None
    tautulli_api_key: Optional[str] = None

    prowlarr_api_key: Optional[str] = None
    sonarr_api_key: Optional[str] = None
    radarr_api_key: Optional[str] = None
    lidarr_api_key: Optional[str] = None
    readarr_api_key: Optional[str] = None
    bazarr_api_key: Optional[str] = None

    deluge_pass: Optional[str] = None
    n8n_api_key: Optional[str] = None
    github_token: Optional[str] = None
    tailscale_api_key: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for Ansible secret creation.

        Raises ValueError if any required secret is missing from SSM.
        """
        return {
            'HOMEPAGE_VAR_PROXMOX_USER': self.proxmox_user,
            'HOMEPAGE_VAR_PROXMOX_PASS':        _require(self.proxmox_pass,        '/homelab/proxmox/password'),
            'HOMEPAGE_VAR_PIHOLE_API_KEY':       _require(self.pihole_api_key,      '/homelab/pihole/api-key'),
            'HOMEPAGE_VAR_NAS_USER': self.nas_user,
            'HOMEPAGE_VAR_NAS_PASS':             _require(self.nas_pass,            '/homelab/nas/password'),
            'HOMEPAGE_VAR_ARGOCD_PASS':          _require(self.argocd_pass,         '/homelab/argocd/admin-password'),
            'HOMEPAGE_VAR_GRAFANA_PASS':         _require(self.grafana_pass,        '/homelab/grafana/admin-password'),
            'HOMEPAGE_VAR_JELLYFIN_API_KEY':     _require(self.jellyfin_api_key,    '/homelab/jellyfin/api-key'),
            'HOMEPAGE_VAR_JELLYSEERR_API_KEY':   _require(self.jellyseerr_api_key,  '/homelab/jellyseerr/api-key'),
            'HOMEPAGE_VAR_TAUTULLI_API_KEY':     _require(self.tautulli_api_key,    '/homelab/tautulli/api-key'),
            'HOMEPAGE_VAR_PROWLARR_API_KEY':     _require(self.prowlarr_api_key,    '/homelab/prowlarr/api-key'),
            'HOMEPAGE_VAR_SONARR_API_KEY':       _require(self.sonarr_api_key,      '/homelab/sonarr/api-key'),
            'HOMEPAGE_VAR_RADARR_API_KEY':       _require(self.radarr_api_key,      '/homelab/radarr/api-key'),
            'HOMEPAGE_VAR_LIDARR_API_KEY':       _require(self.lidarr_api_key,      '/homelab/lidarr/api-key'),
            'HOMEPAGE_VAR_READARR_API_KEY':      _require(self.readarr_api_key,     '/homelab/readarr/api-key'),
            'HOMEPAGE_VAR_BAZARR_API_KEY':       _require(self.bazarr_api_key,      '/homelab/bazarr/api-key'),
            'HOMEPAGE_VAR_DELUGE_PASS':          _require(self.deluge_pass,         '/homelab/deluge/password'),
            'HOMEPAGE_VAR_N8N_API_KEY':          _require(self.n8n_api_key,         '/homelab/n8n/api-key'),
            'HOMEPAGE_VAR_GITHUB_TOKEN':         _require(self.github_token,        '/tokens/github'),
            'HOMEPAGE_VAR_TAILSCALE_API_KEY':    _require(self.tailscale_api_key,   '/homelab/tailscale/api-key'),
        }
