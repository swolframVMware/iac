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
module: sddc_manager_ceip
short_description: Manages CEIP status in SDDC Manager.
description:
    - This module manages the Customer Experience Improvement Program (CEIP) status in SDDC Manager for VMware Cloud Foundation.
    - This module can enable or disable CEIP and monitors the task status.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    state:
        description:
            - The desired state of CEIP.
            - C(enabled) will enable CEIP.
            - C(disabled) will disable CEIP.
        required: true
        type: str
        choices:
            - enabled
            - disabled
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Enable CEIP
  broadcom.vcf.sddc_manager_ceip:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: enabled

- name: Disable CEIP
  broadcom.vcf.sddc_manager_ceip:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: disabled

- name: Enable CEIP and capture task ID for monitoring
  broadcom.vcf.sddc_manager_ceip:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: enabled
  register: ceip_result

- name: Enable CEIP with verbose output
  broadcom.vcf.sddc_manager_ceip:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: enabled
  register: result

- name: Display the result message
  ansible.builtin.debug:
    var: result.msg
"""

RETURN = r"""
msg:
    description: Status message about the operation or error details
    returned: on failure or when no change is needed
    type: str
    sample: "CEIP is already ENABLED."
task:
    description: Task information for the CEIP status update operation
    returned: on success when state changes
    type: dict
    sample:
        id: "3f39d4a1-78d2-11e8-af85-f1cf26258cdc"
        status: "IN_PROGRESS"
        isCancellable: false
        isRetryable: false
changed:
    description: Whether the module made changes
    returned: always
    type: bool
    sample: true
"""

import json

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


class SddcManagerCeip:
    """This class represents CEIP management in SDDC Manager.

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
        state (str): The desired state of CEIP (enabled or disabled).

    Methods:
        get_current_ceip_status(self): Retrieves current CEIP status from SDDC Manager.
        update_ceip_status(self): Updates CEIP status in SDDC Manager.
        run(self): Runs the CEIP management process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params["sddc_manager_hostname"]
        self.sddc_manager_user = module.params["sddc_manager_user"]
        self.sddc_manager_password = module.params["sddc_manager_password"]
        self.state = module.params["state"]
        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )

    def get_current_ceip_status(self):
        """Retrieves current CEIP status from SDDC Manager.

        Returns:
            str: The current CEIP status (ENABLED or DISABLED).
        """
        try:
            api_response = self.api_client.get_ceip_status()
            return api_response.get("status", "").upper()
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error retrieving current CEIP status: {e}")

    def update_ceip_status(self, desired_status):
        """Updates CEIP status in SDDC Manager.

        Args:
            desired_status (str): The desired CEIP status (ENABLE or DISABLE).

        Returns:
            dict: The task information for the CEIP status update.
        """
        try:
            payload = {"status": desired_status}
            api_response = self.api_client.update_ceip_status(json.dumps(payload))
            return api_response
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error updating CEIP status: {e}")

    def run(self):
        """Runs the CEIP management process."""
        # Map state to API status values
        desired_status_map = {
            "enabled": "ENABLE",
            "disabled": "DISABLE",
        }

        # Map for comparing current status
        current_status_map = {
            "enabled": "ENABLED",
            "disabled": "DISABLED",
        }

        desired_status = desired_status_map[self.state]
        expected_current_status = current_status_map[self.state]

        # Get current CEIP status
        current_status = self.get_current_ceip_status()

        # Check if change is needed
        if current_status == expected_current_status:
            self.module.exit_json(
                changed=False,
                msg=f"CEIP is already {expected_current_status}.",
            )

        # Check mode
        if self.module.check_mode:
            self.module.exit_json(
                changed=True,
                msg=f"Check Mode: Would change CEIP status from {current_status} to {expected_current_status}.",
            )

        # Update CEIP status
        task_response = self.update_ceip_status(desired_status)

        self.module.exit_json(
            changed=True,
            msg=f"Successfully submitted task to update CEIP to {expected_current_status} state. Task ID: {task_response.get('id')}",
            task=task_response,
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
        state=dict(
            required=True,
            type="str",
            choices=["enabled", "disabled"],
        ),
    )

    module = AnsibleModule(argument_spec=parameters, supports_check_mode=True)

    ceip = SddcManagerCeip(module)
    ceip.run()


if __name__ == "__main__":
    main()
