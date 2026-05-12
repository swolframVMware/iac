# Day 2: Manage Cluster Hosts

## Overview

This workflow manages host membership in existing clusters within VMware Cloud Foundation using the
`broadcom.vcf.sddc_manager.cluster_hosts` role and the `sddc_manager_cluster_hosts` module.

Supported operations:

- Ensure hosts are present in a cluster (Cluster Expansion/Scale-Out).
- Ensure hosts are absent from a cluster (Cluster Compaction/Scale-In).

The role is state-driven via `cluster_hosts_state`:

- `present` – validate and add hosts to the cluster (Cluster Expansion/Scale-Out)..
- `absent` – validate and remove hosts from the cluster (Cluster Compaction/Scale-In).

!!! warning "Host Removal Considerations"
    When `cluster_hosts_state: absent`:

    - Hosts are removed from the cluster and returned to `UNASSIGNED_USEABLE` status.
    - Removed hosts are automatically decommissioned (`cluster_hosts_decommission_hosts: true`).
    - To skip decommissioning and retain hosts for an alternate process, set `cluster_hosts_decommission_hosts: false`.
    - Ensure VMs are migrated off hosts before removal.
    - vSAN storage rebalancing may be required.
    - The role includes safety checks to prevent removing hosts below a minimum threshold.

    Use Ansible's check mode (`--check`) to preview changes before execution.

## Prerequisites

Before you begin, make sure:

1. [Deployment prerequisites](../day1/deployment-prerequisites.md) are met.
2. [Prechecks](../day1/precheck/precheck.md) have passed.
3. Management domain and target workload domain are deployed and operational.
4. Target cluster exists and is operational.
5. For host addition:
   - ESX hosts are reachable and appropriately configured (networking, DNS, NTP, etc.).
   - Hosts are in `UNASSIGNED_USEABLE` status or ready to be commissioned.
6. For host removal:
   - Hosts are members of the target cluster.
   - VMs have been migrated off the hosts to be removed.
7. Infrastructure‑as‑Code (IaC) data is defined under `./infra-as-code/` (typically in `vsphere.yml`).
8. You can authenticate to SDDC Manager with sufficient privileges to:
   - Commission/decommission hosts.
   - Expand/compact clusters.
   - Query cluster and host information.

## Configuration Requirements

The following configuration must be provided under `./infra-as-code/`:

- vSphere configuration (`vsphere.yml`):
   - Datacenter(s) and cluster definitions.
   - ESX host specifications for hosts being added.
   - Network configuration referenced by the payload template.

- SDDC Manager configuration:
   - SDDC Manager hostname and admin credentials.
   - Cluster name where hosts will be added or removed.

The role uses IaC data (via `broadcom.vcf.iac.generate_api_payload`)
to render an API payload for the cluster scale-out/scale-in, typically from Jinja2 templates:
- `add_hosts.j2` for scale-out
- `remove_hosts.j2` for scale-in

## Role Interface

Role: `broadcom.vcf.sddc_manager.cluster_hosts`

### Variables

Key variables:

- `cluster_hosts_state` - Desired state of hosts in the cluster.
    - `present` (default): validate and add hosts to the cluster.
    - `absent`: validate and remove hosts from the cluster.
- `cluster_input` - Name of the cluster to modify. Required for both add and remove operations.
- `hosts_input` - List of host FQDNs to add or remove. Required for both operations.
- `add_hosts_template_name` - Jinja2 template for scale-out payload. Default: `add_hosts.j2`.
- `remove_hosts_template_name` - Jinja2 template for scale-in payload. Default: `remove_hosts.j2`.

Safety check variables scale-out:
- `maximum_cluster_hosts` - Maximum hosts allowed in cluster (default: 64). Set to 0 to disable.
- `force_host_addition` - Bypass maximum host safety check (default: false).

Safety check variables scale-in:
- `minimum_cluster_hosts` - Minimum hosts required in cluster (default: 3). Set to 0 to disable.
- `force_host_removal` - Bypass minimum host safety check (default: false).

Decommission variables scale-in:
- `cluster_hosts_decommission_hosts` - Controls whether removed hosts are decommissioned after removal. Default: `true`.
    - `true` (default): All removed hosts are automatically decommissioned.
    - `false`: Removed hosts remain in an `UNASSIGNED_USEABLE` status for an alternate decommission process.

Additional inputs are drawn from your IaC structure, e.g. `all_iac_vars`:

- `all_iac_vars.sddc_manager.hostname`
- `all_iac_vars.vsphere.vcenter.sso.username`
- `all_iac_vars.vsphere.vcenter.sso.password` or overrides
- Network, storage, and host configuration referenced by the templates.

### Return Values

- `changed` - Boolean indicating if changes were made.
- `msg` - Status message.
- `meta` - Response data from SDDC Manager (includes task ID for tracking).

## Execution

### Add Hosts to Cluster (`cluster_hosts_state: present`)

