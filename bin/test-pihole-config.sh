#!/usr/bin/env bash
# Tests Pi-hole configuration and DNS functionality.

set -e

# Funcs.
die() { echo "$1" >&2; exit "${2:-1}"; }

# Check deps.
deps=(ssh dig)
missing=()
for dep in "${deps[@]}"; do hash "$dep" 2>/dev/null || missing+=("$dep"); done
if [[ ${#missing[@]} -ne 0 ]]; then
    [[ "${#missing[@]}" -gt 1 ]] && s="s"
    die "Missing dep${s}: ${missing[*]}."
fi

# Vars.
piholeHost="${PIHOLE_HOST:-10.0.0.2}"
piholeUser="${PIHOLE_USER:-pi}"
customListPath="/etc/pihole/custom.list"

# Test SSH connectivity.
ssh -o ConnectTimeout=5 -o BatchMode=yes "${piholeUser}@${piholeHost}" "exit" 2>/dev/null \
    || die "Cannot connect to Pi-hole at ${piholeHost}; Check SSH configuration."

echo "Testing Pi-hole configuration at ${piholeHost}"
echo "============================================================"

# Check if Pi-hole is running.
piholeStatus=$(ssh "${piholeUser}@${piholeHost}" "pihole status" 2>/dev/null || echo "error")
[[ "$piholeStatus" =~ "Pi-hole blocking is enabled" ]] \
    || die "Pi-hole is not running or blocking is disabled."
echo "✓ Pi-hole service is running"

# Check custom DNS list exists.
ssh "${piholeUser}@${piholeHost}" "test -f $customListPath" \
    || die "Custom DNS list not found at $customListPath"
echo "✓ Custom DNS list exists: $customListPath"

# Count custom DNS entries.
entryCount=$(ssh "${piholeUser}@${piholeHost}" "grep -v '^#' $customListPath | grep -v '^$' | wc -l" 2>/dev/null || echo "0")
echo "✓ Custom DNS entries: $entryCount"

# Display custom entries.
echo ""
echo "Custom DNS entries:"
echo "-------------------"
ssh "${piholeUser}@${piholeHost}" "grep -v '^#' $customListPath | grep -v '^$'" 2>/dev/null || echo "(none)"
echo "-------------------"

# Test DNS resolution.
echo ""
echo "Testing DNS resolution:"
testDomain="grafana.jmpa.lab"
result=$(dig +short "@${piholeHost}" "$testDomain" 2>/dev/null | head -1)
if [[ -n "$result" ]]; then
    echo "✓ $testDomain -> $result"
else
    echo "✗ $testDomain -> FAILED (no result)"
fi

echo ""
echo "Pi-hole configuration test complete!"
