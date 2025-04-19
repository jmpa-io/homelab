
# Default PROJECT, if not given by another Makefile.
ifndef PROJECT
PROJECT=homelab
endif

#
# Variables.
#

DOMAIN ?= jmpa.lab

#
# Targets.
#

ping-inventory: ## Pings the Ansible inventory.
ping-inventory: inventory.*
	ansible all -i $< -m ping

check-playbook: ## Check the Ansible playbook.
check-playbook: playbook.yml
	ansible-playbook -vvv $< --check \
		--extra-vars root_playbook_directory="$$PWD"

run-playbook: ## Executes the Ansible playbook.
run-playbook: playbook.yml
	ansible-playbook -vv $< \
		--extra-vars root_playbook_directory="$$PWD"

cert: ## Generates & uploads both a private-key and self-signed cert to AWS SSM Parameter Store.
cert: upload-private-key upload-cert

#
# Cert.
#

$$HOME/.ssl/private: # Creates the $HOME/.ssl/private directory.
$$HOME/.ssl/private:
	@mkdir -p $@

$$HOME/.ssl/certs: # Creates the $HOME/.ssl/certs directory.
	@mkdir -p $@

generate-private-key: ## Generates a private self-signed private key.
generate-private-key: $$HOME/.ssl/private/self-signed.key
$$HOME/.ssl/private/self-signed.key: $$HOME/.ssl/private
	openssl genpkey -algorithm RSA -out $@ -pkeyopt rsa_keygen_bits:2048

upload-private-key: ## Uploads the self-signed private key to AWS SSM Parameter Store.
upload-private-key: $$HOME/.ssl/private/self-signed.key
	aws ssm put-parameter --name "/homelab/ssl/private-key" --value "file://$<" --type SecureString --overwrite

generate-cert: ## Generates a private self-signed cert, using the self-signed private key.
generate-cert: $$HOME/.ssl/certs/self-signed.crt
$$HOME/.ssl/certs/self-signed.crt: $$HOME/.ssl/private/self-signed.key $$HOME/.ssl/certs
	openssl req -new -x509 -key $< -out $@ -days 3650 -subj "/CN=${DOMAIN}"

upload-cert: ## Uploads the self-signed cert to AWS SSM Parameter Store.
upload-cert: $$HOME/.ssl/certs/self-signed.crt
	aws ssm put-parameter --name "/homelab/ssl/cert" --value "file://$<" --type SecureString --overwrite

#
# Docker.
#

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

