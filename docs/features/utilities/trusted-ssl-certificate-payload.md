# Utilities: Trusted SSL Certificate Payload

## Overview

This utility retrieves the SSL certificate from a target endpoint using the
`broadcom.vcf.util.trusted_ssl_certificate` role and builds the trusted certificate JSON
payload required by the Trusted Certificate API operations on both VCF Installer
and SDDC Manager.

!!! info "Use Case"
    VMware Cloud Foundation requires a trusted certificate to be added to the trust store
    for outbound HTTPS connections to the following endpoints:

    - Offline depot instance for VCF Installer.
    - Offline depot instance for SDDC Manager.

## Prerequisites

Before you begin, make sure:

1. The target endpoint is accessible from the Ansible control node.
2. SSL/TLS service is running on the target endpoint (default port 443).
3. The target endpoint has a valid SSL certificate configured.
4. Network connectivity allows SSL traffic to the target endpoint.
5. Required command-line tools are available:
    - `openssl`

## Role Interface

Role: `broadcom.vcf.util.trusted_ssl_certificate`

### Input Variables

- `target_host` - **(Required)** The hostname or IP address of the target endpoint from
  which the SSL certificate will be retrieved.
- `target_port` - **(Optional)** The port number for the SSL connection. Default: `443`.
- `certificate_usage_type` - **(Optional)** The certificate usage type for the payload.
  Valid values: `TRUSTED_FOR_OUTBOUND`. Default: `TRUSTED_FOR_OUTBOUND`.

### Output Variables

- `trusted_ssl_certificate_payload` - A dict containing the trusted certificate request body:
    - `certificate` - The PEM certificate string with subject and issuer header lines,
      formatted with embedded newlines.
    - `certificateUsageType` - The certificate usage type value.

  Example:

  ```json
  {
    "certificate": "subject=C = US, ST = California, L = Palo Alto, O = Example, OU = IT, CN = depot.example.com\nissuer=DC = com, DC = example, CN = example-ca\n-----BEGIN CERTIFICATE-----\nMIIFnDCCBISg...==\n-----END CERTIFICATE-----\n\n",
    "certificateUsageType": "TRUSTED_FOR_OUTBOUND"
  }
  ```

### Behavior

The role performs the following operations:

1. **Validate Input** - Ensures:
    - `target_host` is provided and not empty.
    - `target_port` is a valid port number (1-65535).

2. **Check Accessibility** - Tests if the SSL port is accessible on the target host:
    - Uses `ansible.builtin.wait_for` with a 10-second timeout.
    - If port is not accessible, fails with diagnostic information.

3. **Retrieve Certificate** - Executes SSL certificate retrieval:
    - Connects to the endpoint using `openssl s_client`.
    - Extracts the certificate subject and issuer lines.
    - Extracts the full PEM certificate block (`-----BEGIN CERTIFICATE-----` through `-----END CERTIFICATE-----`).

4. **Validate Certificate** – Ensures the retrieved PEM:
    - Is not empty.
    - Contains a valid `BEGIN CERTIFICATE` / `END CERTIFICATE` block.

5. **Build Payload** – Assembles the certificate string with subject and issuer headers,
   and packages it into a dict matching the trusted certificate request body format.

6. **Set Output** – Stores the payload in the `trusted_ssl_certificate_payload` fact for use
   by the caller.

## Usage

### Using the Role Directly

```yaml
- name: Get Trusted Certificate Payload for Depot Server
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Retrieve Trusted Certificate Payload
      ansible.builtin.include_role:
        name: broadcom.vcf.util.trusted_ssl_certificate
      vars:
        target_host: depot.example.com
        target_port: 443

    - name: Use the Payload
      ansible.builtin.debug:
        msg: "Payload: {{ trusted_ssl_certificate_payload }}"
```

### Using the Playbook

The collection includes a convenience playbook for standalone execution:

```bash
ansible-playbook playbooks/get_trusted_ssl_certificate_payload.yml \
  -e "target_host=depot.example.com"
```

**Examples:**

```bash
# Get payload from FQDN (default port 443)
ansible-playbook playbooks/get_trusted_ssl_certificate_payload.yml \
  -e "target_host=depot.example.com"

# Get payload from FQDN with specific port
ansible-playbook playbooks/get_trusted_ssl_certificate_payload.yml \
  -e "target_host=depot.example.com target_port=8443"

# Get payload from IP address
ansible-playbook playbooks/get_trusted_ssl_certificate_payload.yml \
  -e "target_host=192.168.1.100"
```

### Custom Timeout

The role uses a 10-second timeout for port checking. For slower networks, you can
modify the role's behavior by overriding the internal task (not recommended), or
perform your own pre-check before calling the role.

## Technical Details

### Certificate Payload Format

The role assembles the certificate string in the following format, which matches the
trusted certificate request body expected by both VCF Installer and SDDC Manager:

```
subject=<subject>\nissuer=<issuer>\n-----BEGIN CERTIFICATE-----\n<base64>\n-----END CERTIFICATE-----\n\n
```

**Example:**

```
subject=C = US, ST = California, L = Palo Alto, O = Example, OU = IT, CN = depot.example.com
issuer=DC = com, DC = example, CN = example-ca
-----BEGIN CERTIFICATE-----
MIIFnDCCBISgAwIBAgITIgAAAA...MpEkV22x6geVze1RvRzCm/3EfOvkeoreg==
-----END CERTIFICATE-----

```

### Commands Executed

The role executes the equivalent of:

```bash
# Retrieve the subject
echo | openssl s_client -connect <hostname>:<port> 2>/dev/null | \
  openssl x509 -noout -subject | sed 's/subject=//'

# Retrieve the issuer
echo | openssl s_client -connect <hostname>:<port> 2>/dev/null | \
  openssl x509 -noout -issuer | sed 's/issuer=//'

# Retrieve the PEM certificate block
echo | openssl s_client -connect <hostname>:<port> 2>/dev/null | \
  openssl x509
```

Each command:

1. `echo |` - Provides empty input to openssl.
2. `openssl s_client -connect <hostname>:<port>` - Connects to SSL/TLS service and retrieves certificate.
3. `2>/dev/null` - Suppresses stderr output (connection messages).
4. `openssl x509 ...` - Parses and extracts the end-entity certificate details.

## Reference

### Related Playbooks

- `playbooks/get_trusted_ssl_certificate_payload.yml` - A standalone playbook.

### Related Roles

- `broadcom.vcf.util.trusted_ssl_certificate` - This helper role.

### Related API Operations

- `POST /v1/sddc-manager/trusted-certificates` - VCF Installer: Add a trusted certificate.
- `POST /v1/trusted-certificates` - SDDC Manager: Add a trusted certificate.

### Related Modules

This role uses Ansible built-in modules:

- `ansible.builtin.set_fact` - Store variables
- `ansible.builtin.assert` - Validate inputs and outputs
- `ansible.builtin.wait_for` - Check port accessibility
- `ansible.builtin.lookup` with `pipe` - Execute shell commands

## Security Considerations

!!! warning "Trust on First Use"
    This utility retrieves the SSL certificate without prior verification. The first
    retrieval should be performed in a secure environment or verified through
    out-of-band means to prevent man-in-the-middle attacks.

!!! note "Certificate Scope"
    This utility retrieves only the end-entity (leaf) certificate from the endpoint.
    If your environment uses intermediate or root CA certificates that are not presented
    by the endpoint, those must be added to the trust store separately.
