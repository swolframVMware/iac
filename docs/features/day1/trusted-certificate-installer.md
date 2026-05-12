# Day 1: Manage Trusted Certificates for VCF Installer

## Overview

This workflow adds trusted certificates to the VCF Installer appliance's trust store
using the `broadcom.vcf.vcf_installer.trusted_certificate` role and the
`vcf_installer_trusted_certificate` module.

Supported operations:

- Add a trusted certificate to the VCF Installer trust store.
- Query all trusted certificates in the VCF Installer trust store.

!!! info "About Trusted Certificates for VCF Installer"
    VCF Installer requires trusted certificates in its trust store to establish secure
    outbound connections, for example to an offline depot.

    - Certificates are identified in the trust store by an auto-generated alias derived
      from the certificate fingerprint. The alias does not need to be known in advance.
    - Certificate matching is done by comparing the PEM content, normalized to strip
      subject and issuer header lines and whitespace differences.
    - The `util.trusted_ssl_certificate` role retrieves the certificate directly from a
      target endpoint over SSL so you do not need to manage PEM files manually.

!!! warning "Certificate Removal Not Supported"
    Removal of trusted certificates is not supported by the VCF Installer API when the
    appliance is in installer mode. There is no remove or absent operation for this workflow.

## Prerequisites

Before you begin, make sure:

1. [Deployment prerequisites](../day1/deployment-prerequisites.md) are met.
2. VCF Installer is deployed and operational.
3. VCF Installer is reachable and you have administrative credentials.
4. Infrastructure‑as‑Code (IaC) data is defined under `./infra-as-code/`.
5. The target endpoint (e.g. offline depot server) is reachable on port 443 (or the
   specified port) from the Ansible control node.
6. You can authenticate to VCF Installer with sufficient privileges to:
   - Query trusted certificates.
   - Add trusted certificates.

## Configuration Requirements

The following configuration must be provided under `./infra-as-code/`:

- VCF Installer configuration:
    - VCF Installer hostname and admin credentials.

The certificate is retrieved live from the target endpoint at runtime — no PEM file
needs to be pre-staged. The `util.trusted_ssl_certificate` role handles retrieval using
OpenSSL.

## Role Interface

Role: `broadcom.vcf.vcf_installer.trusted_certificate`

### Variables

Key variables:

- `trusted_certificate` - (Required) The certificate in PEM format to add to the trust
  store. Typically sourced from `trusted_ssl_certificate_payload.certificate` set by the
  `broadcom.vcf.util.trusted_ssl_certificate` role.
- `trusted_certificate_usage_type` - (Optional) Certificate usage type.
    - Default: `TRUSTED_FOR_OUTBOUND`.

### Return Values

- `changed` - Boolean indicating if changes were made.
- `msg` - Status message.
- `trusted_certificate` - Updated list of trusted certificates in the trust store.

Additional inputs are drawn from your IaC structure, e.g. `all_iac_vars`:

- `all_iac_vars.vcf_installer.hostname`
- `all_iac_vars.vcf_installer.username`
- `all_iac_vars.vcf_installer.password` or overrides

## Execution

### Add Trusted Certificate (`trusted_certificate_state: present`)

Example:

```yaml
- name: Add Trusted Certificate to VCF Installer Trust Store
  hosts: localhost
  tasks:
    - name: Get IaC Settings
      ansible.builtin.include_role:
        name: broadcom.vcf.iac.get_settings

    - name: Retrieve SSL Certificate Payload from Target Host
      ansible.builtin.include_role:
        name: broadcom.vcf.util.trusted_ssl_certificate

    - name: Add Trusted Certificate
      ansible.builtin.include_role:
        name: broadcom.vcf.vcf_installer.trusted_certificate
      vars:
        trusted_certificate: "{{ trusted_ssl_certificate_payload.certificate }}"
        trusted_certificate_usage_type: "{{ trusted_ssl_certificate_payload.certificateUsageType }}"
```

Behavior:

1. Retrieve SSL certificate payload from target host:
    - Uses `util.trusted_ssl_certificate` to connect to `target_host:target_port` over
      SSL using OpenSSL.
    - Builds `trusted_ssl_certificate_payload` containing the PEM certificate and usage
      type.
2. Check if certificate already exists in the trust store:
    - Uses `vcf_installer_trusted_certificate_info` with the retrieved PEM to search the
      trust store.
    - Extracts and normalises the PEM block (stripping subject/issuer headers) before
      comparing.
    - Sets `trust_store_check.found` — does not fail if no match is found.
3. Add certificate (if not already present):
    - If `trust_store_check.found` is `false`, calls the `trusted_certificate` role.
    - Posts the certificate and usage type to the VCF Installer API.
    - Returns the updated trust store list.
4. Display result:
    - If already present: displays the pre-check message.
    - If added: displays the add confirmation message.

#### Check Mode Behavior: `present`

When run with `--check`, the module returns a message without making changes:

```shell
Check Mode: Would add the trusted certificate to the trust store.
```

- No API calls are made to modify the trust store.

## SDK / API Calls

The following VCF Installer endpoints are used by the supporting module utility
(`plugins/module_utils/vcf_installer.py`):

- `GET /v1/sddc-manager/trusted-certificates` - Retrieves all trusted certificates from
  the trust store.
- `POST /v1/sddc-manager/trusted-certificates` - Adds a trusted certificate to the trust
  store.

## Ansible Components

- Module Utils:
    - `plugins/module_utils/vcf_installer.py`

- Modules:
    - `plugins/modules/vcf_installer_trusted_certificate.py`
    - `plugins/modules/vcf_installer_trusted_certificate_info.py`

