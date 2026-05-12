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
module: sddc_manager_ceip_info
short_description: Retrieves the CEIP status from SDDC Manager.
description:
    - This module retrieves the Customer Experience Improvement Program (CEIP) status from SDDC Manager for VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Get CEIP Status
  broadcom.vcf.sddc_manager_ceip_info:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
  register: ceip_status

- name: Display CEIP Status
  ansible.builtin.debug:
    msg: "CEIP Status: {{ ceip_status.ceip.status }}, Instance ID: {{ ceip_status.ceip.instanceId }}"
"""

RETURN = r"""
msg:
    description: Human-readable message about the CEIP status
    returned: always
    type: str
    sample: "CEIP Status: ENABLED, Instance ID: 3f39d4a1-78d2-11e8-af85-f1cf26258cdc"
ceip:
    description: CEIP status information
    returned: on success
    type: dict
    sample:
        status: "ENABLED"
        instanceId: "3f39d4a1-78d2-11e8-af85-f1cf26258cdc"
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


class SddcManagerCeipInfo:
    """This class represents the CEIP status information retrieval in SDDC Manager.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager
            instance.
        sddc_manager_user (str): The username for authenticating with the SDDC
            Manager.
        sddc_manager_password (str): The password for authenticating with the SDDC
            Manager.

    Methods:
        get_ceip_status(self): Retrieves CEIP status from SDDC Manager.
        run(self): Runs the CEIP status retrieval process.

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

    def get_ceip_status(self):
        """Retrieves CEIP status from SDDC Manager."""
        try:
            api_response = self.api_client.get_ceip_status()
            status = api_response.get("status", "UNKNOWN")
            instance_id = api_response.get("instanceId", "N/A")
            self.module.exit_json(
                changed=False,
                msg=f"CEIP Status: {status}, Instance ID: {instance_id}",
                ceip=api_response,
            )

        except VcfApiException as e:
            self.module.fail_json(msg=f"Error retrieving CEIP status: {e}")

    def run(self):
        """Runs the CEIP status retrieval process."""
        self.get_ceip_status()


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

    ceip_info = SddcManagerCeipInfo(module)
    ceip_info.run()


if __name__ == "__main__":
    main()
