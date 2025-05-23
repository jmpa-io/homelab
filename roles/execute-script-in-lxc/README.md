
## `execute-script-in-lxc`

```diff
+ This role copies a local script to the given Proxmox host, then uses pct to
+ copy the script into the given LXC container and then executed directly 
+ inside the LXC container.The script copied over is also run through 
+ ansible.builtin.template.
```

Variable|Required|Description|Default
:---|:---:|:---|:---:
`execute_script_in_lxc_node_ip`| ✅ |The IPv4 address of the Proxmox node running the LXC container you want to copy a script into.|-
|||
`execute_script_in_lxc_container_id`| ✅ |The id of the LXC container on the Proxmox node.|-
|||
`execute_script_in_lxc_script_source`| ✅ |The source of the script to-be-copied on the machine running Ansible.|-
`execute_script_in_lxc_script_destination`| ✅ |The destination of where the script will be copied to inside the LXC container.|-
`execute_script_in_lxc_script_mode`| - |The mode of the script copied into the LXC container. Useful if you wanted to copy a script but don't want it to be executed at this time.|`0755`
|||
`execute_script_in_lxc_copy_to_node_no_log`| - |Shows logs from the 'copy file from host to Proxmox node' step.|`true`
`execute_script_in_lxc_copy_to_node_show_difference`| - |Shows the difference from running `ansible.builtin.template` when copying the given file to the Proxmox node.|`false`
|||
`execute_script_in_lxc_copy_to_lxc_no_log`| - |Shows logs from the 'copy file from Proxmox node into LXC container' step.|`true`
|||
`execute_script_in_lxc_execute_script_no_log`| - |Shows logs from the 'execute the script inside the LXC container' step.|`true`