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
module: sddc_manager_depot_info
short_description: Retrieves the depot configuration from SDDC Manager.
description:
    - This module retrieves the depot configuration from SDDC Manager for VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Get Depot Configuration
  broadcom.vcf.sddc_manager_depot_info:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
  register: depot_config

- name: Display Status Message
  ansible.builtin.debug:
    msg: "{{ depot_config.msg }}"

- name: Display Configuration Details
  ansible.builtin.debug:
    var: depot_config.depot
"""

RETURN = r"""
depot:
    description: The depot configuration details.
    returned: always
    type: dict
    sample:
        vmwareAccount:
            status: "DEPOT_CONNECTION_SUCCESSFUL"
            message: "Depot Status: Success"
        depotConfiguration:
            hostname: "depot.example.com"
            port: 443
            isOfflineDepot: true
changed:
    description: Whether the module made changes.
    returned: always
    type: bool
    sample: false
msg:
    description: A status message describing the depot configuration state.
    returned: always
    type: str
    sample: "Online depot is configured and operational."
    alternatives:
        - "Offline depot is configured and operational. (depot.example.com:443)"
        - "Online depot configured but not available."
        - "Offline depot configured but not available. (depot.example.com:443)"
        - "No depot configuration has been set."
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


class SddcManagerDepotInfo:
    """This class represents the depot configuration information retrieval in SDDC Manager.

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
        get_depot_settings(self): Retrieves the depot configuration from SDDC Manager.
        run(self): Runs the depot configuration retrieval process.

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

    def get_depot_settings(self):
        """Retrieves depot configuration from SDDC Manager."""
        try:
            api_response = self.api_client.get_depot_settings()

            # Extract the relevant information from the response.
            vmware_account = api_response.get("vmwareAccount") if api_response else None
            offline_account = (
                api_response.get("offlineAccount") if api_response else None
            )
            depot_config = (
                api_response.get("depotConfiguration") if api_response else None
            )

            # Determine the appropriate message based on the depot configuration.
            msg = self._build_depot_message(
                vmware_account, offline_account, depot_config
            )

            self.module.exit_json(
                changed=False, depot=api_response if api_response else {}, msg=msg
            )

        except VcfApiException as e:
            self.module.fail_json(msg=f"Error retrieving depot configuration: {e}")

    def _build_depot_message(
        self, vmware_account, offline_account, depot_config
    ) -> str:
        """Builds a descriptive message based on depot configuration.

        Args:
            vmware_account: The online depot account information.
            offline_account: The offline depot account information.
            depot_config: The depot configuration details.

        Returns:
            str: A status message describing the depot configuration state.
        """
        # Check if neither depot is configured.
        if not vmware_account and not offline_account:
            return "No depot configuration has been set."

        # Determine depot type.
        is_offline = False
        hostname = "Unknown"
        port = None

        # Check the depot configuration details.
        if depot_config:
            is_offline = depot_config.get("isOfflineDepot", False)
            hostname = depot_config.get("hostname", "Unknown")
            port = depot_config.get("port")

        # Process online depot.
        if vmware_account and vmware_account.get("status"):
            status = vmware_account.get("status", "")
            message = vmware_account.get("message", "")

            if status == "DEPOT_CONNECTION_SUCCESSFUL":
                return "Online depot is configured and operational."
            elif status == "DEPOT_INVALID_CREDENTIAL":
                return "Online depot configured but the download token is invalid."
            elif status == "DEPOT_NOT_AVAILABLE":
                return "Online depot configured but not available."
            elif status == "DEPOT_UNKNOWN_HOST":
                return "Online depot configured with an unknown host."
            elif status == "DEPOT_USER_NOT_SET":
                return (
                    "Online depot configured but the download token has not been set."
                )
            elif message:
                return f"Online Depot Status: {message}."
            else:
                return f"Online Depot Status: {status}."

        # Process offline depot.
        if offline_account and offline_account.get("status"):
            status = offline_account.get("status", "")
            message = offline_account.get("message", "")

            location = f"{hostname}:{port}" if port else hostname

            if status == "DEPOT_CONNECTION_SUCCESSFUL":
                return f"Offline depot is configured and operational. ({location})"
            elif status == "DEPOT_INVALID_CREDENTIAL":
                return f"Offline depot configured but the credentials are invalid. ({location})"
            elif status == "DEPOT_NOT_AVAILABLE":
                return f"Offline depot configured but not available. ({location})"
            elif status == "DEPOT_UNKNOWN_HOST":
                return f"Offline depot configured with an unknown host. ({location})"
            elif status == "DEPOT_USER_NOT_SET":
                return f"Offline depot configured but a user has not been set. ({location})"
            elif message:
                return f"Offline Depot Status: {message} ({location})"
            else:
                return f"Offline Depot Status: {status} ({location})"

        # Fallback for unexpected configuration.
        depot_type = "Offline" if is_offline else "Online"
        return f"{depot_type} Depot Status: Unknown"

    def run(self):
        """Runs the depot configuration retrieval process."""
        self.get_depot_settings()


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

    depot_info = SddcManagerDepotInfo(module)
    depot_info.run()


if __name__ == "__main__":
    main()
