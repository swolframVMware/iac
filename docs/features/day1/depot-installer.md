# Day 1: Manage Depot Settings for VCF Installer

## Overview

This workflow manages depot configuration for VCF Installer instance using the
`broadcom.vcf.vcf_installer.depot` role and the `vcf_installer_depot` module.

Supported operations:

- Ensure depot configuration is present (Online or Offline).
- Ensure depot configuration is absent (Disabled).

The role is state-driven via `depot_state`:

- `present` – enable depot configuration (online or offline based on `depot_type`).
- `absent` – disable depot configuration.

!!! info "About Depot Configuration for VCF Installer"
    VCF Installer supports two types of depot configurations:
    
    - **Online Depot**: Uses the Broadcom software depot to download software bundles.
        - Requires valid download token from the Broadcom Support Portal (9.0.x.x).
        - Requires Internet connectivity from VCF Installer.
    
    - **Offline Depot**: Uses a local depot to download software bundles.
        - Requires a local depot server with downloaded bundles.
        - Uses HTTP or HTTPS protocol.
        - Supports authentication with username and password.
        - Requires SSL certificate that is trusted by VCF Installer.
    
    Only one depot type can be active at a time.

## Prerequisites

Before you begin, make sure:

1. [Deployment prerequisites](../day1/deployment-prerequisites.md) are met.
2. VCF Installer is deployed and operational.
3. VCF Installer is reachable and you have administrative credentials.
4. Infrastructure‑as‑Code (IaC) data is defined under `./infra-as-code/`.
5. You can authenticate to VCF Installer with sufficient privileges to:
   - Query and manage depot configuration.

## Configuration Requirements

The following configuration must be provided under `./infra-as-code/`:

- VCF Installer configuration:
    - VCF Installer hostname and credentials.
    - Depot configuration (type, credentials, server details).

- Depot configuration (for online depot):
    - Download token from Broadcom Support Portal.

- Depot configuration (for offline depot):
    - Offline depot server hostname and port.
    - Username and password for authentication.
    - SSL thumbprint of the depot server certificate (optional; auto-retrieved if not provided).

The role reads depot configuration from IaC structure at `all_iac_vars.depot`:

```yaml
depot:
  type: offline
  hostname: "depot.example.com"
  port: 443
  username: "vcf"
  password: "password"
  ssl_thumbprint: "AB:CD:EF:12:34:56:78:90:AB:CD:EF:12:34:56:78:90:AB:CD:EF:12"
```

Variables can be manually specified to override IaC configuration.

## Role Interface

Role: `broadcom.vcf.vcf_installer.depot`

### Variables

Key variables:

- `depot_state` - Desired state of depot configuration.
    - `present` (default): enable depot configuration (online or offline based on `depot_type`).
    - `absent`: disable depot configuration.
- `depot_type` - Type of depot to configure (required when `depot_state` is `present`).
    - `online`: configure online depot with Broadcom download token.
    - `offline`: configure offline depot with local server.
        - Default: Read from IaC at `all_iac_vars.depot.type`.

**Online Depot Variables** (required when `depot_type` is `online`):

- `depot_download_token` - Token from the Broadcom Support Portal (9.0.x.x).
    - Default: Read from IaC at `all_iac_vars.depot.download_token`.
- `depot_download_activation_code` - Activation code from the Broadcom Support Portal (9.1.x.x+).
    - Default: Read from IaC at `all_iac_vars.depot.activation_code`.

!!! note
    Provide either `depot_download_token` or `depot_download_activation_code`, not both.

**Offline Depot Variables** (required when `depot_type` is `offline`):

- `depot_offline_hostname` - Hostname or IP address of the offline depot server.
    - Default: Read from IaC at `all_iac_vars.depot.hostname`.
- `depot_offline_port` - Port number of the offline depot server.
    - Default: Read from IaC at `all_iac_vars.depot.port` (defaults to 443).
- `depot_offline_username` - Username for authenticating with the offline depot server.
    - Default: Read from IaC at `all_iac_vars.depot.username`.
- `depot_offline_password` - Password for authenticating with the offline depot server.
    - Default: Read from IaC at `all_iac_vars.depot.password`.
- `depot_offline_ssl_thumbprint` - SSL thumbprint of the offline depot server certificate (optional).
    - Default: Read from IaC at `all_iac_vars.depot.ssl_thumbprint`.
    - If not provided, the role automatically retrieves the SSL certificate fingerprint from the depot server using the `broadcom.vcf.util.ssl_fingerprint` role.

Additional inputs are drawn from your IaC structure, e.g. `all_iac_vars`:

- `all_iac_vars.vcf_installer.hostname`
- `all_iac_vars.vcf_installer.username`
- `all_iac_vars.vcf_installer.password` or overrides

