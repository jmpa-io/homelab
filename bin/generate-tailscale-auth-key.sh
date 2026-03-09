#!/usr/bin/env bash
# Generates a new Tailscale auth key and stores it in AWS SSM Parameter Store.

# Funcs.
die() { echo "$1" >&2; exit "${2:-1}"; }
diejq() { echo "$1:" >&2; <<< "$2" jq '.' >&2; exit "${3:-1}"; }

# Check pwd.
[[ ! -d .git ]] \
  && die "Must be run from repository root directory."

# Check deps.
deps=(aws curl jq)
for dep in "${deps[@]}"; do
  hash "$dep" 2>/dev/null || missing+=("$dep")
done
if [[ ${#missing[@]} -ne 0 ]]; then
  s=""; [[ ${#missing[@]} -gt 1 ]] && { s="s"; }
  die "Missing dep${s}: ${missing[*]}."
fi

# Check auth.
aws sts get-caller-identity &>/dev/null \
  || die "Unable to connect to AWS; are you authed?"

# Fetch tailnet from SSM.
tailnet=$(aws ssm get-parameter \
  --name "/homelab/tailscale/tailnet" \
  --query 'Parameter.Value' \
  --output text 2>/dev/null \
  --with-decryption) \
  || die "Failed to fetch the Tailscale tailnet from AWS SSM Parameter Store."

# Fetch API key from SSM.
apiKey=$(aws ssm get-parameter \
  --name "/homelab/tailscale/api-key" \
  --query 'Parameter.Value' \
  --output text 2>/dev/null \
  --with-decryption) \
  || die "Failed to fetch the Tailscale API key from AWS SSM Parameter Store."

# Generate auth key using Tailscale API.
response=$(curl -s -X POST \
  "https://api.tailscale.com/api/v2/tailnet/$tailnet/keys" \
  -H "Authorization: Bearer $apiKey" \
  -H "Content-Type: application/json" \
  -d '{
    "capabilities": {
      "devices": {
        "create": {
          "reusable": true,
          "ephemeral": true,
          "preauthorized": true,
          "tags": [
            "tag:jmpa-server",
            "tag:jmpa-nas",
            "tag:jmpa-dns",
            "tag:jmpa-vps"
          ]
        }
      }
    },
    "description": "Ansible automation key"
  }') \
  || die "Failed to generate Tailscale auth key."

# Extract key from response.
authKey=$(<<< "$response" jq -r '.key // empty' 2>/dev/null) \
  || diejq "Failed to parse Tailscale API response" "$response" 1
[[ -z "$authKey" ]] \
  && diejq "Failed to extract auth key from API response" "$response" 1

# Store in AWS SSM.
aws ssm put-parameter \
  --name "/homelab/tailscale/auth-key" \
  --value "$authKey" \
  --type SecureString \
  --overwrite \
  &>/dev/null \
  || die "Failed to store the Tailscale auth key in AWS SSM Parameter Store."