- Roles:
    - `roles/vcf_installer/trusted_certificate`
    - `roles/vcf_installer/trusted_certificate_info`
    - `roles/util/trusted_ssl_certificate`

- Playbooks:
    - `playbooks/add_trusted_certificate_installer.yml`
    - `playbooks/get_trusted_certificate_info_installer.yml` (Informational only)

## Querying Information

The `vcf_installer_trusted_certificate_info` module and `trusted_certificate_info` role
provide read-only access to the trust store.

### Module: `vcf_installer_trusted_certificate_info`

This informational module retrieves trusted certificates from VCF Installer without
making any changes.

Parameters:

- `vcf_installer_hostname` - (Required) VCF Installer hostname or IP address.
- `vcf_installer_user` - (Required) VCF Installer username.
- `vcf_installer_password` - (Required) VCF Installer password.
- `certificate` - (Optional) A PEM certificate string to search for in the trust store.
  When provided, the matching entry is returned as `trusted_certificate` (singular) and
  `found` is set accordingly. No error is raised if no match is found.

Return Values:

- `found` - Boolean indicating whether a matching certificate was found.
- `trusted_certificates` - Full list of trusted certificate objects in the trust store.
- `trusted_certificate` - The single matching certificate entry when `certificate` is
  provided and `found` is `true`.
    - `alias` - Auto-generated alias (certificate fingerprint).
    - `certificate` - The PEM certificate string as stored in the trust store.
- `changed` - Always `false` (read-only operation).
- `msg` - Human-readable status message.

Example: 

Retrieve all certificates.

```yaml
- name: Get All Trusted Certificates
  broadcom.vcf.vcf_installer_trusted_certificate_info:
    vcf_installer_hostname: "{{ all_iac_vars.vcf_installer.hostname }}"
    vcf_installer_user: "{{ all_iac_vars.vcf_installer.username }}"
    vcf_installer_password: "{{ vcf_installer_password | default(all_iac_vars.vcf_installer.password) }}"
  register: trusted_certs

- name: Display Status Message
  ansible.builtin.debug:
    msg: "{{ trusted_certs.msg }}"
```

Example:

Check whether a specific certificate is already trusted.

```yaml
- name: Check If Certificate Exists in Trust Store
  broadcom.vcf.vcf_installer_trusted_certificate_info:
    vcf_installer_hostname: "{{ all_iac_vars.vcf_installer.hostname }}"
    vcf_installer_user: "{{ all_iac_vars.vcf_installer.username }}"
    vcf_installer_password: "{{ vcf_installer_password | default(all_iac_vars.vcf_installer.password) }}"
    certificate: "{{ trusted_ssl_certificate_payload.certificate }}"
  register: trust_store_check

- name: Display Result
  ansible.builtin.debug:
    msg: "{{ trust_store_check.msg }}"
```

### Role: `trusted_certificate_info`

This role wraps the `vcf_installer_trusted_certificate_info` module to retrieve trusted
certificates from the trust store.

Variables:

- `trusted_certificate` - (Optional) A PEM certificate string to search for. When
  provided the matching entry is returned in `trusted_certificate_info.trusted_certificate`
  and `trusted_certificate_info.found` reflects whether a match was found.

Example:

```yaml
- name: Get IaC Settings
  ansible.builtin.include_role:
    name: broadcom.vcf.iac.get_settings

- name: Get Trusted Certificate Information
  ansible.builtin.include_role:
    name: broadcom.vcf.vcf_installer.trusted_certificate_info

- name: Display Status Message
  ansible.builtin.debug:
    msg: "{{ trusted_certificate_info.msg }}"
```

The role is commonly used when you need to:

- Verify a certificate is trusted before deployment.
- Audit the current trust store contents.
- Pre-check whether a certificate needs to be added.

API Endpoint:

- `GET /v1/sddc-manager/trusted-certificates` - Retrieves all trusted certificates.

## Usage Examples

### Example 1: Add Trusted Certificate Using Playbook

```bash
ansible-playbook playbooks/add_trusted_certificate_installer.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "target_host=depot.example.com"
```

### Example 2: Add Certificate on a Non-Standard Port

```bash
ansible-playbook playbooks/add_trusted_certificate_installer.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "target_host=depot.example.com target_port=8443"
```

### Example 3: Validate Changes with Check Mode

```bash
ansible-playbook playbooks/add_trusted_certificate_installer.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "target_host=depot.example.com" \
  --check
```

### Example 4: Query All Trusted Certificates

```bash
ansible-playbook playbooks/get_trusted_certificate_info_installer.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

## Workflow Sequence

### Add Trusted Certificate Workflow

1. `playbooks/add_trusted_certificate_installer.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `util/trusted_ssl_certificate` role executes:
   - Validates `target_host` and `target_port`
   - Checks SSL port accessibility
   - Retrieves certificate subject, issuer, and PEM via OpenSSL
   - Sets `trusted_ssl_certificate_payload` fact
4. `vcf_installer_trusted_certificate_info` module checks the trust store:
   - Normalises and compares PEM content (strips subject/issuer headers)
   - Sets `trust_store_check.found` to `true` or `false`
5. If `trust_store_check.found` is `false`:
   - `vcf_installer/trusted_certificate` role adds the certificate
   - Posts certificate and usage type to VCF Installer API
   - Returns updated trust store list
6. Result is displayed

### Query Trusted Certificates Workflow

1. `playbooks/get_trusted_certificate_info_installer.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `vcf_installer/trusted_certificate_info` role executes:
   - Retrieves all trusted certificates from the trust store
   - Displays count and status message
