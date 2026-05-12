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
module: sddc_manager_nsx_edge_cluster
short_description: Manages NSX Edge clusters in SDDC Manager.
description:
    - This module manages NSX Edge clusters in SDDC Manager for VMware Cloud Foundation.
    - It allows to validate and create NSX Edge clusters.
    - Note that NSX Edge cluster deletion is not supported by the VCF API.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    edge_cluster_payload:
        description:
            - The payload containing the NSX Edge cluster configuration.
            - Refer to VMware Cloud Foundation API documentation for the payload structure.
        required: true
        type: dict
    state:
        description:
            - Desired state of the NSX Edge cluster.
            - When set to C(present), the edge cluster configuration is validated
              and, unless in check mode or when I(validate_only=true), an edge cluster
              is added.
        type: str
        choices:
            - present
        default: present
    validate_only:
        description:
            - If true, perform validation only without creating the edge cluster.
            - When I(state=present) and I(validate_only=true), the module calls the
              validation API and returns C(changed=false).
            - When in Ansible check mode, the module also performs validation only
              and reports C(changed=false), regardless of this flag.
        type: bool
        default: false
requirements:
    - python >= 3.12
notes:
    - NSX Edge cluster deletion is not supported by the VCF API.
    - To remove an edge cluster, you must delete the associated workload domain.
"""

EXAMPLES = r"""
- name: Validate NSX Edge cluster configuration (explicit validate-only)
  broadcom.vcf.sddc_manager_nsx_edge_cluster:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: present
    validate_only: true
    edge_cluster_payload: {...}

- name: Validate NSX Edge cluster configuration using check mode
  broadcom.vcf.sddc_manager_nsx_edge_cluster:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: present
    edge_cluster_payload: {...}
  check_mode: true

- name: Add NSX Edge cluster in SDDC Manager
  broadcom.vcf.sddc_manager_nsx_edge_cluster:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: present
    edge_cluster_payload: {...}
"""

RETURN = r"""
msg:
    description: Error message when the module fails
    returned: on failure
    type: str
meta:
    description: The response from SDDC Manager API
    returned: always
    type: dict
    sample:
        id: "12345678-1234-1234-1234-123456789012"
        name: "edge-cluster-01"
        resultStatus: "COMPLETED"
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


class SddcManagerNsxEdgeCluster:
    """This class represents an NSX Edge cluster in SDDC Manager.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager
            instance.
        sddc_manager_user (str): The username for authenticating with the SDDC Manager.
        sddc_manager_password (str): The password for authenticating with the SDDC
            Manager.
        edge_cluster_payload (dict): The payload containing the edge cluster configuration.
        state (str): The desired state of the edge cluster.
        validate_only (bool): Whether to perform validation only when state is
            C(present).
        api_client (object): The SDDC Manager API client object.

    Methods:
        evaluate_response(data): Evaluates the response data from the SDDC Manager API.
        validate_edge_cluster(self): Validates the edge cluster configuration.
        add_edge_cluster(self): Adds an edge cluster.
        run(self): Runs the edge cluster process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params["sddc_manager_hostname"]
        self.sddc_manager_user = module.params["sddc_manager_user"]
        self.sddc_manager_password = module.params["sddc_manager_password"]
        self.edge_cluster_payload = module.params["edge_cluster_payload"]
        self.state = module.params["state"]
        self.validate_only = module.params["validate_only"]
        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )

    @staticmethod
    def evaluate_response(data):
        """Evaluates the response data from the SDDC Manager API."""
        output = {"errors": [], "message": ""}
        if data.get("resultStatus") == "FAILED":
            output["message"] = "FAILED"
            for check in data.get("validationChecks", []):
                if check.get("resultStatus") == "FAILED":
                    error_response = check.get("errorResponse", {}) or {}
                    error_info = {
                        "errorCode": error_response.get("errorCode"),
                        "arguments": error_response.get("arguments"),
                        "message": error_response.get("message"),
                    }
                    output["errors"].append(error_info)
        else:
            output["message"] = "Successful"

        return output

    def validate_edge_cluster(self):
        """Validates the edge cluster configuration."""
        try:
            api_response = self.api_client.validate_edge_cluster(
                json.dumps(self.edge_cluster_payload)
            )
            payload_data = api_response
            response = self.evaluate_response(payload_data)
            if response["message"] == "Successful":
                return response
            else:
                self.module.log(response)
                self.module.fail_json(msg=json.dumps(response))
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error: {e}")

    def add_edge_cluster(self):
        """Adds an edge cluster."""
        try:
            return self.api_client.create_edge_cluster(
                json.dumps(self.edge_cluster_payload)
            )
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error: {e}")

    def run(self):
        """Runs the edge cluster process.

        Behavior matrix:
        - state=present, validate_only=True          -> validate, changed=False
        - state=present, check_mode=True             -> validate, changed=False
        - state=present, normal                      -> add, changed=True
        """
        # Check mode for present state - perform validation only
        if self.module.check_mode and self.state == "present":
            if not self.edge_cluster_payload:
                self.module.fail_json(
                    msg="edge_cluster_payload is required for state 'present'."
                )

            # In check mode, we validate but don't actually create
            self.validate_edge_cluster()
            self.module.exit_json(
                changed=False,
                msg="Check Mode: NSX Edge cluster payload validated successfully; no changes would be made.",
            )

        # Add NSX Edge cluster (state=present)
        if self.state == "present":
            if not self.edge_cluster_payload:
                self.module.fail_json(
                    msg="edge_cluster_payload is required for state 'present'."
                )

            # If validate_only is True, just validate
            if self.validate_only:
                result = self.validate_edge_cluster()
                self.module.exit_json(changed=False, meta=result)
            else:
                # Actually add the edge cluster
                result = self.add_edge_cluster()
                self.module.exit_json(changed=True, meta=result)
        else:
            self.module.fail_json(msg="Not a valid option for state parameter.")


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = dict(
        sddc_manager_hostname=dict(required=True, type="str"),
        sddc_manager_user=dict(required=True, type="str"),
        sddc_manager_password=dict(required=True, type="str", no_log=True),
        edge_cluster_payload=dict(required=True, type="dict"),
        state=dict(
            required=False,
            type="str",
            choices=["present"],
            default="present",
        ),
        validate_only=dict(required=False, type="bool", default=False),
    )

    module = AnsibleModule(supports_check_mode=True, argument_spec=parameters)
    edge_cluster = SddcManagerNsxEdgeCluster(module)
    edge_cluster.run()


if __name__ == "__main__":
    main()
