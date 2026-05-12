# Day 2: Manage CEIP

## Overview

This workflow manages the Customer Experience Improvement Program (CEIP) status in
VMware Cloud Foundation using the `broadcom.vcf.sddc_manager.ceip` role and the
`sddc_manager_ceip` module.

Supported operations:

- Ensure CEIP is enabled.
- Ensure CEIP is disabled.

The role is state-driven via `ceip_state`:

- `enabled` – enable CEIP telemetry collection.
- `disabled` – disable CEIP telemetry collection (default).

!!! info "About CEIP"
    The Customer Experience Improvement Program (CEIP):
    
    - Collects anonymous usage data from your VMware Cloud Foundation environment.
    - Helps Broadcom improve product quality and customer experience.
    - Can be enabled or disabled at any time.
    - Changes are applied asynchronously via a background task.

    Use Ansible's check mode (`--check`) to preview changes before execution.

## Prerequisites

Before you begin, make sure:

1. [Deployment prerequisites](../day1/deployment-prerequisites.md) are met.
2. Management domain is deployed and SDDC Manager is operational.
3. SDDC Manager is reachable and you have administrative credentials.
4. Infrastructure‑as‑Code (IaC) data is defined under `./infra-as-code/`.
5. You can authenticate to SDDC Manager with sufficient privileges to:
   - Query CEIP status.
   - Modify CEIP configuration.

## Configuration Requirements

The following configuration must be provided under `./infra-as-code/`:

- SDDC Manager configuration:
    - SDDC Manager hostname and admin credentials.

No additional configuration is required for CEIP management.

## Role Interface

Role: `broadcom.vcf.sddc_manager.ceip`

### Variables

Key variables:

- `ceip_state` - Desired state of CEIP.
    - `enabled`: enable CEIP telemetry collection.
    - `disabled` (default): disable CEIP telemetry collection.

### Return Values

- `changed` - Boolean indicating if changes were made.
- `msg` - Status message.
- `task` - Task information for the CEIP status update operation (includes task ID for tracking).

Additional inputs are drawn from your IaC structure, e.g. `all_iac_vars`:

- `all_iac_vars.sddc_manager.hostname`
- `all_iac_vars.vsphere.vcenter.sso.username`
- `all_iac_vars.vsphere.vcenter.sso.password` or overrides

## Execution

### Enable CEIP (`ceip_state: enabled`)

Example:

```yaml
- name: Enable CEIP
  hosts: localhost
  roles:
    - role: broadcom.vcf.sddc_manager.ceip
      vars:
        ceip_state: enabled
```

Behavior:

1. Query current CEIP status:
    - Uses `sddc_manager_ceip_info` to retrieve CEIP status.
2. Compare with desired state:
    - If already enabled, skips with `changed=false`.
    - If disabled, prepares to enable CEIP.
3. Update configuration (if needed):
    - Calls `sddc_manager_ceip` with `state: enabled`.
    - Enables CEIP via SDDC Manager API.
    - Waits for task completion.
    - Verifies status and displays confirmation.

#### Check Mode Behavior: `enabled`

When run with `--check`, the module returns a message without making changes:

```shell
Check Mode: Would change CEIP status from DISABLED to ENABLED.
```

- No API calls are made to modify configuration.

To see the check mode message in your playbook output, use verbose mode (`-v`) or register and display the result:

```yaml
- name: Enable CEIP
  hosts: localhost
  roles:
    - role: broadcom.vcf.sddc_manager.ceip
      vars:
        ceip_state: enabled
  register: ceip_result

- name: Display CEIP Result
  ansible.builtin.debug:
    msg: "{{ ceip_result.msg }}"
  when: ansible_check_mode
```

This gives you a dry run preview without enabling CEIP.

### Disable CEIP (`ceip_state: disabled`)

Example:

```yaml
- name: Disable CEIP
  hosts: localhost
  roles:
    - role: broadcom.vcf.sddc_manager.ceip
      vars:
        ceip_state: disabled
```

Behavior:

1. Query current CEIP status:
    - Uses `sddc_manager_ceip_info` to retrieve CEIP status.
2. Compare with desired state:
    - If already disabled, skips with `changed=false`.
    - If enabled, prepares to disable CEIP.
3. Update configuration (if needed):
    - Calls `sddc_manager_ceip` with `state: disabled`.
    - Disables CEIP via SDDC Manager API.
    - Waits for task completion.
    - Verifies status and displays confirmation.

#### Check Mode Behavior: `disabled`

When run with `--check`, the module returns a message without making changes:

```shell
Check Mode: Would change CEIP status from ENABLED to DISABLED.
```

- No API calls are made to modify configuration.

To see the check mode message in your playbook output, use verbose mode (`-v`) or register and display the result:

