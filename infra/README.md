# infra

Pulumi (Python) program that provisions an Oracle Cloud Always Free ARM VM inside a dedicated compartment.

This layer provisions infrastructure only. App/runtime stacks are managed separately via Docker and Komodo.

It also manages core Cloudflare DNS records for the primary domain so DNS follows VM replacements automatically.

## What it creates

| Resource         | Details                                                       |
| ---------------- | ------------------------------------------------------------- |
| Compartment      | Dedicated child compartment, cleanly deleted on `pulumi down` |
| VCN              | `10.0.0.0/16`                                                 |
| Internet Gateway | Attached to VCN                                               |
| Route Table      | Default route via Internet Gateway                            |
| Security List    | SSH 22/2222, HTTP 80, HTTPS 443, ICMP                        |
| Public Subnet    | `10.0.0.0/24`                                                 |
| Compute Instance | `VM.Standard.A1.Flex` — 4 OCPU / 24 GB RAM / 200 GB boot volume (default) |
| Cloudflare DNS   | `A` apex + `A` www + CNAMEs (`backup`, `git`, `komodo`, `n8n`, `sure`) |

All constants (CIDRs, ports, image, shape) are defined in `../Taskfile.yml` vars and generated into `constants.py` by `task sync` or `task init`.

## Prerequisites

- [Pulumi CLI](https://www.pulumi.com/docs/get-started/install/) — logged in to Pulumi Cloud (`pulumi login`)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- OCI account with Always Free resources available
- OCI API key (`~/.oci/oci_api_key.pem`) and its fingerprint

## Setup

From the repo root:

```bash
task sync
task init STACK=kiran-prod
```

Equivalent direct commands:

```bash
cd infra

# Install dependencies
uv sync

# Create the stack
pulumi stack init kiran-prod
```

## Config

```bash
# OCI credentials (all stored as secrets)
pulumi config set --secret oci:tenancyOcid  <your-tenancy-ocid>
pulumi config set --secret oci:userOcid     <your-user-ocid>
pulumi config set --secret oci:fingerprint  <your-api-key-fingerprint>
pulumi config set --secret oci:privateKey   "$(cat ~/.oci/oci_api_key.pem)"
pulumi config set          oci:region       <your-region>   # e.g. ap-melbourne-1

# Project config
pulumi config set kiran-vm-infra:projectName  <your-project-name>
pulumi config set kiran-vm-infra:sshPublicKey "$(cat ~/.ssh/id_ed25519.pub)"
pulumi config set kiran-vm-infra:cloudflareZoneId <your-cloudflare-zone-id>

# Optional domain override (default: fewa.app)
pulumi config set kiran-vm-infra:domainName fewa.app

# Optional overrides (defaults shown)
pulumi config set kiran-vm-infra:bootVolumeSizeGb 200   # default from Taskfile.yml -> constants.py
pulumi config set kiran-vm-infra:adIndex          0     # try 1 or 2 if AD is out of A1 capacity
```

> **Finding your OCI credentials:**
> - Tenancy OCID: OCI Console → top-right menu → Tenancy
> - User OCID: OCI Console → top-right menu → My Profile
> - API key + fingerprint: My Profile → API Keys → Add API Key

## Usage

From the repo root:

```bash
task preview STACK=kiran-prod
task up STACK=kiran-prod
task destroy STACK=kiran-prod CONFIRM=yes
```

Equivalent direct commands:

```bash
# Preview changes
pulumi preview

# Deploy
pulumi up

# Tear down everything (including the compartment)
pulumi down
```

## Outputs

| Key                  | Description                               |
| -------------------- | ----------------------------------------- |
| `publicIp`           | Instance public IP                        |
| `privateIp`          | Instance private IP                       |
| `instanceId`         | OCI OCID of the compute instance          |
| `domainName`         | DNS zone domain managed in Cloudflare     |
| `apexDnsRecordId`    | Cloudflare record ID for apex `A` record  |
| `wwwDnsRecordId`     | Cloudflare record ID for `www` `A` record |
| `compartmentId`      | OCI OCID of the dedicated compartment     |
| `vcnId`              | OCI OCID of the VCN                       |
| `subnetId`           | OCI OCID of the subnet                    |
| `sshCommand`         | `ssh -p 2222 deploy@<publicIp>`           |
| `sshCommandBootstrap`| `ssh -p 22 deploy@<publicIp>` (first run) |

## After provisioning

```bash
cd ../provision
./inventory/generate.sh   # pull IP from Pulumi stack → writes hosts.ini
./bootstrap.sh            # first-run only: hardens sshd (22 → 2222)
ansible-playbook site.yml # full provisioning
```

See `../provision/README.md` for the complete provisioning guide.

## Cloudflare token file

`task preview` and `task up` read Cloudflare token from one of:

1. `CLOUDFLARE_API_TOKEN` environment variable
2. `CLOUDFLARE_API_TOKEN_FILE` path (defaults to `~/.cloudflare_pass`)

Create default token file:

```bash
echo '<cloudflare-api-token>' > ~/.cloudflare_pass
chmod 600 ~/.cloudflare_pass
```

## Always Free limits

Oracle Always Free gives **200 GB total block storage** across all instances. This stack uses 200 GB by default. If you want room for AMD Micro instances (`VM.Standard.E2.1.Micro`), lower `bootVolumeSizeGb` (for example, to 100).

To view your current usage: OCI Console → Storage → Block Volumes.
