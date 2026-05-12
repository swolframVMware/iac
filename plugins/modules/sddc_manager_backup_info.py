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
module: sddc_manager_backup_info
short_description: Retrieves the backup configuration from SDDC Manager.
description:
    - This module retrieves the backup configuration from SDDC Manager for VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Get Backup Information
  broadcom.vcf.sddc_manager_backup_info:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
  register: backup_info

- name: Display Backup Information
  ansible.builtin.debug:
    msg: ""backup": {{ xxxx }}"
"""

RETURN = r"""
backup:
    description: Backup Information
    returned: on success
    type: dict
    sample:
        {
            "backup": [
                {
                    "ipAddress": "192.168.0.253"
                }
            ]
        }
changed:
    description: Whether the module made changes
    returned: always
    type: bool
    sample: false
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


class SddcManagerBackupInfo:
    """This class represents the backup configuration information retrieval in SDDC Manager.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager
            instance.
        sddc_manager_user (str): The username for authenticating with the SDDC
            Manager.
        sddc_manager_password (str): The password for authenticating with the SDDC
            Manager.

    Methods:
        get_backup_configuration(self): Retrieves backup configuration from SDDC Manager.
        run(self): Runs the backup configuration retrieval process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params["sddc_manager_hostname"]
        self.sddc_manager_user = module.params["sddc_manager_user"]
        self.sddc_manager_password = module.params["sddc_manager_password"]
        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )

    def get_backup_configuration(self):
        """Retrieves backup configuration from SDDC Manager."""
        try:
            api_response = self.api_client.get_backup_configuration()
            self.module.exit_json(changed=False, backup=api_response)

        except VcfApiException as e:
            self.module.fail_json(msg=f"Error retrieving backup configuration: {e}")

    def run(self):
        """Runs the backup configuration retrieval process."""
        self.get_backup_configuration()


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = dict(
        sddc_manager_hostname=dict(required=True, type="str"),
        sddc_manager_user=dict(required=True, type="str"),
        sddc_manager_password=dict(required=True, type="str", no_log=True),
    )

    module = AnsibleModule(argument_spec=parameters, supports_check_mode=True)

    backup_info = SddcManagerBackupInfo(module)
    backup_info.run()


if __name__ == "__main__":
    main()
