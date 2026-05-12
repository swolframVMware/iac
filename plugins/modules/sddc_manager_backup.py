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
module: sddc_manager_backup
short_description: Manages backup configuration in SDDC Manager.
description:
    - This module manages the backup configuration n SDDC Manager for VMware Cloud Foundation.
    - This module can update backup and monitors the task status.
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
- name: Validate Backup Configuration
  broadcom.vcf.sddc_manager_backup:
    sddc_manager_hostname: "{{ all_iac_vars.sddc_manager.hostname }}"
    sddc_manager_user: "{{ all_iac_vars.vsphere.vcenter.sso.username }}"
    sddc_manager_password: "{{ vcenter_administrator_password | default(all_iac_vars.vsphere.vcenter.sso.password) }}"
    backup_iac_config: "{{ backup_iac_config }}"
    backup_encryption_passphrase: "{{ backup_encryption_passphrase | default(omit) }}"
    backup_password:  "{{ backup_password | default(omit) }}"
    backup_ssh_fingerprint:  "{{ backup_ssh_fingerprint | default(omit) }}"
    state: "{{ backup_state }}"
    validate_only: true
  register: backup_result

- name: Update Backup Configuration
  broadcom.vcf.sddc_manager_backup:
    sddc_manager_hostname: "{{ all_iac_vars.sddc_manager.hostname }}"
    sddc_manager_user: "{{ all_iac_vars.vsphere.vcenter.sso.username }}"
    sddc_manager_password: "{{ vcenter_administrator_password | default(all_iac_vars.vsphere.vcenter.sso.password) }}"
    backup_iac_config: "{{ backup_iac_config }}"
    backup_encryption_passphrase: "{{ backup_encryption_passphrase | default(omit) }}"
    backup_password:  "{{ backup_password | default(omit) }}"
    backup_ssh_fingerprint:  "{{ backup_ssh_fingerprint | default(omit) }}"
    state: "{{ backup_state }}"
  register: backup_result

- name: Display Status Message
  ansible.builtin.debug:
    var: result.msg
"""

RETURN = r"""
msg:
    description: Status message about the operation or error details
    returned: on failure or when no change is needed
    type: str
    sample: "The backup configuration is compliant with the desired state."
task:
    description: Task information for the backup configuration update operation
    returned: on success when state changes
    type: dict
    sample: "Successfully updated the backup configuration."
changed:
    description: Whether the module made changes
    returned: always
    type: bool
    sample: true
