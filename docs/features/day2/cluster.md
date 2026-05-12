# Day 2: Manage Clusters

## Overview

This workflow manages clusters in workload domains within VMware Cloud Foundation using the
`broadcom.vcf.sddc_manager.cluster` role and the `sddc_manager_cluster` module.

Supported operations:

- Ensure a cluster is present (Validated and Added).
- Ensure a cluster is absent (Removed).

The role is state-driven via `cluster_state`:

- `present` – validate and add the cluster to a workload domain.
- `absent` – resolve the cluster by name and remove it.

!!! warning "Deletion is Irreversible"
    When `cluster_state: absent`:

    - The cluster and all VMs within it are deleted.
    - Datastores associated with the cluster are destroyed.
    - Hosts from the cluster are set to an `UNASSIGNED_UNUSEABLE` status.
    - All hosts from the cluster are automatically decommissioned (`cluster_decommission_hosts: true`).
    - To skip decommissioning and retain hosts for an alternate process, set `cluster_decommission_hosts: false`.
    - Network configurations may need manual cleanup.

    Use Ansible's check mode (`--check`) to preview changes before execution.

## Prerequisites

Before you begin, make sure:

1. [Deployment prerequisites](../day1/deployment-prerequisites.md) are met.
2. [Prechecks](../day1/precheck/precheck.md) have passed.
3. Management domain and target workload domain are deployed and operational.
4. ESX hosts that will back the cluster are reachable and appropriately 
   configured (networking, DNS, NTP, etc.).
5. Infrastructure‑as‑Code (IaC) data for clusters is defined under
   `./infra-as-code/` (typically in `vsphere.yml` and related files).
6. You can authenticate to SDDC Manager with sufficient privileges to:
   - Commission/decommission hosts.
   - Add and remove clusters.
   - Query cluster and workload domain information.

## Configuration Requirements

The following configuration must be provided under `./infra-as-code/`:

- vSphere configuration (`vsphere.yml`):
    - Datacenter(s), cluster definitions, ESX hosts.
    - Cluster‑specific configuration (compute, storage, and network
      parameters used in the payload template).

- SDDC Manager configuration:
    - SDDC Manager hostname and admin credentials.
    - Workload domain name where the cluster will be added.
    - Any cluster‑specific settings referenced by the payload template.

The role uses IaC data (via `broadcom.vcf.iac.generate_api_payload`)
to render an API payload for the cluster, typically from a Jinja2 template
such as `cluster.j2`.

## Role Interface

Role: `broadcom.vcf.sddc_manager.cluster`

### Variables

Key variables:

- `cluster_state` - Desired state of the cluster.
    - `present` (default): validate and add the cluster.
    - `absent`: remove the cluster.
- `cluster_input` - Name of the cluster to manage. Required for both add and remove operations.
- `hosts_input` - List of host FQDNs for cluster creation (required when `cluster_state: present`).
- `cluster_decommission_hosts` - Controls whether hosts are decommissioned after cluster removal. Default: `true`.
    - `true` (default): All hosts from the cluster are automatically decommissioned.
    - `false`: All hosts from the cluster remain in an `UNASSIGNED_UNUSEABLE` status for an alternate decommission process.
- `cluster_template_name` - Jinja2 template used to generate the cluster payload for creation. Default: `cluster.j2`.

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

### Add Cluster (`cluster_state: present`)

Example:

```yaml
- name: Add Cluster to Workload Domain
  hosts: localhost
  roles:
    - role: broadcom.vcf.sddc_manager.cluster
      vars:
        cluster_state: present
        cluster_input: "w01-cl01"
        hosts_input:
          - "w01-esx01.example.com"
          - "w01-esx02.example.com"
          - "w01-esx03.example.com"
          - "w01-esx04.example.com"
        # Optionally override template:
        # cluster_template_name: "custom_cluster.j2"
```

Behavior:

1. Get domain and LCM information (`present.yml`):
    - Uses `sddc_manager_workload_domain_info` to retrieve workload domain details.
    - Uses `sddc_manager_lcm_image_info` to get available cluster images.

2. Host checks and preparation (`check_hosts_status.yml`):
    - Validates that required hosts exist in IaC configuration.
    - Uses `sddc_manager_host_info` to categorize host status.
    - Fails if hosts are already assigned or in unexpected states.
    - Runs `broadcom.vcf.ops.prep_hosts` to prepare and (if needed) commission hosts.
      - In check mode, host preparation is skipped (no changes).

3. Generate cluster payload (`generate_payload.yml`):
    - Invokes `broadcom.vcf.iac.generate_api_payload` to produce `api_payload_json`
      from `cluster_template_name` (default `cluster.j2`).

4. Validate payload (`validate_cluster.yml`):
    - Calls `sddc_manager_cluster` with:
      - `state: present`
      - `validate_only: true`
    - Fails if validation errors are returned.

