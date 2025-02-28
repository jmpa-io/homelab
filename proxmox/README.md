
# Proxmox

This section covers setting up a new `jmpa-server` physical machine.

**Contents:**

* [Prerequisites](#prerequisites).
* [Setup `Proxmox` on new machine](#setting-up-proxmox-on-new-machine).
* [Add new machine to the existing Proxmox cluster](#add-new-machine-to-the-existing-proxmox-cluster).

## `Prerequisites`

On the new machine...

1. [Estabilish an internet connection, through `Ethernet` or `Wi-Fi`](#establish-an-internet-connection).
1. [Update dependencies](#update-dependencies).
1. [Setup `ssh`](#setting-up-ssh).

### Establish an internet connection.

To download the `Proxmox` dependencies (or any dependencies really), you need an internet connection.

```bash
# Debian 12 - Bookworm.

# Setup /etc/network/interfaces
cat <<EOF | sudo tee /etc/network/interfaces

# The lookback network interface.
auto lo
iface lo inet lookback

# Ethernet.
auto enoxxxx
allow-hotplug enoxxxx
iface enoxxxx inet dhcp

# Wi-Fi.
auto wlxxxxx
allow-hotplug wlxxxxx
iface wlxxxxx inet static
    address 192.168.1.xxx/24
    gateway 192.168.1.1
    dns-nameserver 1.1.1.1
    wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf

# Source any other network interfaces.
source /etc/network/interfaces.d/*

EOF

# Restart networking service.
sudo systemctl restart networking

# Ensure the network interface is 'UP' and there is an IPv4 Address.
ip a

# (Wi-Fi only) If that doesn't provide internet access to the Wi-Fi interface, then you'll need to setup internet through Ethernet first to install some dependencies.

# To use `wpa-conf` in the /etc/network/interfaces file, you need to install:
sudo apt update && sudo apt install wpasupplicant -y
wpa_passphrase "SSID" "Password" | sudo tee /etc/wpa_supplicant/wpa_supplicant.conf
# Ensure you go to /etc/wpa_supplicant/wpa_supplicant.conf and remove the #psk field.
sudo systemctl enable wpa_supplicant
sudo systemctl start wpa_supplicant
```

### Update dependencies

To pull any dependencies, run the following:

```bash
# Debian 12 - Bookworm.

# Setup apt 'sources.list'.
cat <<EOF | sudo tee /etc/apt/sources.list
deb http://deb.debian.org/debian/ bookworm main contrib non-free-firmware
deb http://security.debian.org/debian-security bookworm-security main contrib non-free-firmware
deb http://deb.debian.org/debian/ bookworm-updates main contrib non-free-firmware

EOF

# Update dependencies.
sudo apt update && sudo apt full-upgrade
```

### Setting up `ssh`

To setup `ssh`, run:

```bash
# Debian 12 - Bookworm.

sudo apt install openssh-server
sudo systemctl enable ssh
sudo systemctl start ssh
```

On the machine you want to `ssh` from, run:

```bash
ssh <user>@<new-machine-ip>
```
Replacing `<user>` with the name of the user you've set up, and `<new-machine-ip>` with the IP Address of the new machine.

## Setting up `Proxmox` on new machine

The following is [based on this wiki guide](https://pve.proxmox.com/wiki/Install_Proxmox_VE_on_Debian_12_Bookworm).

```bash
# Debian 12 - Bookworm.

# Setup /etc/hosts.
cat <<EOF | sudo tee /etc/hosts
127.0.0.1       localhost.localdomain localhost
127.0.0.1       jmpa-server-#
192.168.1.xxx   jmpa-server-#.palnet.net jmpa-server-#

# The following lines are desirable for IPv6 capable hosts
::1     localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters

EOF

# Setup Proxmox VE repository.
cat <<EOF | sudo tee /etc/apt/sources.list.d/pve-install-repo.list
deb [arch=amd64] http://download.proxmox.com/debian/pve bookworm pve-no-subscription

EOF

# Setup Proxmox VE repository key.
sudo wget https://enterprise.proxmox.com/debian/proxmox-release-bookworm.gpg -O /etc/apt/trusted.gpg.d/proxmox-release-bookworm.gpg

# Verify the key.
sha512sum /etc/apt/trusted.gpg.d/proxmox-release-bookworm.gpg
# 7da6fe34168adc6e479327ba517796d4702fa2f8b4f0a9833f5ea6e6b48f6507a6da403a274fe201595edc86a84463d50383d07f64bdde2e3658108db7d6dc87 /etc/apt/trusted.gpg.d/proxmox-release-bookworm.gpg

# Update apt repository.
sudo apt update && sudo apt full-upgrade

# Install Proxmox VE Kernel.
sudo apt install proxmox-default-kernel
sudo apt install proxmox-ve postfix open-iscsi chrony
sudo reboot

# Run community scripts.
# https://community-scripts.github.io/ProxmoxVE/scripts?id=post-pve-install
bash -c "$(wget -qLO - https://github.com/community-scripts/ProxmoxVE/raw/main/misc/post-pve-install.sh)"
```

The Proxmox UI should now be accessible via:

```bash
http://<new-machine-ip>:8006
```
If not, you have a problem somewhere along the way above and need to debug these steps.

## Connect new machine to the existing Proxmox cluster.

1. Gather the existing Proxmox cluster join information.

Login to https://proxmox.jmpa.io > `Datacenter` > `Cluster` > `Join Information` > Click `Copy Information`.

2. In another tab, login to the Proxmox UI for the new machine:

```bash
http://<new-machine-ip>:8006
```

The login credentials should be:

```bash
username: root
password: <password-for-root-user>
```

If you didn't set a password for the `root` user, run the following on the new machine:

```bash
sudo passwd root
```

And try again to login with the password you just set for the `root` user.

3. Navigate to `Datacenter` > `Cluster` > `Join Cluster` - paste the information & enter the password for the root user of the IP address printed.

4. Refresh the page and login again - you should now see the other nodes in the cluster. You should also see this new machine in the list of nodes in https://proxmox.jmpa.io.
