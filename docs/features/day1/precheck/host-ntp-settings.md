# Precheck: ESX Host NTP Settings

## Overview

Checks NTP server configuration and service status on ESX hosts. Attempts to configure
NTP servers and start the NTP service if not already correct, ensuring time
synchronisation before management domain deployment begins.

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
- `esx_service_name` - The name of the NTP service (e.g. `ntpd`).
- `esx_service_state` - The desired state of the NTP service (e.g. `running`).
- `esx_ntp_servers` - List of NTP server hostnames or IP addresses.
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
    - `plugins/modules/precheck_esx_ntp.py`

- Roles:
    - `roles/precheck/esx_ntp`

- Playbooks:
    - `playbooks/preconfig_prechecks.yml`

## SDK / API Calls

- `RetrieveServiceInfo` - Retrieves details about services running on the ESX host.
- `StartService` - Starts the specified service.
- `RestartService` - Restarts the specified service.
- `StopService` - Stops the specified service.
- `dateTimeSystem` - Used to get and update NTP server configuration.

## Workflow Sequence

1. `playbooks/preconfig_prechecks.yml` triggers the `precheck/esx_ntp` role.
2. The role calls the `precheck_esx_ntp` module.
3. The module loops through each ESX host and:
    - Checks if NTP servers are configured:
        - If NTP servers are not set: attempts to set them using the `dateTimeSystem` API.
        - If NTP servers are already set: reports success.
    - Checks NTP service status using Service Manager:
        - If the NTP service is running: reports success.
        - If the NTP service is not running: attempts to start it.
            - If the service starts successfully: reports success.
            - If the service fails to start: reports an error with exception details.
