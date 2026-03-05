import pulumi
import pulumi_oci as oci

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
    cidr_block="10.0.0.0/16",
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
        # SSH (standard — only during initial bootstrap, can be removed after)
        oci.core.SecurityListIngressSecurityRuleArgs(
            protocol="6",  # TCP
            source="0.0.0.0/0",
            tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                max=22, min=22
            ),
            description="SSH (standard)",
        ),
        # SSH (custom port — Ansible uses this after hardening)
        oci.core.SecurityListIngressSecurityRuleArgs(
            protocol="6",
            source="0.0.0.0/0",
            tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                max=2222, min=2222
            ),
            description="SSH (hardened port)",
        ),
        # HTTP
        oci.core.SecurityListIngressSecurityRuleArgs(
            protocol="6",
            source="0.0.0.0/0",
            tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                max=80, min=80
            ),
            description="HTTP",
        ),
        # HTTPS
        oci.core.SecurityListIngressSecurityRuleArgs(
            protocol="6",
            source="0.0.0.0/0",
            tcp_options=oci.core.SecurityListIngressSecurityRuleTcpOptionsArgs(
                max=443, min=443
            ),
            description="HTTPS",
        ),
        # ICMP type 3 (destination unreachable) — required for path MTU discovery
        oci.core.SecurityListIngressSecurityRuleArgs(
            protocol="1",  # ICMP
            source="0.0.0.0/0",
            icmp_options=oci.core.SecurityListIngressSecurityRuleIcmpOptionsArgs(
                type=3, code=4
            ),
            description="ICMP path MTU discovery",
        ),
        # ICMP type 8 (echo / ping)
        oci.core.SecurityListIngressSecurityRuleArgs(
            protocol="1",
            source="0.0.0.0/0",
            icmp_options=oci.core.SecurityListIngressSecurityRuleIcmpOptionsArgs(
                type=8
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
    cidr_block="10.0.0.0/24",
    display_name=f"{project_name}-subnet",
    dns_label="public",
    route_table_id=route_table.id,
    security_list_ids=[security_list.id],
    prohibit_public_ip_on_vnic=False,
)


# ── Compute Instance ──────────────────────────────────────────────────────────
# VM.Standard.A1.Flex — Oracle Always Free: 4 OCPU, 24 GB RAM total per account
def get_availability_domain(cid):
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
    shape="VM.Standard.A1.Flex",
    shape_config=oci.core.InstanceShapeConfigArgs(
        ocpus=4,
        memory_in_gbs=24,
    ),
    source_details=oci.core.InstanceSourceDetailsArgs(
        source_type="image",
        source_id=image_ocid,
        # 200 GB boot volume — uses all of the Always Free block storage allocation
        boot_volume_size_in_gbs="200",
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
    "sshCommand", pulumi.Output.concat("ssh -p 2222 deploy@", instance.public_ip)
)
pulumi.export("vcnId", vcn.id)
pulumi.export("subnetId", subnet.id)