5. Create cluster (`add_cluster.yml`):
    - Calls `sddc_manager_cluster` with:
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
- The add step does not actually add the cluster:
    - The module detects check mode and returns `changed: true` with a message like:
      
      ```shell
      Check Mode: Cluster would be created; no changes were performed.
      ```
    
    - The role does not wait for a creation task.

This gives you a realistic dry run: errors are surfaced, but nothing is changed.

### Remove Cluster (`cluster_state: absent`)

Example:

```yaml
- name: Remove Cluster from Workload Domain
  hosts: localhost
  roles:
    - role: broadcom.vcf.sddc_manager.cluster
      vars:
        cluster_state: absent
        cluster_input: "w01-cl01"
        # Optional: Keep hosts in inventory for an alternate decommission process.
        # cluster_decommission_hosts: false
```

Behavior:

1. Lookup by name (`absent.yml`):
    - Uses `sddc_manager_cluster_info` to locate the cluster by `cluster_input`
      and extract `cluster_id`.

2. Collect resources for decommissioning (`decommission_info.yml`, only if `cluster_decommission_hosts: true`):
    - Retrieves cluster details using `sddc_manager_cluster_info`.
    - Extracts host IDs from the cluster.
    - Retrieves host details using `sddc_manager_host_info`.
    - Builds a list of host FQDNs (`hosts_to_decommission`) for later decommissioning.
    - This step happens **before** cluster removal to preserve host information.

3. Remove (`remove_cluster.yml`):
    - Calls `sddc_manager_cluster` with:
      - `state: absent`
      - `cluster_payload.id: "{{ cluster_id }}"`

   The module performs a two-step deletion:

   1. `PATCH /v1/clusters/{id}` with `{"markForDeletion": true}` (mark the cluster for deletion).
   2. `DELETE /v1/clusters/{id}` (trigger cluster removal).

4. Wait for removal task:
    - Extracts the remove task ID from `remove_result.meta.id`.
    - Uses `sddc_manager_tasks_status` to poll the task until completion.
    - Fails if the task reports error codes.
    - Prints a success message on completion.

5. Decommission hosts (`decommission_resources.yml`, if `cluster_decommission_hosts: true`):
    - After successful cluster removal, decommissions all hosts that were part of the cluster.
    - Uses the `broadcom.vcf.sddc_manager.host` role with `host_state: absent`.

#### Check Mode Behavior: `absent`

- The module detects `check_mode` and does not call the API:
   - Returns `changed: true` with a message like:

     ```shell
     Check Mode: Cluster ID '<id>' would be marked for deletion and removed; no changes were performed.
     ```

- The role:
  - Displays this message.
  - If `cluster_decommission_hosts: true`, collects and displays which hosts would be decommissioned.
  - Skips waiting for a removal task.
  - Does not actually remove the cluster or decommission hosts.

This lets you see *which* cluster would be removed, *which* hosts would be decommissioned, and confirm the plan without performing the deletion.

## SDK / API Calls

The following SDDC Manager endpoints are used by the supporting module utility (`plugins/module_utils/sddc_manager.py`):

For creation:

- `POST /v1/clusters/validations` - Validates cluster configuration.
- `POST /v1/clusters` - Creates a cluster.

For deletion:

- `PATCH /v1/clusters/{id}` with body `{"markForDeletion": true}` - Marks a cluster for deletion.
- `DELETE /v1/clusters/{id}` - Removes a cluster.

Additional calls for cluster workflows:

- `GET /v1/clusters` - Retrieves all clusters (for lookup by name).
- `GET /v1/domains` - Retrieves workload domain information.
- `GET /v1/hosts?fqdn={fqdn}` - Retrieves host status for categorization.
- `POST /v1/hosts/validations` - Validates host commissioning.
- `POST /v1/hosts` - Commissions hosts.

Task tracking:

- `GET /v1/tasks/{id}` - Used by `sddc_manager_tasks_status` to poll creation and deletion tasks.

## Ansible Components

- Module Utils:
    - `plugins/module_utils/sddc_manager.py`

- Modules:
    - `plugins/modules/sddc_manager_cluster.py`
    - `plugins/modules/sddc_manager_cluster_info.py`
    - `plugins/modules/sddc_manager_tasks_status.py`
    - `plugins/modules/sddc_manager_host.py`
    - `plugins/modules/sddc_manager_host_info.py`
    - `plugins/modules/sddc_manager_workload_domain_info.py`
    - `plugins/modules/sddc_manager_lcm_image_info.py`

- Roles:
    - `roles/sddc_manager/cluster`
    - `roles/sddc_manager/cluster_info`
    - `roles/sddc_manager/workload_domain_info`
    - `roles/sddc_manager/lcm_image_info`

