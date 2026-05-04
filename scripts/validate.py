#!/usr/bin/env python3
"""
Structural validation for the homelab repository.

Checks:
  1.  All YAML files parse correctly (handles multi-document files)
  2.  LXC install script templates referenced in playbooks exist on disk
  3.  All import_playbook paths in playbooks/ resolve to real files
  4.  All Python inventory files have valid syntax
  5.  No genuinely old/renamed Ansible group names remain ('server', 'agent',
      'hosts: lxc_loki', 'hosts: lxc_tempo')
  6.  All proxmox-community-script callers use pcs_-prefixed variables
  7.  No 'changeme' placeholder values remain in executable code
  8.  ansible_ssh_private_key_file in inventory.py points to a path variable,
      not raw key content
  9.  kubernetes.core.helm_repository tasks do not use a kubeconfig: param
      (that module doesn't support it)
  10. k3s service playbooks targeting k3s_masters or k3s_nodes have
      gather_facts: false

Usage:
  python3 scripts/validate.py   (from repo root)
  make validate
"""

import glob
import os
import py_compile
import re
import sys
import yaml


# Always run relative to the repo root, regardless of where the script is invoked from.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO_ROOT)

SKIP_DIRS = {'.git', 'node_modules', 'dist', '__pycache__'}


def _iter_files(*patterns):
    """Yield file paths matching any of the glob patterns, skipping skip dirs."""
    for pattern in patterns:
        for f in sorted(glob.glob(pattern, recursive=True)):
            parts = set(f.split(os.sep))
            if parts & SKIP_DIRS:
                continue
            yield f


def _read(path):
    return open(path, encoding='utf-8', errors='replace').read()


# ── 1. YAML validity ──────────────────────────────────────────────────────────

def check_yaml_validity():
    issues = []
    for f in _iter_files('**/*.yml', '**/*.yaml'):
        try:
            list(yaml.safe_load_all(_read(f)))
        except yaml.YAMLError as e:
            # Only first line of the error — enough to identify the file/location
            issues.append('  %s: %s' % (f, str(e).split('\n')[0]))
    return issues


# ── 2. LXC install script templates exist ─────────────────────────────────────

def check_lxc_templates():
    issues = []
    for f in _iter_files('services/lxc/**/main.yml'):
        svc_dir = os.path.dirname(f)
        for m in re.finditer(r'script_source:\s*["\']?([^\s"\']+)', _read(f)):
            src = m.group(1)
            full = os.path.join(svc_dir, 'templates', src)
            if not os.path.exists(full):
                issues.append('  %s -> %s (missing)' % (f, full))
    return issues


# ── 3. Playbook import_playbook paths exist ───────────────────────────────────

def check_playbook_imports():
    issues = []
    for f in _iter_files('playbooks/*.yml'):
        base = os.path.dirname(f)
        for m in re.finditer(r'import_playbook:\s*(\S+)', _read(f)):
            path = os.path.normpath(os.path.join(base, m.group(1)))
            if not os.path.exists(path):
                issues.append('  %s -> %s (missing)' % (f, path))
    return issues


# ── 4. Python syntax ──────────────────────────────────────────────────────────

def check_python_syntax():
    issues = []
    for f in _iter_files('inventory/**/*.py'):
        try:
            py_compile.compile(f, doraise=True)
        except py_compile.PyCompileError as e:
            issues.append('  %s: %s' % (f, e))
    return issues


# ── 5. Old group names ────────────────────────────────────────────────────────

def check_old_group_names():
    """
    Detect genuinely obsolete group references.
    Uses line-level checks to avoid false positives on comments or names
    like 'jmpa-server-1' which legitimately contain 'server'.
    """
    issues = []
    # Patterns that indicate actual group usage, not name substrings
    bad_patterns = [
        (r"^\s*hosts:\s+server\s*$",     'hosts: server (old group name)'),
        (r"^\s*hosts:\s+agent\s*$",      'hosts: agent (old group name)'),
        (r"^\s*hosts:\s+lxc_loki\s*$",   'hosts: lxc_loki (old group name)'),
        (r"^\s*hosts:\s+lxc_tempo\s*$",  'hosts: lxc_tempo (old group name)'),
        (r"groups\['server'\]",           "groups['server'] (old group name)"),
        (r"groups\['agent'\]",            "groups['agent'] (old group name)"),
    ]
    for f in _iter_files('services/**/*.yml', 'roles/**/*.yml', 'playbooks/**/*.yml'):
        content = _read(f)
        for pattern, label in bad_patterns:
            for lineno, line in enumerate(content.splitlines(), 1):
                if re.search(pattern, line):
                    issues.append('  %s:%d — %s' % (f, lineno, label))
    return issues


# ── 6. PCS prefix consistency ─────────────────────────────────────────────────

