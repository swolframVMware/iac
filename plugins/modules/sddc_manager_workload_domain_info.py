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
module: sddc_manager_workload_domain_info
short_description: Retrieves workload domain information from SDDC Manager.
description:
    - This module retrieves workload domain information from SDDC Manager for VMware Cloud Foundation.
    - Can retrieve a specific domain by name or all domains.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    domain:
        description:
            - The name of the workload domain to retrieve information for.
            - If not specified, returns all workload domains.
        required: false
        type: str
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Get Workload Domain Information
  broadcom.vcf.sddc_manager_workload_domain_info:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
"""

RETURN = r"""
msg:
    description: Error or status message
    returned: on failure or when retrieving all domains
    type: str
    sample: "Retrieved 3 workload domain(s)."
domain:
    description: Single domain information (when domain name is specified)
    returned: when domain parameter is provided
    type: dict
    sample:
        id: "12345678-1234-1234-1234-123456789012"
        name: "sfo-w01"
        type: "WORKLOAD"
        status: "ACTIVE"
domains:
    description: List of all workload domains (when no domain name is specified)
    returned: when workload domain parameter is not provided
    type: list
    elements: dict
    sample:
        - id: "12345678-1234-1234-1234-123456789012"
          name: "sfo-m01"
          type: "MANAGEMENT"
          status: "ACTIVE"
        - id: "87654321-4321-4321-4321-210987654321"
          name: "sfo-w01"
          type: "WORKLOAD"
          status: "ACTIVE"
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


class SddcManagerDomainInfo:
    """This class represents the workload domain information from SDDC Manager.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager
            instance.
        sddc_manager_user (str): The username for authenticating with the SDDC Manager.
        sddc_manager_password (str): The password for authenticating with the SDDC
            Manager.
        domain (str): The name of the workload domain to retrieve. If None, all domains
            are retrieved.

    Methods:
        get_domain_info(self): Retrieves workload domain information from SDDC Manager.
        run(self): Runs the workload domain information process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params["sddc_manager_hostname"]
        self.sddc_manager_user = module.params["sddc_manager_user"]
        self.sddc_manager_password = module.params["sddc_manager_password"]
        self.domain = module.params.get("domain")
        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )

    def get_domain_info(self):
        """Retrieves workload domain information from SDDC Manager.

        Returns:
            dict or list: Workoad domain information if found, None otherwise.
        """
        try:
            api_response = self.api_client.get_all_domains()
            response = api_response

            if not response["elements"]:
                return None

            if self.domain:
                for domain in response["elements"]:
                    if domain["name"] == self.domain:
                        return domain
                return None
            else:
                return response["elements"]

        except VcfApiException as e:
            self.module.fail_json(msg=f"Error retrieving workload domains: {e}")

    def run(self):
        """Runs the domain information retrieval process."""
        if self.domain:
            domain = self.get_domain_info()

            if domain is None:
                self.module.fail_json(
                    msg=f"Workload domain '{self.domain}' not found in SDDC Manager {self.sddc_manager_hostname}."
                )

            self.module.exit_json(changed=False, domain=domain)
        else:
            domains = self.get_domain_info()
            if domains:
                self.module.exit_json(
                    changed=False,
                    msg=f"Retrieved {len(domains)} workload domain(s).",
                    domains=domains,
                )
            else:
                self.module.exit_json(
                    changed=False, msg="No workload domains found.", domains=[]
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
        domain=dict(required=False, type="str"),
    )

    module = AnsibleModule(
        argument_spec=parameters,
        supports_check_mode=True,
    )

    domain_info = SddcManagerDomainInfo(module)
    domain_info.run()


if __name__ == "__main__":
    main()
