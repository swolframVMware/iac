# Day 2: Manage Workload Domains

## Overview

This workflow manages workload domains in VMware Cloud Foundation using the
`broadcom.vcf.sddc_manager.workload_domain` role and the
`sddc_manager_workload_domain` module.

Supported operations:

- Ensure a workload domain is present (Validated and Added).
- Ensure a workload domain is absent (Marked for deletion and Removed).

The role is state-driven via `workload_domain_state`:

- `present` – validate and add the workload domain.
- `absent` – resolve the workload domain by name and remove it.

!!! warning "Deletion is Irreversible"
    When `workload_domain_state: absent`:
    
    - All clusters and virtual machines in the workload domain are deleted.
    - All vSAN datastores are destroyed.
    - All hosts from the workload domain are set to an `UNASSIGNED_UNUSEABLE` status.
    - All hosts from the workload domain are automatically decommissioned (`workload_domain_decommission_hosts: true`).
    - To skip decommissioning and retain hosts for an alternate process, set `workload_domain_decommission_hosts: false`.

    Use Ansible's check mode (`--check`) to preview changes before execution.

## Prerequisites

Before you begin, make sure:

1. [Deployment prerequisites](../day1/deployment-prerequisites.md) are met.
2. [Prechecks](../day1/precheck/precheck.md) have passed.
3. Management domain is deployed and SDDC Manager is operational.
4. ESX hosts that will back the workload domain are reachable and
   appropriately configured (networking, DNS, NTP, etc.).
5. Infrastructure‑as‑Code (IaC) data for workload domains is defined under
   `./infra-as-code/` (typically in `vsphere.yml` and related files).
6. You can authenticate to SDDC Manager with sufficient privileges to:
   - Commission/decommission hosts.
   - Add and remove workload domains.

## Configuration Requirements

The following configuration must be provided under `./infra-as-code/`:

- vSphere configuration (`vsphere.yml`):
    - Datacenter(s), cluster definitions, ESX hosts.
    - Workload‑domain specific configuration (compute, storage, and network
      parameters used in the payload template).

- SDDC Manager configuration:
    - SDDC Manager hostname and admin credentials.
    - Any domain‑specific settings referenced by the payload template.

The role uses IaC data (for example through `broadcom.vcf.iac.generate_api_payload`)
to render an API payload for the workload domain, typically from a Jinja2 template
such as `workload_domain.j2`.

## Role Interface

Role: `broadcom.vcf.sddc_manager.workload_domain`

### Variables

Key variables:

- `workload_domain_state` - Desired state of the workload domain.
    - `present` (default): validate and add the workload domain.
    - `absent`: remove the workload domain.
- `workload_domain_name` - Name of the workload domain to manage. Used when `workload_domain_state: absent` to look up the domain and obtain its ID.
- `workload_domain_decommission_hosts` - Controls whether hosts are decommissioned after workload domain removal. Default: `true`.
    - `true` (default): All hosts from the workload domain are automatically decommissioned.
    - `false`: All hosts from the workload domain remain in an `UNASSIGNED_UNUSEABLE` status for an alternate decommission process.
- `workload_domain_template_name` - Jinja2 template used to generate the workload‑domain payload for creation. Default: `workload_domain.j2`.

Additional inputs are drawn from your IaC structure, e.g. `all_iac_vars`:

- `all_iac_vars.sddc_manager.hostname`
- `all_iac_vars.vsphere.vcenter.sso.username`
- `all_iac_vars.vsphere.vcenter.sso.password` or overrides
- Network, storage, and host layout referenced by the template.

### Return Values

- `changed` - Boolean indicating if changes were made.
- `msg` - Status message.
- `meta` - Response data from SDDC Manager (includes task ID for tracking).

## Execution

### Add Workload Domain (`workload_domain_state: present`)

Example playbook snippet:

```yaml
- name: Add Workload Domain
  hosts: localhost
  roles:
    - role: broadcom.vcf.sddc_manager.workload_domain
      vars:
        workload_domain_state: present
        workload_domain_name: {{ workload_domain_name}}
        # Optionally override template:
        # workload_domain_template_name: {{ workload_domain_template_name }}
```

Behavior:

1. Host checks and preparation (`check_hosts.yml`):
    - Validates that required clusters and ESX hosts exist in IaC.
    - Uses `sddc_manager_hosts_info` to categorize host status.
    - Fails if hosts are already assigned or in unexpected states.
    - Runs `broadcom.vcf.ops.prep_hosts` to prepare and (if needed) commission hosts.  
      - In check mode, host preparation is skipped (no changes).

2. Generate workload domain payload (`generate_add_payload.yml`):
    - Invokes `broadcom.vcf.iac.generate_api_payload` to produce `api_payload_json`
      from `workload_domain_template_name` (default `workload_domain.j2`).

3. Validate payload (`validate_add_payload.yml`):
    - Calls `sddc_manager_workload_domain` with:
      - `state: present`
      - `validate_only: true`
    - Fails if validation errors are returned.