def check_pcs_prefix():
    """
    Proxmox community-script callers must use pcs_-prefixed variables.
    Checks for known unprefixed names at the vars indentation level.
    """
    issues = []
    bad = [
        r'^\s{8}script_url:',
        r'^\s{8}script_name:',
        r'^\s{8}container_id:',
        r'^\s{8}container_hostname:',
        r'^\s{8}container_memory:',
        r'^\s{8}container_cores:',
        r'^\s{8}container_port:',
    ]
    for f in _iter_files('services/proxmox-community-scripts/*.yml'):
        content = _read(f)
        for lineno, line in enumerate(content.splitlines(), 1):
            for pattern in bad:
                if re.match(pattern, line):
                    issues.append('  %s:%d — unprefixed var: %s' % (f, lineno, line.strip()))
    return issues


# ── 7. No 'changeme' in executable code ──────────────────────────────────────

def check_no_changeme():
    issues = []
    for f in _iter_files('inventory/**/*.py', 'services/**/*.yml', 'roles/**/*.yml'):
        for lineno, line in enumerate(_read(f).splitlines(), 1):
            # Skip comments
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('//'):
                continue
            if 'changeme' in line.lower():
                issues.append('  %s:%d — %s' % (f, lineno, stripped[:80]))
    return issues


# ── 8. ansible_ssh_private_key_file is a path variable, not inline content ───

def check_ssh_key_not_inline():
    """
    ansible_ssh_private_key_file must reference a file path, not raw key content.
    A correct value references a variable like ansible_ssh_private_key_file
    or a path string. An incorrect value would be the literal key PEM content.
    """
    issues = []
    for f in _iter_files('inventory/inventory.py'):
        for lineno, line in enumerate(_read(f).splitlines(), 1):
            if 'ansible_ssh_private_key_file' in line and 'BEGIN' in line:
                issues.append('  %s:%d — value looks like raw key content, not a path' % (f, lineno))
    return issues


# ── 9. helm_repository tasks don't use kubeconfig param ──────────────────────

def check_helm_repository_no_kubeconfig():
    """
    kubernetes.core.helm_repository does not support kubeconfig:.
    Only helm, k8s, k8s_info etc. support it.
    """
    issues = []
    for f in _iter_files('services/**/*.yml', 'roles/**/*.yml'):
        content = _read(f)
        # Find helm_repository blocks and check if kubeconfig: appears before the next task
        in_helm_repo = False
        for lineno, line in enumerate(content.splitlines(), 1):
            if 'kubernetes.core.helm_repository:' in line:
                in_helm_repo = True
            elif in_helm_repo:
                # New task starts (- name:) — end of block
                if re.match(r'\s*-\s+name:', line):
                    in_helm_repo = False
                elif re.match(r'\s+kubeconfig:', line):
                    issues.append('  %s:%d — helm_repository does not accept kubeconfig:' % (f, lineno))
                    in_helm_repo = False
    return issues


# ── 10. k3s service playbooks have gather_facts: false ───────────────────────

def check_k3s_gather_facts():
    """
    All k3s service playbooks (deploy-*.yml, configure-*.yml) that target
    k3s_masters or k3s_nodes should declare gather_facts: false — facts are
    not used and the gather adds unnecessary overhead and connection time.
    """
    issues = []
    for f in _iter_files('services/vms/k3s/deploy-*.yml', 'services/vms/k3s/configure-*.yml'):
        content = _read(f)
        # Only check plays that target k3s hosts
        if not re.search(r'hosts:\s+k3s_', content):
            continue
        if 'gather_facts: false' not in content:
            issues.append('  %s — targets k3s hosts but missing gather_facts: false' % f)
    return issues


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    checks = [
        ('YAML validity',                    check_yaml_validity),
        ('LXC script templates',             check_lxc_templates),
        ('Playbook imports',                  check_playbook_imports),
        ('Python syntax',                     check_python_syntax),
        ('Old group names',                   check_old_group_names),
        ('PCS prefix consistency',            check_pcs_prefix),
        ('No changeme in code',               check_no_changeme),
        ('SSH key not inline',                check_ssh_key_not_inline),
        ('helm_repository no kubeconfig',     check_helm_repository_no_kubeconfig),
        ('k3s plays have gather_facts:false', check_k3s_gather_facts),
    ]

    total = 0
    for name, fn in checks:
        try:
            issues = fn()
        except Exception as e:
            issues = ['  ERROR running check: %s' % e]
        if issues:
            print('FAIL [%s]: %d issue(s)' % (name, len(issues)))
            for x in issues:
                print(x)
        else:
            print('OK   [%s]' % name)
        total += len(issues)

    print('\n%s — %d issue(s) found' % ('PASS' if total == 0 else 'FAIL', total))
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())
