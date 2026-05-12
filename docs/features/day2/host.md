# Day 2: Manage Hosts

## Overview

This workflow manages ESX hosts in VMware Cloud Foundation using the
`broadcom.vcf.sddc_manager.host` role and the `sddc_manager_host` module.

Supported operations:

- Ensure hosts are present (Validated and Added/Commissioned).
- Ensure hosts are absent (Validated and Removed/Decommissioned).

The role is state-driven via `host_state`:

- `present` – validate and commission hosts.
- `absent` – validate and decommission hosts.

!!! warning "Decommission Requirements"
    When `host_state: absent`:
    
    - Hosts must be in `UNASSIGNED_UNUSEABLE` status (after removing a cluster or workload domain).
    - Hosts in `ASSIGNED` status cannot be decommissioned.
    - Hosts in `UNASSIGNED_USEABLE` status can be decommissioned.

    Use Ansible's check mode (`--check`) to preview changes before execution.

## Prerequisites

Before you begin, make sure:

1. [Deployment prerequisites](../day1/deployment-prerequisites.md) are met.
2. [Prechecks](../day1/precheck/precheck.md) have passed.
3. Management domain is deployed and SDDC Manager is operational.
4. ESX hosts are reachable and appropriately configured (networking, DNS, NTP, etc.).
5. A network pool exists in SDDC Manager for host commissioning.
6. Infrastructure‑as‑Code (IaC) data for hosts is defined under
   `./infra-as-code/` (typically in `vsphere.yml`).
7. You can authenticate to SDDC Manager with sufficient privileges to:
   - Commission/decommission hosts.
   - Query host status and network pools.

## Configuration Requirements

The following configuration must be provided under `./infra-as-code/`:

- vSphere configuration (`vsphere.yml`):
    - Datacenter(s) and cluster definitions.
    - ESX host entries with FQDNs.
    - Storage type configuration (VSAN, VSAN_ESA, NFS, VMFS_FC, VVOL).

- SDDC Manager configuration:
    - SDDC Manager hostname and admin credentials.
    - Network pool configuration.

The role uses IaC data (via `broadcom.vcf.iac.generate_api_payload`)
to render an API payload for host operations, using Jinja2 templates:
- `commission_hosts.j2` for commissioning
- `decommission_hosts.j2` for decommissioning

## Role Interface

Role: `broadcom.vcf.sddc_manager.host`

### Variables

Key variables:

- `host_state` - Desired state of the host(s).
    - `present` (default): validate and commission hosts.
    - `absent`: validate and decommission hosts.
- `cluster_input` - Name of the cluster whose hosts to manage (required).
- `hosts_input` - List of host FQDNs to manage. If not provided, all hosts from the cluster configuration are used.
- `esx_host_password` - Root password for ESX hosts (required for commissioning).
- `host_commission_template_name` - Jinja2 template for commission payload. Default: `commission_hosts.j2`.
- `host_decommission_template_name` - Jinja2 template for decommission payload. Default: `decommission_hosts.j2`.

Additional inputs are drawn from your IaC structure, e.g. `all_iac_vars`:

- `all_iac_vars.sddc_manager.hostname`
- `all_iac_vars.vsphere.vcenter.sso.username`
- `all_iac_vars.vsphere.vcenter.sso.password` or overrides
- Network pool ID (retrieved via `broadcom.vcf.sddc_manager.network_pool_info`)
- Storage type (derived from cluster storage configuration)

### Return Values

- `changed` - Boolean indicating if changes were made.
- `msg` - Status message.
- `meta` - Response data from SDDC Manager (includes task ID for tracking).

## Execution

### Commission Hosts (`host_state: present`)

Example:

```yaml
- name: Commission Hosts
  hosts: localhost
  roles:
    - role: broadcom.vcf.sddc_manager.host
      vars:
        host_state: present
        cluster_input: w01-cl01
        esx_host_password: <password>
        hosts_input:
          - w01-esx01.example.com
          - w01-esx02.example.com
          - w01-esx03.example.com
          - w01-esx04.example.com
        # Optionally omit hosts_input to use all hosts from cluster configuration.
```

Behavior:

1. Generate commission payload (`generate_commission_payload.yml`):
    - Retrieves network pool via `broadcom.vcf.sddc_manager.network_pool_info`.
    - Determines storage type from cluster configuration.
    - Validates that specified hosts exist in IaC configuration.
    - Invokes `broadcom.vcf.iac.generate_api_payload` with `commission_hosts.j2` template.

