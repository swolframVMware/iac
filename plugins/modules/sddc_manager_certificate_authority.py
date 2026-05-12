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
module: sddc_manager_certificate_authority
short_description: Manages certificate authority configuration in SDDC Manager.
description:
    - This module manages the certificate authority configuration in SDDC Manager for VMware Cloud Foundation.
    - This module can configure OpenSSL or Microsoft CA as the certificate authority.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    state:
        description:
            - The desired state of the certificate authority configuration.
            - C(update) will configure the certificate authority (OpenSSL or Microsoft CA).
        required: true
        type: str
        choices:
            - update
    ca_type:
        description:
            - The type of certificate authority to configure.
            - C(OpenSSL) configures an OpenSSL certificate authority.
            - C(Microsoft) configures a Microsoft Certificate Authority.
            - Required when state is C(update).
            - Case-insensitive (e.g., 'openssl', 'OpenSSL', 'OPENSSL' are all accepted).
        required: false
        type: str
    openssl_common_name:
        description:
            - Common name for the OpenSSL certificate authority.
            - Required when ca_type is C(OpenSSL) and state is C(update).
        required: false
        type: str
    openssl_organization:
        description:
            - Organization for the OpenSSL certificate authority.
            - Required when ca_type is C(OpenSSL) and state is C(update).
        required: false
        type: str
    openssl_organization_unit:
        description:
            - Organization unit for the OpenSSL certificate authority.
            - Required when ca_type is C(OpenSSL) and state is C(update).
        required: false
        type: str
    openssl_locality:
        description:
            - Locality for the OpenSSL certificate authority.
            - Required when ca_type is C(OpenSSL) and state is C(update).
        required: false
        type: str
    openssl_state:
        description:
            - State/Province for the OpenSSL certificate authority.
            - Required when ca_type is C(OpenSSL) and state is C(update).
        required: false
        type: str
    openssl_country:
        description:
            - Country code for the OpenSSL certificate authority.
            - Required when ca_type is C(OpenSSL) and state is C(update).
        required: false
        type: str
    microsoft_server:
        description:
            - FQDN of the Microsoft Certificate Authority.
            - Will be automatically transformed to the full URL format (https://<server>/certsrv) for the API.
            - Required when ca_type is C(Microsoft) and state is C(update).
        required: false
        type: str
    microsoft_username:
        description:
            - Username to authenticate with the Microsoft Certificate Authority.
            - Required when ca_type is C(Microsoft) and state is C(update).
        required: false
        type: str
    microsoft_password:
        description:
            - Password to authenticate with the Microsoft Certificate Authority.
            - Required when ca_type is C(Microsoft) and state is C(update).
        required: false
        type: str
        no_log: true
    microsoft_template_name:
        description:
            - Template name for the Microsoft Certificate Authority.
            - Required when ca_type is C(Microsoft) and state is C(update).
        required: false
        type: str
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Configure OpenSSL Certificate Authority
  broadcom.vcf.sddc_manager_certificate_authority:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: update
    ca_type: OpenSSL
    openssl_common_name: "ca.example.com"
    openssl_organization: "Example"
    openssl_organization_unit: "Platform Engineering"
    openssl_locality: "San Francisco"
    openssl_state: "California"
    openssl_country: "US"

- name: Configure Microsoft Certificate Authority
  broadcom.vcf.sddc_manager_certificate_authority:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: update
    ca_type: Microsoft
    microsoft_server: "ca.example.com"
    microsoft_username: "DOMAIN\\ca_admin"
    microsoft_password: "ca_password"
    microsoft_template_name: "VMware"

- name: Configure Certificate Authority with Result
  broadcom.vcf.sddc_manager_certificate_authority:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: update
    ca_type: OpenSSL
    openssl_common_name: "ca.example.com"
    openssl_organization: "Example"
    openssl_organization_unit: "Platform Engineering"
    openssl_locality: "San Francisco"
    openssl_state: "California"
    openssl_country: "US"
  register: ca_result

- name: Display Certificate Authority Result
  ansible.builtin.debug:
    var: ca_result.msg
"""

RETURN = r"""
msg:
    description: Status message about the operation or error details
    returned: always
    type: str
    sample: "Successfully configured OpenSSL certificate authority."
    alternatives:
        - "Successfully configured Microsoft certificate authority."
        - "Successfully updated OpenSSL certificate authority configuration."
        - "Successfully updated Microsoft certificate authority configuration."
        - "OpenSSL certificate authority already configured as requested."
        - "Microsoft certificate authority already configured as requested."
        - "Check Mode: Would configure Microsoft certificate authority."
        - "Check Mode: Would update OpenSSL certificate authority configuration."
changed:
    description: Whether the module made changes
    returned: always
    type: bool
    sample: true
certificate_authority:
    description: Current certificate authority configuration after the operation
    returned: when state is update
    type: dict
    sample:
        id: "OpenSSL"
        commonName: "ca.example.com"
        organization: "Example"
        organizationUnit: "Platform Engineering"
        locality: "San Francisco"
        state: "California"
        country: "US"
"""

import json

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


class SddcManagerCertificateAuthority:
    """This class represents a certificate authority configuration in SDDC Manager.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager instance.
        sddc_manager_user (str): The username for authenticating with the SDDC Manager instance.
        sddc_manager_password (str): The password for authenticating with the SDDC Manager instance.
        state (str): The desired state of certificate authority configuration (update).
        ca_type (str): The type of certificate authority (openssl or microsoft).

    Methods:
        get_current_ca_config(self): Retrieves current certificate authority configuration.
        configure_ca(self): Configures certificate authority in SDDC Manager.
        run(self): Runs the certificate authority management process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params["sddc_manager_hostname"]
        self.sddc_manager_user = module.params["sddc_manager_user"]
        self.sddc_manager_password = module.params["sddc_manager_password"]
        self.state = module.params["state"]
        raw_ca_type = module.params.get("ca_type")

        if raw_ca_type:
            self.ca_type = raw_ca_type.lower()
            if self.ca_type not in ["openssl", "microsoft"]:
                self.module.fail_json(
                    msg=f"Invalid ca_type '{raw_ca_type}'. Must be one of 'openssl' or 'microsoft'."
                )
        else:
            self.ca_type = None

        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )

    @staticmethod
    def _format_ca_type_for_display(ca_type):
        """Formats CA type for display with proper capitalization.

        Args:
            ca_type (str): The CA type in lowercase (openssl or microsoft).

        Returns:
            str: The properly formatted CA type (OpenSSL or Microsoft).
        """
        if not ca_type:
            return ca_type

        ca_type_lower = ca_type.lower()
        if ca_type_lower == "openssl":
            return "OpenSSL"
        elif ca_type_lower == "microsoft":
            return "Microsoft"
        else:
            return ca_type.capitalize()

    @staticmethod
    def _build_microsoft_server_url(server):
        """Builds the full Microsoft CA server URL from FQDN.

        Args:
            server (str): The server FQDN.

        Returns:
            str: The full server URL in format https://<server>/certsrv
        """
        if not server:
            return None

        # Build the standard Microsoft CA URL.
        return f"https://{server}/certsrv"

    def get_current_ca_config(self):
        """Retrieves current certificate authority configuration.

        Returns:
            dict: The current certificate authority configuration or None if not configured.
        """
        try:
            api_response = self.api_client.get_certificate_authority()

            if api_response:
                if isinstance(api_response, dict):
                    if "elements" in api_response:
                        elements = api_response.get("elements", [])
                        if elements:
                            if self.ca_type:
                                for ca in elements:
                                    ca_id = ca.get("id") or ca.get("caType")
                                    if ca_id and ca_id.lower() == self.ca_type:
                                        return ca
                            return elements[0] if elements else None
                    else:
                        return api_response
                elif isinstance(api_response, list):
                    if len(api_response) > 0:
                        if self.ca_type:
                            for ca in api_response:
                                ca_id = ca.get("id") or ca.get("caType")
                                if ca_id and ca_id.lower() == self.ca_type:
                                    return ca
                        return api_response[0]

            return None
        except VcfApiException as e:
            self.module.fail_json(
                msg=f"Error retrieving current certificate authority configuration: {e}"
            )

    def _determine_current_ca_type(self, ca_config):
        """Determines the current certificate authority type from configuration.

        Args:
            ca_config (dict): The certificate authority configuration.

        Returns:
            str: 'OpenSSL', 'Microsoft', or None if not configured.
        """
        if not ca_config:
            return None

        ca_type = ca_config.get("id") or ca_config.get("caType")
        return ca_type if ca_type else None

    def _build_payload(self):
        """Builds the payload for configuring certificate authority.

        Returns:
            dict: The payload for certificate authority configuration.
        """
        if self.ca_type == "openssl":
            # Validate all required OpenSSL parameters are provided.
            required_params = [
                "openssl_common_name",
                "openssl_organization",
                "openssl_organization_unit",
                "openssl_locality",
                "openssl_state",
                "openssl_country",
            ]
            missing = [p for p in required_params if not self.module.params.get(p)]
            if missing:
                self.module.fail_json(
                    msg=f"Missing required OpenSSL parameters: {', '.join(missing)}"
                )

            payload = {
                "caType": "OpenSSL",
                "openSSLCertificateAuthoritySpec": {
                    "commonName": self.module.params["openssl_common_name"],
                    "organization": self.module.params["openssl_organization"],
                    "organizationUnit": self.module.params["openssl_organization_unit"],
                    "locality": self.module.params["openssl_locality"],
                    "state": self.module.params["openssl_state"],
                    "country": self.module.params["openssl_country"],
                },
            }
        else:
            # Validate all required Microsoft parameters are provided.
            required_params = [
                "microsoft_server",
                "microsoft_username",
                "microsoft_password",
                "microsoft_template_name",
            ]
            missing = [p for p in required_params if not self.module.params.get(p)]
            if missing:
                self.module.fail_json(
                    msg=f"Missing required Microsoft parameters: {', '.join(missing)}"
                )

            server_url = self._build_microsoft_server_url(
                self.module.params["microsoft_server"]
            )
            payload = {
                "caType": "Microsoft",
                "microsoftCertificateAuthoritySpec": {
                    "serverUrl": server_url,
                    "username": self.module.params["microsoft_username"],
                    "secret": self.module.params["microsoft_password"],
                    "templateName": self.module.params["microsoft_template_name"],
                },
            }

        return payload

    def _is_config_same(self, current_config):
        """Checks if current configuration matches desired configuration.

        Args:
            current_config (dict): The current certificate authority configuration.

        Returns:
            bool: True if configurations match, False otherwise.
        """
        if not current_config:
            return False

        current_type = current_config.get("caType")

        if not current_type or current_type.lower() != self.ca_type:
            return False

        if self.ca_type == "openssl":
            fields = [
                "commonName",
                "organization",
                "organizationUnit",
                "locality",
                "state",
                "country",
            ]
            param_map = {
                "commonName": "openssl_common_name",
                "organization": "openssl_organization",
                "organizationUnit": "openssl_organization_unit",
                "locality": "openssl_locality",
                "state": "openssl_state",
                "country": "openssl_country",
            }
            for field in fields:
                current_val = current_config.get(field)
                desired_val = self.module.params.get(param_map[field])
                if current_val != desired_val:
                    return False
        else:
            desired_server_url = self._build_microsoft_server_url(
                self.module.params.get("microsoft_server")
            )
            if current_config.get("serverUrl") != desired_server_url:
                return False
            if current_config.get("username") != self.module.params.get(
                "microsoft_username"
            ):
                return False
            if current_config.get("templateName") != self.module.params.get(
                "microsoft_template_name"
            ):
                return False

        return True

    def configure_ca(self):
        """Configures certificate authority.

        Returns:
            dict: The certificate authority configuration response.
        """
        try:
            payload = self._build_payload()

            current_config = self.get_current_ca_config()
            current_ca_type = self._determine_current_ca_type(current_config)

            if current_config is None or (
                current_ca_type and current_ca_type.lower() != self.ca_type
            ):
                api_response = self.api_client.set_certificate_authority(
                    json.dumps(payload)
                )
            else:
                api_response = self.api_client.update_certificate_authority(
                    json.dumps(payload)
                )

            return api_response

        except VcfApiException as e:
            self.module.fail_json(
                msg=f"Failed to configure the certificate authority: {e}"
            )

    def run(self):
        """Runs the certificate authority management process."""
        current_config = self.get_current_ca_config()
        current_ca_type = self._determine_current_ca_type(current_config)

        if self.state == "update":
            if not self.ca_type:
                self.module.fail_json(msg="ca_type is required when state is update")

            if self._is_config_same(current_config):
                display_type = self._format_ca_type_for_display(self.ca_type)
                self.module.exit_json(
                    changed=False,
                    msg=f"{display_type} certificate authority already configured as requested.",
                    certificate_authority=current_config,
                )

            if self.module.check_mode:
                display_type = self._format_ca_type_for_display(self.ca_type)
                if current_ca_type is None:
                    msg = f"Check Mode: Would configure {display_type} certificate authority."
                else:
                    msg = f"Check Mode: Would update {display_type} certificate authority configuration."
                self.module.exit_json(changed=True, msg=msg)

            updated_config = self.configure_ca()

            display_type = self._format_ca_type_for_display(self.ca_type)
            if current_ca_type is None:
                msg = f"Successfully configured {display_type} certificate authority."
            else:
                msg = f"Successfully updated {display_type} certificate authority configuration."

            self.module.exit_json(
                changed=True,
                msg=msg,
                certificate_authority=updated_config,
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
        state=dict(
            required=True,
            type="str",
            choices=["update"],
        ),
        ca_type=dict(
            required=False,
            type="str",
        ),
        openssl_common_name=dict(required=False, type="str"),
        openssl_organization=dict(required=False, type="str"),
        openssl_organization_unit=dict(required=False, type="str"),
        openssl_locality=dict(required=False, type="str"),
        openssl_state=dict(required=False, type="str"),
        openssl_country=dict(required=False, type="str"),
        microsoft_server=dict(required=False, type="str"),
        microsoft_username=dict(required=False, type="str"),
        microsoft_password=dict(required=False, type="str", no_log=True),
        microsoft_template_name=dict(required=False, type="str"),
    )

    required_if = [
        ["state", "update", ["ca_type"]],
    ]

    module = AnsibleModule(
        argument_spec=parameters,
        supports_check_mode=True,
        required_if=required_if,
    )

    if module.params["state"] == "update":
        ca_type = module.params.get("ca_type")

        if not ca_type:
            module.fail_json(msg="ca_type is required when state is update")

        ca_type_lower = ca_type.lower()

        if ca_type_lower not in ["openssl", "microsoft"]:
            module.fail_json(
                msg=f"Invalid ca_type '{ca_type}'. Must be 'openssl' or 'microsoft'."
            )

        if ca_type_lower == "openssl":
            missing = []
            if not module.params.get("openssl_common_name"):
                missing.append("openssl_common_name")
            if not module.params.get("openssl_organization"):
                missing.append("openssl_organization")
            if not module.params.get("openssl_organization_unit"):
                missing.append("openssl_organization_unit")
            if not module.params.get("openssl_locality"):
                missing.append("openssl_locality")
            if not module.params.get("openssl_state"):
                missing.append("openssl_state")
            if not module.params.get("openssl_country"):
                missing.append("openssl_country")

            if missing:
                module.fail_json(
                    msg=f"The following parameters are required when the certificate authority type is OpenSSL: {', '.join(missing)}"
                )

        elif ca_type_lower == "microsoft":
            missing = []
            if not module.params.get("microsoft_server"):
                missing.append("microsoft_server")
            if not module.params.get("microsoft_username"):
                missing.append("microsoft_username")
            if not module.params.get("microsoft_password"):
                missing.append("microsoft_password")
            if not module.params.get("microsoft_template_name"):
                missing.append("microsoft_template_name")

            if missing:
                module.fail_json(
                    msg=f"The following parameters are required when the certificate authority type is Microsoft: {', '.join(missing)}"
                )

    ca = SddcManagerCertificateAuthority(module)
    ca.run()


if __name__ == "__main__":
    main()
