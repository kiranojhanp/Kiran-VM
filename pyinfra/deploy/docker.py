"""
Docker CE install — mirrors ansible/roles/docker/tasks/main.yml.
Target: Ubuntu ARM64.
"""

import io
import json

from pyinfra.operations import apt, files, server, systemd

# ── 1. Remove old Docker packages ───────────────────────────────────────────
apt.packages(
    name="Remove old Docker packages",
    packages=["docker", "docker-engine", "docker.io", "containerd", "runc"],
    present=False,
    _sudo=True,
)

# ── 2. Create /etc/apt/keyrings ─────────────────────────────────────────────
files.directory(
    name="Create /etc/apt/keyrings directory",
    path="/etc/apt/keyrings",
    mode="755",
    _sudo=True,
)

# ── 3. Download Docker GPG key ───────────────────────────────────────────────
# Ansible uses get_url with force=false (idempotent skip if file exists).
# We replicate that with a test-then-download shell one-liner.
server.shell(
    name="Download Docker GPG key",
    commands=[
        "test -f /etc/apt/keyrings/docker.asc || curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc",
        "chmod a+r /etc/apt/keyrings/docker.asc",
    ],
    _sudo=True,
)

# ── 4. Add Docker apt repository ─────────────────────────────────────────────
# Ansible dynamically resolves arch (aarch64 → arm64) and distro codename.
# We hard-code arm64 (task spec) and use lsb_release -cs for the codename.
server.shell(
    name="Add Docker apt repository",
    commands=[
        'echo "deb [arch=arm64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list',
    ],
    _sudo=True,
)

# ── 5. Install Docker CE and plugins ─────────────────────────────────────────
apt.packages(
    name="Install Docker CE and plugins",
    packages=[
        "docker-ce",
        "docker-ce-cli",
        "containerd.io",
        "docker-buildx-plugin",
        "docker-compose-plugin",
    ],
    update=True,
    _sudo=True,
)

# ── 6. Enable and start Docker ───────────────────────────────────────────────
systemd.service(
    name="Enable and start Docker",
    service="docker",
    enabled=True,
    running=True,
    _sudo=True,
)

# ── 7. Add users to docker group ─────────────────────────────────────────────
# Ansible uses the 'user' module (ansible.builtin.user) with append=true.
# pyinfra has no direct equivalent; usermod -aG is the standard shell approach.
# `|| true` keeps the step non-fatal if a user doesn't exist on this host.
server.shell(
    name="Add users to docker group",
    commands=[
        "usermod -aG docker ubuntu || true",
        "usermod -aG docker deploy || true",
    ],
    _sudo=True,
)

# ── 8. Configure Docker daemon and restart ───────────────────────────────────
# Ansible uses copy + notify (handler) to restart only on change.
# pyinfra operations are always applied; restart is unconditional here.
daemon_config = {
    "log-driver": "json-file",
    "log-opts": {"max-size": "10m", "max-file": "3"},
    "live-restore": True,
    "userland-proxy": False,
}

files.put(
    name="Configure Docker daemon",
    src=io.StringIO(json.dumps(daemon_config, indent=2)),
    dest="/etc/docker/daemon.json",
    _sudo=True,
)

systemd.service(
    name="Restart Docker after daemon config",
    service="docker",
    restarted=True,
    _sudo=True,
)
