# -*- coding: utf-8 -*-
#
# Copyright (c) Broadcom. All Rights Reserved.
# The term “Broadcom” refers solely to the Broadcom Inc. corporate affiliate that
# distributes this software.
#
# You are hereby granted a non-exclusive, worldwide, royalty-free license under
# Broadcom’s copyrights to use, copy, modify, and distribute this software in source
# code or binary form for use in connection with Broadcom products.
#
# This copyright notice shall be included in all copies or substantial portions of the
# software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from __future__ import absolute_import, division, print_function

DOCUMENTATION = r"""
---
module: precheck_esx_service
short_description: Manage the state of a service on ESX hosts.
description:
    - This module allows you to restart, start, or stop a service on ESX hosts.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.esx
options:
    esx_service_name:
        description:
            - The name of the service on the ESX host.
        required: true
    esx_service_state:
        description:
            - The desired state of service on the ESX host.
        choices:
            - start
            - stop
            - restart
        required: false
        type: str
        default: start
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""      
- name: Check ESX SSH Service (with strings)
  broadcom.vcf.precheck_esx_service:
      esx_hosts:
        - esx-01a.example.com
        - esx-02a.example.com
      esx_host_user: root
      esx_host_password: password
      esx_service_name: TSM-SSH
      esx_service_state: start
      validate_certs: False
      
- name: Check ESX SSH Service (with dicts)
  broadcom.vcf.precheck_esx_service:
      esx_hosts:
        - hostname: esx-01a.example.com
        - hostname: esx-02a.example.com
      esx_host_user: root
      esx_host_password: password
      esx_service_name: TSM-SSH
      esx_service_state: start
      validate_certs: False
"""

