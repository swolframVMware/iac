# Day 1: Manage VCF Installer Appliance

## Overview

This workflow manages the lifecycle of the VCF Installer appliance in a vSphere
environment using the `broadcom.vcf.vcf_installer.appliance` role and the
`vcf_installer_appliance` module.

Supported operations:

- Add the VCF Installer appliance to an environment.
- Remove the VCF Installer appliance to an environment.
- Validate that all required resources exist before deployment.

The role is state-driven via `appliance_state`:

- `present` – deploy the VCF Installer appliance (default).
- `absent` – remove the VCF Installer appliance.
- `validate` – validate that required vSphere resources exist without deploying.

## Prerequisites

Before you begin, make sure:

1. [Deployment prerequisites](../day1/deployment-prerequisites.md) are met.
2. A vCenter instance or standalone ESX host is reachable with valid credentials.
3. The VCF Installer OVA file is accessible via a local file path or URL.
4. Infrastructure-as-Code (IaC) data is defined under `./infra-as-code/`.
5. You can authenticate to vCenter or ESX with sufficient privileges to:
    - Deploy virtual machines from OVA/OVF templates.
    - Power on virtual machines.
    - Remove virtual machines (for `absent` state).

## Configuration Requirements

The following configuration must be provided under `./infra-as-code/`:

- VCF Installer appliance configuration:
    - Appliance hostname, IP address, netmask, and gateway.
    - VM name as it will appear in the vSphere inventory.
    - Path or URL to the VCF Installer OVA file.
    - OVF network to vSphere port group mapping.

- vSphere deployment target configuration:
    - vCenter or ESX host hostname and credentials.
    - Datacenter, cluster or ESX host, and datastore names.
    - Optional: folder, resource pool, disk provisioning type.

- DNS and NTP settings:
    - By default, shared `dns.yml` and `ntp.yml` IaC files are used.
    - Override with `dns_servers`, `ntp_servers`, `dns_domain`, or `dns_search` if
      needed.

The role reads configuration from the IaC structure at `all_iac_vars.vcf_installer`:

## Role Interface

Role: `broadcom.vcf.vcf_installer.appliance`

### Variables

Key variables:

- `appliance_state` - Desired state of the VCF Installer appliance.
    - `present` (default): deploy the appliance.
    - `absent`: remove the appliance.
    - `validate`: validate vSphere resources only.

**Credential Variables** (can be passed directly or read from IaC):

- `vcf_installer_vsphere_password` - Password for the vCenter or ESX host.
    - Default: Read from IaC at `all_iac_vars.vcf_installer.deployment.password`.
- `vcf_installer_root_password` - Root password for the VCF Installer appliance VM.
- `vcf_installer_local_password` - Local user (`admin@local`) password for the appliance
  API.

Additional inputs are drawn from your IaC structure at `all_iac_vars.vcf_installer`:

- `all_iac_vars.vcf_installer.hostname`
- `all_iac_vars.vcf_installer.username`
- `all_iac_vars.vcf_installer.vm_name`
- `all_iac_vars.vcf_installer.ip_address`
- `all_iac_vars.vcf_installer.deployment.hostname`
- `all_iac_vars.vcf_installer.deployment.username`
- `all_iac_vars.vcf_installer.deployment.datastore`
- `all_iac_vars.vcf_installer.deployment.networks`

### Return Values

- `changed` - Boolean indicating if changes were made.
- `msg` - Status message describing the operation result.
- `instance` - Dictionary of VM facts for the deployed or existing appliance.

## Execution

### Add Appliance (`appliance_state: present`)

Example:

```yaml
- name: Add VCF Installer Appliance
  hosts: localhost
  roles:
    - role: broadcom.vcf.vcf_installer.appliance
      vars:
        appliance_state: present
        vcf_installer_vsphere_password: "{{ vsphere_password }}"
        vcf_installer_root_password: "{{ root_password }}"
        vcf_installer_local_password: "{{ local_password }}"
```

Behavior:

1. Build vApp properties from IaC configuration:
    - Assembles network, DNS, NTP, and credential properties into an OVF property map.
2. Deploy the appliance:
    - Calls `vcf_installer_appliance` with `state: present`.
    - Checks if a VM with the same name already exists.
    - If the VM already exists: displays a message and stops the playbook immediately.
    - If the VM does not exist: deploys the OVA to the target vSphere environment.
    - Powers on the appliance and waits for an IP address (configurable).
