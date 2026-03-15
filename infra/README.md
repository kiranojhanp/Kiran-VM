# infra

Pulumi layer for VM, network, and DNS.

## Quickstart

From repo root:

```bash
task prepare

# set Pulumi config once for this stack
pulumi config set --secret oci:tenancyOcid <your-tenancy-ocid>
pulumi config set --secret oci:userOcid <your-user-ocid>
pulumi config set --secret oci:fingerprint <your-api-key-fingerprint>
pulumi config set --secret oci:privateKey "$(cat ~/.oci/oci_api_key.pem)"
pulumi config set oci:region <your-region>
pulumi config set kiran-vm-infra:sshPublicKey "$(cat ~/.ssh/id_ed25519.pub)"

task preview
task up
```

To tear everything down:

```bash
task destroy CONFIRM=yes
```

## Notes

- Default stack is `kiran-self-hosting`.
- Use `STACK=<name>` only when you want another stack.
- Cloudflare token is managed in `provision/secrets.yml` (`cloudflare_api_token`) via ansible-vault.
