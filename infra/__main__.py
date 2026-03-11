import base64
import pulumi
import pulumi_oci as oci

from constants import (
    PROJECT_NAME_DEFAULT,
    SUFFIX_COMPARTMENT,
    SUFFIX_VCN,
    SUFFIX_IGW,
    SUFFIX_RT,
    SUFFIX_SL,
    SUFFIX_SUBNET,
    SUFFIX_VM,
    SUFFIX_VNIC,
    ANYWHERE,
    VCN_CIDR,
    SUBNET_CIDR,
    SUBNET_DNS_LABEL,
    PORT_HTTP,
    PORT_HTTPS,
    SSH_PORT_INITIAL,
    SSH_PORT_HARDENED,
    PROTO_TCP,
    PROTO_ICMP,
    ICMP_TYPE_PATH_MTU,
    ICMP_CODE_PATH_MTU,
    ICMP_TYPE_PING,
    INSTANCE_SHAPE,
    INSTANCE_OCPUS,
    INSTANCE_MEM_GB,
    IMAGE_OS,
    IMAGE_OS_VERSION,
    BOOT_VOLUME_GB_DEFAULT,
    AD_INDEX_DEFAULT,
)

# ── Config ────────────────────────────────────────────────────────────────────
cfg = pulumi.Config()

project_name = (cfg.get("projectName") or PROJECT_NAME_DEFAULT).strip()
ssh_public_key = cfg.require("sshPublicKey")

# bootVolumeSizeGb — configurable; default 100 GB leaves headroom for AMD Micro instances
# (Oracle Always Free gives 200 GB total block storage across all instances)
BOOT_VOLUME_GB = cfg.get("bootVolumeSizeGb") or BOOT_VOLUME_GB_DEFAULT

# OCI provider config — pulled from `pulumi config set --secret`
oci_cfg = pulumi.Config("oci")
tenancy_ocid = oci_cfg.require_secret("tenancyOcid")

# ── 1. Dedicated Compartment ──────────────────────────────────────────────────
# Isolates all project resources from the root tenancy.
# enable_delete=True allows `pulumi down` to cleanly remove the compartment.
project_compartment = oci.identity.Compartment(
    f"{project_name}{SUFFIX_COMPARTMENT}",
    compartment_id=tenancy_ocid,
    description=f"Isolated compartment for {project_name}",
    name=project_name,
    enable_delete=True,
)

compartment_id = project_compartment.id

# ── VCN ───────────────────────────────────────────────────────────────────────
vcn = oci.core.Vcn(
    f"{project_name}{SUFFIX_VCN}",
    compartment_id=compartment_id,
    cidr_block=VCN_CIDR,
    display_name=f"{project_name}{SUFFIX_VCN}",
    dns_label=project_name.replace("-", ""),
)

# ── Internet Gateway ──────────────────────────────────────────────────────────
igw = oci.core.InternetGateway(
    f"{project_name}{SUFFIX_IGW}",
    compartment_id=compartment_id,
    vcn_id=vcn.id,
    display_name=f"{project_name}{SUFFIX_IGW}",
    enabled=True,
)

# ── Route Table ───────────────────────────────────────────────────────────────
route_table = oci.core.RouteTable(
    f"{project_name}{SUFFIX_RT}",
    compartment_id=compartment_id,
    vcn_id=vcn.id,
    display_name=f"{project_name}{SUFFIX_RT}",
    route_rules=[
        oci.core.RouteTableRouteRuleArgs(
            network_entity_id=igw.id,
            destination=ANYWHERE,
            destination_type="CIDR_BLOCK",
        )
    ],
)

# ── Security List ─────────────────────────────────────────────────────────────
security_list = oci.core.SecurityList(
    f"{project_name}{SUFFIX_SL}",
    compartment_id=compartment_id,
    vcn_id=vcn.id,
    display_name=f"{project_name}{SUFFIX_SL}",
    # Egress: allow all outbound
    egress_security_rules=[
        oci.core.SecurityListEgressSecurityRuleArgs(
            destination=ANYWHERE,
            protocol="all",
            description="Allow all outbound",
        )
    ],
    # Ingress rules
    ingress_security_rules=[
        # SSH port 22 — needed during initial bootstrap (cloud-init / first pyinfra run)
        oci.core.SecurityListIngressSecurityRuleArgs(
            protocol=PROTO_TCP,
            source=ANYWHERE,
            tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                min=SSH_PORT_INITIAL,
                max=SSH_PORT_INITIAL,
            ),
            description="SSH port 22 (bootstrap)",
        ),
        # SSH hardened port — pyinfra moves sshd here after common role runs
        oci.core.SecurityListIngressSecurityRuleArgs(
            protocol=PROTO_TCP,
            source=ANYWHERE,
            tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                min=SSH_PORT_HARDENED,
                max=SSH_PORT_HARDENED,
            ),
            description="SSH hardened port 2222 (post-provisioning)",
        ),
        # HTTP
        oci.core.SecurityListIngressSecurityRuleArgs(
            protocol=PROTO_TCP,
            source=ANYWHERE,
            tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                min=PORT_HTTP,
                max=PORT_HTTP,
            ),
            description="HTTP",
        ),
        # HTTPS
        oci.core.SecurityListIngressSecurityRuleArgs(
            protocol=PROTO_TCP,
            source=ANYWHERE,
            tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                min=PORT_HTTPS,
                max=PORT_HTTPS,
            ),
            description="HTTPS",
        ),
        # ICMP type 3 code 4 — path MTU discovery (required for TCP to work correctly)
        oci.core.SecurityListIngressSecurityRuleArgs(
            protocol=PROTO_ICMP,
            source=ANYWHERE,
            icmp_options=oci.core.SecurityListIngressSecurityRuleIcmpOptionsArgs(
                type=ICMP_TYPE_PATH_MTU,
                code=ICMP_CODE_PATH_MTU,
            ),
            description="ICMP path MTU discovery",
        ),
        # ICMP type 8 — ping
        oci.core.SecurityListIngressSecurityRuleArgs(
            protocol=PROTO_ICMP,
            source=ANYWHERE,
            icmp_options=oci.core.SecurityListIngressSecurityRuleIcmpOptionsArgs(
                type=ICMP_TYPE_PING,
            ),
            description="ICMP ping",
        ),
    ],
)