3. Wait for the VCF Installer API to become available (configurable):
    - Polls the VCF Installer API until it responds (default: 60 retries × 30 seconds).
    - Fails if the API does not become available within the retry window.
4. Display API status on successful deployment.

#### Deployment Targets

The role supports three deployment scenarios:

**vCenter with cluster** (most common):

```yaml
deployment:
  hostname: vc01.example.com
  datacenter: dc01
  cluster: cl01
  datastore: ds01
```

**vCenter with specific ESX host**:

```yaml
deployment:
  hostname: vc01.example.com
  datacenter: dc01
  esx_hostname: esx01.example.com
  datastore: ds01
```

**Standalone ESX host** (no vCenter):

```yaml
deployment:
  hostname: esx01.example.com
  datacenter: ha-datacenter
  datastore: ds01
```

!!! note "Standalone ESX Deployments"
    When deploying to a standalone ESX host, omit the `datacenter`, `cluster`, and
    `esx_hostname` fields. The `hostname` in the deployment section points directly to
    the ESX host for both connection and deployment target.

#### OVA Source Options

Use a local file path:

```yaml
deployment:
  ova_path: /mnt/f/VCF-SDDC-Manager-Appliance-9.x.x.x.ova
```

Use a remote URL:

```yaml
deployment:
  ova_url: https://packages.example.com/VCF-SDDC-Manager-Appliance-9.x.x.x.ova
```

Use a remote URL with Basic Authentication:

```yaml
deployment:
  ova_url: https://packages.example.com/VCF-SDDC-Manager-Appliance-9.x.x.x.ova
  ova_url_username: "vcf"
  ova_url_password: {{ vault_vcf_installer_ova_url_password}}
```

!!! warning "OVA Source"
    `ova_path` and `ova_url` are mutually exclusive. Only one may be specified.
    When `ova_url` requires Basic Authentication, provide `ova_url_username` and
    `ova_url_password` in IaC. These are mapped to the module's `url_username` and
    `url_password` parameters internally. Local file paths (`ova_path`) are generally
    more reliable for large OVA files as they avoid potential network transfer
    timeouts.

#### Check Mode Behavior: `present`

When run with `--check`, the module validates all vSphere resources and returns a
detailed deployment plan without making any changes:

```shell
Check Mode: Would deploy VCF Installer appliance 'vcf-installer'; no changes were performed.
```

The check mode result includes:

- `deployment_plan` - Full details of what would be deployed:
    - VM name, datacenter, datastore, resource pool, folder.
    - Deployment target type (cluster or ESX host) and name.
    - Disk provisioning type.
    - Power-on and IP wait settings.
    - OVA source path or URL.
    - Files to be uploaded with sizes.
    - Total upload size in bytes.
- `network_mappings` - OVF network to vSphere port group mappings.
- `properties_count` - Number of vApp properties to be configured.

No API calls are made to deploy the appliance.

### Remove Appliance (`appliance_state: absent`)

Example:

```yaml
- name: Remove VCF Installer Appliance
  hosts: localhost
  roles:
    - role: broadcom.vcf.vcf_installer.appliance
      vars:
        appliance_state: absent
        vcf_installer_vsphere_password: "{{ vsphere_password }}"
```

Behavior:

1. Check if the appliance VM exists:
    - If the VM does not exist: displays a message and exits with `changed=false`.
    - If the VM exists: proceeds with removal.
2. Remove the appliance:
    - Powers off the VM if it is running (the role passes `force: true`).
    - Destroys the VM and removes it from the vSphere inventory.
3. Display removal result.

#### Check Mode Behavior: `absent`

When run with `--check`, the module returns a message without making changes:

```shell
Check Mode: Would remove VCF Installer appliance 'vcf-installer'; no changes were performed.
```

```shell
Check Mode: Would power off and remove VCF Installer appliance 'vcf-installer'; no changes were performed.
```

- No API calls are made to remove the appliance.

### Validate vSphere Resources (`appliance_state: validate`)

Example:

```yaml
- name: Validate vSphere Resources
  hosts: localhost
  roles:
    - role: broadcom.vcf.vcf_installer.appliance
      vars:
        appliance_state: validate
        vcf_installer_vsphere_password: "{{ vsphere_password }}"
```

Behavior:

1. Connect to the vCenter or ESX host.
2. Validate the existence and accessibility of:
    - Datacenter.
    - Cluster or ESX host (based on configuration).
    - Datastore (including free space information).
    - Folder (if specified).
    - All configured vSphere networks (port groups).
3. Display a detailed validation report.
4. Fail if any required resource is missing or inaccessible.

Validation output example:

