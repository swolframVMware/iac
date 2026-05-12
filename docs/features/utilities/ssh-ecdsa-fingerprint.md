# Utilities: SSH ECDSA Fingerprint

## Overview

This utility retrieves the SSH ECDSA fingerprint from a target endpoint using the
`broadcom.vcf.util.ssh_ecdsa_fingerprint` role and provides it in SHA256 format.

!!! info "Use Case"
    VMware Cloud Foundation requires an SSH ECDSA fingerprint to verify the identity of
    the following endpoints:
    
    - SFTP backup server for SDDC Manager backups.

## Prerequisites

Before you begin, make sure:

1. The target endpoint is accessible from the Ansible control node.
2. SSH service (port 22) is running on the target endpoint.
3. The target endpoint has an ECDSA host key configured.
4. Network connectivity allows SSH traffic to the target endpoint.
5. Required command-line tools are available:
    - `ssh-keyscan`
    - `ssh-keygen`

## Role Interface

Role: `broadcom.vcf.util.ssh_ecdsa_fingerprint`

### Input Variables

- `target_host` - **(Required)** The hostname or IP address of the target endpoint.

### Output Variables

- `ssh_ecdsa_fingerprint` - The SSH ECDSA fingerprint in SHA256 format (e.g., `SHA256:abc123...`).

### Behavior

The role performs the following operations:

1. **Validate Input** - Ensures `target_host` is provided and not empty.

2. **Check Accessibility** - Tests if SSH port 22 is accessible on the target host:
    - Uses `ansible.builtin.wait_for` with a 10-second timeout.
    - If port is not accessible, fails with diagnostic information.

3. **Retrieve Fingerprint** - Executes SSH fingerprint retrieval:
    - Runs `ssh-keyscan -t ecdsa` to retrieve the ECDSA host key.
    - Pipes output to `ssh-keygen -lf - -E sha256` to compute SHA256 fingerprint.
    - Extracts the fingerprint using regex pattern `SHA256:[A-Za-z0-9+/]+`.

4. **Validate Format** - Ensures the retrieved fingerprint:
    - Is not empty.
    - Starts with `SHA256:` prefix.
    - Matches expected format.

5. **Set Output** - Stores the fingerprint in `ssh_ecdsa_fingerprint` fact for use by caller.

## Usage

### Using the Role Directly

```yaml
- name: Get SSH Fingerprint for Backup Server
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Retrieve SSH ECDSA Fingerprint
      ansible.builtin.include_role:
        name: broadcom.vcf.util.ssh_ecdsa_fingerprint
      vars:
        target_host: backup.example.com

    - name: Use the Fingerprint
      ansible.builtin.debug:
        msg: "Fingerprint: {{ ssh_ecdsa_fingerprint }}"
```

### Using the Playbook

The collection includes a convenience playbook for standalone execution:

```bash
ansible-playbook playbooks/get_ssh_ecdsa_fingerprint.yml \
  -e "target_host=backup.example.com"
```

**Examples:**

```bash
# Get fingerprint from FQDN
ansible-playbook playbooks/get_ssh_ecdsa_fingerprint.yml \
  -e "target_host=backup.example.com"

# Get fingerprint from IP address
ansible-playbook playbooks/get_ssh_ecdsa_fingerprint.yml \
  -e "target_host=192.168.1.100"

```

## Error Handling

### SSH Port Not Accessible

**Error:**

```
SSH port 22 is not accessible on <target_host>.
```

**Resolution:**

1. Verify the host is reachable:

    ```bash
    ping <target_host>
    ```

2. Check if SSH port is open:

    ```bash
    nc -zv <target_host> 22
    ```

3. Verify SSH service is running on the target:

    ```bash
    systemctl status sshd  # On target system
    ```

4. Check firewall rules on the target:

    ```bash
    iptables -L -n | grep 22
    firewall-cmd --list-all
    ```

### Invalid Fingerprint Format

**Error:**

```
Failed to retrieve valid SSH ECDSA fingerprint from <target_host>.
```

**Possible Causes:**

- **No ECDSA key available** - Target may only have RSA or ED25519 keys.
- **SSH configuration issue** - SSH service may not be properly configured.
- **Network timeout** - Connection interrupted during key retrieval.

**Resolution:**

1. Manually verify SSH keys on the target:

    ```bash
    ssh-keyscan -t ecdsa <target_host>
    ```

2. Check available key types:

    ```bash
    ssh-keyscan <target_host>
    ```

3. On the target system, verify ECDSA key exists:

    ```bash
    ls -l /etc/ssh/ssh_host_ecdsa_key*
    ```

4. If ECDSA key is missing, generate it:

    ```bash
    ssh-keygen -t ecdsa -f /etc/ssh/ssh_host_ecdsa_key -N ""
    systemctl restart sshd
    ```

## Advanced Usage

### Multiple Endpoints

Retrieve fingerprints from multiple endpoints in a single play:

```yaml
- name: Retrieve Multiple SSH Fingerprints
  hosts: localhost
  gather_facts: false
  vars:
    endpoints:
      - backup.example.com
      - nfs.example.com
      - archive.example.com
      
  tasks:
    - name: Get Fingerprints
      ansible.builtin.include_role:
        name: broadcom.vcf.util.ssh_ecdsa_fingerprint
      vars:
        target_host: "{{ item }}"
      loop: "{{ endpoints }}"
      register: fingerprint_results

    - name: Store All Fingerprints
      ansible.builtin.set_fact:
        endpoint_fingerprints: "{{ endpoint_fingerprints | default({}) | combine({item: ssh_ecdsa_fingerprint}) }}"
      loop: "{{ endpoints }}"
```

### Custom Timeout

The role uses a 10-second timeout for port checking. For slower networks, you can
modify the role's behavior by overriding the internal task (not recommended), or
perform your own pre-check before calling the role.

## Technical Details

### SSH Fingerprint Format

The role retrieves fingerprints in the following format:

```
SHA256:YourBase64EncodedFingerprintHere
```

Example:

```
SHA256:nThbg6kXUpJWGl7E1IGOCspRomTxdCARLviKw6E5SY8
```

### Commands Executed

The role executes the equivalent of:

```bash
ssh-keyscan -t ecdsa <target_host> 2>/dev/null | \
  ssh-keygen -lf - -E sha256
```

This command:

1. `ssh-keyscan -t ecdsa <target_host>` - Retrieves the ECDSA public key from the host.
2. `2>/dev/null` - Suppresses stderr output.
3. `ssh-keygen -lf - -E sha256` - Computes the SHA256 fingerprint from the key.
4. Regex extraction - Isolates the `SHA256:...` portion from the output.

## Reference

### Related Playbooks

- `playbooks/get_ssh_ecdsa_fingerprint.yml` - A standalone playbook.

### Related Roles

- `broadcom.vcf.util.ssh_ecdsa_fingerprint` - The helper role.

### Related Modules

This role uses Ansible built-in modules:

- `ansible.builtin.set_fact` - Store variables
- `ansible.builtin.assert` - Validate inputs and outputs
- `ansible.builtin.wait_for` - Check port accessibility
- `ansible.builtin.debug` - Display results
- `ansible.builtin.lookup` with `pipe` - Execute shell commands

## Security Considerations

!!! warning "Trust on First Use"
    This utility retrieves the SSH fingerprint without prior verification. The first
    retrieval should be performed in a secure environment or verified through
    out-of-band means to prevent man-in-the-middle attacks.