# ── Public Subnet ─────────────────────────────────────────────────────────────
subnet = oci.core.Subnet(
    f"{project_name}{SUFFIX_SUBNET}",
    compartment_id=compartment_id,
    vcn_id=vcn.id,
    cidr_block=SUBNET_CIDR,
    display_name=f"{project_name}{SUFFIX_SUBNET}",
    dns_label=SUBNET_DNS_LABEL,
    route_table_id=route_table.id,
    security_list_ids=[security_list.id],
    prohibit_public_ip_on_vnic=False,
)


# ── Compute Instance ──────────────────────────────────────────────────────────
# ad_index config lets you try different ADs if one is out of A1 capacity (default: 0)
_ad_index = int(cfg.get("adIndex") or AD_INDEX_DEFAULT)

# Use _invoke variants so Pulumi resolves these synchronously during planning,
# avoiding engine hang that can occur with .apply()-based SDK calls.
_ad_data = oci.identity.get_availability_domains_output(compartment_id=tenancy_ocid)
availability_domain = _ad_data.availability_domains.apply(
    lambda ads: ads[min(_ad_index, len(ads) - 1)].name
)

_image_data = oci.core.get_images_output(
    compartment_id=tenancy_ocid,
    operating_system=IMAGE_OS,
    operating_system_version=IMAGE_OS_VERSION,
    shape=INSTANCE_SHAPE,
    sort_by="TIMECREATED",
    sort_order="DESC",
)
image_ocid = _image_data.images.apply(lambda imgs: imgs[0].id)


def make_user_data(ssh_key: str) -> str:
    """Build base64-encoded cloud-init script that pre-creates the deploy user."""
    script = f"""#!/bin/bash
set -e
# Create deploy user (idempotent — useradd exits 9 if user already exists)
useradd -m -s /bin/bash deploy || true
# NOPASSWD sudo — pyinfra uses _sudo=True without a password
echo 'deploy ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/90-deploy
chmod 0440 /etc/sudoers.d/90-deploy
# Install SSH public key
mkdir -p /home/deploy/.ssh
echo '{ssh_key}' >> /home/deploy/.ssh/authorized_keys
sort -u /home/deploy/.ssh/authorized_keys -o /home/deploy/.ssh/authorized_keys
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh
"""
    return base64.b64encode(script.encode()).decode()


user_data = make_user_data(ssh_public_key)

instance = oci.core.Instance(
    f"{project_name}{SUFFIX_VM}",
    compartment_id=compartment_id,
    availability_domain=availability_domain,
    display_name=f"{project_name}{SUFFIX_VM}",
    shape=INSTANCE_SHAPE,
    shape_config=oci.core.InstanceShapeConfigArgs(
        ocpus=INSTANCE_OCPUS,
        memory_in_gbs=INSTANCE_MEM_GB,
    ),
    source_details=oci.core.InstanceSourceDetailsArgs(
        source_type="image",
        source_id=image_ocid,
        boot_volume_size_in_gbs=BOOT_VOLUME_GB,
    ),
    create_vnic_details=oci.core.InstanceCreateVnicDetailsArgs(
        subnet_id=subnet.id,
        assign_public_ip="true",
        display_name=f"{project_name}{SUFFIX_VNIC}",
        hostname_label=project_name,
    ),
    metadata={
        "ssh_authorized_keys": ssh_public_key,
        # cloud-init: pre-create deploy user with NOPASSWD sudo + SSH key
        # Built as a Pulumi Output so ssh_public_key resolves before encoding
        "user_data": user_data,
    },
)

# ── Outputs ───────────────────────────────────────────────────────────────────
pulumi.export("publicIp", instance.public_ip)
pulumi.export("privateIp", instance.private_ip)
pulumi.export("instanceId", instance.id)
pulumi.export(
    "sshCommand",
    pulumi.Output.concat(f"ssh -p {SSH_PORT_HARDENED} deploy@", instance.public_ip),
)
pulumi.export(
    "sshCommandBootstrap",
    pulumi.Output.concat(f"ssh -p {SSH_PORT_INITIAL} deploy@", instance.public_ip),
)
pulumi.export("vcnId", vcn.id)
pulumi.export("subnetId", subnet.id)