4. Create workload domain (`add_domain.yml`):
    - Calls `sddc_manager_workload_domain` with:
      - `state: present`
      - `validate_only: false`
    - Receives a creation task ID and waits for task completion using
     `sddc_manager_tasks_status` (unless in check mode).
    - Fails if the task reports error codes.

#### Check Mode Behavior: `present`

- The role still:
    - Runs host checks (read‑only API calls, plus safety checks).
    - Generates the payload.
    - Validates the payload.
- The add step does not actually add the workload domain:
    - The module detects check mode and performs only validation, returning
     `changed: false`.
    - The role does not wait for a creation task.

This gives you a realistic dry run: errors are surfaced, but nothing is changed.

### Remove Workload Domain (`workload_domain_state: absent`)

Example:

```yaml
- name: Remove Workload Domain
  hosts: localhost
  roles:
    - role: broadcom.vcf.sddc_manager.workload_domain
      vars:
        workload_domain_state: absent
        workload_domain_name: "w01"
        # Optional: Keep hosts in inventory for an alternate decommission process.
        # workload_domain_decommission_hosts: false
```

Behavior:

1. Lookup by name (`lookup_domain.yml`):
    - Uses `sddc_manager_workload_domain_info` to locate the domain by `workload_domain_name`
      and extract `workload_domain_id`.

2. Collect resources for decommissioning (`decommission_info.yml`, only if `workload_domain_decommission_hosts: true`):
    - Retrieves all clusters in the workload domain using `sddc_manager_cluster_info`.
    - Extracts host IDs from each cluster.
    - Retrieves host details using `sddc_manager_host_info`.
    - Builds a list of host FQDNs (`hosts_to_decommission`) for later decommissioning.
    - This step happens **before** domain removal to preserve host information.

3. Remove workload domain (`remove_domain.yml`):
    - Calls `sddc_manager_workload_domain` with:
      - `state: absent`
      - `workload_domain_payload.id: "{{ workload_domain_id }}"`

   The module performs a two-step deletion:

   1. `PATCH /v1/domains/{id}` with `{"markForDeletion": true}` (mark the domain for deletion).
   2. `DELETE /v1/domains/{id}` (trigger domain removal).

   Both responses (`mark_result` and `remove_result`) are returned in `meta`.

4. Wait for removal task:
    - Extracts the remove task ID from `meta.remove_result.id`.
    - Uses `sddc_manager_tasks_status` to poll the task until completion.
    - Fails if the task reports error codes.
    - Prints a success message on completion.

5. Decommission hosts (`decommission_resources.yml`, if `workload_domain_decommission_hosts: true`):
    - After successful domain removal, decommissions all hosts that were part of the domain.
    - Uses the `broadcom.vcf.sddc_manager.host` role with `host_state: absent`.

#### Check Mode Behavior: `absent`

- The module detects `check_mode` and does not call the API:
   - Returns `changed: true` with a message like:
  
     ```shell
     Check mode: Workload domain ID '<id>' would be removed; no changes were performed.
     ```
     
- The role:
  - Displays this message.
  - If `workload_domain_decommission_hosts: true`, collects and displays which hosts would be decommissioned.
  - Skips waiting for a removal task.
  - Does not actually remove the domain or decommission hosts.

This lets you see *which* domain would be removed, *which* hosts would be decommissioned, and confirm the plan without performing the deletion.

## SDK / API Calls

The following SDDC Manager endpoints are used by the supporting module utility, `plugins/module_utils/sddc_manager.py`):

For creation:

- `POST /v1/domains/validations` - Validates workload domain configuration.
- `POST /v1/domains` - Adds workload domain.

For deletion:

- `PATCH /v1/domains/{id}` with body `{"markForDeletion": true}` - Marks a workload domain for deletion.
- `DELETE /v1/domains/{id}` - Removes a workload domain.

Additional calls for host workflows:

- `GET /v1/hosts?fqdn={fqdn}` - Retrieves host status for categorization.
- `POST /v1/hosts/validations` - Validates host commissioning.
- `POST /v1/hosts` - Commissions hosts.
- `GET /v1/hosts?status=UNASSIGNED_USEABLE` - Retrieves IDs of usable unassigned hosts.

Task tracking:

- `GET /v1/tasks/{id}` - Used by `sddc_manager_tasks_status` to poll creation and deletion tasks.

## Ansible Components

- Module Utils:
    - `plugins/module_utils/sddc_manager.py`

- Modules:
    - `plugins/modules/sddc_manager_workload_domain.py`
    - `plugins/modules/sddc_manager_tasks_status.py`
    - `plugins/modules/sddc_manager_host.py`
    - `plugins/modules/sddc_manager_host_info.py`
    - `plugins/modules/sddc_manager_workload_domain_info.py`

- Roles:
    - `roles/sddc_manager/workload_domain`
    - `roles/ops/prep_hosts`

