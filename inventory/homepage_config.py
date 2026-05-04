"""Homepage configuration for inventory."""
from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class HomepageConfig:
    """Homepage dashboard configuration.

    All secrets are optional at inventory generation time — missing values
    mean that Homepage widget will show an error, but nothing else breaks.
    The Homepage deployment playbook will fail if the secrets it needs are
    not populated, which is the right time to surface that.
    """

    namespace: str = "homepage"

    # Secrets (from SSM/environment) — all optional
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

        Missing values are emitted as empty strings — Homepage will show a
        widget error for that service but everything else keeps working.
        Add the SSM parameter to populate it at any time and redeploy.
        """
        def val(v: Optional[str]) -> str:
            return v or ''

        return {
            'HOMEPAGE_VAR_PROXMOX_USER':       self.proxmox_user,
            'HOMEPAGE_VAR_PROXMOX_PASS':        val(self.proxmox_pass),
            'HOMEPAGE_VAR_PIHOLE_API_KEY':       val(self.pihole_api_key),
            'HOMEPAGE_VAR_NAS_USER':             self.nas_user,
            'HOMEPAGE_VAR_NAS_PASS':             val(self.nas_pass),
            'HOMEPAGE_VAR_ARGOCD_PASS':          val(self.argocd_pass),
            'HOMEPAGE_VAR_GRAFANA_PASS':         val(self.grafana_pass),
            'HOMEPAGE_VAR_JELLYFIN_API_KEY':     val(self.jellyfin_api_key),
            'HOMEPAGE_VAR_JELLYSEERR_API_KEY':   val(self.jellyseerr_api_key),
            'HOMEPAGE_VAR_TAUTULLI_API_KEY':     val(self.tautulli_api_key),
            'HOMEPAGE_VAR_PROWLARR_API_KEY':     val(self.prowlarr_api_key),
            'HOMEPAGE_VAR_SONARR_API_KEY':       val(self.sonarr_api_key),
            'HOMEPAGE_VAR_RADARR_API_KEY':       val(self.radarr_api_key),
            'HOMEPAGE_VAR_LIDARR_API_KEY':       val(self.lidarr_api_key),
            'HOMEPAGE_VAR_READARR_API_KEY':      val(self.readarr_api_key),
            'HOMEPAGE_VAR_BAZARR_API_KEY':       val(self.bazarr_api_key),
            'HOMEPAGE_VAR_DELUGE_PASS':          val(self.deluge_pass),
            'HOMEPAGE_VAR_N8N_API_KEY':          val(self.n8n_api_key),
            'HOMEPAGE_VAR_GITHUB_TOKEN':         val(self.github_token),
            'HOMEPAGE_VAR_TAILSCALE_API_KEY':    val(self.tailscale_api_key),
        }
