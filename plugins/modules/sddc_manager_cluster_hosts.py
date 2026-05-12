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
module: sddc_manager_cluster_hosts
short_description: Manages hosts for a cluster in SDDC Manager.
description:
    - This module manages hosts for a cluster in SDDC Manager for VMware Cloud Foundation.
    - It allows to add and remove hosts to and from a cluster.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
  state:
    description:
      - Desired state of hosts in the cluster
      - C(present) adds hosts to the cluster (expansion)
      - C(absent) removes hosts from the cluster (compaction)
    required: false
    type: str
    choices: ['present', 'absent']
    default: 'present'
  cluster_id:
    description:
      - ID of the cluster to modify
    required: true
    type: str
  cluster_payload:
    description:
      - Cluster modification payload
      - For C(state=present), uses clusterExpansionSpec
      - For C(state=absent), uses clusterCompactionSpec
    required: true
    type: dict
  validate_only:
    description:
      - If true, perform validation only without modifying the cluster
      - When I(validate_only=true), the module calls the validation API
        and returns C(changed=false)
    required: false
    type: bool
    default: false
"""

EXAMPLES = r"""
# Add hosts to cluster
- name: Add hosts to cluster
  broadcom.vcf.sddc_manager_cluster_hosts:
    state: present
    cluster_id: "abc-123"
    cluster_payload:
      clusterExpansionSpec:
        hostSpecs: [...]

# Remove hosts from cluster
- name: Remove hosts from cluster
  broadcom.vcf.sddc_manager_cluster_hosts:
    state: absent
    cluster_id: "abc-123"
    cluster_payload:
      clusterCompactionSpec:
        hosts: [...]
"""

RETURN = r"""
msg:
    description: Status message about the operation
    returned: on failure
    type: str
    sample: "Validation failed. Check the subtasks for more details."
meta:
    description: Task metadata returned from the SDDC Manager API
    returned: always
    type: dict
    sample:
        id: "12345678-1234-1234-1234-123456789012"
        name: "Expand Cluster"
        status: "IN_PROGRESS"
        type: "EXPAND_CLUSTER"
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


class SddcManagerClusterHosts:
    """Manages host membership in a VCF cluster.

    This class handles both adding hosts (expansion) and removing hosts (compaction)
    from a cluster via the SDDC Manager API.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager.
        sddc_manager_user (str): The username for authenticating with SDDC Manager.
        sddc_manager_password (str): The password for authenticating with SDDC Manager.
        cluster_id (str): The ID of the cluster to modify.
        cluster_payload (dict): The cluster modification payload (expansion or compaction spec).
        api_client (object): An instance of the SddcManagerApiClient class.

    Methods:
        validate_cluster_update: Validates the cluster modification operation.
        evaluate_validation_status: Evaluates validation response and handles errors.
        update_cluster_hosts: Executes the cluster modification operation.
        run: Main execution method.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params["sddc_manager_hostname"]
        self.sddc_manager_user = module.params["sddc_manager_user"]
        self.sddc_manager_password = module.params["sddc_manager_password"]
        self.cluster_id = module.params["cluster_id"]
        self.cluster_payload = module.params["cluster_payload"]
        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )

    def validate_cluster_update(self):
        """Validates cluster host modification operation.

        Calls the validation API endpoint to check if the operation can succeed.
        Evaluates the validation response and handles any errors.
        """
        try:
            api_response = self.api_client.validate_update_cluster(
                self.cluster_id, json.dumps(self.cluster_payload)
            )
            self.evaluate_validation_status(api_response)
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error: {e}")

    def evaluate_validation_status(self, payload_data):
        """Evaluates the validation status from the API response.

        Args:
            payload_data (dict): The validation response from the API.

        Handles validation failures by extracting error details and failing the module.
        Exits successfully if validation passes.
        """
        if (
            payload_data["executionStatus"] == "FAILED"
            or payload_data["executionStatus"] == "COMPLETED"
            and payload_data["resultStatus"] == "FAILED"
        ):
            validation_check_list = payload_data["validationChecks"]
            error_codes = []
            for validation_check in validation_check_list:
                if validation_check["resultStatus"] in ["FAILED", "SUCCEEDED"]:
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
                msg="Validation failed. Check the subtasks for more details.",
            )
        elif payload_data["executionStatus"] == "COMPLETED":
            self.module.exit_json(changed=False, meta=payload_data)

    def update_cluster_hosts(self):
        """Executes cluster host modification operation.

        Calls the PATCH API to add or remove hosts based on the payload structure.

        Returns:
             dict: API response containing task information.
        """
        try:
            api_response = self.api_client.update_cluster(
                self.cluster_id, json.dumps(self.cluster_payload)
            )
            return api_response
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error: {e}")

    def run(self):
        """Main execution method for cluster host management.

        Handles check mode, validation mode, and actual execution.
        Determines operation type from payload structure for messaging.

        Behavior matrix:
        - validate_only=True           -> validate, changed=False
        - check_mode=True              -> exit with message, changed=True
        - normal execution             -> modify cluster, changed=True
        """
        host_fqdns = []
        operation_type = "modify"

        if "clusterExpansionSpec" in self.cluster_payload:
            operation_type = "add"
            host_specs = self.cluster_payload.get("clusterExpansionSpec", {}).get(
                "hostSpecs", []
            )
            host_fqdns = [spec.get("hostName", "unknown") for spec in host_specs]
        elif "clusterCompactionSpec" in self.cluster_payload:
            operation_type = "remove"
            hosts = self.cluster_payload.get("clusterCompactionSpec", {}).get(
                "hosts", []
            )
            host_fqdns = [
                host.get("id", "unknown") if isinstance(host, dict) else str(host)
                for host in hosts
            ]

        # Handle validation-only mode
        if self.module.params.get("validate_only"):
            self.validate_cluster_update()
            # validate_cluster_update will exit with changed=False if successful
            return

        # Handle check mode
        if self.module.check_mode:
            if host_fqdns:
                host_list = ", ".join(host_fqdns)
                self.module.exit_json(
                    changed=True,
                    meta={
                        "message": (
                            f"Check Mode: Would update cluster {self.cluster_id} and "
                            f"{operation_type} the following hosts: {host_list}."
                        )
                    },
                )
            else:
                self.module.exit_json(
                    changed=True,
                    meta={
                        "message": f"Check Mode: Would update cluster {self.cluster_id}."
                    },
                )

        # Execute the actual operation
        result = self.update_cluster_hosts()

        if host_fqdns:
            host_list = ", ".join(host_fqdns)
            success_msg = f"Successfully completed {operation_type} operation for cluster ID {self.cluster_id} with the following hosts: {host_list}"
        else:
            success_msg = f"Successfully completed {operation_type} operation for cluster ID {self.cluster_id}."

        self.module.exit_json(changed=True, msg=success_msg, meta=result)


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
            required=False, type="str", choices=["present", "absent"], default="present"
        ),
        cluster_id=dict(required=True, type="str"),
        cluster_payload=dict(required=True, type="dict"),
        validate_only=dict(required=False, type="bool", default=False),
    )

    module = AnsibleModule(argument_spec=parameters, supports_check_mode=True)

    cluster_hosts = SddcManagerClusterHosts(module)
    cluster_hosts.run()


if __name__ == "__main__":
    main()
