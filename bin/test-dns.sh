#!/usr/bin/env bash
# Tests DNS resolution for homelab services via Pi-hole.

set -e

# Funcs.
die() { echo "$1" >&2; exit "${2:-1}"; }

# Check deps.
deps=(dig ping)
missing=()
for dep in "${deps[@]}"; do hash "$dep" 2>/dev/null || missing+=("$dep"); done
if [[ ${#missing[@]} -ne 0 ]]; then
    [[ "${#missing[@]}" -gt 1 ]] && s="s"
    die "Missing dep${s}: ${missing[*]}."
fi

# Vars.
dnsServer="${DNS_SERVER:-10.0.0.2}"
domain="${DNS_DOMAIN:-jmpa.lab}"
testHosts=(
    "grafana"
    "prometheus"
    "uptime-kuma"
    "speedtest"
    "n8n"
    "jellyfin"
)

# Test DNS server reachability.
ping -c 1 -W 2 "$dnsServer" >/dev/null 2>&1 \
    || die "DNS server $dnsServer is not reachable."

echo "Testing DNS resolution via $dnsServer for domain: $domain"
echo "============================================================"

# Test each host.
failed=0
for host in "${testHosts[@]}"; do
    fqdn="${host}.${domain}"
    result=$(dig +short "@$dnsServer" "$fqdn" 2>/dev/null | head -1)

    if [[ -n "$result" ]]; then
        echo "✓ $fqdn -> $result"
    else
        echo "✗ $fqdn -> FAILED"
        ((failed++))
    fi
done

echo "============================================================"

# Test external DNS.
externalResult=$(dig +short "@$dnsServer" "google.com" 2>/dev/null | head -1)
if [[ -n "$externalResult" ]]; then
    echo "✓ External DNS (google.com) -> $externalResult"
else
    echo "✗ External DNS (google.com) -> FAILED"
    ((failed++))
fi

# Summary.
echo ""
if [[ $failed -eq 0 ]]; then
    echo "All DNS tests passed!"
    exit 0
else
    die "$failed DNS test(s) failed."
fi
