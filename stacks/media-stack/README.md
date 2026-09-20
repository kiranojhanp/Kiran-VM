# Media Stack

Self-hosted media web apps: the Live Sports addon and the ARVIO browser media hub.

## Quick Start

1. Create/open the `media-stack` in Komodo
2. Set compose path to `stacks/media-stack/compose.yaml`
3. Copy `.env.sample` to `.env` and fill in values
4. Add stack environment variables:
   - `LIVE_SPORTS_HOST` = `live-sports.fewa.app`
   - `ARVIO_HOST` = `arvio.fewa.app`
   - `SHARED_DOCKER_NETWORK` = `internal-network`
   - `TMDB_API_KEY` = (your TMDB API v3 key, required for ARVIO)
5. Deploy

## Required Variables

| Variable | Description | Example |
| -------- | ----------- | ------- |
| `LIVE_SPORTS_HOST` | Public hostname for Live Sports | `live-sports.fewa.app` |
| `ARVIO_HOST` | Public hostname for ARVIO | `arvio.fewa.app` |
| `TMDB_API_KEY` | TMDB API v3 key (ARVIO built-in catalogs) | (your key) |

## Services

| Service | URL | Purpose |
|---------|-----|---------|
| Live Sports | `https://live-sports.fewa.app` | Live sports addon (scrapes/aggregates public fixtures and streams) |
| ARVIO | `https://arvio.fewa.app` | Browser media hub (profiles, home-server libraries, addons) |

## Live Sports setup

- Add `https://live-sports.fewa.app/manifest.json` as an addon in Nuvio / Stremio.
- Open `https://live-sports.fewa.app/configure` to filter sports categories, providers, timezone, and favorite teams.
- **Built from source via `live-sports.Dockerfile`** (`ghcr.io/rajhodedara/live-sport-plugin:latest` is amd64-only, and this host is ARM64 Ampere with no QEMU emulation). Multi-stage Dockerfile clones the upstream repo, builds the ncc bundle, and produces a native arm64 image tagged `ghcr.io/rajhodedara/live-sport-plugin:latest` locally. `pull_policy: never` keeps Komodo's `pull` stage from trying to fetch the amd64-only published image. First/refresh build takes ~1 min on the server. Set `LIVE_SPORTS_REF` to pin the upstream ref (default `main`).
- **Stateless:** uses no Postgres/Redis (persistent prefs live in the addon config URL, catalogs are held in memory), so it joins only the `shared` network — no `infra` network, no shared DB access.

## ARVIO setup

- **Built from source via `arvio.Dockerfile`** (no prebuilt official image). The multi-stage Dockerfile clones `ProdigyV21/ARVIO`, runs `npm ci` and `npm run build`, and produces a native Next.js standalone image. First/refresh build takes a few minutes on the server. Set `ARVIO_REF` to pin the upstream ref (default `main`).
- **Stateless:** uses browser local storage only (profiles, settings, history stay in the browser), so it joins only the `shared` network — no `infra` network, no shared DB/Redis.
- Open `https://arvio.fewa.app`, choose/create a local profile, and add your sources in Settings.
- `TMDB_API_KEY` (API v3 key, not the bearer token) is required for the built-in movie/show catalogs. Trakt, Simkl, and Telegram are optional.
- **Build-time settings** (`NEXT_PUBLIC_SELF_HOSTED`, `TRAKT_CLIENT_ID`, `SIMKL_CLIENT_ID`, Telegram app credentials, resolver URL) require a rebuild after changing them. **Server-only runtime** vars (`TMDB_API_KEY`, `TRAKT_CLIENT_SECRET`, `SIMKL_CLIENT_SECRET`) only need a restart/recreate. Do not prefix the server-only secrets with `NEXT_PUBLIC_`.
- `ALLOW_PRIVATE_PROXY` enables server-side access to LAN home-server APIs (Plex/Emby/Jellyfin metadata). Off by default; enable only on a trusted, authenticated installation.

## Notes

- This stack replaces the old `aiostreams` stack which included AIOStreams, Jackett, WARP, and MediaFlow Proxy
