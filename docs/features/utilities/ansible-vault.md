# Utilities: Manage Vaulted Passwords

## Overview

This guide shows how to create, store, and use the `vault_*` variables referenced by the
infrastructure-as-code samples in this collection.

Use this guide when you want to:

- Replace the sample `vault_*` placeholders with real secrets.
- Keep passwords out of clear-text IaC files.
- Run playbooks locally with `ansible-playbook`.
- Run the same content in Ansible Automation Platform (AAP) or automation controller.

The collection's sample IaC now expects vaulted variables such as
`vault_vcf_installer_password` and `vault_proxy_password` instead of embedded demo
passwords.

## Recommended Approach

The recommended workflow is to keep secret values in a separate vaulted vars file and pass that file
alongside your normal IaC inputs.

### 1. Create a Vaulted vars File

Create a new encrypted file with the `ansible-vault create` command:

```bash
ansible-vault create ~/vault/vcf-vault-secrets.yml
```

Add only the variables you need for the sample or workflow you are using.

=== "9.0.x.x"

    ```yaml
    vault_depot_download_token: "replace-me"
    vault_depot_offline_password: "replace-me"
    vault_certificate_authority_microsoft_password: "replace-me"
    vault_backup_encryption_passphrase: "replace-me"
    vault_backup_password: "replace-me"
    vault_proxy_password: "replace-me"
    vault_vcf_installer_local_password: "replace-me"
    vault_vcf_installer_root_password: "replace-me"
    vault_vcf_installer_vsphere_password: "replace-me"
    vault_vcf_installer_password: "replace-me"
    vault_sddc_manager_root_password: "replace-me"
    vault_sddc_manager_admin_password: "replace-me"
    vault_sddc_manager_vcf_password: "replace-me"
    vault_vcenter_root_password: "replace-me"
    vault_vcenter_administrator_password: "replace-me"
    vault_sso_domain_password: "replace-me"
    vault_esx_host_password: "replace-me"
    vault_nsx_root_password: "replace-me"
    vault_nsx_admin_password: "replace-me"
    vault_nsx_audit_password: "replace-me"
    vault_edge_root_password: "replace-me"
    vault_edge_admin_password: "replace-me"
    vault_edge_audit_password: "replace-me"
    vault_bgp_peer_password: "replace-me"
    vault_operations_root_password: "replace-me"
    vault_operations_admin_password: "replace-me"
    vault_fleet_management_root_password: "replace-me"
    vault_fleet_management_admin_password: "replace-me"
    vault_collector_root_password: "replace-me"
    vault_automation_admin_password: "replace-me"
    ```

=== "9.1.x.x"

    ```yaml
    vault_depot_download_activation_code: "replace-me"
    vault_depot_offline_password: "replace-me"
    vault_certificate_authority_microsoft_password: "replace-me"
    vault_backup_encryption_passphrase: "replace-me"
    vault_backup_password: "replace-me"
    vault_proxy_password: "replace-me"
    vault_management_password: "replace-me"
    vault_vcf_installer_local_password: "replace-me"
    vault_vcf_installer_root_password: "replace-me"
    vault_vcf_installer_vsphere_password: "replace-me"
    vault_vcf_installer_password: "replace-me"
    vault_sddc_manager_root_password: "replace-me"
    vault_sddc_manager_admin_password: "replace-me"
    vault_sddc_manager_vcf_password: "replace-me"
    vault_vcenter_root_password: "replace-me"
    vault_vcenter_administrator_password: "replace-me"
    vault_sso_domain_password: "replace-me"
    vault_esx_host_password: "replace-me"
    vault_nsx_root_password: "replace-me"
    vault_nsx_admin_password: "replace-me"
    vault_nsx_audit_password: "replace-me"
    vault_edge_root_password: "replace-me"
    vault_edge_admin_password: "replace-me"
    vault_edge_audit_password: "replace-me"
    vault_bgp_peer_password: "replace-me"
    vault_operations_root_password: "replace-me"
    vault_operations_admin_password: "replace-me"
    vault_collector_root_password: "replace-me"
    vault_automation_admin_password: "replace-me"
    ```

### 2. Run Playbooks with Both IaC and Ansible Vault Secrets

Pass your normal IaC input file and the vaulted vars file together:

```bash
ansible-playbook playbooks/deploy_instance.yml \
  -e @/path/to/iac-settings.yml \
  -e @~/vault/vcf-vault-secrets.yml \
  --ask-vault-pass
```

If you already use an Ansible Vault password file, use that instead of an interactive prompt:

```bash
ansible-playbook playbooks/deploy_instance.yml \
  -e @/path/to/iac-settings.yml \
  -e @~/vault/vcf-vault-secrets.yml \
  --vault-password-file ~/.ansible/ansible-vault.txt
```

### 3. Update Secrets in Ansible Vault

Common lifecycle commands:

```bash
ansible-vault edit ~/vault/vcf-vault-secrets.yml
ansible-vault view ~/vault/vcf-vault-secrets.yml
ansible-vault rekey ~/vault/vcf-vault-secrets.yml
```

If you already have a plaintext vars file, encrypt it in place:

```bash
ansible-vault encrypt /path/to/vcf-vault-secrets.yml
```

## Vault Variable Names Used by the Sample IaC

### Sample Default Configurations

These are referenced by the infrastructure-as-code samples under
`infra-as-code/global/regions/defaults/config/`:

