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
module: sddc_manager_vcenter_info
short_description: Retrieves information for vCenter instances from SDDC Manager.
description:
    - This module retrieves information for vCenter instances from SDDC Manager for VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Get vCenter information from SDDC Manager
  broadcom.vcf.sddc_manager_vcenter_info:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
"""


RETURN = r"""
msg:
    description: Error message if no vCenter instances are found
    returned: on failure
    type: str
    sample: "No vCenter instances found in SDDC Manager sddc-manager.example.com."
meta:
    description: vCenter information response from SDDC Manager API
    returned: on success
    type: dict
    sample:
        elements:
            - id: "12345678-1234-1234-1234-123456789012"
              fqdn: "sfo-m01-vc01.example.com"
              version: "9.0.0.0-12345678"
              status: "ACTIVE"
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
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


class SddcManagervCenterInfo:
    """This class represents the vCenter information process in SDDC Manager.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager
            instance.
        sddc_manager_user (str): The username for authenticating with the SDDC Manager.
        sddc_manager_password (str): The password for authenticating with the SDDC
            Manager.

    Methods:
        get_vcenter_info(self): Retrieves the vCenter information from SDDC Manager.
        run(self): Runs the vCenter information process.

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

    def get_vcenter_info(self):
        """Retrieves the vCenter information from SDDC Manager."""
        try:
            api_response = self.api_client.get_vcenters_info()
            response = api_response

            if not response["elements"]:
                self.module.fail_json(
                    msg=f"No vCenter instances found in SDDC Manager {self.sddc_manager_hostname}."
                )
            else:
                self.module.exit_json(changed=False, meta=response)

        except VcfApiException as e:
            self.module.fail_json(msg=f"Error: {e}")

    def run(self):
        """Runs the vCenter information retrieval process."""
        self.get_vcenter_info()


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

    vcenter_info = SddcManagervCenterInfo(module)
    vcenter_info.run()


if __name__ == "__main__":
    main()
