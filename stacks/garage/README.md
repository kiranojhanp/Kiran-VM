# Garage Stack

Compose file: `stacks/garage/compose.yaml`
Config template: `stacks/garage/garage.toml.tmpl`
Dockerfile: `stacks/garage/Dockerfile`
Entrypoint: `stacks/garage/entrypoint.sh`

[Garage](https://garagehq.deuxfleurs.fr) is an S3-compatible object storage solution designed for self-hosting. This stack deploys both Garage and the [garage-webui](https://github.com/khairul169/garage-webui) management interface.

The Docker image is built from the base image with an entrypoint that generates `garage.toml` from environment variables on first start.

## In Komodo

1. Create or open the `garage` stack.
2. Set run directory to `stacks/garage`.
3. Set compose path to `stacks/garage/compose.yaml`.
4. Add the variables below in the stack Environment.
5. Add `GARAGE_ADMIN_TOKEN` and `GARAGE_METRICS_TOKEN` in Komodo as secret variables.
6. Deploy (or Redeploy). Note: first deploy will build the Docker image.
7. Run the post-deploy layout setup (see below).

## Stack environment variables

- `GARAGE_HOST` (required): public hostname for webui. Example: `garage.fewa.app`.
- `GARAGE_RPC_SECRET` (required): RPC secret for inter-node communication. Generate with `openssl rand -hex 32`.
- `GARAGE_ADMIN_TOKEN` (required secret): admin API token. Generate with `openssl rand -hex 32`.
- `GARAGE_METRICS_TOKEN` (required secret): metrics API token. Generate with `openssl rand -hex 32`.
- `GARAGE_S3_REGION` (optional): S3 region name. Default: `us-east-1`.
- `GARAGE_DOMAIN` (optional): domain for S3/web endpoints. Default: `localhost`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.

## Post-deploy cluster setup

After the first deploy, you must initialize the storage layout. Run these commands on the host:

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

Use these S3-compatible endpoints:

- **S3 API**: `http://<host>:3900`
- **S3 region**: set via `GARAGE_S3_REGION`

Example s5cmd config:

```bash
s5cmd config host endpoint http://<host>:3900
s5cmd config credentials static <ACCESS_KEY> <SECRET_KEY>
```
