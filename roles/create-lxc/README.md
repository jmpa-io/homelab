
## `copy-file-to-lxc`

```diff
+ This role copies a local file to the Proxmox host, then uses pct to copy the
+ file into the given LXC container.
```

### `Usage`

Below is a breakdown of the variables for this role.

|Required|Variable|Description|Default Value|
|:---|:---|:---|:---
| |`proxmox_api_user`|User for the Proxmox API.|`root@pam`
| |`proxmox_api_token_id`|API token ID for Proxmox.|`proxmox-api-token`
|x|`container_vmid`|VMID for the container.|`{{ node_id }}{{ container_id }}`
| |`container_ostemplate`|OS template for the container.|`lxc:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst`
| |`container_cores`|Number of CPU cores for the container.|`4`
| |`container_memory`|Amount of RAM for the container in MB.|`2048`
| |`container_ssh_pubkey`|Path to the SSH public key for root access.|`{{ lookup('env', 'HOME') + '/.ssh/id_ed25519.pub' }}`
| |`container_hostname`|Hostname for the LXC container.|`tailscale`
|x|`container_root_password`|Root password for the LXC container.|`xxxx`
|x|`container_ip`|Static IPv4 address for the container.|`10.0.1.115`
|x|`container_ip_cidr`|CIDR for the container's static IP.|`24`
|x|`proxmox_node_name`|Name of the Proxmox node.|`jmpa-server-1`
| |`proxmox_node_id`|ID for the Proxmox node.|`1`
| |`proxmox_node_ip`|IP address of the Proxmox node.|`192.168.1.158`
| |`proxmox_node_bridge_ip`|Bridge IP address on the Proxmox node.|`10.0.1.1`
| |`proxmox_node_bridge_name`|Name of the bridge on the Proxmox node.|`vmbr0`
| |`tailscale_gateway_ipv4`|IP address for the Tailscale gateway.|`10.0.1.15`
| |`tailscale_gateway_ipv4_cidr`|CIDR for the Tailscale gateway IP.|`24`