### Return Values

- `changed` - Boolean indicating if changes were made.
- `msg` - Status message.
- `depot` - Current depot configuration after the operation.

## Execution

### Enable Online Depot (`depot_state: present`, `depot_type: online`)

Example:

```yaml
- name: Enable Online Depot Configuration
  hosts: localhost
  roles:
    - role: broadcom.vcf.vcf_installer.depot
      vars:
        depot_state: present
        depot_type: online
        depot_download_token: "{{ depot_download_token }}"
```

Or using a activation code (9.1.x.x+):

```yaml
- name: Enable Online Depot Configuration
  hosts: localhost
  roles:
    - role: broadcom.vcf.vcf_installer.depot
      vars:
        depot_state: present
        depot_type: online
        depot_download_activation_code: "{{ depot_download_activation_code }}"
```

Behavior:

1. Query current depot configuration:
    - Uses `vcf_installer_depot_info` to retrieve depot status.
2. Compare with desired state:
    - If online depot is already configured, skips with `changed=false`.
    - If offline depot is configured, prepares to switch to online depot.
    - If no depot is configured, prepares to configure online depot.
3. Update configuration (if needed):
    - Calls `vcf_installer_depot` with `state: present` and `depot_type: online`.
    - Configures online depot via VCF Installer API.

#### Check Mode Behavior: `present` (Online)

- The module detects check mode and returns `changed: true` with a message like:

    ```shell
    Check Mode: Would configure online depot.
    ```

    ```shell
    Check Mode: Would change depot type from offline to online.
    ```

- No API calls are made to modify configuration.

### Enable Offline Depot (`depot_state: present`, `depot_type: offline`)

Example:

```yaml
- name: Enable Offline Depot Configuration
  hosts: localhost
  roles:
    - role: broadcom.vcf.vcf_installer.depot
      vars:
        depot_state: present
        depot_type: offline
        depot_offline_hostname: "depot.example.com"
        depot_offline_port: 443
        depot_offline_username: "vcf"
        depot_offline_password: "{{ depot_offline_password }}"
        depot_offline_ssl_thumbprint: "AB:CD:EF:..."
```

Behavior:

1. Query current depot configuration:
    - Uses `vcf_installer_depot_info` to retrieve depot status.
2. Compare with desired state:
    - If offline depot is already configured with same settings, skips with `changed=false`.
    - If online depot is configured, prepares to switch to offline depot.
    - If no depot is configured, prepares to configure offline depot.
3. Retrieve SSL certificate fingerprint (if not provided):
    - If `depot_offline_ssl_thumbprint` is not set, automatically retrieves the fingerprint from the depot server using the `broadcom.vcf.util.ssl_fingerprint` role.
4. Update configuration (if needed):
    - Calls `vcf_installer_depot` with `state: present` and `depot_type: offline`.
    - Configures offline depot via VCF Installer API.

#### Check Mode Behavior: `present` (Offline)

- The module detects check mode and returns `changed: true` with a message like:

    ```shell
    Check Mode: Would configure offline depot.
    ```

    ```shell
    Check Mode: Would change depot type from online to offline.
    ```

- No API calls are made to modify configuration.

### Disable Depot (`depot_state: absent`)

Example:

```yaml
- name: Disable Depot Configuration
  hosts: localhost
  roles:
    - role: broadcom.vcf.vcf_installer.depot
      vars:
        depot_state: absent
```

Behavior:

1. Query current depot configuration:
    - Uses `vcf_installer_depot_info` to retrieve depot status.
2. Check if depot exists:
    - If no depot is configured, skips with `changed=false`.
3. Remove configuration (if needed):
    - Calls `vcf_installer_depot` with `state: absent`.
    - Removes depot configuration via VCF Installer API.

#### Check Mode Behavior: `absent`

- The module detects check mode and returns `changed: true` with a message like:

    ```shell
    Check Mode: Would remove online depot configuration.
    ```

    ```shell
    Check Mode: Would remove offline depot configuration.
    ```

- No API calls are made to modify configuration.

This lets you see *which* depot would be removed and confirm the plan without performing the deletion.

## SDK / API Calls

The following VCF Installer endpoints are used by the supporting module utility (`plugins/module_utils/vcf_installer.py`):

For depot management:

- `GET /v1/depots` - Retrieves current depot configuration.
- `POST /v1/depots` - Creates depot configuration (online or offline).
- `DELETE /v1/depots` - Removes depot configuration.

## Ansible Components

- Module Utils:
    - `plugins/module_utils/vcf_installer.py`

- Modules:
    - `plugins/modules/vcf_installer_depot.py`
    - `plugins/modules/vcf_installer_depot_info.py`

