# -*- coding: utf-8 -*-
#
# Copyright (c) Broadcom. All Rights Reserved.
# The term "Broadcom" refers solely to the Broadcom Inc. corporate affiliate that
# distributes this software.
#
# You are hereby granted a non-exclusive, worldwide, royalty-free license under
# Broadcom's copyrights to use, copy, modify, and distribute this software in source
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
module: vcf_installer_instance
short_description: Deploys a VCF Instance with VCF Installer.
description:
    - This module manages the deployment of a VCF Instance with VCF Installer
      for VMware Cloud Foundation.
    - It consolidates payload validation and bring-up into a single idempotent
      module that mirrors the interface of M(broadcom.vcf.sddc_manager_workload_domain).
    - When I(validate_only=true) or Ansible check mode is active, no irreversible
      changes are made.
    - Because a VCF Instance cannot be removed through VCF Installer, there
      is no C(absent) state; only C(present) is supported.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.vcf_installer
options:
    sddc_management_domain_payload:
        description:
            - The payload containing the VCF Instance configuration.
            - Mutually exclusive with I(sddc_id).
            - Required when I(sddc_id) is not provided.
            - Refer to the PAYLOAD_SAMPLE for an example.
        required: false
        type: dict
    sddc_id:
        description:
            - The ID of an existing VCF Instance bring-up to retry.
            - When provided, the module retries the failed deployment identified by
              this ID and polls until it reaches C(COMPLETED_WITH_SUCCESS).
            - Mutually exclusive with I(sddc_management_domain_payload) and
              I(validate_only).
        required: false
        type: str
    validate_only:
        description:
            - When C(true), submits the payload for validation and polls until the
              validation completes, but does not proceed with the actual deployment.
            - Returns C(changed=false).
            - When Ansible check mode is active the module exits before making any
              API call and reports C(changed=true) to indicate a deployment B(would)
              occur; use I(validate_only=true) when you need a real pre-flight check.
        type: bool
        default: false
    validation_timeout:
        description:
            - Total wall-clock seconds the module will wait for the validation to
              reach a terminal state before failing.
            - The module polls every I(validation_poll_interval) seconds.
            - Set to C(0) to wait indefinitely.
            - The default of C(1800) covers 30 minutes, which is sufficient for
              most payload validations.
        type: int
        default: 1800
    validation_poll_interval:
        description:
            - Seconds to wait between validation status polling attempts.
        type: int
        default: 30
    deployment_timeout:
        description:
            - Total wall-clock seconds the module will wait for the deployment to
              reach a terminal state before failing.
            - The module polls every I(deployment_poll_interval) seconds and continues as
              long as the deployment is actively running, regardless of how long
              individual subtasks take.
            - Set to C(0) to wait indefinitely until the deployment succeeds or fails.
        type: int
        default: 43200
    deployment_poll_interval:
        description:
            - Seconds to wait between deployment status polling attempts.
        type: int
        default: 30
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Validate VCF Instance Payload
  broadcom.vcf.vcf_installer_instance:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    validate_only: true
    sddc_management_domain_payload: "{{ api_payload_json }}"

- name: Deploy VCF Instance
  broadcom.vcf.vcf_installer_instance:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    sddc_management_domain_payload: "{{ api_payload_json }}"

- name: Deploy VCF Instance with Custom Polling Parameters
  broadcom.vcf.vcf_installer_instance:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    sddc_management_domain_payload: "{{ api_payload_json }}"
    validation_timeout: 3600
    validation_poll_interval: 30
    deployment_timeout: 86400
    deployment_poll_interval: 60

- name: Retry a Failed VCF Instance Deployment
  broadcom.vcf.vcf_installer_instance:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    sddc_id: 12345678-1234-1234-1234-123456789012
"""

RETURN = r"""
msg:
    description: Human-readable status or error message.
    returned: always
    type: str
meta:
    description: The final response payload from the VCF Installer API.
    returned: always
    type: dict