2. Validate payload (`validate_commission_payload.yml`):
    - Calls `sddc_manager_host` with:
        - `state: present`
        - `validate: true`
    - If validation completes immediately (`executionStatus: COMPLETED`):
        - Displays success message and continues.
    - If validation is asynchronous:
        - Sets `commission_hosts_validation_id` from response.
        - Polls with `sddc_manager_tasks_status` until validation completes.
    - Fails if validation errors are returned.

3. Commission hosts (`commission_host.yml`):
    - Calls `sddc_manager_host` with:
        - `state: present`
        - `validate: false`
    - Receives a commission task ID.
    - Polls with `sddc_manager_tasks_status` until commission completes.
    - Displays success message with commissioned host FQDNs.
    - Fails if task reports error codes.

#### Check Mode Behavior: `present`

- The role still:
    - Generates the payload.
    - Validates the payload.
- The commission step does not actually commission hosts:
    - The module detects check mode and performs only validation, returning
     `changed: false`.
    - The role does not wait for a commission task.

This gives you a realistic dry run: errors are surfaced, but hosts are not commissioned.

### Decommission Hosts (`host_state: absent`)

Example:

```yaml
- name: Decommission Hosts
  hosts: localhost
  roles:
    - role: broadcom.vcf.sddc_manager.host
      vars:
        host_state: absent
        cluster_input: w01-cl01
        hosts_input:
          - sfo01-w01-esx01.sfo.rainpole.io
          - sfo01-w01-esx02.sfo.rainpole.io
          - sfo01-w01-esx03.sfo.rainpole.io
          - sfo01-w01-esx04.sfo.rainpole.io
```

Behavior:

1. Generate decommission payload (`generate_decommission_payload.yml`):
    - Validates that specified hosts exist in IaC configuration.
    - If `hosts_input` not provided, uses all hosts from cluster configuration.
    - Invokes `broadcom.vcf.iac.generate_api_payload` with `decommission_hosts.j2` template.

2. Validate payload (`validate_decommission_payload.yml`):
    - Calls `sddc_manager_host` with:
        - `state: absent`
        - `validate: true`
    - If validation completes immediately (`executionStatus: COMPLETED`):
        - Displays success message and continues.
    - If validation is asynchronous:
        - Sets `decommission_hosts_validation_id` from response.
        - Polls with `sddc_manager_tasks_status` until validation completes.
    - Fails if validation errors are returned (e.g., hosts still assigned to clusters).

3. Decommission hosts (`decommission_host.yml`):
    - Calls `sddc_manager_host` with:
        - `state: absent`
        - `validate: false`
    - Receives a decommission task ID.
    - Polls with `sddc_manager_tasks_status` until decommission completes.
    - Displays success message with decommissioned host FQDNs.
    - Fails if task reports error codes.

#### Check Mode Behavior: `absent`

- The module detects `check_mode` and does not call the API:
    - Returns `changed: true` with a message like:
  
        ```shell
        Check mode: Would decommission 2 host(s); no changes were performed.
        ```

