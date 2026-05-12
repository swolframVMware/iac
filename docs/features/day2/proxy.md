# Day 2: Manage Proxy Settings

## Overview

This workflow manages proxy configuration in VMware Cloud Foundation using the
`broadcom.vcf.sddc_manager.proxy` and `broadcom.vcf.sddc_manager.proxy_info` roles.

A proxy server is used by VMware Cloud Foundation to route outbound network traffic
through a controlled gateway for security, monitoring, or compliance requirements.

Supported operations:

- Ensure proxy is configured and enabled.
- Ensure proxy is disabled.
- Retrieve proxy configuration information.

!!! warning "Limitation: Proxy Configuration Cannot Be Removed"
    The VMware Cloud Foundation API does not support complete removal of proxy configuration. 
    You can only enable or disable the proxy; however, when disabled the configuration will persist but in a disabled state.

## Prerequisites

Before you begin, make sure:

1. [Deployment prerequisites](../day1/deployment-prerequisites.md) are met.
2. Management domain is deployed and SDDC Manager is operational.
3. SDDC Manager is reachable and you have administrative credentials.
4. Infrastructure‑as‑Code (IaC) data is defined under `./infra-as-code/`.
5. You can authenticate to SDDC Manager with sufficient privileges to:
   - Query and manage proxy configuration.

## Configuration Requirements

The following configuration must be provided under `./infra-as-code/`:

- SDDC Manager configuration:
    - SDDC Manager hostname and credentials.

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

### Role: `broadcom.vcf.sddc_manager.proxy`

This role manages proxy configuration in SDDC Manager, allowing you to enable or disable the proxy configuration.

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

- `all_iac_vars.sddc_manager.hostname`
- `all_iac_vars.vsphere.vcenter.sso.username`
- `all_iac_vars.vsphere.vcenter.sso.password` or overrides

### Role: `broadcom.vcf.sddc_manager.proxy_info`

This informational role retrieves current proxy configuration and status.

#### Variables

No input variables are required. The role automatically retrieves proxy configuration from SDDC Manager.

Additional inputs are drawn from your IaC structure, e.g. `all_iac_vars`:

- `all_iac_vars.sddc_manager.hostname`
- `all_iac_vars.vsphere.vcenter.sso.username`
- `all_iac_vars.vsphere.vcenter.sso.password` or overrides

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
    - role: broadcom.vcf.sddc_manager.proxy
      vars:
        proxy_state: enabled
```

Behavior:

1. Reads proxy configuration from IaC (`all_iac_vars.proxy`).
2. Queries current proxy configuration from SDDC Manager.
3. If proxy is already enabled with same settings, skips with `changed=false`.
4. If configuration differs or proxy is disabled, updates the configuration.
5. Enables the proxy with the configured settings via SDDC Manager API.

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
    - role: broadcom.vcf.sddc_manager.proxy
      vars:
        proxy_state: disabled
```

Behavior:

1. Queries current proxy configuration from SDDC Manager.
2. If proxy is already disabled, skips with `changed=false`.
3. If proxy is enabled, disables it via SDDC Manager API.
4. Configuration settings remain stored in SDDC Manager.

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

The following SDDC Manager endpoints are used by the supporting module utility (`plugins/module_utils/sddc_manager.py`):

For proxy management:

- `GET /v1/system/proxy-configuration` - Retrieves current proxy configuration.
- `PATCH /v1/system/proxy-configuration` - Updates proxy configuration.

## Ansible Components

- Module Utils:
    - `plugins/module_utils/sddc_manager.py`

- Modules:
    - `plugins/modules/sddc_manager_proxy.py`
    - `plugins/modules/sddc_manager_proxy_info.py`

- Roles:
    - `roles/sddc_manager/proxy`
    - `roles/sddc_manager/proxy_info`

- Playbooks:
    - `playbooks/enable_proxy.yml` (Uses `proxy_state: enabled`)
    - `playbooks/disable_proxy.yml` (Uses `proxy_state: disabled`)
    - `playbooks/get_proxy_info.yml` (Informational only)

## Querying Information

The `sddc_manager_proxy_info` module and `proxy_info` role provide read-only access to proxy configuration data.

### Module: `sddc_manager_proxy_info`

This informational module retrieves proxy configuration from SDDC Manager without making any changes.

Parameters:

- `sddc_manager_hostname` - (Required) SDDC Manager hostname or IP address.
- `sddc_manager_user` - (Required) SDDC Manager username.
- `sddc_manager_password` - (Required) SDDC Manager password.

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
  broadcom.vcf.sddc_manager_proxy_info:
    sddc_manager_hostname: "{{ all_iac_vars.sddc_manager.hostname }}"
    sddc_manager_user: "{{ all_iac_vars.vsphere.vcenter.sso.username }}"
    sddc_manager_password: "{{ vcenter_administrator_password | default(all_iac_vars.vsphere.vcenter.sso.password) }}"
  register: proxy_info

- name: Display Proxy Status
  ansible.builtin.debug:
    msg: "{{ proxy_info.msg }}"
```

### Role: `proxy_info`

This role wraps the `sddc_manager_proxy_info` module to retrieve proxy configuration and display the status.

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
    name: broadcom.vcf.sddc_manager.proxy_info

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
ansible-playbook playbooks/enable_proxy.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

### Example 2: Disable Proxy Using Playbook

```bash
ansible-playbook playbooks/disable_proxy.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

### Example 3: Validate Changes with Check Mode

```bash
ansible-playbook playbooks/enable_proxy.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  --check
```

### Example 4: Query Proxy Information

```bash
ansible-playbook playbooks/get_proxy_info.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

## Workflow Sequence

### Enable Proxy Workflow

1. `playbooks/enable_proxy.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `sddc_manager/proxy` role executes with `proxy_state: enabled`:
   - Reads proxy configuration from IaC
   - Queries current proxy configuration
   - Compares with desired state
   - Updates proxy configuration if needed
   - Enables proxy and returns success message
   - Queries proxy configuration and displays status message

### Disable Proxy Workflow

1. `playbooks/disable_proxy.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `sddc_manager/proxy` role executes with `proxy_state: disabled`:
   - Queries current proxy configuration
   - Compares with desired state
   - Disables proxy if currently enabled
   - Returns success message (configuration persists)
   - Queries proxy configuration and displays status message
