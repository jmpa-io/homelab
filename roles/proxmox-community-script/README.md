# Proxmox Community Script Role

This role automates the deployment of [Proxmox VE Community Scripts](https://community-scripts.org/scripts) (formerly tteck scripts) using Ansible.

## Description

The community scripts provide easy deployment of LXC containers with pre-configured applications. This role wraps those scripts to enable automated, repeatable deployments.

## Requirements

- Proxmox VE host(s) in inventory
- SSH access to Proxmox host
- Internet connectivity on Proxmox host

## Role Variables

### Required Variables

```yaml
script_url: ""          # URL to the community script
script_name: ""         # Name for the script (used for temp files)
container_id: ""        # Proxmox container ID (e.g., "100")
hostname: ""            # Container hostname
```

### Optional Variables

```yaml
# Proxmox host
proxmox_host: "{{ groups['proxmox_hosts'][0] }}"  # Which Proxmox host to deploy to

# Resources
ram: "2048"             # RAM in MB
swap: "512"             # Swap in MB
disk_size: "8"          # Disk size in GB
cpu_cores: "2"          # Number of CPU cores

# OS
os_type: "debian"       # OS type
os_version: "12"        # OS version

# Network
bridge: "vmbr0"         # Network bridge

# Container options
verbose: "yes"          # Enable verbose output
privileged: "no"        # Run as privileged container
features: "nesting=1"   # Container features

# Advanced
advanced_options: ""    # Additional environment variables
ssh_root_password: ""   # Set root password
cleanup_script: true    # Remove script files after execution
```

## Dependencies

None

## Example Playbook

### Basic Usage

```yaml
---
- name: Deploy Home Assistant
  hosts: localhost
  gather_facts: false
  roles:
    - role: proxmox-community-script
      vars:
        script_url: "https://github.com/community-scripts/ProxmoxVE/raw/main/ct/homeassistant.sh"
        script_name: "homeassistant"
        container_id: "100"
        hostname: "homeassistant"
        ram: "4096"
        disk_size: "16"
        cpu_cores: "4"
```

### Multiple Services

```yaml
---
- name: Deploy multiple services
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Deploy Plex
      include_role:
        name: proxmox-community-script
      vars:
        script_url: "https://github.com/community-scripts/ProxmoxVE/raw/main/ct/plex.sh"
        script_name: "plex"
        container_id: "110"
        hostname: "plex"
        ram: "4096"
        disk_size: "32"

    - name: Deploy Jellyfin
      include_role:
        name: proxmox-community-script
      vars:
        script_url: "https://github.com/community-scripts/ProxmoxVE/raw/main/ct/jellyfin.sh"
        script_name: "jellyfin"
        container_id: "111"
        hostname: "jellyfin"
        ram: "4096"
        disk_size: "32"
```

### With Advanced Options

```yaml
---
- name: Deploy with custom configuration
  hosts: localhost
  gather_facts: false
  roles:
    - role: proxmox-community-script
      vars:
        script_url: "https://github.com/community-scripts/ProxmoxVE/raw/main/ct/docker.sh"
        script_name: "docker"
        container_id: "120"
        hostname: "docker-host"
        ram: "8192"
        disk_size: "100"
        cpu_cores: "8"
        privileged: "yes"
        features: "nesting=1,keyctl=1"
        advanced_options: |
          export DOCKER_COMPOSE_VERSION="2.24.0"
          export PORTAINER="yes"
```

## Popular Scripts

Here are some commonly used community scripts:

### Media Servers
- **Plex**: `https://github.com/community-scripts/ProxmoxVE/raw/main/ct/plex.sh`
- **Jellyfin**: `https://github.com/community-scripts/ProxmoxVE/raw/main/ct/jellyfin.sh`
- **Emby**: `https://github.com/community-scripts/ProxmoxVE/raw/main/ct/emby.sh`

### Home Automation
- **Home Assistant**: `https://github.com/community-scripts/ProxmoxVE/raw/main/ct/homeassistant.sh`
- **Node-RED**: `https://github.com/community-scripts/ProxmoxVE/raw/main/ct/node-red.sh`
- **Zigbee2MQTT**: `https://github.com/community-scripts/ProxmoxVE/raw/main/ct/zigbee2mqtt.sh`

### Development
- **Docker**: `https://github.com/community-scripts/ProxmoxVE/raw/main/ct/docker.sh`
- **Portainer**: `https://github.com/community-scripts/ProxmoxVE/raw/main/ct/portainer.sh`
- **GitLab**: `https://github.com/community-scripts/ProxmoxVE/raw/main/ct/gitlab.sh`

### Monitoring
- **Uptime Kuma**: `https://github.com/community-scripts/ProxmoxVE/raw/main/ct/uptimekuma.sh`
- **Grafana**: `https://github.com/community-scripts/ProxmoxVE/raw/main/ct/grafana.sh`
- **Prometheus**: `https://github.com/community-scripts/ProxmoxVE/raw/main/ct/prometheus.sh`

### Networking
- **Pi-hole**: `https://github.com/community-scripts/ProxmoxVE/raw/main/ct/pihole.sh`
- **AdGuard Home**: `https://github.com/community-scripts/ProxmoxVE/raw/main/ct/adguard.sh`
- **Nginx Proxy Manager**: `https://github.com/community-scripts/ProxmoxVE/raw/main/ct/nginxproxymanager.sh`

## How It Works

1. **Validation**: Checks that required variables are set
2. **Existence Check**: Verifies container ID isn't already in use
3. **Download**: Downloads the community script to Proxmox host
4. **Environment**: Creates environment file with configuration
5. **Execute**: Runs the script with environment variables
6. **Wait**: Waits for container to be fully started
7. **IP Discovery**: Gets the container's IP address
8. **Cleanup**: Removes temporary files
9. **Inventory**: Adds container to Ansible inventory for further configuration

## Troubleshooting

### Script Fails

Check the script output:
```bash
ansible-playbook playbook.yml -vvv
```

### Container Already Exists

Remove the existing container:
```bash
pct stop <container_id>
pct destroy <container_id>
```

### Script Not Found

Verify the script URL is correct:
```bash
curl -I <script_url>
```

### Network Issues

Ensure Proxmox host has internet access:
```bash
ansible proxmox_hosts -m shell -a "ping -c 1 github.com"
```

## License

MIT

## Author Information

Created for jmpa-io/homelab infrastructure automation.
