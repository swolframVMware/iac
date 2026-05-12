# Day 2: Manage Trusted Certificates

## Overview

This workflow manages trusted certificates in the SDDC Manager appliance's trust store
using the `broadcom.vcf.sddc_manager.trusted_certificate` role and the
`sddc_manager_trusted_certificate` module.

Supported operations:

- Add a trusted certificate to the SDDC Manager trust store.
- Remove a trusted certificate from the SDDC Manager trust store.
- Query all trusted certificates in the SDDC Manager trust store.

!!! info "About Trusted Certificates for SDDC Manager"
    SDDC Manager requires trusted certificates in its trust store to establish secure
    outbound connections, for example to an offline depot.

    - Certificates are identified in the trust store by an auto-generated alias derived
      from the certificate fingerprint. The alias does not need to be known in advance —
      the module resolves it automatically by comparing PEM content.
    - Certificate matching is done by comparing the PEM content, normalized to strip
      subject and issuer header lines and whitespace differences.
    - The `util.trusted_ssl_certificate` role retrieves the certificate directly from a
      target endpoint over SSL so you do not need to manage PEM files manually.

## Prerequisites

Before you begin, make sure:

1. [Deployment prerequisites](../day1/deployment-prerequisites.md) are met.
2. SDDC Manager is deployed and operational.
3. SDDC Manager is reachable and you have administrative credentials.
4. Infrastructure‑as‑Code (IaC) data is defined under `./infra-as-code/`.
5. The target endpoint (e.g. offline depot server) is reachable on port 443 (or the
   specified port) from the Ansible control node.
6. You can authenticate to SDDC Manager with sufficient privileges to:
   - Query trusted certificates.
   - Add and remove trusted certificates.

## Configuration Requirements

The following configuration must be provided under `./infra-as-code/`:

- SDDC Manager configuration:
    - SDDC Manager hostname and admin credentials.

The certificate is retrieved live from the target endpoint at runtime — no PEM file
needs to be pre-staged. The `util.trusted_ssl_certificate` role handles retrieval using
OpenSSL.

## Role Interface

Role: `broadcom.vcf.sddc_manager.trusted_certificate`

### Variables

Key variables:

- `trusted_certificate` - (Required) The certificate in PEM format to add to or remove
  from the trust store. Typically sourced from `trusted_ssl_certificate_payload.certificate`
  set by the `broadcom.vcf.util.trusted_ssl_certificate` role.
- `trusted_certificate_usage_type` - (Optional) Certificate usage type. Only used when
  `trusted_certificate_state=present`.
    - Default: `TRUSTED_FOR_OUTBOUND`.
- `trusted_certificate_state` - (Optional) Desired state of the certificate.
    - `present` (default) — ensures the certificate is in the trust store.
    - `absent` — ensures the certificate is removed from the trust store.

### Return Values

- `changed` - Boolean indicating if changes were made.
- `msg` - Status message.
- `trusted_certificate` - Updated list of trusted certificates in the trust store.

Additional inputs are drawn from your IaC structure, e.g. `all_iac_vars`:

- `all_iac_vars.sddc_manager.hostname`
- `all_iac_vars.vsphere.vcenter.sso.username`
- `all_iac_vars.vsphere.vcenter.sso.password` or overrides

## Execution

### Add Trusted Certificate (`trusted_certificate_state: present`)

Example:

```yaml
- name: Add Trusted Certificate to SDDC Manager Trust Store
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
        name: broadcom.vcf.sddc_manager.trusted_certificate
      vars:
        trusted_certificate: "{{ trusted_ssl_certificate_payload.certificate }}"
        trusted_certificate_usage_type: "{{ trusted_ssl_certificate_payload.certificateUsageType }}"
        trusted_certificate_state: present
```

Behavior:

1. Retrieve SSL certificate payload from target host:
    - Uses `util.trusted_ssl_certificate` to connect to `target_host:target_port` over
      SSL using OpenSSL.
    - Builds `trusted_ssl_certificate_payload` containing the PEM certificate and usage
      type.
2. Check if certificate already exists in the trust store:
    - Uses `sddc_manager_trusted_certificate_info` with the retrieved PEM to search the
      trust store.
    - Extracts and normalises the PEM block (stripping subject/issuer headers) before
      comparing.
    - Sets `trust_store_check.found` — does not fail if no match is found.
