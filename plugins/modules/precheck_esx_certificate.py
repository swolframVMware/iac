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
module: precheck_esx_certificate
short_description: Check the common name of the certificate on ESX hosts.
description:
    - This module allows you to check the common name of the certificate on ESX hosts.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.esx
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Check ESX Host Connection (with strings)
  broadcom.vcf.precheck_esx_certificate:
      esx_hosts:
        - esx-01a.example.com
        - esx-02a.example.com
      esx_host_user: root
      esx_host_password: password
      validate_certs: False

- name: Check ESX Host Certificate (with dicts)
  broadcom.vcf.precheck_esx_certificate:
      esx_hosts:
        - hostname: esx-01a.example.com
        - hostname: esx-02a.example.com
      esx_host_user: root
      esx_host_password: password
      validate_certs: False
"""

RETURN = r"""
msg:
    description: ESX host certificate common name validation result message.
    returned: always
    type: str
    sample: >
        All ESX hosts have the correct common name.
        Output Details: [{'The common name on certificate esx-01a.example.com matches
        the ESX host hostname esx-01a.example.com.'}]
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.esx_host import EsxHost


class EsxCertificatePrecheck:
    """This class provides methods to check certificate on the ESX host.

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
        get_content: Retrieves the content for an ESX host.
        get_cert_cn: Retrieves the common name from the ESX host certificate and
            validates it.
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

    def get_cert_cn(self, content: dict):
        """Retrieves the common name from the ESX host certificate and validates it.

        Retrieves the certificate common name and compares it with the ESX host hostname
        to ensure they match.

        Args:
            content (dict): The ESX host content object (as returned by `get_content`)
                used by the API client.

        Returns:
            dict: A dictionary containing a success message if the common name matches
                the ESX host hostname.

        Raises:
            ValueError: If the common name does not match the ESX host hostname.
            Exception: If there is an error retrieving the certificate common name.
        """
        try:
            common_name = self.api_client.get_certificate_common_name(content)
            if common_name == self.esx_hostname:
                return {
                    f"The common name on certificate {common_name} matches the ESX host hostname {self.esx_hostname}."
                }
            raise ValueError(
                {
                    f"The common name on certificate {common_name} does not match the ESX host hostname {self.esx_hostname}."
                }
            )
        except Exception as cert_cn_error:
            raise Exception(cert_cn_error)


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
        esx_certificate_check = EsxCertificatePrecheck(module, host)
        try:
            esx_content = esx_certificate_check.get_content()
            common_name = esx_certificate_check.get_cert_cn(esx_content)
            output_array.append(common_name)
        except Exception as esx_cert_error:
            success = False
            output_array.append(esx_cert_error)

    # Generate the output.
    if success:
        module.exit_json(
            msg=f"All ESX hosts have the correct common bame. Output Details: {output_array}"
        )
    else:
        module.fail_json(
            msg=f"One or more ESX hosts have an incorrect common name. Check output details for more information: {output_array}"
        )


if __name__ == "__main__":
    main()
