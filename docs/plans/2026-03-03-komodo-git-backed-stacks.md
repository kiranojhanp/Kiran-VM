# Plan: Komodo Git-Backed Stacks + Auto-Deploy via Gitea Webhooks

**Date:** 2026-03-03  
**Goal:** Replace Ansible-managed compose files for Sure, Gitea, NocoDB, and Databasus with plain `compose.yaml` files stored in `stacks/` in this repo. Komodo pulls from Gitea (which mirrors GitHub) and auto-deploys on every push.

---

## Architecture

```
Push to GitHub (primary)
    │
    └──► Gitea mirror (git.fewa.app) ──webhook──► Komodo Stack
                                                       │
                                              pulls repo + redeploys
                                                       │
                                            container on /opt/<service>/
```

**Ansible continues to manage:** `komodo`, `caddy`, `infra`, `common`, `docker`  
**Komodo will manage:** `sure`, `nocodb`, `databasus`, `gitea`

---

## Task 1: Ansible — Komodo improvements

### 1a. `KOMODO_RESOURCE_POLL_INTERVAL`

**`ansible/group_vars/all.yml`** — add:
```yaml
komodo_resource_poll_interval: 3600
```

**`ansible/roles/komodo/templates/komodo.env.j2`** — add after `KOMODO_INIT_ADMIN_PASSWORD`:
```
KOMODO_RESOURCE_POLL_INTERVAL={{ komodo_resource_poll_interval }}
```

### 1b. Periphery: `komodo.skip` label + `DOCKER_DATA` env

**`ansible/roles/komodo/templates/docker-compose.yml.j2`** — add to `periphery` service:

```yaml
    labels:
      komodo.skip: "true"
    environment:
      PERIPHERY_ROOT_DIRECTORY: "{{ komodo_dir }}/periphery"
      PERIPHERY_INCLUDE_DISK_MOUNTS: "/,/mnt,/opt"
      PERIPHERY_SSL_ENABLED: "false"
      DOCKER_DATA: "/opt"
```

`komodo.skip` prevents Komodo from trying to restart/stop its own agent container.  
`DOCKER_DATA=/opt` matches our existing bind mount prefix so stacks using `$DOCKER_DATA/<service>-data` work correctly.

### 1c. `dex.sh` — container exec utility

**New file: `ansible/roles/common/templates/dex.sh.j2`**

```bash
#!/bin/bash

# Fuzzy search for container by name, exec into it
# Usage: dex PARTIAL_NAME [SHELL:-sh]
# Examples:
#   dex sure        → execs into sure container with sh
#   dex sure bash   → execs with bash
#   dex test        → if multiple matches, lists all; uses exact match if found

if [[ -z "$1" ]]; then
  printf "Usage: CONTAINER_FUZZY_NAME [SHELL_CMD:-sh]\n"
else

  names=$(docker ps --filter name=^/.*$1.*$ --format '{{.Names}}')
  lines=$(echo -n "$names" | grep -c '^')
  name=""

  if [ "$lines" -eq "0" ]; then
    printf "No container found\n"

  elif [ "$lines" -gt "1" ]; then
    while IFS= read -r line
    do
      printf "Found: %s\n" "$line"
      if [ "$line" = "$1" ]; then
        name="$1"
      fi
    done < <(printf '%s\n' "$names")

    if [[ -z "$name" ]]; then
      printf "More than one container found, be more specific\n"
    else
      printf "More than one container found but input matched one perfectly.\n"
    fi

  else
    name="$names"
    printf "Found: %s\n" "$name"
  fi

  if [[ -n "$name" ]]; then
    docker container exec -it $name ${2:-sh}
  fi

fi
```

**`ansible/roles/common/tasks/main.yml`** — add tasks after the deploy user phase (after the `authorized_key` task, before the SSH hardening phase):

```yaml
- name: Create ~/.local/bin for deploy user
  ansible.builtin.file:
    path: "/home/{{ deploy_user }}/.local/bin"
    state: directory
    owner: "{{ deploy_user }}"
    group: "{{ deploy_user }}"
    mode: "0755"

- name: Deploy dex container exec utility
  ansible.builtin.template:
    src: dex.sh.j2
    dest: "/home/{{ deploy_user }}/.local/bin/dex"
    owner: "{{ deploy_user }}"
    group: "{{ deploy_user }}"
    mode: "0755"

- name: Ensure ~/.local/bin is on PATH in .bashrc
  ansible.builtin.lineinfile:
    path: "/home/{{ deploy_user }}/.bashrc"
    line: 'export PATH="$HOME/.local/bin:$PATH"'
    state: present
    create: false
```