3. Add certificate (if not already present):
    - If `trust_store_check.found` is `false`, calls the `trusted_certificate` role.
    - Posts the certificate and usage type to the SDDC Manager API.
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

### Remove Trusted Certificate (`trusted_certificate_state: absent`)

Example:

```yaml
- name: Remove Trusted Certificate from SDDC Manager Trust Store
  hosts: localhost
  tasks:
    - name: Get IaC Settings
      ansible.builtin.include_role:
        name: broadcom.vcf.iac.get_settings

    - name: Retrieve SSL Certificate Payload from Target Host
      ansible.builtin.include_role:
        name: broadcom.vcf.util.trusted_ssl_certificate

    - name: Remove Trusted Certificate
      ansible.builtin.include_role:
        name: broadcom.vcf.sddc_manager.trusted_certificate
      vars:
        trusted_certificate: "{{ trusted_ssl_certificate_payload.certificate }}"
        trusted_certificate_state: absent
```

Behavior:

1. Retrieve SSL certificate payload from target host:
    - Uses `util.trusted_ssl_certificate` to connect to `target_host:target_port` over
      SSL using OpenSSL.
    - Builds `trusted_ssl_certificate_payload` containing the PEM certificate.
2. Check if certificate exists in the trust store:
    - Uses `sddc_manager_trusted_certificate_info` with the retrieved PEM to search the
      trust store.
    - Normalises and compares PEM content to resolve the certificate alias automatically.
    - Sets `trust_store_check.found` — does not fail if no match is found.
3. Remove certificate (if present):
    - If `trust_store_check.found` is `true`, calls the `trusted_certificate` role with
      `trusted_certificate_state: absent`.
    - Deletes the certificate from the SDDC Manager trust store by its resolved alias.
    - Returns the remaining trust store list.
4. Display result:
    - If not present: displays the pre-check not-found message.
    - If removed: displays the removal confirmation message.

#### Check Mode Behavior: `absent`

When run with `--check`, the module returns a message without making changes:

```shell
Check Mode: Would remove the trusted certificate from the trust store.
```

- No API calls are made to modify the trust store.

## SDK / API Calls

The following SDDC Manager endpoints are used by the supporting module utility
(`plugins/module_utils/sddc_manager.py`):

- `GET /v1/sddc-manager/trusted-certificates` - Retrieves all trusted certificates from
  the trust store.
- `POST /v1/sddc-manager/trusted-certificates` - Adds a trusted certificate to the trust
  store.
- `DELETE /v1/sddc-manager/trusted-certificates/{alias}` - Removes a trusted certificate
  from the trust store by alias.

## Ansible Components

- Module Utils:
    - `plugins/module_utils/sddc_manager.py`

- Modules:
    - `plugins/modules/sddc_manager_trusted_certificate.py`
    - `plugins/modules/sddc_manager_trusted_certificate_info.py`

- Roles:
    - `roles/sddc_manager/trusted_certificate`
    - `roles/sddc_manager/trusted_certificate_info`
    - `roles/util/trusted_ssl_certificate`

- Playbooks:
    - `playbooks/add_trusted_certificate.yml`
    - `playbooks/remove_trusted_certificate.yml`
    - `playbooks/get_trusted_certificate_info.yml`

## Querying Information

The `sddc_manager_trusted_certificate_info` module and `trusted_certificate_info` role
provide read-only access to the trust store.

### Module: `sddc_manager_trusted_certificate_info`

This informational module retrieves trusted certificates from SDDC Manager without
making any changes.

Parameters:

- `sddc_manager_hostname` - (Required) SDDC Manager hostname or IP address.
- `sddc_manager_user` - (Required) SDDC Manager username.
- `sddc_manager_password` - (Required) SDDC Manager password.
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
  broadcom.vcf.sddc_manager_trusted_certificate_info:
    sddc_manager_hostname: "{{ all_iac_vars.sddc_manager.hostname }}"
    sddc_manager_user: "{{ all_iac_vars.vsphere.vcenter.sso.username }}"
    sddc_manager_password: "{{ vcenter_administrator_password | default(all_iac_vars.vsphere.vcenter.sso.password) }}"
  register: trusted_certs

