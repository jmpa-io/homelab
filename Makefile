
# Default PROJECT, if not given by another Makefile.
ifndef PROJECT
PROJECT=homelab
endif

# Override DEPENDENCIES from Makefile.common.mk — this is an Ansible/Python
# project, not a Go project. We don't need golangci-lint, hadolint, go, etc.
DEPENDENCIES ?= \
	aws \
	ansible \
	ansible-playbook \
	python3 \
	jq

#
# Variables.
#

DOMAIN ?= jmpa.lab
INVENTORY ?= inventory/main.py

# Dashboard token settings.
DASHBOARD_NAMESPACE       ?= kubernetes-dashboard
DASHBOARD_TOKEN_DURATION  ?= 24h
DASHBOARD_SSM_PATH        ?= /homelab/k3s/dashboard-token
KUBECONFIG_PATH           ?= services/vms/k3s/kubeconfig.yaml

# EC2 settings.
EC2_DIR         ?= terraform/ec2
EC2_INSTANCE    ?= jmpa-ec2-1

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
	@python3 $<

print-inventory: inventory/main.py  ## Outputs the contents of the dynamic Ansible inventory.
	@python3 $< | jq '.'

check-playbook: ## Check the Ansible playbook.
check-playbook: playbook.yml
	ansible-playbook -vvv $< --check \
		--extra-vars root_playbook_directory="$$PWD"

run-playbook: ## Executes the Ansible playbook.
run-playbook: playbook.yml
	ansible-playbook -vv $< -f 5 \
		--extra-vars root_playbook_directory="$$PWD"

validate: ## Run structural validation checks on the repository.
validate:
	@python3 scripts/validate.py

.PHONY += validate

#
# k3s.
#

k3s: ## Does everything related to k3s.
k3s: deploy-k3s

create-k3s-inventory: ## Creates the 'dist/k3s-inventory.json'.
create-k3s-inventory: dist/k3s-inventory.json
dist/k3s-inventory.json: dist
dist/k3s-inventory.json: inventory/main.py
	@python3 $< | jq 'with_entries(select(.key == "k3s_cluster"))' > $@

create-inventory: ## Creates the full 'dist/inventory.json'.
create-inventory: dist/inventory.json
dist/inventory.json: dist
dist/inventory.json: inventory/main.py
	@python3 $< > $@

.PHONY += create-k3s-inventory dist/k3s-inventory.json create-inventory dist/inventory.json

#
# Dashboard token rotation.
#

rotate-dashboard-token: ## Rotate the Kubernetes Dashboard token and store it in AWS SSM.
rotate-dashboard-token: ## Duration can be overridden: make rotate-dashboard-token DASHBOARD_TOKEN_DURATION=8h
	@echo "Rotating Kubernetes Dashboard token (duration: $(DASHBOARD_TOKEN_DURATION))..."
	@TOKEN=$$(kubectl --kubeconfig $(KUBECONFIG_PATH) \
		-n $(DASHBOARD_NAMESPACE) \
		create token admin-user --duration=$(DASHBOARD_TOKEN_DURATION)); \
	aws ssm put-parameter \
		--name "$(DASHBOARD_SSM_PATH)" \
		--value "$$TOKEN" \
		--type SecureString \
		--overwrite \
		--region "$$AWS_REGION"; \
	echo ""; \
	echo "Token rotated successfully."; \
	echo "  Duration : $(DASHBOARD_TOKEN_DURATION)"; \
	echo "  SSM path : $(DASHBOARD_SSM_PATH)"; \
	echo ""; \
	echo "Retrieve it at any time with:"; \
	echo "  aws ssm get-parameter --name $(DASHBOARD_SSM_PATH) --with-decryption --query Parameter.Value --output text"

.PHONY += rotate-dashboard-token

#
# SSH.
#

# PLEASE NOTE: This MUST be added to PHONY.
SSH_PUBLIC_KEY ?= $$HOME/.ssh/id_ed25519.pub

PHONY += $(SSH_PUBLIC_KEY)

upload-ssh-public-key: ## Uploads your local SSH public key to AWS SSM Parameter Store.
upload-ssh-public-key: $$HOME/.ssh/id_ed25519.pub
	aws ssm put-parameter --name "/homelab/ssh/public-key" --value "file://$<" --type String --overwrite

upload-ssh-private-key: ## Uploads your local SSH private key to AWS SSM Parameter Store.
upload-ssh-private-key: $$HOME/.ssh/id_ed25519
	aws ssm put-parameter --name "/homelab/ssh/private-key" --value "file://$<" --type SecureString --overwrite

upload-ssh-keys: ## Uploads both SSH public and private keys to AWS SSM Parameter Store.
upload-ssh-keys: upload-ssh-public-key upload-ssh-private-key

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

#
# Proxmox community scripts.
#

COMMUNITY_SCRIPTS_DIR ?= services/proxmox-community-scripts

