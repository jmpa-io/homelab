"""K8s service definitions for inventory."""
from dataclasses import dataclass, field
from typing import Optional, List


def _require(value: Optional[str], ssm_path: str) -> str:
    """Return value if set, otherwise raise with a clear message pointing to SSM."""
    if value is None:
        raise ValueError(
            f"Required secret is missing from AWS SSM Parameter Store: {ssm_path}\n"
            f"Run: aws ssm put-parameter --name \"{ssm_path}\" --value \"<value>\" --type SecureString"
        )
    return value


# ---------------------------------------------------------------------------
# ArgoCD
# ---------------------------------------------------------------------------

@dataclass
class ArgoCDConfig:
    version: str = "v2.10.4"
    namespace: str = "argocd"

    def to_dict(self) -> dict:
        return {
            'version': self.version,
            'namespace': self.namespace,
        }


# ---------------------------------------------------------------------------
# Kubernetes Dashboard
# ---------------------------------------------------------------------------

@dataclass
class KubernetesDashboardConfig:
  # Helm chart version (not app version). Check https://artifacthub.io/packages/helm/k8s-dashboard/kubernetes-dashboard
  version: str = "7.10.0"
  namespace: str = "kubernetes-dashboard"
  service_type: str = "LoadBalancer"

  def to_dict(self) -> dict:
    return {
      'version': self.version,
      'namespace': self.namespace,
      'service_type': self.service_type,
    }


# ---------------------------------------------------------------------------
# MetalLB
# ---------------------------------------------------------------------------

@dataclass
class MetalLBConfig:
    version: str = "v0.13.12"
    # Must be a free IP range within your LAN subnet.
    # Set via K3S_METALLB_IP_RANGE env var or override at construction.
    ip_range: str = "10.0.0.200-10.0.0.250"

    def to_dict(self) -> dict:
        return {
            'version': self.version,
            'ip_range': self.ip_range,
        }


# ---------------------------------------------------------------------------
# NFS storage
# ---------------------------------------------------------------------------

@dataclass
class NFSVolume:
    path: str
    pv_name: str
    capacity: str

    def to_dict(self) -> dict:
        return {
            'path': self.path,
            'pv_name': self.pv_name,
            'capacity': self.capacity,
        }


@dataclass
class NFSStorageConfig:
    # NAS IPv4 — injected at construction from hostvars, not hardcoded here.
    server: str = ""
    dynamic_path: str = "/volume4/k3s-storage"
    dynamic_storage_class: str = "nfs-storage"
    media_volumes: dict = field(default_factory=lambda: {
        'movies':    NFSVolume(path="/volume1/media/movies",  pv_name="nfs-media-movies",    capacity="5Ti"),
        'tv':        NFSVolume(path="/volume1/media/tv",      pv_name="nfs-media-tv",        capacity="5Ti"),
        'downloads': NFSVolume(path="/volume1/downloads",     pv_name="nfs-media-downloads", capacity="2Ti"),
        'music':     NFSVolume(path="/volume1/media/music",   pv_name="nfs-media-music",     capacity="2Ti"),
        'books':     NFSVolume(path="/volume1/media/books",   pv_name="nfs-media-books",     capacity="500Gi"),
        'media':     NFSVolume(path="/volume1/media",         pv_name="nfs-media-root",      capacity="10Ti"),
        'volume2':   NFSVolume(path="/volume2",               pv_name="nfs-volume2",         capacity="10Ti"),
    })

    def to_dict(self) -> dict:
        return {
            'server': self.server,
            'dynamic': {
                'path': self.dynamic_path,
                'storage_class_name': self.dynamic_storage_class,
            },
            'media': {k: v.to_dict() for k, v in self.media_volumes.items()},
        }


# ---------------------------------------------------------------------------
# GitHub Actions Runner
# ---------------------------------------------------------------------------

@dataclass
class GitHubRunnerConfig:
    namespace: str = "actions-runner-system"
    repository: str = "jmpa-io/homelab"
    labels: List[str] = field(default_factory=lambda: [
        "self-hosted", "k3s", "homelab", "linux", "x64"
    ])

    def to_dict(self) -> dict:
        return {
            'namespace': self.namespace,
            'repository': self.repository,
            'labels': self.labels,
        }


# ---------------------------------------------------------------------------
# Observability
# ---------------------------------------------------------------------------

@dataclass
class ObservabilityConfig:
    namespace: str = "observability"
    grafana_pass: Optional[str] = None
    prometheus_retention: str = "30d"
    prometheus_storage: str = "100Gi"
    loki_retention: str = "744h"   # 31 days
    loki_storage: str = "50Gi"
    tempo_storage: str = "50Gi"

    def to_dict(self) -> dict:
        """Raises if required secrets are missing."""
        return {
            'namespace': self.namespace,
            'grafana_pass': _require(self.grafana_pass, '/homelab/grafana/admin-password'),
            'prometheus': {
                'retention': self.prometheus_retention,
                'storage': self.prometheus_storage,
            },
            'loki': {
                'retention': self.loki_retention,
                'storage': self.loki_storage,
            },
            'tempo': {
                'storage': self.tempo_storage,
            },
        }


