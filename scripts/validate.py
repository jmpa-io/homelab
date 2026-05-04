#!/usr/bin/env python3
"""
Structural validation for the homelab repository.

Checks:
  1. All YAML files parse correctly
  2. LXC install script templates referenced in playbooks exist
  3. All import_playbook paths in playbooks/ resolve
  4. All Python inventory files have valid syntax
  5. No old/renamed group names remain in playbooks
  6. All proxmox-community-script callers use pcs_ variable prefix
  7. No 'changeme' placeholder values remain in executable code

Usage:
  python3 scripts/validate.py
  make validate
"""

import glob
import os
import py_compile
import re
import sys
import yaml


def check_yaml_validity():
    issues = []
    for f in sorted(
        glob.glob('**/*.yml', recursive=True) +
        glob.glob('**/*.yaml', recursive=True)
    ):
        if any(x in f for x in ['.git', 'node_modules', 'dist/']):
            continue
        try:
            list(yaml.safe_load_all(open(f)))
        except Exception as e:
            issues.append('  %s: %s' % (f, str(e).split('\n')[0]))
    return issues


def check_lxc_templates():
    issues = []
    for f in glob.glob('services/lxc/**/main.yml', recursive=True):
        svc_dir = os.path.dirname(f)
        for m in re.finditer(r'script_source:\s*(\S+)', open(f).read()):
            src = m.group(1).strip('"\'')
            full = os.path.join(svc_dir, 'templates', src)
            if not os.path.exists(full):
                issues.append('  %s -> %s (missing)' % (f, full))
    return issues


def check_playbook_imports():
    issues = []
    for f in glob.glob('playbooks/*.yml'):
        base = os.path.dirname(f)
        for m in re.finditer(r'import_playbook:\s*(\S+)', open(f).read()):
            path = os.path.normpath(os.path.join(base, m.group(1)))
            if not os.path.exists(path):
                issues.append('  %s -> %s (missing)' % (f, path))
    return issues


def check_python_syntax():
    issues = []
    for f in glob.glob('inventory/**/*.py', recursive=True):
        try:
            py_compile.compile(f, doraise=True)
        except py_compile.PyCompileError as e:
            issues.append('  %s: %s' % (f, e))
    return issues


def check_old_group_names():
    issues = []
    # These are genuinely wrong — not Ansible slice syntax
    old_names = [
        '"server"', "'server'",
        '"agent"',  "'agent'",
        'hosts: lxc_loki',
        'hosts: lxc_tempo',
    ]
    for f in (
        glob.glob('services/**/*.yml', recursive=True) +
        glob.glob('roles/**/*.yml', recursive=True)
    ):
        content = open(f).read()
        for name in old_names:
            if name in content:
                issues.append('  %s: contains old group name "%s"' % (f, name.strip()))
    return issues


def check_pcs_prefix():
    issues = []
    # Unprefixed vars that should now have pcs_ prefix
    unprefixed = [
        '        script_url:',
        '        script_name:',
        '        container_id:',
        '        container_hostname:',
        '        container_memory:',
        '        container_cores:',
        '        container_port:',
    ]
    for f in glob.glob('services/proxmox-community-scripts/*.yml'):
        content = open(f).read()
        for v in unprefixed:
            if v in content:
                issues.append('  %s: unprefixed var "%s"' % (f, v.strip()))
    return issues


def check_no_changeme():
    issues = []
    for f in (
        glob.glob('inventory/**/*.py', recursive=True) +
        glob.glob('services/**/*.yml', recursive=True) +
        glob.glob('roles/**/*.yml', recursive=True)
    ):
        if 'changeme' in open(f).read():
            issues.append('  %s' % f)
    return issues


def main():
    checks = [
        ('YAML validity',              check_yaml_validity),
        ('LXC script templates',       check_lxc_templates),
        ('Playbook imports',           check_playbook_imports),
        ('Python syntax',              check_python_syntax),
        ('Old group names',            check_old_group_names),
        ('PCS prefix consistency',     check_pcs_prefix),
        ('No changeme in code',        check_no_changeme),
    ]

    total = 0
    for name, fn in checks:
        issues = fn()
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