"""

import json
import time
import copy

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


class SddcManagerBackup:
    """This class represents backup management in SDDC Manager.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager instance.
        sddc_manager_user (str): The username for authenticating with the SDDC Manager instance.
        sddc_manager_password (str): The password for authenticating with the SDDC Manager instance.
        backup_iac_config (dict): The backup configuration from IaC.
        backup_encryption_passphrase: The encryption passphrase for backup.
        backup_password: The password for backup.
        backup_ssh_fingerprint: The sshFingerprint for backup.
        state (str): The desired state of backup.

    Methods:
        validate_backup_configuration(self): Validates backup configuration.
        update_backup_configuration(self): Updates the backup configuration.
        get_backup_configuration(self): Retrieves the backup configuration.
        run(self): Runs the backup process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    POLL_INTERVAL = 15
    POLL_TIMEOUT = 120

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params["sddc_manager_hostname"]
        self.sddc_manager_user = module.params["sddc_manager_user"]
        self.sddc_manager_password = module.params["sddc_manager_password"]
        self.backup_iac_config = module.params["backup_iac_config"]
        self.backup_password = module.params["backup_password"]
        self.backup_encryption_passphrase = module.params[
            "backup_encryption_passphrase"
        ]
        self.backup_ssh_fingerprint = module.params["backup_ssh_fingerprint"]
        self.state = module.params["state"]
        self.validate_only = module.params["validate_only"]
        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )

    def _build_backup_config(self):
        config = copy.deepcopy(self.backup_iac_config)
        for location in config.get("backupLocations", []):
            location["password"] = self.backup_password
            location["sshFingerprint"] = self.backup_ssh_fingerprint
        config["encryption"] = {}
        config["encryption"]["passphrase"] = self.backup_encryption_passphrase
        return config

    def _normalize(self, data):
        return json.dumps(data, sort_keys=True)

    def is_backup_different(self, current_config):
        config = copy.deepcopy(self.backup_iac_config)
        for location in config["backupLocations"]:
            location["sshFingerprint"] = self.backup_ssh_fingerprint
        current = self._normalize(current_config)
        proposed = self._normalize(config)
        return current != proposed

    def dict_diff(self, current):

        desired = copy.deepcopy(self.backup_iac_config)
        for location in desired["backupLocations"]:
            location["sshFingerprint"] = self.backup_ssh_fingerprint

        path = ""
        diff = {}
        current_keys = set(current.keys())
        desired_keys = set(desired.keys())

        for k in desired_keys - current_keys:
            diff[f"{path}{k}"] = {
                "OLD": "<missing>",
                "NEW": desired[k],
            }

        for k in current_keys - desired_keys:
            diff[f"{path}{k}"] = {
                "OLD": current[k],
                "NEW": "<removed>",
            }

        for k in desired_keys & current_keys:
            v_current = current[k]
            v_desired = desired[k]
            current_path = f"{path}{k}."

            if isinstance(v_current, dict) and isinstance(v_desired, dict):
                nested = self._recursive_diff(v_current, v_desired, current_path)
                diff.update(nested)

            elif isinstance(v_current, list) and isinstance(v_desired, list):
                if v_current != v_desired:
                    diff[f"{path}{k}"] = {
                        "OLD": v_current,
                        "NEW": v_desired,
                    }

            elif v_current != v_desired:
                diff[f"{path}{k}"] = {
                    "OLD": v_current,
                    "NEW": v_desired,
                }

        return diff

    def _poll_until(self, condition_func, failure_message):
        """Generic polling helper."""
        start_time = time.time()
        while time.time() - start_time < self.POLL_TIMEOUT:
            if condition_func():
                return
            time.sleep(self.POLL_INTERVAL)
        self.module.fail_json(
            msg=failure_message,
            timeout=self.POLL_TIMEOUT,
        )

    def wait_for_update(self):
        time.sleep(self.POLL_INTERVAL)

        def config_matches():
            current = self.get_backup_configuration()
            return not self.is_backup_different(current)

        self._poll_until(
            config_matches,
            "backup update failed: configuration did not match",
        )

    def validate_backup_configuration(self):
        """Validates the backup configuration in SDDC Manager."""
        try:
            return self.api_client.validate_backup_configuration(
                json.dumps(self._build_backup_config())
            )
        except VcfApiException as e:
            self.module.fail_json(msg=f"Failed to validate backup configuration: {e}")

    def update_backup_configuration(self):
        """Updates the backup configuration in SDDC Manager."""
        try:
            return self.api_client.update_backup_configuration(
                json.dumps(self._build_backup_config())
            )
        except VcfApiException as e:
            self.module.fail_json(msg=f"backup update failed: {e}")

    def get_backup_configuration(self):
        """Retrieves the backup configuration from SDDC Manager."""
        try:
            return self.api_client.get_backup_configuration()
        except VcfApiException as e:
            self.module.fail_json(
                msg=f"Failed retrieving current backup configuration: {e}"
            )

    def run(self):
        """Runs the backup process."""

        current_config = self.get_backup_configuration()
        if not self.is_backup_different(current_config):
            self.module.exit_json(
                changed=False,
                msg="The backup configuration is compliant with the desired state.",
                current_config=current_config,
            )

        # Handle validation-only mode.
        if self.validate_only:
            self.validate_backup_configuration()
            self.module.exit_json(
                changed=False,
                msg="Successfully validated the backup configuration; no changes were performed.",
                proposed_config=self.backup_iac_config,
                current_config=current_config,
            )

        differences = self.dict_diff(current_config)
        # Handle check mode.
        if self.module.check_mode:
            self.module.exit_json(
                changed=True,
                msg=f"Check Mode: Would update the backup configuration differences {differences}. No changes were performed.",
                proposed_config=self.backup_iac_config,
                current_config=current_config,
            )

        # Execute the operation.
        self.update_backup_configuration()
        self.wait_for_update()
        self.module.exit_json(
            changed=True,
            msg="Successfully updated the backup configuration.",
            proposed_config=self.backup_iac_config,
            differences=differences,
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
        backup_iac_config=dict(required=True, type="dict"),
        backup_encryption_passphrase=dict(required=True, type="str", no_log=True),
        backup_password=dict(required=True, type="str", no_log=True),
        backup_ssh_fingerprint=dict(required=False, type="str", default=None),
        state=dict(required=False, type="str", choices=["update"], default="update"),
        validate_only=dict(required=False, type="bool", default=False),
    )

    module = AnsibleModule(argument_spec=parameters, supports_check_mode=True)

    backup = SddcManagerBackup(module)
    backup.run()


if __name__ == "__main__":
    main()
