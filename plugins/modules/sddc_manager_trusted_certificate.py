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

__metaclass__ = type

DOCUMENTATION = r"""
---
module: sddc_manager_trusted_certificate
short_description: Manages trusted certificates in the SDDC Manager trust store.
description:
    - This module manages trusted certificates in the SDDC Manager appliance's trust store.
    - When C(state=present) the certificate is added if it does not already exist (idempotent).
    - When C(state=absent) the certificate is removed if it exists (idempotent). The certificate
      is located by comparing normalised PEM content and its alias is resolved automatically.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    certificate:
        description:
            - The certificate in PEM format to add to or remove from the trust store.
            - Whitespace is normalized before comparison so minor formatting differences are tolerated.
        required: true
        type: str
    certificate_usage_type:
        description:
            - The intended usage type for the certificate.
            - Only used when C(state=present).
            - Defaults to C(TRUSTED_FOR_OUTBOUND).
        required: false
        type: str
        default: TRUSTED_FOR_OUTBOUND
        choices:
            - TRUSTED_FOR_OUTBOUND
    state:
        description:
            - The desired state of the trusted certificate.
            - C(present) ensures the certificate is in the trust store.
            - C(absent) ensures the certificate is removed from the trust store.
        required: false
        type: str
        default: present
        choices:
            - present
            - absent
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Add Trusted Certificate
  broadcom.vcf.sddc_manager_trusted_certificate:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    certificate: "{{ trusted_ssl_certificate_payload.certificate }}"
    certificate_usage_type: TRUSTED_FOR_OUTBOUND
    state: present
  register: result

- name: Display Result
  ansible.builtin.debug:
    msg: "{{ result.msg }}"

- name: Remove Trusted Certificate
  broadcom.vcf.sddc_manager_trusted_certificate:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    certificate: "{{ trusted_ssl_certificate_payload.certificate }}"
    state: absent
  register: result

- name: Display Result
  ansible.builtin.debug:
    msg: "{{ result.msg }}"
"""

RETURN = r"""
trusted_certificate:
    description: The updated list of trusted certificates in the SDDC Manager appliance's trust store.
    returned: always
    type: list
    elements: dict
    sample:
        - alias: "vcf_59:24:D5:18:04:A0:26:B0:A4:05:EA:82:60:95:82:A2:4B:F6:31:FB:81:93:01:F3:29:7D:34:9C:D3:05:39:90"
          certificate: "-----BEGIN CERTIFICATE-----\nMIIFq...\n-----END CERTIFICATE-----"
changed:
    description: Whether the module made changes.
    returned: always
    type: bool
    sample: true
msg:
    description: A status message describing the result of the operation.
    returned: always
    type: str
    sample: "Successfully added trusted certificate to the trust store."
    alternatives:
        - "Trusted certificate already exists in the trust store. No changes made."
        - "Successfully removed trusted certificate from the trust store."
        - "Trusted certificate not found in the trust store. No changes made."
"""

import json

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


