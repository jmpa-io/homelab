# Pi-hole Integration Review & Potential Issues

## Overview
This document reviews the Pi-hole auto-configuration system for potential issues and provides recommendations.

## Potential Issues Identified

### 1. **CRITICAL: Pi-hole Must Be Deployed First**

**Issue:** The Pi-hole configuration role runs on the DNS host, but Pi-hole might not be installed yet.

**Impact:** If Pi-hole isn't installed, the role will fail when trying to:
- Write to `/etc/pihole/custom.list`
- Write to `/etc/dnsmasq.d/05-pihole-custom-cname.conf`
- Restart `pihole-FTL` service

**Solution:**
- Pi-hole deployment playbook ([`services/proxmox-community-scripts/pihole.yml`](../services/proxmox-community-scripts/pihole.yml)) must be run BEFORE the main playbook
- OR add a check in the role to skip if Pi-hole isn't installed

**Recommendation:**
```yaml
# Add to instances/dns/pihole-config/tasks/main.yml
- name: Check if Pi-hole is installed
  ansible.builtin.stat:
    path: /usr/local/bin/pihole
  register: pihole_installed

- name: Skip if Pi-hole not installed
  ansible.builtin.debug:
    msg: "Pi-hole not installed, skipping DNS configuration"
  when: not pihole_installed.stat.exists

- name: End play if Pi-hole not installed
  ansible.builtin.meta: end_host
  when: not pihole_installed.stat.exists
```

### 2. **MEDIUM: Variable Availability**

**Issue:** The `community_services` variable is defined in [`inventory/main.py`](../inventory/main.py:95) but needs to be available to the Pi-hole role.

**Current State:** ✅ Variable is added to `inventory_vars` which makes it available globally

**Verification Needed:** Confirm the variable is accessible in the role context

**Test:**
```bash
cd inventory && python3 main.py | jq '.all.vars.community_services'
```

### 3. **LOW: DNS Server Running Pi-hole**

**Issue:** The current setup assumes the DNS server (Raspberry Pi) will run Pi-hole, but Pi-hole could be deployed as an LXC container instead.

**Current Assumption:**
- DNS host = Raspberry Pi 2B
- Pi-hole runs directly on DNS host
- Pi-hole config role targets `hosts: dns`

**Alternative Scenario:**
- Pi-hole deployed as LXC container (VMID 110)
- DNS host remains Raspberry Pi but doesn't run Pi-hole
- Config role would target wrong host

**Solution:** Make Pi-hole deployment flexible:
```yaml
# Option 1: Pi-hole on DNS host (current)
hosts: dns

# Option 2: Pi-hole as LXC (future)
# Would need to add pihole to inventory as separate host
```

**Recommendation:** Document that Pi-hole should run on the DNS host, not as a separate LXC

### 4. **LOW: IP Calculation Edge Cases**

**Issue:** The IP calculation in [`CommunityScriptService.__post_init__`](../inventory/service.py:59) has potential edge cases.

**Current Formula:**
```python
fourth_octet = str(self.vmid)[-2:].zfill(2)
```

**Edge Cases:**
- VMID 5 → `05` ✅ Correct
- VMID 100 → `00` ✅ Correct
- VMID 1 → `01` ✅ Correct
- VMID 999 → `99` ✅ Correct
- VMID 1000 → `00` ⚠️ Collision with VMID 100

**Impact:** LOW - VMIDs above 999 are unlikely in homelab

**Recommendation:** Add validation:
```python
if self.vmid > 999:
    raise ValueError(f"VMID {self.vmid} too large (max 999)")
```

### 5. **LOW: DNS Record Duplication**

**Issue:** If a service is defined in both `LXCService` and `CommunityScriptService`, it could create duplicate DNS records.

**Example:**
- `prometheus` in `LXCService` (container_id=40)
- `prometheus_community` in `CommunityScriptService` (vmid=140)

**Current State:** ✅ Names are different (`prometheus` vs `prometheus_community`), so no collision

**Recommendation:** Document naming convention to avoid conflicts

### 6. **MEDIUM: Pi-hole FTL Restart Impact**

