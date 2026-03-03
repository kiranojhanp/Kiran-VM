# kiran-vm

Production server config for `fewa.app` — Ansible provisions the server, Komodo manages app deployments.

## How it works

**Ansible** handles infra concerns (runs once, or when infra changes):
- OS hardening, SSH, iptables, fail2ban, swap, Docker
- Komodo + MongoDB, Caddy reverse proxy
- Shared Postgres + Redis for apps
- Caddy vhosts for each app

**Komodo** handles app deployments (triggered on every push):
- Each app lives in `stacks/<name>/compose.yaml`
- GitHub Actions detects which stack changed and fires the matching Komodo procedure webhook
- Procedure: pull latest repo → deploy stack

## Directory structure

```
kiran-vm/
├── ansible/                  ← server provisioning
│   ├── site.yml              ← master playbook
│   ├── group_vars/all.yml    ← non-secret variables
│   ├── secrets.yml           ← secrets (gitignored)
│   ├── secrets.yml.example   ← template
│   ├── inventory/hosts.ini   ← server inventory
│   └── roles/
│       ├── common/           ← OS hardening
│       ├── docker/           ← Docker CE
│       ├── infra/            ← shared Postgres + Redis
│       ├── komodo/           ← Komodo + MongoDB
│       ├── caddy/            ← reverse proxy
│       ├── sure/
│       ├── nocodb/
│       ├── databasus/
│       └── gitea/
│
├── stacks/                   ← Komodo-managed app stacks
│   ├── sure/compose.yaml
│   ├── nocodb/compose.yaml
│   ├── databasus/compose.yaml
│   ├── gitea/compose.yaml
│   └── n8n/compose.yaml
│
└── .github/workflows/
    └── deploy-stacks.yml     ← path-based selective deploys
```

## Running Ansible

```bash
cd ansible
ansible-playbook site.yml --extra-vars "@secrets.yml" \
  --extra-vars "ansible_become_password=<deploy_password>"
```

Run only specific roles:

```bash
ansible-playbook site.yml --extra-vars "@secrets.yml" \
  --extra-vars "ansible_become_password=<deploy_password>" \
  --tags caddy
```

## Adding a new stack

1. Create `stacks/<name>/compose.yaml` — use `infra_net` external network, bind port to `127.0.0.1`
2. Add a Caddy vhost block in `ansible/roles/caddy/templates/Caddyfile.j2`
3. If it needs Postgres, add a user + database to `ansible/roles/infra/templates/init.sql.j2`
4. Run Ansible with `--tags infra,caddy` to apply
5. In Komodo: create Stack → create Procedure (pull repo + deploy stack) → copy webhook URL
6. Add `KOMODO_WEBHOOK_<NAME>` secret to GitHub
7. Add a filter entry to `.github/workflows/deploy-stacks.yml`

## Secrets

Copy the template and fill in values:

```bash
cp ansible/secrets.yml.example ansible/secrets.yml
```

Secrets are gitignored and never committed. App secrets (DB passwords, API keys) live in Komodo → Settings → Variables, referenced in Stack environments as `[[SECRET_NAME]]`.