```yaml
- name: Disable CEIP
  hosts: localhost
  roles:
    - role: broadcom.vcf.sddc_manager.ceip
      vars:
        ceip_state: disabled
  register: ceip_result

- name: Display CEIP Result
  ansible.builtin.debug:
    msg: "{{ ceip_result.msg }}"
  when: ansible_check_mode
```

This lets you see what would change without performing the operation.

## SDK / API Calls

The following SDDC Manager endpoints are used by the supporting module utility (`plugins/module_utils/sddc_manager.py`):

For status changes:

- `GET /v1/system/ceip` - Retrieves current CEIP status and instance ID.
- `PATCH /v1/system/ceip` - Updates CEIP status (enable or disable).

The PATCH operation returns a task object that can be monitored for completion.

## Ansible Components

- Module Utils:
    - `plugins/module_utils/sddc_manager.py`

- Modules:
    - `plugins/modules/sddc_manager_ceip.py`
    - `plugins/modules/sddc_manager_ceip_info.py`

- Roles:
    - `roles/sddc_manager/ceip`
    - `roles/sddc_manager/ceip_info`

- Playbooks:
    - `playbooks/enable_ceip.yml` (Uses `ceip_state: enabled`)
    - `playbooks/disable_ceip.yml` (Uses `ceip_state: disabled`)
    - `playbooks/get_ceip_info.yml` (Informational only)

## Querying Information

The `sddc_manager_ceip_info` module and `ceip_info` role provide read-only access to CEIP status.

### Module: `sddc_manager_ceip_info`

This informational module retrieves CEIP status from SDDC Manager without making any changes.

Parameters:

- `sddc_manager_hostname` - (Required) SDDC Manager hostname or IP address.
- `sddc_manager_user` - (Required) SDDC Manager username.
- `sddc_manager_password` - (Required) SDDC Manager password.

Return Values:

- `msg` - Human-readable message summarizing the CEIP status and instance ID.
- `ceip` - Dictionary containing CEIP information:
    - `status` - Current CEIP status (`ENABLED` or `DISABLED`).
    - `instanceId` - Unique identifier for the SDDC Manager instance.
- `changed` - Always `false` for this informational module.

Example usage:

```yaml
- name: Get CEIP Status
  broadcom.vcf.sddc_manager_ceip_info:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
  register: ceip_status

- name: Display CEIP Status
  ansible.builtin.debug:
    msg: "{{ ceip_status.msg }}"
```

Output example:

```
"CEIP Status: ENABLED, Instance ID: 3f39d4a1-78d2-11e8-af85-f1cf26258cdc"
```

You can also access individual fields:

```yaml
- name: Display detailed CEIP information
  ansible.builtin.debug:
    msg: "Status: {{ ceip_status.ceip.status }}, Instance: {{ ceip_status.ceip.instanceId }}"
```

### Role: `ceip_info`

This role wraps the `sddc_manager_ceip_info` module to retrieve CEIP status and set it
as a fact.

Variables:

- No input variables required. Uses IaC settings from `all_iac_vars`.

Sets the following facts:

- `ceip_info` - Complete CEIP status response.

Example:

```yaml
- name: Get IaC Settings
  ansible.builtin.include_role:
    name: broadcom.vcf.iac.get_settings

- name: Get CEIP Status
  ansible.builtin.include_role:
    name: broadcom.vcf.sddc_manager.ceip_info

- name: Display CEIP Status
  ansible.builtin.debug:
    msg: "{{ ceip_info.msg }}"
```

The role is commonly used when you need to:

- Verify CEIP status before or after configuration changes.
- Check CEIP status for troubleshooting or validation.
- Generate reports or audit logs of CEIP configuration.

API Endpoint:

- `GET /v1/system/ceip` - Retrieves the CEIP status and instance ID.

## Usage Examples

### Example 1: Enable CEIP Using Playbook

```bash
ansible-playbook playbooks/enable_ceip.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

### Example 2: Disable CEIP Using Playbook

```bash
ansible-playbook playbooks/disable_ceip.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

### Example 3: Validate Changes with Check Mode

```bash
ansible-playbook playbooks/enable_ceip.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  --check
```

### Example 4: Query CEIP Status

```bash
ansible-playbook playbooks/get_ceip_info.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

## Workflow Sequence

### Enable CEIP Workflow

1. `playbooks/enable_ceip.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `sddc_manager/ceip` role executes with `ceip_state: enabled`:
   - Gets current CEIP status
   - Compares with desired state
   - Updates CEIP configuration if needed
   - Waits for task completion
   - Verifies status and returns success message

### Disable CEIP Workflow

1. `playbooks/disable_ceip.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `sddc_manager/ceip` role executes with `ceip_state: disabled`:
   - Gets current CEIP status
   - Compares with desired state
   - Updates CEIP configuration if needed
   - Waits for task completion
   - Verifies status and returns success message
