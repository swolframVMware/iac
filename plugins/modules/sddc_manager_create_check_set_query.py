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
module: sddc_manager_create_check_set_query
short_description: Create a check-set query for SDDC Manager.
description:
    - This module creates a check-set query in SDDC Manager for VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    software_target_bundles:
        description:
            - The target upgrade payload.
        required: true
        type: dict
    domain_info:
        description:
            - The domain information.
        required: true
        type: dict
    sddc_info:
        description:
            - The SDDC information.
        required: true
        type: dict
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Create check-set query for single component upgrade
  broadcom.vcf.sddc_manager_create_check_set_query:
    sddc_manager_hostname: sddcmanager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    software_target_bundles:
      vcenter:
        version: 9.0.0.1-12345678
        bundleId: 12345678-1234-1234-1234-123456789012
    domain_info:
      id: 12345678-1234-1234-1234-123456789012
      name: sfo-m01
      vcenters:
        - id: 12345678-1234-1234-1234-123456789012
          fqdn: sfo-m01-vc01.example.com
      nsxtCluster:
        - id: 12345678-1234-1234-1234-123456789012
          vip: sfo-m01-nsx01.example.com
      clusters:
        - id: 12345678-1234-1234-1234-123456789012
          name: sfo-m01-cl01
    sddc_info:
      id: 12345678-1234-1234-1234-123456789012
      version: 9.0.0.1
  register: vcenter_check_set_query

- name: Create a check-set query for domain upgrade
  broadcom.vcf.sddc_manager_create_check_set_query:
    sddc_manager_hostname: sddcmanager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    software_target_bundles:
      vcenter:
        version: 9.0.0.1-12345678
        bundleId: 12345678-1234-1234-1234-123456789012
      nsx:
        version: 9.0.0.1-12345678
        bundleId: 12345678-1234-1234-1234-123456789012
      host:
        version: 9.0.0.1-12345678
        bundleId: 12345678-1234-1234-1234-123456789012
      sddc_manager:
        version: 9.0.0.1-12345678
        bundleId: 12345678-1234-1234-1234-123456789012
    domain_info:
      id: 12345678-1234-1234-1234-123456789012
      name: sfo-m01
      vcenters:
        - id: 12345678-1234-1234-1234-123456789012
          fqdn: sfo-m01-vc01.example.com
      nsxtCluster:
        - id: 12345678-1234-1234-1234-123456789012
          vip: sfo-m01-nsx01.example.com
      clusters:
        - id: 12345678-1234-1234-1234-123456789012
          name: sfo-m01-cl01
        - id: 12345678-1234-1234-1234-123456789012
          name: sfo-m01-cl02
    sddc_info:
      id: 12345678-1234-1234-1234-123456789012
      version: 9.0.0.1
  register: check_set_query_result
"""

RETURN = r"""
msg:
    description: Status message from the API response
    returned: always
    type: str
meta:
    description: The response from the API operation
    returned: always
    type: dict
