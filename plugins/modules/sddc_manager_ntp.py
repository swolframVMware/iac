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
module: sddc_manager_ntp
short_description: Manages NTP configuration update in SDDC Manager.
description:
    - This module manages the Network Time Protocol (NTP) configuration update in SDDC Manager for VMware Cloud Foundation.
    - This module can update NTP and monitors the task status.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    state:
        required: true
        type: str
        choices:
            - update
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Validate NTP Configuration
  broadcom.vcf.sddc_manager_ntp:
    sddc_manager_hostname: "{{ all_iac_vars.sddc_manager.hostname }}"
    sddc_manager_user: "{{ all_iac_vars.vsphere.vcenter.sso.username }}"
    sddc_manager_password: "{{ vcenter_administrator_password | default(all_iac_vars.vsphere.vcenter.sso.password) }}"
    ntp_config: "{{ ntp_config }}"
    state: "{{ ntp_state }}"
    validate_only: true
  register: ntp_result

- name: Update NTP Configuration
  broadcom.vcf.sddc_manager_ntp:
    sddc_manager_hostname: "{{ all_iac_vars.sddc_manager.hostname }}"
    sddc_manager_user: "{{ all_iac_vars.vsphere.vcenter.sso.username }}"
    sddc_manager_password: "{{ vcenter_administrator_password | default(all_iac_vars.vsphere.vcenter.sso.password) }}"
    ntp_config: "{{ ntp_config }}"
    state: "{{ ntp_state }}"
  register: ntp_result

- name: Display the result message
  ansible.builtin.debug:
    var: result.msg
"""

RETURN = r"""
msg:
    description: Status message about the operation or error details
    returned: on failure or when no change is needed
    type: str
    sample: "The NTP configuration is compliant with the desired state."
task:
    description: Task information for the NTP configuration update operation
    returned: on success when state changes
    type: dict
    sample: "Successfully updated the NTP configuration."
changed:
    description: Whether the module made changes
    returned: always
    type: bool
    sample: true
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


