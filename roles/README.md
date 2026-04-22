# Ansible Roles

Custom roles for homelab infrastructure.

## Roles

- **`cleanup`** - Remove deprecated files and packages
- **`copy-file-to-lxc`** - Copy files to LXC containers
- **`create-lxc`** - Create LXC containers
- **`create-vm`** - Create virtual machines
- **`create-vm-template`** - Build VM templates
- **`execute-script-in-lxc`** - Run scripts in containers
- **`proxmox-community-script`** - Deploy services using community scripts

## Usage

Roles are included by playbooks. See individual role directories for details.

## Creating a Role

```bash
mkdir -p roles/my-role/{tasks,templates,vars,defaults}
```

See [Ansible docs](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html) for best practices.
