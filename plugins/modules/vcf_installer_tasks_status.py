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
module: vcf_installer_tasks_status
short_description: Retrieves the status of tasks and validations in VCF Installer.
description:
    - This module retrieves the status of tasks and validations in VCF Installer for VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.vcf_installer
options:
    task_id:
        description:
            - The ID of the task or validation to monitor.
            - For validations, this is the validation ID returned from the validate_sddc endpoint.
            - For tasks, this is the task ID returned from deployment or other operations.
        required: true
        type: str
    validation:
        description:
            - Whether to monitor a validation (true) or a deployment task (false).
            - When true, monitors SDDC validation status via the validations endpoint.
            - When false, monitors task status via the tasks endpoint.
        required: true
        type: bool
    timeout:
        description:
            - Total wall-clock seconds to wait for the task or validation to reach a
              terminal state before failing.
            - The module polls every I(poll_interval) seconds and continues regardless
              of how long individual subtasks take.
            - Set to C(0) to wait indefinitely until the operation succeeds or fails.
            - The default of C(43200) covers environments that take up to 12 hours.
        required: false
        type: int
        default: 43200
    poll_interval:
        description:
            - Seconds to wait between status polling attempts.
        required: false
        type: int
        default: 10
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Monitor Validation Status
  broadcom.vcf.vcf_installer_tasks_status:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    task_id: 12345678-1234-1234-1234-123456789012
    validation: true
    poll_interval: 10

- name: Monitor Task Status
  broadcom.vcf.vcf_installer_tasks_status:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    task_id: 12345678-1234-1234-1234-123456789012
    validation: false
    poll_interval: 30

- name: Monitor Task Status with Custom Timeout
  broadcom.vcf.vcf_installer_tasks_status:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    task_id: 12345678-1234-1234-1234-123456789012
    validation: false
    timeout: 86400
    poll_interval: 60
"""

RETURN = r"""
msg:
    description: Status message about the task or validation completion/failure
    returned: on completion or failure
    type: str
    sample: "Successfully completed <task>."
meta:
    description: Task or validation details returned from the VCF Installer API
    returned: always
    type: dict
    sample:
        id: "12345678-1234-1234-1234-123456789012"
        name: "Deploy SDDC"
        status: "COMPLETED"
        type: "SDDC_DEPLOYMENT"
        creationTimestamp: "2026-02-26T10:00:00.000Z"
changed:
    description: Whether the task completed successfully (true for completed tasks, false for validations)
    returned: always
    type: bool
    sample: true
