# Audiobookshelf Stack

Compose file: `stacks/audiobookshelf/compose.yaml`

## In Komodo

1. Create or open the `audiobookshelf` stack.
2. Set compose path to `stacks/audiobookshelf/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<AUDIOBOOKSHELF_HOST>`.

## Stack environment variables

- `AUDIOBOOKSHELF_HOST` (required): public hostname. Example: `audiobookshelf.fewa.app`.
- `TZ` (optional): timezone. Default: `UTC`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.

## Volume mappings

- `/config`: database, users, books, libraries, settings.
- `/metadata`: cache, streams, covers, downloads, backups, logs.
- `/audiobooks`: audiobooks collection.
- `/podcasts`: podcasts collection.
- `/books`: ebooks collection (epub, pdf, cbr, cbz).

## Notes

Audiobookshelf uses SQLite internally and requires all volumes to be on the same filesystem.

## Security

This stack includes Docker security hardening:

- **Read-only root filesystem**: Prevents container from writing to root filesystem
- **No new privileges**: Prevents privilege escalation attacks
- **Dropped all capabilities**: Removes all Linux capabilities (`cap_drop: ALL`)
- **Memory limits**: `mem_limit` and `memswap_limit` set to prevent resource exhaustion
- **Process limits**: `pids_limit: 100` prevents fork bombs
