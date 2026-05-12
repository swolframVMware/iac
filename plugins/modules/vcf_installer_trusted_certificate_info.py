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
module: vcf_installer_trusted_certificate_info
short_description: Retrieves trusted certificates from VCF Installer.
description:
    - This module retrieves all trusted certificates from the VCF Installer appliance's trust store.
    - When C(certificate) is provided, the module searches the trust store for a matching
      entry by normalising PEM whitespace and returns it as C(trusted_certificate) (singular).
    - The module fails if C(certificate) is provided but no match is found.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.vcf_installer
options:
    certificate:
        description:
            - A PEM-formatted certificate string to search for in the trust store.
            - Whitespace is normalised before comparison so minor formatting differences
              are tolerated.
            - When provided, the matching entry is returned as C(trusted_certificate).
            - The module fails if no match is found.
        required: false
        type: str
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Get All Trusted Certificates
  broadcom.vcf.vcf_installer_trusted_certificate_info:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
  register: trusted_certs

- name: Display Status Message
  ansible.builtin.debug:
    msg: "{{ trusted_certs.msg }}"

- name: Display All Trusted Certificates
  ansible.builtin.debug:
    var: trusted_certs.trusted_certificate

- name: Look Up a Specific Certificate by PEM Content
  broadcom.vcf.vcf_installer_trusted_certificate_info:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    certificate: "{{ trusted_ssl_certificate_payload.certificate }}"
  register: single_cert

- name: Display the Matched Certificate
  ansible.builtin.debug:
    var: single_cert.trusted_certificate
"""

RETURN = r"""
found:
    description: Whether a matching certificate was found.
    returned: always
    type: bool
    sample: true
trusted_certificates:
    description: The full list of trusted certificates retrieved from the appliance's trust store.
    returned: always
    type: list
    elements: dict
    sample:
        - alias: "vcf_59:24:D5:18:04:A0:26:B0:A4:05:EA:82:60:95:82:A2:4B:F6:31:FB:81:93:01:F3:29:7D:34:9C:D3:05:39:90"
          certificate: "-----BEGIN CERTIFICATE-----\nMIIFq...\n-----END CERTIFICATE-----"
trusted_certificate:
    description: The single trusted certificate whose PEM content matches the provided certificate.
    returned: when certificate is provided and a match is found
    type: dict
    sample:
        alias: "vcf_59:24:D5:18:04:A0:26:B0:A4:05:EA:82:60:95:82:A2:4B:F6:31:FB:81:93:01:F3:29:7D:34:9C:D3:05:39:90"
        certificate: "-----BEGIN CERTIFICATE-----\nMIIFq...\n-----END CERTIFICATE-----"
changed:
    description: Whether the module made changes.
    returned: always
    type: bool
    sample: false
msg:
    description: A status message describing the trusted certificates retrieval result.
    returned: always
    type: str
    sample: "Retrieved 3 trusted certificate(s)."
    alternatives:
        - "No trusted certificates found."
        - "Found matching trusted certificate with alias: vcf_59:24:..."
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.vcf_installer import (
    VcfInstallerApiClient,
)


class VcfInstallerTrustedCertificatesInfo:
    """This class represents the trusted certificates information retrieval in VCF Installer.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        vcf_installer_hostname (str): The hostname or IP address of the VCF Installer instance.
        vcf_installer_user (str): The username for authenticating with the VCF Installer instance.
        vcf_installer_password (str): The password for authenticating with the VCF Installer instance.
        certificate (str): Optional PEM certificate to search for in the trust store.

    Methods:
        get_trusted_certificates(self): Retrieves trusted certificates from VCF Installer.
        run(self): Runs the trusted certificates retrieval process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.vcf_installer_hostname = module.params["vcf_installer_hostname"]
        self.vcf_installer_user = module.params["vcf_installer_user"]
        self.vcf_installer_password = module.params["vcf_installer_password"]
        self.certificate = module.params.get("certificate")
        self.api_client = VcfInstallerApiClient(
            self.vcf_installer_hostname,
            self.vcf_installer_user,
            self.vcf_installer_password,
        )

    @staticmethod
    def _extract_pem(cert_string):
        """Extracts and normalizes the PEM block from a certificate string.

        The API and the util.trusted_ssl_certificate role may prepend subject/issuer
        header lines before the PEM block. This method strips everything outside
        the BEGIN/END CERTIFICATE markers before normalizing whitespace, so comparisons
        are not affected by those headers.

        Args:
            cert_string (str): A certificate string, optionally containing subject/
                issuer header lines before the PEM block.

        Returns:
            str: The normalised PEM block with all whitespace removed, or the full
                normalized input if no PEM markers are found.
        """
        start = cert_string.find("-----BEGIN CERTIFICATE-----")
        end = cert_string.find("-----END CERTIFICATE-----")
        if start != -1 and end != -1:
            pem = cert_string[start : end + len("-----END CERTIFICATE-----")]
        else:
            pem = cert_string
        return "".join(pem.split())

    def get_trusted_certificates(self):
        """Retrieves trusted certificates from VCF Installer."""
        try:
            api_response = self.api_client.get_trusted_certificates()
            elements = api_response.get("elements", []) if api_response else []

            # If a certificate PEM was provided, search for a matching entry.
            if self.certificate:
                normalised = self._extract_pem(self.certificate)
                match = next(
                    (
                        c
                        for c in elements
                        if self._extract_pem(c.get("certificate", "")) == normalised
                    ),
                    None,
                )
                if not match:
                    self.module.exit_json(
                        changed=False,
                        found=False,
                        trusted_certificates=elements,
                        trusted_certificate={},
                        msg="No matching trusted certificate found in the trust store.",
                    )
                self.module.exit_json(
                    changed=False,
                    found=True,
                    trusted_certificates=elements,
                    trusted_certificate=match,
                    msg=f"Found matching trusted certificate with alias: {match.get('alias')}",
                )

            # No certificate filter — return the full list.
            count = len(elements)
            msg = (
                f"Retrieved {count} trusted certificate(s)."
                if count
                else "No trusted certificates found."
            )

            self.module.exit_json(
                changed=False,
                found=count > 0,
                trusted_certificates=elements,
                msg=msg,
            )

        except VcfApiException as e:
            self.module.fail_json(msg=f"Error retrieving trusted certificates: {e}")

    def run(self):
        """Runs the trusted certificates retrieval process."""
        self.get_trusted_certificates()


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = dict(
        vcf_installer_hostname=dict(required=True, type="str"),
        vcf_installer_user=dict(required=True, type="str"),
        vcf_installer_password=dict(required=True, type="str", no_log=True),
        certificate=dict(required=False, type="str"),
    )

    module = AnsibleModule(argument_spec=parameters, supports_check_mode=True)

    trusted_certs_info = VcfInstallerTrustedCertificatesInfo(module)
    trusted_certs_info.run()


if __name__ == "__main__":
    main()
