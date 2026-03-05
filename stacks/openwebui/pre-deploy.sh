#!/bin/sh
# Komodo Pre Deploy script for openwebui stack.
# Copies the stable .env (written by Ansible, survives git pull) into the
# compose working directory before docker compose up runs.
set -e
cp /opt/openwebui/.env /opt/komodo/periphery/repos/kiran-vm/stacks/openwebui/.env
