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

__metaclass__ = type

DOCUMENTATION = r"""
---
module: vcf_installer_depot
short_description: Manage depot configuration in VCF Installer
description:
    - This module manages the depot configuration in VCF Installer for VMware Cloud Foundation.
    - It supports enabling online depot, offline depot, or disabling depot configuration.
version_added: "1.0.0"
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.vcf_installer
options:
    state:
        description:
            - The desired state of the depot configuration.
            - C(present) will configure the depot (online or offline based on depot_type).
            - C(absent) will remove the depot configuration.
        required: true
        type: str
        choices: ['present', 'absent']
    depot_type:
        description:
            - The type of depot to configure.
            - C(online) configures an online depot connection.
            - C(offline) configures an offline depot.
            - Required when state is C(present).
        required: false
        type: str
        choices: ['online', 'offline']
    download_token:
        description:
            - The download token for the Broadcom Support Portal.
            - Mutually exclusive with C(activation_code).
            - One of C(download_token) or C(activation_code) is required when depot_type is C(online) and state is C(present).
            - Supported on VCF 9.0.x.x.
        required: false
        type: str
    activation_code:
        description:
            - The activation code for the Broadcom Support Portal.
            - Mutually exclusive with C(download_token).
            - One of C(download_token) or C(activation_code) is required when depot_type is C(online) and state is C(present).
            - Supported on VCF 9.1.x.x+.
        required: false
        type: str
    offline_hostname:
        description:
            - The hostname or IP address of the offline depot instance.
            - Required when depot_type is C(offline) and state is C(present).
        required: false
        type: str
    offline_port:
        description:
            - The port number of the offline depot instance.
            - Required when depot_type is C(offline) and state is C(present).
        required: false
        type: int
        default: 443
    offline_username:
        description:
            - The username for authenticating with the offline depot instance.
            - Required when depot_type is C(offline) and state is C(present).
        required: false
        type: str
    offline_password:
        description:
            - The password for authenticating with the offline depot instance.
            - Required when depot_type is C(offline) and state is C(present).
        required: false
        type: str
    offline_ssl_thumbprint:
        description:
            - The SSL thumbprint of the offline depot instance certificate.
            - Required when depot_type is C(offline) and state is C(present).
        required: false
        type: str
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Configure Online Depot with Download Token
  broadcom.vcf.vcf_installer_depot:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    state: present
    depot_type: online
    download_token: "{{ vmware_download_token }}"

- name: Configure Online Depot with Activation Code (9.1.x.x+)
  broadcom.vcf.vcf_installer_depot:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    state: present
    depot_type: online
    activation_code: "{{ vmware_activation_code }}"

- name: Configure Offline Depot
  broadcom.vcf.vcf_installer_depot:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    state: present
    depot_type: offline
    offline_hostname: depot.example.com
    offline_port: 443
    offline_username: depot_user
    offline_password: depot_password
    offline_ssl_thumbprint: "AB:CD:EF:12:34:56:78:90:AB:CD:EF:12:34:56:78:90:AB:CD:EF:12"

- name: Remove Depot Configuration
  broadcom.vcf.vcf_installer_depot:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    state: absent

- name: Configure Depot with result capture
  broadcom.vcf.vcf_installer_depot:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    state: present
    depot_type: offline
    offline_hostname: depot.example.com
    offline_port: 443
    offline_username: depot_user
    offline_password: depot_password
    offline_ssl_thumbprint: "AB:CD:EF:12:34:56:78:90:AB:CD:EF:12:34:56:78:90:AB:CD:EF:12"
  register: depot_result

- name: Display depot result
  ansible.builtin.debug:
    var: depot_result.msg
"""

RETURN = r"""
msg:
    description: Status message about the operation or error details
    returned: always
    type: str
    sample: "Depot configuration updated to offline depot."
    alternatives:
        - "Depot configuration updated to online depot."
        - "Changed depot type from online to offline."
        - "Changed depot type from offline to online."
        - "Depot configuration removed."
        - "No depot configuration exists."
        - "Depot already configured as requested."
changed:
    description: Whether the module made changes
    returned: always
    type: bool
    sample: true
depot:
    description: Current depot configuration after the operation
    returned: when state is present
    type: dict
    sample:
        vmwareAccount:
            status: "DEPOT_CONNECTION_SUCCESSFUL"
            message: "Depot Status: Success"
        depotConfiguration:
            hostname: "depot.example.com"
            port: 443
            isOfflineDepot: true
"""

