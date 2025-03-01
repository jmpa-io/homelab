
# Default PROJECT, if not given by another Makefile.
ifndef PROJECT
PROJECT=homelab
endif

# Targets.
ping-inventory: ## Pings the Ansible inventory.
ping-inventory: inventory.yml
	ansible all -i $< -m ping

run-playbook: ## Executes the Ansible playbook.
run-playbook: playbook.yml
	ansible-playbook $<

---: ## ---

# Includes the common Makefile.
# NOTE: this recursively goes back and finds the `.git` directory and assumes
# this is the root of the project. This could have issues when this assumtion
# is incorrect.ory.yml as an inventory source
include $(shell while [[ ! -d .git ]]; do cd ..; done; pwd)/Makefile.common.mk

