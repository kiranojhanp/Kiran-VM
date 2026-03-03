# infra/

Pulumi TypeScript that provisions an Oracle Cloud Always Free ARM VM: VCN, subnet, security list, internet gateway, and a `VM.Standard.A1.Flex` instance.

## Prerequisites

- [Pulumi CLI](https://www.pulumi.com/docs/get-started/install/)
- Oracle Cloud account with Always Free quota
- OCI API key at `~/.oci/oci_api_key.pem`
- Node.js 18+

## Passphrase setup

Secrets are encrypted with a passphrase. Store it in a file to avoid typing it every time:

```bash
echo 'your-passphrase' > ~/.pulumi-passphrase
chmod 600 ~/.pulumi-passphrase
echo 'export PULUMI_CONFIG_PASSPHRASE_FILE=$HOME/.pulumi-passphrase' >> ~/.zshrc
```

> State is local (`~/.pulumi/stacks/`), not Pulumi Cloud. Back it up if needed.

## Setup

```bash
cd infra
npm install
pulumi login --local
pulumi stack init prod

pulumi config set oci:region <your-region>
pulumi config set --secret oci:tenancyOcid <tenancy-ocid>
pulumi config set --secret oci:userOcid    <user-ocid>
pulumi config set --secret oci:fingerprint <key-fingerprint>
pulumi config set --secret oci:privateKey  "$(cat ~/.oci/oci_api_key.pem)"
pulumi config set sshPublicKey "$(cat ~/.ssh/id_ed25519.pub)"

# Ubuntu 22.04 Minimal ARM — find your region's OCID at:
# https://docs.oracle.com/en-us/iaas/images/
pulumi config set imageOcid <image-ocid>
```

## Deploy

```bash
pulumi up
# outputs: publicIp, sshCommand
```

Copy `publicIp` into `ansible/inventory/hosts.ini`.

## Other commands

```bash
pulumi stack output   # view outputs without deploying
pulumi destroy        # tear down all resources
```

## Config reference

| Key | Secret | Description |
|-----|--------|-------------|
| `oci:region` | no | OCI region (e.g. `ap-melbourne-1`) |
| `oci:tenancyOcid` | yes | OCI tenancy OCID |
| `oci:userOcid` | yes | OCI user OCID |
| `oci:fingerprint` | yes | API key fingerprint |
| `oci:privateKey` | yes | API private key PEM |
| `sshPublicKey` | no | SSH public key for the VM |
| `imageOcid` | no | OS image OCID (region-specific) |
| `projectName` | no | Prefix for OCI resource names (default: `kiran-vm`) |
| `compartmentId` | no | OCI compartment (default: root tenancy) |
