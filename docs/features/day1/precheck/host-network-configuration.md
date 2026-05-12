# Precheck: ESX Host Standard Switch

## Overview

Checks the MTU of the standard switch on ESX hosts and attempts to update it if it does
not match the expected value, ensuring correct network configuration before management
domain deployment begins.

## Prerequisites

Before you begin, make sure:

1. [Deployment prerequisites](../deployment-prerequisites.md) are met.
2. ESX hosts are reachable from the Ansible control node.
3. Infrastructure-as-Code (IaC) data is defined under `./infra-as-code/`.

## Configuration Requirements

The following inputs must be available:

- `esx_hosts` - List of ESX host hostnames or IP addresses.
- `esx_host_user` - Username to authenticate with the ESX hosts.
- `esx_host_password` - Password to authenticate with the ESX hosts.
- `virtual_standard_switch` - Dictionary containing standard switch details:
    - `virtual_standard_switch.name` - Name of the vSwitch to check.
    - `virtual_standard_switch.mtu` - Expected MTU value.
- `validate_certs` - Whether to validate SSL certificates of the ESX hosts.

## Execution

=== ":material-ansible: Ansible CLI"

    ```bash
    ansible-playbook playbooks/preconfig_prechecks.yml \
      -e @examples/lab/vars/mgmt_automation_settings.yml
    ```

## Ansible Components

- Module Utils:
    - `plugins/module_utils/esx_host.py`

- Modules:
    - `plugins/modules/precheck_esx_standard_switch.py`

- Roles:
    - `roles/precheck/esx_virtual_standard_switch`

- Playbooks:
    - `playbooks/preconfig_prechecks.yml`

## SDK / API Calls

- `networkInfo` - Retrieves the standard switch MTU setting.
- `networkSystem` - Updates the standard switch MTU setting.

## Workflow Sequence

1. `playbooks/preconfig_prechecks.yml` triggers the `precheck/esx_virtual_standard_switch` role.
2. The role calls the `precheck_esx_standard_switch` module.
3. The module loops through each ESX host and checks the standard switch MTU using the `networkInfo` method.
    - If the MTU matches the expected value: reports success.
    - If the MTU does not match: attempts to update it using the `networkSystem` method.
        - If the MTU updates successfully: reports success.
        - If the MTU fails to update: reports an error with exception details.
