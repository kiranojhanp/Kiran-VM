.PHONY: help infra.sync infra.stack-init infra.preview infra.up infra.down ansible.inventory ansible.bootstrap ansible.provision

STACK ?= kiran-prod

help:
	@printf "Targets:\n"
	@printf "  infra.sync        Install infra dependencies (uv sync)\n"
	@printf "  infra.stack-init  Initialize Pulumi stack (STACK=<name>)\n"
	@printf "  infra.preview     Preview infra changes\n"
	@printf "  infra.up          Provision/update VM\n"
	@printf "  infra.down        Destroy VM and network\n"
	@printf "  ansible.inventory Generate ansible/inventory/hosts.ini from Pulumi output\n"
	@printf "  ansible.bootstrap First-run SSH hardening bootstrap (22 -> hardened port)\n"
	@printf "  ansible.provision Run full server provisioning playbook\n"

infra.sync:
	uv --directory infra sync

infra.stack-init:
	pulumi --cwd infra stack init $(STACK)

infra.preview:
	pulumi --cwd infra preview

infra.up:
	pulumi --cwd infra up

infra.down:
	pulumi --cwd infra down

ansible.inventory:
	./ansible/inventory/generate.sh

ansible.bootstrap:
	./ansible/bootstrap.sh

ansible.provision:
	ansible-playbook -i ansible/inventory/hosts.ini ansible/site.yml --extra-vars "@ansible/secrets.yml" --extra-vars "ansible_become_password={{ deploy_password }}"
