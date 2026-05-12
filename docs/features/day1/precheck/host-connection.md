# Precheck: ESX Host Connection

## Overview

Checks the connection to ESX hosts to confirm they are reachable before the management
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
    - `plugins/modules/precheck_esx_connection.py`

- Roles:
    - `roles/precheck/esx_connection`

- Playbooks:
    - `playbooks/preconfig_prechecks.yml`

## SDK / API Calls

- `GET /ui` - Primary endpoint used to verify ESX host connectivity.

## Workflow Sequence

1. `playbooks/preconfig_prechecks.yml` triggers the `precheck/esx_connection` role.
2. The role calls the `precheck_esx_connection` module.
3. The module loops through each ESX host and attempts to connect via the `/ui` endpoint.
    - If connection succeeds: reports back success.
    - If connection fails: checks the exit code and reports the failure details.
