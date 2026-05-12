# Day 2: Manage NSX Edge Clusters

## Overview

This workflow manages NSX Edge clusters in VMware Cloud Foundation using the
`broadcom.vcf.sddc_manager.nsx_edge_cluster` role and the `sddc_manager_nsx_edge_cluster` module.

Supported operations:

- Ensure NSX Edge cluster is present (Added).

The role is state-driven via `edge_cluster_state`:

- `present` – add an NSX Edge cluster.

!!! warning "Deletion Not Supported"
    NSX Edge cluster deletion is not supported by the VCF API:

    - Edge clusters cannot be deleted directly.

    Use Ansible's check mode (`--check`) to preview changes before execution.

## Prerequisites

Before you begin, make sure:

1. [Deployment prerequisites](../day1/deployment-prerequisites.md) are met.
2. Management domain and target workload domain are deployed and operational.
3. SDDC Manager is reachable and you have administrative credentials.
4. Infrastructure‑as‑Code (IaC) data for NSX Edge clusters is defined under
   `./infra-as-code/` (typically in `nsx.yml`).
5. You can authenticate to SDDC Manager with sufficient privileges to:
   - Add NSX Edge clusters.
   - Query cluster information.
6. Edge cluster configuration details are prepared:
   - Edge node hostnames and management IPs.
   - Form factors (SMALL, MEDIUM, LARGE, XLARGE).
   - Storage and networking assignments.
   - Credentials for edge node accounts (root, admin, audit).
   - BGP configuration (ASN, routing details).
   - Tier-0 gateway settings.

## Configuration Requirements

The following configuration must be provided under `./infra-as-code/`:

- NSX configuration (`nsx.yml`):
    - Edge cluster specifications:
        - Edge cluster name and type.
        - Edge node details (names, IPs, form factors).
        - Tier-0 gateway configuration.
        - BGP ASN and routing settings.
        - High availability mode.
        - Storage and datastore assignments.
        - Network configurations.
        - Credentials for edge accounts.

- vSphere configuration:
    - Compute cluster information.
    - Network and datastore assignments.

The role uses IaC data (via `broadcom.vcf.iac.generate_api_payload`)
to render an API payload for NSX Edge cluster operations, using the Jinja2 template:
- `nsx_edge_cluster.j2` for creation

## Role Interface

Role: `broadcom.vcf.sddc_manager.nsx_edge_cluster`

### Variables

Key variables:

- `edge_cluster_state` - Desired state of the NSX Edge cluster.
    - `present` (default): add an NSX Edge cluster.
- `cluster_input` - Name of the compute cluster where edge nodes will be deployed.
- `edge_cluster_template_name` - Jinja2 template for creation payload. Default: `nsx_edge_cluster.j2`.

Vault-backed sample IaC values:

- `vault_edge_root_password`, `vault_edge_admin_password`, `vault_edge_audit_password`
  - Used by the sample `nsx.yml` edge cluster credentials.
- `vault_bgp_peer_password`
  - Used by the sample `nsx.yml` BGP peer password entries.

See [Manage Vaulted Passwords](../utilities/ansible-vault.md) for a complete
example of creating and supplying these `vault_*` variables.

### Return Values

- `changed` - Boolean indicating if changes were made.
- `msg` - Status message.
- `meta` - Response data from SDDC Manager (includes task ID for tracking).

Additional inputs are drawn from your IaC structure, e.g. `all_iac_vars`:

- `all_iac_vars.sddc_manager.hostname`
- `all_iac_vars.vsphere.vcenter.sso.username`
- `all_iac_vars.vsphere.vcenter.sso.password` or overrides
- NSX Edge cluster configuration (extracted from NSX IaC data)

## Execution

### Add NSX Edge Cluster (`edge_cluster_state: present`)

Example:

```yaml
- name: Add NSX Edge Cluster
  hosts: localhost
  roles:
    - role: broadcom.vcf.sddc_manager.nsx_edge_cluster
      vars:
        edge_cluster_state: present
        cluster_input: "w01-cl01"
        # Optionally override template:
        # edge_cluster_template_name: "custom_nsx_edge_cluster.j2"
```

Behavior:

1. Get cluster information (`present.yml`):
    - Uses `sddc_manager_cluster_info` to retrieve compute cluster details.

2. Generate payload (`generate_payload.yml`):
    - Extracts NSX Edge cluster configuration from IaC data.
    - Invokes `broadcom.vcf.iac.generate_api_payload` with template.
    - Sets `api_payload_json` variable with edge cluster configuration.

3. Validate payload (`validate_edge_cluster.yml`):
    - Calls `sddc_manager_nsx_edge_cluster` with:
        - `state: present`
        - `validate_only: true`
    - Fails if validation errors are returned.

4. Add edge cluster (`add_edge_cluster.yml`):
    - Calls `sddc_manager_nsx_edge_cluster` with:
        - `state: present`
        - `validate_only: false`
    - Monitors task until completion (unless in check mode).

#### Check Mode Behavior: `present`

- The module detects check mode and returns a message:

    ```shell
    Check Mode: NSX Edge cluster payload validated successfully; no changes would be made.
    ```

This gives you a dry run preview: validation is performed, but no edge cluster is created.

## SDK / API Calls

The following SDDC Manager endpoints are used by the supporting module utility (`plugins/module_utils/sddc_manager.py`):

For addition:

- `GET /v1/clusters` - Retrieves compute cluster information.
- `POST /v1/edge-clusters/validations` - Validates edge cluster configuration.
- `POST /v1/edge-clusters` - Adds an NSX Edge cluster.
- `GET /v1/tasks/{id}` - Monitors edge cluster creation task progress.

## Ansible Components

- Module Utils:
    - `plugins/module_utils/sddc_manager.py`

- Modules:
    - `plugins/modules/sddc_manager_nsx_edge_cluster.py`
    - `plugins/modules/sddc_manager_nsx_edge_cluster_info.py`
    - `plugins/modules/sddc_manager_cluster_info.py`
    - `plugins/modules/sddc_manager_tasks_status.py`

- Roles:
    - `roles/sddc_manager/nsx_edge_cluster`
    - `roles/sddc_manager/nsx_edge_cluster_info`
    - `roles/sddc_manager/cluster_info`
    - `roles/iac/generate_api_payload`

- Playbooks:
    - `playbooks/add_nsx_edge_cluster.yml` (Uses `edge_cluster_state: present`)

## Related Documentation

For more information about NSX Edge cluster operations, see:

- [VMware Cloud Foundation API - Create Edge Cluster](https://developer.broadcom.com/xapis/vmware-cloud-foundation-api/latest/nsx-tedge-clusters/)
- [Manage Clusters](./cluster.md)
- [Manage Workload Domains](./workload-domain.md)

## Querying Information

The `sddc_manager_nsx_edge_cluster_info` module and `nsx_edge_cluster_info` role provide read-only access to edge cluster data.

### Module: `sddc_manager_nsx_edge_cluster_info`

This informational module retrieves NSX edge cluster details from SDDC Manager without making any changes.

Parameters:

- `sddc_manager_hostname` - (Required) SDDC Manager hostname or IP address.
- `sddc_manager_user` - (Required) SDDC Manager username.
- `sddc_manager_password` - (Required) SDDC Manager password.
- `edge_cluster_name` - (Optional) Name of the edge cluster to retrieve. Mutually exclusive with `edge_cluster_id`.
- `edge_cluster_id` - (Optional) ID of the edge cluster to retrieve. Mutually exclusive with `edge_cluster_name`.
- If neither is specified, returns all edge clusters.

Return Values:

- `edge_clusters` - List of all edge clusters (when no specific cluster is requested).
- `edge_cluster` - Single edge cluster details (when name or ID is specified).
- `changed` - Always `false` (read-only operation).
- `msg` - Status or error message.

Example:

```yaml
- name: Get NSX Edge Cluster Information
  broadcom.vcf.sddc_manager_nsx_edge_cluster_info:
    sddc_manager_hostname: "{{ all_iac_vars.sddc_manager.hostname }}"
    sddc_manager_user: "{{ all_iac_vars.vsphere.vcenter.sso.username }}"
    sddc_manager_password: "{{ vcenter_administrator_password | default(all_iac_vars.vsphere.vcenter.sso.password) }}"
    edge_cluster_name: "edge-cluster-01"
  register: edge_cluster_info

- name: Display Edge Cluster ID
  ansible.builtin.debug:
    msg: "Edge Cluster ID: {{ edge_cluster_info.edge_cluster.id }}"
```

### Role: `nsx_edge_cluster_info`

This role wraps the `sddc_manager_nsx_edge_cluster_info` module to retrieve edge cluster information and set it as a fact.

Variables:

- `edge_cluster_name` - (Optional) Name of the edge cluster to query.
- `edge_cluster_id` - (Optional) ID of the edge cluster to query.

Sets the following facts:

- `edge_cluster_info` - Complete edge cluster information response.
- `edge_cluster_id` - Extracted edge cluster ID for convenience.

Example:

```yaml
- name: Get IaC Settings
  ansible.builtin.include_role:
    name: broadcom.vcf.iac.get_settings

- name: Get NSX Edge Cluster Information
  ansible.builtin.include_role:
    name: broadcom.vcf.sddc_manager.nsx_edge_cluster_info
  vars:
    edge_cluster_name: "edge-cluster-01"

- name: Display NSX Edge Cluster ID
  ansible.builtin.debug:
    msg: "Edge Cluster ID: {{ edge_cluster_id }}"
```

The role automatically sets `edge_cluster_id` as a fact when retrieving a specific edge cluster.

API Endpoint:

- `GET /v1/edge-clusters` - Retrieves all NSX Edge clusters.

## Usage Examples

### Example 1: Add NSX Edge Cluster Using Vars File

```bash
ansible-playbook playbooks/add_nsx_edge_cluster.yml \
  -e @examples/lab/vars/wld_automation_settings.yml
```

### Example 2: Add NSX Edge Cluster Using Inline Variables

```bash
ansible-playbook playbooks/add_nsx_edge_cluster.yml \
  -e "region=amer datacenter=dc01 az=az01 vcf=lab domain=w01" \
  -e "cluster_input=w01-cl01"
```

### Example 3: Validate Changes with Check Mode

```bash
ansible-playbook playbooks/add_nsx_edge_cluster.yml \
  -e @examples/lab/vars/wld_automation_settings.yml \
  --check
```

## Workflow Sequence

### Add NSX Edge Cluster Workflow

1. `playbooks/add_nsx_edge_cluster.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `sddc_manager/nsx_edge_cluster` role executes with `edge_cluster_state: present`:
   - Gets compute cluster information
   - Extracts NSX Edge cluster configuration from IaC
   - Generates edge cluster payload from template
   - Validates payload with SDDC Manager API
   - Creates NSX Edge cluster
   - Waits for edge cluster creation task to complete
