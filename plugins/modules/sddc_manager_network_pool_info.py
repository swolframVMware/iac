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
module: sddc_manager_network_pool_info
short_description: Retrieves information about network pools in SDDC Manager.
description:
    - This module retrieves information about network pools in SDDC Manager for VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    network_pool_name:
        description:
            - The name of the network pool to retrieve.
            - Mutually exclusive with I(network_pool_id).
        required: false
        type: str
    network_pool_id:
        description:
            - The ID of the network pool to retrieve.
            - Mutually exclusive with I(network_pool_name).
        required: false
        type: str
requirements:
    - python >= 3.12
notes:
    - If neither I(network_pool_name) nor I(network_pool_id) is specified, returns all network pools.
    - I(network_pool_name) and I(network_pool_id) are mutually exclusive.
"""

EXAMPLES = r"""
- name: Get specific network pool by name
  broadcom.vcf.sddc_manager_network_pool_info:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    network_pool_name: network-pool-01
  register: network_pool

- name: Get specific network pool by ID
  broadcom.vcf.sddc_manager_network_pool_info:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    network_pool_id: "12345678-1234-1234-1234-123456789012"
  register: network_pool

- name: Get all network pools
  broadcom.vcf.sddc_manager_network_pool_info:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
  register: all_network_pools
"""

RETURN = r"""
network_pools:
    description: List of network pools (when no specific pool is requested)
    returned: when neither network_pool_name nor network_pool_id is specified
    type: list
    elements: dict
    sample:
        - id: "12345678-1234-1234-1234-123456789012"
          name: "network-pool-01"
          networks:
            - type: "VSAN"
              vlanId: 100
network_pool:
    description: Single network pool (when network_pool_name or network_pool_id is specified)
    returned: when network_pool_name or network_pool_id is provided
    type: dict
    sample:
        id: "12345678-1234-1234-1234-123456789012"
        name: "network-pool-01"
        networks:
          - type: "VSAN"
            vlanId: 100
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


class SddcManagerNetworkPoolInfo:
    """This class retrieves network pool information from SDDC Manager."""

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params["sddc_manager_hostname"]
        self.sddc_manager_user = module.params["sddc_manager_user"]
        self.sddc_manager_password = module.params["sddc_manager_password"]
        self.network_pool_name = module.params.get("network_pool_name")
        self.network_pool_id = module.params.get("network_pool_id")
        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )

    def get_all_network_pools(self):
        """Retrieves all network pools from SDDC Manager."""
        try:
            api_response = self.api_client.get_network_pools()  # ✅ CORRECT (plural)
            return api_response.get("elements", [])
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error retrieving network pools: {e}")

    def get_network_pool_by_id(self, pool_id):
        """Retrieves a specific network pool by ID (direct API call)."""
        try:
            api_response = self.api_client.get_network_pool_by_id(pool_id)
            return api_response
        except VcfApiException as e:
            self.module.fail_json(
                msg=f"Error retrieving network pool with ID '{pool_id}': {e}"
            )

    def get_network_pool_by_name(self, pool_name):
        """Retrieves a specific network pool by name (requires listing all)."""
        pools = self.get_all_network_pools()

        for pool in pools:
            if pool.get("name") == pool_name:
                return pool

        return None

    def run(self):
        """Retrieves network pool information."""
        # Get network pool by ID.
        if self.network_pool_id:
            pool = self.get_network_pool_by_id(self.network_pool_id)

            if not pool:
                self.module.fail_json(
                    msg=f"Network pool with ID '{self.network_pool_id}' not found in SDDC Manager {self.sddc_manager_hostname}."
                )

            self.module.exit_json(
                changed=False,
                network_pool=pool,
            )

        # Get network pool by name.
        elif self.network_pool_name:
            pool = self.get_network_pool_by_name(self.network_pool_name)

            if not pool:
                self.module.fail_json(
                    msg=f"Network pool '{self.network_pool_name}' not found in SDDC Manager {self.sddc_manager_hostname}."
                )

            self.module.exit_json(
                changed=False,
                network_pool=pool,
            )

        # Get all network pools.
        else:
            pools = self.get_all_network_pools()

            self.module.exit_json(
                changed=False,
                network_pools=pools,
            )


def main():
    """Main entry point for the Ansible module."""
    parameters = dict(
        sddc_manager_hostname=dict(required=True, type="str"),
        sddc_manager_user=dict(required=True, type="str"),
        sddc_manager_password=dict(required=True, type="str", no_log=True),
        network_pool_name=dict(required=False, type="str"),
        network_pool_id=dict(required=False, type="str"),
    )

    module = AnsibleModule(
        argument_spec=parameters,
        supports_check_mode=True,
        mutually_exclusive=[
            ["network_pool_name", "network_pool_id"],
        ],
    )

    network_pool_info = SddcManagerNetworkPoolInfo(module)
    network_pool_info.run()


if __name__ == "__main__":
    main()
