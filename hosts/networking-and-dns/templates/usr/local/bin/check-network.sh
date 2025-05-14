#!/usr/bin/env bash
# This script checks if the WIFI device is working correctly. If the network is
# unreachable, it attempts to restart the networking.service to attempt to fix
# the issue.
#
# {{ ansible_managed }}

if ! ping -c 5 1.1.1.1 > /dev/null 2>&1; then
  echo "Network unreachable! Restarting networking.service..."
  systemctl restart networking.service
fi
