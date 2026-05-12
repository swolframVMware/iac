# Precheck: ESX Host SSH Service

## Overview

Checks the status of the SSH service on ESX hosts and attempts to start it if not
running, ensuring SSH is available before management domain deployment begins.

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
- `esx_service_name` - The name of the ESX service to check (e.g. `TSM-SSH`).
- `esx_service_state` - The desired state of the ESX service (e.g. `running`).
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
    - `plugins/modules/precheck_esx_service.py`

- Roles:
    - `roles/precheck/esx_service`

- Playbooks:
    - `playbooks/preconfig_prechecks.yml`

## SDK / API Calls

- `RetrieveServiceInfo` - Retrieves details about services running on the ESX host.
- `StartService` - Starts the specified service.
- `RestartService` - Restarts the specified service.
- `StopService` - Stops the specified service.

## Workflow Sequence

1. `playbooks/preconfig_prechecks.yml` triggers the `precheck/esx_service` role.
2. The role calls the `precheck_esx_service` module.
3. The module loops through each ESX host and checks the SSH service status using Service Manager.
    - If the SSH service is running: reports back success.
    - If the SSH service is not running: attempts to start it.
        - If the service starts successfully: reports back success.
        - If the service fails to start: reports back an error with exception details.
