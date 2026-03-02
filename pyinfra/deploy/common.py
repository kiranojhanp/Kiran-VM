"""
OS hardening deploy module.

Mirrors ansible/roles/common/tasks/main.yml — see that file for rationale
on each step (e.g. why UFW is removed, why /dev/shm is hardened, etc.).

Run from the pyinfra/ directory:
    pyinfra inventory.py deploy/common.py
"""

from pyinfra import host
from pyinfra.facts.files import File
from pyinfra.operations import apt, server, systemd
from utils import tpl

# ── Phase 1: System update ────────────────────────────────────────────────────

# Ubuntu ARM64 packages live on ports.ubuntu.com; the universe repo is not
# always enabled by default on minimal cloud images.
server.shell(
    name="Enable universe repository",
    commands=[
        "add-apt-repository -y universe",
    ],
    _sudo=True,
)

apt.update(
    name="Update apt cache",
    _sudo=True,
)

server.shell(
    name="Upgrade all packages",
    commands=["DEBIAN_FRONTEND=noninteractive apt-get upgrade -y"],
    _sudo=True,
)

apt.packages(
    name="Install base packages",
    packages=[
        "curl",
        "gnupg2",
        "lsb-release",
        "ca-certificates",
        "apt-transport-https",
        "software-properties-common",
        "iptables",
        "iptables-persistent",
        "netfilter-persistent",
        "fail2ban",
        "unattended-upgrades",
        "auditd",
        "audispd-plugins",
        "htop",
        "iotop",
        "nethogs",
        "apparmor",
        "apparmor-utils",
    ],
    _sudo=True,
)

# ── Phase 2: deploy user ──────────────────────────────────────────────────────

server.user(
    name="Create deploy user",
    user=host.data.deploy_user,
    shell="/bin/bash",
    groups=["sudo"],
    # append=True equivalent: pyinfra server.user appends groups by default
    # create_home=True is the default
    present=True,
    _sudo=True,
)

# Set password via chpasswd (plain text → PAM hashes it).
# Ansible uses password_hash('sha512') + the user module; chpasswd -e would
# need a pre-hashed value. Using plain chpasswd is equivalent for our purposes.
server.shell(
    name="Set deploy user password",
    commands=[
        "echo '{user}:{password}' | chpasswd".format(
            user=host.data.deploy_user,
            password=host.data.deploy_password,
        ),
    ],
    _sudo=True,
)

# Push the SSH public key into authorized_keys.
# The key string lives in deploy_ssh_public_key (loaded from DEPLOY_SSH_PUBLIC_KEY env var).
server.shell(
    name="Set up deploy user SSH directory",
    commands=[
        "mkdir -p /home/{user}/.ssh".format(user=host.data.deploy_user),
        "chmod 700 /home/{user}/.ssh".format(user=host.data.deploy_user),
        "chown {user}:{user} /home/{user}/.ssh".format(user=host.data.deploy_user),
    ],
    _sudo=True,
)

server.shell(
    name="Deploy SSH authorized_keys for deploy user",
    commands=[
        # Write key; idempotent — overwrites with the canonical single key each run.
        "echo '{key}' > /home/{user}/.ssh/authorized_keys".format(
            key=host.data.deploy_ssh_public_key,
            user=host.data.deploy_user,
        ),
        "chmod 600 /home/{user}/.ssh/authorized_keys".format(
            user=host.data.deploy_user
        ),
        "chown {user}:{user} /home/{user}/.ssh/authorized_keys".format(
            user=host.data.deploy_user
        ),
    ],
    _sudo=True,
)

# ── Phase 3: SSH hardening ────────────────────────────────────────────────────

# Template vars ssh_port and deploy_user are in host.data and are passed
# automatically to Jinja2 by pyinfra.
tpl(
    name="Configure sshd",
    src="templates/common/sshd_config.j2",
    dest="/etc/ssh/sshd_config",
    mode="600",
    user="root",
    group="root",
    _sudo=True,
)

# Validate config before reloading to avoid locking ourselves out.
server.shell(
    name="Validate sshd config",
    commands=["sshd -t"],
    _sudo=True,
)

systemd.service(
    name="Reload sshd",
    service="ssh",
    reloaded=True,
    _sudo=True,
)

# ── Phase 4: iptables-persistent ─────────────────────────────────────────────
# UFW is NOT used on OCI Ubuntu — UFW's reset flushes OCI's VNIC routing rules.
# See ansible/roles/common/tasks/main.yml for the full rationale.

apt.packages(
    name="Remove UFW (conflicts with OCI networking)",
    packages=["ufw"],
    present=False,
    _sudo=True,
)

# Template vars: ssh_port, ssh_allow_port_22, gitea_ssh_port, komodo_port
# All live in host.data (group_data/all.py) and are passed automatically.
tpl(
    name="Deploy iptables rules",
    src="templates/common/rules.v4.j2",
    dest="/etc/iptables/rules.v4",
    mode="640",
    user="root",
    group="root",
    _sudo=True,
)

