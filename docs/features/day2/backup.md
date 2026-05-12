# Day 2: Manage Backup

## Overview

This workflow manages backup in VMware Cloud Foundation using the
`broadcom.vcf.sddc_manager.backup` role and the `sddc_manager_backup` module.

Supported operations:

- Update Backup Configuration (update).

The role is state-driven via `backup_state`:

- `update` – update Backup configuration.

!!! warning "Requirements"
    When `backup_state: update`:

    Use Ansible's check mode (`--check`) to preview changes before execution.

## Prerequisites

Before you begin, make sure:

1. [Deployment prerequisites](../day1/deployment-prerequisites.md) are met.
2. Management domain is deployed and SDDC Manager is operational.
3. SDDC Manager is reachable and you have administrative credentials.
4. Infrastructure‑as‑Code (IaC) data for backup is defined under
   `./infra-as-code/` (typically in `backup.yml`).
5. You can authenticate to SDDC Manager with sufficient privileges to:
   - Update Backup configuration.
   - Query Backup information.

## Configuration Requirements

The following configuration must be provided under `./infra-as-code/`:

- Backup configuration (`backup.yml`):
    - Information under backupLocations: server's IP address or FQDN, port, protocol, username, directoryPath
    - SSH fingerprint of the backup server (optional; auto-retrieved if not provided)
- SDDC Manager configuration:
    - SDDC Manager hostname and admin credentials.

## Role Interface

Role: `broadcom.vcf.sddc_manager.backup`

### Variables

Key variables:

- `backup_state` - Desired state of the backup.
    - `update` (default): update backup configuration.

### Return Values

- `changed` - Boolean indicating if changes were made.
- `msg` - Status message.
- `meta` - Response data from SDDC Manager.

Additional inputs are drawn from your IaC structure, e.g. `all_iac_vars`, `mgmt_automation_settings.yml`:

- `all_iac_vars.sddc_manager.hostname`
- `all_iac_vars.vsphere.vcenter.sso.username`
- `all_iac_vars.vsphere.vcenter.sso.password` or overrides
- `backup_encryption_passphrase`- Required when `state: update`
- `backup_password` - Required when `state: update` 
- `backup_ssh_fingerprint` - SSH ECDSA fingerprint of the backup server (optional when `state: update`).
    - If not provided, the role automatically retrieves the fingerprint from the backup server (`backupLocations[0].server`) using the `broadcom.vcf.util.ssh_ecdsa_fingerprint` role.
- `backup_iac_config` - Backup configuration (extracted from `backup.yml` in IaC). Required when `state: update`

## Execution

### Update Backup (`backup_state: update`)

Example:

```yaml
- name: Update Backup configuration
  ansible.builtin.include_role:
    name: broadcom.vcf.sddc_manager.backup
  vars:
    backup_state: update
```

Behavior:

1. Find backup in IaC:
    - Extracts all backup data in IaC.
    - Sets `backup_iac_config` variable with Backup configurations.

2. Retrieve SSH ECDSA fingerprint (if not provided):
    - If `backup_sshFingerprint` is not set, automatically retrieves the fingerprint from the backup server (`backupLocations[0].server`) using the `broadcom.vcf.util.ssh_ecdsa_fingerprint` role.

3. Validate Backup configuration (`validate_backup_config.yml`):
    - Calls `sddc_manager_backup` with:
        - `state: update`
        - `validate_only: true`
    - If validation completes (`executionStatus: COMPLETED`):
        - Displays success message and continues.
    - Fails if validation errors are returned.

4. Update Backup (`update_backup_config.yml`):
    - Calls `sddc_manager_backup` with:
        - `state: update`
    - Receives current backup information.
    - If current backup information is the same as required backup_iac_config:
        - Displays compliant message.
        - Returns `changed: false`.
    - If current backup information is different from required backup_iac_config:
        - Updates backup.
        - Receives new backup information.
        - If new backup information is the same as required backup_iac_config, displays success message
    - Fails if update errors are returned.

#### Check Mode Behavior: `update`

- The module detects check mode and returns a message:

    ```shell
    Check Mode: Would update backup configuration differences. No changes were performed.
    ```