class SddcManagerNtp:
    """This class represents NTP management in SDDC Manager.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager instance.
        sddc_manager_user (str): The username for authenticating with the SDDC Manager.
        sddc_manager_password (str): The password for authenticating with the SDDC Manager.
        ntp_config (dict): NTP configuration.
        state (str): The desired state of NTP (update).

    Methods:
        validate_ntp_configuration(self): Validates NTP configuration.
        get_ntp_configuration_validations(self): Retrieves a list of NTP configuration validations.
        update_ntp_configuration(self): Updates the NTP configuration.
        get_ntp_configuration(self): Retrieves the NTP configuration.
        run(self): Runs the NTP process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    POLL_INTERVAL = 10
    POLL_TIMEOUT = 300

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params["sddc_manager_hostname"]
        self.sddc_manager_user = module.params["sddc_manager_user"]
        self.sddc_manager_password = module.params["sddc_manager_password"]
        self.ntp_config = module.params["ntp_config"]
        self.state = module.params["state"]
        self.validate_only = module.params["validate_only"]
        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )

    @staticmethod
    def _normalize(data):
        return json.dumps(data, sort_keys=True)

    def is_ntp_different(self, current_config):
        return self._normalize(current_config) != self._normalize(self.ntp_config)

    def _poll_until(self, condition_func, failure_message):
        """Generic polling helper."""
        start_time = time.time()
        last_result = None

        while time.time() - start_time < self.POLL_TIMEOUT:
            last_result = condition_func()
            if last_result:
                return
            time.sleep(self.POLL_INTERVAL)

        self.module.fail_json(
            msg=failure_message,
            timeout=self.POLL_TIMEOUT,
        )

    def wait_for_validation(self):
        def validation_complete():
            response = self.get_ntp_configuration_validations()
            success, errors = self.evaluate_validation(response[-1])
            if errors:
                self.module.fail_json(
                    msg="NTP validation failed",
                    errors=errors,
                )
            return success

        self._poll_until(
            validation_complete,
            "Validation timed out",
        )

    def wait_for_update(self):
        def config_matches():
            current = self.get_ntp_configuration()
            return not self.is_ntp_different(current)

        self._poll_until(
            config_matches,
            "NTP update failed: configuration did not match",
        )

    def evaluate_validation(self, data):
        """Evaluates the response data from the SDDC Manager API."""
        if data.get("resultStatus") == "FAILED":
            errors = []
            for check in data.get("validationChecks", []):
                if check.get("resultStatus") == "FAILED":
                    error = check.get("errorResponse") or {}
                    errors.append(
                        {
                            "errorCode": error.get("errorCode"),
                            "message": error.get("message"),
                            "arguments": error.get("arguments"),
                        }
                    )
            return False, errors
        return True, []

    def validate_ntp_configuration(self):
        """Validates the NTP configuration in SDDC Manager."""
        try:
            return self.api_client.validate_ntp_configuration(
                json.dumps(self.ntp_config)
            )
        except VcfApiException as e:
            self.module.fail_json(msg=f"Failed to validate NTP configuration: {e}")

    def get_ntp_configuration_validations(self):
        """Retrieves a list of completed NTP configuration validations."""
        try:
            return self.api_client.get_ntp_configuration_validations()
            # return self.api_client.get_ntp_configuration_validations("COMPLETED")
        except VcfApiException as e:
            self.module.fail_json(msg=f"Failed retrieving validation results: {e}")

    def update_ntp_configuration(self):
        """Updates the NTP configuration in SDDC Manager."""
        try:
            return self.api_client.update_ntp_configuration(json.dumps(self.ntp_config))
        except VcfApiException as e:
            self.module.fail_json(msg=f"NTP update failed: {e}")

    def get_ntp_configuration(self):
        """Retrieves the NTP configuration from SDDC Manager."""
        try:
            return self.api_client.get_ntp_configuration()
        except VcfApiException as e:
            self.module.fail_json(
                msg=f"Failed retrieving current NTP configuration: {e}"
            )

    def run(self):
        """Runs the NTP process."""

        current_config = self.get_ntp_configuration()
        if not self.is_ntp_different(current_config):
            self.module.exit_json(
                changed=False,
                msg="The NTP configuration is compliant with the desired state.",
                current_config=self.ntp_config,
            )

        # Handle validation-only mode.
        if self.validate_only:
            self.validate_ntp_configuration()
            self.wait_for_validation()
            self.module.exit_json(
                changed=False,
                msg="Successfully updated the NTP configuration; no changes were performed.",
            )

        # Handle check mode.
        if self.module.check_mode:
            self.module.exit_json(
                changed=True,
                msg=f"Check Mode: Would update NTP configuration from {[c["ipAddress"] for c in current_config["ntpServers"]]} to {[p["ipAddress"] for p in self.ntp_config["ntpServers"]]}. No changes were performed.",
                proposed_config=self.ntp_config,
                current_config=current_config,
            )

        # Execute the operation.
        self.update_ntp_configuration()
        self.wait_for_update()
        self.module.exit_json(
            changed=True,
            msg="Successfully updated the NTP configuration.",
            updated_config=self.ntp_config,
        )


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = dict(
        sddc_manager_hostname=dict(required=True, type="str"),
        sddc_manager_user=dict(required=True, type="str"),
        sddc_manager_password=dict(required=True, type="str", no_log=True),
        ntp_config=dict(required=True, type="dict"),
        state=dict(required=False, type="str", choices=["update"], default="update"),
        validate_only=dict(required=False, type="bool", default=False),
    )

    module = AnsibleModule(argument_spec=parameters, supports_check_mode=True)

    ntp = SddcManagerNtp(module)
    ntp.run()


if __name__ == "__main__":
    main()
