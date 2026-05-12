# Day 2: Manage NTP

## Overview

This workflow manages NTP (Network Time Protocol) in VMware Cloud Foundation using the
`broadcom.vcf.sddc_manager.ntp` role and the `sddc_manager_ntp` module.

Supported operations:

- Update NTP Configuration (update).

The role is state-driven via `ntp_state`:

- `update` – update NTP configuration.

!!! warning "Requirements"
    When `ntp_state: update`:

    Use Ansible's check mode (`--check`) to preview changes before execution.

## Prerequisites

Before you begin, make sure:

1. [Deployment prerequisites](../day1/deployment-prerequisites.md) are met.
2. Management domain is deployed and SDDC Manager is operational.
3. SDDC Manager is reachable and you have administrative credentials.
4. Infrastructure‑as‑Code (IaC) data for ntp is defined under
   `./infra-as-code/` (typically in `ntp.yml`).
5. You can authenticate to SDDC Manager with sufficient privileges to:
   - Update NTP configuration.
   - Query NTP information.

## Configuration Requirements

The following configuration must be provided under `./infra-as-code/`:

- NTP configuration (`ntp.yml`):
    - NTP IP address or FQDN.

- SDDC Manager configuration:
    - SDDC Manager hostname and admin credentials.

## Role Interface

Role: `broadcom.vcf.sddc_manager.ntp`

### Variables

Key variables:

- `ntp_state` - Desired state of the NTP.
    - `update` (default): update NTP configuration.

### Return Values

- `changed` - Boolean indicating if changes were made.
- `msg` - Status message.
- `meta` - Response data from SDDC Manager.

Additional inputs are drawn from your IaC structure, e.g. `all_iac_vars`:

- `all_iac_vars.sddc_manager.hostname`
- `all_iac_vars.vsphere.vcenter.sso.username`
- `all_iac_vars.vsphere.vcenter.sso.password` or overrides
- `ntp_config` - NTP configuration (extracted from ntp in IaC). Required when `state: update`. 

## Execution

### Update NTP (`ntp_state: update`)

Example:

```yaml
- name: Update NTP Configuration
  ansible.builtin.include_role:
    name: broadcom.vcf.sddc_manager.ntp
  vars:
    ntp_state: update
```

Behavior:

1. Find NTP in IaC:
    - Extracts all NTP data in IaC.
    - Sets `ntp_config` variable with NTP configurations.

2. Validate NTP configuration (`validate_ntp_config.yml`):
    - Calls `sddc_manager_ntp` with:
        - `state: update`
        - `validate_only: true`
    - If validation completes (`executionStatus: COMPLETED`):
        - Displays success message and continues.
    - Fails if validation errors are returned.

3. Update NTP (`update_ntp_config.yml`):
    - Calls `sddc_manager_ntp` for ntp with:
        - `state: update`
    - Receives current NTP information.
    - If current NTP information is the same as required ntp_config:
        - Displays compliant message.
        - Returns `changed: false`.
    - If current NTP information is different from required ntp_config:
        - Updates NTP.
        - Receives new NTP information.
        - If new NTP information is the same as required ntp_config, displays success message
    - Fails if update errors are returned.

#### Check Mode Behavior: `update`

- The module detects check mode and returns a message:

    ```shell
    Check Mode: Would update NTP configuration from xxx to yyy. No changes were performed.
    ```

- The role:
    - Displays this message.
    - Skips changes.

This gives you a dry run preview without updating NTP.

## SDK / API Calls

The following SDDC Manager endpoints are used by the supporting module utility (`plugins/module_utils/sddc_manager.py`):

For update:

- `GET /v1/system/ntp-configuration` - Retrieves the NTP configuration.
- `PUT /v1/system/ntp-configuration` - Updates the NTP configuration.
- `POST /v1/system/ntp-configuration/validations` - Perform validation of the NTP configuration specification.
- `GET /v1/system/ntp-configuration/validations` - Retrieves a list of NTP configuration validation.

## Ansible Components

- Module Utils:
    - `plugins/module_utils/sddc_manager.py`

- Modules:
    - `plugins/modules/sddc_manager_ntp.py`
    - `plugins/modules/sddc_manager_ntp_info.py`

- Roles:
    - `roles/sddc_manager/ntp`
    - `roles/sddc_manager/ntp_info`

- Playbooks:
    - `playbooks/update_ntp.yml` (Uses `ntp_state: update`)
    - `playbooks/get_ntp_info.yml` (Informational only)

## Querying Information

The `sddc_manager_ntp_info` module and `ntp_info` role provide read-only access to NTP information.

### Module: `sddc_manager_ntp_info`

This informational module retrieves NTP information from SDDC Manager without making any changes.

Parameters:

- `sddc_manager_hostname` - (Required) SDDC Manager hostname or IP address.
- `sddc_manager_user` - (Required) SDDC Manager username.
- `sddc_manager_password` - (Required) SDDC Manager password.

Return Values:

- `ntp_info` - NTP configuration information.
- `changed` - Always `false` (read-only operation).
- `msg` - Human-readable status message.

Example:

```yaml
- name: Get NTP Configuration
  broadcom.vcf.sddc_manager_ntp_info:
    sddc_manager_hostname: "{{ all_iac_vars.sddc_manager.hostname }}"
    sddc_manager_user: "{{ all_iac_vars.vsphere.vcenter.sso.username }}"
    sddc_manager_password: "{{ vcenter_administrator_password | default(all_iac_vars.vsphere.vcenter.sso.password) }}"
  register: ntp_info

- name: Display NTP Information
  ansible.builtin.debug:
    msg: "{{ ntp_info.msg }}"
```

### Role: `ntp_info`

This role wraps the `sddc_manager_ntp_info` module to retrieve NTP information and set it as a fact.

Variables:

- No input variables required. Uses IaC settings from `all_iac_vars`.

Sets the following facts:

- `ntp_info` - Complete NTP configuration response.

Example:

```yaml
- name: Get IaC Settings
  ansible.builtin.include_role:
    name: broadcom.vcf.iac.get_settings

- name: Get NTP Information
  ansible.builtin.include_role:
    name: broadcom.vcf.sddc_manager.ntp_info

- name: Display NTP Information
  ansible.builtin.debug:
    msg: "{{ ntp_info.msg }}"
```

The role is commonly used when you need to:

- Verify NTP configuration before or after configuration changes.
- Check NTP settings for troubleshooting or validation.
- Generate reports or audit logs of NTP configuration.

API Endpoint:

- `GET /v1/system/ntp-configuration` - Retrieves the NTP configuration.

## Usage Examples

### Example 1: Update NTP Configuration Using Playbook

```bash
ansible-playbook playbooks/update_ntp.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

### Example 2: Validate Changes with Check Mode

```bash
ansible-playbook playbooks/update_ntp.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  --check
```

### Example 3: Query NTP Configuration

```bash
ansible-playbook playbooks/get_ntp_info.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

## Workflow Sequence

### Update NTP Workflow

1. `playbooks/update_ntp.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `sddc_manager/ntp` role executes with `ntp_state: update`:
   - Extracts NTP configuration from IaC
   - Validates NTP configuration with SDDC Manager API
   - Compares current configuration with desired state
   - Updates NTP configuration if changes are needed
   - Returns success message