```
vSphere Resource Validation Results:
  Overall Status: VALID
  Datacenter: EXISTS
  Cluster: EXISTS
  Datastore: EXISTS (Free: 1024GB)
  Networks:
    - Network 1: EXISTS
```

## SDK / API Calls

The following vSphere APIs are used by the supporting module utility
(`plugins/module_utils/vsphere.py`):

- vSphere OVF Manager – Deploys the VCF Installer appliance from OVA/OVF.
- vSphere VirtualMachine - Powers on, powers off, and destroys VMs.
- vSphere PropertyCollector – Polls for IP address assignment after power-on.
- vSphere Datacenter, ClusterComputeResource, HostSystem, Datastore, Network - Used
  for resource validation and deployment target selection.

## Ansible Components

- Module Utils:
    - `plugins/module_utils/vsphere.py`

- Modules:
    - `plugins/modules/vcf_installer_appliance.py`

- Roles:
    - `roles/vcf_installer/appliance`

- Playbooks:
    - `playbooks/add_installer_appliance.yml` (Uses `appliance_state: present`)
    - `playbooks/remove_installer_appliance.yml` (Uses `appliance_state: absent`)

## Module: `vcf_installer_appliance`

The `vcf_installer_appliance` module manages the full lifecycle of the VCF Installer
appliance VM in a vSphere environment.

### Parameters

**Connection Parameters**:

- `hostname` - (Required) FQDN or IP address of the vCenter instance or ESX host used
  to connect and authenticate. For standalone ESX deployments, this is also the
  deployment target.
- `username` - (Required) Username to authenticate with the vCenter instance or ESX
  host.
- `password` - (Required) Password to authenticate with the vCenter instance or ESX
  host.
- `port` - (Optional) Port number of the vCenter or ESX host. Default: `443`.
- `validate_certs` - (Optional) Whether to validate SSL certificates. Default: `true`.

**Deployment Target Parameters**:

- `name` - (Required) Name of the VCF Installer VM in the vSphere inventory.
- `datacenter` - (Optional) Name of the vSphere datacenter. Default: `ha-datacenter`.
- `cluster` - (Optional) Name of the vSphere cluster for deployment. Mutually exclusive
  with `esx_hostname`.
- `esx_hostname` - (Optional) FQDN of a specific ESX host within a vCenter-managed
  datacenter. Use when deploying to a specific host rather than letting vCenter choose.
  Mutually exclusive with `cluster`.
- `datastore` - (Required) Name of the datastore for deployment. Supports datastore
  clusters (automatically selects the datastore with the most free space).
- `folder` - (Optional) Absolute path of the vSphere folder. Default: datacenter VM
  folder (e.g., `/datacenter1/vm`).
- `resource_pool` - (Optional) Name of the vSphere resource pool. Default: `Resources`.

**OVA Source Parameters** (one required for `state: present`):

- `ovf` - Local OVF/OVA file path. Mutually exclusive with `url`. (Alias: `ova`)
- `url` - URL to a remote OVF/OVA file. Mutually exclusive with `ovf`.
- `url_username` - (Optional) Username to authenticate with the remote OVA URL.
- `url_password` - (Optional) Password to authenticate with the remote OVA URL.

**Deployment Configuration Parameters**:

- `networks` - (Optional) Mapping of OVF network names to vSphere port group names.
  Default: `{"Network 1": "VM Network"}`.
- `properties` - (Optional) vApp properties to configure on the deployed VM.
- `disk_provisioning` - (Optional) Disk provisioning type. Choices: `thin`, `thick`,
  `eagerZeroedThick`. Default: `thin`.
- `power_on` - (Optional) Power on the appliance after deployment. Default: `true`.
- `wait_for_ip_address` - (Optional) Wait for the VM to receive an IP address after
  power-on. Default: `true`.
- `force` - (Optional) Force removal when `state: absent` by powering off the VM if
  running. Default: `false`.
- `allow_duplicates` - (Optional) Allow deploying a VM with the same name as an
  existing VM. Default: `false`.
- `fail_on_spec_warnings` - (Optional) Fail the deployment if OVF spec warnings are
  reported. Default: `false`.
- `state` - (Optional) Desired state. Choices: `present`, `absent`, `validate`.
  Default: `present`.

### Return Values

