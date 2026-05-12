# Implementation Plan

## Overview

This implementation plan captures how this repository can be used to go through an
example VMware Cloud Foundation deployment.

As detailed in the [High-Level Design](../design/high-level-design.md), all of the code
will require the IaC inputs.

## Common / Initial Configurations

### Inputs

#### IaC Inputs

Provide the following inputs to get down to the specific domain from the IaC data:

- `region`
- `datacenter`
- `az`
- `vcf`
- `domain`

The IaC Loader needs as many as a required to find the specific domain. Initially,
likely just the VCF instance and domain name may be all that's necessary (_e.g._,
`vcf` = `vcf_poc_lab`, and `domain` = `mgmt`).

#### Password Overrides

The IaC datasets in the lab provides the passwords, however these need to be passed in
as variables (Credentials or Survey in AAP). Here's the list of expected variables that
are used by the various playbooks, all collate in one spot in order to make it easier
for setup:

- `esx_host_password` (shared password for now)
- `vcf_installer_password`
- `vcenter_root_password`, `vcenter_administrator_password`
- `nsx_root_password`, `nsx_admin_password`, `nsx_audit_password`
- `sddc_manager_root_password`, `sddc_manager_admin_password`, `sddc_manager_vcf_password`

The shipped sample IaC files reference dedicated Ansible Vault variables
(`vault_*`) instead of embedding demo passwords. Populate those vaulted values in
your inventory, AAP credential inputs, or vaulted vars files before running the
playbooks. See [Manage Vaulted Passwords](../features/utilities/ansible-vault.md)
for a step-by-step setup workflow.

## Pre-Deployment

**Configure:**

- [Deploy Prerequisites](../features/day1/deployment-prerequisites.md)
- Configure the IaC dataset with the management domain information
    - particularly under `vsphere.yml` with the ESX hosts under `vsphere.datacenter.clusters`
- Configure Credentials within AAP which will override the expected IaC data for the passwords

**Perform:**