systemd.service(
    name="Enable and start netfilter-persistent",
    service="netfilter-persistent",
    enabled=True,
    running=True,
    _sudo=True,
)

server.shell(
    name="Restore iptables rules",
    commands=["netfilter-persistent reload"],
    _sudo=True,
)

# ── Phase 5: Fail2Ban ─────────────────────────────────────────────────────────

# Template var: ssh_port (from host.data)
tpl(
    name="Deploy jail.local",
    src="templates/common/jail.local.j2",
    dest="/etc/fail2ban/jail.local",
    mode="644",
    user="root",
    group="root",
    _sudo=True,
)

systemd.service(
    name="Enable and start fail2ban",
    service="fail2ban",
    enabled=True,
    running=True,
    _sudo=True,
)

systemd.service(
    name="Restart fail2ban (pick up new jail.local)",
    service="fail2ban",
    restarted=True,
    _sudo=True,
)

# ── Phase 6: Unattended upgrades ─────────────────────────────────────────────
# Ansible writes /etc/apt/apt.conf.d/20auto-upgrades directly.
# Using files.put with a string-rendered inline file is awkward; server.shell
# with a heredoc is the simplest equivalent.

server.shell(
    name="Configure unattended-upgrades (20auto-upgrades)",
    commands=[
        r"""cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
EOF""",
        "chmod 644 /etc/apt/apt.conf.d/20auto-upgrades",
    ],
    _sudo=True,
)

# ── Phase 7: sysctl hardening ─────────────────────────────────────────────────

# 99-harden.conf.j2 has no template vars — it is effectively a static file.
tpl(
    name="Deploy sysctl hardening config",
    src="templates/common/99-harden.conf.j2",
    dest="/etc/sysctl.d/99-harden.conf",
    mode="644",
    user="root",
    group="root",
    _sudo=True,
)

server.shell(
    name="Apply sysctl settings",
    commands=["sysctl --system"],
    _sudo=True,
)

# ── Phase 8: /dev/shm hardening ───────────────────────────────────────────────
# Write fstab entry first (makes it persistent across reboots), then remount
# immediately so the restriction is active in the current session.
# Do NOT mount on /run/shm — it is a symlink to /dev/shm and creates a second
# tmpfs overlay that can break containers.

server.shell(
    name="Ensure /dev/shm fstab entry with hardened options",
    commands=[
        # Remove any existing /dev/shm fstab line, then append the hardened one.
        "sed -i '/[[:space:]]\/dev\/shm[[:space:]]/d' /etc/fstab",
        "echo 'tmpfs /dev/shm tmpfs defaults,noexec,nosuid,nodev 0 0' >> /etc/fstab",
    ],
    _sudo=True,
)

server.shell(
    name="Remount /dev/shm with hardened options",
    commands=["mount -o remount,noexec,nosuid,nodev /dev/shm"],
    _sudo=True,
)

# ── Phase 9: Swap ─────────────────────────────────────────────────────────────

swapfile_exists = host.get_fact(File, path="/swapfile")

if not swapfile_exists:
    server.shell(
        name="Create 2 GB swapfile",
        commands=[
            "fallocate -l 2G /swapfile",
            "chmod 600 /swapfile",
            "mkswap /swapfile",
            "swapon /swapfile",
        ],
        _sudo=True,
    )

# Add swap to fstab (idempotent: only add if not already present).
server.shell(
    name="Add swapfile to fstab",
    commands=[
        "grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab",
    ],
    _sudo=True,
)

# ── Phase 10: Timezone, auditd ───────────────────────────────────────────────

server.shell(
    name="Set timezone to UTC",
    commands=["timedatectl set-timezone {tz}".format(tz=host.data.timezone)],
    _sudo=True,
)

systemd.service(
    name="Enable and start auditd",
    service="auditd",
    enabled=True,
    running=True,
    _sudo=True,
)

# ── Phase 11: AppArmor verification ──────────────────────────────────────────
# AppArmor is installed in Phase 1. Verify it is active (matches Ansible's
# aa-status check). We do not fail the run on non-zero rc here — just surface
# the output so the operator can see if AppArmor is not yet active after reboot.

server.shell(
    name="Verify AppArmor is active",
    commands=[
        "aa-status --enabled && echo 'AppArmor: active' || echo 'AppArmor: NOT active (may need reboot)'"
    ],
    _sudo=True,
)

# ── Phase 12: Reboot check ────────────────────────────────────────────────────
# Ansible reboots automatically when /var/run/reboot-required exists.
# pyinfra does not have a built-in reboot+wait handler, so we surface the
# flag and leave the decision to the operator.

server.shell(
    name="Check if reboot is required",
    commands=[
        "if [ -f /var/run/reboot-required ]; then "
        "echo 'REBOOT REQUIRED — run: ssh -p {port} {user}@SERVER sudo reboot'; "
        "cat /var/run/reboot-required.pkgs 2>/dev/null || true; "
        "fi".format(port=host.data.ssh_port, user=host.data.deploy_user),
    ],
    _sudo=True,
)
