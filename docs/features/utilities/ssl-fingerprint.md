# Utilities: SSL Certificate Fingerprint

## Overview

This utility retrieves the SSL certificate fingerprint from a target endpoint using the
`broadcom.vcf.util.ssl_fingerprint` role and provides it in SHA256 colon-separated hexadecimal format.

!!! info "Use Case"
    VMware Cloud Foundation requires an SSL fingerprint to verify the identity of
    the following endpoints:
    
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

Role: `broadcom.vcf.util.ssl_fingerprint`

### Input Variables

- `target_host` - **(Required)** The hostname or IP address of the target endpoint.
- `target_port` - **(Optional)** The port number for SSL connection. Default: `443`.

### Output Variables

- `ssl_fingerprint` - The SSL certificate fingerprint in SHA256 colon-separated hex format.
  
  Example: `73:D8:AC:0E:0A:AA:91:6B:B0:07:33:0E:C4:03:DB:B8:3C:E3:EB:58:E6:C2:02:D8:1F:00:22:F7:B4:F4:7B:80`

### Behavior

The role performs the following operations:

1. **Validate Input** - Ensures:
    - `target_host` is provided and not empty.
    - `target_port` is a valid port number (1-65535).

2. **Check Accessibility** - Tests if the SSL port is accessible on the target host:
    - Uses `ansible.builtin.wait_for` with a 10-second timeout.
    - If port is not accessible, fails with diagnostic information.

3. **Retrieve Fingerprint** - Executes SSL certificate retrieval:
    - Connects to the endpoint using `openssl s_client`.
    - Extracts the certificate and computes SHA256 fingerprint.
    - Formats as colon-separated hexadecimal.

4. **Validate Format** – Ensures the retrieved fingerprint:
    - Is not empty.
    - Matches the expected format: 32 hex byte pairs separated by colons.
    - Conforms to pattern: `XX:XX:XX:...:XX` (64 hex chars + 31 colons = 95 chars total).

5. **Set Output** – Stores the fingerprint in `ssl_fingerprint` fact for use by caller.

## Usage

### Using the Role Directly

```yaml
- name: Get SSL Fingerprint for Depot Server
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Retrieve SSL Fingerprint
      ansible.builtin.include_role:
        name: broadcom.vcf.util.ssl_fingerprint
      vars:
        target_host: depot.example.com
        target_port: 443

    - name: Use the Fingerprint
      ansible.builtin.debug:
        msg: "Fingerprint: {{ ssl_fingerprint }}"
```

### Using the Playbook

The collection includes a convenience playbook for standalone execution:

```bash
ansible-playbook playbooks/get_ssl_certificate_fingerprint.yml \
  -e "target_host=depot.example.com"
```

**Examples:**

```bash
# Get fingerprint from FQDN (default port 443)
ansible-playbook playbooks/get_ssl_certificate_fingerprint.yml \
  -e "target_host=depot.example.com"

# Get fingerprint from FQDN with specific port
ansible-playbook playbooks/get_ssl_certificate_fingerprint.yml \
  -e "target_host=depot.example.com target_port=8443"

# Get fingerprint from IP address
ansible-playbook playbooks/get_ssl_certificate_fingerprint.yml \
  -e "target_host=192.168.1.100"
```

## Error Handling

### SSL Port Not Accessible

**Error:**

```
SSL port <port> is not accessible on <target_host>.
```

**Resolution:**

1. Verify the host is reachable:

    ```bash
    ping <target_host>
    ```

2. Check if SSL port is open:

    ```bash
    nc -zv <target_host> <port>
    ```

3. Verify SSL/TLS service is running on the target:

    ```bash
    systemctl status httpd  # On target system (or nginx, apache2, etc.)
    ```

4. Check firewall rules on the target:

    ```bash
    iptables -L -n | grep <port>
    firewall-cmd --list-all
    ```

### Invalid Fingerprint Format

**Error:**

```
Failed to retrieve valid SSL fingerprint from <target_host>:<port>.
```

