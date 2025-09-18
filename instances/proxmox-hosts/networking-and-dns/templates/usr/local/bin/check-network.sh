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

# Check connection, restarting the networking interface if it's not reachable.
maxRetries=10; baseSleep=5;
for (( i=1; i<=maxRetries; i++)); do

  # Check connectivity.
  ipUp=false; dnsUp=false
  ping -c 3 -W 5 1.1.1.1 >/dev/null 2>&1 && ipUp=true \
    || log "($i of $maxRetries) Network unreachable ( check)"
  ping -c 1 -W 5 google.com >/dev/null 2>&1 && dnsUp=true \
    || log "($i of $maxRetries) Network reachable, but DNS failed (dnsmasq?)"
  if $ipUp && $dnsUp; then
    log "($i of $maxRetries) Network is reachable! Exiting early."
    exit 0
  fi

  # Restart networking interfaces, if connectivity isn't working.
  log "($i of $maxRetries) Network is unreachable! Restarting Wi-FI."
  ifreload -a

  # Sleep w/ exponetial backoff.
  sleepTime=$(( baseSleep * 2**(i-1) ))
  [[ $sleepTime -gt 60 ]] && sleepTime=60
  sleep $sleepTime

done

log "Network is unreachable after $maxRetries retry attempts! Rebooting system..."
reboot

