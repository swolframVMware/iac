# Day 1: Manage Proxy Settings for VCF Installer

## Overview

This workflow manages proxy configuration for a VCF Installer instance using the
`broadcom.vcf.vcf_installer.proxy` and `broadcom.vcf.vcf_installer.proxy_info` roles.

A proxy server is used by VCF Installer to route outbound network traffic through a
controlled gateway for security, monitoring, or compliance requirements.

Supported operations:

- Ensure proxy is configured and enabled.
- Ensure proxy is disabled.
- Retrieve proxy configuration information.

!!! warning "Limitation: Proxy Configuration Cannot Be Removed"
    The VCF Installer API does not support complete removal of proxy configuration. 
    You can only enable or disable the proxy; however, when disabled the configuration will persist but in a disabled state.

## Prerequisites

Before you begin, make sure:

1. [Deployment prerequisites](../day1/deployment-prerequisites.md) are met.
2. VCF Installer is deployed and operational.
3. VCF Installer is reachable and you have administrative credentials.
4. Infrastructure‑as‑Code (IaC) data is defined under `./infra-as-code/`.
5. You can authenticate to VCF Installer with sufficient privileges to:
   - Query and manage proxy configuration.

## Configuration Requirements

The following configuration must be provided under `./infra-as-code/`:

- VCF Installer configuration:
    - VCF Installer hostname and admin credentials.

For proxy configuration (when using the `proxy` role):

The role automatically reads proxy configuration from the IaC structure at `all_iac_vars.proxy`:

```yaml
proxy:
  host: "proxy.example.com"
  port: 3128
  protocol: https
  authenticate: true
  username: "vcf"
  password: "{{ vault_proxy_password }}"
```

**Note:** 

- The `proxy_state` variable is passed by the playbook.
  - Use `enable_proxy.yml` playbook to enable the proxy configuration.
  - Use `disable_proxy.yml` playbook to disable the proxy configuration.

Variables can be manually specified to override IaC configuration.

No additional configuration is required for proxy information retrieval (when using the `proxy_info` role).

## Role Interface

### Role: `broadcom.vcf.vcf_installer.proxy`

This role manages proxy configuration in VCF Installer, allowing you to enable or disable the proxy configuration.

**IaC Integration:** By default, the role reads configuration from `all_iac_vars.proxy`. The `proxy_state` variable must be passed by the playbook to determine whether to enable or disable the proxy.

#### Variables

Key variables:

- `proxy_state` - (Required) Desired state of proxy.
    - `enabled`: Apply the settings and enable the proxy configuration.
    - `disabled`: Disable the proxy configuration while retaining the settings
    - Must be passed by playbook (use `enable_proxy.yml` or `disable_proxy.yml`).

**Proxy Variables** (optional overrides, automatically read from IaC when not specified):

- `proxy_host` - IP address or FQDN of proxy server.
  - Default: Read from IaC at `all_iac_vars.proxy.host`.
- `proxy_port` - Port number of the proxy server.
  - Default: Read from IaC at `all_iac_vars.proxy.port` (defaults to 3128).
- `proxy_transfer_protocol` - The proxy transfer protocol (`http` or `https`).
  - Default: Read from IaC at `all_iac_vars.proxy.protocol` (defaults to `http`).
- `proxy_is_authenticated` - If proxy authentication is required.
  - Default: Read from IaC at `all_iac_vars.proxy.authenticate` (defaults to `false`).
- `proxy_username` - Username to authenticate with the proxy server (required if `proxy_is_authenticated` is `true`).
  - Default: Read from IaC at `all_iac_vars.proxy.username`.
- `proxy_password` - Password to authenticate with the proxy server (required if `proxy_is_authenticated` is `true`).
  - Default: Read from IaC at `all_iac_vars.proxy.password`.

#### Return Values

- `changed` - Boolean indicating if changes were made.
- `msg` - Status message about the operation.
- `proxy` - Current proxy configuration after the operation.

Additional inputs are drawn from your IaC structure, e.g. `all_iac_vars`:

- `all_iac_vars.vcf_installer.hostname`
- `all_iac_vars.vcf_installer.username`
- `all_iac_vars.vcf_installer.password` or overrides

