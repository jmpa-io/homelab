#!/usr/bin/env bash
# Generates a new Tailscale OAuth client token and stores it in AWS SSM Parameter.

# Funcs.
die() { echo "$1" >&2; exit "${2:-1}"; }
diejq() { echo "$1" | jq '.' >&2; exit "${2:-1}"; }

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

# Check auth.
aws sts get-caller-identity &>/dev/null \
  || die "Unable to connect to AWS; are you authed?"

# Generate OAuth client token using Tailscale API.
response=$(curl -s -X POST \
  "https://api.tailscale.com/api/v2/tailnet/$tailnet/keys" \
  -H "Authorization: Bearer $apiKey" \
  -H "Content-Type: application/json" \
  -d '{
    "capabilities": {
      "devices": {
        "create": {
          "reusable": false,
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
    "expirySeconds": 7776000,
    "description": "Ansible automation key"
  }') \
  || die "Failed to generate Tailscale OAuth client token."

# Extract key from response.
clientToken=$(<<< "$response" jq -r '.key // empty') \
  || diejq "$response" "Failed to parse Tailscale API response."
[[ -z "$clientToken" ]] \
  && diejq "$response" "Failed to extract Tailscale OAuth client token from API response."

# Store in AWS SSM.
aws ssm put-parameter \
  --name "/homelab/tailscale/oauth-client-token" \
  --value "$clientToken" \
  --type SecureString \
  --overwrite \
  &>/dev/null \
  || die "Failed to store the Tailscale OAuth client token in AWS SSM Parameter Store."
