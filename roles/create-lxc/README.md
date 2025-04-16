
## `create-lxc`

```diff
+ This role creates an LXC container and installs all the default required
+ dependencies expected to ensure the container is secure.
```

Variable|Required|Description|Default
:---|:---:|:---|:---:
`create_lxc_node_ip`| ✅ |The IPv4 address of the Proxmox node running the LXC container you want to copy a file into.|-
`create_lxc_node_name`| ✅ |The name of the Proxmox node.|-
`create_lxc_node_bridge_ip`| ✅ |The IPv4 address of the Linux bridge on the Proxmox node.|-
`create_lxc_node_bridge_name`| ✅ |The name of the Linux bridge on the Proxmox node.|-
|||
`create_lxc_proxmox_api_ip`| ✅ |The IPv4 address of the Proxmox API used to send queries against.|-
`create_lxc_proxmox_api_user`| - |The name of the user used when sending queries to the `api_ip`.|`root@pam`
`create_lxc_proxmox_api_token_id`| - |The id of the token used when sending queries to the `api_ip`.|`proxmox-api-token`
`create_lxc_proxmox_api_token_secret`| ✅ |The value of the API token used when sending queries to the `api_ip`.|-
|||
`create_lxc_container_id`| ✅ |The id used when creating the new LXC container|-
`create_lxc_container_ostemplate`| - |The `tar.zst` image used as the base of the LXC container.|`lxc:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst`
`create_lxc_container_hostname`| ✅ |The hostname used when creating the new LXC container.|-
`create_lxc_container_root_password`| ✅ |The root user used when creating the new LXC container.|-
`create_lxc_container_subnet`| ✅ |The IPv4 address + CIDR used when creating the new LXC container.|-
`create_lxc_container_tags`| ✅ |The tags associated with the new LXC container.|-
`create_lxc_container_cores`| - |The number of CPU cores allocated to the new LXC container.|`4`
`create_lxc_container_memory`| - |The amount of memory allocated to the new LXC container.|`2048`
