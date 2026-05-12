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
module: sddc_manager_workload_domain
short_description: Manages workload domains in SDDC Manager.
description:
    - This module manages workload domains in SDDC Manager for VMware Cloud Foundation.
    - It allows to add and remove workload domains.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    workload_domain_payload:
        description:
            - The payload containing the workload domain information.
            - When I(state=absent), at minimum the C(id) of the workload domain
              to remove must be provided.
        required: true
        type: dict
    state:
        description:
            - Desired state of the workload domain.
            - When set to C(present), the workload domain configuration is validated
              and, unless in check mode or when I(validate_only=true), a workload
              domain is added.
            - When set to C(absent), the workload domain identified by
              I(workload_domain_payload.id) is removed.
        type: str
        choices: [present, absent]
        default: present
    validate_only:
        description:
            - If true, perform validation only without adding the workload domain.
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
- name: Validate workload domain configuration
  broadcom.vcf.sddc_manager_workload_domain:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: present
    validate_only: true
    workload_domain_payload: {...}

- name: Validate workload domain configuration using check mode
  broadcom.vcf.sddc_manager_workload_domain:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: present
    workload_domain_payload: {...}
  check_mode: true

- name: Create Workload Domain
  broadcom.vcf.sddc_manager_workload_domain:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: present
    workload_domain_payload: {...}

- name: Delete workload domain by ID
  broadcom.vcf.sddc_manager_workload_domain:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: absent
    workload_domain_payload: {...}
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


