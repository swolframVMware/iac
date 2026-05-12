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
module: precheck_esx_connection
short_description: Checks the connection to ESX hosts.
description:
    - This module allows you to test the connection to ESX hosts.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.esx
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Check ESX Host Connection (with strings)
  broadcom.vcf.precheck_esx_connection:
      esx_hosts:
        - esx-01a.example.com
        - esx-02a.example.com
      esx_host_user: root
      esx_host_password: password
      validate_certs: False

- name: Check ESX Host Connection (with dicts)
  broadcom.vcf.precheck_esx_connection:
      esx_hosts:
        - hostname: esx-01a.example.com
        - hostname: esx-02a.example.com
      esx_host_user: root
      esx_host_password: password
      validate_certs: False
"""

RETURN = r"""
msg:
    description: ESX host connection test result message
    returned: always
    type: str
    sample: >
        All ESX hosts passed the connection test.
        Output Details: [{'ESX host esx-01a.example.com is online and accessible.'}]"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.esx_host import EsxHost


class EsxConnectionPrecheck:
    """This class provides methods to check the connection to the ESX host.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        esx_hosts (list or dict): A list or dictionary (with 'hostname' key) of
            hostnames or IP addresses for ESX hosts.
        esx_host_user (str): The username to authenticate with the ESX host.
        esx_host_password (str): The password to authenticate with the ESX host.
        validate_certs (bool, optional): Whether to verify the SSL certificate of the
            ESX host. Defaults to False.

    Methods:
        check_esx_connection: Checks the connection to the ESX host.

    Raises:
        Exception: All built-in, non-system-exiting exceptions are derived from this
            class. All user-defined exceptions should also be derived from this class.
        ConnectionRefusedError: A subclass of ConnectionError, raised when a connection
            attempt is refused by the peer.
        ConnectionError: A base class for connection-related issues.
    """

    def __init__(self, module, host):
        self.module = module
        if isinstance(host, str):
            self.esx_hostname = host
        else:
            self.esx_hostname = host.get("hostname")
        self.esx_host_user = module.params["esx_host_user"]
        self.esx_host_password = module.params["esx_host_password"]
        self.validate_certs = module.params["validate_certs"]
        self.api_client = EsxHost(
            self.esx_hostname,
            self.esx_host_user,
            self.esx_host_password,
            self.validate_certs,
        )

    def check_esx_connection(self):
        """Checks the ESX host connection.

        Returns:
            dict: A dictionary containing a success message if the ESX host is
                reachable and authentication is successful.

        Raises:
            ConnectionRefusedError: If the ESX host is reachable but authentication
                fails.
            ConnectionError: If the ESX host not reachable or other network/connection
                issues occurred.
        """
        esx_connection = self.api_client.can_connect(
            self.esx_hostname, self.esx_host_user, self.esx_host_password, 443
        )
        if not esx_connection:  # Cannot connect to the ESX host; checking status.
            esx_status = self.api_client.check_esx_ui()
            if esx_status:  # Received a 200 response. Credentials may be incorrect.
                raise ConnectionRefusedError(
                    {
                        "Host": f"{self.esx_hostname} login page is accessible, but cannot connect. Please check the credentials."
                    }
                )
            else:  # Other connection related issues.
                raise ConnectionError(
                    {
                        "Host": f"{self.esx_hostname} login page is inaccessible. Please check the connection."
                    }
                )
        if esx_connection:
            return {f"ESX host {self.esx_hostname} is online and accessible."}
        return None


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = dict(
        esx_hosts=dict(required=True, type="list", elements="raw"),
        esx_host_user=dict(required=True, type="str"),
        esx_host_password=dict(required=True, type="str", no_log=True),
        validate_certs=dict(required=False, type="bool", default=False),
    )

    output_array = []
    success = True
    module = AnsibleModule(supports_check_mode=True, argument_spec=parameters)

    for host in module.params["esx_hosts"]:
        esx_connection_check = EsxConnectionPrecheck(module, host)
        try:
            esx_output = esx_connection_check.check_esx_connection()
            output_array.append(esx_output)
        except Exception as esx_connection_error:
            success = False
            output_array.append(esx_connection_error)

    # Generate the output.
    if success:
        module.exit_json(
            msg=f"All ESX hosts passed the connection test. Output Details: {output_array}"
        )
    else:
        module.fail_json(
            msg=f"One or more ESX hosts FAILED the connection check. Check output details for more information: {output_array}"
        )


if __name__ == "__main__":
    main()
