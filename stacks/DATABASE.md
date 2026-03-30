# Adding a New Stack with the Centralized Database

This guide explains how to create a new database, user, and credentials for a new application stack that uses the centralized PostgreSQL instance.

## Automatic Database Creation

Databases are automatically created/updated when you run `task update`. To add a new database:

1. Add the database name to `postgres_databases_list` in `provision/group_vars/all.yml`:
   ```yaml
   postgres_databases_list:
     - mealie
     - vikunja
     - yournewapp
   ```

2. Run `task update` to re-provision the infra.

This works even if Postgres already has data - it won't recreate existing databases.

All databases use the same password defined by `shared_postgres_password` in `secrets.yml`.

## Container Name

The shared Postgres container name is defined in `provision/group_vars/all.yml`:

```yaml
postgres_container_name: "infra-postgres-1"
```

Change this value to customize the container name (must be unique on the host). After changing, re-run `task update` to redeploy.

## Prerequisites

- You have SSH access to the VM
- The infra containers are running (`/opt/infra`)

## Step 1: Generate a Password

On your local machine (or anywhere), generate a secure password:

```bash
openssl rand -base64 24 | tr -dc 'A-Za-z0-9' | head -c 24
```

Save this password - you'll need it for the next steps.

## Step 2: SSH into the VM

```bash
ssh user@your-vm-ip
```

## Step 3: Create the Database User

Replace `myapp` with your stack name and `YOUR_PASSWORD_HERE` with the password from Step 1:

```bash
docker exec <postgres_container_name> psql -U postgres -c "
CREATE USER myapp WITH PASSWORD 'YOUR_PASSWORD_HERE';
"
```

## Step 4: Create the Database

```bash
docker exec <postgres_container_name> psql -U postgres -c "
CREATE DATABASE myapp OWNER myapp;
"
```

## Step 5: Grant Privileges

```bash
docker exec <postgres_container_name> psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE myapp TO myapp;"
docker exec <postgres_container_name> psql -U postgres -d myapp -c "GRANT ALL ON SCHEMA public TO myapp;"
```

## Step 6: Update Your Stack's compose.yaml

Add these environment variables to your service:

```yaml
services:
  myapp:
    environment:
      - SHARED_POSTGRES_HOST=shared-postgres
      - SHARED_POSTGRES_PORT=5432
      - MYAPP_DB_NAME=myapp
      - MYAPP_DB_USER=myapp
      - MYAPP_DB_PASSWORD=YOUR_PASSWORD_HERE
    networks:
      - internal-network
```

Most apps use standard variable names like `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`. Check your app's documentation for the exact variable names.

## Alternative: If Your App Uses Different Variable Names

You'll need to map the environment variables to what your app expects. For example, if your app uses `POSTGRES_HOST` instead of `DB_HOST`:

```yaml
environment:
  - POSTGRES_HOST=shared-postgres
  - POSTGRES_PORT=5432
  - POSTGRES_DB=myapp
  - POSTGRES_USER=myapp
  - POSTGRES_PASSWORD=YOUR_PASSWORD_HERE
```

## Connecting from Outside Docker Network

If you need to connect to the database from your host machine (for debugging):

```
Host: localhost (or VM IP)
Port: 5432
Database: myapp
Username: myapp
Password: YOUR_PASSWORD_HERE
```

Note: Make sure port 5432 is accessible through the firewall if you need external access.

## Useful Commands

### List all databases and owners:
```bash
docker exec <postgres_container_name> psql -U postgres -c "SELECT datname, pg_catalog.pg_get_userbyid(datdba) FROM pg_database WHERE datname NOT IN ('postgres', 'template0', 'template1');"
```

### List all users:
```bash
docker exec <postgres_container_name> psql -U postgres -c "SELECT rolname FROM pg_roles WHERE rolname NOT LIKE 'pg_%';"
```

### Drop a database and user (DANGER!):
```bash
docker exec <postgres_container_name> psql -U postgres -c "DROP DATABASE IF EXISTS myapp;"
docker exec <postgres_container_name> psql -U postgres -c "DROP USER IF EXISTS myapp;"
```

## Example: Adding a New Stack

Let's say you want to add **Vikunja** (the kanban app):

1. Generate password: `openssl rand -base64 24 | tr -dc 'A-Za-z0-9' | head -c 24`
2. SSH to VM
3. Create user: `docker exec <postgres_container_name> psql -U postgres -c "CREATE USER vikunja WITH PASSWORD 'your-password';"`
4. Create DB: `docker exec <postgres_container_name> psql -U postgres -c "CREATE DATABASE vikunja OWNER vikunja;"`
5. Grant privileges:
   ```bash
   docker exec <postgres_container_name> psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE vikunja TO vikunja;"
   docker exec <postgres_container_name> psql -U postgres -d vikunja -c "GRANT ALL ON SCHEMA public TO vikunja;"
   ```
6. Add to `stacks/vikunja/compose.yaml`:
   ```yaml
   services:
     vikunja:
       environment:
         - VIKUNJA_DB_HOST=shared-postgres
         - VIKUNJA_DB_PORT=5432
         - VIKUNJA_DB_DATABASE=vikunja
         - VIKUNJA_DB_USER=vikunja
         - VIKUNJA_DB_PASSWORD=your-password
       networks:
         - internal-network
   ```