- `msg` - Human-readable message about the operation result.
- `changed` - Whether the operation resulted in changes.
- `instance` - Dictionary of VM facts (returned when `state: present`):
    - `hw_name` - VM name.
    - `hw_power_status` - Power state (`poweredOn`, `poweredOff`).
    - `hw_guest_full_name` - Guest OS full name.
    - `hw_product_uuid` - VM product UUID.
    - `instance_uuid` - VM instance UUID.
    - `ipv4` - Primary IPv4 address.
- `deployment_plan` - Detailed deployment plan (check mode only).
- `validation` - vSphere resource validation results (returned when `state: validate`).
- `missing_resources` - List of missing or inaccessible resources (when
  `state: validate` and validation fails).

### vApp Properties

The role automatically configures the following vApp properties on the deployed
appliance from the IaC configuration:

| Property                       | Description                   | Source                                  |
|--------------------------------|-------------------------------|-----------------------------------------|
| `vami.hostname`                | FQDN of the appliance         | `all_iac_vars.vcf_installer.hostname`   |
| `vami.ip0.SDDC-Manager`        | IP address                    | `all_iac_vars.vcf_installer.ip_address` |
| `vami.netmask0.SDDC-Manager`   | Subnet mask                   | `all_iac_vars.vcf_installer.netmask`    |
| `vami.gateway.SDDC-Manager`    | Default gateway               | `all_iac_vars.vcf_installer.gateway`    |
| `vami.DNS.SDDC-Manager`        | DNS servers (comma-separated) | `all_iac_vars.dns.servers`              |
| `vami.domain.SDDC-Manager`     | DNS domain                    | `all_iac_vars.dns.domain_name`          |
| `vami.searchpath.SDDC-Manager` | DNS search path               | `all_iac_vars.dns.domain_name`          |
| `guestinfo.ntp`                | NTP servers (comma-separated) | `all_iac_vars.ntp`                      |
| `ROOT_PASSWORD`                | Root OS password              | `vcf_installer_root_password`           |
| `LOCAL_USER_PASSWORD`          | Admin API user password       | `vcf_installer_local_password`          |

## Usage Examples

### Example 1: Deploy Appliance Using Playbook

```bash
ansible-playbook playbooks/add_installer_appliance.yml \
  -e @examples/lab-arkham/vars/installer_automation_settings.yml \
  --ask-vault-pass
```

### Example 2: Remove Appliance Using Playbook

```bash
ansible-playbook playbooks/remove_installer_appliance.yml \
  -e @examples/lab-arkham/vars/installer_automation_settings.yml \
  --ask-vault-pass
```

### Example 3: Preview Deployment with Check Mode

```bash
ansible-playbook playbooks/add_installer_appliance.yml \
  -e @examples/lab-arkham/vars/installer_automation_settings.yml \
  --check
```

### Example 4: Inline Variables

```bash
ansible-playbook playbooks/add_installer_appliance.yml \
  -e "region=amer datacenter=dc1 az=az1 vcf=lab-arkham"
```

### Example 5: Deploy to Standalone ESX Host

Configure the IaC file to point `deployment.hostname` directly to the ESX host and
omit `datacenter`, `cluster`, and `esx_hostname`:

```yaml
vcf_installer:
  deployment:
    hostname: esx-01.example.com
    username: root
    password: "{{ vcf_installer_vsphere_password }}"
    datastore: datastore1
    networks:
      "Network 1": "VM Network"
```

Then run:

```bash
ansible-playbook playbooks/add_installer_appliance.yml \
  -e @examples/lab/vars/installer_automation_settings.yml
```

## Workflow Sequence

### Deploy Appliance Workflow

1. `playbooks/add_installer_appliance.yml` is triggered.
2. `iac/get_settings` combines all IaC data into `all_iac_vars`.
3. `vcf_installer/appliance` role executes with `appliance_state: present`:
    - Assembles vApp properties from IaC configuration.
    - Calls `vcf_installer_appliance` with `state: present`.
    - If VM already exists: displays message and stops the playbook.
    - If VM does not exist: uploads and deploys the OVA.
    - Powers on the VM and waits for IP address assignment.
    - Waits for the VCF Installer API to become available (up to ~30 minutes).
    - Displays API status on success.

### Remove Appliance Workflow

1. `playbooks/remove_installer_appliance.yml` is triggered.
2. `iac/get_settings` combines all IaC data into `all_iac_vars`.
3. `vcf_installer/appliance` role executes with `appliance_state: absent`:
    - Calls `vcf_installer_appliance` with `state: absent` and `force: true`.
    - If VM does not exist: displays message and exits with `changed=false`.
    - If VM exists and is powered on: powers off the VM.
    - Destroys the VM from the vSphere inventory.
    - Displays removal result.
