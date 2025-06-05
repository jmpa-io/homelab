#!/usr/bin/env bash
# This script checks if the WIFI device is working correctly. If the network is
# unreachable, it attempts to restart the networking.service to attempt to fix
# the issue.
#
# PLEASE NOTE:
# * https://forum.proxmox.com/threads/containers-loose-network-until-reboot-of-the-lxc.153588/.
#
# {{ ansible_managed }}

set -e

# Funcs.
log() { echo "{ \"ts\":\"$(date --iso-8601=seconds)\", \"msg\":\"$1\" }"; }

# Check connection, restarting the 'networking.service' if it's not reachable.
# NOTE: The following '-W 5' + 'sleep 5' = 10 seconds per check for 'networking.service'.
retries=2
for (( i=1; i<=retries; i++)); do
  if ! ping -c 5 -W 5 1.1.1.1 > /dev/null 2>&1; then
    log "(${i} of ${retries}) Network is unreachable! Restarting WIFI..."
    # systemctl restart networking.service
    ifreload -a
    sleep 5
  else
    log "Network is reachable! Exiting early..."
    exit 0
  fi
done

# One last try - reboot if it doesn't work.
if ! ping -c 5 -W 5 1.1.1.1 > /dev/null 2>&1; then
  log "Network is unreachable! Rebooting system..."
  reboot
fi