# ---------------------------------------------------------------------------
# Media suite
# ---------------------------------------------------------------------------

@dataclass
class MediaService:
    """Individual *arr service configuration."""

    name: str
    port: int
    enabled: bool = True
    replicas: int = 1
    storage_size: str = "5Gi"
    memory_request: str = "256Mi"
    memory_limit: str = "1Gi"
    cpu_request: str = "100m"
    cpu_limit: str = "1000m"
    api_key: Optional[str] = None
    external_url: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'port': self.port,
            'enabled': self.enabled,
            'replicas': self.replicas,
            'storage_size': self.storage_size,
            'resources': {
                'requests': {'memory': self.memory_request, 'cpu': self.cpu_request},
                'limits':   {'memory': self.memory_limit,   'cpu': self.cpu_limit},
            },
            'api_key': self.api_key,
            'external_url': self.external_url,
        }


@dataclass
class MediaSuite:
    namespace: str = "media"
    timezone: str = "Australia/Melbourne"
    puid: str = "1000"
    pgid: str = "1000"
    download_client: str = "deluge"  # or "qbittorrent"

    sonarr:     MediaService = field(default_factory=lambda: MediaService(name="sonarr",     port=8989, storage_size="10Gi"))
    radarr:     MediaService = field(default_factory=lambda: MediaService(name="radarr",     port=7878, storage_size="10Gi"))
    lidarr:     MediaService = field(default_factory=lambda: MediaService(name="lidarr",     port=8686))
    readarr:    MediaService = field(default_factory=lambda: MediaService(name="readarr",    port=8787))
    prowlarr:   MediaService = field(default_factory=lambda: MediaService(name="prowlarr",   port=9696))
    bazarr:     MediaService = field(default_factory=lambda: MediaService(name="bazarr",     port=6767))
    jellyseerr: MediaService = field(default_factory=lambda: MediaService(name="jellyseerr", port=5055))
    tautulli:   MediaService = field(default_factory=lambda: MediaService(name="tautulli",   port=8181))
    deluge:     MediaService = field(default_factory=lambda: MediaService(
        name="deluge", port=8112, storage_size="10Gi",
        memory_request="512Mi", memory_limit="2Gi",
        cpu_request="200m", cpu_limit="2000m",
    ))

    # External Jellyfin — host is derived from NAS instance name + domain in main.py.
    jellyfin_host: str = ""
    jellyfin_port: int = 8096

    def to_dict(self) -> dict:
        return {
            'namespace': self.namespace,
            'timezone': self.timezone,
            'puid': self.puid,
            'pgid': self.pgid,
            'download_client': self.download_client,
            'services': {
                'sonarr':     self.sonarr.to_dict(),
                'radarr':     self.radarr.to_dict(),
                'lidarr':     self.lidarr.to_dict(),
                'readarr':    self.readarr.to_dict(),
                'prowlarr':   self.prowlarr.to_dict(),
                'bazarr':     self.bazarr.to_dict(),
                'deluge':     self.deluge.to_dict(),
                'jellyseerr': self.jellyseerr.to_dict(),
                'tautulli':   self.tautulli.to_dict(),
            },
            'jellyfin': {
                'host': self.jellyfin_host,
                'port': self.jellyfin_port,
            },
        }


# ---------------------------------------------------------------------------
# Top-level K8sServices
# ---------------------------------------------------------------------------

@dataclass
class K8sServices:
    """All K8s service configurations — single source of truth for the inventory."""

    argocd:               ArgoCDConfig               = field(default_factory=ArgoCDConfig)
    kubernetes_dashboard: KubernetesDashboardConfig   = field(default_factory=KubernetesDashboardConfig)
    metallb:              MetalLBConfig               = field(default_factory=MetalLBConfig)
    nfs_storage:          NFSStorageConfig            = field(default_factory=NFSStorageConfig)
    github_runner:        GitHubRunnerConfig          = field(default_factory=GitHubRunnerConfig)
    observability:        Optional[ObservabilityConfig] = None
    media:                MediaSuite                  = field(default_factory=MediaSuite)
    homepage:             Optional['HomepageConfig']  = None  # Populated from main.py

    def to_dict(self) -> dict:
        """Convert to dictionary for Ansible. Raises on any missing required secret."""
        result = {
            'argocd':               self.argocd.to_dict(),
            'kubernetes_dashboard': self.kubernetes_dashboard.to_dict(),
            'metallb':              self.metallb.to_dict(),
            'nfs_storage':          self.nfs_storage.to_dict(),
            'github_runner':        self.github_runner.to_dict(),
            'media':                self.media.to_dict(),
        }

        if self.observability:
            result['observability'] = self.observability.to_dict()

        if self.homepage:
            result['homepage'] = {
                'secrets': self.homepage.to_dict()
            }

        return result