- Playbooks:
    - `playbooks/add_workload_domain.yml` (Uses `workload_domain_state: present`)
    - `playbooks/remove_workload_domain.yml` (Uses `workload_domain_state: absent`)

## Querying Information

The `sddc_manager_workload_domain_info` module and `workload_domain_info` role provide read-only access to workload domain data.

### Module: `sddc_manager_workload_domain_info`

This informational module retrieves workload domain details from SDDC Manager without making any changes.

Parameters:

- `sddc_manager_hostname` - (Required) SDDC Manager hostname or IP address.
- `sddc_manager_user` - (Required) SDDC Manager username.
- `sddc_manager_password` - (Required) SDDC Manager password.
- `domain` - (Optional) Name of the workload domain to retrieve. If not specified, module returns error (use `sddc_manager_workload_domain_info` to retrieve all domains).

Return Values:

- `meta` - Workload omain information dictionary keyed by workload domain name.
- `changed` - Always `false` (read-only operation).
- `msg` - Error message if workload domain not found.

Example:

```yaml
- name: Get Workload Domain Information
  broadcom.vcf.sddc_manager_workload_domain_info:
    sddc_manager_hostname: "{{ all_iac_vars.sddc_manager.hostname }}"
    sddc_manager_user: "{{ all_iac_vars.vsphere.vcenter.sso.username }}"
    sddc_manager_password: "{{ vcenter_administrator_password | default(all_iac_vars.vsphere.vcenter.sso.password) }}"
    domain: "{{ all_iac_vars.domain.name }}"
  register: domain_info

- name: Set Workload Domain Information
  ansible.builtin.set_fact:
    domain_info: "{{ domain_info }}"

- name: Set Workload Domain ID
  ansible.builtin.set_fact:
    domain_id: "{{ domain_info.domain.id }}"
```

### Role: `workload_domain_info`

This role wraps the `sddc_manager_workload_domain_info` module to retrieve workload domain information and set it as facts.

Variables:

- Uses `all_iac_vars.domain.name` to determine which workload domain to query.

Sets the following facts:

- `domain_info` - Complete workload domain information response.
- `domain_id` - Extracted workload domain ID for convenience.

Example:

```yaml
- name: Get IaC Settings
  ansible.builtin.include_role:
    name: broadcom.vcf.iac.get_settings

- name: Get Workload Domain Information
  ansible.builtin.include_role:
    name: broadcom.vcf.sddc_manager.workload_domain_info
    
- name: Display Workload Domain ID 
  ansible.builtin.debug: 
    msg: "Workload Domain ID: {{ domain_id }}"
```

The role is commonly used when you need to:

- Resolve a workload domain name to its ID for subsequent operations.
- Check workload domain status before performing operations.
- Retrieve workload domain details for validation or reporting.

API Endpoint:

- `GET /v1/domains` - Retrieves all domains, then filters by name.

## Usage Examples

### Example 1: Add Workload Domain Using Vars File

```bash
ansible-playbook playbooks/add_workload_domain.yml \
  -e @examples/lab/vars/wld_automation_settings.yml
```

### Example 2: Add Workload Domain Using Inline Variables

```bash
ansible-playbook playbooks/add_workload_domain.yml \
  -e "region=amer datacenter=dc01 az=az01 vcf=lab domain=w01"
```

### Example 3: Remove Workload Domain

```bash
ansible-playbook playbooks/remove_workload_domain.yml \
  -e @examples/lab/vars/wld_automation_settings.yml \
  -e "workload_domain_name=w01"
```

### Example 4: Remove Workload Domain Without Decommissioning

```bash
ansible-playbook playbooks/remove_workload_domain.yml \
  -e @examples/lab/vars/wld_automation_settings.yml \
  -e "workload_domain_name=w01" \
  -e "workload_domain_decommission_hosts=false"
```

### Example 5: Validate Changes with Check Mode

```bash
ansible-playbook playbooks/add_workload_domain.yml \
  -e @examples/lab/vars/wld_automation_settings.yml \
  --check
```

## Workflow Sequence

### Add Workload Domain Workflow

1. `playbooks/add_workload_domain.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `sddc_manager/workload_domain` role executes with `workload_domain_state: present`:
   - Checks host status and commissions hosts if needed
   - Generates workload domain payload from template
   - Validates payload with SDDC Manager API
   - Creates workload domain
   - Waits for workload domain creation task to complete

### Remove Workload Domain Workflow

1. `playbooks/remove_workload_domain.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `sddc_manager/workload_domain` role executes with `workload_domain_state: absent`:
   - Looks up workload domain ID by name
   - Collects host information for decommissioning (if `workload_domain_decommission_hosts: true`)
   - Marks workload domain for deletion
   - Removes workload domain
   - Waits for workload domain deletion task to complete
   - Decommissions hosts (if `workload_domain_decommission_hosts: true`)