- [Perform initial pre-checks, primarily against the Hosts](../features/day1/precheck/precheck.md)
    - portions are manual (or pre-configuredModule: `the Reset Hosts automation)
    - portions are covered by the `preconfig_prechecks.yaml` playbook. Create and run a template against those with the IaC inputs.

**Validate:**

To validate, log into an ESX system and ensure the following:

- generally, that they meet the specifics called out by the [prechecks](../features/day1/precheck/precheck.md)
- ensure that no vSAN disks are present (from previous usage)  
- ensure SSH has been turned on
- ensure the NTP settings are valid

## Deploy a Management Domain

**Configure:**

Follow these guides to configure the systems and ensure availability against the systems.

- Configure the IaC dataset with the management domain information
    - use the IaC path to AMER/gcp_lab/mgmt as a good example
    - along with other data configurations, make sure to configure:
        - the vsphere.yml to have the initial MGMT cluster
        - the vcf_installer.yml to include details for the VCF Installer instance that will be used
    - _the WLD folder is not necessary to fill out at this point in time_
- Configure Credentials within AAP which will override the expected IaC data for the passwords
- Reset the VCF Installer instance (as needed)

**Perform:**

Kick off the Ansible Automation Platform Template which initiates the `create_mgmt_domain.yml` playbook.  It only needs the standard IaC inputs.

If issues arise, the error messages may indicate what needs to be corrected.  If additional details are needed, check within VCF Installer or SDDC Manager (depending on how far it made it).  If the code does not expect to be restarted from there, you may be able to continueModule: `SDDC Manager directly.  If necessary, start again by resetting the hosts and trying again (which may be desirable in any case, as the installation is a clean run).

**Validate:**

To validate, log into SDDC Manager and look at the Workload Domains to see the management domain is present.  Navigate to it and see that the system was deployed with 4 hosts and that it matches what is within the vsphere.yml IaC.

**Post-Deploy:**

Update SDDC Manager to add the license keys.

## Add a Cluster to a Management Domain

**Configure:**
Follow these guides to configure the systems and ensure availability against systems.

- Configure the domain  domain IaC dataset with the additional ESX Host information and must at least 3
    - The Files to be updated are in ../regions/{region name}/datacenters/{datacenter name}/vcfs/{vcf instance}/domains/{domain name}/config/
    - along with other data configurations, make sure to configure:
        - the vsphere.yml to have additional ESX hosts that will be added to the cluster
- Configure Credentials within AAP which will override the expected IaC data for the passwords

**Perform:**

Kick off the Ansible Automation Platform Template which initiates the `add_cluster.yml` playbook.  Inputs for `domain_input`  and `cluster_input` will need to be provided to make sure we pull the correct IaC dataset and that we have the correct cluster and hosts that we're using for adding the host to the cluster.

If issues arise, the error messages may indicate what needs to be corrected.  If additional details are needed, check within SDDC Manager for more information.  After remediating the errors,  you may be able to continueModule: `SDDC Manager directly depending on where it failed.  If it fails again you can check the SDDC manager logsModule: `ssh to SDDC Manager and investigate the logs  `/var/log/vmware/vcf/domainmanager/domainmanager.log`.  If necessary, start again by resetting the hosts and trying again (which may be desirable in any case, as the hosts addition is a clean run).

**Validate:**

To validate, log into SDDC Manager and look at the Workload Domains to find the the domain you added the cluster to.  Navigate to the domain and see that the additional cluster that was added and that it matches what is within the vsphere.yml IaC.

## Add 4th host to the Management Domain

**Configure:**

Follow these guides to configure the systems and ensure availability against the systems.

- Configure the management domain IaC dataset with the additional ESX Host information
    - use the IaC path to AMER/gcp_lab/mgmt as a good example
    - along with other data configurations, make sure to configure:
        - the vsphere.yml to have additional ESX hosts that will be added to the cluster
- Configure Credentials within AAP which will override the expected IaC data for the passwords

**Perform:**

Kick off the Ansible Automation Platform Template which initiates the `add_hosts.yml` playbook.  Inputs for `domain`, `cluster_input`, and `hosts_input` will need to be provided to make sure we pull the correct IaC dataset and that we have the correct cluster and hosts that we're using for adding the host.

If issues arise, the error messages may indicate what needs to be corrected.  If additional details are needed, check within SDDC Manager for more information.  After remediating the errors, check the hosts to see if they have been commissioned. If hosts have not been commissioned you can reRun the playbook. If the hosts have been commissioned, you may be able to continueModule: `SDDC Manager directly depending on where it failed.  If necessary, start again by resetting the hosts and trying again (which may be desirable in any case, as the host addition is a clean run).

**Validate:**

To validate, log into SDDC Manager and look at the Workload Domains to find the management domain.  Navigate to the domain and see that the additional ESX hosts were added to the cluster and that it matches what is within the vsphere.yml IaC.

## Deploy a Workload Domain

**Configure:**

Follow these guides to configure the systems and ensure availability against the systems.

- Configure the IaC dataset with the WLD domain information
    - use the IaC path to AMER/gcp_lab/wld as a good example
    - along with other data configurations, make sure to configure:
        - the vsphere.yml to have the WLD cluster
- Configure Credentials within AAP which will override the expected IaC data for the passwords
- Manually configure new WLD network pool in SDDC to use in the WLD deployment

**Perform:**

Kick off the Ansible Automation Platform Template which initiates the `add_workload_domain.yml` playbook.  It only needs the standard IaC inputs.

If issues arise, the error messages may indicate what needs to be corrected.  If additional details are needed, check within SDDC Manager.  After remediating the errors, check the hosts to see if they have been commissioned. If hosts have not been commissioned you can reRun the playbook.  If the hosts have been commissioned, you may be able to continueModule: `SDDC Manager directly depending on where it failed.  If necessary, start again by resetting the hosts and trying again (which may be desirable in any case, as the installation is a clean run).

**Validate:**

To validate, log into SDDC Manager and look at the Workload Domains to see the WLD domain is present.  Navigate to it and see that the system was deployed with 3 hosts and that it matches what is within the vsphere.yml IaC.

## Deploy an NSX Edge Cluster for a Workload Domain

**Configure:**

Follow these guides to configure the systems and ensure availability against the systems.

- Configure the IaC dataset with the NSX Edge cluster information
    - use the IaC path to AMER/gcp_lab1/wld/nsx as a good example
    - along with other data configurations, make sure to configure:
        - the nsx.yml to have the edge_cluster and edge_nodes section
- Configure Credentials within AAP which will override the expected IaC data for the passwords

**Perform:**

Kick off the Ansible Automation Platform Template which initiates the `create_edge_cluster.yml` playbook.  It needs the standard IaC inputs as well as the domain and cluster_input specifying which cluster the edge nodes will be added to.

If issues arise, the error messages may indicate what needs to be corrected.  If additional details are needed, check within SDDC Manager.  Depending on where it failed you may need to delete what was deployed before retrying the automation. If it failed for validation reasons, fix the problem and retry the automation. If it failed post validation, check if there is an edge cluster present in SDDC.

**Validate:**

To validate log into SDDC manager and select the workload domain you deployed the nsxt edge cluster to, then select edge clusters. You should see the edge cluster deployed and active. Then check NSX under the Networking tab for Network Topology, Tier 0 Gateway, Tier 1 Gateway, and Segments. On the System tab select Fabric -> Nodes. Check that the edge nodes are present and linked to the edge cluster that was just created.
