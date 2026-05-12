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
module: vcf_installer_proxy_info
short_description: Retrieves the proxy configuration from VCF Installer.
description:
    - This module retrieves the proxy configuration from VCF Installer for VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.vcf_installer
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Get Proxy Configuration
  broadcom.vcf.vcf_installer_proxy_info:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
  register: proxy_config

- name: Display Status Message
  ansible.builtin.debug:
    msg: "{{ proxy_config.msg }}"

- name: Display Configuration Details
  ansible.builtin.debug:
    var: proxy_config.proxy
"""

RETURN = r"""
proxy:
    description: The proxy configuration details.
    returned: always
    type: dict
    sample:
        host: "proxy.example.com"
        port: 3128
        isConfigured: true
        isEnabled: true
        isAuthenticated: false
        transferProtocol: "http"
changed:
    description: Whether the module made changes.
    returned: always
    type: bool
    sample: false
msg:
    description: A status message describing the proxy configuration state.
    returned: always
    type: str
    sample: "HTTP Proxy Status: Enabled (proxy.example.com:3128)"
    alternatives:
        - "HTTP Proxy Status: Disabled (proxy.example.com:3128)"
        - "HTTPS Proxy Status: Enabled (proxy.example.com:3128 with authentication)"
        - "HTTPS Proxy Status: Disabled (proxy.example.com:3128 with authentication)"
        - "Proxy Status: Not Configured"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.vcf_installer import (
    VcfInstallerApiClient,
)


class VcfInstallerProxyInfo:
    """This class represents the proxy configuration information retrieval in VCF Installer.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        vcf_installer_hostname (str): The hostname or IP address of the VCF Installer instance.
        vcf_installer_user (str): The username for authenticating with the VCF Installer instance.
        vcf_installer_password (str): The password for authenticating with the VCF Installer instance.

    Methods:
        get_proxy_settings(self): Retrieves the proxy configuration from VCF Installer.
        run(self): Runs the proxy configuration retrieval process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.vcf_installer_hostname = module.params["vcf_installer_hostname"]
        self.vcf_installer_user = module.params["vcf_installer_user"]
        self.vcf_installer_password = module.params["vcf_installer_password"]
        self.api_client = VcfInstallerApiClient(
            self.vcf_installer_hostname,
            self.vcf_installer_user,
            self.vcf_installer_password,
        )

    def get_proxy_settings(self):
        """Retrieves proxy configuration from VCF Installer."""
        try:
            api_response = self.api_client.get_proxy_configuration()

            # Determine the appropriate message based on the proxy configuration.
            msg = self._build_proxy_message(api_response)

            self.module.exit_json(
                changed=False, proxy=api_response if api_response else {}, msg=msg
            )

        except VcfApiException as e:
            self.module.fail_json(msg=f"Error retrieving proxy configuration: {e}")

    def _build_proxy_message(self, proxy_config) -> str:
        """Builds a descriptive message based on proxy configuration.

        Args:
            proxy_config: The proxy configuration details.

        Returns:
            str: A status message describing the proxy configuration state.
        """
        # Check if proxy is not configured.
        if not proxy_config or not proxy_config.get("isConfigured"):
            return "Proxy Status: Not Configured"

        # Extract configuration details.
        host = proxy_config.get("host", "Unknown")
        port = proxy_config.get("port")
        protocol = proxy_config.get("transferProtocol", "HTTP").upper()
        is_authenticated = proxy_config.get("isAuthenticated", False)
        is_enabled = proxy_config.get("isEnabled", False)

        location = f"{host}:{port}" if port else host
        auth_info = " with authentication" if is_authenticated else ""

        # Build status message with protocol in prefix.
        state = "Enabled" if is_enabled else "Disabled"
        return f"{protocol} Proxy Status: {state} ({location}{auth_info})"

    def run(self):
        """Runs the proxy configuration retrieval process."""
        self.get_proxy_settings()


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = dict(
        vcf_installer_hostname=dict(required=True, type="str"),
        vcf_installer_user=dict(required=True, type="str"),
        vcf_installer_password=dict(required=True, type="str", no_log=True),
    )

    module = AnsibleModule(argument_spec=parameters, supports_check_mode=True)

    proxy_info = VcfInstallerProxyInfo(module)
    proxy_info.run()


if __name__ == "__main__":
    main()
