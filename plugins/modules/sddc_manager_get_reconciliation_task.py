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
module: sddc_manager_get_reconciliation_task
short_description: Retrieves the reconciliation task information from SDDC Manager.
description:
    - This module retrieves reconciliation task information from SDDC Manager in VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    task_id:
        description:
            - The ID of the reconciliation task.
        required: true
        type: str
    retries:
        description:
            - Number of retry attempts.
        required: false
        type: int
        default: 60
    delay:
        description:
            - Delay in seconds between retries.
        required: false
        type: int
        default: 10
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Get reconciliation task information
  broadcom.vcf.sddc_manager_get_reconciliation_task:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    task_id: 12345678-1234-1234-1234-123456789012

- name: Get reconciliation task with custom retries
  broadcom.vcf.sddc_manager_get_reconciliation_task:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    task_id: 12345678-1234-1234-1234-123456789012
    retries: 120
    delay: 5
"""

RETURN = r"""
meta:
    description: The reconciliation task information including status and resolution
    returned: always
    type: dict
    sample:
        status: "SUCCESSFUL"
        resolutionStatus: "RESOLVED"
        id: "12345678-1234-1234-1234-123456789012"
        name: "Reconciliation Task"
        type: "RECONCILIATION"
        creationTimestamp: "2025-01-15T10:30:00.000Z"
        completionTimestamp: "2025-01-15T10:35:00.000Z"
msg:
    description: Error message when task fails or exceeds retries
    returned: on failure
    type: str
    sample: "Validation failed. Check the subtasks for more details."
changed:
    description: Whether any changes were made
    returned: always
    type: bool
    sample: false
"""

import json
import time

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


def extract_warnings(payload_data):
    """Extracts warnings from the task payload data."""
    warning_list = []
    for check in payload_data.get("validationChecks", []):
        for error in check.get("errorResponse", {}).get("nestedErrors", []):
            if error["errorCode"].endswith(".warning"):
                warning_list.append(
                    {
                        "description": check["description"],
                        "errorCode": error["errorCode"],
                        "message": error["message"],
                    }
                )
    return warning_list


def extract_errors(payload_data):
    """Extracts errors from the task payload data."""
    error_list = []

    def traverse_errors(errors):
        """Traverses the errors list recursively to extract nested errors."""
        for error in errors:
            error_list.append(
                {
                    "errorCode": error.get("errorCode"),
                    "errorType": error.get("errorType"),
                    "message": error.get("message"),
                    "remediationMessage": error.get("remediationMessage"),
                    "causes": error.get("causes", []),
                    "nestedErrors": error.get("nestedErrors", []),
                }
            )
            # Recursively traverse nested errors
            if "nestedErrors" in error:
                traverse_errors(error["nestedErrors"])

    def traverse_subtasks(subtasks):
        """Traverses the subtasks recursively to extract errors."""
        for subtask in subtasks:
            if "errors" in subtask:
                traverse_errors(subtask["errors"])
            if "stages" in subtask:
                for stage in subtask["stages"]:
                    if "errors" in stage:
                        traverse_errors(stage["errors"])
            if "subTasks" in subtask:
                traverse_subtasks(subtask["subTasks"])

    # Extract errors from the main task.
    if "errors" in payload_data:
        traverse_errors(payload_data["errors"])

    # Extract errors from subtasks.
    if "subTasks" in payload_data:
        traverse_subtasks(payload_data["subTasks"])

    return error_list


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = {
        "sddc_manager_hostname": {"required": True, "type": "str"},
        "task_id": {"required": True, "type": "str"},
        "sddc_manager_user": {"required": True, "type": "str"},
        "sddc_manager_password": {"required": True, "type": "str", "no_log": True},
        "retries": {"required": False, "type": "int", "default": 60},
        "delay": {"required": False, "type": "int", "default": 10},
    }

    module = AnsibleModule(supports_check_mode=True, argument_spec=parameters)

    sddc_manager_hostname = module.params["sddc_manager_hostname"]
    task_id = module.params["task_id"]
    sddc_manager_user = module.params["sddc_manager_user"]
    sddc_manager_password = module.params["sddc_manager_password"]
    retries = module.params["retries"]
    delay = module.params["delay"]

    try:
        api_client = SddcManagerApiClient(
            sddc_manager_hostname, sddc_manager_user, sddc_manager_password
        )

        for attempt in range(retries):
            validation_report = api_client.get_reconciliation_task(task_id)
            payload_data = validation_report.data

            warnings = extract_warnings(payload_data)

            error_codes = extract_errors(payload_data)

            if payload_data["status"] == "FAILED":
                response = {"error_codes": error_codes}
                if warnings:
                    response["warnings"] = json.dumps(warnings)
                module.fail_json(
                    changed=False,
                    msg="Validation failed. Check the subtasks for more details.",
                    meta=response,
                )
            elif (
                payload_data["status"] == "SUCCESSFUL"
                and payload_data["resolutionStatus"] == "RESOLVED"
            ):
                if warnings:
                    module.exit_json(
                        changed=False, meta=payload_data, warnings=json.dumps(warnings)
                    )
                else:
                    module.exit_json(changed=False, meta=payload_data)

            time.sleep(delay)

        module.fail_json(
            msg="Exceeded maximum retries, validation did not complete within the allotted time."
        )

    except VcfApiException as e:
        module.fail_json(changed=False, msg=f"Error: {e}")


if __name__ == "__main__":
    main()
