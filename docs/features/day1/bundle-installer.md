# Day 1: Manage Bundles for VCF Installer

## Overview

This workflow manages bundle download operations for a VCF Installer instance using the
`broadcom.vcf.vcf_installer.bundle` and `broadcom.vcf.vcf_installer.bundle_info` roles.

Bundles contain the software components required for VMware Cloud Foundation deployment.

Supported operations:

- Query INSTALL bundle status for the releases and components defined in `bundle.yml`.
- Download INSTALL bundles for VCF deployment.
- Delete downloaded bundle payloads from the system.

The role is state-driven via `bundle_state`:

- `present` - download bundle immediately.
- `stopped` – stop an ongoing bundle download.
- `absent` – delete a bundle from the system.

The bundled day-1 playbooks currently focus on three operational workflows:

- `playbooks/add_bundles_installer.yml` - add/download bundles from `bundle.yml`.
- `playbooks/get_bundle_status_installer.yml` - read-only status reporting for bundles from `bundle.yml`.
- `playbooks/remove_bundles_installer.yml` - remove downloaded bundle payloads for bundles from `bundle.yml`.

!!! info "About Bundles"
    **Terminology:** The VCF Installer UI refers to these as "Component Binaries", while the API
    calls them "Bundles". This collection uses "bundles" to align with the API terminology.

    Bundles (Component Binaries) in VCF Installer:

    - Contain software components for VCF products (vCenter, NSX, SDDC Manager, etc.).
    - Must be downloaded from the depot before they can be used in deployment.
    - Can be large (multiple GB) and may take significant time to download.
    - Only one download can be active per bundle at a time.
    - Support downloading for multiple VCF release versions simultaneously.

    Use Ansible's check mode (`--check`) to preview changes before execution.

## Prerequisites

Before you begin, make sure:

1. VCF Installer is deployed and operational.
2. VCF Installer is reachable and you have administrative credentials.
3. Depot is configured (online or offline) for bundle downloads.
4. Infrastructure‑as‑Code (IaC) data is defined under `./infra-as-code/`.
5. You can authenticate to VCF Installer with sufficient privileges to:
   - Query bundle information.
   - Initiate bundle downloads.
   - Delete bundles.

## Configuration Requirements

The following configuration must be provided under `./infra-as-code/`:

- VCF Installer configuration:
    - VCF Installer hostname and admin credentials.
- Depot configuration (required for bundle downloads):
    - Online depot with download token, or offline depot with connection details.
- Bundle configuration (`bundle.yml`):
    - VCF release version(s) to download.
    - Component selection (download all or specific products).

Example `bundle.yml`:

=== "9.1.x.x"

    ```yaml
    bundle:
      releases:
        - release_version: "9.1.0.0"
          download_all: false
          components:
            - avi-lb
            - cloud-proxy
            - fleet-lcm
            - identity-broker
            - license-server
            - migration-services-engine
            - nsx
            - salt-master
            - salt-raas
            - sddc-lcm
            - sddc-manager
            - software-depot
            - telemetry
            - vcenter
            - vcf-automation
            - vcf-operations
            - vcf-operations-fleet
            - vcf-operations-hcx
            - vcf-service-runtime
      download_options:
        wait_for_completion: false
        timeout: 7200
        retry_count: 3
    ```

=== "9.0.x.x"

    ```yaml
    bundle:
      releases:
        - release_version: "9.0.2.0"
          download_all: false
          components:
            - cloud-proxy
            - nsx
            - sddc-manager
            - vcenter
            - vcf-automation
            - vcf-operations
            - vcf-operations-fleet
      download_options:
        wait_for_completion: false
        timeout: 7200
        retry_count: 3
    ```

## Role Interface

Role: `broadcom.vcf.vcf_installer.bundle`

### Variables

Key variables:

- `bundle_state` - (Required) Desired state of the bundle.
  - `present`: Download the bundle immediately.
  - `stopped`: Stop an ongoing bundle download.
    - `absent`: Delete the bundle from the system.

- `bundle_id` - (Required) The ID of the bundle to manage.

**Wait Variables** (applicable when `bundle_state: present`):
  - Default: `false`.
- `bundle_timeout` - Maximum time in seconds to wait for task completion.
  - Default: `3600` (1 hour).

**Delete Variables** (applicable when `bundle_state: absent`):

- `bundle_binary_files_only` - If true, only binary files from storage will be deleted.
  - Default: `true`.
  - Recommended: keep `true` for operational cleanup so bundle records and status history remain visible.

