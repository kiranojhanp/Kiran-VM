# infra

Pulumi (Python) program that provisions the Oracle Cloud Always Free ARM VM.

## What it creates

- VCN + Internet Gateway + Route Table + Security List + Public Subnet
- `VM.Standard.A1.Flex` compute instance — 4 OCPU / 24 GB RAM / 200 GB boot volume

## Prerequisites

- [Pulumi CLI](https://www.pulumi.com/docs/get-started/install/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- OCI account with Always Free resources available

## Setup

```bash
cd infra

# Install dependencies (uv creates and manages the venv automatically)
uv sync

# Use local state (no Pulumi Cloud account needed)
pulumi login --local
export PULUMI_CONFIG_PASSPHRASE_FILE=~/.pulumi-passphrase

# Select the prod stack (creates it if it doesn't exist yet)
pulumi stack select prod --create
```

## Config

```bash
# OCI auth (all secrets)
pulumi config set --secret oci:tenancyOcid  <your-tenancy-ocid>
pulumi config set --secret oci:userOcid     <your-user-ocid>
pulumi config set --secret oci:fingerprint  <your-api-key-fingerprint>
pulumi config set --secret oci:privateKey   "$(cat ~/.oci/oci_api_key.pem)"
pulumi config set          oci:region       ap-melbourne-1

# Instance config
pulumi config set kiran-vm-infra:imageOcid    <ubuntu-22.04-arm64-image-ocid>
pulumi config set kiran-vm-infra:projectName  fewaapp
pulumi config set kiran-vm-infra:sshPublicKey "$(cat ~/.ssh/id_ed25519.pub)"
```

## Usage

```bash
# Preview changes
pulumi preview

# Deploy
pulumi up

# Tear down all resources
pulumi down
```

## Outputs

| Key          | Value                             |
|--------------|-----------------------------------|
| `publicIp`   | Instance public IP                |
| `privateIp`  | Instance private IP               |
| `instanceId` | OCI OCID of the compute instance  |
| `sshCommand` | `ssh -p 2222 deploy@<publicIp>`   |
| `vcnId`      | OCI OCID of the VCN               |
| `subnetId`   | OCI OCID of the subnet            |

## After provisioning

Run Ansible to configure the OS:

```bash
cd ../ansible
ansible-playbook site.yml -e @secrets.yml \
  --extra-vars "ansible_become_password=<sudo-password>"
```
