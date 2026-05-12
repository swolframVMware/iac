# Day 2: Manage DNS

## Overview

This workflow manages DNS (Domain Name System) in VMware Cloud Foundation using the
`broadcom.vcf.sddc_manager.dns` role and the `sddc_manager_dns` module.

Supported operations:

- Update DNS Configuration (update).

The role is state-driven via `dns_state`:

- `update` – update DNS configuration.

!!! warning "Requirements"
    When `dns_state: update`:

    Use Ansible's check mode (`--check`) to preview changes before execution.

## Prerequisites

Before you begin, make sure:

1. [Deployment prerequisites](../day1/deployment-prerequisites.md) are met.
2. Management domain is deployed and SDDC Manager is operational.
3. SDDC Manager is reachable and you have administrative credentials.
4. Infrastructure‑as‑Code (IaC) data for DNS is defined under
   `./infra-as-code/` (typically in `dns.yml`).
5. You can authenticate to SDDC Manager with sufficient privileges to:
   - Update DNS configuration.
   - Query DNS information.

## Configuration Requirements

The following configuration must be provided under `./infra-as-code/`:

- DNS configuration (`dns.yml`):
    - DNS IP address or FQDN.

- SDDC Manager configuration:
    - SDDC Manager hostname and admin credentials.

## Role Interface

Role: `broadcom.vcf.sddc_manager.dns`

### Variables

Key variables:

- `dns_state` - Desired state of the DNS.
    - `update` (default): update DNS configuration.

### Return Values

- `changed` - Boolean indicating if changes were made.
- `msg` - Status message.
- `meta` - Response data from SDDC Manager.

Additional inputs are drawn from your IaC structure, e.g. `all_iac_vars`:

- `all_iac_vars.sddc_manager.hostname`
- `all_iac_vars.vsphere.vcenter.sso.username`
- `all_iac_vars.vsphere.vcenter.sso.password` or overrides
- `dns_config` - DNS configuration (extracted from dns in IaC). Required when `state: update`.

## Execution

### Update DNS (`dns_state: update`)

Example:

```yaml
- name: Update DNS Configuration
  ansible.builtin.include_role:
    name: broadcom.vcf.sddc_manager.dns
  vars:
    dns_state: update
```

Behavior:

1. Find DNS in IaC:
    - Extracts all DNS data in IaC.
    - Sets `dns_config` variable with DNS configurations.

2. Validate DNS configuration (`validate_dns_config.yml`):
    - Calls `sddc_manager_dns` with:
        - `state: update`
        - `validate_only: true`
    - If validation completes (`executionStatus: COMPLETED`):
        - Displays success message and continues.
    - Fails if validation errors are returned.

3. Update DNS (`update_dns_config.yml`):
    - Calls `sddc_manager_dns` for dns with:
        - `state: update`
    - Receives current DNS information.
    - If current DNS information is the same as required dns_config:
        - Displays compliant message.
        - Returns `changed: false`.
    - If current DNS information is different from required dns_config:
        - Updates DNS.
        - Receives new DNS information.
        - If new DNS information is the same as required dns_config, displays success message
    - Fails if update errors are returned.

#### Check Mode Behavior: `update`

- The module detects check mode and returns a message:

    ```shell
    Check Mode: Would update DNS configuration from xxx to yyy. No changes were performed.
    ```

- The role:
    - Displays this message.
    - Skips changes.

This gives you a dry run preview without updating DNS.

## SDK / API Calls

The following SDDC Manager endpoints are used by the supporting module utility (`plugins/module_utils/sddc_manager.py`):

For update:

- `GET /v1/system/dns-configuration` - Retrieves the DNS configuration.
- `PUT /v1/system/dns-configuration` - Updates the DNS configuration.
- `POST /v1/system/dns-configuration/validations` - Perform validation of the DNS configuration specification.
- `GET /v1/system/dns-configuration/validations` - Retrieves a list of DNS configuration validation.

## Ansible Components

- Module Utils:
    - `plugins/module_utils/sddc_manager.py`

- Modules:
    - `plugins/modules/sddc_manager_dns.py`
    - `plugins/modules/sddc_manager_dns_info.py`

- Roles:
    - `roles/sddc_manager/dns`
    - `roles/sddc_manager/dns_info`

- Playbooks:
    - `playbooks/update_dns.yml` (Uses `dns_state: update`)
    - `playbooks/get_dns_info.yml` (Informational only)

## Querying Information

The `sddc_manager_dns_info` module and `dns_info` role provide read-only access to DNS information.

### Module: `sddc_manager_dns_info`

This informational module retrieves DNS information from SDDC Manager without making any changes.

Parameters:

- `sddc_manager_hostname` - (Required) SDDC Manager hostname or IP address.
- `sddc_manager_user` - (Required) SDDC Manager username.
- `sddc_manager_password` - (Required) SDDC Manager password.

Return Values:

- `dns_info` - DNS configuration information.
- `changed` - Always `false` (read-only operation).
- `msg` - Human-readable status message.

Example:

```yaml
- name: Get DNS Configuration
  broadcom.vcf.sddc_manager_dns_info:
    sddc_manager_hostname: "{{ all_iac_vars.sddc_manager.hostname }}"
    sddc_manager_user: "{{ all_iac_vars.vsphere.vcenter.sso.username }}"
    sddc_manager_password: "{{ vcenter_administrator_password | default(all_iac_vars.vsphere.vcenter.sso.password) }}"
  register: dns_info

- name: Display DNS Information
  ansible.builtin.debug:
    msg: "{{ dns_info.msg }}"
```

### Role: `dns_info`

This role wraps the `sddc_manager_dns_info` module to retrieve DNS information and set it as a fact.

Variables:

- No input variables required. Uses IaC settings from `all_iac_vars`.

Sets the following facts:

- `dns_info` - Complete DNS configuration response.

Example:

```yaml
- name: Get IaC Settings
  ansible.builtin.include_role:
    name: broadcom.vcf.iac.get_settings

- name: Get DNS Information
  ansible.builtin.include_role:
    name: broadcom.vcf.sddc_manager.dns_info

- name: Display DNS Information
  ansible.builtin.debug:
    msg: "{{ dns_info.msg }}"
```

The role is commonly used when you need to:

- Verify DNS configuration before or after configuration changes.
- Check DNS settings for troubleshooting or validation.
- Generate reports or audit logs of DNS configuration.

API Endpoint:

- `GET /v1/system/dns-configuration` - Retrieves the DNS configuration.

## Usage Examples

### Example 1: Update DNS Configuration Using Playbook

```bash
ansible-playbook playbooks/update_dns.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

### Example 2: Validate Changes with Check Mode

```bash
ansible-playbook playbooks/update_dns.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  --check
```

### Example 3: Query DNS Configuration

```bash
ansible-playbook playbooks/get_dns_info.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

## Workflow Sequence

### Update DNS Workflow

1. `playbooks/update_dns.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `sddc_manager/dns` role executes with `dns_state: update`:
   - Extracts DNS configuration from IaC
   - Validates DNS configuration with SDDC Manager API
   - Compares current configuration with desired state
   - Updates DNS configuration if changes are needed
   - Returns success message
