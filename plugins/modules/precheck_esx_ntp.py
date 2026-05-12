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
module: precheck_esx_ntp
short_description: Manage the NTP servers configured on ESX hosts.
description:
    - This module allows you to configure the NTP servers on ESX hosts
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.esx
options:
    esx_ntp_servers:
        description:
            - Array of strings. Contains the NTP servers.
        required: true
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Check ESX Host NTP Configuration (with strings)
  broadcom.vcf.precheck_esx_ntp:
      esx_hosts:
        - esx-01a.example.com
        - esx-02a.example.com
      esx_host_user: root
      esx_host_password: password
      esx_ntp_servers:
        - ntp-01a.example.com
        - ntp-02a.example.com
      validate_certs: False

- name: Check ESX Host NTP Configuration (with dicts)
  broadcom.vcf.precheck_esx_ntp:
      esx_hosts:
        - hostname: esx-01a.example.com
        - hostname: esx-02a.example.com
      esx_host_user: root
      esx_host_password: password
      esx_ntp_servers:
        - ntp-01a.example.com
        - ntp-02a.example.com
      validate_certs: False
"""

RETURN = r"""
msg:
    description: NTP server configuration result message
    returned: always
    type: str
    sample: >
        All ESX hosts have correct NTP servers.
        Output Details: ['Deleted [192.168.200.1, 192.168.200.2] and replaced with
        [192.168.100.1, 192.168.100.2] on ESX host: esx-01a.example.com.']
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.esx_host import EsxHost


class EsxServicePrecheck:
    """This class provides methods to set ntp servers on the ESX host.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        esx_hosts (list or dict): A list or dictionary (with 'hostname' key) of
            hostnames or IP addresses for ESX hosts.
        esx_host_user (str): The username to authenticate with the ESX host.
        esx_host_password (str): The password to authenticate with the ESX host.
        esx_ntp_servers (list): Array of strings. Contains the NTP servers.
        validate_certs (bool, optional): Whether to verify the SSL certificate of the
            ESX host. Defaults to False.

    Methods:
        get_content: Retrieves the content from the ESX host.
        get_date_time_manager: Retrieves the Date Time Manager for NTP configuration.
        check_and_config_ntp_servers: Checks and configures NTP servers on the ESX host.

    Raises:
        Exception: All built-in, non-system-exiting exceptions are derived from this
            class. All user-defined exceptions should also be derived from this class.
    """

    def __init__(self, module, host):
        self.module = module
        if isinstance(host, str):
            self.esx_hostname = host
        else:
            self.esx_hostname = host.get("hostname")
        self.esx_host_user = module.params["esx_host_user"]
        self.esx_host_password = module.params["esx_host_password"]
        self.esx_ntp_servers = module.params["esx_ntp_servers"]
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

    def get_date_time_manager(self, content: dict):
        """Retrieves the Date Time Manager for NTP configuration.

        Args:
            content (dict): The ESX host content object (as returned by `get_content`)
                used by the API client.

        Returns:
            object: The Date Time Manager object used for NTP server management.
        """
        return self.api_client.get_date_time_manager(content)

    def check_and_config_ntp_servers(self, date_time_manager: dict, ntp_servers: dict):
        """Checks and configures NTP servers on the ESX host.

        Compares the current NTP servers with the provided NTP servers and updates the configuration if they differ.

        Args:
            date_time_manager (dict): The Date Time Manager object containing NTP
                configuration.
            ntp_servers (dict): List of NTP server addresses to configure.

        Returns:
            dict: A dictionary containing the result message indicating whether NTP servers
                were updated or if they already matched the desired configuration.

        Raises:
            Exception: If there is an error configuring the NTP servers.
        """
        current_ntp_servers = date_time_manager.dateTimeInfo.ntpConfig.server

        if current_ntp_servers == ntp_servers:
            return {
                f"Current NTP Servers {list(current_ntp_servers)} match NTP servers "
                f"provided from input {ntp_servers} on ESX host: {self.esx_hostname}, "
                f"nothing to update."
            }
        else:
            try:
                self.api_client.configure_ntp_servers(date_time_manager, ntp_servers)
                return {
                    f"Deleted {list(current_ntp_servers)} and replaced with {ntp_servers} on ESX host {self.esx_hostname}."
                }
            except Exception as ntp_error:
                raise Exception(ntp_error)


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = dict(
        esx_hosts=dict(required=True, type="list", elements="raw"),
        esx_host_user=dict(required=True, type="str"),
        esx_host_password=dict(required=True, type="str", no_log=True),
        esx_ntp_servers=dict(required=False, type="list"),
        validate_certs=dict(required=False, type="bool", default=False),
    )

    output_array = []
    success = True
    module = AnsibleModule(supports_check_mode=True, argument_spec=parameters)

    for host in module.params["esx_hosts"]:
        esx_service_check = EsxServicePrecheck(module, host)
        try:
            esx_content = esx_service_check.get_content()
            date_time_manager = esx_service_check.get_date_time_manager(esx_content)
            ntp_servers = esx_service_check.check_and_config_ntp_servers(
                date_time_manager, module.params["esx_ntp_servers"]
            )
            output_array.append(ntp_servers)
        except Exception as esx_ntp_error:
            success = False
            output_array.append(esx_ntp_error)

    # Generate the output.
    if success:
        module.exit_json(
            msg=f"All ESX hosts have correct NTP servers. Output Details: {output_array}"
        )
    else:
        module.fail_json(
            msg=f"One or more ESX hosts FAILED to configure NTP servers. Check output details for more information: {output_array}"
        )


if __name__ == "__main__":
    main()