---

## Task 2: Ansible — Gitea webhook allowlist

**`ansible/roles/gitea/templates/gitea.env.j2`** — add at the end:
```
# ── Webhooks ──────────────────────────────────────────────────────────────────
GITEA__webhook__ALLOWED_HOST_LIST={{ komodo_subdomain }}
```

This allows Gitea to send webhook requests to `komodo.fewa.app`. Without this line, Gitea silently blocks outbound webhooks to non-allowlisted hosts.

---

## Task 3: New `stacks/` directory — plain compose files

Create a `stacks/<service>/compose.yaml` for each migrated service. These are **plain YAML** (no Jinja2). All Jinja2 template vars are replaced with literal values. Secrets come from Komodo Variables (referenced as `[[SECRET_NAME]]` in Komodo Stack Environment, which then become `${VAR}` in compose interpolation).

### Jinja2 → literal substitutions

| Template var              | Literal value                              |
|---------------------------|--------------------------------------------|
| `{{ sure_port }}`         | `3000`                                     |
| `{{ nocodb_image }}`      | `nocodb/nocodb:latest`                     |
| `{{ nocodb_port }}`       | `8080`                                     |
| `{{ nocodb_dir }}/data`   | `/opt/nocodb/data`                         |
| `{{ databasus_image }}`   | `databasus/databasus:latest`               |
| `{{ databasus_port }}`    | `4005`                                     |
| `{{ databasus_dir }}/data`| `/opt/databasus/data`                      |
| `{{ gitea_image }}`       | `docker.gitea.com/gitea:latest-rootless`   |
| `{{ gitea_http_port }}`   | `3001`                                     |
| `{{ gitea_ssh_port }}`    | `2223`                                     |
| `{{ gitea_dir }}/data`    | `/opt/gitea/data`                          |
| `{{ gitea_dir }}/config`  | `/opt/gitea/config`                        |

### Komodo Variables (Settings > Variables, marked secret)

These must be created manually in Komodo UI once after initial deploy:

| Komodo Variable Name    | Source Ansible Secret               | Used by       |
|-------------------------|-------------------------------------|---------------|
| `SURE_DB_PASSWORD`      | `shared_postgres_sure_password`     | Sure          |
| `SURE_SECRET_KEY_BASE`  | `sure_secret_key_base`              | Sure          |
| `OPENAI_ACCESS_TOKEN`   | `openai_access_token`               | Sure          |
| `NOCODB_DB_PASSWORD`    | `shared_postgres_nocodb_password`   | NocoDB        |
| `NOCODB_JWT_SECRET`     | `nocodb_jwt_secret`                 | NocoDB        |
| `DATABASUS_SECRET_KEY`  | `databasus_secret_key`              | Databasus     |
| `R2_ACCESS_KEY_ID`      | `r2_access_key_id`                  | Databasus     |
| `R2_SECRET_ACCESS_KEY`  | `r2_secret_access_key`              | Databasus     |
| `GITEA_DB_PASSWORD`     | `shared_postgres_gitea_password`    | Gitea         |
| `GITEA_SECRET_KEY`      | `gitea_secret_key`                  | Gitea         |

### `stacks/sure/compose.yaml`

The existing template is almost git-ready — the image is already a literal. Only one change: replace `{{ sure_port }}` with `3000`.

Komodo Stack Environment for Sure:
```
SECRET_KEY_BASE=[[SURE_SECRET_KEY_BASE]]
POSTGRES_PASSWORD=[[SURE_DB_PASSWORD]]
OPENAI_ACCESS_TOKEN=[[OPENAI_ACCESS_TOKEN]]
SELF_HOSTED=true
RAILS_FORCE_SSL=false
RAILS_ASSUME_SSL=true
POSTGRES_USER=sure_user
POSTGRES_DB=sure_production
DB_HOST=postgres
DB_PORT=5432
REDIS_URL=redis://redis:6379/2
```

### `stacks/nocodb/compose.yaml`

Replace three Jinja2 vars with literals. Move the env vars (currently in `.env.j2`) into Komodo Stack Environment:

```
NC_DB=pg://postgres:5432?u=nocodb_user&p=[[NOCODB_DB_PASSWORD]]&d=nocodb
NC_AUTH_JWT_SECRET=[[NOCODB_JWT_SECRET]]
NC_PUBLIC_URL=https://nocodb.fewa.app
NC_DISABLE_TELE=true
```

The compose file uses `env_file: .env` today — switch to `environment:` block using `${VAR}` for secrets so Komodo can inject them, OR remove `env_file` and use Komodo's Stack Environment directly (Komodo injects vars into the compose env).

> **Note:** Komodo Stack Environment vars are passed as environment variables to the `docker compose` command, making them available for `${VAR}` interpolation in compose files. For service-level env vars (passed into the container), they must appear in the `environment:` block of the service using `${VAR}` syntax.

### `stacks/databasus/compose.yaml`

Replace three Jinja2 vars with literals. The two external network references (`infra_net`, `komodo_komodo-net`) remain unchanged — both still exist on the host.

Komodo Stack Environment for Databasus:
```
SECRET_KEY=[[DATABASUS_SECRET_KEY]]
R2_ACCESS_KEY_ID=[[R2_ACCESS_KEY_ID]]
R2_SECRET_ACCESS_KEY=[[R2_SECRET_ACCESS_KEY]]
R2_ACCOUNT_ID=144d079696599a9af7525be0c68a459f
R2_BUCKET_NAME=kiran-vm-database-backup
R2_ENDPOINT=https://144d079696599a9af7525be0c68a459f.eu.r2.cloudflarestorage.com
```

### `stacks/gitea/compose.yaml`

Replace five Jinja2 vars with literals. The `/etc/timezone` and `/etc/localtime` mounts are already literals — keep them.

Komodo Stack Environment for Gitea:
```
GITEA__database__PASSWD=[[GITEA_DB_PASSWORD]]
GITEA__security__SECRET_KEY=[[GITEA_SECRET_KEY]]
GITEA__database__DB_TYPE=postgres
GITEA__database__HOST=postgres:5432
GITEA__database__NAME=gitea
GITEA__database__USER=gitea_user
GITEA__database__SSL_MODE=disable
GITEA__server__DOMAIN=git.fewa.app
GITEA__server__ROOT_URL=https://git.fewa.app
GITEA__server__HTTP_PORT=3000
GITEA__server__SSH_DOMAIN=git.fewa.app
GITEA__server__SSH_PORT=2223
GITEA__server__SSH_LISTEN_PORT=2222
GITEA__server__DISABLE_SSH=false
GITEA__server__ENABLE_PPROF=false
GITEA__service__DISABLE_REGISTRATION=false
GITEA__service__REQUIRE_SIGNIN_VIEW=false
GITEA__ui__DEFAULT_THEME=gitea-dark
GITEA__ui__THEMES=gitea-light,gitea-dark,gitea-auto
GITEA__log__LEVEL=info
GITEA__webhook__ALLOWED_HOST_LIST=komodo.fewa.app
```

> **Note:** The `GITEA__webhook__ALLOWED_HOST_LIST` is set both here (for Komodo-managed Gitea) and in the Ansible template (Task 2) for the transition period while Gitea is still Ansible-managed.

---

## Task 4: Strip compose management from migrated Ansible roles

Once stacks are Komodo-managed, Ansible must no longer template or start compose files for the 4 migrated roles. **Keep directory creation — Komodo needs the directories to exist.**

### `ansible/roles/sure/tasks/main.yml`
**Remove:**
- Template task for `sure.env.j2` → `.env`
- Template task for `docker-compose.yml.j2`
- `docker_compose_v2` start task
- The `docker_compose_v2_pull` task (if present)

**Keep:**
- `file` task creating `sure_dir` (Komodo needs `/opt/sure/` to exist)
- `docker_volume` absent tasks removing old `sure_postgres-data` + `sure_redis-data` volumes

**Remove:** `ansible/roles/sure/templates/sure.env.j2` and `docker-compose.yml.j2`  
**Remove:** `ansible/roles/sure/handlers/main.yml` (Restart sure handler — no longer needed)

### `ansible/roles/nocodb/tasks/main.yml`
**Remove:**
- `assert` task (secrets no longer needed by Ansible)
- Template task for `nocodb.env.j2` → `.env`
- Template task for `docker-compose.yml.j2`
- `docker_compose_v2` start task

