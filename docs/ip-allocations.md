# IP Address Allocations

Complete IP addressing scheme for the homelab. All physical host IPs (servers,
NAS, DNS, internet gateway) are stored in AWS SSM Parameter Store — nothing
is hardcoded.

---

## Physical LAN (`/homelab/subnet` in SSM)

All physical devices live on the LAN subnet stored in SSM. The exact range
depends on your router, but the scheme assumes a `/24`.

| Device | SSM Path | Notes |
|--------|----------|-------|
| jmpa-server-1 | `/homelab/jmpa-server-1/ipv4-address` | Proxmox host 1 physical IP |
| jmpa-server-2 | `/homelab/jmpa-server-2/ipv4-address` | Proxmox host 2 physical IP |
| jmpa-server-3 | `/homelab/jmpa-server-3/ipv4-address` | Proxmox host 3 physical IP |
| jmpa-nas-1 | `/homelab/jmpa-nas-1/ipv4-address` | NAS (also NFS server for k3s) |
| jmpa-dns-1 | `/homelab/jmpa-dns-1/ipv4-address` | Raspberry Pi running Pi-hole |
| Internet gateway | `/homelab/internet-gateway` | Router |
| MetalLB pool | `<LAN_BASE>.200 – <LAN_BASE>.250` | LoadBalancer IPs for k3s services |

The MetalLB range is derived from the LAN subnet at inventory generation time:
`inventory/main.py` takes the first three octets of `/homelab/subnet` and
appends `.200–.250`. Override with `K3S_METALLB_IP_RANGE` env var if needed.

---

## Proxmox Bridge Subnets

Each Proxmox host (on-prem or VPS) has a `vmbr0` bridge with its own `/24`.
All LXC containers and VMs on that host get IPs in that subnet.

VPS host IDs are offset by 3 from on-prem servers so their bridge subnets
never collide (`jmpa-vps-1` gets host_id=4, `jmpa-vps-2` gets host_id=5...).

| Host | Type | host_id | Bridge IP | Subnet |
|------|------|---------|-----------|--------|
| jmpa-server-1 | on-prem | 1 | `10.0.1.1` | `10.0.1.0/24` |
| jmpa-server-2 | on-prem | 2 | `10.0.2.1` | `10.0.2.0/24` |
| jmpa-server-3 | on-prem | 3 | `10.0.3.1` | `10.0.3.0/24` |
| jmpa-vps-1 | cloud KVM VPS | 4 | `10.0.4.1` | `10.0.4.0/24` |
| jmpa-vps-2 | cloud KVM VPS | 5 | `10.0.5.1` | `10.0.5.0/24` |

---

## Per-Host IP Allocation Table

This table shows the full `.x` allocation for each `/24` host subnet.
Hosts 2, 3 and 4 follow the same pattern as host 1 (substitute `10.0.2.x` etc.).

| Last Octet | Allocation | Type | Notes |
|------------|-----------|------|-------|
| `.0` | **Reserved** | Network address | Do not use |
| `.1` | Bridge gateway | Infrastructure | `vmbr0` |
| `.2 – .4` | Free | — | |
| `.5` | `nginx_reverse_proxy` | Ansible LXC | VMID `{host_id}05` |
| `.6 – .14` | Free | — | |
| `.15` | `tailscale_gateway` | Ansible LXC | VMID `{host_id}15` |
| `.16 – .39` | Free | — | |
| `.40` | `prometheus` | Ansible LXC | VMID `{host_id}40` |
| `.41 – .44` | Free | — | |
| `.45` | `grafana` | Ansible LXC | VMID `{host_id}45` |
| `.46 – .49` | Free | — | |
| `.50` | `loki` | Ansible LXC | VMID `{host_id}50` |
| `.51 – .54` | Free | — | |
| `.55` | `tempo` | Ansible LXC | VMID `{host_id}55` |
| `.56 – .59` | Free | — | |
| `.60 – .69` | k3s master VMs | VM | VMID `{host_id}60+` |
| `.70 – .79` | k3s worker VMs | VM | VMID `{host_id}70+` |
| `.80 – .99` | Free | — | github_runner uses `.80` on host 1 |
| `.100` | `proxmox_backup_server` | Community script | VMID 100, **host 1 only** |
| `.101` | Free | — | |
| `.102` | `prometheus_community` | Community script | VMID 140, **host 1 only** |
| `.103` | `grafana_community` | Community script | VMID 145, **host 1 only** |
| `.104` | `ollama` | Community script | VMID 150, **host 1 only** |
| `.105` | `uptime_kuma` | Community script | VMID 155, **host 1 only** |
| `.106` | `speedtest` | Community script | VMID 160, **host 1 only** |
| `.107` | `n8n` | Community script | VMID 165, **host 1 only** |
| `.108` | `github_runner` | Community script | VMID 180, **host 1 only** |
| `.109 – .199` | Free (reserved for community scripts) | — | |
| `.200 – .254` | Free | — | |
| `.255` | **Reserved** | Broadcast address | Do not use |

### Key Rules