import json

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.vcf_installer import (
    VcfInstallerApiClient,
)


class VcfInstallerDepot:
    """This class represents depot management in VCF Installer.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        vcf_installer_hostname (str): The hostname or IP address of the VCF Installer instance.
        vcf_installer_user (str): The username for authenticating with the VCF Installer instance.
        vcf_installer_password (str): The password for authenticating with the VCF Installer instance.
        state (str): The desired state of depot configuration (present or absent).
        depot_type (str): The type of depot (online or offline).

    Methods:
        get_current_depot_config(self): Retrieves current depot configuration from VCF Installer.
        configure_depot(self): Configures depot in VCF Installer.
        remove_depot(self): Removes depot configuration from VCF Installer.
        run(self): Runs the depot management process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.vcf_installer_hostname = module.params["vcf_installer_hostname"]
        self.vcf_installer_user = module.params["vcf_installer_user"]
        self.vcf_installer_password = module.params["vcf_installer_password"]
        self.state = module.params["state"]
        self.depot_type = module.params.get("depot_type")
        self.api_client = VcfInstallerApiClient(
            self.vcf_installer_hostname,
            self.vcf_installer_user,
            self.vcf_installer_password,
        )

    def get_current_depot_config(self):
        """Retrieves current depot configuration from VCF Installer.

        Returns:
            dict: The current depot configuration or None if not configured.
        """
        try:
            api_response = self.api_client.get_depot_settings()
            return api_response
        except VcfApiException as e:
            self.module.fail_json(
                msg=f"Error retrieving current depot configuration: {e}"
            )

    def _determine_current_depot_type(self, depot_config):
        """Determines the current depot type from configuration.

        Args:
            depot_config (dict): The depot configuration.

        Returns:
            str: 'online', 'offline', or None if not configured.
        """
        if not depot_config:
            return None

        # Check if depot configuration exists.
        depot_conf = depot_config.get("depotConfiguration")
        if depot_conf:
            is_offline = depot_conf.get("isOfflineDepot", False)
            return "offline" if is_offline else "online"

        # Check for online account.
        vmware_account = depot_config.get("vmwareAccount")
        if vmware_account and (
            vmware_account.get("status")
            or vmware_account.get("downloadToken")
            or vmware_account.get("downloadActivationCode")
        ):
            return "online"

        # Check for offline account.
        offline_account = depot_config.get("offlineAccount")
        if offline_account and (
            offline_account.get("status") or offline_account.get("username")
        ):
            return "offline"

        return None

    def configure_depot(self):
        """Configures depot in VCF Installer.

        Returns:
            dict: Updated depot configuration
        """
        try:
            # Validate required parameters for online depot.
            if self.depot_type == "online":
                download_token = self.module.params.get("download_token")
                activation_code = self.module.params.get("activation_code")
                if not download_token and not activation_code:
                    self.module.fail_json(
                        msg="One of download_token or activation_code is required for online depot configuration."
                    )
                vmware_account = {}
                if download_token:
                    vmware_account["downloadToken"] = download_token
                if activation_code:
                    vmware_account["downloadActivationCode"] = activation_code
                payload = {"vmwareAccount": vmware_account}
            else:  # Validate required parameters for offline depot.
                payload = {
                    "offlineAccount": {
                        "username": self.module.params["offline_username"],
                        "password": self.module.params["offline_password"],
                    },
                    "depotConfiguration": {
                        "hostname": self.module.params["offline_hostname"],
                        "port": self.module.params["offline_port"],
                        "isOfflineDepot": True,
                        "sslThumbprint": self.module.params["offline_ssl_thumbprint"],
                    },
                }

            # Update the depot configuration.
            self.api_client.update_depot_settings(json.dumps(payload))

            # Get the updated configuration.
            updated_config = self.get_current_depot_config()

            return updated_config

        except VcfApiException as e:
            self.module.fail_json(msg=f"Failed to enable the depot configuration: {e}")

    def remove_depot(self):
        """Removes depot configuration from VCF Installer.

        Returns:
            dict: Empty dict on successful deletion.
        """
        try:
            return self.api_client.delete_depot_settings()
        except VcfApiException as e:
            self.module.fail_json(msg=f"Failed to remove the depot configuration: {e}")

    def run(self):
        """Runs the depot management process."""
        # Get current depot configuration
        current_config = self.get_current_depot_config()
        current_depot_type = self._determine_current_depot_type(current_config)

        # Handle absent state.
        if self.state == "absent":
            if current_depot_type is None:
                self.module.exit_json(
                    changed=False,
                    msg="No depot configuration exists.",
                )

            if self.module.check_mode:
                self.module.exit_json(
                    changed=True,
                    msg=f"Check Mode: Would remove the {current_depot_type} depot configuration.",
                )

            # Disable depot configuration.
            self.remove_depot()
            self.module.exit_json(
                changed=True,
                msg=f"Successfully removed the {current_depot_type} depot configuration.",
            )

        # Handle present state.
        if self.state == "present":
            # Validate depot_type is provided.
            if not self.depot_type:
                self.module.fail_json(
                    msg="depot_type is required when state is present"
                )

            # Check if depot is already configured as requested.
            if current_depot_type == self.depot_type:
                self.module.exit_json(
                    changed=False,
                    msg=f"The system is already configured with an {self.depot_type} depot.",
                    depot=current_config,
                )

            if self.module.check_mode:
                if current_depot_type is None:
                    msg = f"Check Mode: Would configure an {self.depot_type} depot."
                else:
                    msg = f"Check Mode: Would change depot type from {current_depot_type} to {self.depot_type}."
                self.module.exit_json(changed=True, msg=msg)

            # Enable depot configuration.
            updated_config = self.configure_depot()

            if current_depot_type is None:
                msg = f"Successfully enabled an {self.depot_type} depot configuration."
            else:
                msg = f"Successfully updated the depot configuration type from {current_depot_type} to {self.depot_type}."

            self.module.exit_json(
                changed=True,
                msg=msg,
                depot=updated_config,
            )


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = dict(
        vcf_installer_hostname=dict(required=True, type="str"),
        vcf_installer_user=dict(required=True, type="str"),
        vcf_installer_password=dict(required=True, type="str", no_log=True),
        state=dict(
            required=True,
            type="str",
            choices=["present", "absent"],
        ),
        depot_type=dict(
            required=False,
            type="str",
            choices=["online", "offline"],
        ),
        download_token=dict(required=False, type="str", no_log=True),
        activation_code=dict(required=False, type="str", no_log=True),
        offline_hostname=dict(required=False, type="str"),
        offline_port=dict(required=False, type="int"),
        offline_username=dict(required=False, type="str"),
        offline_password=dict(required=False, type="str", no_log=True),
        offline_ssl_thumbprint=dict(required=False, type="str"),
    )

    required_if = [
        # When state is present, the depot type must be provided.
        ["state", "present", ["depot_type"]],
    ]

    module = AnsibleModule(
        argument_spec=parameters,
        supports_check_mode=True,
        required_if=required_if,
    )

    # Validate parameters based on state and depot type.
    if module.params["state"] == "present":
        depot_type = module.params.get("depot_type")

        if depot_type == "online":
            if not module.params.get("download_token") and not module.params.get("activation_code"):
                module.fail_json(
                    msg="One of download_token or activation_code is required when depot_type is online"
                )

        elif depot_type == "offline":
            missing = []
            if not module.params.get("offline_hostname"):
                missing.append("offline_hostname")
            if not module.params.get("offline_port"):
                missing.append("offline_port")
            if not module.params.get("offline_username"):
                missing.append("offline_username")
            if not module.params.get("offline_password"):
                missing.append("offline_password")
            if not module.params.get("offline_ssl_thumbprint"):
                missing.append("offline_ssl_thumbprint")

            if missing:
                module.fail_json(
                    msg=f"The following parameters are required when depot_type is offline: {', '.join(missing)}"
                )

    depot = VcfInstallerDepot(module)
    depot.run()


if __name__ == "__main__":
    main()
