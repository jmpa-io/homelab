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

# Fetch OAuth client ID from SSM.
oauthClientId=$(aws ssm get-parameter \
  --name "/homelab/tailscale/oauth-client-id" \
  --query 'Parameter.Value' \
  --output text 2>/dev/null) \
  || die "Failed to fetch the Tailscale OAuth client ID from AWS SSM Parameter Store."

# Fetch OAuth client secret from SSM.
oauthClientSecret=$(aws ssm get-parameter \
  --name "/homelab/tailscale/oauth-client-secret" \
  --query 'Parameter.Value' \
  --output text 2>/dev/null \
  --with-decryption) \
  || die "Failed to fetch the Tailscale OAuth client secret from AWS SSM Parameter Store."

# Exchange OAuth credentials for access token.
tokenResponse=$(curl -s -X POST \
  "https://api.tailscale.com/api/v2/oauth/token" \
  -u "$oauthClientId:$oauthClientSecret" \
  -d "grant_type=client_credentials") \
  || die "Failed to exchange OAuth credentials for access token."

# Extract access token.
accessToken=$(<<< "$tokenResponse" jq -r '.access_token // empty' 2>/dev/null) \
  || diejq "Failed to parse OAuth token response" "$tokenResponse" 1
[[ -z "$accessToken" ]] \
  && diejq "Failed to extract access token from OAuth response" "$tokenResponse" 1

# Generate auth key using Tailscale API.
response=$(curl -s -X POST \
  "https://api.tailscale.com/api/v2/tailnet/$tailnet/keys" \
  -H "Authorization: Bearer $accessToken" \
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
    "expirySeconds": 7776000,
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