**Keep:**
- `file` tasks creating `nocodb_dir` and `nocodb_dir/data` (bind mount path must exist)

**Remove:** `ansible/roles/nocodb/templates/nocodb.env.j2` and `docker-compose.yml.j2`  
**Remove:** `ansible/roles/nocodb/handlers/main.yml`

### `ansible/roles/databasus/tasks/main.yml`
**Remove:**
- `assert` task
- Template task for `databasus.env.j2` → `.env`
- Template task for `docker-compose.yml.j2`
- `docker_compose_v2` start task

**Keep:**
- `file` tasks creating `databasus_dir` and `databasus_dir/data` (bind mount path must exist)

**Remove:** `ansible/roles/databasus/templates/databasus.env.j2` and `docker-compose.yml.j2`  
**Remove:** `ansible/roles/databasus/handlers/main.yml`

### `ansible/roles/gitea/tasks/main.yml`
**Remove:**
- Template task for `gitea.env.j2` → `.env`
- Template task for `docker-compose.yml.j2`
- `docker_compose_v2` start task

**Keep:**
- `assert` task (gitea_secret_key, shared_postgres_gitea_password still in secrets.yml — used for Komodo Variables reference)
- `file` tasks creating `gitea_dir` (0750, deploy_user)
- `file` tasks creating `gitea_dir/data` and `gitea_dir/config` (owner 1000:1000 — rootless requirement)
- `file` tasks creating custom template dirs (`data/custom/templates/`, etc., owner 1000:1000)
- `copy` tasks for `home.tmpl` and `header.tmpl` (these are bind-mounted into the container, Komodo doesn't touch them)

**Remove:** `ansible/roles/gitea/templates/gitea.env.j2` and `docker-compose.yml.j2`  
**Remove:** `ansible/roles/gitea/handlers/main.yml`

> **Exception for gitea `assert`:** The assert task can stay or be removed — the secrets it checks are still needed but only to look up the values to put into Komodo Variables. Remove it to reduce confusion.

---

## Task 5: Ansible — handoff tasks (stop old stacks)

Add a one-time teardown step to each migrated role's tasks to stop the existing containers before Komodo takes over. These use `docker_compose_v2 state=absent` and can be removed from the playbook after the first successful migration run.

Add to each migrated role's `tasks/main.yml` (only runs if compose file still exists, to be idempotent):

```yaml
- name: Stop Ansible-managed <service> stack (hand off to Komodo)
  community.docker.docker_compose_v2:
    project_src: "{{ <service>_dir }}"
    project_name: <service>
    state: absent
    remove_orphans: true
  ignore_errors: true
  tags: [<service>, services, komodo-handoff]
```

Using `ignore_errors: true` ensures this is safe even if the stack was never started or already removed.

After the handoff is confirmed working, these tasks can be removed in a follow-up commit.

---

## Task 6: Manual Komodo setup (post-Ansible, one-time)

This part cannot be automated by Ansible — it's done once in the Komodo UI.

### Step 1: Add Komodo Variables (secrets)

Komodo UI > Settings > Variables > New Variable

Add each variable from the table in Task 3, marked as secret:
- `SURE_DB_PASSWORD`, `SURE_SECRET_KEY_BASE`, `OPENAI_ACCESS_TOKEN`
- `NOCODB_DB_PASSWORD`, `NOCODB_JWT_SECRET`
- `DATABASUS_SECRET_KEY`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`
- `GITEA_DB_PASSWORD`, `GITEA_SECRET_KEY`

Values come from `ansible/secrets.yml`.

### Step 2: Add Gitea as a Git provider

Komodo UI > Settings > Git Providers > New Provider
- URL: `https://git.fewa.app`
- Create a Gitea access token: Gitea > Settings > Applications > Generate Token
  - Permissions: `read:repository` (read-only is sufficient)
- Add token to Komodo

### Step 3: Create a Linked Repo resource

Komodo UI > Resources > Repos > New Repo
- Name: `kiran-vm`
- Provider: `git.fewa.app` (from Step 2)
- Repo: `<your-username>/kiran-vm`
- Branch: `main`

This single Repo resource is reused by all 4 stacks.

### Step 4: Create each Stack

For each service (`sure`, `nocodb`, `databasus`, `gitea`):

1. Komodo UI > Resources > Stacks > New Stack
2. Mode: **Git Repo**
3. Linked Repo: `kiran-vm`
4. Run Directory: `stacks/sure/` (adjust per service)
5. Compose File: `compose.yaml` (default)
6. Stack Environment: paste the vars from Task 3 above
7. Enable: **Poll For Updates** (toggle in Stack > Config > Auto Update)
8. Enable: **Webhook** toggle → copy the webhook URL shown

### Step 5: Configure Gitea webhooks

In Gitea > `kiran-vm` repo > Settings > Webhooks > Add Webhook (GitHub-style):

| Field          | Value                                        |
|----------------|----------------------------------------------|
| Target URL     | Komodo webhook URL (from Step 4)             |
| Content type   | `application/json`                           |
| Secret         | value of `komodo_webhook_secret` from secrets |
| Trigger        | Push events                                  |

Repeat for each of the 4 stacks, or use a single webhook for the repo and let all stacks poll (polling at `KOMODO_RESOURCE_POLL_INTERVAL=3600` is the fallback).

### Step 6: Initial deploy + verify

1. In Komodo, deploy each stack once manually (Stack > Deploy)
2. Verify containers are running, check logs
3. Test the webhook: make a trivial commit (e.g. update a comment in `stacks/sure/compose.yaml`), push to GitHub, confirm Gitea mirrors it, confirm Komodo redeploys

---

## What Stays the Same

| Role       | Managed by | Reason                                        |
|------------|------------|-----------------------------------------------|
| `common`   | Ansible    | OS hardening, not a stack                     |
| `docker`   | Ansible    | Docker installation                           |
| `infra`    | Ansible    | Shared Postgres + Redis                       |
| `komodo`   | Ansible    | Cannot manage itself                          |
| `caddy`    | Ansible    | xcaddy build, host networking                 |
| `postiz`   | Ansible    | Already dormant, no change                    |

---

## Important Notes

### databasus dual-network
Databasus joins `infra_net` AND `komodo_komodo-net`. The second network (`komodo_komodo-net`) is created by Ansible's Komodo stack (project name `komodo`, network name `komodo-net`). As long as Ansible keeps managing Komodo, this network name is stable and the external reference in `stacks/databasus/compose.yaml` will work.

### Gitea custom templates
Gitea's `home.tmpl` and `header.tmpl` are deployed by Ansible to `/opt/gitea/data/custom/templates/`. These are bind-mounted into the container — Komodo doesn't touch them. Ansible's gitea role continues to manage these files even after compose management is handed off.

### File cleanup
After successful migration, the following template files can be deleted (they're replaced by `stacks/`):
- `ansible/roles/sure/templates/sure.env.j2`
- `ansible/roles/sure/templates/docker-compose.yml.j2`
- `ansible/roles/nocodb/templates/nocodb.env.j2`
- `ansible/roles/nocodb/templates/docker-compose.yml.j2`
- `ansible/roles/databasus/templates/databasus.env.j2`
- `ansible/roles/databasus/templates/docker-compose.yml.j2`
- `ansible/roles/gitea/templates/gitea.env.j2`
- `ansible/roles/gitea/templates/docker-compose.yml.j2`

And the handler files:
- `ansible/roles/sure/handlers/main.yml`
- `ansible/roles/nocodb/handlers/main.yml`
- `ansible/roles/databasus/handlers/main.yml`
- `ansible/roles/gitea/handlers/main.yml`

### `secrets.yml.example`
No changes needed. The secrets haven't changed — they still need to exist in `secrets.yml` so you can look up the values to paste into Komodo Variables. The example file remains a useful reference.

---

## Execution Order

1. **Task 1** — Ansible Komodo improvements (poll interval, periphery label, dex.sh)
2. **Task 2** — Gitea webhook allowlist (add one line to gitea.env.j2)
3. **Task 3** — Create `stacks/` directory with all 4 compose files
4. **Task 4** — Strip compose management from migrated Ansible roles
5. **Task 5** — Add handoff tasks to Ansible roles
6. **Run Ansible** — applies Tasks 1-5 in one playbook run: stops old stacks, sets up dirs, configures Gitea+Komodo env
7. **Task 6** — Manual Komodo UI setup (Komodo Variables, Repo, Stacks, Webhooks, initial deploy)
8. **Follow-up** — Remove Task 5 handoff tasks in a cleanup commit once migration is confirmed