- Playbooks:
    - `playbooks/add_cluster.yml` (Uses `cluster_state: present`)
    - `playbooks/remove_cluster.yml` (Uses `cluster_state: absent`)

## Querying Information

The `sddc_manager_cluster_info` module and `cluster_info` role provide read-only access to cluster data.

### Module: `sddc_manager_cluster_info`

This informational module retrieves cluster details from SDDC Manager without making any changes.

Parameters:

- `sddc_manager_hostname` - (Required) SDDC Manager hostname or IP address.
- `sddc_manager_user` - (Required) SDDC Manager username.
- `sddc_manager_password` - (Required) SDDC Manager password.
- `cluster_name` - (Optional) Name of the cluster to retrieve. Mutually exclusive with `cluster_id`.
- `cluster_id` - (Optional) ID of the cluster to retrieve. Mutually exclusive with `cluster_name`.
- If neither is specified, returns all clusters.

Return Values:

- `clusters` - List of all clusters (when no specific cluster is requested).
- `cluster` - Single cluster details (when name or ID is specified).
- `changed` - Always `false` (read-only operation).
- `msg` - Error message if cluster not found.

Example:

```yaml
- name: Get Cluster Information
  broadcom.vcf.sddc_manager_cluster_info:
    sddc_manager_hostname: "{{ all_iac_vars.sddc_manager.hostname }}"
    sddc_manager_user: "{{ all_iac_vars.vsphere.vcenter.sso.username }}"
    sddc_manager_password: "{{ vcenter_administrator_password | default(all_iac_vars.vsphere.vcenter.sso.password) }}"
    cluster_name: "{{ cluster_input }}"
  register: cluster_info

- name: Display Cluster ID
  ansible.builtin.debug:
    msg: "Cluster ID: {{ cluster_info.cluster.id }}"
```

### Role: `cluster_info`

This role wraps the `sddc_manager_cluster_info` module to retrieve cluster information and set it as facts.

Variables:

- Uses `cluster_input` or `cluster_id` to determine which cluster to query.

Sets the following facts:

- `cluster_info` - Complete cluster information response.
- `cluster_id` - Extracted cluster ID for convenience.

Example:

```yaml
- name: Get IaC Settings
  ansible.builtin.include_role:
    name: broadcom.vcf.iac.get_settings

- name: Get Cluster Information
  ansible.builtin.include_role:
    name: broadcom.vcf.sddc_manager.cluster_info
  vars:
    cluster_input: "w01-cl01"

- name: Display Cluster ID
  ansible.builtin.debug:
    msg: "Cluster ID: {{ cluster_id }}"
```

The role is commonly used when you need to:

- Resolve a cluster name to its ID for subsequent operations.
- Check cluster status before performing operations.
- Retrieve cluster details for validation or reporting.

API Endpoint:

- `GET /v1/clusters` - Retrieves all clusters, then filters by name or ID.

## Usage Examples

### Example 1: Add Cluster Using Vars File

```bash
ansible-playbook playbooks/add_cluster.yml \
  -e @examples/lab/vars/wld_automation_settings.yml
```

### Example 2: Add Cluster Using Inline Variables

```bash
ansible-playbook playbooks/add_cluster.yml \
  -e "region=amer datacenter=dc01 az=az01 vcf=lab domain=w01 cluster_input=w01-cl01"
```

### Example 3: Remove Cluster

```bash
ansible-playbook playbooks/remove_cluster.yml \
  -e "region=amer datacenter=dc01 az=az01 vcf=lab domain=w01 cluster_input=w01-cl01"
```

### Example 4: Remove Cluster Without Decommissioning

```bash
ansible-playbook playbooks/remove_cluster.yml \
  -e "region=amer datacenter=dc01 az=az01 vcf=lab domain=w01 cluster_input=w01-cl01" \
  -e "cluster_decommission_hosts=false"
```

### Example 5: Validate Changes with Check Mode

```bash
ansible-playbook playbooks/add_cluster.yml \
  -e @examples/lab/vars/wld_automation_settings.yml \
  --check
```

## Workflow Sequence

### Add Cluster Workflow

1. `playbooks/add_cluster.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `sddc_manager/cluster` role executes with `cluster_state: present`:
   - Gets workload domain information
   - Gets LCM image information
   - Checks host status and commissions hosts if needed
   - Generates cluster payload from template
   - Validates payload with SDDC Manager API
   - Creates cluster
   - Waits for cluster creation task to complete

### Remove Cluster Workflow

1. `playbooks/remove_cluster.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `sddc_manager/cluster` role executes with `cluster_state: absent`:
   - Looks up cluster ID by name
   - Collects host information for decommissioning (if `cluster_decommission_hosts: true`)
   - Removes cluster
   - Waits for cluster deletion task to complete
   - Decommissions hosts (if `cluster_decommission_hosts: true`)
