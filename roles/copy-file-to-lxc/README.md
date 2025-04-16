
## `copy-file-to-lxc`

```diff
+ This role copies a local file to the given Proxmox node, then uses pct to
+ copy the file into the given LXC container. The file copied over is also run
+ through ansible.builtin.template.
```

Variable|Required|Description|Default
:---|:---:|:---|:---:
`copy_file_to_lxc_node_ip`| ✅ |The IPv4 address of the Proxmox node running the LXC container you want to copy a file into.|-
|||
`copy_file_to_lxc_container_id`| ✅ |The id of the LXC container on the Proxmox node.|-
|||
`copy_file_to_lxc_file_source`| ✅ |The source of the file to-be-copied on the machine running Ansible.|-
`copy_file_to_lxc_file_destination`| ✅ |The destination of where the file will be copied to inside the LXC container.|-
`copy_file_to_lxc_file_mode`| - |The mode of the file copied into the LXC container. Useful if you wanted to copy a script but don't want it to be executed at this time.|`0755`
|||
`copy_file_to_lxc_copy_to_node_no_log`| - |Shows logs from the 'copy file from host to Proxmox node' step.|`true`
`copy_file_to_lxc_copy_to_node_show_difference`| - |Shows the difference from running `ansible.builtin.template` when copying the given file to the Proxmox node.|`false`
|||
`copy_file_to_lxc_copy_to_lxc_no_log`| - |Shows logs from the 'copy file from Proxmox node into LXC container' step.|`false`
