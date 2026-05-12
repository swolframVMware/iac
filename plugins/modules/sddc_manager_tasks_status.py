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
module: sddc_manager_tasks_status
short_description: Retrieves the status of tasks in SDDC Manager.
description:
    - This module retrieves the status of tasks in SDDC Manager for VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    validation:
        description:
            - Whether to validate the task.
        required: true
        type: bool
    sddc_manager_task_type:
        description:
            - The type of the task.
        required: false
        choices:
            - wld_domain
            - avns
            - clusters
            - cluster_datastore
            - hosts
            - nsxt_manager
            - nsxt_edge_cluster
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Monitor workload domain creation validation
  broadcom.vcf.sddc_manager_tasks_status:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    task_id: 12345678-1234-1234-1234-123456789012
    validation: true
    sddc_manager_task_type: wld_domain
    retries: 60
    delay: 10

- name: Monitor cluster creation task
  broadcom.vcf.sddc_manager_tasks_status:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    task_id: 12345678-1234-1234-1234-123456789012
    validation: false
    sddc_manager_task_type: clusters
    retries: 120
    delay: 15

- name: Monitor host commissioning validation
  broadcom.vcf.sddc_manager_tasks_status:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    task_id: 12345678-1234-1234-1234-123456789012
    validation: true
    sddc_manager_task_type: hosts

- name: Monitor NSX Edge cluster validation
  broadcom.vcf.sddc_manager_tasks_status:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    task_id: 12345678-1234-1234-1234-123456789012
    validation: true
    sddc_manager_task_type: nsxt_edge_cluster
"""

RETURN = r"""
msg:
    description: Status message about the task or error details
    returned: on failure
    type: str
    sample: "Task failed. Check the subtasks for more details."
meta:
    description: Task or validation details returned from the SDDC Manager API
    returned: always
    type: dict
    sample:
        id: "12345678-1234-1234-1234-123456789012"
        name: "Create Cluster"
        status: "COMPLETED"
        type: "CREATE_CLUSTER"
        subTasks:
            - name: "Validate cluster configuration"
              status: "SUCCESSFUL"
              description: "Validating cluster configuration"
            - name: "Create cluster in vCenter"
              status: "SUCCESSFUL"
              description: "Creating cluster in vCenter"
changed:
    description: Whether the module made changes or detected task completion
    returned: always
    type: bool
    sample: true
"""

import time

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


class SddcManagerTaskProcessor:
    """The class represents the task processor for SDDC Manager. It handles the task
    processing and validation checks.

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
        validation (bool): Flag indicating whether to perform validation checks or not.
        sddc_manager_task_type (str): The type of task to be processed.
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
        status = payload_data.get("status", "").upper()

        if status == "FAILED":
            error_check_list = [
                {"task_name": task["name"], "task_description": task["description"]}
                for task in payload_data["subTasks"]
                if task["status"] == "FAILED"
            ]
            self.module.fail_json(
                changed=False,
                meta={"error_codes": error_check_list},
                msg="Task failed. Check the subtasks for more details.",
            )
        elif status in ("COMPLETED", "SUCCESSFUL"):
            success_msg = self._generate_success_message(payload_data)
            self.module.exit_json(changed=True, msg=success_msg, meta=payload_data)

    def _generate_success_message(self, payload_data):
        """Generates a success message based on task type and results."""
        task_name = payload_data.get("name", "Task")

        # Extract host information, if available.
        hosts = []

        # Try to extract from resources array.
        if "resources" in payload_data:
            for resource in payload_data["resources"]:
                if resource.get("type") == "HOST":
                    fqdn = resource.get("fqdn") or resource.get("name")
                    if fqdn:
                        hosts.append(fqdn)

        # Alternative: Try to extract from subTasks.
        if not hosts and "subTasks" in payload_data:
            for subtask in payload_data["subTasks"]:
                # Look for FQDN in subtask name or description.
                if "fqdn" in subtask:
                    hosts.append(subtask["fqdn"])
                elif "host" in subtask and isinstance(subtask["host"], str):
                    hosts.append(subtask["host"])

        # Alternative: Parse from task name if still empty.
        if not hosts and "host(s)" in task_name.lower():
            import re

            match = re.search(r"host\(s\)\s+([^\s]+)", task_name)
            if match:
                hosts_str = match.group(1)
                hosts = [h.strip() for h in hosts_str.split(",") if h.strip()]

        # Generate message based on task type and extracted data.
        if self.sddc_manager_task_type == "hosts":
            if hosts:
                if "decommission" in task_name.lower():
                    return f"Successfully decommissioned {len(hosts)} host(s): {', '.join(hosts)}."
                elif "commission" in task_name.lower():
                    return f"Successfully commissioned {len(hosts)} host(s): {', '.join(hosts)}."
                else:
                    return f"Successfully completed host operation for {len(hosts)} host(s): {', '.join(hosts)}."
            else:
                return f"Successfully completed {task_name}."
        else:
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
        if self.validation:
            method_mapping = {
                "wld_domain": self.api_client.validate_domains,
                "avns": self.api_client.validate_avns,
                "clusters": self.api_client.validate_clusters,
                "cluster_datastore": self.api_client.validate_mount_datastore_on_cluster,
                "hosts": self.api_client.get_validate_hosts_status,
                # 'nsxt_manager': self.api_client.get_nsxt_manager_validation_status,
                "nsxt_edge_cluster": self.api_client.edge_cluster_validation_status,
            }
            api_call_method = method_mapping.get(self.sddc_manager_task_type)
            if api_call_method:
                self.process_validation_task(api_call_method)
            else:
                self.module.fail_json(
                    msg=f"Unsupported task type: {self.sddc_manager_task_type}"
                )
        else:
            try:
                for attempt in range(self.retries):
                    api_response = self.api_client.get_sddc_manager_task_by_id(
                        self.task_id
                    )
                    payload_data = api_response
                    self.evaluate_task_status(payload_data)
                    time.sleep(self.delay)
                self.module.fail_json(
                    msg="Exceeded maximum retries, validation did not complete within the allotted time."
                )
            except VcfApiException as e:
                self.module.fail_json(msg=f"Error: {e}", status_code=e.status_code)


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
        "validation": {"required": True, "type": "bool"},
        "sddc_manager_task_type": {
            "required": False,
            "type": "str",
            "choices": [
                "wld_domain",
                "avns",
                "clusters",
                "cluster_datastore",
                "hosts",
                "nsxt_manager",
                "nsxt_edge_cluster",
            ],
        },
        "retries": {"required": False, "type": "int", "default": 60},
        "delay": {"required": False, "type": "int", "default": 10},
    }

    module = AnsibleModule(
        argument_spec=parameters,
        supports_check_mode=True,
        required_if=[
            (
                "validation",
                True,
                ["sddc_manager_task_type"],
            )
        ],
    )
    task_processor = SddcManagerTaskProcessor(module)
    task_processor.process_task()


if __name__ == "__main__":
    main()
