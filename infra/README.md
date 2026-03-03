# infra/

Pulumi TypeScript program that provisions an Oracle Cloud **Always Free** ARM VM — VCN, subnet, security list, internet gateway, and a `VM.Standard.A1.Flex` compute instance (4 OCPU, 24 GB RAM, 200 GB boot volume).

Portable by design: change a handful of config values to provision for a completely different project or OCI account.

## Architecture

```mermaid
flowchart TD
    Internet["Internet"]

    subgraph OCI["Oracle Cloud (Always Free)"]
        subgraph VCN["VCN 10.0.0.0/16"]
            IGW["Internet Gateway"]
            RT["Route Table\n0.0.0.0/0 → IGW"]
            SL["Security List\nIngress: 22, 2222, 80, 443, ICMP\nEgress: all"]
            subgraph Subnet["Public Subnet 10.0.0.0/24"]
                VM["VM.Standard.A1.Flex\n4 OCPU · 24 GB RAM\n200 GB boot volume\nUbuntu 22.04 ARM"]
            end
        end
    end

    Internet <--> IGW
    IGW --> RT --> SL --> VM
```

## Prerequisites

- [Pulumi CLI](https://www.pulumi.com/docs/get-started/install/) installed
- An Oracle Cloud account with Always Free quota
- OCI API key generated (`~/.oci/oci_api_key.pem`)
- Node.js 18+

## State backend

This project uses a **local file backend** — Pulumi state is stored on your machine, not in Pulumi Cloud.

State location: `~/.pulumi/stacks/kiran-vm-infra/prod.json`

This means:
- No Pulumi Cloud account required
- State is not synced automatically — back up `~/.pulumi/` if needed
- You must be on the same machine (or copy state) to run `pulumi up`/`pulumi destroy`

## Passphrase setup

Secrets in `Pulumi.prod.yaml` are encrypted with a passphrase. Rather than typing it every time, store it in a file and point Pulumi at it.

```bash
# Create the passphrase file (one-time)
echo 'your-passphrase-here' > ~/.pulumi-passphrase
chmod 600 ~/.pulumi-passphrase

# Add to ~/.zshrc or ~/.bashrc so it's always set
echo 'export PULUMI_CONFIG_PASSPHRASE_FILE=$HOME/.pulumi-passphrase' >> ~/.zshrc
source ~/.zshrc
```

With `PULUMI_CONFIG_PASSPHRASE_FILE` set, `pulumi up` / `pulumi preview` / `pulumi stack output` work without any passphrase prompts.

> **Never commit the passphrase file.** It's not in the repo — keep it only on your local machine.

## First-time setup

```bash
cd infra
npm install

# Log in to the local file backend (one-time per machine)
pulumi login --local

# Create a new stack
pulumi stack init prod

# OCI credentials (stored encrypted in Pulumi state)
pulumi config set           oci:region      ap-melbourne-1   # your OCI region
pulumi config set --secret  oci:tenancyOcid <your-tenancy-ocid>
pulumi config set --secret  oci:userOcid    <your-user-ocid>
pulumi config set --secret  oci:fingerprint <your-key-fingerprint>
pulumi config set --secret  oci:privateKey  "$(cat ~/.oci/oci_api_key.pem)"

# SSH public key (placed in instance metadata for cloud-init)
pulumi config set sshPublicKey "$(cat ~/.ssh/id_ed25519.pub)"

# imageOcid: Ubuntu 22.04 Minimal ARM (Melbourne region)
# Current value used in prod:
pulumi config set imageOcid ocid1.image.oc1.ap-melbourne-1.aaaaaaaawr3xahtf7zbw6uov2yawyerlfkm246qbtrku7cvcel7enu66y5tq

# For other regions, find the correct OCID at:
# https://docs.oracle.com/en-us/iaas/images/
```

## Deploy

```bash
pulumi up
```

Pulumi will print the public IP and SSH command on success:

```
Outputs:
  publicIp   : "207.211.156.85"
  sshCommand : "ssh -p 2222 deploy@207.211.156.85"
```

Copy `publicIp` into `ansible/inventory/hosts.ini` and run Ansible to complete provisioning.

## Existing prod stack

The `prod` stack is already deployed. Current resources:

| Resource | Value |
|---------|-------|
| VM public IP | `207.211.156.85` |
| VM private IP | `10.0.0.110` |
| Shape | `VM.Standard.A1.Flex` (4 OCPU, 24 GB RAM) |
| Boot volume | 200 GB |
| Region | `ap-melbourne-1` |
| Resource prefix | `fewaapp` |

To view current outputs without deploying:

```bash
pulumi stack output
```

## Using for a different project

To provision a fresh VM for another product:

1. `pulumi stack init <newproject>`
2. Set all config values above (different tenancy, region, or just a new stack)
3. Change `projectName` if you want different OCI resource name prefixes:
   ```bash
   pulumi config set projectName my-other-project
   ```
4. `pulumi up`

## Teardown

```bash
pulumi destroy
```

## Config reference

| Key | Required | Default | Description |
|-----|----------|---------|-------------|
| `oci:region` | yes | — | OCI region identifier |
| `oci:tenancyOcid` | yes (secret) | — | OCI tenancy OCID |
| `oci:userOcid` | yes (secret) | — | OCI user OCID |
| `oci:fingerprint` | yes (secret) | — | API key fingerprint |
| `oci:privateKey` | yes (secret) | — | OCI API private key PEM |
| `sshPublicKey` | yes | — | SSH public key for the VM |
| `imageOcid` | yes | Melbourne Ubuntu 22.04 Minimal ARM | OS image OCID (region-specific) |
| `projectName` | no | `kiran-vm` | Prefix for all OCI resource names |
| `compartmentId` | no | `tenancyOcid` | OCI compartment (defaults to root) |

## Outputs

| Output | Description |
|--------|-------------|
| `publicIp` | VM public IP address |
| `sshCommand` | Ready-to-use SSH command |
| `vcnId` | VCN OCID |
| `subnetId` | Subnet OCID |
