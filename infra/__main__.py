import pulumi
import pulumi_oci as oci

# ── Constants ─────────────────────────────────────────────────────────────────
VCN_CIDR = "10.0.0.0/16"
SUBNET_CIDR = "10.0.0.0/24"
SUBNET_DNS_LABEL = "public"

# VM.Standard.A1.Flex — Oracle Always Free allocation: 4 OCPU, 24 GB RAM, 200 GB storage
INSTANCE_SHAPE = "VM.Standard.A1.Flex"
INSTANCE_OCPUS = 4
INSTANCE_MEM_GB = 24
BOOT_VOLUME_GB = "200"

# OCI protocol numbers
PROTO_TCP = "6"
PROTO_ICMP = "1"

# Hardened SSH port (post-Ansible)
SSH_PORT = 2222

# ── Config ────────────────────────────────────────────────────────────────────
cfg = pulumi.Config()

project_name = cfg.get("projectName") or "kiran-vm"
ssh_public_key = cfg.require("sshPublicKey")
image_ocid = cfg.require("imageOcid")

# OCI provider config — pulled from `pulumi config set --secret`
oci_cfg = pulumi.Config("oci")
tenancy_ocid = oci_cfg.require_secret("tenancyOcid")

# compartmentId defaults to tenancyOcid (root compartment)
compartment_id = cfg.get("compartmentId") or tenancy_ocid

# ── VCN ───────────────────────────────────────────────────────────────────────
vcn = oci.core.Vcn(
    f"{project_name}-vcn",
    compartment_id=compartment_id,
    cidr_block=VCN_CIDR,
    display_name=f"{project_name}-vcn",
    dns_label=project_name.replace("-", ""),
)

# ── Internet Gateway ──────────────────────────────────────────────────────────
igw = oci.core.InternetGateway(
    f"{project_name}-igw",
    compartment_id=compartment_id,
    vcn_id=vcn.id,
    display_name=f"{project_name}-igw",
    enabled=True,
)

# ── Route Table ───────────────────────────────────────────────────────────────
route_table = oci.core.RouteTable(
    f"{project_name}-rt",
    compartment_id=compartment_id,
    vcn_id=vcn.id,
    display_name=f"{project_name}-rt",
    route_rules=[
        oci.core.RouteTableRouteRuleArgs(
            network_entity_id=igw.id,
            destination="0.0.0.0/0",
            destination_type="CIDR_BLOCK",
        )
    ],
)

# ── Security List ─────────────────────────────────────────────────────────────
security_list = oci.core.SecurityList(
    f"{project_name}-sl",
    compartment_id=compartment_id,
    vcn_id=vcn.id,
    display_name=f"{project_name}-sl",
    # Egress: allow all outbound
    egress_security_rules=[
        oci.core.SecurityListEgressSecurityRuleArgs(
            destination="0.0.0.0/0",
            protocol="all",
            description="Allow all outbound",
        )
    ],
    # Ingress rules
    ingress_security_rules=[
        # SSH hardened port — Ansible uses this after provisioning
        oci.core.SecurityListIngressSecurityRuleArgs(
            protocol=PROTO_TCP,
            source="0.0.0.0/0",
            tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                min=SSH_PORT,
                max=SSH_PORT,
            ),
            description="SSH (hardened port)",
        ),
        # HTTP
        oci.core.SecurityListIngressSecurityRuleArgs(
            protocol=PROTO_TCP,
            source="0.0.0.0/0",
            tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                min=80,
                max=80,
            ),
            description="HTTP",
        ),
        # HTTPS
        oci.core.SecurityListIngressSecurityRuleArgs(
            protocol=PROTO_TCP,
            source="0.0.0.0/0",
            tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                min=443,
                max=443,
            ),
            description="HTTPS",
        ),
        # ICMP type 3 code 4 — path MTU discovery (required for TCP to work correctly)
        oci.core.SecurityListIngressSecurityRuleArgs(
            protocol=PROTO_ICMP,
            source="0.0.0.0/0",
            icmp_options=oci.core.SecurityListIngressSecurityRuleIcmpOptionsArgs(
                type=3,
                code=4,
            ),
            description="ICMP path MTU discovery",
        ),
        # ICMP type 8 — ping
        oci.core.SecurityListIngressSecurityRuleArgs(
            protocol=PROTO_ICMP,
            source="0.0.0.0/0",
            icmp_options=oci.core.SecurityListIngressSecurityRuleIcmpOptionsArgs(
                type=8,
            ),
            description="ICMP ping",
        ),
    ],
)

# ── Public Subnet ─────────────────────────────────────────────────────────────
subnet = oci.core.Subnet(
    f"{project_name}-subnet",
    compartment_id=compartment_id,
    vcn_id=vcn.id,
    cidr_block=SUBNET_CIDR,
    display_name=f"{project_name}-subnet",
    dns_label=SUBNET_DNS_LABEL,
    route_table_id=route_table.id,
    security_list_ids=[security_list.id],
    prohibit_public_ip_on_vnic=False,
)


# ── Compute Instance ──────────────────────────────────────────────────────────
def get_availability_domain(cid: str) -> str:
    result = oci.identity.get_availability_domains(compartment_id=cid)
    return result.availability_domains[0].name


availability_domain = pulumi.Output.from_input(compartment_id).apply(
    get_availability_domain
)

instance = oci.core.Instance(
    f"{project_name}-vm",
    compartment_id=compartment_id,
    availability_domain=availability_domain,
    display_name=f"{project_name}-vm",
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
        display_name=f"{project_name}-vnic",
        hostname_label=project_name,
    ),
    metadata={
        "ssh_authorized_keys": ssh_public_key,
    },
)

# ── Outputs ───────────────────────────────────────────────────────────────────
pulumi.export("publicIp", instance.public_ip)
pulumi.export("privateIp", instance.private_ip)
pulumi.export("instanceId", instance.id)
pulumi.export(
    "sshCommand", pulumi.Output.concat(f"ssh -p {SSH_PORT} deploy@", instance.public_ip)
)
pulumi.export("vcnId", vcn.id)
pulumi.export("subnetId", subnet.id)