### User-Friendly Product Names

When configuring components in `bundle.yml`, use these user-friendly names:

=== "9.1.x.x"

    | Friendly Name                  | API Name                            | Product                         |
    |--------------------------------|-------------------------------------|---------------------------------|
    | `avi-lb`                       | `NSX_ALB`                           | Avi Load Balancer               |
    | `cloud-proxy`                  | `VCF_OPS_CLOUD_PROXY`               | Cloud Proxy                     |
    | `fleet-lcm`                    | `VCF_FLEET_LCM`                     | Fleet Lifecycle                 |
    | `identity-broker`              | `VIDB`                              | Identity Broker                 |
    | `license-server`               | `VCF_LICENSE_SERVER`                | License Server                  |
    | `migration-services-engine`    | `VCF_SERVICE_VCD_MIGRATION_BACKEND` | Migration Service Engine        |
    | `nsx`                          | `NSX_T_MANAGER`                     | NSX                             |
    | `salt-master`                  | `VCF_SALT`                          | Salt Master                     |
    | `salt-raas`                    | `VCF_SALT_RAAS`                     | Salt RaaS                       |
    | `sddc-lcm`                     | `VCF_SDDC_LCM`                      | SDDC Lifecycle                  |
    | `sddc-manager`                 | `SDDC_MANAGER`                      | SDDC Manager                    |
    | `software-depot`               | `DEPOT_SERVICE`                     | Software Depot                  |
    | `telemetry`                    | `TELEMETRY_ACCEPTOR`                | Telemetry                       |
    | `vcenter`                      | `VCENTER`                           | vCenter                         |
    | `vcf-automation`               | `VRA`                               | VCF Automation                  |
    | `vcf-operations`               | `VROPS`                             | VCF Operations                  |
    | `vcf-operations-hcx`           | `HCX`                               | VCF Operations HCX              |
    | `vcf-service-runtime`          | `VSP`                               | VCF Services Runtime            |

=== "9.0.x.x"

    | Friendly Name                  | API Name                            | Product                         |
    |--------------------------------|-------------------------------------|---------------------------------|
    | `cloud-proxy`                  | `VCF_OPS_CLOUD_PROXY`               | Cloud Proxy                     |
    | `nsx`                          | `NSX_T_MANAGER`                     | NSX                             |
    | `sddc-manager`                 | `SDDC_MANAGER`                      | SDDC Manager                    |
    | `vcenter`                      | `VCENTER`                           | vCenter                         |
    | `vcf-automation`               | `VRA`                               | VCF Automation                  |
    | `vcf-operations`               | `VROPS`                             | VCF Operations                  |
    | `vcf-operations-fleet`         | `VRSLCM`                            | VCF Operations Fleet Management |

**Note:** Both friendly names (lowercase) and API names (uppercase) work. Friendly names are recommended for better readability.

### Return Values

- `changed` - Boolean indicating if changes were made.
- `msg` - Status message about the operation.
- `task` - Task information for download/stop operations (includes task ID for tracking).

Additional inputs are drawn from your IaC structure, e.g. `all_iac_vars`:

- `all_iac_vars.vcf_installer.hostname`
- `all_iac_vars.vcf_installer.username`
- `all_iac_vars.vcf_installer.password` or overrides

## Execution

### Download Bundle (`bundle_state: present`)

Example:

```yaml
- name: Download Bundle Immediately
  hosts: localhost
  roles:
    - role: broadcom.vcf.vcf_installer.bundle
      vars:
        bundle_state: present
        bundle_id: "e6ba8240-d9b7-11ef-bf62-63832c57ab1a"
```

Behavior:

1. Query bundle information:
    - Uses `vcf_installer_bundle_info` to verify bundle exists.
2. Initiate download (immediate):
    - Calls `vcf_installer_bundle` with `state: present`.
    - Sends download request to VCF Installer API.
    - Returns task information.
3. Wait for completion (if configured):
    - Polls task status until complete or timeout.
    - Verifies download success.

#### Check Mode Behavior: `present`

When run with `--check`, the module returns a message without making changes:

```shell
Check Mode: Would download bundle e6ba8240-d9b7-11ef-bf62-63832c57ab1a.
```

- No API calls are made to initiate downloads.

To see the check mode message in your playbook output, use verbose mode (`-v`) or
register and display the result:

```yaml
- name: Download Bundle
  hosts: localhost
  roles:
    - role: broadcom.vcf.vcf_installer.bundle
      vars:
        bundle_state: present
        bundle_id: "e6ba8240-d9b7-11ef-bf62-63832c57ab1a"
  register: bundle_result

- name: Display Bundle Result
  ansible.builtin.debug:
    msg: "{{ bundle_result.msg }}"
  when: ansible_check_mode
```

This gives you a dry run preview without downloading bundles.

### Stop Bundle Download (`bundle_state: stopped`)

This state remains available at the module and role level for targeted operations,
but there is no dedicated day-1 playbook for stop/cancel. The current day-1 bundle
playbooks focus on add, get status, and remove workflows.

Example:

```yaml
- name: Stop Bundle Download
  hosts: localhost
  roles:
    - role: broadcom.vcf.vcf_installer.bundle
      vars:
        bundle_state: stopped
        bundle_id: "e6ba8240-d9b7-11ef-bf62-63832c57ab1a"
```

Behavior:

1. Query current bundle download status:
    - Uses `vcf_installer_bundle_info` to check if download is in progress.
2. Stop download:
    - Sends stop/cancel request to VCF Installer API.
    - Returns task information confirming the operation.

#### Check Mode Behavior: `stopped`

When run with `--check`, the module returns a message without making changes:

```shell
Check Mode: Would stop bundle download for e6ba8240-d9b7-11ef-bf62-63832c57ab1a.
```

- No API calls are made to stop downloads.

### Delete Bundle (`bundle_state: absent`)

Example:

```yaml
- name: Delete Bundle
  hosts: localhost
  roles:
    - role: broadcom.vcf.vcf_installer.bundle
      vars:
        bundle_state: absent
        bundle_id: "e6ba8240-d9b7-11ef-bf62-63832c57ab1a"
        bundle_binary_files_only: true
```

Behavior:

1. Query bundle information:
    - Uses `vcf_installer_bundle_info` to verify bundle exists.
2. Delete bundle:
    - Calls `vcf_installer_bundle` with `state: absent`.
    - Sends delete request to VCF Installer API.
    - Returns success message.

!!! warning "Safe Delete Default"
  The remove playbook uses `binary_files_only: true` by default. This removes the
  downloaded payloads while preserving bundle records and status visibility.

  Setting `binary_files_only: false` performs a full delete and can remove bundle
  records/status history until depot metadata is refreshed.

#### Check Mode Behavior: `absent`

When run with `--check`, the module returns a message without making changes:

```shell
Check Mode: Would delete bundle e6ba8240-d9b7-11ef-bf62-63832c57ab1a.
```

- No API calls are made to delete bundles.

## SDK / API Calls

The following VCF Installer endpoints are used by the supporting module utility (`plugins/module_utils/vcf_installer.py`):

For bundle operations:

- `GET /v1/bundles` - Retrieves list of all bundles.
- `GET /v1/bundles/{id}` - Retrieves specific bundle by ID.
- `GET /v1/bundles/download-status` - Retrieves download status for bundles.
- `PATCH /v1/bundles/{id}` - Downloads or cancels bundle download.
- `DELETE /v1/bundles/{id}` - Deletes a bundle from the system.

The PATCH operation returns a task object that can be monitored for completion.

## Ansible Components
            
- Module Utils:
    - `plugins/module_utils/vcf_installer.py`
    - `plugins/module_utils/bundle_types.py`

- Modules:
    - `plugins/modules/vcf_installer_bundle.py`
    - `plugins/modules/vcf_installer_bundle_info.py`

- Roles:
    - `roles/vcf_installer/bundle`
    - `roles/vcf_installer/bundle_info`

- Playbooks:
  - `playbooks/add_bundles_installer.yml`
  - `playbooks/get_bundle_status_installer.yml`
  - `playbooks/remove_bundles_installer.yml`

## Querying Bundle Information

The `vcf_installer_bundle_info` module and `bundle_info` role provide read-only access
to bundle information and download status.

### Module: `vcf_installer_bundle_info`

This informational module retrieves bundle information from VCF Installer without making
any changes.

Parameters:

- `vcf_installer_hostname` - (Required) VCF Installer hostname or IP address.
- `vcf_installer_user` - (Required) VCF Installer username.
- `vcf_installer_password` - (Required) VCF Installer password.
- `operation` - (Required) Type of information to retrieve.
    - `list` - List all bundles with optional filtering.
    - `get_by_id` - Get a specific bundle by ID.
    - `download_status` - Get download status for bundles.