"""

import json

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


class CreateCheckSetsPayload:
    """This class represents the payload for creating a check-set query in SDDC Manager.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager
            instance.
        sddc_manager_user (str): The username for authenticating with the SDDC Manager.
        sddc_manager_password (str): The password for authenticating with the SDDC
            Manager.
        software_target_bundles (dict): The target upgrade payload.
        domain_info (dict): The domain information.
        sddc_info (dict): The SDDC information.
        api_client (object): The SDDC Manager API client object.

    Methods:
        transform_payload(self): Transforms the input parameters into the required
            payload format for creating a check-set query.
        get_resource_type(product_type): Retrieves the resource type based on the
            product type.
        get_vcenter_ids(self): Retrieves the vCenter ID from the domain information.
        get_nsxt_cluster_id(self): Retrieves the NSX cluster ID from the domain
            information.
        get_cluster_ids(self): Retrieves the cluster IDs from the domain information.
        get_sddc_manager_id(self): Retrieves the SDDC Manager ID.
        get_resource_id(product_type, vcenter_ids, nsxt_cluster_id, cluster_ids,
            sddc_manager_id): Retrieves the resource ID for a given product type.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params.get("sddc_manager_hostname")
        self.sddc_manager_user = module.params.get("sddc_manager_user")
        self.sddc_manager_password = module.params.get("sddc_manager_password")
        self.software_target_bundles = module.params.get("software_target_bundles")
        self.domain_info = module.params.get("domain_info")
        self.sddc_info = module.params.get("sddc_info")
        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )
        self.target_versions_with_bundles = self.software_target_bundles

    def transform_payload(self):
        """Transforms the input parameters into the required payload format for creating
        a check-set query.
        """
        resources = []

        vcenter_ids = self.get_vcenter_ids()
        nsxt_cluster_id = self.get_nsxt_cluster_id()
        cluster_ids = self.get_cluster_ids()
        sddc_manager_id = self.get_sddc_manager_id()

        for product_type, target in self.target_versions_with_bundles.items():
            resource_id = self.get_resource_id(
                product_type, vcenter_ids, nsxt_cluster_id, cluster_ids, sddc_manager_id
            )
            if resource_id is None:
                self.module.log(f"Resource ID for product type {product_type} is None")
                continue

            resource_obj = {
                "resourceId": resource_id,
                "resourceTargetVersion": target["version"],
                "resourceType": self.get_resource_type(product_type),
            }
            resources.append(resource_obj)

        domain_resource_obj = {
            "domainId": self.domain_info.get("id"),
            "resources": resources,
        }

        output_payload = {"checkSetType": "UPGRADE", "domains": [domain_resource_obj]}

        return output_payload

    @staticmethod
    def get_resource_type(product_type):
        """Retrieves the resource type based on the product type."""
        resource_types = {
            "host": "HOST",
            "nsx": "NSX_T_MANAGER",
            "sddc_manager": "SDDC_MANAGER",
            "vcenter": "VCENTER",
        }
        return resource_types.get(product_type.lower(), "UNKNOWN")

    def get_vcenter_ids(self):
        """Retrieves the vCenter ID from the domain information."""
        vcenters = self.domain_info.get("vcenters", [])
        return [vcenter["id"] for vcenter in vcenters]

    def get_nsxt_cluster_id(self):
        """Retrieves the NSX cluster ID from the domain information."""
        nsxt_cluster = self.domain_info.get("nsxtCluster", {})
        return nsxt_cluster.get("id")

    def get_cluster_ids(self):
        """Retrieves the cluster IDs from the domain information."""
        clusters = self.domain_info.get("clusters", [])
        return [cluster["id"] for cluster in clusters]

    def get_sddc_manager_id(self):
        """Retrieves the SDDC Manager ID."""
        return self.sddc_info.get("id")

    @staticmethod
    def get_resource_id(
        product_type, vcenter_ids, nsxt_cluster_id, cluster_ids, sddc_manager_id
    ):
        """Retrieves the resource ID for a given product type."""
        if product_type.lower() == "vcenter":
            return vcenter_ids[0] if vcenter_ids else None
        elif product_type.lower() == "nsx":
            return nsxt_cluster_id
        elif product_type.lower() == "host":
            return cluster_ids[0] if cluster_ids else None
        elif product_type.lower() == "sddc_manager":
            return sddc_manager_id
        return None


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    module = AnsibleModule(
        argument_spec=dict(
            sddc_manager_hostname=dict(required=True, type="str"),
            sddc_manager_user=dict(required=True, type="str"),
            sddc_manager_password=dict(required=True, type="str", no_log=True),
            software_target_bundles=dict(required=True, type="dict"),
            domain_info=dict(required=True, type="dict"),
            sddc_info=dict(required=True, type="dict"),
        )
    )

    try:
        payload_creator = CreateCheckSetsPayload(module)
        check_sets_payload = payload_creator.transform_payload()

        # module.exit_json(changed=False, meta=check_sets_payload)
        try:
            api_client = SddcManagerApiClient(
                module.params.get("sddc_manager_hostname"),
                module.params.get("sddc_manager_user"),
                module.params.get("sddc_manager_password"),
            )
            result = api_client.create_sddc_manager_check_set(
                json.dumps(check_sets_payload)
            )
            payload_data = result
        except VcfApiException as e:
            module.fail_json(
                changed=False, msg="Unexpected error occurred.", meta=f"Error: {e}"
            )

        module.exit_json(
            changed=False,
            status_code=result.status_code,
            msg=result.message,
            meta=payload_data,
        )

    except VcfApiException as e:
        module.fail_json(
            changed=False, msg="Unexpected error occurred.", meta=f"Error: {e}"
        )


if __name__ == "__main__":
    main()
