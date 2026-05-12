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
module: sddc_manager_cluster
short_description: Manages clusters for workload domains in SDDC Manager.
description:
    - This module manages clusters for workload domains in SDDC Manager for VMware Cloud Foundation.
    - It allows to add and remove clusters.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    cluster_payload:
        description:
            - The payload containing the cluster configuration.
            - Refer to the PAYLOAD_SAMPLE for an example.
            - When I(state=absent), at minimum the C(id) of the cluster
              to remove must be provided.
        required: true
        type: dict
    state:
        description:
            - Desired state of the cluster.
            - When set to C(present), the cluster configuration is validated
              and, unless in check mode or when I(validate_only=true), a cluster
              is added.
            - When set to C(absent), the cluster identified by
              I(cluster_payload.id) is removed.
        type: str
        choices: [present, absent]
        default: present
    validate_only:
        description:
            - If true, perform validation only without creating the cluster.
            - When I(state=present) and I(validate_only=true), the module calls the
              validation API and returns C(changed=false).
            - When in Ansible check mode, the module also performs validation only
              and reports C(changed=false), regardless of this flag.
        type: bool
        default: false
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Validate cluster configuration (explicit validate-only)
  broadcom.vcf.sddc_manager_cluster:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: present
    validate_only: true
    cluster_payload: {...}

- name: Validate cluster configuration using check mode
  broadcom.vcf.sddc_manager_cluster:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: present
    cluster_payload: {...}
  check_mode: true

- name: Create a cluster in SDDC Manager
  broadcom.vcf.sddc_manager_cluster:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: present
    cluster_payload: {...}

- name: Delete cluster by ID
  broadcom.vcf.sddc_manager_cluster:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: absent
    cluster_payload:
      id: "12345678-1234-1234-1234-123456789012"
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
changed:
    description: Whether the module detected task completion
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