**Possible Causes:**

- **No SSL certificate** – Service may not have SSL enabled.
- **Invalid certificate** – Certificate may be corrupted or expired.
- **Network timeout** – Connection interrupted during certificate retrieval.

**Resolution:**

1. Manually verify SSL connection:

    ```bash
    echo | openssl s_client -connect <target_host>:<port>
    ```

2. Check certificate validity:

    ```bash
    echo | openssl s_client -connect <target_host>:<port> 2>/dev/null | \
      openssl x509 -noout -text
    ```

3. On the target system, verify certificate exists and is valid:

    ```bash
    openssl x509 -in /path/to/cert.pem -noout -dates
    ```

4. If certificate is missing or invalid, regenerate it on the target.

## Advanced Usage

### Multiple Endpoints

Retrieve fingerprints from multiple endpoints in a single play:

```yaml
- name: Retrieve Multiple SSL Fingerprints
  hosts: localhost
  gather_facts: false
  vars:
    endpoints:
      - host: depot.example.com
        port: 443
      - host: packages.example.com
        port: 8443
      
  tasks:
    - name: Get Fingerprints
      ansible.builtin.include_role:
        name: broadcom.vcf.util.ssl_fingerprint
      vars:
        target_host: "{{ item.host }}"
        target_port: "{{ item.port }}"
      loop: "{{ endpoints }}"
      loop_control:
        label: "{{ item.host }}:{{ item.port }}"

    - name: Store Fingerprint
      ansible.builtin.set_fact:
        endpoint_fingerprints: "{{ endpoint_fingerprints | default({}) | combine({item.host + ':' + (item.port | string): ssl_fingerprint}) }}"
      loop: "{{ endpoints }}"
      loop_control:
        label: "{{ item.host }}:{{ item.port }}"
```

### Custom Timeout

The role uses a 10-second timeout for port checking. For slower networks, you can
modify the role's behavior by overriding the internal task (not recommended), or
perform your own pre-check before calling the role.

## Technical Details

### SSL Fingerprint Format

The role retrieves fingerprints in the following format:

```
XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX:XX
```

- 32 pairs of hexadecimal digits (64 characters total)
- Separated by colons (31 colons)
- Uppercase letters A-F
- Total length: 95 characters

**Example:**

```
73:D8:AC:0E:0A:AA:91:6B:B0:07:33:0E:C4:03:DB:B8:3C:E3:EB:58:E6:C2:02:D8:1F:00:22:F7:B4:F4:7B:80
```

### Commands Executed

The role executes the equivalent of:

```bash
echo | openssl s_client -connect <hostname>:<port> 2>/dev/null | \
  openssl x509 -noout -fingerprint -sha256 | \
  cut -d'=' -f2
```

This command:

1. `echo |` - Provides empty input to openssl.
2. `openssl s_client -connect <hostname>:<port>` - Connects to SSL/TLS service and retrieves certificate.
3. `2>/dev/null` - Suppresses stderr output (connection messages).
4. `openssl x509 -noout -fingerprint -sha256` - Computes SHA256 fingerprint of the certificate.
5. `cut -d'=' -f2` - Extracts the fingerprint value after the `=` sign.

## Reference

### Related Playbooks

- `playbooks/get_ssl_fingerprint.yml` - A standalone playbook.

### Related Roles

- `broadcom.vcf.util.ssl_fingerprint` - This helper role.

### Related Modules

This role uses Ansible built-in modules:

- `ansible.builtin.set_fact` - Store variables
- `ansible.builtin.assert` - Validate inputs and outputs
- `ansible.builtin.wait_for` - Check port accessibility
- `ansible.builtin.debug` - Display results
- `ansible.builtin.lookup` with `pipe` - Execute shell commands

## Security Considerations

!!! warning "Trust on First Use"
    This utility retrieves the SSL fingerprint without prior verification. The first
    retrieval should be performed in a secure environment or verified through
    out-of-band means to prevent man-in-the-middle attacks.
