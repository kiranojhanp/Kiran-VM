import * as pulumi from "@pulumi/pulumi";
import * as oci from "@pulumi/oci";

// ── Config ────────────────────────────────────────────────────────────────────
const cfg = new pulumi.Config();

const projectName = cfg.get("projectName") ?? "kiran-vm";
const sshPublicKey = cfg.require("sshPublicKey");

// OCI provider config — pulled from `pulumi config set --secret`
const ociCfg = new pulumi.Config("oci");
const tenancyOcid = ociCfg.requireSecret("tenancyOcid");
const region = ociCfg.require("region");

// compartmentId defaults to tenancyOcid (root compartment)
const compartmentId: pulumi.Input<string> =
  cfg.get("compartmentId") ?? tenancyOcid;

// Ubuntu 22.04 Minimal ARM64 — set per region in Pulumi.<stack>.yaml
const imageOcid = cfg.require("imageOcid");

// ── VCN ───────────────────────────────────────────────────────────────────────
const vcn = new oci.core.Vcn(`${projectName}-vcn`, {
  compartmentId,
  cidrBlock: "10.0.0.0/16",
  displayName: `${projectName}-vcn`,
  dnsLabel: projectName.replace(/-/g, ""),
});

// ── Internet Gateway ──────────────────────────────────────────────────────────
const igw = new oci.core.InternetGateway(`${projectName}-igw`, {
  compartmentId,
  vcnId: vcn.id,
  displayName: `${projectName}-igw`,
  enabled: true,
});

// ── Route Table ───────────────────────────────────────────────────────────────
const routeTable = new oci.core.RouteTable(`${projectName}-rt`, {
  compartmentId,
  vcnId: vcn.id,
  displayName: `${projectName}-rt`,
  routeRules: [
    {
      networkEntityId: igw.id,
      destination: "0.0.0.0/0",
      destinationType: "CIDR_BLOCK",
    },
  ],
});

// ── Security List ─────────────────────────────────────────────────────────────
const securityList = new oci.core.SecurityList(`${projectName}-sl`, {
  compartmentId,
  vcnId: vcn.id,
  displayName: `${projectName}-sl`,

  // Egress: allow all outbound
  egressSecurityRules: [
    {
      destination: "0.0.0.0/0",
      protocol: "all",
      description: "Allow all outbound",
    },
  ],

  // Ingress rules
  ingressSecurityRules: [
    // SSH (standard — only during initial bootstrap, can be removed after)
    {
      protocol: "6", // TCP
      source: "0.0.0.0/0",
      tcpOptions: { max: 22, min: 22 },
      description: "SSH (standard)",
    },
    // SSH (custom port — Ansible uses this after hardening)
    {
      protocol: "6",
      source: "0.0.0.0/0",
      tcpOptions: { max: 2222, min: 2222 },
      description: "SSH (hardened port)",
    },
    // HTTP
    {
      protocol: "6",
      source: "0.0.0.0/0",
      tcpOptions: { max: 80, min: 80 },
      description: "HTTP",
    },
    // HTTPS
    {
      protocol: "6",
      source: "0.0.0.0/0",
      tcpOptions: { max: 443, min: 443 },
      description: "HTTPS",
    },
    // ICMP type 3 (destination unreachable) — required for path MTU discovery
    {
      protocol: "1", // ICMP
      source: "0.0.0.0/0",
      icmpOptions: { type: 3, code: 4 },
      description: "ICMP path MTU discovery",
    },
    // ICMP type 8 (echo / ping)
    {
      protocol: "1",
      source: "0.0.0.0/0",
      icmpOptions: { type: 8 },
      description: "ICMP ping",
    },
  ],
});

// ── Public Subnet ─────────────────────────────────────────────────────────────
const subnet = new oci.core.Subnet(`${projectName}-subnet`, {
  compartmentId,
  vcnId: vcn.id,
  cidrBlock: "10.0.0.0/24",
  displayName: `${projectName}-subnet`,
  dnsLabel: "public",
  routeTableId: routeTable.id,
  securityListIds: [securityList.id],
  prohibitPublicIpOnVnic: false,
});

// ── Compute Instance ──────────────────────────────────────────────────────────
// VM.Standard.A1.Flex — Oracle Always Free: 4 OCPU, 24 GB RAM total per account
const instance = new oci.core.Instance(`${projectName}-vm`, {
  compartmentId,
  availabilityDomain: pulumi.output(
    oci.identity.getAvailabilityDomains({ compartmentId })
  ).apply((ads) => ads.availabilityDomains[0].name),

  displayName: `${projectName}-vm`,
  shape: "VM.Standard.A1.Flex",
  shapeConfig: {
    ocpus: 4,
    memoryInGbs: 24,
  },

  sourceDetails: {
    sourceType: "image",
    imageId: imageOcid,
    // 200 GB boot volume — uses all of the Always Free block storage allocation
    bootVolumeSizeInGbs: 200,
  },

  createVnicDetails: {
    subnetId: subnet.id,
    assignPublicIp: "true",
    displayName: `${projectName}-vnic`,
  },

  metadata: {
    ssh_authorized_keys: sshPublicKey,
    // cloud-init: iptables rules so OCI firewall allows ports 80/443/2222
    // (OCI has a host-level iptables firewall on top of the Security List)
    user_data: Buffer.from(cloudInit).toString("base64"),
  },
});

// ── Cloud-init (iptables) ─────────────────────────────────────────────────────
// OCI Ubuntu images ship with iptables rules that block ports not in the default
// ACCEPT chain. Ansible handles hardening, but cloud-init opens the ports that
// Caddy and SSH need so the first Ansible run can connect.
const cloudInit = `#!/bin/bash
set -e

# Allow Ansible SSH (standard + hardened port), HTTP, HTTPS
iptables  -I INPUT 1 -p tcp --dport 22   -j ACCEPT
iptables  -I INPUT 2 -p tcp --dport 2222 -j ACCEPT
iptables  -I INPUT 3 -p tcp --dport 80   -j ACCEPT
iptables  -I INPUT 4 -p tcp --dport 443  -j ACCEPT
ip6tables -I INPUT 1 -p tcp --dport 22   -j ACCEPT
ip6tables -I INPUT 2 -p tcp --dport 2222 -j ACCEPT
ip6tables -I INPUT 3 -p tcp --dport 80   -j ACCEPT
ip6tables -I INPUT 4 -p tcp --dport 443  -j ACCEPT

# Persist rules across reboots
apt-get install -y iptables-persistent
netfilter-persistent save
`;

// ── Outputs ───────────────────────────────────────────────────────────────────
export const publicIp = instance.publicIp;
export const sshCommand = pulumi.interpolate`ssh -p 2222 deploy@${instance.publicIp}`;
export const vcnId = vcn.id;
export const subnetId = subnet.id;