- The role:
    - Displays this message.
    - Skips changes.

This gives you a dry run preview without updating backup.

## SDK / API Calls

The following SDDC Manager endpoints are used by the supporting module utility (`plugins/module_utils/sddc_manager.py`):

For update:

- `GET /v1/system/backup-configuration` - Retrieves the backup configuration.
- `PATCH /v1/system/backup-configuration` - Updates the backup configuration.
- `POST /v1/system/backup-configuration/validations` - Perform validation of the backup configuration specification.

## Ansible Components

- Module Utils:
    - `plugins/module_utils/sddc_manager.py`

- Modules:
    - `plugins/modules/sddc_manager_backup.py`
    - `plugins/modules/sddc_manager_backup_info.py`

- Roles:
    - `roles/sddc_manager/backup`
    - `roles/sddc_manager/backup_info`

- Playbooks:
    - `playbooks/update_backup.yml` (Uses `backup_state: update`)
    - `playbooks/get_backup_info.yml` (Informational only)

## Querying Information

The `sddc_manager_backup_info` module and `backup_info` role provide read-only access to Backup information.

### Module: `sddc_manager_backup_info`

This informational module retrieves Backup information from SDDC Manager without making any changes.

Parameters:

- `sddc_manager_hostname` - (Required) SDDC Manager hostname or IP address.
- `sddc_manager_user` - (Required) SDDC Manager username.
- `sddc_manager_password` - (Required) SDDC Manager password.

Return Values:

- `backup_info` - Backup configuration information.
- `changed` - Always `false` (read-only operation).
- `msg` - Human-readable status message.

Example:

```yaml
- name: Get Backup Configuration
  broadcom.vcf.sddc_manager_backup_info:
    sddc_manager_hostname: "{{ all_iac_vars.sddc_manager.hostname }}"
    sddc_manager_user: "{{ all_iac_vars.vsphere.vcenter.sso.username }}"
    sddc_manager_password: "{{ vcenter_administrator_password | default(all_iac_vars.vsphere.vcenter.sso.password) }}"
  register: backup_info

- name: Display Backup Information
  ansible.builtin.debug:
    msg: "{{ backup_info.msg }}"
```

### Role: `backup_info`

This role wraps the `sddc_manager_backup_info` module to retrieve Backup information and set it as a fact.

Variables:

- No input variables required. Uses IaC settings from `all_iac_vars`.

Sets the following facts:

- `backup_info` - Complete backup configuration response.

Example:

```yaml
- name: Get IaC Settings
  ansible.builtin.include_role:
    name: broadcom.vcf.iac.get_settings

- name: Get Backup Information
  ansible.builtin.include_role:
    name: broadcom.vcf.sddc_manager.backup_info

- name: Display Backup Information
  ansible.builtin.debug:
    msg: "{{ backup_info.msg }}"
```

The role is commonly used when you need to:

- Verify backup configuration before or after configuration changes.
- Check backup settings for troubleshooting or validation.
- Generate reports or audit logs of backup configuration.

API Endpoint:

- `GET /v1/system/backup-configuration` - Retrieves the backup configuration.

## Usage Examples

### Example 1: Update Backup Configuration Using Playbook

```bash
ansible-playbook playbooks/update_backup.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "backup_encryption_passphrase=passphrase" \
  -e "backup_password=password"
```

### Example 2: Validate Changes with Check Mode

```bash
ansible-playbook playbooks/update_backup.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "backup_encryption_passphrase=passphrase" \
  -e "backup_password=password" \
  --check
```

### Example 3: Query Backup Configuration

```bash
ansible-playbook playbooks/get_backup_info.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

## Workflow Sequence

### Update Backup Workflow

1. `playbooks/update_backup.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `sddc_manager/backup` role executes with `backup_state: update`:
   - Extracts backup configuration from IaC
   - Retrieves SSH ECDSA fingerprint if not provided
   - Validates backup configuration with SDDC Manager API
   - Compares current configuration with desired state
   - Updates backup configuration if changes are needed
   - Returns success message
