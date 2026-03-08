#!/usr/bin/env bash
# cleanup-ansible-backups.sh
# Removes timestamped backup files created by Ansible on remote instances.

set -euo pipefail

#
# Functions.
#

usage() {
    cat <<EOF
usage: $0 <hostname|ip> [ssh_port] [ssh_user]

Removes timestamped backup files created by Ansible on remote instances.

Examples:
  $0 192.168.1.100
  $0 jmpa-nas-1 9222 jmpa-nas-1
  $0 jmpa-server-1 22 root

EOF
}

die() {
    echo "error: $*" >&2
    exit 1
}

#
# Main.
#

# Check if host is provided.
[ $# -eq 0 ] && usage && die "missing hostname or ip address"

HOST="$1"
SSH_PORT="${2:-22}"
SSH_USER="${3:-root}"

echo "connecting to ${SSH_USER}@${HOST}:${SSH_PORT}..."

# List backup files first.
echo "searching for ansible backup files..."
BACKUP_FILES=$(ssh -p "${SSH_PORT}" "${SSH_USER}@${HOST}" "find /etc -name '*.20*' -type f 2>/dev/null" || true)

if [ -z "$BACKUP_FILES" ]; then
    echo "no backup files found on ${HOST}"
    exit 0
fi

# Display found files.
echo "found the following backup files:"
echo "$BACKUP_FILES"

# Ask for confirmation.
echo ""
read -rp "delete these files? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "aborted. no files were deleted."
    exit 0
fi

# Delete the files.
echo "deleting backup files..."
ssh -p "${SSH_PORT}" "${SSH_USER}@${HOST}" "find /etc -name '*.20*' -type f -delete 2>/dev/null" || \
    die "failed to delete backup files"

echo "successfully deleted backup files from ${HOST}"
