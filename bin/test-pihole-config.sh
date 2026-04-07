#!/usr/bin/env bash
# Test script for Pi-hole DNS auto-configuration system
# This validates that the inventory correctly generates DNS records

set -e

echo "=== Pi-hole DNS Configuration Test ==="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Validate inventory generates community_services
echo "Test 1: Validating inventory generates community_services..."
cd inventory
INVENTORY_OUTPUT=$(python3 main.py 2>&1)
INVENTORY_EXIT_CODE=$?

if [ $INVENTORY_EXIT_CODE -ne 0 ]; then
  echo -e "${RED}✗ FAILED${NC} - Inventory script failed to execute"
  echo "$INVENTORY_OUTPUT"
  exit 1
fi

# Check if community_services exists in output
if echo "$INVENTORY_OUTPUT" | jq -e '.all.vars.community_services' > /dev/null 2>&1; then
  echo -e "${GREEN}✓ PASSED${NC} - community_services found in inventory"
else
  echo -e "${RED}✗ FAILED${NC} - community_services not found in inventory"
  exit 1
fi

# Test 2: Validate service IP calculation
echo ""
echo "Test 2: Validating IP calculation for services..."
SERVICES=$(echo "$INVENTORY_OUTPUT" | jq -r '.all.vars.community_services')

# Expected services and their IPs
declare -A EXPECTED_IPS=(
  ["proxmox_backup_server"]="10.0.1.00"
  ["prometheus_community"]="10.0.1.40"
  ["grafana_community"]="10.0.1.45"
  ["ollama"]="10.0.1.50"
)

ALL_PASSED=true
for service_name in "${!EXPECTED_IPS[@]}"; do
  EXPECTED_IP="${EXPECTED_IPS[$service_name]}"
  ACTUAL_IP=$(echo "$SERVICES" | jq -r ".[] | select(.name == \"$service_name\") | .ipv4")

  if [ "$ACTUAL_IP" == "$EXPECTED_IP" ]; then
    echo -e "${GREEN}✓ PASSED${NC} - $service_name: $ACTUAL_IP (expected: $EXPECTED_IP)"
  else
    echo -e "${RED}✗ FAILED${NC} - $service_name: $ACTUAL_IP (expected: $EXPECTED_IP)"
    ALL_PASSED=false
  fi
done

if [ "$ALL_PASSED" = false ]; then
  exit 1
fi

# Test 3: Validate DNS record generation
echo ""
echo "Test 3: Validating DNS record generation..."
DNS_RECORDS=$(echo "$SERVICES" | jq -r '.[].dns_record')

if [ -z "$DNS_RECORDS" ]; then
  echo -e "${RED}✗ FAILED${NC} - No DNS records generated"
  exit 1
fi

# Check each service has proper DNS record
for service_name in "${!EXPECTED_IPS[@]}"; do
  HOSTNAME=$(echo "$SERVICES" | jq -r ".[] | select(.name == \"$service_name\") | .dns_record.hostname")
  SHORT_HOSTNAME=$(echo "$SERVICES" | jq -r ".[] | select(.name == \"$service_name\") | .dns_record.short_hostname")

  if [[ "$HOSTNAME" == *.jmpa.lab ]]; then
    echo -e "${GREEN}✓ PASSED${NC} - $service_name has FQDN: $HOSTNAME"
  else
    echo -e "${RED}✗ FAILED${NC} - $service_name missing FQDN: $HOSTNAME"
    ALL_PASSED=false
  fi

  if [ -n "$SHORT_HOSTNAME" ]; then
    echo -e "${GREEN}✓ PASSED${NC} - $service_name has short hostname: $SHORT_HOSTNAME"
  else
    echo -e "${RED}✗ FAILED${NC} - $service_name missing short hostname"
    ALL_PASSED=false
  fi
done

if [ "$ALL_PASSED" = false ]; then
  exit 1
fi

# Test 4: Validate Pi-hole templates exist
echo ""
echo "Test 4: Validating Pi-hole configuration files exist..."
cd ..

REQUIRED_FILES=(
  "instances/dns/pihole-config/tasks/main.yml"
  "instances/dns/pihole-config/handlers/main.yml"
  "instances/dns/pihole-config/templates/etc/pihole/custom.list.j2"
  "instances/dns/pihole-config/templates/etc/pihole/05-pihole-custom-cname.conf.j2"
  "instances/dns/pihole-config/vars/main.yml"
  "instances/dns/pihole-config/README.md"
)

for file in "${REQUIRED_FILES[@]}"; do
  if [ -f "$file" ]; then
    echo -e "${GREEN}✓ PASSED${NC} - $file exists"
  else
    echo -e "${RED}✗ FAILED${NC} - $file missing"
    ALL_PASSED=false
  fi
done

if [ "$ALL_PASSED" = false ]; then
  exit 1
fi

# Test 5: Validate playbook includes Pi-hole config
echo ""
echo "Test 5: Validating playbook includes Pi-hole configuration..."
if grep -q "instances/dns/pihole-config" playbook.yml; then
  echo -e "${GREEN}✓ PASSED${NC} - playbook.yml includes Pi-hole configuration role"
else
  echo -e "${RED}✗ FAILED${NC} - playbook.yml missing Pi-hole configuration role"
  exit 1
fi

# Test 6: Validate Pi-hole deployment playbook exists
echo ""
echo "Test 6: Validating Pi-hole deployment playbook..."
if [ -f "services/proxmox-community-scripts/pihole.yml" ]; then
  echo -e "${GREEN}✓ PASSED${NC} - Pi-hole deployment playbook exists"
else
  echo -e "${RED}✗ FAILED${NC} - Pi-hole deployment playbook missing"
  exit 1
fi

# Test 7: Validate CommunityScriptService class
echo ""
echo "Test 7: Validating CommunityScriptService class..."
if grep -q "class CommunityScriptService" inventory/service.py; then
  echo -e "${GREEN}✓ PASSED${NC} - CommunityScriptService class exists"
else
  echo -e "${RED}✗ FAILED${NC} - CommunityScriptService class missing"
  exit 1
fi

# Summary
echo ""
echo "=== Test Summary ==="
echo -e "${GREEN}All tests passed!${NC}"
echo ""
echo "Pi-hole DNS auto-configuration system is ready to use."
echo ""
echo "Next steps:"
echo "1. Deploy Pi-hole: ansible-playbook services/proxmox-community-scripts/pihole.yml -i inventory.json"
echo "2. Configure DNS: ansible-playbook playbook.yml -i inventory.json --tags dns"
echo "3. Test DNS: nslookup prometheus.jmpa.lab <dns-server-ip>"
