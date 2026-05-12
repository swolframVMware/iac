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
module: sddc_manager_proxy
short_description: Manages proxy configuration in SDDC Manager.
description:
    - This module manages the proxy configuration in SDDC Manager for VMware Cloud Foundation.
    - This module can configure, enable, or disable proxy configuration.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    host:
        description:
            - IP address or FQDN of proxy server.
            - Required when is_enabled is C(true).
        required: false
        type: str
    port:
        description:
            - Port number of the proxy server.
            - Required when is_enabled is C(true).
        required: false
        type: int
    is_enabled:
        description:
            - Defines if the proxy configuration is enabled.
            - To disable the proxy, this should be set to false.
            - Defaults to true.
        required: false
        type: bool
        default: true
    transfer_protocol:
        description:
            - The proxy transfer protocol.
            - Can be either C(http) or C(https).
            - Defaults to C(http).
        required: false
        type: str
        choices:
            - http
            - https
        default: http
    is_authenticated:
        description:
            - If proxy authentication is required.
            - When enabled, username and password must be provided.
        required: false
        type: bool
        default: false
    username:
        description:
            - Username to authenticate with the proxy server.
            - Required when is_authenticated is C(true).
        required: false
        type: str
    password:
        description:
            - Password to authenticate with the proxy server.
            - Required when is_authenticated is C(true).
        required: false
        type: str
        no_log: true
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Enable Proxy Without Authentication
  broadcom.vcf.sddc_manager_proxy:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    host: proxy.example.com
    port: 3128
    transfer_protocol: http
    is_enabled: true
    is_authenticated: false

- name: Enable Proxy With Authentication
  broadcom.vcf.sddc_manager_proxy:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    host: proxy.example.com
    port: 3128
    transfer_protocol: https
    is_enabled: true
    is_authenticated: true
    username: proxy_user
    password: proxy_password

- name: Disable Proxy
  broadcom.vcf.sddc_manager_proxy:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    is_enabled: false
"""

RETURN = r"""
msg:
    description: Status message about the operation or error details
    returned: always
    type: str
    sample: "Successfully updated the proxy configuration."
    alternatives:
        - "Successfully enabled the proxy configuration."
        - "Successfully disabled the proxy configuration."
        - "No proxy configuration changes are required."
changed:
    description: Whether the module made changes
    returned: always
    type: bool
    sample: true
proxy:
    description: Current proxy configuration after the operation
    returned: always
    type: dict
    sample:
        host: "proxy.example.com"
        port: 3128
        isConfigured: true
        isEnabled: true
        isAuthenticated: false
        transferProtocol: "http"