- name: Display Status Message
  ansible.builtin.debug:
    msg: "{{ trusted_certs.msg }}"
```

Example:

Check whether a specific certificate is already trusted.

```yaml
- name: Check If Certificate Exists in Trust Store
  broadcom.vcf.sddc_manager_trusted_certificate_info:
    sddc_manager_hostname: "{{ all_iac_vars.sddc_manager.hostname }}"
    sddc_manager_user: "{{ all_iac_vars.vsphere.vcenter.sso.username }}"
    sddc_manager_password: "{{ vcenter_administrator_password | default(all_iac_vars.vsphere.vcenter.sso.password) }}"
    certificate: "{{ trusted_ssl_certificate_payload.certificate }}"
  register: trust_store_check

- name: Display Result
  ansible.builtin.debug:
    msg: "{{ trust_store_check.msg }}"
```

### Role: `trusted_certificate_info`

This role wraps the `sddc_manager_trusted_certificate_info` module to retrieve trusted
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
    name: broadcom.vcf.sddc_manager.trusted_certificate_info

- name: Display Status Message
  ansible.builtin.debug:
    msg: "{{ trusted_certificate_info.msg }}"
```

The role is commonly used when you need to:

- Verify a certificate is trusted before deployment.
- Audit the current trust store contents.
- Pre-check whether a certificate needs to be added or removed.

API Endpoint:

- `GET /v1/sddc-manager/trusted-certificates` - Retrieves all trusted certificates.

## Usage Examples

### Example 1: Add Trusted Certificate Using Playbook

```bash
ansible-playbook playbooks/add_trusted_certificate.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "target_host=depot.example.com"
```

### Example 2: Add Certificate on a Non-Standard Port

```bash
ansible-playbook playbooks/add_trusted_certificate.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "target_host=depot.example.com target_port=8443"
```

### Example 3: Validate Changes with Check Mode

```bash
ansible-playbook playbooks/add_trusted_certificate.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "target_host=depot.example.com" \
  --check
```

### Example 4: Remove Trusted Certificate Using Playbook

```bash
ansible-playbook playbooks/remove_trusted_certificate.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "target_host=depot.example.com"
```

### Example 5: Query All Trusted Certificates

```bash
ansible-playbook playbooks/get_trusted_certificate_info.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml
```

## Workflow Sequence

### Add Trusted Certificate Workflow

1. `playbooks/add_trusted_certificate.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `util/trusted_ssl_certificate` role executes:
   - Validates `target_host` and `target_port`
   - Checks SSL port accessibility
   - Retrieves certificate subject, issuer, and PEM via OpenSSL
   - Sets `trusted_ssl_certificate_payload` fact
4. `sddc_manager_trusted_certificate_info` module checks the trust store:
   - Normalises and compares PEM content (strips subject/issuer headers)
   - Sets `trust_store_check.found` to `true` or `false`
5. If `trust_store_check.found` is `false`:
   - `sddc_manager/trusted_certificate` role adds the certificate (`state: present`)
   - Posts certificate and usage type to SDDC Manager API
   - Returns updated trust store list
6. Result is displayed

### Remove Trusted Certificate Workflow

1. `playbooks/remove_trusted_certificate.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `util/trusted_ssl_certificate` role executes:
   - Validates `target_host` and `target_port`
   - Checks SSL port accessibility
   - Retrieves certificate PEM via OpenSSL
   - Sets `trusted_ssl_certificate_payload` fact
4. `sddc_manager_trusted_certificate_info` module checks the trust store:
   - Normalises and compares PEM content (strips subject/issuer headers)
   - Resolves the certificate alias automatically
   - Sets `trust_store_check.found` to `true` or `false`
5. If `trust_store_check.found` is `true`:
   - `sddc_manager/trusted_certificate` role removes the certificate (`state: absent`)
   - Sends DELETE request to SDDC Manager API using the resolved alias
   - Returns the remaining trust store list
6. Result is displayed

### Query Trusted Certificates Workflow

1. `playbooks/get_trusted_certificate_info.yml` is triggered
2. `iac/get_settings` combines all IaC data into `all_iac_vars`
3. `sddc_manager/trusted_certificate_info` role executes:
   - Retrieves all trusted certificates from the trust store
   - Displays count and status message
