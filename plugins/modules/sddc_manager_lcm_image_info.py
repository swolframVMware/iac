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
module: sddc_manager_lcm_image_info
short_description: Retrieves the lifecycle management image information from SDDC Manager.
description:
    - This module retrieves lifecycle management image information from SDDC Manager for VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    lcm_image:
        description:
            - The name of the lifecycle management image.
        required: true
        type: str
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Get lifecycle management image information from SDDC Manager
  broadcom.vcf.sddc_manager_lcm_image_info:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    lcm_image: vcenter-9.0.0
"""

RETURN = r"""
msg:
    description: Error message if the lifecycle management image is not found
    returned: on failure
    type: str
    sample: >
        No lifecycle management image named 'vcenter-9.0.0' in SDDC Manager sddc-manager.example.com.
        Error: ...
meta:
    description: Lifecycle management image information response from SDDC Manager API
    returned: on success
    type: dict
    sample:
        vcenter-9.0.0:
            id: "12345678-1234-1234-1234-123456789012"
            personalityName: "vcenter-9.0.0"
            version: "9.0.0.12456-12345678"
            imageType: "INSTALL"
            status: "AVAILABLE"
changed:
    description: Whether the module made changes
    returned: always
    type: bool
    sample: true
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


class SddcManagerLcmImageInfo:
    """This class represents the lifecycle management image information from SDDC Manager.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager
            instance.
        sddc_manager_user (str): The username for authenticating with the SDDC Manager.
        sddc_manager_password (str): The password for authenticating with the SDDC
            Manager.
        lcm_image (str): The name of the lifecycle management image.

    Methods:
        get_lcm_image(self): Retrieves the lifecycle management image information from
            SDDC Manager.
        run(self): Runs the lifecycle management image information process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params["sddc_manager_hostname"]
        self.sddc_manager_user = module.params["sddc_manager_user"]
        self.sddc_manager_password = module.params["sddc_manager_password"]
        self.lcm_image = module.params["lcm_image"]
        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )

    def get_lcm_image_info(self):
        """Retrieves lifecycle management image information from SDDC Manager."""
        try:
            api_response = self.api_client.get_lifecycle_manager_image_by_name(
                self.lcm_image
            )
            response = api_response

            if not response["elements"]:
                self.module.fail_json(
                    msg=f"No lifecycle management image named '{self.lcm_image}' in SDDC Manager {self.sddc_manager_hostname}."
                )
            else:
                return response["elements"][0]
        except VcfApiException as e:
            self.module.fail_json(
                msg=f"Failed to retrieve lifecycle management image information from SDDC Manager {self.sddc_manager_hostname}. Error: {e}"
            )

    def run(self):
        """Retrieves lifecycle management image information."""
        image = self.get_lcm_image_info()

        self.module.exit_json(
            changed=False,
            meta={image["personalityName"]: image},
        )


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = dict(
        sddc_manager_hostname=dict(required=True, type="str"),
        sddc_manager_user=dict(required=True, type="str"),
        sddc_manager_password=dict(required=True, type="str", no_log=True),
        lcm_image=dict(required=True, type="str"),
    )

    module = AnsibleModule(argument_spec=parameters, supports_check_mode=True)

    lcm_image_info = SddcManagerLcmImageInfo(module)
    lcm_image_info.run()


if __name__ == "__main__":
    main()
