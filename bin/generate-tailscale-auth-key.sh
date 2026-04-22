#!/usr/bin/env bash
# Generates a Tailscale auth key and stores it in AWS SSM Parameter Store.

set -e

# Funcs.
die() { echo "$1" >&2; exit "${2:-1}"; }

# Check deps.
deps=(tailscale aws)
missing=()
for dep in "${deps[@]}"; do hash "$dep" 2>/dev/null || missing+=("$dep"); done
if [[ ${#missing[@]} -ne 0 ]]; then
    [[ "${#missing[@]}" -gt 1 ]] && s="s"
    die "Missing dep${s}: ${missing[*]}."
fi

# Vars.
ssmPath="/homelab/tailscale/auth-key"
region="${AWS_REGION:-ap-southeast-2}"

# Generate Tailscale auth key.
authKey=$(tailscale up --auth-key="" 2>&1 | grep -o 'tskey-auth-[a-zA-Z0-9-]*' | head -1) \
    || authKey=$(tailscale status --json 2>/dev/null | grep -o 'tskey-auth-[a-zA-Z0-9-]*' | head -1) \
    || die "Failed to generate Tailscale auth key; Ensure you're logged into Tailscale."

[[ -z "$authKey" ]] && \
    die "No auth key generated; Try: tailscale up --auth-key=<key> or generate via admin console."

# Store in AWS SSM.
aws ssm put-parameter \
    --name "$ssmPath" \
    --value "$authKey" \
    --type "SecureString" \
    --overwrite \
    --region "$region" \
    || die "Failed to store auth key in SSM; path=$ssmPath, region=$region"

echo "Tailscale auth key stored successfully in SSM: $ssmPath"
echo "Key: $authKey"