- Roles:
    - `roles/vcf_installer/depot`
    - `roles/vcf_installer/depot_info`

- Playbooks:
    - `playbooks/enable_depot_installer.yml` (Uses `depot_state: present`)
    - `playbooks/disable_depot_installer.yml` (Uses `depot_state: absent`)
    - `playbooks/get_depot_info_installer.yml` (Informational only)

## Querying Information

The `vcf_installer_depot_info` module and `depot_info` role provide read-only access to depot configuration data.

### Module: `vcf_installer_depot_info`

This informational module retrieves depot configuration from VCF Installer without making any changes.

Parameters:

- `vcf_installer_hostname` - (Required) VCF Installer hostname or IP address.
- `vcf_installer_user` - (Required) VCF Installer username.
- `vcf_installer_password` - (Required) VCF Installer password.
- `include_sync_info` - (Optional) Include depot sync information. Default: true.

Return Values:

- `depot` - Dictionary containing depot configuration details.
    - `vmwareAccount` - Online depot account information (if configured).
    - `offlineAccount` - Offline depot account information (if configured).
    - `depotConfiguration` - Depot server configuration (hostname, port, type).
- `changed` - Always `false` (read-only operation).
- `msg` - Human-readable status message describing depot configuration state.

Example:

```yaml
- name: Get Depot Configuration
  broadcom.vcf.vcf_installer_depot_info:
    vcf_installer_hostname: "{{ all_iac_vars.vcf_installer.hostname }}"
    vcf_installer_user: "{{ all_iac_vars.vcf_installer.username }}"
    vcf_installer_password: "{{ vcf_installer_password | default(all_iac_vars.vcf_installer.password) }}"
  register: depot_info

- name: Display Depot Status
  ansible.builtin.debug:
    msg: "{{ depot_info.msg }}"
```

### Role: `depot_info`

This role wraps the `vcf_installer_depot_info` module to retrieve depot configuration and set it as facts.

Variables:

- No input variables required. Uses IaC settings from `all_iac_vars`.

Sets the following facts:

- `depot_info` - Complete depot configuration response.

Example:

```yaml
- name: Get IaC Settings
  ansible.builtin.include_role:
    name: broadcom.vcf.iac.get_settings

- name: Get Depot Configuration
  ansible.builtin.include_role:
    name: broadcom.vcf.vcf_installer.depot_info

- name: Display Depot Status
  ansible.builtin.debug:
    msg: "{{ depot_info.msg }}"
```

The role is commonly used when you need to:

- Verify depot connectivity before management domain deployment.
- Determine if online or offline depot is configured.
- Check depot status for troubleshooting or validation.
- Generate reports or audit logs of depot configuration.

API Endpoint:

- `GET /v1/depots` - Retrieves the depot configuration and status.

## Usage Examples

### Example 1: Enable Online Depot Using Playbook

```bash
ansible-playbook playbooks/enable_depot_installer.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "depot_download_token=your-download-token"
```

Or using a activation code (9.1.x.x+):

```bash
ansible-playbook playbooks/enable_depot_installer.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "depot_download_activation_code=your-activation-code"
```

### Example 2: Enable Offline Depot Using Playbook

```bash
ansible-playbook playbooks/enable_depot_installer.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "depot_offline_hostname=depot.example.com" \
  -e "depot_offline_port=443" \
  -e "depot_offline_username=vcf" \
  -e "depot_offline_password=password" \
  -e "depot_offline_ssl_thumbprint=AB:CD:EF:12:34:56:78:90:AB:CD:EF:12:34:56:78:90:AB:CD:EF:12"
```

### Example 3: Disable Depot Configuration

```bash
ansible-playbook playbooks/disable_depot_installer.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

### Example 4: Validate Changes with Check Mode

```bash
ansible-playbook playbooks/enable_depot_installer.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "depot_offline_hostname=depot.example.com" \
  -e "depot_offline_port=443" \
  -e "depot_offline_username=admin" \
  -e "depot_offline_password=password" \
  -e "depot_offline_ssl_thumbprint=AB:CD:EF:12:34:56:78:90:AB:CD:EF:12:34:56:78:90:AB:CD:EF:12" \
  --check
```

## Workflow Sequence

### Enable Depot Workflow

1. `playbooks/enable_depot_installer.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `vcf_installer/depot` role executes with `depot_state: present`:
   - Gets current depot configuration
   - Determines depot type from IaC or variables
   - Validates required parameters
   - Configures depot (online or offline)
   - Returns success message

### Disable Depot Workflow

1. `playbooks/disable_depot_installer.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `vcf_installer/depot` role executes with `depot_state: absent`:
   - Gets current depot configuration
   - Removes depot configuration
   - Returns success message