"""

import json

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


class SddcManagerProxy:
    """This class represents proxy management in SDDC Manager.

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
        get_current_proxy_config(self): Retrieves current proxy configuration from SDDC Manager.
        configure_proxy(self): Configures proxy in SDDC Manager.
        run(self): Runs the proxy management process.

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

    def get_current_proxy_config(self):
        """Retrieves current proxy configuration from SDDC Manager.

        Returns:
            dict: The current proxy configuration or None if not configured.
        """
        try:
            api_response = self.api_client.get_proxy_configuration()
            return api_response
        except VcfApiException as e:
            self.module.fail_json(
                msg=f"Error retrieving current proxy configuration: {e}"
            )

    def _proxy_config_changed(self, current_config):
        """Determines if the proxy configuration needs to be updated.

        Args:
            current_config (dict): The current proxy configuration.

        Returns:
            bool: True if configuration differs from desired state.
        """
        if not current_config:
            return True

        # Check enabled state.
        is_enabled = self.module.params.get("is_enabled", True)
        if current_config.get("isEnabled") != is_enabled:
            return True

        # If disabling, no need to check other parameters.
        if not is_enabled:
            return False

        # Check host and port.
        if current_config.get("host") != self.module.params.get("host"):
            return True
        if current_config.get("port") != self.module.params.get("port"):
            return True

        # Check transfer protocol.
        protocol = self.module.params.get("transfer_protocol", "http").upper()
        if current_config.get("transferProtocol", "").upper() != protocol:
            return True

        # Check authentication.
        is_authenticated = self.module.params.get("is_authenticated", False)
        if current_config.get("isAuthenticated") != is_authenticated:
            return True

        # Check username if authenticated.
        if is_authenticated:
            if current_config.get("username") != self.module.params.get("username"):
                return True

        return False

    def configure_proxy(self):
        """Configures proxy in SDDC Manager.

        Returns:
            dict: Updated proxy configuration.
        """
        try:
            is_enabled = self.module.params.get("is_enabled", True)
            is_authenticated = self.module.params.get("is_authenticated", False)

            # Build the payload.
            payload = {
                "isConfigured": True,
                "isEnabled": is_enabled,
            }

            # Add configuration details if enabling.
            if is_enabled:
                payload["host"] = self.module.params["host"]
                payload["port"] = self.module.params["port"]
                payload["transferProtocol"] = self.module.params.get(
                    "transfer_protocol", "http"
                ).upper()
                payload["isAuthenticated"] = is_authenticated

                if is_authenticated:
                    payload["username"] = self.module.params["username"]
                    payload["password"] = self.module.params["password"]

            # Update the proxy configuration.
            self.api_client.update_proxy_configuration(json.dumps(payload))

            # Get the updated configuration.
            updated_config = self.get_current_proxy_config()

            return updated_config

        except VcfApiException as e:
            self.module.fail_json(msg=f"Failed to update the proxy configuration: {e}")

    def run(self):
        """Runs the proxy management process."""
        # Get current proxy configuration.
        current_config = self.get_current_proxy_config()

        # Check if configuration needs to be updated.
        needs_update = self._proxy_config_changed(current_config)

        if not needs_update:
            self.module.exit_json(
                changed=False,
                msg="No proxy configuration changes are required.",
                proxy=current_config,
            )

        if self.module.check_mode:
            is_enabled = self.module.params.get("is_enabled", True)
            if is_enabled:
                msg = "Check Mode: Would enable the proxy configuration."
            else:
                msg = "Check Mode: Would disable the proxy configuration."
            self.module.exit_json(changed=True, msg=msg)

        # Configure proxy.
        updated_config = self.configure_proxy()

        is_enabled = self.module.params.get("is_enabled", True)
        is_configured = current_config and current_config.get("isConfigured", False)

        if is_enabled:
            if is_configured:
                msg = "Successfully updated the proxy configuration."
            else:
                msg = "Successfully enabled the proxy configuration."
        else:
            msg = "Successfully disabled the proxy configuration."

        self.module.exit_json(
            changed=True,
            msg=msg,
            proxy=updated_config,
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
        host=dict(required=False, type="str"),
        port=dict(required=False, type="int"),
        is_enabled=dict(required=False, type="bool", default=True),
        transfer_protocol=dict(
            required=False,
            type="str",
            choices=["http", "https"],
            default="http",
        ),
        is_authenticated=dict(required=False, type="bool", default=False),
        username=dict(required=False, type="str"),
        password=dict(required=False, type="str", no_log=True),
    )

    module = AnsibleModule(
        argument_spec=parameters,
        supports_check_mode=True,
    )

    # Validate parameters based on is_enabled.
    is_enabled = module.params.get("is_enabled", True)

    if is_enabled:
        # Check required parameters when enabling.
        missing = []
        if not module.params.get("host"):
            missing.append("host")
        if not module.params.get("port"):
            missing.append("port")

        if missing:
            module.fail_json(
                msg=f"The following parameters are required when is_enabled is true: {', '.join(missing)}"
            )

        # Check authentication parameters.
        is_authenticated = module.params.get("is_authenticated", False)
        if is_authenticated:
            auth_missing = []
            if not module.params.get("username"):
                auth_missing.append("username")
            if not module.params.get("password"):
                auth_missing.append("password")

            if auth_missing:
                module.fail_json(
                    msg=f"The following parameters are required when is_authenticated is true: {', '.join(auth_missing)}"
                )

    proxy = SddcManagerProxy(module)
    proxy.run()


if __name__ == "__main__":
    main()