validation_warnings:
    description: >
        List of non-fatal warning objects returned by the validation API.
        Each entry contains C(description), C(errorCode), and C(message) keys.
    returned: when warnings are present during validation
    type: list
    elements: dict
changed:
    description: Whether the module made or would make a change.
    returned: always
    type: bool
"""

import json
import time

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.vcf_installer import (
    VcfInstallerApiClient,
)


class VcfInstallerInstance:
    """Manages the deployment of a VCF Instance instance with VCF Installer.

    Args:
        module: The Ansible module object.

    Attributes:
        module (AnsibleModule): The Ansible module object.
        vcf_installer_hostname (str): Hostname or IP of the VCF Installer appliance.
        vcf_installer_user (str): Username for VCF Installer authentication.
        vcf_installer_password (str): Password for VCF Installer authentication.
        sddc_management_domain_payload (dict): VCF Instance configuration payload.
        sddc_id (str): SDDC ID of an existing deployment to retry.
        validate_only (bool): When True, perform validation without deployment.
        validation_timeout (int): Total seconds to wait for validation; 0 = no limit.
        validation_poll_interval (int): Seconds between validation status polling attempts.
        deployment_timeout (int): Total seconds to wait for deployment; 0 = no limit.
        deployment_poll_interval (int): Seconds between deployment status polling attempts.
        api_client (VcfInstallerApiClient): The VCF Installer API client.

    Methods:
        extract_validation_warnings: Extracts warning entries from a validation report.
        extract_validation_errors: Extracts error entries from a validation report.
        validate_instance: Submits the payload for validation and polls until complete.
        create_instance: Submits the deployment request and polls until complete.
        retry_instance: Retries a failed deployment by SDDC ID and polls until complete.
        run: Orchestrates the module workflow based on parameters and mode.

    Raises:
        VcfApiException: If an unexpected error occurs during an API call.
    """

    # Deployment terminal statuses.
    _DEPLOY_FAILED_STATUSES = frozenset(
        {"FAILED", "COMPLETED_WITH_FAILURE"}
    )
    _DEPLOY_SUBTASK_FAILED_STATUSES = frozenset(
        {"FAILED", "COMPLETED_WITH_FAILURE", "POSTVALIDATION_COMPLETED_WITH_FAILURE"}
    )
    _DEPLOY_SUCCESS_STATUS = "COMPLETED_WITH_SUCCESS"

    # Validation terminal statuses.
    _VALIDATION_FAILED_STATUS = "FAILED"
    _VALIDATION_SUCCESS_STATUSES = frozenset({"SUCCEEDED", "COMPLETED"})

    def __init__(self, module: AnsibleModule):
        self.module = module
        self.vcf_installer_hostname = module.params["vcf_installer_hostname"]
        self.vcf_installer_user = module.params["vcf_installer_user"]
        self.vcf_installer_password = module.params["vcf_installer_password"]
        self.sddc_management_domain_payload = module.params[
            "sddc_management_domain_payload"
        ]
        self.sddc_id = module.params["sddc_id"]
        self.validate_only = module.params["validate_only"]
        self.validation_timeout = module.params["validation_timeout"]
        self.validation_poll_interval = module.params["validation_poll_interval"]
        self.deployment_timeout = module.params["deployment_timeout"]
        self.deployment_poll_interval = module.params["deployment_poll_interval"]
        self.api_client = VcfInstallerApiClient(
            self.vcf_installer_hostname,
            self.vcf_installer_user,
            self.vcf_installer_password,
        )

    @staticmethod
    def extract_validation_warnings(payload_data: dict) -> list:
        """Extracts warning entries from a validation report.

        Args:
            payload_data (dict): The validation report returned by the API.

        Returns:
            list: A list of warning dicts, each with C(description), C(errorCode),
                and C(message) keys.
        """
        warnings = []
        for check in payload_data.get("validationChecks", []):
            for error in check.get("errorResponse", {}).get("nestedErrors", []):
                if str(error.get("errorCode", "")).endswith(".warning"):
                    warnings.append(
                        {
                            "description": check.get("description"),
                            "errorCode": error["errorCode"],
                            "message": error["message"],
                        }
                    )
        return warnings

    @staticmethod
    def extract_validation_errors(payload_data: dict) -> tuple:
        """Extracts error entries from a validation report.

        Args:
            payload_data (dict): The validation report returned by the API.

        Returns:
            tuple: A 2-tuple of (error_check_list, error_codes) where
                C(error_check_list) is the list of failed validation check objects
                and C(error_codes) is a flattened list of error code dicts.
        """
        result_status = payload_data.get("resultStatus", "")
        execution_status = payload_data.get("executionStatus", "")
        if result_status == "FAILED" or execution_status == "FAILED":
            error_check_list = []
            error_codes = []
            for check in payload_data.get("validationChecks", []):
                if (
                    check.get("resultStatus") == "FAILED"
                    or execution_status == "FAILED"
                ):
                    error_check_list.append(check)
                    for error in (
                        check.get("errorResponse", {}).get("nestedErrors", [])
                    ):
                        if "errorCode" in error:
                            error_codes.append(
                                {
                                    "errorCode": error["errorCode"],
                                    "errorMessage": error["message"],
                                }
                            )
            return error_check_list, error_codes
        return [], []

    def validate_instance(self) -> dict:
        """Submits the VCF Instance payload for validation and polls until complete.

        Polls every C(validation_poll_interval) seconds. Stops on a terminal
        success/failure status or when C(validation_timeout) wall-clock seconds have
        elapsed (C(0) = no limit).

        Returns:
            dict: A result dict with C(meta) (full validation report) and
                optionally C(warnings).

        The module will fail if:
            - The validation submission request fails.
            - The validation report indicates a C(FAILED) execution status.
            - C(validation_timeout) > 0 and the timeout elapses before completion.
        """
        try:
            validation_response = self.api_client.validate_sddc(
                json.dumps(self.sddc_management_domain_payload)
            )
            validation_id = validation_response["id"]
        except VcfApiException as e:
            self.module.fail_json(
                msg=f"Failed to submit VCF Instance payload for validation: {e}"
            )
        except (KeyError, TypeError):
            self.module.fail_json(
                msg="Failed to retrieve validation ID from the API response."
            )

        start_time = time.monotonic()

        while True:
            try:
                validation_report = self.api_client.get_sddc_validation(validation_id)
            except VcfApiException as e:
                self.module.fail_json(msg=f"Failed to retrieve validation status: {e}")

            execution_status = validation_report.get("executionStatus", "")
            warnings = self.extract_validation_warnings(validation_report)

            if execution_status == self._VALIDATION_FAILED_STATUS:
                _, error_codes = self.extract_validation_errors(validation_report)
                self.module.fail_json(
                    msg="VCF Instance payload validation failed. Review the error codes for details.",
                    meta={"error_codes": error_codes},
                    validation_warnings=warnings,
                )

            if execution_status in self._VALIDATION_SUCCESS_STATUSES:
                result = {"meta": validation_report}
                if warnings:
                    result["validation_warnings"] = warnings
                return result

            if self.validation_timeout > 0:
                elapsed = time.monotonic() - start_time
                if elapsed >= self.validation_timeout:
                    self.module.fail_json(
                        msg=(
                            f"VCF Instance validation timed out after {int(elapsed)}s "
                            f"(validation_timeout={self.validation_timeout}s). "
                            f"Last status: {execution_status}."
                        ),
                        meta=validation_report,
                    )

            time.sleep(self.validation_poll_interval)

    def create_instance(self) -> dict:
        """Submits the VCF Instance deployment request and polls until complete.

        Polls every C(deployment_poll_interval) seconds. Continues as long as the deployment
        is running regardless of individual subtask duration. Stops only on a terminal
        success/failure status, or when C(deployment_timeout) wall-clock seconds have
        elapsed (C(0) = no limit).

        Returns:
            dict: The final SDDC status response from the VCF Installer API.

        The module will fail if:
            - The deployment submission request fails.
            - The SDDC status indicates a C(FAILED) or C(COMPLETED_WITH_FAILURE) state.
            - C(deployment_timeout) > 0 and the timeout elapses before a terminal state.
        """
        try:
            create_response = self.api_client.create_sddc(
                json.dumps(self.sddc_management_domain_payload)
            )
            sddc_id = create_response["id"]
        except VcfApiException as e:
            self.module.fail_json(
                msg=f"Failed to submit VCF Instance deployment: {e}"
            )
        except (KeyError, TypeError):
            self.module.fail_json(
                msg="Failed to retrieve SDDC ID from the deployment API response."
            )

        start_time = time.monotonic()

        while True:
            try:
                sddc_status = self.api_client.get_sddc(sddc_id)
            except VcfApiException as e:
                self.module.fail_json(
                    msg=f"Failed to retrieve VCF Instance deployment status: {e}"
                )

            status = sddc_status.get("status", "")

            if status in self._DEPLOY_FAILED_STATUSES:
                failed_subtasks = [
                    {
                        "task_name": task.get("name"),
                        "task_description": task.get("description"),
                    }
                    for task in sddc_status.get("sddcSubTasks", [])
                    if task.get("status") in self._DEPLOY_SUBTASK_FAILED_STATUSES
                ]
                self.module.fail_json(
                    msg=(
                        "VCF Instance deployment failed. "
                        f"Additional logs: {self.vcf_installer_hostname}:"
                        "/var/log/vmware/vcf/domainmanager/domainmanager.log"
                    ),
                    meta={"errors": failed_subtasks, "status": status},
                )

            if status == self._DEPLOY_SUCCESS_STATUS:
                return sddc_status

            if self.deployment_timeout > 0:
                elapsed = time.monotonic() - start_time
                if elapsed >= self.deployment_timeout:
                    self.module.fail_json(
                        msg=(
                            f"VCF Instance deployment timed out after {int(elapsed)}s "
                            f"(deployment_timeout={self.deployment_timeout}s). "
                            f"Last status: {status}. "
                            "The deployment may still be running on the appliance. "
                            f"Additional logs: {self.vcf_installer_hostname}:"
                            "/var/log/vmware/vcf/domainmanager/domainmanager.log"
                        ),
                        meta=sddc_status,
                    )

            time.sleep(self.deployment_poll_interval)

    def retry_instance(self) -> dict:
        """Retries a failed SDDC deployment and polls until complete.

        Issues a C(PATCH /sddcs/{sddc_id}) retry request, then polls
        C(GET /sddcs/{sddc_id}) until the deployment reaches C(COMPLETED_WITH_SUCCESS).

        Polls every C(deployment_poll_interval) seconds. Continues as long as the deployment
        is running regardless of individual subtask duration. Stops only on a terminal
        success/failure status, or when C(deployment_timeout) wall-clock seconds have
        elapsed (C(0) = no limit).

        Returns:
            dict: The final SDDC status response from the VCF Installer API.

        The module will fail if:
            - The retry request fails.
            - The SDDC status indicates a terminal failure state.
            - C(deployment_timeout) > 0 and the timeout elapses before a terminal state.
        """
        try:
            self.api_client.retry_sddc(self.sddc_id)
        except VcfApiException as e:
            self.module.fail_json(
                msg=f"Failed to retry VCF Instance deployment (ID: {self.sddc_id}): {e}"
            )

        start_time = time.monotonic()

        while True:
            try:
                sddc_status = self.api_client.get_sddc(self.sddc_id)
            except VcfApiException as e:
                self.module.fail_json(
                    msg=f"Failed to retrieve VCF Instance status during retry: {e}"
                )

            status = sddc_status.get("status", "")

            if status in self._DEPLOY_FAILED_STATUSES:
                failed_subtasks = [
                    {
                        "task_name": task.get("name"),
                        "task_description": task.get("description"),
                    }
                    for task in sddc_status.get("sddcSubTasks", [])
                    if task.get("status") in self._DEPLOY_SUBTASK_FAILED_STATUSES
                ]
                self.module.fail_json(
                    msg=(
                        f"VCF Instance retry failed (ID: {self.sddc_id}). "
                        f"Additional logs: {self.vcf_installer_hostname}:"
                        "/var/log/vmware/vcf/domainmanager/domainmanager.log"
                    ),
                    meta={"errors": failed_subtasks, "status": status},
                )

            if status == self._DEPLOY_SUCCESS_STATUS:
                return sddc_status

            if self.deployment_timeout > 0:
                elapsed = time.monotonic() - start_time
                if elapsed >= self.deployment_timeout:
                    self.module.fail_json(
                        msg=(
                            f"VCF Instance retry (ID: {self.sddc_id}) timed out after "
                            f"{int(elapsed)}s (deployment_timeout={self.deployment_timeout}s). "
                            f"Last status: {status}. "
                            "The deployment may still be running on the appliance. "
                            f"Additional logs: {self.vcf_installer_hostname}:"
                            "/var/log/vmware/vcf/domainmanager/domainmanager.log"
                        ),
                        meta=sddc_status,
                    )

            time.sleep(self.deployment_poll_interval)

    def run(self):
        """Orchestrates the module workflow based on parameters and Ansible mode.

        Raises:
            AnsibleFailJson: If a mutually exclusive parameter combination is detected.
        """
        has_payload = bool(self.sddc_management_domain_payload)
        has_id = bool(self.sddc_id)

        # Mutual-exclusivity and presence checks
        if not has_payload and not has_id:
            self.module.fail_json(
                msg="One of 'sddc_management_domain_payload' or 'sddc_id' must be provided."
            )
        if has_payload and has_id:
            self.module.fail_json(
                msg="'sddc_management_domain_payload' and 'sddc_id' are mutually exclusive."
            )
        if has_id and self.validate_only:
            self.module.fail_json(
                msg="'validate_only' cannot be used together with 'sddc_id' (retry mode)."
            )

        if has_id:
            if self.module.check_mode:
                check_msg = (
                    f"Check Mode: VCF Instance '{self.sddc_id}' would be retried; "
                    "no changes were performed."
                )
                self.module.exit_json(
                    changed=True,
                    msg=check_msg,
                    meta={"message": check_msg},
                )
            result = self.retry_instance()
            self.module.exit_json(
                changed=True,
                msg=f"VCF Instance retry completed successfully (ID: {self.sddc_id}).",
                meta=result,
            )

        if self.validate_only:
            result = self.validate_instance()
            self.module.exit_json(
                changed=False,
                msg="VCF Instance payload validation completed successfully.",
                **result,
            )

        if self.module.check_mode:
            check_msg = (
                "Check Mode: VCF Instance would be deployed; "
                "no changes were performed."
            )
            self.module.exit_json(
                changed=True,
                msg=check_msg,
                meta={"message": check_msg},
            )

        self.validate_instance()
        result = self.create_instance()
        self.module.exit_json(
            changed=True,
            msg="VCF Instance deployed successfully.",
            meta=result,
        )


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    """
    parameters = dict(
        vcf_installer_hostname=dict(required=True, type="str"),
        vcf_installer_user=dict(required=True, type="str"),
        vcf_installer_password=dict(required=True, type="str", no_log=True),
        sddc_management_domain_payload=dict(required=False, type="dict", default=None),
        sddc_id=dict(required=False, type="str", default=None),
        validate_only=dict(required=False, type="bool", default=False),
        validation_timeout=dict(required=False, type="int", default=1800),
        validation_poll_interval=dict(required=False, type="int", default=30),
        deployment_timeout=dict(required=False, type="int", default=43200),
        deployment_poll_interval=dict(required=False, type="int", default=30),
    )

    module = AnsibleModule(supports_check_mode=True, argument_spec=parameters)
    instance = VcfInstallerInstance(module)
    instance.run()


if __name__ == "__main__":
    main()

