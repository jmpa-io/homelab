#!/usr/bin/env bash
# Removes timestamped backup files created by Ansible on remote instances.

set -e

# Funcs.
die() { echo "$1" >&2; exit "${2:-1}"; }
usage() {
    cat <<EOF
Usage: $0 <hostname|ip> [ssh_port] [ssh_user]

Removes timestamped backup files created by Ansible on remote instances.

Arguments:
  hostname|ip    Target host (hostname or IP address)
  ssh_port       SSH port (default: 22)
  ssh_user       SSH user (default: root)

Examples:
  $0 192.168.1.100
  $0 jmpa-nas-1 9222 jmpa
  $0 proxmox-host-1 22 root
EOF
    exit 64
}

# Check deps.
deps=(ssh find wc)
missing=()
for dep in "${deps[@]}"; do hash "$dep" 2>/dev/null || missing+=("$dep"); done
if [[ ${#missing[@]} -ne 0 ]]; then
    [[ "${#missing[@]}" -gt 1 ]] && s="s"
    die "Missing dep${s}: ${missing[*]}."
fi

# Check args.
[[ $# -eq 0 ]] && usage
host="$1"
sshPort="${2:-22}"
sshUser="${3:-root}"

# Test SSH connectivity.
ssh -p "$sshPort" -o ConnectTimeout=5 -o BatchMode=yes "${sshUser}@${host}" "exit" 2>/dev/null \
    || die "Cannot connect to ${host}:${sshPort} as ${sshUser}; Check SSH configuration."

# Search for backup files.
backupFiles=$(ssh -p "$sshPort" "${sshUser}@${host}" "find /etc -name '*.20*' -type f 2>/dev/null" || true)
[[ -z "$backupFiles" ]] && \
    { echo "No backup files found on ${host}; Exiting early..."; exit 0; }

# Count and display files.
fileCount=$(echo "$backupFiles" | wc -l | tr -d ' ')
echo "Found ${fileCount} backup file(s) on ${host}:"
echo "===================="
echo "$backupFiles"
echo "===================="
echo ""

# Confirm deletion.
read -p "Delete these files? [y/N] " -n 1 -r
echo
[[ ! $REPLY =~ ^[Yy]$ ]] && { echo "Aborted."; exit 0; }

# Delete files.
while IFS= read -r file; do
    ssh -p "$sshPort" "${sshUser}@${host}" "rm -f '$file'" \
        || die "Failed to delete: $file"
    echo "Deleted: $file"
done <<< "$backupFiles"

# Verify deletion.
remainingFiles=$(ssh -p "$sshPort" "${sshUser}@${host}" "find /etc -name '*.20*' -type f 2>/dev/null" || true)
[[ -z "$remainingFiles" ]] \
    || die "Some files remain after deletion; Check manually."

echo "All backup files removed successfully from ${host}."
