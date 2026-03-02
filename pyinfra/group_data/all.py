# Variables shared across all hosts.
# Non-secret vars mirror ansible/group_vars/all.yml.
# Secrets are imported from secrets.py (gitignored) which reads env vars.
# group_data/all.py is the only file auto-loaded by pyinfra for all hosts.

# Import secrets so they are available as host.data.*
try:
    from group_data.secrets import *  # noqa: F401, F403
except ImportError:
    pass  # secrets.py not present; vars will fail at runtime if needed

# ── Server ──────────────────────────────────────────────
deploy_user = "deploy"
ssh_port = 2222
timezone = "UTC"
ssh_allow_port_22 = True

# ── Domain ──────────────────────────────────────────────
domain = "fewa.app"
komodo_subdomain = f"komodo.{domain}"

# ── Komodo ──────────────────────────────────────────────
komodo_port = 9120
komodo_image = "ghcr.io/moghtech/komodo-core:latest"
komodo_periphery_image = "ghcr.io/moghtech/komodo-periphery:latest"
komodo_log_level = "info"
komodo_init_admin_username = "fewaadmin"

# ── FerretDB (MongoDB adapter for Komodo) ───────────────
# FerretDB requires its own patched postgres image — cannot share stock postgres:16.
ferretdb_image = "ghcr.io/ferretdb/ferretdb:latest"
ferretdb_pg_image = "ghcr.io/ferretdb/postgres-documentdb:latest"

# ── Caddy ───────────────────────────────────────────────
# caddy_image intentionally omitted: Caddy uses a build: directive in
# docker-compose to build a custom image via xcaddy (adds Cloudflare DNS module).
caddy_email = f"admin@{domain}"

# ── Paths ───────────────────────────────────────────────
infra_dir = "/opt/infra"
komodo_dir = "/opt/komodo"
caddy_dir = "/opt/caddy"
sure_dir = "/opt/sure"
gitea_dir = "/opt/gitea"
nocodb_dir = "/opt/nocodb"
databasus_dir = "/opt/databasus"

# ── Sure ────────────────────────────────────────────────
sure_subdomain = f"sure.{domain}"
sure_port = 3000

# ── Gitea ───────────────────────────────────────────────
gitea_subdomain = f"git.{domain}"
gitea_http_port = 3001
gitea_ssh_port = 2223
gitea_image = "docker.gitea.com/gitea:latest-rootless"

# ── NocoDB ──────────────────────────────────────────────
nocodb_subdomain = f"nocodb.{domain}"
nocodb_port = 8080
nocodb_image = "nocodb/nocodb:latest"

# ── Databasus ───────────────────────────────────────────
databasus_subdomain = f"backup.{domain}"
databasus_port = 4005
databasus_image = "databasus/databasus:latest"
