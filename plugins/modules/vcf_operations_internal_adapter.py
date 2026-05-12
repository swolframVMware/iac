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
module: vcf_operations_internal_adapter
short_description: This module gets the internal adapter from VCF Operations
description:
    - This module is a wrapper around the VCF Operations API. It allows gatherin information on the internal adapters.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.vcf_operations
options:
    sddc_hostname:
        description:
            - The hostname of the SDDC Manager.
        required: false
        type: str
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Get the internal adapter from VCF Operations
  broadcom.vcf.vcf_operations_internal_adapters:
    vcf_operations_hostname: vcf-operations.example.com
    vcf_operations_user: admin
    vcf_operations_password: password
    sddc_hostname: sddc-manager.example.com
"""

RETURN = r"""
meta:
    description: Result payload from VCF Operations internal adapters API.
    returned: always
    type: dict
    contains:
        vcfDomainTree:
            description: List of VCF domains and their internal adapter information.
            type: list
            elements: dict
            returned: when available
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.vcf_operations import (
    VcfOperationsApiClient,
)


class VcfOperationsInternalAdapters:
    """This class represents the internal adapters in VCF Operations.

    Args:
        module: The Ansible module object.

    Attributes:

        module (object): The Ansible module object.
        vcf_operations_hostname (str): The hostname or IP address of the VCF Operations
            deployment.
        vcf_operations_user (str): The username for authenticating with VCF Operations.
        vcf_operations_password (str): The password for authenticating with VCF
            Operations.
        sddc_hostname (str): The hostname of the SDDC Manager.
        api_client (object): The VCF Operations API client object.

    Methods:
        get_internal_adapters(self): Retrieves the list of internal adapters from
            VCF Operations.
        get_internal_adapter_by_name(self): Retrieves the internal adapter by SDDC
            Manager hostname from VCF Operations.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.vcf_operations_hostname = module.params["vcf_operations_hostname"]
        self.vcf_operations_user = module.params["vcf_operations_user"]
        self.vcf_operations_password = module.params["vcf_operations_password"]
        self.sddc_hostname = module.params["sddc_hostname"]
        self.api_client = VcfOperationsApiClient(
            self.vcf_operations_hostname,
            self.vcf_operations_user,
            self.vcf_operations_password,
        )

    def get_internal_adapters(self):
        """Retrieves the list of internal adapters from VCF Operations."""
        try:
            api_response = self.api_client.get_vcf_operations_internal_adapters()
            self.module.exit_json(changed=False, meta=api_response)
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error: {e}")

    def get_internal_adapter_by_name(self):
        """Retrieves the internal adapter by SDDC Manager hostname from VCF Operations."""
        try:
            api_response = self.api_client.get_vcf_operations_internal_adapters()
            for vcf in api_response["vcfDomainTree"]:
                if vcf["instanceHostname"] == self.sddc_hostname:
                    self.module.exit_json(
                        changed=False,
                        meta=api_response["vcfDomainTree"][0]["internalId"],
                    )

            self.module.fail_json(
                msg=f"Unable to find SDDC Manager {self.sddc_hostname}."
            )
        except VcfApiException as e:
            self.module.fail_json(msg=f"Unexpected error occurred. Error: {str(e)}")


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = dict(
        vcf_operations_hostname=dict(required=True, type="str"),
        vcf_operations_user=dict(required=True, type="str"),
        vcf_operations_password=dict(required=True, type="str", no_log=True),
        sddc_hostname=dict(required=False, type="str"),
    )

    module = AnsibleModule(argument_spec=parameters, supports_check_mode=True)

    host_commission = VcfOperationsInternalAdapters(module)
    host_commission.get_internal_adapter_by_name()


if __name__ == "__main__":
    main()