"""

import time

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.vcf_installer import (
    VcfInstallerApiClient,
)


class VcfInstallerTaskProcessor:
    """The class represents the task processor for VCF Installer. It handles the task
    processing and validation checks.

    Args:
        module (object): The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        vcf_installer_hostname (str): The hostname or IP address of the VCF Installer instance.
        vcf_installer_user (str): The username for authenticating with the VCF Installer instance.
        vcf_installer_password (str): The password for authenticating with the VCF Installer instance.
        task_id (str): The ID of the task to be processed.
        validation (bool): Flag indicating whether to perform validation checks or not.
        timeout (int): Total wall-clock seconds to wait for a task; 0 = no limit.
        poll_interval (int): Seconds between polling attempts.
        api_client (object): The VCF Installer API client object.

    Methods:
        evaluate_task_status(payload_data): Evaluates the status of the task and handles
            the corresponding actions.
        evaluate_validation_status(payload_data): Evaluates the status of the validation
            checks and handles the corresponding actions.
        run(): Processes the task based on the validation flag and the task type.

    Raises:
        VcfApiException: If an error occurs during the API call.
        Failed Task: If the task fails.
    """

    def __init__(self, module):
        self.module = module
        self.vcf_installer_hostname = module.params["vcf_installer_hostname"]
        self.vcf_installer_user = module.params["vcf_installer_user"]
        self.vcf_installer_password = module.params["vcf_installer_password"]
        self.task_id = module.params["task_id"]
        self.validation = module.params["validation"]
        self.timeout = module.params["timeout"]
        self.poll_interval = module.params["poll_interval"]
        self.api_client = VcfInstallerApiClient(
            self.vcf_installer_hostname,
            self.vcf_installer_user,
            self.vcf_installer_password,
        )

    def evaluate_task_status(self, payload_data):
        """Evaluates the status of the task and handles the corresponding actions."""
        status = payload_data.get("status", "").upper()

        if not status:
            self.module.exit_json(
                changed=True, msg="Task completed.", meta=payload_data
            )

        if status == "FAILED":
            error_check_list = []
            if "subTasks" in payload_data:
                error_check_list = [
                    {"task_name": task["name"], "task_description": task["description"]}
                    for task in payload_data["subTasks"]
                    if task.get("status") == "FAILED"
                ]
            self.module.fail_json(
                changed=False,
                meta={"error_codes": error_check_list, "task": payload_data},
                msg="Task failed. Check the subtasks for more details.",
            )
        elif status in ("SUCCESSFUL", "COMPLETED", "SUCCEEDED"):
            success_msg = self._generate_success_message(payload_data)
            self.module.exit_json(changed=True, msg=success_msg, meta=payload_data)
        elif status in ("IN_PROGRESS", "IN PROGRESS", "PENDING", "RUNNING"):
            return
        elif status in ("CANCELLED", "SKIPPED"):
            self.module.exit_json(
                changed=False, msg=f"Task was {status.lower()}.", meta=payload_data
            )
        else:
            return

    def _generate_success_message(self, payload_data):
        """Generates a success message based on task type and results."""
        task_name = payload_data.get("name", "Task")
        return f"Successfully completed {task_name}."

    def evaluate_validation_status(self, payload_data):
        """Evaluates the status of the validation checks and handles the corresponding
        actions.
        """
        execution_status = payload_data.get("executionStatus", "").upper()
        result_status = payload_data.get("resultStatus", "").upper()

        if execution_status == "FAILED" or (
            execution_status == "COMPLETED" and result_status == "FAILED"
        ):
            validation_check_list = payload_data["validationChecks"]
            error_codes = []
            for validation_check in validation_check_list:
                check_result = validation_check.get("resultStatus", "").upper()
                if check_result in ("FAILED", "SUCCEEDED"):
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
                msg="Validation failed. Check the validation checks for more details.",
            )
        elif execution_status == "COMPLETED":
            self.module.exit_json(changed=False, meta=payload_data)

    def run(self):
        """Processes the task based on the validation flag and the task type."""
        try:
            start_time = time.monotonic()

            while True:
                if self.validation:
                    api_response = self.api_client.get_sddc_validation(self.task_id)
                    self.evaluate_validation_status(api_response)
                else:
                    api_response = self.api_client.get_task_by_id(self.task_id)
                    # evaluate_task_status calls exit_json / fail_json on terminal states.
                    self.evaluate_task_status(api_response)

                # Still in progress — check the wall-clock timeout before sleeping.
                if self.timeout > 0:
                    elapsed = time.monotonic() - start_time
                    if elapsed >= self.timeout:
                        last_status = (
                            api_response.get("executionStatus", "UNKNOWN")
                            if self.validation
                            else api_response.get("status", "UNKNOWN")
                        )
                        self.module.fail_json(
                            msg=(
                                f"Operation timed out after {int(elapsed)}s "
                                f"(timeout={self.timeout}s). "
                                f"Last status: {last_status}. "
                                "The operation may still be running on the appliance."
                            ),
                            meta=api_response,
                        )

                time.sleep(self.poll_interval)
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error: {e}", status_code=e.status_code)


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = {
        "vcf_installer_hostname": {"required": True, "type": "str"},
        "vcf_installer_user": {"required": True, "type": "str"},
        "vcf_installer_password": {"required": True, "type": "str", "no_log": True},
        "task_id": {"required": True, "type": "str"},
        "validation": {"required": True, "type": "bool"},
        "timeout": {"required": False, "type": "int", "default": 43200},
        "poll_interval": {"required": False, "type": "int", "default": 10},
    }

    module = AnsibleModule(
        argument_spec=parameters,
        supports_check_mode=True,
    )
    task_processor = VcfInstallerTaskProcessor(module)
    task_processor.run()


if __name__ == "__main__":
    main()
