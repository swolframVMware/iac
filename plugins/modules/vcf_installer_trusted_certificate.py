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
module: vcf_installer_trusted_certificate
short_description: Adds a trusted certificate to the VCF Installer trust store.
description:
    - This module adds a trusted certificate to the VCF Installer appliance's trust store.
    - The operation is idempotent; if a matching certificate already exists no change is made.
    - Removal of trusted certificates is not supported by the VCF Installer API when the appliance is in installer mode.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.vcf_installer
options:
    certificate:
        description:
            - The certificate in PEM format to add to the trust store.
            - Whitespace is normalized before comparison so minor formatting differences are tolerated.
        required: true
        type: str
    certificate_usage_type:
        description:
            - The intended usage type for the certificate.
            - Defaults to C(TRUSTED_FOR_OUTBOUND).
        required: false
        type: str
        default: TRUSTED_FOR_OUTBOUND
        choices:
            - TRUSTED_FOR_OUTBOUND
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Add Trusted Certificate
  broadcom.vcf.vcf_installer_trusted_certificate:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    certificate: "{{ trusted_ssl_certificate_payload.certificate }}"
    certificate_usage_type: TRUSTED_FOR_OUTBOUND
  register: result

- name: Display Result
  ansible.builtin.debug:
    msg: "{{ result.msg }}"
"""

RETURN = r"""
trusted_certificate:
    description: The updated list of trusted certificates in the appliance's trust store.
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
"""

import json

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.vcf_installer import (
    VcfInstallerApiClient,
)


class VcfInstallerTrustedCertificates:
    """This class represents trusted certificate management in VCF Installer.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        vcf_installer_hostname (str): The hostname or IP address of the VCF Installer instance.
        vcf_installer_user (str): The username for authenticating with the VCF Installer instance.
        vcf_installer_password (str): The password for authenticating with the VCF Installer instance.
        certificate (str): The certificate in PEM format.
        certificate_usage_type (str): The certificate usage type for the add operation.

    Methods:
        get_existing_certificates(self): Retrieves all existing trusted certificates.
        _extract_pem(cert_string): Extracts the PEM block from a certificate string.
        find_match(self, existing_certificates): Finds a matching certificate by PEM content.
        add_certificate(self): Adds the certificate to the trust store.
        run(self): Runs the trusted certificate management process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.vcf_installer_hostname = module.params["vcf_installer_hostname"]
        self.vcf_installer_user = module.params["vcf_installer_user"]
        self.vcf_installer_password = module.params["vcf_installer_password"]
        self.certificate = module.params["certificate"].strip()
        self.certificate_usage_type = module.params["certificate_usage_type"]
        self.api_client = VcfInstallerApiClient(
            self.vcf_installer_hostname,
            self.vcf_installer_user,
            self.vcf_installer_password,
        )

    def get_existing_certificates(self):
        """Retrieves all existing trusted certificates from VCF Installer.

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
        """Adds the certificate to the VCF Installer trust store.

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

    def run(self):
        """Runs the trusted certificate management process."""
        existing_certificates = self.get_existing_certificates()
        match = self.find_match(existing_certificates)

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
        vcf_installer_hostname=dict(required=True, type="str"),
        vcf_installer_user=dict(required=True, type="str"),
        vcf_installer_password=dict(required=True, type="str", no_log=True),
        certificate=dict(required=True, type="str"),
        certificate_usage_type=dict(
            required=False,
            type="str",
            default="TRUSTED_FOR_OUTBOUND",
            choices=["TRUSTED_FOR_OUTBOUND"],
        ),
    )

    module = AnsibleModule(argument_spec=parameters, supports_check_mode=True)

    trusted_certs = VcfInstallerTrustedCertificates(module)
    trusted_certs.run()


if __name__ == "__main__":
    main()
