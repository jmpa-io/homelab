
# Default PROJECT, if not given by another Makefile.
ifndef PROJECT
PROJECT=homelab
endif

# Targets.
ping-inventory: ## Pings the Ansible inventory.
ping-inventory: inventory.*
	ansible all -i $< -m ping

check-playbook: ## Check the Ansible playbook.
check-playbook: playbook.yml
	ansible-playbook -vv $< --check \
		--extra-vars root_playbook_directory="$$PWD"

run-playbook: ## Executes the Ansible playbook.
run-playbook: playbook.yml
	ansible-playbook -vv $< \
		--extra-vars root_playbook_directory="$$PWD"

docker: ## Run this project locally inside a docker container.
docker: image-root
	# TODO: remove 'CI=true' when the Makefile.common.mk is refactored.
	docker run -it --network host \
		-v "$(PWD):/app" \
		-v "$(HOME)/.aws:/root/.aws" \
		-v "$(HOME)/.ssh:/root/.ssh" \
		-e "AWS_REGION=$(AWS_REGION)" \
		-e "AWS_PROFILE=jmpa" \
		-e "MITOGEN_STRATEGY_PATH=/usr/local/lib/python3.13/site-packages/ansible_mitogen/plugins/strategy/" \
		-e "ANSIBLE_STRATEGY_PLUGINS=/usr/local/lib/python3.13/site-packages/ansible_mitogen/plugins/strategy/" \
		-e "CI=true" \
		"$(PROJECT)" bash

---: ## ---

# Includes the common Makefile.
# NOTE: this recursively goes back and finds the `.git` directory and assumes
# this is the root of the project. This could have issues when this assumtion
# is incorrect.ory.yml as an inventory source
include $(shell while [[ ! -d .git ]]; do cd ..; done; pwd)/Makefile.common.mk

