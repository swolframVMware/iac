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
module: sddc_manager_tasks_status_upgrade
short_description: Retrieves the status of tasks in SDDC Manager.
description:
    - This module retrieves the status of tasks in SDDC Manager for VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    task_id:
        description:
            - The ID of the task.
        required: true
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Monitor upgrade task
  broadcom.vcf.sddc_manager_tasks_status_upgrade:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    task_id: 12345678-1234-1234-1234-123456789012
    retries: 240
    delay: 30

- name: Monitor upgrade with custom retry settings
  broadcom.vcf.sddc_manager_tasks_status_upgrade:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    task_id: 12345678-1234-1234-1234-123456789012
    retries: 360
    delay: 60
"""

RETURN = r"""
msg:
    description: Status message about the task or error details
    returned: on failure
    type: str
    sample: "Task failed. Check the subtasks for more details."
meta:
    description: Task details returned from the SDDC Manager API
    returned: always
    type: dict
    sample:
        id: "12345678-1234-1234-1234-123456789012"
        name: "Upgrade vCenter Server"
        status: "COMPLETED"
        type: "UPGRADE"
        subTasks:
            - name: "Pre-upgrade validation"
              status: "SUCCESSFUL"
              description: "Validating upgrade prerequisites"
            - name: "Perform upgrade"
              status: "SUCCESSFUL"
              description: "Upgrading vCenter Server"
changed:
    description: Whether the module detected task completion
    returned: always
    type: bool
    sample: true
"""

import time

import requests
from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


class SddcManagerTaskProcessorForUpgrade:
    """The class is responsible for processing task and validation checks in the SDDC
    Manager.

    Args:
        module (object): The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager
            instance.
        task_id (str): The ID of the task to be processed.
        sddc_manager_user (str): The username for authenticating with the SDDC Manager.
        sddc_manager_password (str): The password for authenticating with the SDDC
            Manager.
        retries (int): The maximum number of retries for task processing.
        delay (int): The delay in seconds between retries.
        api_client (object): The SDDC Manager API client object.

    Methods:
        evaluate_task_status(payload_data): Evaluates the status of the task and handles
            the corresponding actions.
        evaluate_validation_status(payload_data): Evaluates the status of the validation
            checks and handles the corresponding actions.
        process_validation_task(api_call_method): Processes the validation task by
            making API calls and evaluating the status.
        process_task(): Processes the task based on the validation flag and the task
            type.

    Raises:
        VcfApiException: If an error occurs during the API call.
        Failed Task: If the task fails.
    """

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params["sddc_manager_hostname"]
        self.task_id = module.params["task_id"]
        self.sddc_manager_user = module.params["sddc_manager_user"]
        self.sddc_manager_password = module.params["sddc_manager_password"]
        self.validation = module.params["validation"]
        self.sddc_manager_task_type = module.params["sddc_manager_task_type"]
        self.retries = module.params.get("retries", 60)
        self.delay = module.params.get("delay", 10)
        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )

    def evaluate_task_status(self, payload_data):
        """Evaluates the status of the task and handles the corresponding actions."""
        if (
            payload_data["status"] == "FAILED" or payload_data["status"] == "Failed"
        ):  # Might need updating!
            error_check_list = [
                {"task_name": task["name"], "task_description": task["description"]}
                for task in payload_data["subTasks"]
                if task["status"] == "FAILED"
            ]
            self.module.fail_json(
                changed=False,
                meta=error_check_list,
                msg="Task failed. Check the subtasks for more details.",
            )
        elif (
            payload_data["status"] == "COMPLETED"
            or payload_data["status"] == "Successful"
        ):
            self.module.exit_json(changed=True, meta=payload_data)

    def evaluate_validation_status(self, payload_data):
        """Evaluates the status of the validation checks and handles the corresponding
        actions.
        """
        if (
            payload_data["executionStatus"] == "FAILED"
            or payload_data["executionStatus"] == "COMPLETED"
            and payload_data["resultStatus"] == "FAILED"
        ):  # resultStatus does not exist until executionStatus is COMPLETED or FAILED
            validation_check_list = payload_data["validationChecks"]
            self.module.fail_json(msg=validation_check_list)
            error_codes = []
            for validation_check in validation_check_list:
                if (
                    validation_check["resultStatus"] == "FAILED"
                    or validation_check["resultStatus"] == "SUCCEEDED"
                ):
                    if (
                        "errorResponse" in validation_check
                        and "nestedErrors" in validation_check["errorResponse"]
                    ):
                        for error in validation_check["errorResponse"]["nestedErrors"]:
                            if "errorCode" in error:
                                error_response = {
                                    "errorCode": error["errorCode"],
                                    "errorMessage": error["message"],
                                }
                                error_codes.append(error_response)
                    elif "errorResponse" in validation_check:
                        error_codes.append(validation_check["errorResponse"])
            self.module.fail_json(
                changed=False,
                meta={"error_codes": error_codes},
                msg="Validation Failed Please Check Errors",
            )
        elif payload_data["executionStatus"] == "COMPLETED":
            self.module.exit_json(changed=False, meta=payload_data)

    def process_validation_task(self, api_call_method):
        """Processes the validation task by making API calls and evaluating the status."""
        try:
            for attempt in range(self.retries):
                api_response = api_call_method(self.task_id)
                payload_data = api_response
                self.evaluate_validation_status(payload_data)
                time.sleep(self.delay)
            self.module.fail_json(
                msg="Exceeded maximum retries, validation did not complete within the allotted time."
            )
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error: {e}", status_code=e.status_code)

    def process_task(self):
        """Processes the task based on the validation flag and the task type."""
        try:
            for attempt in range(self.retries):
                try:
                    api_response = self.api_client.get_sddc_manager_task_by_id(
                        self.task_id
                    )
                    payload_data = api_response
                    self.evaluate_task_status(payload_data)
                    time.sleep(self.delay)
                except VcfApiException as e:
                    if e.status_code in [500] or e.status_code is None:
                        time.sleep(self.delay)
                    else:
                        self.module.fail_json(
                            msg=f"Error: {e}", status_code=e.status_code
                        )
                except requests.exceptions.ConnectionError:
                    time.sleep(self.delay)
            self.module.fail_json(
                msg="Exceeded maximum retries, task did not complete within the allotted time."
            )
        except Exception as e:
            self.module.fail_json(msg=f"Unexpected error occurred. Error: {e}")


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = {
        "sddc_manager_hostname": {"required": True, "type": "str"},
        "sddc_manager_user": {"required": True, "type": "str"},
        "sddc_manager_password": {"required": True, "type": "str", "no_log": True},
        "task_id": {"required": True, "type": "str"},
        "retries": {"required": False, "type": "int", "default": 240},
        "delay": {"required": False, "type": "int", "default": 30},
    }

    module = AnsibleModule(argument_spec=parameters, supports_check_mode=True)
    task_status = SddcManagerTaskProcessorForUpgrade(module)
    task_status.process_task()


if __name__ == "__main__":
    main()
