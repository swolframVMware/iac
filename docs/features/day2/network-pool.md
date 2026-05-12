# Day 2: Manage Network Pools

## Overview

This workflow manages network pools in VMware Cloud Foundation using the
`broadcom.vcf.sddc_manager.network_pool` role and the `sddc_manager_network_pool` module.

Supported operations:

- Ensure network pool is present (Added).
- Ensure network pool is absent (Removed).

The role is state-driven via `network_pool_state`:

- `present` – add a network pool.
- `absent` – remove a network pool.

!!! warning "Requirements"
    When `network_pool_state: absent`:

    - The network pool must not be in use by any hosts or clusters.
    - Network pools associated with active workload domains cannot be removed directly.
    - Ensure hosts using the network pool are decommissioned.

    Use Ansible's check mode (`--check`) to preview changes before execution.

## Prerequisites

Before you begin, make sure:

1. [Deployment prerequisites](../day1/deployment-prerequisites.md) are met.
2. Management domain is deployed and SDDC Manager is operational.
3. SDDC Manager is reachable and you have administrative credentials.
4. Infrastructure‑as‑Code (IaC) data for network pools is defined under
   `./infra-as-code/` (typically in `vsphere.yml`).
5. You can authenticate to SDDC Manager with sufficient privileges to:
   - Add and remove a network pool.
   - Query network pool status.
6. Network configuration details are prepared:
   - VLAN IDs for different network types (VSAN, vMotion, Management, etc.).
   - IP address ranges and subnets.
   - Gateway addresses.
   - MTU settings.

## Configuration Requirements

The following configuration must be provided under `./infra-as-code/`:

- vSphere configuration (`vsphere.yml`):
    - Datacenter and cluster definitions.
    - Host pool configuration with network details:
        - Network types (VSAN, vMotion, Management, NFS, etc.).
        - VLAN IDs.
        - IP address pools (start/end ranges).
        - Subnet masks and gateways.
        - MTU values.

- SDDC Manager configuration:
    - SDDC Manager hostname and admin credentials.

The role uses IaC data (via `broadcom.vcf.iac.generate_api_payload`)
to render an API payload for network pool operations, using the Jinja2 template:
- `add_network_pool.j2` for creation

## Role Interface

Role: `broadcom.vcf.sddc_manager.network_pool`

### Variables

Key variables:

- `network_pool_state` - Desired state of the network pool(s).
    - `present` (default): add a network pool.
    - `absent`: remove a network pool.
- `network_pool_name` - Name of the network pool to manage. Required when `state: absent`.
- `network_pool_add_template_name` - Jinja2 template for creation payload. Default: `add_network_pool.j2`.

### Return Values

- `changed` - Boolean indicating if changes were made.
- `msg` - Status message.
- `meta` - Response data from SDDC Manager (includes task ID for tracking).

Additional inputs are drawn from your IaC structure, e.g. `all_iac_vars`:

- `all_iac_vars.sddc_manager.hostname`
- `all_iac_vars.vsphere.vcenter.sso.username`
- `all_iac_vars.vsphere.vcenter.sso.password` or overrides
- Network pool configuration (extracted from cluster host pool definitions)

## Execution

### Add Network Pool (`network_pool_state: present`)

Example:

```yaml
- name: Add Network Pool
  hosts: localhost
  roles:
    - role: broadcom.vcf.sddc_manager.network_pool
      vars:
        network_pool_state: present
        # Network pool configuration is read from IaC data
```

Behavior:

1. Generate payload (`generate_add_payload.yml`):
    - Extracts all network pool configurations from cluster host pool definitions.
    - Identifies unique network pools by name (multiple clusters may reference same pool).
    - Displays which network pools will be processed.
    - Sets `network_pools_to_process` variable with unique pool configurations.

2. Add network pool (`add_network_pool.yml`):
    - Calls `sddc_manager_network_pool` for each network pool with:
        - `state: present`
    - Checks for idempotency (skips if pool exists).

#### Check Mode Behavior: `present`

- The module detects check mode and returns a message:

    ```shell
    Check Mode: Would add network pool '<name>'.
    ```

This gives you a dry run preview without adding network pools.

### Remove Network Pool (`network_pool_state: absent`)

Example:

```yaml
- name: Remove Network Pool
  hosts: localhost
  roles:
    - role: broadcom.vcf.sddc_manager.network_pool
      vars:
        network_pool_state: absent
        network_pool_name: network-pool-01
```

Behavior:

1. Remove network pool (`remove_network_pool.yml`):
    - Calls `sddc_manager_network_pool` with:
        - `state: absent`
    - Checks for idempotency (skips if pool doesn't exist).

#### Check Mode Behavior: `absent`

- The module detects `check_mode` and returns a message:

    ```shell
    Check Mode: Would remove network pool '<name>'.
    ```

This lets you see which network pool would be deleted and confirm the plan without performing the operation.

## SDK / API Calls

The following SDDC Manager endpoints are used by the supporting module utility (`plugins/module_utils/sddc_manager.py`):

For addition:

- `GET /v1/network-pools` - Retrieves all network pools (for existence check).
- `POST /v1/network-pools` - Adds a network pool.

For removal:

- `GET /v1/network-pools` - Retrieves network pools to find ID.
- `GET /v1/network-pools/{id}` - Retrieves specific network pool details.
- `DELETE /v1/network-pools/{id}` - Removes a network pool.

## Ansible Components

- Module Utils:
    - `plugins/module_utils/sddc_manager.py`

- Modules:
    - `plugins/modules/sddc_manager_network_pool.py`
    - `plugins/modules/sddc_manager_network_pool_info.py`

- Roles:
    - `roles/sddc_manager/network_pool`
    - `roles/sddc_manager/network_pool_info`

- Playbooks:
    - `playbooks/add_network_pool.yml` (Uses `network_pool_state: present`)
    - `playbooks/remove_network_pool.yml` (Uses `network_pool_state: absent`)

## Querying Information

The `sddc_manager_network_pool_info` module and `network_pool_info` role provide read-only access to network pool data.

### Module: `sddc_manager_network_pool_info`

This informational module retrieves network pool details from SDDC Manager without making any changes.

Parameters:

- `sddc_manager_hostname` - (Required) SDDC Manager hostname or IP address.
- `sddc_manager_user` - (Required) SDDC Manager username.
- `sddc_manager_password` - (Required) SDDC Manager password.
- `network_pool_name` - (Optional) Name of the network pool to retrieve. Mutually exclusive with `network_pool_id`.
- `network_pool_id` - (Optional) ID of the network pool to retrieve. Mutually exclusive with `network_pool_name`.
- If neither is specified, returns all network pools.

Return Values:

- `network_pools` - List of all network pools (when no specific pool is requested).
- `network_pool` - Single network pool details (when name or ID is specified).
- `changed` - Always `false` (read-only operation).
- `msg` - Status or error message.

Example:

```yaml
- name: Get Network Pool Information
  broadcom.vcf.sddc_manager_network_pool_info:
    sddc_manager_hostname: "{{ all_iac_vars.sddc_manager.hostname }}"
    sddc_manager_user: "{{ all_iac_vars.vsphere.vcenter.sso.username }}"
    sddc_manager_password: "{{ vcenter_administrator_password | default(all_iac_vars.vsphere.vcenter.sso.password) }}"
    network_pool_name: "network-pool-01"
  register: pool_info

- name: Display Network Pool ID
  ansible.builtin.debug:
    msg: "Network Pool ID: {{ pool_info.network_pool.id }}"
```

### Role: `network_pool_info`

This role wraps the `sddc_manager_network_pool_info` module to retrieve network pool information and set it as a fact.

Variables:

- `network_pool_name` - (Optional) Name of the network pool to query.
- `network_pool_id` - (Optional) ID of the network pool to query.

Sets the following facts:

- `network_pool_info` - Complete network pool information response.
- `network_pool_id` - Extracted network pool ID for convenience.

Example:

```yaml
- name: Get IaC Settings
  ansible.builtin.include_role:
    name: broadcom.vcf.iac.get_settings

- name: Get Network Pool Information
  ansible.builtin.include_role:
    name: broadcom.vcf.sddc_manager.network_pool_info

- name: Display Network Pool ID
  ansible.builtin.debug:
    msg: "Network Pool ID: {{ network_pool_id }}"
```

The role is commonly used when you need to:

- Resolve a network pool name to its ID for host commissioning.
- Check network pool status before performing operations.
- Retrieve network pool details for validation or reporting.

API Endpoint:

- `GET /v1/network-pools` - Retrieves all network pools.

## Usage Examples

### Example 1: Add Network Pool Using Vars File

```bash
ansible-playbook playbooks/add_network_pool.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

### Example 2: Add Network Pool Using Inline Variables

```bash
ansible-playbook playbooks/add_network_pool.yml \
  -e "region=amer datacenter=dc01 az=az01 vcf=lab"
```

### Example 3: Remove Network Pool

```bash
ansible-playbook playbooks/remove_network_pool.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "network_pool_name=network-pool-01"
```

### Example 4: Validate Changes with Check Mode

```bash
ansible-playbook playbooks/add_network_pool.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  --check
```

## Workflow Sequence

### Add Network Pool Workflow

1. `playbooks/add_network_pool.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `sddc_manager/network_pool` role executes with `network_pool_state: present`:
   - Extracts network pool configurations from IaC cluster host pool definitions
   - Identifies unique network pools by name
   - Adds each network pool if not already present
   - Returns success message

### Remove Network Pool Workflow

1. `playbooks/remove_network_pool.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `sddc_manager/network_pool` role executes with `network_pool_state: absent`:
   - Looks up network pool by name
   - Removes network pool if present
   - Returns success message

