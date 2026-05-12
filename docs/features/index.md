# Features

The goal of the automation is to provide the following high level capabilities.

## Day 1

### Prerequisites

- [Infrastructure-as-Code](../design/infrastructure-as-code/index.md)
- [Prerequisites](day1/deployment-prerequisites.md)
- [Host Prechecks](day1/precheck/precheck.md)
    - [Host Connection](day1/precheck/host-connection.md).
    - [Host SSH Settings](day1/precheck/host-ssh-service.md)
    - [Host NTP Settings](day1/precheck/host-ntp-settings.md)
    - [Host Network Configuration](day1/precheck/host-network-configuration.md)
  
### Deployment
- [Manage VCF Installer Deployment](day1/installer-deployment.md)
- [Manage VCF Installer Trusted Certificates](day1/trusted-certificate-installer.md)
- [Manage VCF Installer Depot Settings](day1/depot-installer.md)
- [Manage VCF Installer CEIP Settings](day1/ceip-installer.md)
- [Manage VCF Installer Proxy Settings](day1/proxy-installer.md)
- [Deploy VCF Instance](day1/instance.md)

## Day 2

- [Manage Network Pools](day2/network-pool.md)
- [Manage Hosts](day2/host.md)
- [Manage Workload Domains](day2/workload-domain.md)
- [Manage Clusters](day2/cluster.md)
- [Manage Cluster Hosts](day2/cluster-hosts.md)
- [Manage NSX Edge Clusters](day2/nsx-edge-cluster.md)
- [Manage Trusted Certificates](day2/trusted-certificate.md)
- [Manage Depot Settings](day2/depot.md)
- [Manage CEIP Settings](day2/ceip.md)
- [Manage Proxy Settings](day2/proxy.md)
- [Manage NTP Settings](day2/ntp.md)
- [Manage DNS Settings](day2/dns.md)
- [Manage Certificate Authority Settings](day2/certificate-authority.md)

## Utilities

- [Manage Vaulted Passwords](utilities/ansible-vault.md)
- [SSH ECDSA Fingerprint](utilities/ssh-ecdsa-fingerprint.md)
- [SSL Certificate Fingerprint](utilities/ssl-fingerprint.md)
- [Trusted SSL Certificate Payload](utilities/trusted-ssl-certificate-payload.md)
 
## Goal of Deliverables

Each feature is a collection of a set of smaller **use cases** which represent the various ways the automation may be used.

A capability commonly outside the scope of all the features is to detect changes and remediate drift.  This was deemed too complex and time consuming to support, as it would require countless permutations of testing in order to validate the functionality of that capability.

## Getting Started

All the features are initiated by Ansible playbooks. To use the Ansible playbooks, the system structure must be defined in YAML format. The complete picture of how it operates and is initiated for each of the features is defined in the [high-level design](../design/high-level-design.md) as they all follow the same process.

### Feature Prerequisites

Each feature lists a set of prerequisites that must be considered and prepared for before proceeding with its use. Therefore, specific a _getting started_ will look different depending on if you're looking to take advantage of Day 1 vs Day 2 automation.

### Implementation Plan

A guide which walks through the set of supported features can be followed using the [Implementation Plan](../design/implementation-plan.md), which also provides guidance specific to the lab build out.
