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
module: sddc_manager_check_sets_trigger_status
short_description: Retrieves the status of a check set validation from SDDC Manager
description:
    - This module retrieves the status of a check set validation from SDDC Manager for VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    check_set_run_id:
        description:
            - The check set run id.
        required: true
        type: str
    sddc_manager_check_sets_settings:
        description:
            - The settings for the check sets.
        required: true
        type: dict
    retries:
        description:
            - The number of retries to check the status of the check set.
        required: false
        type: int
        default: 60
    delay:
        description:
            - The delay between retries.
        required: false
        type: int
        default: 30
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Wait for check set validation to complete
  broadcom.vcf.sddc_manager_check_sets_trigger_status:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    sddc_manager_check_sets_settings:
      ignore_warnings: false
      ignore_critical_errors: false
      sddc_manager_check_set_white_list:
        - sddc-manager-vcenter-license-state
        - sddc-manager-vsan-license-state
    check_set_run_id: 12345678-1234-1234-1234-123456789012
    retries: 60
    delay: 30
  register: check_set_result

- name: Wait for check set validation with custom retries
  broadcom.vcf.sddc_manager_check_sets_trigger_status:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    sddc_manager_check_sets_settings:
      ignore_warnings: true
      ignore_critical_errors: false
      sddc_manager_check_set_white_list: []
    check_set_run_id: 12345678-1234-1234-1234-123456789012
    retries: 120
    delay: 60
  register: check_set_result
"""

RETURN = r"""
msg:
    description: Status message indicating validation result
    returned: always
    type: str
meta:
    description: The complete validation report from SDDC Manager
    returned: always
    type: dict
warnings:
    description: List of validation warnings that were ignored based on settings
    returned: when validation completes with warnings
    type: list
    elements: dict
error_codes:
    description: List of validation errors that were not whitelisted
    returned: when validation fails
    type: list
    elements: dict
"""

import json
import time

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


def extract_errors(payload_data):
    """Extracts validation errors from the payload data."""
    error_check_list = []
    validation_result = payload_data.get("validationResult", {})
    if validation_result.get("nestedErrors"):
        # =============================================================================
        # Getting Nested Errors
        # =============================================================================
        for nested_error_level_1 in validation_result["nestedErrors"]:
            # Get Level One Errors
            if nested_error_level_1.get("nestedErrors"):
                # Get Level 2 Errors
                nested_error_level_2 = nested_error_level_1["nestedErrors"]
                for nested_error_level_2_item in nested_error_level_2:
                    # Get Level 3 Errors
                    if nested_error_level_2_item.get("nestedErrors"):
                        nested_error_level_3 = nested_error_level_2_item["nestedErrors"]
                        for error in nested_error_level_3:
                            # Get Level 3 errors
                            if (
                                error.get("context")
                                and error["context"].get("validationStatus")
                                == "VALIDATION_FAILED"
                            ):
                                error_check_list.append(error["context"])
                    elif (
                        nested_error_level_2_item.get("context")
                        and nested_error_level_2_item["context"].get("validationStatus")
                        == "VALIDATION_FAILED"
                    ):
                        error_check_list.append(nested_error_level_2_item["context"])
            elif (
                nested_error_level_1.get("context")
                and nested_error_level_1["context"].get("validationStatus")
                == "VALIDATION_FAILED"
            ):
                error_check_list.append(nested_error_level_1["context"])
    return error_check_list


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = {
        "sddc_manager_hostname": {"required": True, "type": "str"},
        "sddc_manager_user": {"required": True, "type": "str"},
        "sddc_manager_password": {"required": True, "type": "str", "no_log": True},
        "sddc_manager_check_sets_settings": {"required": True, "type": "dict"},
        "check_set_run_id": {"required": True, "type": "str"},
        "retries": {"required": False, "type": "int", "default": 60},
        "delay": {"required": False, "type": "int", "default": 30},
    }

    module = AnsibleModule(supports_check_mode=True, argument_spec=parameters)

    sddc_manager_hostname = module.params["sddc_manager_hostname"]
    sddc_manager_user = module.params["sddc_manager_user"]
    sddc_manager_password = module.params["sddc_manager_password"]
    sddc_manager_check_sets_settings = module.params["sddc_manager_check_sets_settings"]
    check_set_run_id = module.params["check_set_run_id"]
    retries = module.params["retries"]
    delay = module.params["delay"]

    ignore_warnings = sddc_manager_check_sets_settings["ignore_warnings"]
    ignore_critical_errors = sddc_manager_check_sets_settings["ignore_critical_errors"]
    sddc_manager_check_set_white_list = sddc_manager_check_sets_settings[
        "sddc_manager_check_set_white_list"
    ]

    try:
        api_client = SddcManagerApiClient(
            sddc_manager_hostname, sddc_manager_user, sddc_manager_password
        )

        for attempt in range(retries):
            validation_report = api_client.get_sddc_manager_check_set_status(
                check_set_run_id
            )
            payload_data = validation_report.data

            error_codes = extract_errors(payload_data)

            filtered_errors = [
                error
                for error in error_codes
                if error["validatorDefinitionId"]
                not in sddc_manager_check_set_white_list
            ]

            if payload_data["status"] == "COMPLETED_WITH_FAILURE":
                response = {"error_codes": filtered_errors}
                if filtered_errors:
                    if (
                        any(
                            error["importanceLevel"] == "CRITICAL"
                            for error in filtered_errors
                        )
                        and not ignore_critical_errors
                    ):
                        module.fail_json(
                            changed=False,
                            msg="Validation failed with critical errors.",
                            meta=response,
                        )
                    elif (
                        any(
                            error["importanceLevel"] == "WARNING"
                            for error in filtered_errors
                        )
                        and not ignore_warnings
                    ):
                        module.fail_json(
                            changed=False,
                            msg="Validation failed with warnings.",
                            meta=response,
                        )
                    else:
                        module.fail_json(
                            changed=False,
                            msg="Validation failed.",
                            meta=payload_data,
                            warnings=filtered_errors,
                        )
                else:
                    module.fail_json(
                        changed=False, msg="Validation failed.", meta=payload_data
                    )
            elif payload_data["status"] == "COMPLETED_WITH_SUCCESS":
                response = {"error_codes": filtered_errors}
                if filtered_errors:
                    if (
                        any(
                            error["importanceLevel"] == "CRITICAL"
                            for error in filtered_errors
                        )
                        and not ignore_critical_errors
                    ):
                        module.fail_json(
                            changed=False,
                            msg="Validation failed with critical errors.",
                            meta=response,
                        )
                    elif (
                        any(
                            error["importanceLevel"] == "WARNING"
                            for error in filtered_errors
                        )
                        and not ignore_warnings
                    ):
                        module.fail_json(
                            changed=False,
                            msg="Validation failed with warnings.",
                            meta=response,
                        )
                    else:
                        module.exit_json(
                            changed=False,
                            meta=payload_data,
                            warnings=json.dumps(
                                f"Validation passed with the following errors not included in the white list: {filtered_errors}"
                            ),
                        )
                else:
                    module.exit_json(
                        changed=False,
                        meta=payload_data,
                        warnings=f"Validation passed with the following warnings raised in the pre-check: {error_codes}",
                    )

            time.sleep(delay)

        module.fail_json(
            changed=False,
            msg="Exceeded maximum retries, validation did not complete within the allotted time.",
        )
    except Exception as e:
        module.fail_json(
            changed=False,
            msg=f"Validation failed: {str(e)} but ignore_warnings: {ignore_warnings} and ignore_critical_errors: {ignore_critical_errors}",
        )


if __name__ == "__main__":
    main()
