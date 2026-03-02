"""
Gitea stack deploy — mirrors ansible/roles/gitea/tasks/main.yml.
Gitea runs rootless (uid 1000); data and config dirs must be owned by 1000:1000.
Static custom templates are uploaded via files.put.
"""

from pyinfra.operations import files, server
from utils import tpl

# ── 1. Create top-level gitea directory (deploy-owned) ───────────────────────
files.directory(
    name="Create directory /opt/gitea",
    path="/opt/gitea",
    present=True,
    user="deploy",
    group="deploy",
    mode="750",
    _sudo=True,
)

# ── 2. Create data and config directories (uid 1000 for rootless container) ──
for path in ["/opt/gitea/data", "/opt/gitea/config"]:
    files.directory(
        name=f"Create directory {path} (uid 1000)",
        path=path,
        present=True,
        user="1000",
        group="1000",
        mode="750",
        _sudo=True,
    )

# ── 3. Create custom templates directories (uid 1000) ────────────────────────
for path in [
    "/opt/gitea/data/custom",
    "/opt/gitea/data/custom/templates",
    "/opt/gitea/data/custom/templates/custom",
]:
    files.directory(
        name=f"Create directory {path} (uid 1000)",
        path=path,
        present=True,
        user="1000",
        group="1000",
        mode="750",
        _sudo=True,
    )

# ── 4. Upload custom home template (redirect / → /explore) ───────────────────
files.put(
    name="Upload home.tmpl",
    src="templates/gitea/files/custom/templates/home.tmpl",
    dest="/opt/gitea/data/custom/templates/home.tmpl",
    user="1000",
    group="1000",
    _sudo=True,
)

# ── 5. Upload custom header CSS template ─────────────────────────────────────
files.put(
    name="Upload header.tmpl",
    src="templates/gitea/files/custom/templates/custom/header.tmpl",
    dest="/opt/gitea/data/custom/templates/custom/header.tmpl",
    user="1000",
    group="1000",
    _sudo=True,
)

# ── 6. Template docker-compose.yml ───────────────────────────────────────────
tpl(
    name="Template gitea docker-compose.yml",
    src="templates/gitea/docker-compose.yml.j2",
    dest="/opt/gitea/docker-compose.yml",
    _sudo=True,
)

# ── 7. Template .env (mode 600 — contains secrets) ───────────────────────────
tpl(
    name="Template gitea .env",
    src="templates/gitea/gitea.env.j2",
    dest="/opt/gitea/.env",
    mode="600",
    _sudo=True,
)

# ── 8. Pull images and start stack ───────────────────────────────────────────
server.shell(
    name="Start gitea stack",
    commands=[
        "docker compose -f /opt/gitea/docker-compose.yml pull",
        "docker compose -f /opt/gitea/docker-compose.yml up -d",
    ],
    _sudo=True,
)