class SddcManagerTrustedCertificates:
    """This class represents trusted certificate management in SDDC Manager.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager instance.
        sddc_manager_user (str): The username for authenticating with the SDDC Manager instance.
        sddc_manager_password (str): The password for authenticating with the SDDC Manager instance.
        certificate (str): The certificate in PEM format.
        certificate_usage_type (str): The certificate usage type for the add operation.
        state (str): The desired state of the certificate (present or absent).

    Methods:
        get_existing_certificates(self): Retrieves all existing trusted certificates.
        _extract_pem(cert_string): Extracts the PEM block from a certificate string.
        find_match(self, existing_certificates): Finds a matching certificate by PEM content.
        add_certificate(self): Adds the certificate to the trust store.
        remove_certificate(self, alias): Removes the certificate from the trust store by alias.
        run(self): Runs the trusted certificate management process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params["sddc_manager_hostname"]
        self.sddc_manager_user = module.params["sddc_manager_user"]
        self.sddc_manager_password = module.params["sddc_manager_password"]
        self.certificate = module.params["certificate"].strip()
        self.certificate_usage_type = module.params["certificate_usage_type"]
        self.state = module.params["state"]
        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )

    def get_existing_certificates(self):
        """Retrieves all existing trusted certificates from SDDC Manager.

        Returns:
            list: The list of existing trusted certificate objects.
        """
        try:
            api_response = self.api_client.get_trusted_certificates()
            return api_response.get("elements", []) if api_response else []
        except VcfApiException as e:
            self.module.fail_json(
                msg=f"Error retrieving existing trusted certificates: {e}"
            )

    @staticmethod
    def _extract_pem(cert_string):
        """Extracts and normalizes the PEM block from a certificate string.

        The util.trusted_ssl_certificate role prepends subject/issuer header lines
        before the PEM block. This method strips everything outside the
        BEGIN/END CERTIFICATE markers before normalizing whitespace, so comparisons
        are not affected by those headers.

        Args:
            cert_string (str): A certificate string, optionally containing subject/
                issuer header lines before the PEM block.

        Returns:
            str: The normalized PEM block with all whitespace removed, or the full
                normalized input if no PEM markers are found.
        """
        start = cert_string.find("-----BEGIN CERTIFICATE-----")
        end = cert_string.find("-----END CERTIFICATE-----")
        if start != -1 and end != -1:
            pem = cert_string[start : end + len("-----END CERTIFICATE-----")]
        else:
            pem = cert_string
        return "".join(pem.split())

    def find_match(self, existing_certificates):
        """Finds a certificate in the trust store by normalized PEM content.

        Args:
            existing_certificates (list): The list of existing trusted certificate
                objects returned by the API.

        Returns:
            dict or None: The matching certificate entry (including alias), or None.
        """
        normalized = self._extract_pem(self.certificate)
        return next(
            (
                c
                for c in existing_certificates
                if self._extract_pem(c.get("certificate", "")) == normalized
            ),
            None,
        )

    def add_certificate(self):
        """Adds the certificate to the SDDC Manager trust store.

        Returns:
            list: The updated list of trusted certificate objects.
        """
        try:
            payload = {
                "certificate": self.certificate,
                "certificateUsageType": self.certificate_usage_type,
            }
            api_response = self.api_client.add_trusted_certificate(json.dumps(payload))
            return api_response.get("elements", []) if api_response else []
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error adding trusted certificate: {e}")

    def remove_certificate(self, alias):
        """Removes the certificate from the SDDC Manager trust store by alias.

        Args:
            alias (str): The alias of the certificate to remove.

        Returns:
            list: The remaining list of trusted certificate objects after removal.
        """
        try:
            self.api_client.delete_trusted_certificate(alias)
            api_response = self.api_client.get_trusted_certificates()
            return api_response.get("elements", []) if api_response else []
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error removing trusted certificate: {e}")

    def run(self):
        """Runs the trusted certificate management process."""
        existing_certificates = self.get_existing_certificates()
        match = self.find_match(existing_certificates)

        if self.state == "absent":
            if not match:
                self.module.exit_json(
                    changed=False,
                    msg="Trusted certificate not found in the trust store. No changes made.",
                    trusted_certificate=existing_certificates,
                )

            if self.module.check_mode:
                self.module.exit_json(
                    changed=True,
                    msg="Check Mode: Would remove the trusted certificate from the trust store.",
                    trusted_certificate=existing_certificates,
                )

            updated_certificates = self.remove_certificate(match["alias"])
            self.module.exit_json(
                changed=True,
                msg="Successfully removed trusted certificate from the trust store.",
                trusted_certificate=updated_certificates,
            )

        # state == "present"
        if match:
            self.module.exit_json(
                changed=False,
                msg="Trusted certificate already exists in the trust store. No changes made.",
                trusted_certificate=existing_certificates,
            )

        if self.module.check_mode:
            self.module.exit_json(
                changed=True,
                msg="Check Mode: Would add the trusted certificate to the trust store.",
                trusted_certificate=existing_certificates,
            )

        updated_certificates = self.add_certificate()
        self.module.exit_json(
            changed=True,
            msg="Successfully added trusted certificate to the trust store.",
            trusted_certificate=updated_certificates,
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
        certificate=dict(required=True, type="str"),
        certificate_usage_type=dict(
            required=False,
            type="str",
            default="TRUSTED_FOR_OUTBOUND",
            choices=["TRUSTED_FOR_OUTBOUND"],
        ),
        state=dict(
            required=False,
            type="str",
            default="present",
            choices=["present", "absent"],
        ),
    )

    module = AnsibleModule(argument_spec=parameters, supports_check_mode=True)

    trusted_certs = SddcManagerTrustedCertificates(module)
    trusted_certs.run()


if __name__ == "__main__":
    main()