**Filter Parameters** (optional):

- `bundle_id` - Bundle ID (required for `get_by_id`, optional for `download_status`).
  - `product_type` - Filter by product type (for `list` operation). Refer to the [User-Friendly Product Names](#user-friendly-product-names) table above.
- `is_compliant` - Filter by compliance with current VCF version (for `list` operation).
- `bundle_type` - Filter by bundle type (for `list` operation).
  - User-friendly: `vmware-software`, `sddc-manager`, `vxrail`.
  - API names: `VMWARE_SOFTWARE`, `SDDC_MANAGER`, `VXRAIL`.
- `release_version` - Filter by release version (for `download_status` operation).

For `download_status`, the module reports INSTALL bundle status and does not require
an `image_type` parameter.

Return Values:

- `changed` - Always `false` (read-only operation).
- `bundles` - Bundle information (for `list` or `get_by_id` operations).
- `download_status` - Download status information (for `download_status` operation).
- `msg` - Status message describing the results.

Example usage:

```yaml
- name: Get Bundle Download Status
  broadcom.vcf.vcf_installer_bundle_info:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    operation: download_status
  register: install_bundles

- name: Display Bundle Count
  ansible.builtin.debug:
    msg: "Found {{ install_bundles.download_status.elements | length }} bundles"
```

Output example:

```
"Retrieved download status for 25 bundle(s)."
```

### Role: `bundle_info`

This role wraps the `vcf_installer_bundle_info` module to retrieve bundle information
and set it as a fact.

!!! note "Role Variable Naming"
  The role uses a `bundle_` prefix for filter variables
  to avoid naming conflicts. These map directly to the module's parameters.

Variables:

- `bundle_operation` - (Required) Type of information to retrieve (`list`, `get_by_id`, or `download_status`).
- `bundle_id`, `bundle_product_type`, `bundle_is_compliant`, `bundle_type`,
  `bundle_release_version` - Optional filter parameters.

Sets the following facts:

- `bundle_info` - Complete bundle information response.

Example:

```yaml
- name: Get IaC Settings
  ansible.builtin.include_role:
    name: broadcom.vcf.iac.get_settings

- name: Get Bundle Status
  ansible.builtin.include_role:
    name: broadcom.vcf.vcf_installer.bundle_info
  vars:
    bundle_operation: download_status

- name: Display Bundle Status
  ansible.builtin.debug:
    msg: "{{ bundle_info.msg }}"
```

The role is commonly used when you need to:

- Verify bundle download status before deployment.
- List available bundles for a specific product type.
- Check bundle information for troubleshooting or validation.

API Endpoints:

- `GET /v1/bundles` - List all bundles.
- `GET /v1/bundles/{id}` - Get specific bundle.
- `GET /v1/bundles/download-status` - Get download status.

## Usage Examples

### Example 1: Download Bundles Using Playbook

```bash
ansible-playbook playbooks/add_bundles_installer.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

### Example 2: Query Bundle Status Using Playbook

```bash
ansible-playbook playbooks/get_bundle_status_installer.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

### Example 3: Remove Downloaded Bundles Using Playbook

```bash
ansible-playbook playbooks/remove_bundles_installer.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "binary_files_only=true"
```

### Example 4: Validate Changes with Check Mode

```bash
ansible-playbook playbooks/add_bundles_installer.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
  --check
```

## Workflow Sequence

### Download Bundle Workflow

1. `playbooks/add_bundles_installer.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `vcf_installer_bundle_info` retrieves current download status per configured release
4. The playbook filters bundle elements based on `bundle.yml`
5. `vcf_installer_bundle` executes with `state: present`:
   - Initiates download for each required bundle
   - Waits for completion (if configured)
   - Verifies status and returns success message

### Get Bundle Status Workflow

1. `playbooks/get_bundle_status_installer.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `vcf_installer_bundle_info` retrieves current download status per configured release
4. The playbook filters bundle elements based on `bundle.yml`
5. The playbook prints per-bundle details and a compact summary line

### Remove Bundle Workflow

1. `playbooks/remove_bundles_installer.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `vcf_installer_bundle_info` retrieves current download status per configured release
4. The playbook filters bundle elements based on `bundle.yml`
5. Only bundles already in `SUCCESSFUL` or `SUCCESS` state are targeted for removal
6. `vcf_installer_bundle` executes with `state: absent` and `binary_files_only: true` by default
