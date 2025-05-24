#!/usr/bin/env bash
# This script updates the DNS entries in Tailscale with those defined in the
# Ansible inventory.

# funcs.
die() { echo "$1"; exit "${2:-1}"; }
usage() { echo "usage: $0 <dns-nameserver-1>,<dns-nameserver-2>,..."; exit 64; }
diejq() { echo "$1:" >&2; jq '.' <<< "$2"; exit "${3:-1}"; }

# check deps.
deps=(aws curl tr jq)
for dep in "${deps[@]}"; do hash "$dep" || missing+=("$dep"); done
if [[ "${#missing[*]}" -gt 0 ]]; then
  [[ "${#missing[*]}" -gt 1 ]] && s="s"
  die "missing dep${s}: ${missing[*]}"
fi

# check args.
[[ -z "$1" ]] && usage
IFS=',' read -r -a nameservers <<< "$1"; unset IFS

# check auth.
aws sts get-caller-identity &>/dev/null \
  || die "unable to connect to AWS; are you authed?"

# pull Tailscale credentials.
clientId=$(aws ssm get-parameter --name "/homelab/tailscale/oauth-tokens/dns/client-id" \
  --query "Parameter.Value" --output text \
  --with-decryption 2>/dev/null) \
  || die "failed to retrieve Tailscale OAuth client-id from Paramstore"
clientToken=$(aws ssm get-parameter --name "/homelab/tailscale/oauth-tokens/dns/client-token" \
  --query "Parameter.Value" --output text \
  --with-decryption 2>/dev/null) \
  || die "failed to retrieve Tailscale OAuth client-token from Paramstore"

# retrieve token.
resp=$(curl -s -X POST "https://api.tailscale.com/api/v2/oauth/token" \
  -d "grant_type=client_credentials" \
  -d "client_id=$clientId" \
  -d "client_secret=$clientToken") \
  || die "failed curl to retrieve token from Tailscale"
[[ $(<<< "$resp" jq '.message') == null ]] \
  || diejq "failed to retrieve token from Tailscale" "$resp"

# parse token.
token="$(<<< "$resp" jq -r '.access_token')" \
  || die "failed to parse response from retrieving token from Tailscale"

# update DNS nameservers in Tailscale.
resp=$(curl -s -X POST "https://api.tailscale.com/api/v2/tailnet/-/dns/nameservers" \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json" \
  -d "$(jq -c -n --argjson ns "$(printf '%s\n' "${nameservers[@]}" | jq -R . | jq -s .)" '{dns: $ns}')") \
  || die "failed to update Tailscale DNS nameservers"
[[ $(<<< "$resp" jq '.message') == null ]] \
  || diejq "failed to update DNS nameservers in Tailscale" "$resp"