### Role: `broadcom.vcf.vcf_installer.proxy_info`

This informational role retrieves current proxy configuration and status.

#### Variables

No input variables are required. The role automatically retrieves proxy configuration from VCF Installer.

Additional inputs are drawn from your IaC structure, e.g. `all_iac_vars`:

- `all_iac_vars.vcf_installer.hostname`
- `all_iac_vars.vcf_installer.username`
- `all_iac_vars.vcf_installer.password` or overrides

#### Return Values

- `changed` - Always `false` (read-only operation).
- `proxy` - Dictionary containing proxy configuration details:
    - `isConfigured` - Boolean indicating if proxy is configured.
    - `isEnabled` - Boolean indicating if the proxy is enabled.
    - `isAuthenticated` - Boolean indicating if proxy authentication is required.
    - `host` - IP address or FQDN of proxy server.
    - `port` - Port number of proxy server.
    - `transferProtocol` - The proxy transfer protocol (HTTP or HTTPS).
    - `username` - Username to authenticate with the proxy server, if proxy authentication is required.
- `msg` - A status message describing the proxy configuration state.

## Execution

### Enable Proxy (`proxy_state: enabled`)

Example:

```yaml
- name: Enable Proxy Configuration
  hosts: localhost
  roles:
    - role: broadcom.vcf.vcf_installer.proxy
      vars:
        proxy_state: enabled
```

Behavior:

1. Reads proxy configuration from IaC (`all_iac_vars.proxy`).
2. Queries current proxy configuration from VCF Installer.
3. If proxy is already enabled with same settings, skips with `changed=false`.
4. If configuration differs or proxy is disabled, updates the configuration.
5. Enables the proxy with the configured settings via VCF Installer API.

#### Check Mode Behavior: `enabled`

- The module detects check mode and returns a message without making changes:

    ```
    "Check Mode: Would enable the proxy configuration."
    ```

- No API calls are made to modify configuration.

### Disable Proxy (`proxy_state: disabled`)

Example:

```yaml
- name: Disable Proxy Configuration
  hosts: localhost
  roles:
    - role: broadcom.vcf.vcf_installer.proxy
      vars:
        proxy_state: disabled
```

Behavior:

1. Queries current proxy configuration from VCF Installer.
2. If proxy is already disabled, skips with `changed=false`.
3. If proxy is enabled, disables it via VCF Installer API.
4. Configuration settings remain stored in VCF Installer.

#### Check Mode Behavior: `disabled`

- The module detects check mode and returns a message without making changes:

    ```
    "Check Mode: Would disable the proxy configuration."
    ```

- No API calls are made to modify configuration.

#### Output Messages

The module provides clear, contextual messages based on the proxy configuration:

##### Proxy Enabled Messages

When proxy is configured and enabled:

- **Enabled Without Authentication**:

    ```
    "HTTP Proxy Status: Enabled (proxy.example.com:3128)"
    ```

- **Enabled With Authentication**:

    ```
    "HTTPS Proxy Status: Enabled (proxy.example.com:3128 with authentication)"
    ```

##### Proxy Disabled Messages

When proxy is configured but disabled:

- **Disabled Without Authentication**:

    ```
    "HTTP Proxy Status: Disabled (proxy.example.com:3128)"
    ```

- **Disabled With Authentication**:

    ```
    "HTTPS Proxy Status: Disabled (proxy.example.com:3128 with authentication)"
    ```

##### No Configuration

When no proxy is configured:

- **Not Configured**:

    ```
    "Proxy Status: Not Configured"
    ```


## SDK / API Calls

The following VCF Installer endpoints are used by the supporting module utility (`plugins/module_utils/vcf_installer.py`):

For proxy management:

- `GET /v1/system/proxy-configuration` - Retrieves current proxy configuration.
- `PATCH /v1/system/proxy-configuration` - Updates proxy configuration.

## Ansible Components

- Module Utils:
    - `plugins/module_utils/vcf_installer.py`

- Modules:
    - `plugins/modules/vcf_installer_proxy.py`
    - `plugins/modules/vcf_installer_proxy_info.py`

- Roles:
    - `roles/vcf_installer/proxy`
    - `roles/vcf_installer/proxy_info`