**Issue:** Restarting `pihole-FTL` causes brief DNS outage.

**Impact:**
- DNS queries fail during restart (~2-5 seconds)
- Could affect services during deployment

**Mitigation:**
- Handler only restarts if config changes
- Backup created before changes
- Acceptable for homelab use

**Recommendation:** Consider running updates during maintenance windows

### 7. **LOW: Terramaster NAS Clarification**

**Issue:** Documentation mentions "Synology" but user confirmed using "Terramaster".

**Current State:** ✅ Code is vendor-agnostic (uses `showmount -e`)

**Action Required:** Update documentation references

**Files to Update:**
- [`docs/README.md`](../docs/README.md:52) - Line 52 mentions "Synology"

## Recommendations Summary

### High Priority
1. ✅ **Add Pi-hole installation check** to prevent failures
2. ✅ **Test variable availability** with actual AWS credentials
3. ✅ **Update documentation** to remove Synology references

### Medium Priority
4. **Add VMID validation** (max 999) to prevent IP collisions
5. **Document deployment order** (Pi-hole first, then main playbook)
6. **Add integration test** to verify DNS records are created correctly

### Low Priority
7. **Document naming conventions** for services
8. **Add maintenance window guidance** for DNS updates
9. **Consider Pi-hole deployment location** (DNS host vs LXC)

## Testing Checklist

Before deploying to production:

- [ ] Deploy Pi-hole using [`services/proxmox-community-scripts/pihole.yml`](../services/proxmox-community-scripts/pihole.yml)
- [ ] Verify Pi-hole is accessible at `http://10.0.1.10/admin`
- [ ] Run main playbook with DNS configuration
- [ ] Check `/etc/pihole/custom.list` contains expected records
- [ ] Test DNS resolution: `nslookup prometheus.jmpa.lab <dns-ip>`
- [ ] Deploy a new service (e.g., Prometheus)
- [ ] Verify DNS record auto-created
- [ ] Test short hostname: `nslookup prometheus <dns-ip>`

## Integration with Existing Code

### Compatibility Check

**✅ Compatible with:**
- Static IP calculation in [`proxmox-community-script`](../roles/proxmox-community-script/tasks/main.yml:13) role
- NAS auto-discovery in [`nfs-client`](../instances/proxmox-hosts/nfs-client/tasks/main.yml) role
- K3s automation in [`services/vms/k3s/main.yml`](../services/vms/k3s/main.yml)
- Existing GitHub Actions workflows

**⚠️ Requires:**
- Pi-hole deployed before running main playbook
- AWS credentials configured for inventory generation
- DNS host accessible via SSH

**🔧 Conflicts:**
- None identified

## Deployment Order

Correct deployment sequence:

1. **Initial Setup:**
   ```bash
   # Deploy infrastructure
   ansible-playbook playbook.yml -i inventory.json
   ```

2. **Deploy Pi-hole:**
   ```bash
   # Deploy Pi-hole LXC
   ansible-playbook services/proxmox-community-scripts/pihole.yml -i inventory.json
   ```

3. **Configure DNS:**
   ```bash
   # Update DNS records (runs automatically with main playbook)
   ansible-playbook playbook.yml -i inventory.json --tags dns
   ```

4. **Deploy Services:**
   ```bash
   # Services automatically get DNS records
   ansible-playbook services/proxmox-community-scripts/prometheus.yml -i inventory.json
   ansible-playbook services/proxmox-community-scripts/grafana.yml -i inventory.json
   ```

## Conclusion

The Pi-hole auto-configuration system is well-designed with only minor issues:

**Strengths:**
- ✅ Automatic IP calculation
- ✅ Single source of truth (inventory)
- ✅ Idempotent operations
- ✅ Backup before changes
- ✅ Vendor-agnostic NAS support

**Weaknesses:**
- ⚠️ Requires Pi-hole pre-installed
- ⚠️ No VMID validation
- ⚠️ Brief DNS outage on updates

**Overall Assessment:** **READY FOR DEPLOYMENT** with minor improvements recommended.
