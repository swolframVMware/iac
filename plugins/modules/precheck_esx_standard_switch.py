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
module: precheck_esx_standard_switch
short_description: Manage the standard switch configuration on ESX hosts.
description:
    - This module allows you to configure the standard switch on ESX hosts.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.esx
options:
    virtual_standard_switch:
        description:
            - Standard switch settings. Contains the name and MTU.
        required: true
        type: dict
    validate_certs:
        description:
            - Whether to verify the SSL certificate of the ESX host.
        required: true
        type: bool
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Check ESX Host Standard Switch Configuration (with strings)
  broadcom.vcf.precheck_esx_standard_switch:
      esx_hosts:
        - esx-01a.example.com
        - esx-02a.example.com
      esx_host_user: root
      esx_host_password: password
      virtual_standard_switch:
        mtu: 1500
        name: vSwitch0
      validate_certs: False
-+
- name: Check ESX Host Standard Switch Configuration (with dicts)
  broadcom.vcf.precheck_esx_standard_switch:
      esx_hosts:
        - hostname: esx-01a.example.com
        - hostname: esx-02a.example.com
      esx_host_user: root
      esx_host_password: password
      virtual_standard_switch:
        mtu: 1500
        name: vSwitch0
      validate_certs: False
"""

RETURN = r"""
msg:
    description: Virtual standard switch MTU configuration result message
    returned: always
    type: str
    sample: >
        All ESX hosts have correct MTU on the standard switch.
        Output Details: [{'Current MTU 1500 already matches input MTU of 1500 on
        vSwitch: vSwitch0 on ESX Host: esx-01a.example.com. No update needed.'}]
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.esx_host import EsxHost


class EsxVssPrecheck:
    """This class provides methods to update standard switches on ESX hosts.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        esx_hosts (list or dict): A list or dictionary (with 'hostname' key) of
            hostnames or IP addresses for ESX hosts.
        esx_host_user (str): The username to authenticate with the ESX host.
        esx_host_password (str): The password to authenticate with the ESX host.
        virtual_standard_switch (dict): The standard switch data, including the name
            and MTU.
        validate_certs (bool, optional): Whether to verify the SSL certificate of the
            ESX host. Defaults to False.

    Methods:
        get_content: Retrieves the content from the ESX host.
        get_virtual_standard_switch_mtu: Retrieves the MTU information for a standard
            switch on the ESX host.
        update_virtual_standard_switch_mtu: Updates the MTU configuration for a standard
            switch on the ESX host.

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
        self.virtual_standard_switch = module.params["virtual_standard_switch"]
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

    def get_virtual_standard_switch_mtu(
        self, virtual_standard_switch: dict, content: dict
    ):
        """Retrieves the MTU information for a standard switch on the ESX host.

        Args:
            virtual_standard_switch (dict): The standard switch data, including the name
                and MTU.
            content (dict): The ESX host content object (as returned by `get_content`)
                used by the API client.

        Returns:
            dict: The standard switch data, including the name and MTU.

        Raises:
            ValueError: If the `name` key is missing from `virtual_standard_switch`.
            Exception: Propagates any exceptions raised by the underlying `EsxHost`
                client when retrieving the MTU of the standard switch.
        """
        if "name" not in virtual_standard_switch:
            raise ValueError(
                f"Missing 'name' key in virtual_standard_switch input. Inputs provided: {virtual_standard_switch}"
            )

        return self.api_client.get_virtual_standard_switch_mtu(
            virtual_standard_switch, content
        )

    def update_virtual_standard_switch_mtu(
        self, virtual_standard_switch: dict, vswitch_info: dict, content: dict
    ):
        """Updates the MTU configuration for a standard switch on the ESX host.

        Args:
            virtual_standard_switch (dict): The standard switch data, including the name
                and MTU.
            vswitch_info (dict): The standard switch data, including the name and MTU.
            content (dict): The ESX host content object (as returned by `get_content`)
                used by the API client.

        Returns:
            set: A set containing the success or failure message.

        Raises:
            ValueError: If the `name` or `mtu` keys are missing from
                `virtual_standard_switch`.
            Exception: Propagates any exceptions raised by the underlying `EsxHost`
                client when updating the MTU of the standard switch.
        """
        if (
            "name" not in virtual_standard_switch
            or "mtu" not in virtual_standard_switch
        ):
            raise ValueError(
                f"Missing required keys ('name', 'mtu') in virtual_standard_switch input. Inputs provided: {virtual_standard_switch}"
            )
        elif not isinstance(virtual_standard_switch["mtu"], int):
            raise ValueError(
                f"MTU provided in virtual_standard_switch input is not an integer. Inputs provided: {virtual_standard_switch}"
            )

        current_vswitch_mtu = vswitch_info["mtu"]

        if current_vswitch_mtu == virtual_standard_switch["mtu"]:
            return {
                f"Current MTU {current_vswitch_mtu} already matches input MTU of "
                f"{virtual_standard_switch['mtu']} on vSwitch: "
                f"{virtual_standard_switch['name']} on ESX Host: {self.esx_hostname}. "
                f"No update needed."
            }
        else:
            try:
                self.api_client.update_virtual_standard_switch_mtu(
                    virtual_standard_switch, content
                )
                return {
                    f"Updated MTU for {virtual_standard_switch['name']} from "
                    f"{current_vswitch_mtu} to {virtual_standard_switch['mtu']} "
                    f"on ESX Host: {self.esx_hostname}"
                }
            except Exception as vss_mtu_error:
                raise Exception(vss_mtu_error)


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = dict(
        esx_hosts=dict(required=True, type="list", elements="raw"),
        esx_host_user=dict(required=True, type="str"),
        esx_host_password=dict(required=True, type="str", no_log=True),
        virtual_standard_switch=dict(required=True, type="dict"),
        validate_certs=dict(required=False, type="bool", default=False),
    )

    output_array = []
    success = True
    module = AnsibleModule(supports_check_mode=True, argument_spec=parameters)

    for host in module.params["esx_hosts"]:
        esx_vss_check = EsxVssPrecheck(module, host)
        try:
            esx_content = esx_vss_check.get_content()
            virtual_standard_switch_info = (
                esx_vss_check.get_virtual_standard_switch_mtu(
                    module.params["virtual_standard_switch"], esx_content
                )
            )
            virtual_standard_switch_mtu = (
                esx_vss_check.update_virtual_standard_switch_mtu(
                    module.params["virtual_standard_switch"],
                    virtual_standard_switch_info,
                    esx_content,
                )
            )
            output_array.append(virtual_standard_switch_mtu)
        except Exception as esx_vss_mtu_error:
            success = False
            output_array.append(esx_vss_mtu_error)

    # Generate the output.
    if success:
        module.exit_json(
            msg=f"All ESX hosts have correct MTU on the standard switch. Output Details: {output_array}"
        )
    else:
        module.fail_json(
            msg=f"One or more ESX hosts FAILED to update MTU on the standard switch. Check output details for more information: {output_array}"
        )


if __name__ == "__main__":
    main()