RETURN = r"""
msg:
    description: Service management result message
    returned: always
    type: str
    sample: >
        All ESX hosts have TSM-SSH restarted.
        Output Details: [{'Service': 'TSM-SSH has been restarted on esx-01a.example.com.', 'Policy Updated': False}]"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.esx_host import EsxHost


class EsxServicePrecheck:
    """This class provides methods to check services on the ESX host.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        esx_hosts (list or dict): A list or dictionary (with 'hostname' key) of
            hostnames or IP addresses for ESX hosts.
        esx_host_user (str): The username to authenticate with the ESX host.
        esx_host_password (str): The password to authenticate with the ESX host.
        esx_service_name (str): The name of the service on the ESX host.
        esx_service_state (str): The desired state of service on the ESX host.
        validate_certs (bool, optional): Whether to verify the SSL certificate of the
            ESX host. Defaults to False.

    Methods:
        get_content: Retrieves the content from the ESX host.
        get_service_manager: Retrieves the service manager for managing services.
        get_service_status: Retrieves the service status for a specific service.
        check_service_state_and_policy: Checks or updates the service state and policy.

    Raises:
        Exception: All built-in, non-system-exiting exceptions are derived from this
            class. All user-defined exceptions should also be derived from this class.
        ValueError: Raised when an operation or function receives an argument that has
            the right type but an inappropriate value.
    """

    def __init__(self, module, host):
        self.module = module
        if isinstance(host, str):
            self.esx_hostname = host
        else:
            self.esx_hostname = host.get("hostname")
        self.esx_host_user = module.params["esx_host_user"]
        self.esx_host_password = module.params["esx_host_password"]
        self.esx_service_name = module.params["esx_service_name"]
        self.esx_service_state = module.params["esx_service_state"]
        self.validate_certs = module.params["validate_certs"]
        self.api_client = EsxHost(
            self.esx_hostname,
            self.esx_host_user,
            self.esx_host_password,
            self.validate_certs,
        )

    def get_content(self):
        """Retrieves the content from the ESX host.

        Returns:
            object: The ESX host content object containing configuration and state
                information.

        Raises:
            Exception: If unable to connect to or retrieve content from the ESX host.
        """
        try:
            esx_connection = self.api_client.get_esx_content(
                self.esx_hostname, self.esx_host_user, self.esx_host_password, 443
            )
            return esx_connection
        except Exception as connection_error:
            raise Exception(connection_error)

    def get_service_manager(self, content: dict):
        """Retrieves the service manager for managing services.

        Args:
            content (dict): The ESX host content object (as returned by `get_content`)
                used by the API client.

        Returns:
            content.serviceManager (object): The service manager object used for
                managing services.
        """
        return self.api_client.get_service_manager(content)

    def get_service_status(self, service_manager: dict):
        """Retrieves the service status for a specific service.

        Args:
            service_manager (dict): The service manager object returned by
                `get_service_manager`.

        Returns:
            service_status (dict): The service status object containing the service
                name, policy, and state.

        Raises:
            Exception: If no service is found with the specified name.
        """
        service_status = self.api_client.get_service_status(
            service_manager, self.esx_service_name
        )

        if len(service_status) >= 1:
            return service_status[0]
        else:
            raise Exception(f"No service found with name {self.esx_service_name}!")

    def check_service_state_and_policy(
        self, service_manager: dict, service_status: dict
    ):
        """Checks or updates the service state and policy.

        Args:
            service_manager (dict): The service manager object returned by
                `get_service_manager`.
            service_status (dict): The service status object containing the service
                name, policy, and state.

        Returns:
            dict: A dictionary containing the result message indicating whether the
                service was started or stopped.

        Raises:
            Exception: If the service state cannot be set or the service policy cannot
                be updated.
        """
        # Update the policy, if needed.
        policy_updated = False

        if service_status.policy != "on":
            try:
                service_manager.UpdatePolicy(self.esx_service_name, "on")
                policy_updated = True
            except Exception as service_status_error:
                raise Exception(
                    {
                        "Service": f"{self.esx_service_name} failed to update policy on {self.esx_hostname}!",
                        "Policy Updated": policy_updated,
                        "Error": service_status_error,
                    }
                )

        # Set the verb.
        verb = (
            "stopped"
            if self.esx_service_state == "stop"
            else f"{self.esx_service_state}ed"
        )

        # Set the success message.
        success = {
            "Service": f"{self.esx_service_name} has been {verb} on {self.esx_hostname}.",
            "Policy Updated": policy_updated,
        }

        # Check the state of the service.
        service_state = self.esx_service_state.lower()
        try:
            if service_state == "start":
                if (
                    str(service_status.running).lower() == "true"
                    or service_status.running is True
                ):
                    return {
                        "Service": f"{self.esx_service_name} is already running on {self.esx_hostname}!",
                        "Policy Updated": policy_updated,
                    }  # Already running, nothing to do.
                service_manager.StartService(self.esx_service_name)
            elif service_state == "stop":
                service_manager.StopService(self.esx_service_name)
            elif service_state == "restart":
                service_manager.RestartService(self.esx_service_name)
            else:
                raise ValueError(
                    {
                        "Service": f"{self.esx_service_name} could not be {service_state}ed on {self.esx_hostname}!"
                    }
                )

            return success

        except ValueError as service_state_error:
            raise Exception(service_state_error)
        except Exception as service_state_error:
            raise Exception(
                {
                    "Service": f"{self.esx_service_name} failed to {service_state} on {self.esx_hostname}!",
                    "Policy Updated": policy_updated,
                    "Error": service_state_error,
                }
            )


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = dict(
        esx_hosts=dict(required=True, type="list", elements="raw"),
        esx_host_user=dict(required=True, type="str"),
        esx_host_password=dict(required=True, type="str", no_log=True),
        esx_service_name=dict(required=True, type="str"),
        esx_service_state=dict(required=True, type="str"),
        validate_certs=dict(required=False, type="bool", default=False),
    )

    output_array = []
    success = True
    module = AnsibleModule(supports_check_mode=True, argument_spec=parameters)
    verb = (
        "stopped"
        if module.params["esx_service_state"] == "stop"
        else f"{module.params['esx_service_state']}ed"
    )

    for host in module.params["esx_hosts"]:
        esx_service_check = EsxServicePrecheck(module, host)
        try:
            esx_content = esx_service_check.get_content()
            service_manager = esx_service_check.get_service_manager(esx_content)
            service_status = esx_service_check.get_service_status(service_manager)
            service_action = esx_service_check.check_service_state_and_policy(
                service_manager, service_status
            )
            output_array.append(service_action)
        except Exception as service_error:
            success = False
            output_array.append(service_error)

    # Generate the output.
    if success:
        module.exit_json(
            msg=(
                f"All ESX hosts have {module.params['esx_service_name']} {verb}. "
                f"Output Details: {output_array}"
            )
        )
    else:
        module.fail_json(
            msg=(
                f"One or more ESX hosts FAILED to {module.params['esx_service_state']} "
                f"the {module.params['esx_service_name']} service. "
                f"Check output details for more information: {output_array}"
            )
        )


if __name__ == "__main__":
    main()