deploy-pbs: ## Deploy Proxmox Backup Server via community script.
deploy-pbs: dist/inventory.json
	ansible-playbook $(COMMUNITY_SCRIPTS_DIR)/proxmox-backup-server.yml \
		-i $< --extra-vars "root_playbook_directory=$$PWD"

deploy-ollama: ## Deploy Ollama via community script.
deploy-ollama: dist/inventory.json
	ansible-playbook $(COMMUNITY_SCRIPTS_DIR)/ollama.yml \
		-i $< --extra-vars "root_playbook_directory=$$PWD"

deploy-uptime-kuma: ## Deploy Uptime Kuma via community script.
deploy-uptime-kuma: dist/inventory.json
	ansible-playbook $(COMMUNITY_SCRIPTS_DIR)/uptime-kuma.yml \
		-i $< --extra-vars "root_playbook_directory=$$PWD"

deploy-speedtest: ## Deploy LibreSpeed speedtest via community script.
deploy-speedtest: dist/inventory.json
	ansible-playbook $(COMMUNITY_SCRIPTS_DIR)/speedtest.yml \
		-i $< --extra-vars "root_playbook_directory=$$PWD"

deploy-n8n: ## Deploy n8n via community script.
deploy-n8n: dist/inventory.json
	ansible-playbook $(COMMUNITY_SCRIPTS_DIR)/n8n.yml \
		-i $< --extra-vars "root_playbook_directory=$$PWD"

.PHONY += deploy-pbs deploy-ollama deploy-uptime-kuma deploy-speedtest deploy-n8n

---: ## ---

#
# EC2. ## Provision the EC2 fleet member via Terraform.
provision-ec2:
	@echo "Initialising Terraform..."
	@cd $(EC2_DIR) && terraform init
	@echo ""
	@echo "Planning..."
	@cd $(EC2_DIR) && terraform plan -out=tfplan
	@echo ""
	@echo "Applying..."
	@cd $(EC2_DIR) && terraform apply tfplan
	@echo ""
	@echo "Done. Uncomment the EC2 block in inventory/main.py then run: make configure-ec2"

destroy-ec2: ## Destroy the EC2 fleet member (WARNING: irreversible).
destroy-ec2:
	@echo "WARNING: This will destroy the EC2 instance and release the Elastic IP."
	@read -p "Type 'yes' to confirm: " confirm && [ "$$confirm" = "yes" ] || exit 1
	@cd $(EC2_DIR) && terraform destroy

configure-ec2: ## Configure the EC2 fleet member via Ansible.
configure-ec2: dist/inventory.json
	ansible-playbook services/ec2/configure.yml \
		-i $< \
		--extra-vars "root_playbook_directory=$$PWD"

configure-k3s-storage: ## Configures NFS storage class on the k3s cluster (requires full inventory).
configure-k3s-storage: dist/inventory.json
	ansible-playbook services/vms/k3s/configure-storage.yml \
		-i $< \
		--extra-vars "root_playbook_directory=$$PWD"

deploy-k3s-media-volumes: ## Deploys NFS media volumes to k3s (requires full inventory for NAS group).
deploy-k3s-media-volumes: dist/inventory.json
	ansible-playbook services/vms/k3s/deploy-media-volumes.yml \
		-i $< \
		--extra-vars "root_playbook_directory=$$PWD"

.PHONY += configure-k3s-storage deploy-k3s-media-volumes

#
# Cloud Proxmox VPS.
#

provision-vps: ## Bootstrap Proxmox VE on a fresh Debian cloud VPS + connect via Tailscale.
provision-vps: ## Usage: make provision-vps VPS_IP=<ip>
provision-vps:
	@test -n "$(VPS_IP)" || (echo "ERROR: VPS_IP is required. Usage: make provision-vps VPS_IP=1.2.3.4" && exit 1)
	ansible-playbook services/vps/provision-vps.yml \
		-i "$(VPS_IP)," \
		--extra-vars "ansible_host=$(VPS_IP) target_host=$(VPS_IP)" \
		--extra-vars "root_playbook_directory=$$PWD"

.PHONY += provision-vps

---: ## ---

# Includes the common Makefile.
# NOTE: this recursively goes back and finds the `.git` directory and assumes
# this is the root of the project. This could have issues when this assumtion
# is incorrect.ory.yml as an inventory source
include $(shell while [[ ! -d .git ]]; do cd ..; done; pwd)/Makefile.common.mk

# ── Post-include additions ────────────────────────────────────────────────────
# Ansible/YAML/structural linting hooks into the lint chain after the include.
# lint-docker is the last sub-target in common lint — we append our checks
# so they run as part of 'make lint' without duplicating any targets.

lint-ansible: ## Runs Ansible/YAML/structural validation.
lint-ansible:
	@echo "Running structural validation..."
	@python3 scripts/validate.py
	@echo ""
	@echo "Running YAML lint..."
	@yamllint -c .yamllint roles/ services/ playbooks/ || true
	@echo ""
	@echo "Running Ansible lint..."
	@ansible-lint --offline playbook.yml || true

lint: lint-ansible

.PHONY += lint-ansible


