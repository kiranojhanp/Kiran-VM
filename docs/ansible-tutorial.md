# Ansible Tutorial for Beginners

Source: [Spacelift — Ansible Tutorial for Beginners](https://spacelift.io/blog/ansible-tutorial)

---

## Table of Contents

1. [What is Ansible?](#what-is-ansible)
2. [Basic Concepts & Terms](#basic-concepts--terms)
3. [How to Install Ansible](#how-to-install-ansible)
4. [Ansible Inventory](#ansible-inventory)
5. [Ansible Ad Hoc Commands](#ansible-ad-hoc-commands)
6. [Intro to Ansible Playbooks](#intro-to-ansible-playbooks)
7. [Using Variables in Playbooks](#using-variables-in-playbooks)
8. [Ansible Roles](#ansible-roles)

---

## What is Ansible?

Ansible is software that enables cross-platform automation and orchestration at scale. It is backed by RedHat and a large open-source community and is considered an excellent option for:

- Configuration management
- Infrastructure provisioning
- Application deployment

Its automation opportunities span hybrid clouds, on-premises infrastructure, and IoT.

### How Ansible Works

Ansible uses the concepts of **control nodes** and **managed nodes**:

- **Control node** — any machine with Ansible installed. This is where you run commands.
- **Managed nodes** — the machines Ansible connects to and configures. No Ansible installation needed on them.

The units of code Ansible executes on managed nodes are called **modules**. Each module is invoked by a **task**, and an ordered list of tasks forms a **playbook**. The managed machines are listed in an **inventory** file.

Ansible uses **YAML** for all configuration, making it human-readable from day one. It requires no extra agents on managed nodes — typically just a terminal and a text editor.

### Key Benefits

- Free and open-source with a large community.
- No extra agents required on managed nodes.
- Easy to learn — no special coding skills needed.
- Idempotent by design — tasks only make changes when needed.
- Extensive official documentation and community resources.

---

## Basic Concepts & Terms

| Term | Description |
|---|---|
| **Host** | A remote machine managed by Ansible. |
| **Group** | Several hosts grouped by a common attribute. |
| **Inventory** | A collection of all hosts and groups Ansible manages. Can be static or dynamic. |
| **Module** | A unit of code Ansible sends to managed nodes for execution. |
| **Task** | A unit of action combining a module, its arguments, and parameters. |
| **Playbook** | An ordered list of tasks defining a recipe to configure a system. |
| **Role** | A redistributable unit of organization for sharing automation code. |
| **YAML** | The simple data format used to write all Ansible configuration files. |

---

## How to Install Ansible

### Requirements

**Control node:**
- Unix-like OS: Linux, macOS, or Windows WSL
- Python 3 available

> Windows *without* WSL is not supported as a native Ansible control node.

**Managed nodes:**
- SSH/SFTP access (Linux/Unix) or WinRM (Windows)
- Python 3 interpreter (for most modules)
- No Ansible installation needed

### Install via pip

Install pip if not already available:
```bash
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py --user
```

Install Ansible:
```bash
python -m pip install --user ansible
```

Verify the installation:
```bash
ansible --version
```

---

## Ansible Inventory

The inventory defines the collection of machines you want to manage. The default location is `/etc/ansible/hosts`, but you can define a custom one in any directory.

### Simple Inventory File (`hosts`)

```ini
host1 ansible_host=127.0.0.1 ansible_user=vagrant ansible_port=2222 ansible_ssh_private_key_file=~/.ssh/host1_key

host2 ansible_host=127.0.0.1 ansible_user=vagrant ansible_port=2200 ansible_ssh_private_key_file=~/.ssh/host2_key
```

Each entry specifies:
- An **alias** (`host1`, `host2`)
- Connection parameters (`ansible_host`, `ansible_user`, `ansible_port`, `ansible_ssh_private_key_file`)

### Inventory with Groups

```ini
[webservers]
webserver1.example.com
webserver2.example.com
192.0.6.45

[databases]
database1.example.com
database2.example.com
```

Two default groups always exist:
- `all` — includes every host.
- `ungrouped` — includes all hosts not in any group.

### ansible.cfg — Configure Default Inventory

To avoid specifying `-i hosts` on every command, create an `ansible.cfg` file in your project directory:

```ini
[defaults]
inventory=./hosts
```

Verify your inventory is parsed correctly:
```bash
ansible-inventory --list
```

---

## Ansible Ad Hoc Commands

Ad hoc commands allow you to run a single task against one or more managed nodes quickly, without writing a playbook. Useful for rebooting servers, copying files, checking connection status, and package management.

### Syntax

```bash
ansible [host-pattern] -m [module] -a "[module options]"
```

| Part | Description |
|---|---|
| `host-pattern` | The hosts or groups to target |
| `-m` | The module to run |
| `-a` | Arguments for the module |

### Examples

**Ping all hosts** (validates inventory and connectivity):
```bash
ansible -i hosts all -m ping
```

**Run a command on a specific host:**
```bash
ansible all -i hosts --limit host2 -a "/bin/echo hello"
```

**Copy a file to all managed nodes:**
```bash
ansible all -i hosts -m ansible.builtin.copy -a "src=./hosts dest=/tmp/hosts"
```

### Idempotency

Most Ansible modules are **idempotent** — they only make changes when needed. Running the `copy` command a second time when the file already exists will succeed without performing any action (shown in green output).

---

## Intro to Ansible Playbooks

Playbooks are reusable, consistent YAML files that automate ordered sets of tasks on managed nodes. Tasks execute **top to bottom**.

### Playbook Structure

At minimum, a playbook defines:
1. The target hosts (`hosts:`)
2. A list of tasks (`tasks:`)

### Example Playbook

```yaml
---
- name: Intro to Ansible Playbooks
  hosts: all

  tasks:
    - name: Copy file with permissions
      ansible.builtin.copy:
        src: ./hosts
        dest: /tmp/hosts_backup
        mode: '0644'

    - name: Add the user 'bob'
      ansible.builtin.user:
        name: bob
      become: yes
      become_method: sudo

    - name: Upgrade all apt packages
      apt:
        force_apt_get: yes
        upgrade: dist
      become: yes
```

### Running a Playbook

```bash
ansible-playbook intro_playbook.yml
```

### Useful Flags

| Flag | Purpose |
|---|---|
| `--syntax-check` | Validate playbook syntax without running it |
| `-C` | Dry run — reports what changes would be made without applying them |
| `--limit host1` | Restrict the run to a specific host or group |

### Playbook Output

At the end of each run, Ansible prints a **PLAY RECAP** summarising results per host:

```
host1   : ok=4    changed=3    unreachable=0    failed=0    skipped=0
host2   : ok=4    changed=3    unreachable=0    failed=0    skipped=0
```

---

## Using Variables in Playbooks

Variables can be defined at multiple levels. The most common method is a `vars` block at the top of the playbook.

Reference variables in tasks using `{{ variable_name }}` (Jinja2 syntax). When a variable value is another variable, wrap it in quotes.

### Example

```yaml
---
- name: Variables playbook
  hosts: all
  vars:
    state: latest
    user: bob

  tasks:
    - name: Add the user {{ user }}
      ansible.builtin.user:
        name: "{{ user }}"

    - name: Upgrade all apt packages
      apt:
        force_apt_get: yes
        upgrade: dist

    - name: Install the {{ state }} version of nginx
      apt:
        name: nginx
        state: "{{ state }}"
```

### Variable Precedence

Ansible chooses which variable to use based on a defined precedence order. Variables can be defined in:
- Playbook `vars` block
- Inventory file
- `group_vars/` and `host_vars/` directories
- Extra vars passed via CLI (`-e`)

CLI extra vars (`-e`) always take the highest precedence.

---

## Ansible Roles

Roles take automation to the next level of abstraction. They provide a **standardized structure** for bundling related tasks, variables, templates, handlers, and files together, making your code DRY and reusable.

In modern Ansible projects, roles often live inside **collections**, which bundle roles, modules, and plugins under a consistent namespace for versioning and distribution.

### Role Directory Structure

```
roles/
  my_role/
    tasks/
      main.yml       # Entry point — list of tasks
    handlers/
      main.yml       # Handlers triggered by notify
    templates/
      config.j2      # Jinja2 templates
    files/
      app.conf       # Static files to copy
    vars/
      main.yml       # Role-level variables
    defaults/
      main.yml       # Default variable values (lowest precedence)
    meta/
      main.yml       # Role metadata and dependencies
```

### Using a Role in a Playbook

```yaml
---
- name: Apply webserver role
  hosts: webservers
  roles:
    - my_role
```

### Why Use Roles?

- Share automation logic between teams, environments, and projects.
- Keep playbooks short and readable.
- Roles from Ansible Galaxy can be installed and reused directly:

```bash
ansible-galaxy install geerlingguy.nginx
```

---

## Quick Reference

### Common Modules

| Module | Purpose |
|---|---|
| `ansible.builtin.ping` | Test connection to hosts |
| `ansible.builtin.copy` | Copy files to managed nodes |
| `ansible.builtin.file` | Manage file and directory attributes |
| `ansible.builtin.user` | Manage user accounts |
| `ansible.builtin.apt` | Manage packages on Debian/Ubuntu |
| `ansible.builtin.yum` | Manage packages on RHEL/CentOS |
| `ansible.builtin.service` | Manage services |
| `ansible.builtin.template` | Deploy Jinja2 templates |
| `ansible.builtin.shell` | Run shell commands |
| `ansible.builtin.command` | Run commands (safer, no shell) |

### Common CLI Commands

```bash
# Check Ansible version
ansible --version

# Ping all hosts
ansible all -m ping

# Run ad hoc command
ansible all -m ansible.builtin.command -a "uptime"

# Run a playbook
ansible-playbook site.yml

# Dry run
ansible-playbook site.yml -C

# Syntax check
ansible-playbook site.yml --syntax-check

# Limit to specific host
ansible-playbook site.yml --limit webserver1

# Pass extra variables
ansible-playbook site.yml -e "user=alice state=present"

# List inventory
ansible-inventory --list

# Install a role from Galaxy
ansible-galaxy install geerlingguy.nginx
```
