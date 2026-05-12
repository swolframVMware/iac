# Day 2: Manage Certificate Authority Settings

## Overview

This workflow manages certificate authority configuration in VMware Cloud Foundation using the
`broadcom.vcf.sddc_manager.certificate_authority` role and the `sddc_manager_certificate_authority` module.

Supported operations:

- Configure certificate authority (OpenSSL or Microsoft CA).

The role is state-driven via `certificate_authority_state`:

- `update` – configure certificate authority (OpenSSL or Microsoft CA based on `certificate_authority_type`).

!!! info "About Certificate Authority Configuration"
    VMware Cloud Foundation supports two types of certificate authorities:
    
    - **OpenSSL Certificate Authority**: Self-signed certificate authority managed by SDDC Manager.
        - Certificates are signed by the internal OpenSSL CA.
    
    - **Microsoft Certificate Authority**: Enterprise certificate authority.
        - Integrates with Active Directory Certificate Services.
        - Provides certificates from a trusted enterprise CA.
    
    Both certificate authority configurations coexist in SDDC Manager. When you configure a certificate authority, you specify which type (OpenSSL or Microsoft) to update. The API returns both configurations, and you work with the specific one you need.

## Prerequisites

Before you begin, make sure:

1. [Deployment prerequisites](../day1/deployment-prerequisites.md) are met.
2. Management domain is deployed and SDDC Manager is operational.
3. SDDC Manager is reachable and you have administrative credentials.
4. Infrastructure‑as‑Code (IaC) data is defined under `./infra-as-code/`.
5. You can authenticate to SDDC Manager with sufficient privileges to:
   - Query and manage certificate authority configuration.
6. For Microsoft CA:
   - Microsoft Certificate Authority server is accessible from SDDC Manager.
   - Valid credentials for the CA server.
   - Certificate template is configured on the Microsoft CA.

## Configuration Requirements

The following configuration must be provided under `./infra-as-code/`:

- SDDC Manager configuration:
    - SDDC Manager hostname and credentials.
    - Certificate authority configuration (type, organizational details, or CA server details).

- Certificate authority configuration (for `openssl`):
    - Common name, organization, organization unit, locality, state, and country.

- Certificate authority configuration (for `microsoft`):
    - FQDN of the Microsoft Certificate Authority.
    - Username and password to authenticate with Microsoft Certificate Authority.
    - Certificate template name on the Microsoft Certificate Authority.

!!! tip "Password Management"
    Passwords can be provided in multiple ways:
    
    - **In IaC configuration files** (for lab/development environments)
    - **As extra variables** at runtime: `-e "certificate_authority_microsoft_password=secret"`
    - **From Ansible Vault** for production: `certificate_authority_microsoft_password: "{{ vault_certificate_authority_microsoft_password }}"`
    
    If not provided in IaC, the password must be supplied via extra vars or the module will fail validation.
    See [Manage Vaulted Passwords](../utilities/ansible-vault.md) for the full
    vaulted file workflow.

The role reads certificate authority configuration from IaC structure at `all_iac_vars.certificate_authority`:

OpenSSL:

```yaml
certificate_authority:
  type: openssl
  openssl:
    common_name: "sddc-manager.example.com"
    organization: "Example"
    organization_unit: "Platform Engineering"
    locality: "San Francisco"
    state: "California"
    country: "US"
```

Microsoft Certificate Authority:

```yaml
certificate_authority:
  type: microsoft
  microsoft:
    server: "ca.example.com"
    username: "DOMAIN\\ca_admin"
    password: "ca_password"  # Can also be provided via extra vars or Vault
    template_name: "VMware"
```

Variables can be manually specified to override IaC configuration.

## Role Interface

Role: `broadcom.vcf.sddc_manager.certificate_authority`

### Variables

Key variables:

- `certificate_authority_state` - Desired state of certificate authority configuration.
    - `update` (default): configure certificate authority.
