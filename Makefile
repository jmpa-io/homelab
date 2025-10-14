
# Default PROJECT, if not given by another Makefile.
ifndef PROJECT
PROJECT=homelab
endif

#
# Variables.
#

DOMAIN ?= jmpa.lab
INVENTORY ?= inventory/main.py

#
# Targets.
#

ping-inventory: ## Pings ALL instances in the Ansible inventory.
ping-inventory: $(INVENTORY)
	@ansible all -i $< -m ping

ping-hosts: ## Ping ONLY proxmox_hosts in the Ansible inventory (VPS + Proxmox Hosts)
ping-hosts: $(INVENTORY)
	@ansible proxmox_hosts -i $< -m ping

ping-nas: ## Ping only NAS instances in the Ansible inventory.
ping-nas: $(INVENTORY)
	@ansible nas -i $< -m ping

.PHONY += ping-inventory ping-hosts ping-nas

print-inventory-no-jq: inventory/main.py # Outputs the contents of the dynamic Ansible inventory, without formatting.
	@python $<

print-inventory: inventory/main.py  ## Outputs the contents of the dynamic Ansible inventory.
	@python $< | jq '.'

check-playbook: ## Check the Ansible playbook.
check-playbook: playbook.yml
	ansible-playbook -vvv $< --check \
		--extra-vars root_playbook_directory="$$PWD"

run-playbook: ## Executes the Ansible playbook.
run-playbook: playbook.yml
	ansible-playbook -vv $< \
		--extra-vars root_playbook_directory="$$PWD"

#
# k3s.
#

k3s: ## Does everything related to k3s.
k3s: deploy-k3s

create-k3s-inventory: ## Creates the 'dist/k3s-inventory.json'.
create-k3s-inventory: dist/k3s-inventory.json
dist/k3s-inventory.json: dist
dist/k3s-inventory.json: inventory/main.py
	@python $< | jq 'with_entries(select(.key == "k3s_cluster"))' > $@

ping-k3s-inventory: ## Pings the k3s inventory.
ping-k3s-inventory: dist/k3s-inventory.json
	@ansible server:agent -i $< -m ping

print-k3s-inventory: ## Prints the k3s inventory.
print-k3s-inventory: inventory/main.py
	@python $< | jq 'with_entries(select(.key == "k3s_cluster"))'

print-k3s-inventory-no-jq: # Prints the k3s inventory, without jq formatting.
print-k3s-inventory-no-jq: inventory/main.py
	@python $<

deploy-k3s: ## TODO
deploy-k3s: dist/k3s-inventory.json
	ansible-playbook k3s.orchestration.site -i $<

PHONY += create-k3s-inventory dist/k3s-inventory.json

#
# SSH.
#

# PLEASE NOTE: This MUST be added to PHONY.
SSH_PUBLIC_KEY ?= $$HOME/.ssh/id_ed25519.pub

PHONY += $(SSH_PUBLIC_KEY)

upload-ssh-public-key: ## Uploads your local SSH public key to AWS SSM Parameter Store.
upload-ssh-public-key: $$HOME/.ssh/id_ed25519.pub
	aws ssm put-parameter --name "/homelab/ssh/public-key" --value "file://$<" --type String --overwrite

#
# Cert.
#

$(HOME)/.ssl/private: # Creates the $HOME/.ssl/private directory.
$(HOME)/.ssl/private:
	@mkdir -p $@

$(HOME)/.ssl/certs: # Creates the $HOME/.ssl/certs directory.
	@mkdir -p $@

# The path to the temporary config used by 'openssl' commands.
OPENSSL_CONFIG ?= dist/.openssl.cnf

# The path to the template used to create the temporary config used by 'openssl' commands.
OPENSSL_CONFIG_TEMPLATE ?= .openssl.cnf.template

$(OPENSSL_CONFIG): # Creates the temporary config, using the temporary config template.
$(OPENSSL_CONFIG): $(OPENSSL_CONFIG_TEMPLATE) dist
	@DOMAIN=$(DOMAIN) envsubst < $< > $@

generate-private-key: ## Generates a private self-signed private key.
generate-private-key: $(HOME)/.ssl/private/self-signed.key
$(HOME)/.ssl/private/self-signed.key: $(HOME)/.ssl/private
	openssl genpkey -algorithm RSA -out $@ -pkeyopt rsa_keygen_bits:2048

upload-private-key: ## Uploads the self-signed private key to AWS SSM Parameter Store.
upload-private-key: $(HOME)/.ssl/private/self-signed.key
	aws ssm put-parameter --name "/homelab/ssl/private-key" --value "file://$<" --type SecureString --overwrite

generate-cert: ## Generates a private self-signed cert, using the self-signed private key.
generate-cert: $(HOME)/.ssl/certs/self-signed.crt
$(HOME)/.ssl/certs/self-signed.crt: $(HOME)/.ssl/private/self-signed.key $(HOME)/.ssl/certs $(OPENSSL_CONFIG)
	openssl req -new -x509 \
		-key $< \
		-out $@ \
		-days 3650 \
		-subj "/CN=${DOMAIN}" \
		-extensions req_ext \
		-config $(OPENSSL_CONFIG)

upload-cert: ## Uploads the self-signed cert to AWS SSM Parameter Store.
upload-cert: $(HOME)/.ssl/certs/self-signed.crt
	aws ssm put-parameter --name "/homelab/ssl/cert" --value "file://$<" --type SecureString --overwrite

cert: ## Generates & uploads both a private-key and self-signed cert to AWS SSM Parameter Store.
cert: upload-private-key upload-cert

PHONY += $(HOME)/.ssl/private/self-signed.key \
		 $(HOME)/.ssl/certs/self-signed.crt

#
# Docker.
#

docker: ## Run this project locally inside a Docker container.
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