=== "9.0.x.x"

    | Area                    | Variables                                                                                                                                                                             |
    |-------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
    | VCF Installer           | `vault_vcf_installer_password`, `vault_vcf_installer_local_password`, `vault_vcf_installer_root_password`, `vault_vcf_installer_vsphere_password`                                     |
    | vSphere                 | `vault_vcenter_root_password`, `vault_vcenter_administrator_password`, `vault_sso_domain_password`, `vault_esx_host_password`                                                         |
    | NSX                     | `vault_nsx_root_password`, `vault_nsx_admin_password`, `vault_nsx_audit_password`                                                                                                     |
    | SDDC Manager            | `vault_sddc_manager_root_password`, `vault_sddc_manager_admin_password`, `vault_sddc_manager_vcf_password`                                                                            |
    | VCF Operations          | `vault_operations_root_password`, `vault_operations_admin_password`, `vault_collector_root_password`, `vault_fleet_management_root_password`, `vault_fleet_management_admin_password` |
    | VCF Automation          | `vault_automation_admin_password`                                                                                                                                                     |

=== "9.1.x.x"

    | Area                    | Variables                                                                                                                                                                             |
    |-------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
    | VCF Installer           | `vault_vcf_installer_password`, `vault_vcf_installer_local_password`, `vault_vcf_installer_root_password`, `vault_vcf_installer_vsphere_password`                                     |
    | vSphere                 | `vault_vcenter_root_password`, `vault_vcenter_administrator_password`, `vault_sso_domain_password`, `vault_esx_host_password`                                                         |
    | NSX                     | `vault_nsx_root_password`, `vault_nsx_admin_password`, `vault_nsx_audit_password`                                                                                                     |
    | SDDC Manager            | `vault_sddc_manager_root_password`, `vault_sddc_manager_admin_password`, `vault_sddc_manager_vcf_password`                                                                            |
    | VCF Management Services | `vault_management_password`                                                                                                                                                           |
    | VCF Operations          | `vault_operations_root_password`, `vault_operations_admin_password`, `vault_collector_root_password`                                                                                  | |
    | VCF Automation          | `vault_automation_admin_password`                                                                                                                                                     |

### Sample Lab Configurations

These are referenced by the infrastructure-as-code samples under
`infra-as-code/global/regions/amer/.../vcfs/.../config/`:

=== "9.0.x.x"

    | Area                    | Variables                                                                                                        |
    |-------------------------|------------------------------------------------------------------------------------------------------------------|
    | Backup                  | `vault_backup_password`, `vault_backup_encryption_passphrase`                                                    |
    | Depot                   | `vault_depot_download_token`, `vault_depot_offline_password`                                                     |
    | Proxy                   | `vault_proxy_password`                                                                                           |
    | Microsoft CA            | `vault_certificate_authority_microsoft_password`                                                                 |
    | NSX Edge                | `vault_edge_root_password`, `vault_edge_admin_password`, `vault_edge_audit_password`, `vault_bgp_peer_password`  |

=== "9.1.x.x"

    | Area                    | Variables                                                                                                        |
    |-------------------------|------------------------------------------------------------------------------------------------------------------|
    | Backup                  | `vault_backup_password`, `vault_backup_encryption_passphrase`                                                    |
    | Depot                   | `vault_depot_download_activation_code`, `vault_depot_offline_password`                                                     |
    | Proxy                   | `vault_proxy_password`                                                                                           |
    | Microsoft CA            | `vault_certificate_authority_microsoft_password`                                                                 |
    | NSX Edge                | `vault_edge_root_password`, `vault_edge_admin_password`, `vault_edge_audit_password`, `vault_bgp_peer_password`  |

## Optional: Encrypt a Single Variable

If you prefer to keep only one value encrypted at a time, use `ansible-vault encrypt_string`.

Example:

```bash
ansible-vault encrypt_string \
  --stdin-name 'vault_proxy_password'
```

You can then paste the generated `!vault` block into a vars file, inventory file, or another
encrypted source that is already part of your workflow.

## Relationship to Runtime Override Variables

The collection still supports the existing runtime override variable names documented in
the feature guides, such as:

- `vcf_installer_password`
- `vcenter_root_password`
- `vcenter_administrator_password`
- `proxy_password`
- `certificate_authority_microsoft_password`
- `edge_root_password`

Use the `vault_*` names when you are consuming the infrastructure-as-code samples files as written.

Use the runtime override names when you want to inject values at playbook runtime,
through surveys, credentials, or other orchestration layers.

## Ansible Automation Platform (AAP) / Automation Controller

When running in AAP or automation controller:

1. Store your vaulted vars file in the project, inventory source, or another approved
   content source available to the controller.
2. Attach a Vault credential to the job template so the controller can decrypt the
   vaulted file at runtime.
3. Continue to use Machine, custom, or other credential types for non-vaulted runtime overrides when
   that better fits your operational model.

If you are using the sample IaC files directly, the important part is that the controller can
decrypt the vars file that defines the `vault_*` names referenced by those YAML files.

## Official References

- [Protecting Sensitive Data with Ansible Vault](https://docs.ansible.com/ansible/latest/vault_guide/index.html)
- [Encrypting Content with Ansible Vault](https://docs.ansible.com/ansible/latest/vault_guide/vault_encrypting_content.html)
- [ansible-vault Command Reference](https://docs.ansible.com/ansible/latest/cli/ansible-vault.html)
- [Automation Controller Credentials](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.4/html/getting_started_with_automation_controller/controller-credentials)