- `certificate_authority_type` - Type of certificate authority to configure (required when `certificate_authority_state` is `update`).
    - `openssl`: configure OpenSSL certificate authority.
    - `microsoft`: configure Microsoft Certificate Authority.
    - Default: Read from IaC at `all_iac_vars.certificate_authority.type`.

**OpenSSL Certificate Authority Variables** (required when `certificate_authority_type` is `openssl`):

- `certificate_authority_openssl_common_name` - Common name for the OpenSSL certificate authority.
    - Default: Read from IaC at `all_iac_vars.certificate_authority.openssl.common_name`.
- `certificate_authority_openssl_organization` - Organization for the OpenSSL certificate authority.
    - Default: Read from IaC at `all_iac_vars.certificate_authority.openssl.organization`.
- `certificate_authority_openssl_organization_unit` - Organization unit for the OpenSSL certificate authority.
    - Default: Read from IaC at `all_iac_vars.certificate_authority.openssl.organization_unit`.
- `certificate_authority_openssl_locality` - Locality for the OpenSSL certificate authority.
    - Default: Read from IaC at `all_iac_vars.certificate_authority.openssl.locality`.
- `certificate_authority_openssl_state` - State/Province for the OpenSSL certificate authority.
    - Default: Read from IaC at `all_iac_vars.certificate_authority.openssl.state`.
- `certificate_authority_openssl_country` - Country code for the OpenSSL certificate authority.
    - Default: Read from IaC at `all_iac_vars.certificate_authority.openssl.country`.

**Microsoft Certificate Authority Variables** (required when `certificate_authority_type` is `microsoft`):