class SddcManagerWorkloadDomain:
    """This class represents a workload domain in SDDC Manager.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager
            instance.
        sddc_manager_user (str): The username for authenticating with the SDDC Manager.
        sddc_manager_password (str): The password for authenticating with the SDDC
            Manager.
        workload_domain_payload (dict): The payload containing the workload domain
            information.
        state (str): The desired state of the workload domain.
        validate_only (bool): Whether to perform validation only when state is
            C(present).
        api_client (object): The SDDC Manager API client object.

    Methods:
        evaluate_response(data): Evaluates the response data from the SDDC Manager API.
        validate_workload_domain(self): Validates the workload domain configuration.
        add_workload_domain(self): Adds a workload domain.
        remove_workload_domain(self): Removes a workload domain by ID.
        run(self): Runs the workload domain process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params["sddc_manager_hostname"]
        self.sddc_manager_user = module.params["sddc_manager_user"]
        self.sddc_manager_password = module.params["sddc_manager_password"]
        self.workload_domain_payload = module.params["workload_domain_payload"]
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

    def validate_workload_domain(self):
        """Validates the workload domain configuration."""
        try:
            api_response = self.api_client.validate_domains(
                json.dumps(self.workload_domain_payload)
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

    def get_domain_with_validation_info(self, domain_id: str):
        """Retrieves domain information for validation.

        Args:
            domain_id (str): The ID of the domain to retrieve.

        Returns:
            dict: Domain information or None if not found.
        """
        try:
            domain_info = self.api_client.get_domain_by_id(domain_id)
            return domain_info
        except VcfApiException as e:
            raise VcfApiException(f"Error retrieving domain information: {e}")

    def add_workload_domain(self):
        """Adds a workload domain."""
        if self.module.check_mode:
            self.module.exit_json(
                changed=True,
                meta={
                    "message": (
                        "Check Mode: Workload domain would be created; "
                        "no changes were performed."
                    )
                },
            )

        try:
            return self.api_client.create_domains(
                json.dumps(self.workload_domain_payload)
            )
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error: {e}")

    def remove_workload_domain(self):
        """Removes a workload domain by ID."""
        domain_id = self.workload_domain_payload.get("id")

        try:
            # Get workload domain information for validation.
            domain_info = self.get_domain_with_validation_info(domain_id)

            if not domain_info:
                self.module.fail_json(
                    msg=f"Workload domain with ID '{domain_id}' not found."
                )

            domain_name = domain_info.get("name", "unknown")
            domain_type = domain_info.get("type", "").upper()

            # Check if the workload domain is the management domain.
            if domain_type == "MANAGEMENT":
                self.module.fail_json(
                    msg=(
                        f"Cannot remove domain type '{domain_type}' (Name: '{domain_name}'). ID: {domain_id}."
                    )
                )

            # Mark the workload domain for deletion.
            mark_body = json.dumps({"markForDeletion": True})
            self.api_client.update_domains(domain_id, mark_body)

            # Remove the workload domain.
            return self.api_client.delete_domains(domain_id)
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error: {e}")

    def run(self):
        """Runs the workload domain process.

        Behavior matrix:
        - state=present, validate_only=True -> validate, changed=False
        - state=present, check_mode=True    -> exit with message, changed=True
        - state=present, normal             -> create, changed=True
        - state=absent,  check_mode=True    -> exit with message, changed=True
        - state=absent,  normal             -> remove, changed=True
        """
        # Extract domain name for messaging
        domain_name = self.workload_domain_payload.get("domainName", "unknown")
        domain_id = self.workload_domain_payload.get("id")

        if self.state == "present":
            # Handle validation-only mode
            if self.validate_only:
                result = self.validate_workload_domain()
                self.module.exit_json(changed=False, meta=result)

            # Handle check mode
            if self.module.check_mode:
                check_msg = f"Check Mode: Would create workload domain '{domain_name}'; no changes were performed."

                self.module.exit_json(
                    changed=True,
                    msg=check_msg,
                    meta={"message": check_msg},
                )

            # Execute the actual operation
            result = self.add_workload_domain()
            success_msg = f"Successfully created workload domain '{domain_name}'."
            self.module.exit_json(changed=True, msg=success_msg, meta=result)

        elif self.state == "absent":
            if not domain_id:
                self.module.fail_json(
                    msg=(
                        "Parameter 'workload_domain_payload.id' is required when "
                        "state is 'absent'."
                    )
                )

            # Try to get domain name from payload, otherwise look it up
            if not domain_name or domain_name == "unknown":
                try:
                    domain_info = self.get_domain_with_validation_info(domain_id)
                    if domain_info:
                        domain_name = domain_info.get("name", "unknown")
                except VcfApiException:
                    pass

            # Handle check mode with validation.
            if self.module.check_mode:
                try:
                    domain_info = self.get_domain_with_validation_info(domain_id)

                    if not domain_info:
                        check_msg = (
                            f"Check Mode: Workload domain with ID '{domain_id}' not found. "
                            f"No removal would be performed."
                        )
                        self.module.exit_json(
                            changed=False, msg=check_msg, meta={"message": check_msg}
                        )

                    domain_name = domain_info.get("name", domain_name)
                    domain_type = domain_info.get("type", "").upper()

                    # Check if the workload domain is the management domain.
                    if domain_type == "MANAGEMENT":
                        check_msg = (
                            f"Check Mode: Would attempt to remove domain type '{domain_type}' and fail. "
                            f"'{domain_name}' (ID: {domain_id}) is the management domain and can not be removed."
                        )
                        self.module.exit_json(
                            changed=False, msg=check_msg, meta={"message": check_msg}
                        )

                    # If validation passes, indicate the workload domain would be removed.
                    check_msg = (
                        f"Check Mode: Would mark workload domain '{domain_name}' "
                        f"(ID: '{domain_id}') for deletion and remove it."
                    )
                    self.module.exit_json(
                        changed=True, msg=check_msg, meta={"message": check_msg}
                    )

                except Exception as e:
                    # If validation fails, provide a warning.
                    check_msg = (
                        f"Check Mode: Would mark workload domain "
                        f"(ID: '{domain_id}') for deletion. "
                        f"Unable to validate domain type (Error: {str(e)})."
                    )
                    self.module.exit_json(
                        changed=True, msg=check_msg, meta={"message": check_msg}
                    )

            # Execute the operation.
            result = self.remove_workload_domain()

            # Generate success message.
            if domain_name and domain_name != "unknown":
                success_msg = f"Successfully removed workload domain '{domain_name}' (ID: {domain_id})."
            else:
                success_msg = (
                    f"Successfully removed workload domain with ID '{domain_id}'."
                )

            self.module.exit_json(changed=True, msg=success_msg, meta=result)
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
        workload_domain_payload=dict(required=True, type="dict"),
        state=dict(
            required=False,
            type="str",
            choices=["present", "absent"],
            default="present",
        ),
        validate_only=dict(required=False, type="bool", default=False),
    )

    module = AnsibleModule(supports_check_mode=True, argument_spec=parameters)
    workload_domain = SddcManagerWorkloadDomain(module)
    workload_domain.run()


if __name__ == "__main__":
    main()
