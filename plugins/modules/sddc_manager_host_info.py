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
module: sddc_manager_host_info
short_description: Retrieves information about ESX hosts in SDDC Manager.
description:
    - This module retrieves information about ESX hosts in SDDC Manager for VMware Cloud Foundation.
    - Supports querying by FQDN, status, or retrieving all hosts.
    - Can return full host information or just IDs.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    fqdn:
        description:
            - The FQDN of a specific ESX host to query.
            - Takes precedence over host_status if both are provided.
        required: false
        type: str
    host_status:
        description:
            - Filter hosts by status.
        required: false
        type: str
        choices:
            - ASSIGNED
            - UNASSIGNED_USEABLE
            - UNASSIGNED_UNUSEABLE
    format:
        description:
            - Output format for the results.
            - info returns complete host information.
            - id returns only hostname and ID mapping.
        required: false
        type: str
        choices:
            - info
            - id
        default: info
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Get All ESX Hosts
  broadcom.vcf.sddc_manager_host_info: 
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
  register: all_hosts

- name: Get Specific Host
  broadcom.vcf.sddc_manager_host_info: 
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    fqdn: esx-01.example.com
  register: single_host

- name: Get Unassigned Usable Hosts
  broadcom.vcf.sddc_manager_host_info:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    host_status: UNASSIGNED_USEABLE
    format: info
  register: usable_hosts

- name: Get Unassigned Usable Host IDs
  broadcom.vcf.sddc_manager_host_info: 
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    host_status: UNASSIGNED_USEABLE
    format: id
  register: host_ids
"""

RETURN = r"""
msg:
    description: Informational or error message
    returned: always
    type: str
    sample: "Retrieved 4 ESX host(s)."
meta:
    description: Dictionary of ESX hosts indexed by hostname
    returned: on success
    type: dict
    sample:
        esx-01.example.com:
            id: "12345678-1234-1234-1234-123456789012"
            fqdn: "esx-01.example.com"
            status: "UNASSIGNED_USEABLE"
            hardwareVendor: "Dell Inc."
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


class SddcManagerHostInfo:
    """This class represents the ESX host information from SDDC Manager.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager instance.
        sddc_manager_user (str): The username for authenticating with the SDDC Manager.
        sddc_manager_password (str): The password for authenticating with the SDDC Manager.
        fqdn (str): The FQDN of a specific ESX host (optional).
        host_status (str): The status filter for ESX hosts (optional).
        format (str): Output format - 'info' or 'id'.

    Methods:
        get_hosts_info(self): Retrieves ESX host information from SDDC Manager.
        format_response(self, hosts): Formats the response based on requested format.
        run(self): Runs the ESX host information retrieval process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params["sddc_manager_hostname"]
        self.sddc_manager_user = module.params["sddc_manager_user"]
        self.sddc_manager_password = module.params["sddc_manager_password"]
        self.fqdn = module.params.get("fqdn")
        self.host_status = module.params.get("host_status")
        self.format = module.params.get("format", "info")
        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )

    def get_hosts_info(self):
        """Retrieves ESX host information from SDDC Manager.

        Returns:
            dict: API response containing host elements.
        """
        try:
            # Priority order: fqdn > host_status > all hosts
            if self.fqdn:
                api_response = self.api_client.get_hosts_by_fqdn(self.fqdn)
            elif self.host_status:
                api_response = self.api_client.get_hosts_by_status(self.host_status)
            else:
                api_response = self.api_client.get_all_hosts()

            return api_response

        except VcfApiException as e:
            self.module.fail_json(msg=f"Error retrieving host information: {e}")

    def format_response(self, response):
        """Formats the response based on requested format.

        Args:
            response (dict): API response containing host elements.

        Returns:
            dict: Formatted host information indexed by FQDN.
        """
        hosts = response.get("elements", [])

        if not hosts:
            return {}

        result = {}

        if self.format == "id":
            # Return only FQDN -> ID mapping
            for host in hosts:
                result[host["fqdn"]] = {"id": host["id"]}
        else:
            # Return full host information
            for host in hosts:
                result[host["fqdn"]] = host

        return result

    def run(self):
        """Runs the ESX host information retrieval process."""
        response = self.get_hosts_info()
        hosts = response.get("elements", [])

        if not hosts:
            if self.fqdn:
                self.module.exit_json(
                    changed=False,
                    meta={},
                    msg=f"Host '{self.fqdn}' not found in SDDC Manager (may need commissioning).",
                )
            else:
                filter_msg = (
                    f"with status '{self.host_status}'" if self.host_status else ""
                )
                self.module.fail_json(
                    msg=f"No ESX hosts found {filter_msg} in SDDC Manager {self.sddc_manager_hostname}."
                )

        formatted_hosts = self.format_response(response)
        host_count = len(formatted_hosts)
        filter_desc = ""

        if self.fqdn:
            filter_desc = f" for FQDN '{self.fqdn}'"
        elif self.host_status:
            filter_desc = f" with status '{self.host_status}'"

        self.module.exit_json(
            changed=False,
            meta=formatted_hosts,
            msg=f"Retrieved {host_count} ESX host(s){filter_desc}.",
        )


def main():
    """Main entry point for the Ansible module."""
    parameters = dict(
        sddc_manager_hostname=dict(required=True, type="str"),
        sddc_manager_user=dict(required=True, type="str"),
        sddc_manager_password=dict(required=True, type="str", no_log=True),
        fqdn=dict(required=False, type="str"),
        host_status=dict(
            required=False,
            type="str",
            choices=["ASSIGNED", "UNASSIGNED_USEABLE", "UNASSIGNED_UNUSEABLE"],
        ),
        format=dict(required=False, type="str", choices=["info", "id"], default="info"),
    )

    module = AnsibleModule(argument_spec=parameters, supports_check_mode=True)

    host_info = SddcManagerHostInfo(module)
    host_info.run()


if __name__ == "__main__":
    main()