- `certificate_authority_microsoft_server` - FQDN of the Microsoft Certificate Authority.
    - Automatically transformed to the full URL format (https://<server>/certsrv) for the API.
    - Default: Read from IaC at `all_iac_vars.certificate_authority.microsoft.server`.
- `certificate_authority_microsoft_username` - Username to authenticate to the Microsoft Certificate Authority.
    - Default: Read from IaC at `all_iac_vars.certificate_authority.microsoft.username`.
- `certificate_authority_microsoft_password` - Password to authenticate to the Microsoft Certificate Authority.
    - Default: Read from IaC at `all_iac_vars.certificate_authority.microsoft.password`.
- `certificate_authority_microsoft_template_name` - Certificate template name for the Microsoft Certificate Authority.
    - Default: Read from IaC at `all_iac_vars.certificate_authority.microsoft.template_name`.

Additional inputs are drawn from your IaC structure, e.g. `all_iac_vars`:

- `all_iac_vars.sddc_manager.hostname`
- `all_iac_vars.vsphere.vcenter.sso.username`
- `all_iac_vars.vsphere.vcenter.sso.password` or overrides

### Return Values

- `changed` - Boolean indicating if changes were made.
- `msg` - Status message.
- `certificate_authorities` - Updated certificate authority configuration.

## Execution

### Configure OpenSSL Certificate Authority (`certificate_authority_state: update`, `certificate_authority_type: openssl`)

Example:

```yaml
- name: Configure OpenSSL Certificate Authority
  hosts: localhost
  roles:
    - role: broadcom.vcf.sddc_manager.certificate_authority
      vars:
        certificate_authority_state: update
        certificate_authority_type: openssl
        certificate_authority_openssl_common_name: "sddc-manager.example.com"
        certificate_authority_openssl_organization: "Example"
        certificate_authority_openssl_organization_unit: "Platform Engineering"
        certificate_authority_openssl_locality: "San Francisco"
        certificate_authority_openssl_state: "California"
        certificate_authority_openssl_country: "US"
```

Behavior:

1. Query current certificate authority configuration:
    - Uses `sddc_manager_certificate_authority_info` to retrieve CA status.
2. Compare with desired state:
    - If OpenSSL CA is already configured with same settings, skips with `changed=false`.
    - If Microsoft CA is configured, prepares to switch to OpenSSL CA.
    - If no CA is configured, prepares to configure OpenSSL CA.
3. Update configuration (if needed):
    - Calls `sddc_manager_certificate_authority` with `state: update` and `ca_type: OpenSSL`.
    - Configures OpenSSL CA via SDDC Manager API.

#### Check Mode Behavior: `update` (OpenSSL)

- The module detects check mode and returns `changed: true` with a message like:

    ```shell
    Check Mode: Would configure OpenSSL certificate authority.
    ```

    ```shell
    Check Mode: Would update OpenSSL certificate authority configuration.
    ```

- No API calls are made to modify configuration.

### Configure Microsoft Certificate Authority (`certificate_authority_state: update`, `certificate_authority_type: microsoft`)

Example:

```yaml
- name: Configure Microsoft Certificate Authority
  hosts: localhost
  roles:
    - role: broadcom.vcf.sddc_manager.certificate_authority
      vars:
        certificate_authority_state: update
        certificate_authority_type: microsoft
        certificate_authority_microsoft_server: "ca.example.com"
        certificate_authority_microsoft_username: "DOMAIN\\ca_admin"
        certificate_authority_microsoft_password: "{{ certificate_authority_microsoft_password }}"
        certificate_authority_microsoft_template_name: "VMware"
```

Behavior:

1. Query current certificate authority configuration:
    - Uses `sddc_manager_certificate_authority_info` to retrieve CA status.
2. Compare with desired state:
    - If Microsoft CA is already configured with same settings, skips with `changed=false`.
    - If OpenSSL CA is configured, prepares to switch to Microsoft CA.
    - If no CA is configured, prepares to configure Microsoft CA.
3. Update configuration (if needed):
    - Calls `sddc_manager_certificate_authority` with `state: update` and `ca_type: Microsoft`.
    - Configures Microsoft CA via SDDC Manager API.

#### Check Mode Behavior: `update` (Microsoft)

- The module detects check mode and returns `changed: true` with a message like:

    ```shell
    Check Mode: Would configure Microsoft certificate authority.
    ```

    ```shell
    Check Mode: Would update Microsoft certificate authority configuration.
    ```

- No API calls are made to modify configuration.

## SDK / API Calls

The following SDDC Manager endpoints are used by the supporting module utility (`plugins/module_utils/sddc_manager.py`):

For certificate authority management:

- `GET /v1/certificate-authorities` - Retrieves the certificate authority configuration.
- `PUT /v1/certificate-authorities` - Sets the certificate authority configuration (initial setup).
- `PATCH /v1/certificate-authorities` - Updates the certificate authority configuration.

## Ansible Components

- Module Utils:
    - `plugins/module_utils/sddc_manager.py`

- Modules:
    - `plugins/modules/sddc_manager_certificate_authority.py`
    - `plugins/modules/sddc_manager_certificate_authority_info.py`

- Roles:
    - `roles/sddc_manager/certificate_authority`
    - `roles/sddc_manager/certificate_authority_info`

- Playbooks:
    - `playbooks/update_certificate_authority.yml` (Uses `certificate_authority_state: update`)
    - `playbooks/get_certificate_authority_info.yml` (Informational only)

## Querying Information

The `sddc_manager_certificate_authority_info` module and `certificate_authority_info` role provide read-only access to certificate authority configuration data.

### Module: `sddc_manager_certificate_authority_info`

This informational module retrieves certificate authority configuration from SDDC Manager without making any changes.

Parameters:

- `sddc_manager_hostname` - (Required) SDDC Manager hostname or IP address.
- `sddc_manager_user` - (Required) SDDC Manager username.
- `sddc_manager_password` - (Required) SDDC Manager password.

Return Values:

- `certificate_authorities` - List of certificate authority configurations (both OpenSSL and Microsoft).
    - Each element has an `id` field indicating the CA type ("OpenSSL" or "Microsoft").
    - For OpenSSL: `commonName`, `organization`, `organizationUnit`, `locality`, `state`, `country`.
    - For Microsoft: `serverUrl`, `username`, `templateName`.
- `changed` - Always `false` (read-only operation).
- `msg` - List of human-readable status messages describing certificate authority configurations.

Example:

```yaml
- name: Get Certificate Authority Configuration
  broadcom.vcf.sddc_manager_certificate_authority_info:
    sddc_manager_hostname: "{{ all_iac_vars.sddc_manager.hostname }}"
    sddc_manager_user: "{{ all_iac_vars.vsphere.vcenter.sso.username }}"
    sddc_manager_password: "{{ vcenter_administrator_password | default(all_iac_vars.vsphere.vcenter.sso.password) }}"
  register: ca_info

- name: Display Certificate Authority Status
  ansible.builtin.debug:
    msg: "{{ ca_info.msg }}"
  # Output:
  # [
  #   "Microsoft CA: ca.example.com",
  #   "OpenSSL CA: sddc-manager.example.com"
  # ]
```

### Role: `certificate_authority_info`

This role wraps the `sddc_manager_certificate_authority_info` module to retrieve certificate authority configuration and set it as facts.

Variables:

- No input variables required. Uses IaC settings from `all_iac_vars`.

Sets the following facts:

- `certificate_authority_info` - Complete certificate authority configuration response.

Example:

```yaml
- name: Get IaC Settings
  ansible.builtin.include_role:
    name: broadcom.vcf.iac.get_settings

- name: Get Certificate Authority Configuration
  ansible.builtin.include_role:
    name: broadcom.vcf.sddc_manager.certificate_authority_info

- name: Display Certificate Authority Status
  ansible.builtin.debug:
    msg: "{{ certificate_authority_info.msg }}"
```

The role is commonly used when you need to:

- Verify certificate authority configuration before certificate operations.
- Determine if OpenSSL or Microsoft CA is configured.
- Check certificate authority status for troubleshooting or validation.
- Generate reports or audit logs of certificate authority configuration.

API Endpoint:

- `GET /v1/certificate-authorities` - Retrieves the certificate authority configuration and status.

## Usage Examples

### Example 1: Configure OpenSSL Certificate Authority Using Playbook

```bash
ansible-playbook playbooks/update_certificate_authority.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "certificate_authority_type=openssl" \
  -e "certificate_authority_openssl_common_name=sddc-manager.example.com" \
  -e "certificate_authority_openssl_organization=Example" \
  -e "certificate_authority_openssl_organization_unit=IT" \
  -e "certificate_authority_openssl_locality=San Francisco" \
  -e "certificate_authority_openssl_state=California" \
  -e "certificate_authority_openssl_country=US"
```

### Example 2: Configure Microsoft Certificate Authority Using Playbook

```bash
ansible-playbook playbooks/update_certificate_authority.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "certificate_authority_type=microsoft" \
  -e "certificate_authority_microsoft_server=ca.example.com" \
  -e "certificate_authority_microsoft_username=DOMAIN\\ca_admin" \
  -e "certificate_authority_microsoft_password=password" \
  -e "certificate_authority_microsoft_template_name=VMware"
```

### Example 3: Query Certificate Authority Configuration

```bash
ansible-playbook playbooks/get_certificate_authority_info.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

### Example 4: Validate Changes with Check Mode

```bash
ansible-playbook playbooks/update_certificate_authority.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "certificate_authority_type=microsoft" \
  -e "certificate_authority_microsoft_server=ca.example.com" \
  -e "certificate_authority_microsoft_username=admin" \
  -e "certificate_authority_microsoft_password=password" \
  -e "certificate_authority_microsoft_template_name=VMware" \
  --check
```

## Workflow Sequence

### Configure Certificate Authority Workflow

1. `playbooks/update_certificate_authority.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `sddc_manager/certificate_authority` role executes with `certificate_authority_state: update`:
   - Gets current certificate authority configuration
   - Determines certificate authority type from IaC or variables
   - Validates required parameters
   - Configures certificate authority (OpenSSL or Microsoft)
   - Returns success message
