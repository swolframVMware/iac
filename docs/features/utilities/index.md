# Utilities

## Overview

This section documents utility roles and playbooks that provide helper functionality
in the Ansible collection. These utilities are designed to be reusable components that
can be invoked standalone or integrated into larger workflows.

## Available Utilities

- [Manage Vaulted Passwords](ansible-vault.md) - Create, encrypt, and supply the `vault_*` variables used by the sample IaC files.
- [SSH ECDSA Fingerprint](ssh-ecdsa-fingerprint.md) - Retrieve SSH ECDSA fingerprints for SFTP/SSH endpoints.
- [SSL Certificate Fingerprint](ssl-fingerprint.md) – Retrieve SSL certificate fingerprint for HTTPS endpoints.
- [Trusted Certificate Payload](trusted-ssl-certificate-payload.md) – Build a trusted certificate payload from for VCF Installer and SDDC Manager.

## Design Principles

Utility roles in this collection follow these principles:

1. **Single Responsibility** – Each utility focuses on one specific task.
2. **Minimal Dependencies** – Utilities have minimal or no dependencies on other roles.
3. **Clear Interface** - Well-defined input and output variables.
4. **Error Handling** - Comprehensive validation and error messages.
5. **Reusability** – Can be used standalone or integrated into larger workflows.
6. **Idempotent** – Safe to run multiple times without side effects.

## Usage Patterns

### Standalone Execution

All utilities can be executed directly via their corresponding playbooks:

```bash
ansible-playbook playbooks/<utility_playbook>.yml -e "param=value"
```

### Role Integration

Utilities can be included in larger workflows:

```yaml
- name: My Workflow
  hosts: localhost
  tasks:
    - name: Use Utility
      ansible.builtin.include_role:
        name: broadcom.vcf.ops.<utility_role>
      vars:
        input_var: value
    
    - name: Use Output
      ansible.builtin.debug:
        msg: "{{ output_var }}"
```

### Variable Passing

Utility roles use clearly defined input/output variables:

- **Input Variables** – Passed when including the role via `vars:` section.
- **Output Variables** – Set as facts, accessible after role execution.
