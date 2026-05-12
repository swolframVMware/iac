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
module: sddc_manager_network_pool
short_description: Manages network pools in SDDC Manager.
description:
    - This module manages network pools in SDDC Manager for VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    network_pool_name:
        description:
            - The name of the network pool.
            - Required when state is 'absent' or when querying existing pools.
        required: false
        type: str
    network_pool_payload:
        description:
            - The payload containing the network pool information.
            - Required when state is 'present'.
        required: false
        type: dict
    state:
        description:
            - The desired state of the network pool.
        required: true
        type: str
        choices:
            - present
            - absent
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Add Network Pool
  broadcom.vcf.sddc_manager_network_pool:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: present
    network_pool_payload:
      name: network-pool-01
      networks:
        - type: VSAN
          vlanId: 100
          mtu: 1500
          subnet: 192.168.100.0/24
          gateway: 192.168.100.1
          ipPools:
            - start: 192.168.100.10
              end: 192.168.100.50

- name: Remove Network Pool
  broadcom.vcf.sddc_manager_network_pool:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: absent
    network_pool_name: network-pool-01
"""

RETURN = r"""
msg:
    description: Error message when operation fails
    returned: on failure
    type: str
    sample: >
        There is no network pool named network-pool-01 in SDDC Manager
        sddc-manager.example.com.
meta:
    description: The network pool information or creation response
    returned: on success
    type: dict
    sample:
        id: "12345678-1234-1234-1234-123456789012"
        name: "network-pool-01"
        networks:
          - type: "VSAN"
            vlanId: 100
changed:
    description: Whether the module made changes
    returned: always
    type: bool
    sample: false
"""

import json

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


class SddcManagerNetworkPool:
    """This class represents network pools in SDDC Manager."""

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params["sddc_manager_hostname"]
        self.sddc_manager_user = module.params["sddc_manager_user"]
        self.sddc_manager_password = module.params["sddc_manager_password"]
        self.network_pool_name = module.params.get("network_pool_name")
        self.network_pool_payload = module.params.get("network_pool_payload")
        self.state = module.params["state"]
        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )

    def _get_pool_name(self):
        """Extract pool name from payload or parameter."""
        if self.network_pool_name:
            return self.network_pool_name
        if self.network_pool_payload:
            return self.network_pool_payload.get("name")
        return None

    def get_network_pool_by_name(self, pool_name):
        """Retrieves the network pool by name from SDDC Manager.

        Args:
            pool_name (str): The name of the network pool to retrieve.

        Returns:
            dict: The network pool data if found, None otherwise.
        """
        try:
            api_response = self.api_client.get_network_pools()
            response = api_response

            for np in response.get("elements", []):
                if np.get("name") == pool_name:
                    return np

            return None
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error retrieving network pools: {e}")

    def add_network_pool(self):
        """Adds a network pool in SDDC Manager."""
        try:
            api_response = self.api_client.create_network_pools(
                json.dumps(self.network_pool_payload)
            )
            return api_response
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error adding network pool: {e}")

    def remove_network_pool(self, pool_id):
        """Removes a network pool from SDDC Manager.

        Args:
            pool_id (str): The ID of the network pool to delete.
        """
        try:
            api_response = self.api_client.delete_network_pools(pool_id)
            return api_response
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error removing network pool: {e}")

    def run(self):
        """Runs the network pool action based on the provided state."""

        # Check mode for present state.
        if self.module.check_mode and self.state == "present":
            pool_name = self._get_pool_name()

            if not pool_name:
                self.module.fail_json(
                    msg="network_pool_name or network_pool_payload.name is required for state 'present'."
                )

            if not self.network_pool_payload:
                self.module.fail_json(
                    msg="network_pool_payload is required for state 'present'."
                )

            existing_pool = self.get_network_pool_by_name(pool_name)

            if existing_pool:
                self.module.exit_json(
                    changed=False,
                    msg=f"Check Mode: Network pool '{pool_name}' already exists; no changes would be made.",
                )
            else:
                self.module.exit_json(
                    changed=True,
                    msg=f"Check Mode: Would add network pool '{pool_name}'.",
                )

        # Check mode for absent state.
        if self.module.check_mode and self.state == "absent":
            if not self.network_pool_name:
                self.module.fail_json(
                    msg="network_pool_name is required for state 'absent'."
                )

            existing_pool = self.get_network_pool_by_name(self.network_pool_name)

            if existing_pool:
                self.module.exit_json(
                    changed=True,
                    msg=f"Check Mode: Would remove network pool '{self.network_pool_name}'.",
                )
            else:
                self.module.exit_json(
                    changed=False,
                    msg=f"Check Mode: Network pool '{self.network_pool_name}' does not exist; no changes would be made.",
                )

        # Add new network pool. (state=present)
        if self.state == "present":
            pool_name = self._get_pool_name()

            if not pool_name:
                self.module.fail_json(
                    msg="network_pool_name or network_pool_payload.name is required for state 'present'."
                )

            if not self.network_pool_payload:
                self.module.fail_json(
                    msg="network_pool_payload is required for state 'present'."
                )

            # Check if network pool exists.
            existing_pool = self.get_network_pool_by_name(pool_name)

            if existing_pool:
                self.module.exit_json(
                    changed=False,
                    msg=f"Network pool '{pool_name}' already exists; no changes needed.",
                    meta=existing_pool,
                )
            else:
                result = self.add_network_pool()
                self.module.exit_json(
                    changed=True,
                    msg=f"Successfully added network pool '{pool_name}'.",
                    meta=result,
                )

        # Remove network pool. (state=absent)
        elif self.state == "absent":
            if not self.network_pool_name:
                self.module.fail_json(
                    msg="network_pool_name is required for state 'absent'."
                )

            existing_pool = self.get_network_pool_by_name(self.network_pool_name)

            if not existing_pool:
                self.module.exit_json(
                    changed=False,
                    msg=f"Network pool '{self.network_pool_name}' does not exist; no changes needed.",
                )
            else:
                pool_id = existing_pool.get("id")
                result = self.remove_network_pool(pool_id)
                self.module.exit_json(
                    changed=True,
                    msg=f"Successfully removed network pool '{self.network_pool_name}'.",
                    meta=result,
                )


def main():
    """Main entry point for the Ansible module."""
    parameters = dict(
        sddc_manager_hostname=dict(required=True, type="str"),
        sddc_manager_user=dict(required=True, type="str"),
        sddc_manager_password=dict(required=True, type="str", no_log=True),
        network_pool_name=dict(required=False, type="str"),
        network_pool_payload=dict(required=False, type="dict"),
        state=dict(required=True, type="str", choices=["present", "absent"]),
    )

    module = AnsibleModule(supports_check_mode=True, argument_spec=parameters)
    network_pool = SddcManagerNetworkPool(module)
    network_pool.run()


if __name__ == "__main__":
    main()