1. **`.0` and `.255` are always reserved** — network and broadcast addresses.
2. **Ansible LXC services use `.1–.79`** — the formula is `10.0.{host_id}.{container_id}`.
3. **k3s VMs use `.60–.79`** — masters start at `.60`, nodes at `.70`.
4. **Community scripts use `.100–.199`** — always on host 1 only (`proxmox_hosts[0]`).
   IPs are explicitly set (not derived from VMID) to prevent collisions.
5. **MetalLB LoadBalancer pool uses `<LAN>.200–<LAN>.250`** — this is the **physical LAN**,
   not a bridge subnet. L2 ARP mode — must be on the same network segment as your router.

---

## k3s Cluster VMs

Default configuration (1 master + 2 workers per host):

| Host | VM | IP | Proxmox VMID |
|------|----|----|--------------|
| jmpa-server-1 | k3s-master-1-1 | `10.0.1.60` | 160 |
| jmpa-server-1 | k3s-node-1-1 | `10.0.1.70` | 170 |
| jmpa-server-1 | k3s-node-1-2 | `10.0.1.71` | 171 |
| jmpa-server-2 | k3s-master-2-1 | `10.0.2.60` | 260 |
| jmpa-server-2 | k3s-node-2-1 | `10.0.2.70` | 270 |
| jmpa-server-2 | k3s-node-2-2 | `10.0.2.71` | 271 |
| jmpa-server-3 | k3s-master-3-1 | `10.0.3.60` | 360 |
| jmpa-server-3 | k3s-node-3-1 | `10.0.3.70` | 370 |
| jmpa-server-3 | k3s-node-3-2 | `10.0.3.71` | 371 |

VM template VMIDs (not in regular allocation — Proxmox-side only):
- jmpa-server-1: VMID 10001
- jmpa-server-2: VMID 10002
- jmpa-server-3: VMID 10003

---

## Community Scripts (Host 1 only)

All community scripts run on `proxmox_hosts[0]` (jmpa-server-1). Their IPs
are in the dedicated `.100–.199` range to prevent collisions.

| Service | VMID | IP | Port | Protocol |
|---------|------|----|------|----------|
| proxmox_backup_server | 100 | `10.0.1.100` | 8007 | HTTPS |
| prometheus_community | 140 | `10.0.1.102` | 9090 | HTTP |
| grafana_community | 145 | `10.0.1.103` | 3000 | HTTP |
| ollama | 150 | `10.0.1.104` | 11434 | HTTP |
| uptime_kuma | 155 | `10.0.1.105` | 3001 | HTTP |
| speedtest | 160 | `10.0.1.106` | 80 | HTTP |
| n8n | 165 | `10.0.1.107` | 5678 | HTTP |
| github_runner | 180 | `10.0.1.108` | 22 | SSH |

---

## Cloud VPS (jmpa-vps-1)

A KVM VPS (e.g. Hetzner CX22, ~€4/month) running Proxmox VE, connected
to the on-prem cluster via Tailscale. Treated identically to an on-prem
`ProxmoxHost` — runs the same LXC services, can join k3s, appears in the
`proxmox_hosts` Ansible group.

**Naming:** `jmpa-vps-1` (appears as `jmpa_vps_1` in Ansible inventory)
**Subnet:** `10.0.4.0/24` (host_id=4, never collides with on-prem)
**Groups:** `proxmox_hosts` (all playbooks work unchanged) + `vps_hosts` (VPS-specific plays)

See `services/vps/provision-vps.yml` for setup.
Run with: `make provision-vps VPS_IP=<your_vps_ip>`

### Connection model

```
Internet ──► jmpa-vps-1 (public IP on eth0)
                │
                ├── Tailscale ──► on-prem homelab (10.0.x.x LAN reachable)
                │
                └── vmbr0 (10.0.4.1/24) ──► LXC containers (10.0.4.x)
```

LXC containers on the VPS can reach on-prem services at `10.0.1.x`,
`10.0.2.x`, `10.0.3.x` directly via Tailscale subnet routing.

### Cost reference

| Provider | Plan | Price | vCPU | RAM | Storage | KVM | Nested VMs |
|----------|------|-------|------|-----|---------|-----|------------|
| Hetzner | CX22 | €3.92/mo | 2 | 4 GB | 40 GB SSD | ✓ | ✓ |
| Hetzner | CX32 | €7.02/mo | 4 | 8 GB | 80 GB SSD | ✓ | ✓ |
| Contabo | VPS S | €4.99/mo | 4 | 8 GB | 50 GB NVMe | ✓ | ✓ |
| OVH | VPS Starter | €3.99/mo | 1 | 2 GB | 20 GB SSD | ✓ | ✗ |

> **Note on $5/month bare metal:** Doesn't exist. €4/month KVM VPS is the
> cheapest option that supports Proxmox LXC properly. For full VM support
> (nested KVM), Hetzner CX22 or Contabo VPS S are the best value.

---

## Adding New Services — Checklist

Before assigning an IP to a new service:

1. Check this table and `scripts/validate.py` (`make validate`) for conflicts
2. **Ansible LXC services**: assign a `container_id` in `.5–.59` that's not taken
3. **Community scripts**: use a VMID in the `100–199` range, IP in `.100–.199`
4. **k3s VMs**: adjust `K3S_MASTERS_START_RANGE` / `K3S_NODES_START_RANGE` env vars
5. **Never use `.0` or `.255`** on any subnet
6. Run `make validate` after any change to catch collisions