- The role:
    - Displays this message.
    - Skips waiting for a decommission task (there isn't one).

This lets you see which hosts would be decommissioned and confirm the plan without performing the operation.

## SDK / API Calls

The following SDDC Manager endpoints are used by the supporting module utility (`plugins/module_utils/sddc_manager.py`):

For commissioning:

- `POST /v1/hosts/validations` - Validates host commission configuration.
- `POST /v1/hosts` - Commissions hosts.

For decommissioning:

- `POST /v1/hosts/validations` - Validates host decommission configuration.
- `DELETE /v1/hosts` - Decommissions hosts.

Additional calls:

- `GET /v1/hosts?fqdn={fqdn}` - Retrieves host status.
- `GET /v1/hosts?status=UNASSIGNED_USEABLE` - Retrieves unassigned usable hosts.
- `GET /v1/network-pools` - Retrieves network pool information.

Task tracking:

- `GET /v1/tasks/{id}` - Used by `sddc_manager_tasks_status` to poll commission and decommission tasks.
- `GET /v1/hosts/validations/{id}` - Used to poll validation task status.

## Ansible Components

- Module Utils:
    - `plugins/module_utils/sddc_manager.py`

- Modules:
    - `plugins/modules/sddc_manager_host.py`
    - `plugins/modules/sddc_manager_host_info.py`
    - `plugins/modules/sddc_manager_network_pool.py`
    - `plugins/modules/sddc_manager_tasks_status.py`

- Roles:
    - `roles/sddc_manager/host`
    - `roles/ops/prep_hosts`
    - `roles/sddc_manager/network_pool_info`

- Playbooks:
    - `playbooks/commission_hosts.yml` (Uses `host_state: present`)
    - `playbooks/decommission_hosts.yml` (Uses `host_state: absent`)

## Querying Information

The `sddc_manager_host_info` module and `hosts_info` role provide read-only access to ESX host data.

### Module: `sddc_manager_host_info`

This informational module retrieves ESX host details from SDDC Manager without making any changes.

Parameters:

- `sddc_manager_hostname` - (Required) SDDC Manager hostname or IP address.
- `sddc_manager_user` - (Required) SDDC Manager username.
- `sddc_manager_password` - (Required) SDDC Manager password.
- `fqdn` - (Optional) The FQDN of a specific ESX host to query. Takes precedence over `host_status`.
- `host_status` - (Optional) Filter hosts by status. Valid values: `ASSIGNED`, `UNASSIGNED_USEABLE`, `UNASSIGNED_UNUSEABLE`.
- `format` - (Optional) Output format. Valid values: `info` (default), `id`.
- If no parameters specified, returns all hosts.

Return Values:

- `meta` - Dictionary of ESX hosts indexed by FQDN.
- `changed` - Always `false` (read-only operation).
- `msg` - Status or error message.

Examples:

```yaml
- name: Get All ESX Hosts
  broadcom.vcf.sddc_manager_host_info: 
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
  register: all_hosts

- name: Get Specific Host
  broadcom.vcf.sddc_manager_host_info: 
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    fqdn: esx-01.example.com
  register: single_host

- name: Get Unassigned Usable Hosts
  broadcom.vcf.sddc_manager_host_info:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    host_status: UNASSIGNED_USEABLE
    format: info
  register: usable_hosts

- name: Get Unassigned Usable Host IDs
  broadcom.vcf.sddc_manager_host_info: 
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    host_status: UNASSIGNED_USEABLE
    format: id
  register: host_ids
```

### Role: `host_info`

This role wraps the `sddc_manager_host_info` module to retrieve ESX host information and set it as a fact.

Variables:

- `host_fqdn` - (Optional) Specific host FQDN to query.
- `host_status_filter` - (Optional) Filter by host status (`ASSIGNED`, `UNASSIGNED_USEABLE`, `UNASSIGNED_UNUSEABLE`).
- `host_info_format` - (Optional) Output format (`info` or `id`). Default: `info`.

Sets the following fact:

- `host_info` - Dictionary of host information indexed by FQDN.

Example:

```yaml
- name: Get IaC Settings
  ansible.builtin.include_role:
    name: broadcom.vcf.iac.get_settings

- name: Get Unassigned Usable Host IDs
  ansible.builtin.include_role:
    name: broadcom.vcf.sddc_manager.host_info
  vars:
    host_status_filter: UNASSIGNED_USEABLE
    host_info_format: id

- name: Display Host IDs
  ansible.builtin.debug:
    var: hosts_info
```

Example Output (`format: id`):

```json
{
  "esx-01.example.com": {
    "id": "12345678-1234-1234-1234-123456789012"
  },
  "esx-02.example.com": {
    "id": "87654321-4321-4321-4321-210987654321"
  }
}
```

The role is commonly used when you need to:

- Query available hosts before commissioning or cluster expansion.
- Check host status for validation or reporting.
- Retrieve host IDs for subsequent operations.
- Monitor unassigned usable hosts in the inventory.

API Endpoints:

- `GET /v1/hosts` - Retrieves all hosts.
- `GET /v1/hosts?fqdn={fqdn}` - Retrieves specific host by FQDN.
- `GET /v1/hosts?status={status}` - Retrieves hosts filtered by status.

## Usage Examples

### Example 1: Commission Hosts Using Vars File

```bash
ansible-playbook playbooks/commission_hosts.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

### Example 2: Commission Hosts Using Inline Variables

```bash
ansible-playbook playbooks/commission_hosts.yml \
  -e "region=amer datacenter=dc01 az=az01 vcf=lab" \
  -e "cluster_input=w01-cl01" \
  -e "esx_host_password=password"
```

### Example 3: Decommission Hosts

```bash
ansible-playbook playbooks/decommission_hosts.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "cluster_input=w01-cl01"
```

### Example 4: Validate Changes with Check Mode

```bash
ansible-playbook playbooks/commission_hosts.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  --check
```

## Workflow Sequence

### Commission Hosts Workflow

1. `playbooks/commission_hosts.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `sddc_manager/host` role executes with `host_state: present`:
   - Retrieves network pool ID from SDDC Manager
   - Determines storage type from cluster configuration
   - Generates commission payload from template
   - Validates payload with SDDC Manager API
   - Commissions hosts
   - Waits for commission task to complete

### Decommission Hosts Workflow

1. `playbooks/decommission_hosts.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `sddc_manager/host` role executes with `host_state: absent`:
   - Generates decommission payload from template
   - Validates payload with SDDC Manager API
   - Decommissions hosts
   - Waits for decommission task to complete
