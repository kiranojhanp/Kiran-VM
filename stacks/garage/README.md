# Garage Stack

Compose file: `stacks/garage/compose.yaml`

[Garage](https://garagehq.deuxfleurs.fr) is an S3-compatible object storage solution designed for self-hosting. This stack deploys both Garage and the [garage-webui](https://github.com/khairul169/garage-webui) management interface.

## Setup

1. Add secrets to `provision/secrets.yml`:
   ```bash
   task secrets:edit
   ```

   Add these variables:
   ```yaml
   garage_rpc_secret: ""      # Generate with: openssl rand -hex 32
   garage_admin_token: ""     # Generate with: openssl rand -hex 32
   garage_metrics_token: ""  # Generate with: openssl rand -hex 32
   ```

2. Optional: set non-secret config in `provision/group_vars/all.yml`:
   ```yaml
   garage_s3_region: ap-southeast-1
   garage_domain: fewa.app
   ```

3. Run provisioning:
   ```bash
   task push
   ```

## In Komodo

1. Create or open the `garage` stack.
2. Set run directory to `stacks/garage`.
3. Set compose path to `stacks/garage/compose.yaml`.
4. Add `GARAGE_HOST` in the stack Environment (e.g., `garage.fewa.app`).
5. Add `SHARED_DOCKER_NETWORK` if not using the default (`internal-network`).
6. Deploy (or Redeploy).

## Post-deploy cluster setup

After the first deploy, run these commands on the host:

```bash
# Get the node ID
docker exec garage garage node id

# Create layout (replace NODE_ID and SIZE as needed)
docker exec garage garage layout assign <NODE_ID> -z dc1 -c 10G
docker exec garage garage layout apply --version 1
```

The `-c 10G` sets 10GB of storage; adjust as needed. Check `docker exec garage garage layout show` to verify.

## Creating access keys

After layout setup, use garage-webui or the CLI:

```bash
# Via CLI
docker exec garage garage key create myapp
docker exec garage garage bucket create mybucket
docker exec garage garage bucket allow mybucket --read --write --key <ACCESS_KEY>
```

Or visit `https://<GARAGE_HOST>` to use the webui.

## Connecting apps

- **S3 API**: `http://<host>:3900`
- **S3 region**: set via `garage_s3_region` in group_vars

Example s5cmd config:

```bash
s5cmd config host endpoint http://<host>:3900
s5cmd config credentials static <ACCESS_KEY> <SECRET_KEY>
```