Example:
```yaml
- name: Add Hosts to Cluster
  hosts: localhost
  roles:
    - role: broadcom.vcf.sddc_manager.cluster_hosts
      vars:
        cluster_hosts_state: present
        cluster_input: "w01-cl01"
        hosts_input:
          - "w01-esx05.example.com"
          - "w01-esx06.example.com"
```

Behavior:

1. Get cluster information (`main.yml`):
    - Uses `sddc_manager_cluster_info` to retrieve cluster details and extract `cluster_id`.

2. Check host status (`check_hosts_to_add.yml`):
    - Validates that hosts exist in IaC configuration.
    - Uses `sddc_manager_host_info` to categorize host status:
        - `UNASSIGNED_USEABLE` hosts are ready to add.
        - Hosts not found in SDDC Manager will be commissioned.
        - `ASSIGNED` hosts cause the workflow to fail.
    - Runs `broadcom.vcf.ops.prep_hosts` to commission hosts if needed.
    - Performs safety checks against `maximum_cluster_hosts`.
    - In check mode, host commissioning is skipped (no changes).

3. Generate scale-out payload (`generate_add_hosts_payload.yml`):
    - Invokes `broadcom.vcf.iac.generate_api_payload` to produce `api_payload_json`
      from `add_hosts_template_name` (default `add_hosts.j2`).

4. Validate payload (`validate_add_hosts_payload.yml`):
    - Calls `sddc_manager_cluster_hosts` with:
        - `state: present`
        - `validate: true`
    - Fails if validation errors are returned.

5. Add hosts to cluster (`add_hosts.yml`):
    - Calls `sddc_manager_cluster_hosts` with:
        - `state: present`
        - `validate: false`
    - Receives a task ID and waits for task completion using
      `sddc_manager_tasks_status` (unless in check mode).
    - Fails if the task reports error codes.

#### Check Mode Behavior: `present`

- The role still:
    - Runs cluster and host checks (read‑only API calls, plus safety checks).
    - Generates the payload.
- The module detects check mode and:
    - Returns `changed: true` with a preview message.
    - Does not perform validation or actual host addition.
- Use `validate_only: true` (without check mode) for validation without changes.

This gives you a quick dry run showing what would happen.

### Remove Hosts from Cluster (`cluster_hosts_state: absent`)

Example:

```yaml
- name: Remove Hosts from Cluster
  hosts: localhost
  roles:
    - role: broadcom.vcf.sddc_manager.cluster_hosts
      vars:
        cluster_hosts_state: absent
        cluster_input: "w01-cl01"
        hosts_input:
          - "esx-04b.example.com"
        # Optionally override safety checks:
        # minimum_cluster_hosts: 4
        # force_host_removal: false
        # Optional: Keep hosts in inventory for an alternate decommission process.
        # cluster_hosts_decommission_hosts: false
```

Behavior:

1. Get cluster information (`main.yml`):
    - Uses `sddc_manager_cluster_info` to retrieve cluster details and extract `cluster_id`.

2. Check hosts can be removed (`check_hosts_to_remove.yml`):
    - Validates that hosts to remove exist in the cluster.
    - Performs safety checks against `minimum_cluster_hosts`.
    - Builds mapping of host FQDNs to IDs for the removal payload.

3. Generate scale-in payload (`generate_remove_hosts_payload.yml`):
    - Invokes `broadcom.vcf.iac.generate_api_payload` to produce `api_payload_json`
      from `remove_hosts_template_name` (default `remove_hosts.j2`).

4. Validate payload (`validate_remove_hosts_payload.yml`):
    - Calls `sddc_manager_cluster_hosts` with:
        - `state: absent`
        - `validate: true`
    - Fails if validation errors are returned.

5. Remove hosts from cluster (`remove_hosts.yml`):
    - Calls `sddc_manager_cluster_hosts` with:
        - `state: absent`
        - `validate: false`
    - Receives a task ID and waits for task completion using
      `sddc_manager_tasks_status` (unless in check mode).
    - Fails if the task reports error codes.

6. Decommission removed hosts (`decommission_hosts.yml`, if `cluster_hosts_decommission_hosts: true`):
    - After successful host removal, decommissions all hosts that were removed from the cluster.
    - Uses the `broadcom.vcf.sddc_manager.host` role with `host_state: absent`.

#### Check Mode Behavior: `absent`

- The module detects `check_mode` and does not call the API:
    - Returns `changed: true` with a message like:

        ```shell
        Check Mode: Would update cluster <cluster_id> and remove the following hosts: <host_list>.
        ```

- The role:
    - Displays this message.
    - If `cluster_hosts_decommission_hosts: true`, displays which hosts would be decommissioned.
    - Skips validation and task waiting.
    - Does not actually remove hosts or decommission them.

This lets you see *which* hosts would be removed and *which* would be decommissioned without performing any API calls.

## SDK / API Calls

The following SDDC Manager endpoints are used by the supporting module utility (`plugins/module_utils/sddc_manager.py`):

For scale-out:

- `POST /v1/clusters/{id}/validations` - Validates cluster scale-out configuration.
- `PATCH /v1/clusters/{id}` with `clusterExpansionSpec` - Scale-out a cluster.

