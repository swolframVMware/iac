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
module: vcf_installer_info
short_description: Retrieves appliance information from VCF Installer.
description:
    - This module retrieves appliance information from the VCF Installer instance.
    - Returns the appliance role and version.
    - Can be used to check if the VCF Installer API is available.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.vcf_installer
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Check if VCF Installer API is Available
  broadcom.vcf.vcf_installer_info:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: "{{ vcf_installer_local_password }}"
  register: installer_info
  until: installer_info.available
  retries: 30
  delay: 10

- name: Get VCF Installer Appliance Information
  broadcom.vcf.vcf_installer_info:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
  register: installer_info

- name: Display Appliance Information
  ansible.builtin.debug:
    msg: "VCF Installer: {{ installer_info.version }}"
"""

RETURN = r"""
available:
    description: Whether the VCF Installer API is available
    returned: always
    type: bool
    sample: true
appliance_info:
    description: Appliance information
    returned: on success
    type: dict
    sample:
        role: "VcfInstaller"
        version: "9.0.2.0.25151285"
role:
    description: Appliance role
    returned: on success
    type: str
    sample: "VcfInstaller"
version:
    description: Appliance version
    returned: on success
    type: str
    sample: "9.0.2.0.25151285"
msg:
    description: Human-readable message about the API status
    returned: always
    type: str
    sample: "VCF Installer API is available."
changed:
    description: Whether the module made changes
    returned: always
    type: bool
    sample: false
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.vcf_installer import (
    VcfInstallerApiClient,
)


class VcfInstallerInfo:
    """This class represents VCF Installer appliance information retrieval.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        vcf_installer_hostname (str): The hostname or IP address of the VCF Installer instance.
        vcf_installer_user (str): The username for authenticating with the VCF Installer instance.
        vcf_installer_password (str): The password for authenticating with the VCF Installer instance.

    Methods:
        get_appliance_info(self): Retrieves appliance information from VCF Installer.
        run(self): Runs the appliance information retrieval process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.vcf_installer_hostname = module.params["vcf_installer_hostname"]
        self.vcf_installer_user = module.params["vcf_installer_user"]
        self.vcf_installer_password = module.params["vcf_installer_password"]
        self.api_client = VcfInstallerApiClient(
            self.vcf_installer_hostname,
            self.vcf_installer_user,
            self.vcf_installer_password,
        )

    def get_appliance_info(self):
        """Retrieves appliance information from VCF Installer."""
        try:
            api_response = self.api_client.get_appliance_info()
            role = api_response.get("role", "Unknown")
            version = api_response.get("version", "Unknown")

            self.module.exit_json(
                changed=False,
                available=True,
                msg=f"VCF Installer API is available.",
                appliance_info=api_response,
                role=role,
                version=version,
            )

        except VcfApiException as e:
            self.module.exit_json(
                changed=False,
                available=False,
                msg=f"VCF Installer API is not available: {e}",
            )

    def run(self):
        """Runs the appliance information retrieval process."""
        self.get_appliance_info()


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = dict(
        vcf_installer_hostname=dict(required=True, type="str"),
        vcf_installer_user=dict(required=True, type="str"),
        vcf_installer_password=dict(required=True, type="str", no_log=True),
    )

    module = AnsibleModule(argument_spec=parameters, supports_check_mode=True)

    info = VcfInstallerInfo(module)
    info.run()


if __name__ == "__main__":
    main()