class SddcManagerCluster:
    """This class represents a cluster in SDDC Manager.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager
            instance.
        sddc_manager_user (str): The username for authenticating with the SDDC Manager.
        sddc_manager_password (str): The password for authenticating with the SDDC
            Manager.
        cluster_payload (dict): The payload containing the cluster configuration.
        state (str): The desired state of the cluster.
        validate_only (bool): Whether to perform validation only when state is
            C(present).
        api_client (object): The SDDC Manager API client object.

    Methods:
        evaluate_response(data): Evaluates the response data from the SDDC Manager API.
        validate_cluster(self): Validates the cluster configuration.
        add_cluster(self): Adds a cluster.
        remove_cluster(self): Removes a cluster by ID.
        run(self): Runs the cluster process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params["sddc_manager_hostname"]
        self.sddc_manager_user = module.params["sddc_manager_user"]
        self.sddc_manager_password = module.params["sddc_manager_password"]
        self.cluster_payload = module.params["cluster_payload"]
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
        if data["resultStatus"] == "FAILED":
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

    def validate_cluster(self):
        """Validates the cluster configuration."""
        try:
            api_response = self.api_client.validate_clusters(
                json.dumps(self.cluster_payload)
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

    def add_cluster(self):
        """Adds a cluster."""
        try:
            return self.api_client.create_clusters(json.dumps(self.cluster_payload))
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error: {e}")

    def get_cluster_with_domain_info(self, cluster_id: str):
        """Retrieves cluster and domain information.

        Args:
            cluster_id (str): The cluster ID to look up.

        Returns:
            tuple: (cluster_info dict, domain_info dict) or (None, None) if not found.
        """
        try:
            cluster_info = self.api_client.get_cluster_by_id(cluster_id)

            if not cluster_info:
                return None, None

            # Extract domain ID from cluster response.
            domain_obj = cluster_info.get("domain", {})
            domain_id = domain_obj.get("id") if domain_obj else None

            if not domain_id:
                return cluster_info, None

            # Get full domain information.
            domain_info = self.api_client.get_domain_by_id(domain_id)

            return cluster_info, domain_info

        except VcfApiException as e:
            raise VcfApiException(f"Error retrieving cluster information: {e}")

    def remove_cluster(self):
        """Removes a cluster by ID."""
        cluster_id = self.cluster_payload.get("id")

        try:
            # Get cluster and domain information.
            cluster_info, domain_info = self.get_cluster_with_domain_info(cluster_id)

            if not cluster_info or not domain_info:
                self.module.fail_json(
                    msg=f"Cluster with ID '{cluster_id}' not found or not associated with any workload domain."
                )

            cluster_name = cluster_info.get("name", "unknown")
            clusters_in_domain = domain_info.get("clusters", [])

            # Check if this is the last cluster in the domain.
            if len(clusters_in_domain) == 1:
                self.module.fail_json(
                    msg=(
                        f"Cannot remove cluster '{cluster_name}' (ID: {cluster_id}). "
                        f"It is the only cluster in workload domain '{domain_info.get('name')}'. "
                        f"A workload domain must have at least one cluster."
                    )
                )

            # Mark the cluster for deletion.
            mark_body = json.dumps({"markForDeletion": True})
            self.api_client.update_cluster(cluster_id, mark_body)

            # Remove the cluster.
            return self.api_client.delete_cluster(cluster_id)
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error: {e}")

    def run(self):
        """Runs the cluster process.

        Behavior matrix:
        - state=present, validate_only=True -> validate, changed=False
        - state=present, check_mode=True    -> exit with message, changed=True
        - state=present, normal             -> create, changed=True
        - state=absent,  check_mode=True    -> exit with message, changed=True
        - state=absent,  normal             -> remove, changed=True
        """
        # Extract cluster name for messaging.
        cluster_name = self.cluster_payload.get("name")

        # If name is not at top level, try to get it from nested structure.
        if not cluster_name:
            compute_spec = self.cluster_payload.get("computeSpec", {})
            cluster_specs = compute_spec.get("clusterSpecs", [])
            if cluster_specs and len(cluster_specs) > 0:
                cluster_name = cluster_specs[0].get("name", "unknown")
            else:
                cluster_name = "unknown"

        cluster_id = self.cluster_payload.get("id")

        if self.state == "present":
            # Handle validation-only mode.
            if self.validate_only:
                result = self.validate_cluster()
                self.module.exit_json(changed=False, meta=result)

            # Handle check mode.
            if self.module.check_mode:
                check_msg = f"Check Mode: Would add cluster '{cluster_name}'; no changes were performed."
                self.module.exit_json(
                    changed=True,
                    msg=check_msg,
                    meta={"message": check_msg},
                )

            # Execute the operation.
            result = self.add_cluster()
            success_msg = f"Successfully created cluster '{cluster_name}'."
            self.module.exit_json(changed=True, msg=success_msg, meta=result)

        elif self.state == "absent":
            if not cluster_id:
                self.module.fail_json(
                    msg=(
                        "Parameter 'cluster_payload.id' is required when "
                        "state is 'absent'."
                    )
                )

            # Try to get cluster name from payload, otherwise look it up.
            if not cluster_name or cluster_name == "unknown":
                try:
                    cluster_info, _ = self.get_cluster_with_domain_info(cluster_id)
                    if cluster_info:
                        cluster_name = cluster_info.get("name", "unknown")
                except VcfApiException:
                    pass

            # Handle check mode with validation.
            if self.module.check_mode:
                try:
                    cluster_info, domain_info = self.get_cluster_with_domain_info(
                        cluster_id
                    )

                    if not cluster_info or not domain_info:
                        check_msg = (
                            f"Check Mode: Cluster with ID '{cluster_id}' not found or not associated with any domain. "
                            f"No removal would be performed."
                        )
                        self.module.exit_json(
                            changed=False, msg=check_msg, meta={"message": check_msg}
                        )

                    cluster_name = cluster_info.get("name", cluster_name)
                    clusters_in_domain = domain_info.get("clusters", [])

                    if len(clusters_in_domain) == 1:
                        check_msg = (
                            f"Check Mode: Would attempt to remove cluster '{cluster_name}' (ID: {cluster_id}), "
                            f"but operation would fail because it is the only cluster in workload domain '{domain_info.get('name')}'. "
                            f"A workload domain must have at least one cluster."
                        )
                        self.module.exit_json(
                            changed=False, msg=check_msg, meta={"message": check_msg}
                        )

                    # Removal would be allowed.
                    check_msg = (
                        f"Check Mode: Would mark cluster '{cluster_name}' (ID: {cluster_id}) for deletion and remove it from "
                        f"workload domain '{domain_info.get('name')}'. "
                        f"{len(clusters_in_domain) - 1} cluster(s) would remain."
                    )
                    self.module.exit_json(
                        changed=True, msg=check_msg, meta={"message": check_msg}
                    )

                except Exception as e:
                    # If validation fails, provide a warning.
                    check_msg = (
                        f"Check Mode: Would mark cluster '{cluster_name}' (ID: {cluster_id}) for deletion. "
                        f"Unable to validate if this is the last cluster (Error: {str(e)}). "
                    )
                    self.module.exit_json(
                        changed=True, msg=check_msg, meta={"message": check_msg}
                    )

            # Execute the operation.
            result = self.remove_cluster()

            # Generate success message.
            if cluster_name and cluster_name != "unknown":
                success_msg = (
                    f"Successfully removed cluster '{cluster_name}' (ID: {cluster_id})."
                )
            else:
                success_msg = f"Successfully removed cluster with ID '{cluster_id}'."

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
        cluster_payload=dict(required=True, type="dict"),
        state=dict(
            required=False,
            type="str",
            choices=["present", "absent"],
            default="present",
        ),
        validate_only=dict(required=False, type="bool", default=False),
    )

    module = AnsibleModule(supports_check_mode=True, argument_spec=parameters)
    cluster = SddcManagerCluster(module)
    cluster.run()


if __name__ == "__main__":
    main()
