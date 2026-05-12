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
module: sddc_manager_dns
short_description: Manages DNS configuration update in SDDC Manager.
description:
    - This module manages the Domain Name System (DNS) configuration update in SDDC Manager for VMware Cloud Foundation.
    - This module can update DNS and monitors the task status.
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
- name: Validate DNS Configuration
  broadcom.vcf.sddc_manager_dns:
    sddc_manager_hostname: "{{ all_iac_vars.sddc_manager.hostname }}"
    sddc_manager_user: "{{ all_iac_vars.vsphere.vcenter.sso.username }}"
    sddc_manager_password: "{{ vcenter_administrator_password | default(all_iac_vars.vsphere.vcenter.sso.password) }}"
    dns_config: "{{ dns_config }}"
    state: "{{ dns_state }}"
    validate_only: true
  register: dns_result

- name: Update DNS Configuration
  broadcom.vcf.sddc_manager_dns:
    sddc_manager_hostname: "{{ all_iac_vars.sddc_manager.hostname }}"
    sddc_manager_user: "{{ all_iac_vars.vsphere.vcenter.sso.username }}"
    sddc_manager_password: "{{ vcenter_administrator_password | default(all_iac_vars.vsphere.vcenter.sso.password) }}"
    dns_config: "{{ dns_config }}"
    state: "{{ dns_state }}"
  register: dns_result

- name: Display the result message
  ansible.builtin.debug:
    var: result.msg
"""

RETURN = r"""
msg:
    description: Status message about the operation or error details
    returned: on failure or when no change is needed
    type: str
    sample: "The DNS configuration is compliant with the desired state."
task:
    description: Task information for the DNS configuration update operation
    returned: on success when state changes
    type: dict
    sample: "Successfully updated the DNS configuration."
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


class SddcManagerDns:
    """This class represents DNS management in SDDC Manager.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager instance.
        sddc_manager_user (str): The username for authenticating with the SDDC Manager.
        sddc_manager_password (str): The password for authenticating with the SDDC Manager.
        dns_config (dict): DNS configuration.
        state (str): The desired state of DNS (update).

    Methods:
        validate_dns_configuration(self): Validates DNS configuration.
        get_dns_configuration_validations(self): Retrieves a list of DNS configuration validations.
        update_dns_configuration(self): Updates the DNS configuration.
        get_dns_configuration(self): Retrieves the DNS configuration.
        run(self): Runs the DNS process.

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
        self.dns_config = module.params["dns_config"]
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

    def is_dns_different(self, current_config):
        return self._normalize(current_config) != self._normalize(self.dns_config)

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
            response = self.get_dns_configuration_validations()
            success, errors = self.evaluate_validation(response[-1])
            if errors:
                self.module.fail_json(
                    msg="DNS validation failed",
                    errors=errors,
                )
            return success

        self._poll_until(
            validation_complete,
            "Validation timed out",
        )

    def wait_for_update(self):
        time.sleep(self.POLL_INTERVAL)

        def config_matches():
            current = self.get_dns_configuration()
            return not self.is_dns_different(current)

        self._poll_until(
            config_matches,
            "DNS update failed: configuration did not match",
        )

    def evaluate_validation(self, data):
        """Evaluates the response data from the SDDC Manager API."""
        if data.get("resultStatus") != "SUCCEEDED":
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

    def validate_dns_configuration(self):
        """Validates the DNS configuration in SDDC Manager."""
        try:
            return self.api_client.validate_dns_configuration(
                json.dumps(self.dns_config)
            )
        except VcfApiException as e:
            self.module.fail_json(msg=f"Failed to validate DNS configuration: {e}")

    def get_dns_configuration_validations(self):
        """Retrieves a list of completed DNS configuration validations."""
        try:
            return self.api_client.get_dns_configuration_validations()
        except VcfApiException as e:
            self.module.fail_json(msg=f"Failed retrieving validation results: {e}")

    def update_dns_configuration(self):
        """Updates the DNS configuration in SDDC Manager."""
        try:
            return self.api_client.update_dns_configuration(json.dumps(self.dns_config))
        except VcfApiException as e:
            self.module.fail_json(msg=f"DNS update failed: {e}")

    def get_dns_configuration(self):
        """Retrieves the DNS configuration from SDDC Manager."""
        try:
            return self.api_client.get_dns_configuration()
        except VcfApiException as e:
            self.module.fail_json(
                msg=f"Failed retrieving current DNS configuration: {e}"
            )

    def run(self):
        """Runs the DNS process."""

        current_config = self.get_dns_configuration()
        if not self.is_dns_different(current_config):
            self.module.exit_json(
                changed=False,
                msg="The DNS configuration is compliant with the desired state.",
                current_config=self.dns_config,
            )

        # Handle validation-only mode.
        if self.validate_only:
            self.validate_dns_configuration()
            self.wait_for_validation()
            self.module.exit_json(
                changed=False,
                msg="Successfully validated the DNS configuration; no changes were performed.",
            )

        # Handle check mode.
        if self.module.check_mode:
            self.module.exit_json(
                changed=True,
                msg=f"Check Mode: Would update DNS configuration from {[c["ipAddress"] for c in current_config["dnsServers"]]} to {[p["ipAddress"] for p in self.dns_config["dnsServers"]]}. No changes were performed.",
                proposed_config=self.dns_config,
                current_config=current_config,
            )

        # Execute the operation.
        self.update_dns_configuration()
        self.wait_for_update()
        self.module.exit_json(
            changed=True,
            msg="Successfully updated the DNS configuration.",
            updated_config=self.dns_config,
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
        dns_config=dict(required=True, type="dict"),
        state=dict(required=False, type="str", choices=["update"], default="update"),
        validate_only=dict(required=False, type="bool", default=False),
    )

    module = AnsibleModule(argument_spec=parameters, supports_check_mode=True)

    dns = SddcManagerDns(module)
    dns.run()


if __name__ == "__main__":
    main()