For scale-in:

- `POST /v1/clusters/{id}/validations` - Validates cluster scale-in configuration.
- `PATCH /v1/clusters/{id}` with `clusterCompactionSpec` - Scale-in a cluster.

Additional calls for cluster host workflows:

- `GET /v1/clusters` - Retrieves all clusters (for lookup by name).
- `GET /v1/hosts` - Retrieves all hosts for ID/FQDN mapping.
- `GET /v1/hosts?fqdn={fqdn}` - Retrieves specific host status for categorization.
- `POST /v1/hosts/validations` - Validates host commissioning.
- `POST /v1/hosts` - Commissions hosts.

Task tracking:

- `GET /v1/tasks/{id}` - Used by `sddc_manager_tasks_status` to poll scale-out and scale-in tasks.

## Ansible Components

- Module Utils:
    - `plugins/module_utils/sddc_manager.py`

- Modules:
    - `plugins/modules/sddc_manager_cluster_hosts.py`
    - `plugins/modules/sddc_manager_cluster_info.py`
    - `plugins/modules/sddc_manager_tasks_status.py`
    - `plugins/modules/sddc_manager_host.py`
    - `plugins/modules/sddc_manager_host_info.py`

- Roles:
    - `roles/sddc_manager/cluster_hosts`
    - `roles/sddc_manager/cluster_info`
    - `roles/ops/prep_hosts`

- Playbooks:
    - `playbooks/add_cluster_hosts.yml` (Uses `cluster_hosts_state: present`)
    - `playbooks/remove_cluster_hosts.yml` (Uses `cluster_hosts_state: absent`)

## Querying Information

There is no dedicated info module for cluster hosts. Host membership is retrieved via the
`sddc_manager_cluster_info` module and `cluster_info` role, which return full cluster details
including the list of host IDs assigned to the cluster.

For full documentation of the `sddc_manager_cluster_info` module and `cluster_info` role, see
[Manage Clusters — Querying Cluster Information](./cluster.md#querying-information).

API Endpoints:

- `GET /v1/clusters/{id}` - Retrieves cluster details including assigned host IDs.
- `GET /v1/hosts` - Retrieves all hosts for FQDN/ID mapping.

## Usage Examples

### Example 1: Add Hosts to Cluster Using Vars File

```bash
ansible-playbook playbooks/add_cluster_hosts.yml \
  -e @examples/lab/vars/wld_automation_settings.yml
```

### Example 2: Add Hosts to Cluster Using Inline Variables

```bash
ansible-playbook playbooks/add_cluster_hosts.yml \
  -e "region=amer datacenter=dc01 az=az01 vcf=lab domain=w01" \
  -e "cluster_input=w01-cl01" \
  -e "hosts_input=['w01-esx05.example.com','w01-esx06.example.com']"
```

### Example 3: Remove Hosts from Cluster

```bash
ansible-playbook playbooks/remove_cluster_hosts.yml \
  -e "region=amer datacenter=dc01 az=az01 vcf=lab domain=w01" \
  -e "cluster_input=w01-cl01" \
  -e "hosts_input=['w01-esx05.example.com']"
```

### Example 4: Force Host Removal Below Minimum

```bash
ansible-playbook playbooks/remove_cluster_hosts.yml \
  -e "cluster_input=w01-cl01" \
  -e "hosts_input=['w01-esx05.example.com','w01-esx06.example.com']" \
  -e "force_host_removal=true"
```

### Example 5: Remove Hosts Without Decommissioning

```bash
ansible-playbook playbooks/remove_cluster_hosts.yml \
  -e "region=amer datacenter=dc01 az=az01 vcf=lab domain=w01" \
  -e "cluster_input=w01-cl01" \
  -e "hosts_input=['w01-esx05.example.com']" \
  -e "cluster_hosts_decommission_hosts=false"
```

### Example 6: Validate Changes with Check Mode

```bash
ansible-playbook playbooks/add_cluster_hosts.yml \
  -e @examples/lab/vars/wld_automation_settings.yml \
  --check
```

## Workflow Sequence

### Add Hosts Workflow

1. `playbooks/add_cluster_hosts.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `sddc_manager/cluster_hosts` role executes with `cluster_hosts_state: present`:
   - Gets cluster information
   - Checks host status and commissions hosts if needed
   - Generates add hosts payload from template
   - Validates payload with SDDC Manager API
   - Adds hosts to cluster
   - Waits for cluster scale-out task to complete

### Remove Hosts Workflow

1. `playbooks/remove_cluster_hosts.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `sddc_manager/cluster_hosts` role executes with `cluster_hosts_state: absent`:
   - Gets cluster information
   - Validates hosts can be safely removed
   - Generates remove hosts payload from template
   - Validates payload with SDDC Manager API
   - Removes hosts from cluster
   - Waits for cluster scale-in task to complete
   - Decommissions removed hosts (if `cluster_hosts_decommission_hosts: true`)