- Playbooks:
    - `playbooks/enable_proxy_installer.yml` (Uses `proxy_state: enabled`)
    - `playbooks/disable_proxy_installer.yml` (Uses `proxy_state: disabled`)
    - `playbooks/get_proxy_info_installer.yml` (Informational only)

## Querying Information

The `vcf_installer_proxy_info` module and `proxy_info` role provide read-only access to proxy configuration data.

### Module: `vcf_installer_proxy_info`

This informational module retrieves proxy configuration from VCF Installer without making any changes.

Parameters:

- `vcf_installer_hostname` - (Required) VCF Installer hostname or IP address.
- `vcf_installer_user` - (Required) VCF Installer username.
- `vcf_installer_password` - (Required) VCF Installer password.

Return Values:

- `changed` - Always `false` (read-only operation).
- `proxy` - Dictionary containing proxy configuration details:
    - `isConfigured` - Boolean indicating if proxy is configured.
    - `isEnabled` - Boolean indicating if the proxy is enabled.
    - `isAuthenticated` - Boolean indicating if proxy authentication is required.
    - `host` - IP address or FQDN of proxy server.
    - `port` - Port number of proxy server.
    - `transferProtocol` - The proxy transfer protocol (HTTP or HTTPS).
    - `username` - Username to authenticate with the proxy server, if proxy authentication is required.
- `msg` - A status message describing the proxy configuration state.

Example:

```yaml
- name: Get Proxy Configuration
  broadcom.vcf.vcf_installer_proxy_info:
    vcf_installer_hostname: "{{ all_iac_vars.vcf_installer.hostname }}"
    vcf_installer_user: "{{ all_iac_vars.vcf_installer.username }}"
    vcf_installer_password: "{{ vcf_installer_password | default(all_iac_vars.vcf_installer.password) }}"
  register: proxy_info

- name: Display Proxy Status
  ansible.builtin.debug:
    msg: "{{ proxy_info.msg }}"
```

### Role: `proxy_info`

This role wraps the `vcf_installer_proxy_info` module to retrieve proxy configuration and display the status.

Variables:

- No input variables required. Uses IaC settings from `all_iac_vars`.

Sets the following facts:

- `proxy_info` - Complete proxy configuration response.

Example:

```yaml
- name: Get IaC Settings
  ansible.builtin.include_role:
    name: broadcom.vcf.iac.get_settings

- name: Get Proxy Information
  ansible.builtin.include_role:
    name: broadcom.vcf.vcf_installer.proxy_info

- name: Display Proxy Status
  ansible.builtin.debug:
    msg: "{{ proxy_info.msg }}"
```

The role is commonly used when you need to:

- Verify proxy configuration before or after configuration changes.
- Check proxy settings for troubleshooting or validation.
- Generate reports or audit logs of proxy configuration.

API Endpoint:

- `GET /v1/system/proxy-configuration` - Retrieves the current proxy configuration.

## Usage Examples

### Example 1: Enable Proxy Using Playbook

```bash
ansible-playbook playbooks/enable_proxy_installer.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

### Example 2: Disable Proxy Using Playbook

```bash
ansible-playbook playbooks/disable_proxy_installer.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

### Example 3: Validate Changes with Check Mode

```bash
ansible-playbook playbooks/enable_proxy_installer.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  --check
```

### Example 4: Query Proxy Information

```bash
ansible-playbook playbooks/get_proxy_info_installer.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

## Workflow Sequence

### Enable Proxy Workflow

1. `playbooks/enable_proxy_installer.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `vcf_installer/proxy` role executes with `proxy_state: enabled`:
   - Reads proxy configuration from IaC
   - Queries current proxy configuration
   - Compares with desired state
   - Updates proxy configuration if needed
   - Enables proxy and returns success message
   - Queries proxy configuration and displays status message

### Disable Proxy Workflow

1. `playbooks/disable_proxy_installer.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `vcf_installer/proxy` role executes with `proxy_state: disabled`:
   - Queries current proxy configuration
   - Compares with desired state
   - Disables proxy if currently enabled
   - Returns success message (configuration persists)
   - Queries proxy configuration and displays status message
