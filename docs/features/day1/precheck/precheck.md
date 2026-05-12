# Prechecks

## Overview

Checks the pre-requisites for ESX hosts to be used in a VMware Cloud Foundation instance.

Supported operations:

- [Verify ESX host connectivity.](./host-connection.md)
- [Verify ESX host SSL certificate.](./host-certificate.md)
- [Verify ESX host SSH service is running.](./host-ssh-service.md)
- [Verify ESX host NTP configuration and service.](./host-ntp-settings.md)
- [Verify ESX host standard switch MTU configuration.](./host-network-configuration.md)

    The following manual checks should also be completed before running the automation:

    - Ensure all A/PTR DNS records resolve successfully.
    - Ensure the ESX version matches the VMware Cloud Foundation version requirement.
    - Ensure that only `vmk0` exists.
    - Ensure that the `VM Network` portgroup is set to the same VLAN as the management portgroup.
    - Ensure that maintenance mode is disabled.
    - Ensure all IaC prerequisite requirements are complete.

## Prerequisites

Before you begin, make sure:

1. [Deployment prerequisites](../deployment-prerequisites.md) are met.
2. ESX hosts are reachable from the Ansible control node.
3. Infrastructure-as-Code (IaC) data is defined under `./infra-as-code/`.

## Configuration Requirements

The following configuration must be provided under `./infra-as-code/`:

- ESX host list and credentials.
- NTP server configuration.
- Standard switch MTU settings.

The [implementation plan](../../../design/implementation-plan.md) provides a
representative example set to follow.

## Execution

The precheck role supports two execution paths controlled by the `init` variable.

=== "New VCF Instance (`init: true`)"

    Use this path when running prechecks before an initial VCF instance deployment.
    Hosts are always sourced from inventory and no SDDC Manager filtering is applied.

    !!! note "VCF Installer Prechecks"
        The VMware Cloud Foundation Installer performs its own prechecks before it
        starts the VCF Instance deployment. 

        These prechecks are recommended to be run before the VCF Installer to
        identify and resolve any potential issues early in the process.

    ```bash
    ansible-playbook playbooks/preconfig_prechecks.yml \
      -e @examples/lab/vars/mgmt_automation_settings.yml \
      -e "init=true"
    ```

=== "Existing VCF Instance (default)"

    Use this path when running prechecks against an existing VCF instance. Hosts
    already assigned to a workload domain in SDDC Manager are automatically excluded.

    !!! note "Used by Other Operations"
        This path is invoked automatically during the following operations, which
        prepare the ESX hosts for use in a workload domain by ensuring they meet the
        necessary prerequisites. 

        Running the prechecks manually before these operations can also help identify
        and resolve any potential issues early in the process, if desired.

        - Commission hosts
        - Add a workload domain
        - Add a cluster
        - Add hosts to a cluster

    ```bash
    ansible-playbook playbooks/preconfig_prechecks.yml \
      -e @examples/lab/vars/mgmt_automation_settings.yml
    ```

## Ansible Components

- Module Utils:
    - `plugins/module_utils/esx_host.py`

- Modules:
    - `plugins/modules/precheck_esx_connection.py`
    - `plugins/modules/precheck_esx_certificate.py`
    - `plugins/modules/precheck_esx_service.py`
    - `plugins/modules/precheck_esx_ntp.py`
    - `plugins/modules/precheck_esx_standard_switch.py`

- Roles:
    - `roles/precheck/esx_precheck`
    - `roles/precheck/get_esx_hosts`
    - `roles/precheck/esx_connection`
    - `roles/precheck/esx_certificate`
    - `roles/precheck/esx_ssh`
    - `roles/precheck/esx_ntp`
    - `roles/precheck/esx_standard_switch`

- Playbooks:
    - `playbooks/preconfig_prechecks.yml`

## Workflow Sequence

=== "New VCF Instance (`init: true`)"

    1. `playbooks/preconfig_prechecks.yml` is triggered
    2. `iac/get_settings` combines all IaC data into `all_iac_vars`
    3. `precheck/esx_precheck` dispatches to the new instance path
    4. `precheck/get_esx_hosts` retrieves the ESX host list from `all_iac_vars`
    5. The following precheck roles execute in order against all inventory hosts:
        - `precheck/esx_connection` — verifies host connectivity
        - `precheck/esx_certificate` — verifies SSL certificate
        - `precheck/esx_ssh` — verifies SSH service is running
        - `precheck/esx_ntp` — verifies NTP configuration and service
        - `precheck/esx_standard_switch` — verifies standard switch MTU

=== "Existing VCF Instance (default)"

    1. `playbooks/preconfig_prechecks.yml` is triggered
    2. `iac/get_settings` combines all IaC data into `all_iac_vars`
    3. `precheck/esx_precheck` dispatches to the existing instance path
    4. ESX hosts are sourced from `hosts_input` or `all_iac_vars` via `precheck/get_esx_hosts`
    5. SDDC Manager is queried for hosts with `ASSIGNED` status
    6. Hosts already assigned to a workload domain are excluded; the play ends if none remain
    7. The following precheck roles execute in order against the remaining hosts:
        - `precheck/esx_connection` — verifies host connectivity
        - `precheck/esx_certificate` — verifies SSL certificate
        - `precheck/esx_ssh` — verifies SSH service is running
        - `precheck/esx_ntp` — verifies NTP configuration and service
        - `precheck/esx_standard_switch` — verifies standard switch MTU
