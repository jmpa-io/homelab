#!/usr/bin/env bash
# generate-tailscale-auth-key.sh
# Generates a new Tailscale OAuth client token and stores it in AWS SSM.

set -euo pipefail

#
# Functions.
#

usage() {
    cat <<EOF
usage: $0 [options]

Generates a new Tailscale OAuth client token using the Tailscale API
and stores it in AWS SSM Parameter Store.

Options:
  -h, --help          Show this help message
  -d, --dry-run       Show what would be done without making changes
  -t, --tailnet       Tailscale tailnet (default: from TAILSCALE_TAILNET env var)
  -k, --api-key       Tailscale API key (default: from TAILSCALE_API_KEY env var)

Environment Variables:
  TAILSCALE_TAILNET   Your Tailscale tailnet (e.g., example.com)
  TAILSCALE_API_KEY   Your Tailscale API key (starts with tskey-api-)

Examples:
  $0
  $0 --dry-run
  $0 --tailnet example.com --api-key tskey-api-...

EOF
}

die() {
    echo "error: $*" >&2
    exit 1
}

#
# Main.
#

# Parse arguments.
DRY_RUN=false
TAILNET="${TAILSCALE_TAILNET:-}"
API_KEY="${TAILSCALE_API_KEY:-}"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -t|--tailnet)
            TAILNET="$2"
            shift 2
            ;;
        -k|--api-key)
            API_KEY="$2"
            shift 2
            ;;
        *)
            usage
            die "unknown option: $1"
            ;;
    esac
done

# Validate required parameters.
[ -z "$TAILNET" ] && usage && die "tailnet is required (set TAILSCALE_TAILNET or use --tailnet)"
[ -z "$API_KEY" ] && usage && die "api key is required (set TAILSCALE_API_KEY or use --api-key)"

# SSM parameter path.
SSM_PARAMETER="/homelab/tailscale/oauth-tokens/ansible/client-token"

echo "generating tailscale oauth client token..."

# Generate OAuth client token using Tailscale API.
RESPONSE=$(curl -s -X POST \
    "https://api.tailscale.com/api/v2/tailnet/${TAILNET}/keys" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d '{
        "capabilities": {
            "devices": {
                "create": {
                    "reusable": false,
                    "ephemeral": true,
                    "preauthorized": true,
                    "tags": ["tag:ansible"]
                }
            }
        },
        "expirySeconds": 7776000,
        "description": "Ansible automation key"
    }')

# Extract the key from the response.
CLIENT_TOKEN=$(echo "$RESPONSE" | jq -r '.key // empty')

if [ -z "$CLIENT_TOKEN" ]; then
    echo "failed to generate token. response:"
    echo "$RESPONSE" | jq '.'
    die "could not extract token from api response"
fi

echo "generated token: ${CLIENT_TOKEN:0:20}..."

if [ "$DRY_RUN" = true ]; then
    echo "[dry-run] would store token in ssm parameter: $SSM_PARAMETER"
    exit 0
fi

# Store in AWS SSM.
echo "storing token in ssm parameter: $SSM_PARAMETER"
aws ssm put-parameter \
    --name "$SSM_PARAMETER" \
    --value "$CLIENT_TOKEN" \
    --type SecureString \
    --overwrite

echo "successfully generated and stored tailscale oauth client token"
