# -*- coding: utf-8 -*-
#
# Copyright (c) Broadcom. All Rights Reserved.
# The term "Broadcom" refers solely to the Broadcom Inc. corporate affiliate that
# distributes this software.
#
# You are hereby granted a non-exclusive, worldwide, royalty-free license under
# Broadcom's copyrights to use, copy, modify, and distribute this software in source
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
module: sddc_manager_certificate_authority_info
short_description: Retrieves the certificate authority configuration from SDDC Manager.
description:
    - This module retrieves the certificate authority configuration from SDDC Manager for VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Get Certificate Authority Configuration
  broadcom.vcf.sddc_manager_certificate_authority_info:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
  register: ca_config

- name: Display Status Message
  ansible.builtin.debug:
    msg: "{{ ca_config.msg }}"

- name: Display Configuration Information
  ansible.builtin.debug:
    var: ca_config.certificate_authority
"""

RETURN = r"""
certificate_authorities:
    description: List of certificate authority configurations (both OpenSSL and Microsoft).
    returned: always
    type: list
    sample:
        - id: "Microsoft"
          username: "svc-vcf-ca"
          serverUrl: "https://ca.example.com/certsrv"
          templateName: "VMware"
        - id: "OpenSSL"
          commonName: "sddc-manager.example.com"
          country: "US"
          state: "California"
          locality: "San Francisco"
          organization: "Rainpole"
          organizationUnit: "Platform Engineering"
changed:
    description: Whether the module made changes.
    returned: always
    type: bool
    sample: false
msg:
    description: A list of status messages describing the certificate authority configuration state.
    returned: always
    type: list
    sample:
        - "Microsoft CA: ca.example.com"
        - "OpenSSL CA: sddc-manager.example.com"
    alternatives:
        - ["No certificate authority has been configured."]
        - ["Microsoft CA: ca.example.com"]
        - ["OpenSSL CA: sddc-manager.example.com"]
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


class SddcManagerCertificateAuthorityInfo:
    """This class represents the certificate authority configuration information retrieval in SDDC Manager.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager instance.
        sddc_manager_user (str): The username for authenticating with the SDDC Manager instance.
        sddc_manager_password (str): The password for authenticating with the SDDC Manager instance.

    Methods:
        get_ca_settings(self): Retrieves the certificate authority configuration from SDDC Manager.
        run(self): Runs the certificate authority configuration retrieval process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params["sddc_manager_hostname"]
        self.sddc_manager_user = module.params["sddc_manager_user"]
        self.sddc_manager_password = module.params["sddc_manager_password"]
        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )

    def get_ca_settings(self):
        """Retrieves certificate authority configuration from SDDC Manager."""
        try:
            api_response = self.api_client.get_certificate_authority()

            ca_configs = []

            if api_response:
                if isinstance(api_response, dict):
                    if "elements" in api_response:
                        elements = api_response.get("elements", [])
                        ca_configs = elements if elements else []
                    else:
                        ca_configs = [api_response]
                elif isinstance(api_response, list):
                    ca_configs = api_response

            msg = self._build_ca_message_list(ca_configs)

            self.module.exit_json(
                changed=False,
                certificate_authorities=ca_configs,
                msg=msg,
            )

        except VcfApiException as e:
            self.module.fail_json(
                msg=f"Error retrieving certificate authority configuration: {e}"
            )

    def _build_ca_message_list(self, ca_configs):
        """Builds a list of messages based on certificate authority configurations.

        Args:
            ca_configs: List of certificate authority configurations.

        Returns:
            list: A list of status messages describing the certificate authority configuration.
        """
        if not ca_configs or len(ca_configs) == 0:
            return ["No certificate authority has been configured."]

        messages = []

        for ca_config in ca_configs:
            ca_type = ca_config.get("id") or ca_config.get("caType")

            if ca_type == "OpenSSL":
                common_name = ca_config.get("commonName", "Unknown")
                messages.append(f"OpenSSL CA: {common_name}")
            elif ca_type == "Microsoft":
                server_url = ca_config.get("serverUrl", "Unknown")
                hostname = (
                    server_url.replace("https://", "")
                    .replace("http://", "")
                    .split("/")[0]
                )
                messages.append(f"Microsoft CA: {hostname}")
            else:
                messages.append(f"Unknown CA type: {ca_type}")

        return messages

    def run(self):
        """Runs the certificate authority configuration retrieval process."""
        self.get_ca_settings()


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = dict(
        sddc_manager_hostname=dict(required=True, type="str"),
        sddc_manager_user=dict(required=True, type="str"),
        sddc_manager_password=dict(required=True, type="str", no_log=True),
    )

    module = AnsibleModule(argument_spec=parameters, supports_check_mode=True)

    ca_info = SddcManagerCertificateAuthorityInfo(module)
    ca_info.run()


if __name__ == "__main__":
    main()
