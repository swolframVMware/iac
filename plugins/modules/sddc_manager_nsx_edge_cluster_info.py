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
module: sddc_manager_nsx_edge_cluster_info
short_description: Retrieves information about NSX Edge clusters in SDDC Manager.
description:
    - This module retrieves information about NSX Edge clusters in SDDC Manager for VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    edge_cluster_name:
        description:
            - The name of the NSX Edge cluster to retrieve.
            - Mutually exclusive with I(edge_cluster_id).
        required: false
        type: str
    edge_cluster_id:
        description:
            - The ID of the NSX Edge cluster to retrieve.
            - Mutually exclusive with I(edge_cluster_name).
        required: false
        type: str
requirements:
    - python >= 3.12
notes:
    - If neither I(edge_cluster_name) nor I(edge_cluster_id) is specified, returns all edge clusters.
    - I(edge_cluster_name) and I(edge_cluster_id) are mutually exclusive.
"""

EXAMPLES = r"""
- name: Get specific NSX Edge cluster by name
  broadcom.vcf.sddc_manager_nsx_edge_cluster_info:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    edge_cluster_name: edge-cluster-01
  register: edge_cluster

- name: Get specific NSX Edge cluster by ID
  broadcom.vcf.sddc_manager_nsx_edge_cluster_info:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    edge_cluster_id: "12345678-1234-1234-1234-123456789012"
  register: edge_cluster

- name: Get all NSX Edge clusters
  broadcom.vcf.sddc_manager_nsx_edge_cluster_info:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
  register: all_edge_clusters
"""

RETURN = r"""
edge_clusters:
    description: List of NSX Edge clusters (when no specific cluster is requested)
    returned: when neither edge_cluster_name nor edge_cluster_id is specified
    type: list
    elements: dict
    sample:
        - id: "12345678-1234-1234-1234-123456789012"
          name: "edge-cluster-01"
          edgeClusterType: "NSX-T"
edge_cluster:
    description: Single NSX Edge cluster (when edge_cluster_name or edge_cluster_id is specified)
    returned: when edge_cluster_name or edge_cluster_id is provided
    type: dict
    sample:
        id: "12345678-1234-1234-1234-123456789012"
        name: "edge-cluster-01"
        edgeClusterType: "NSX-T"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


class SddcManagerNsxEdgeClusterInfo:
    """This class retrieves NSX Edge cluster information from SDDC Manager."""

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params["sddc_manager_hostname"]
        self.sddc_manager_user = module.params["sddc_manager_user"]
        self.sddc_manager_password = module.params["sddc_manager_password"]
        self.edge_cluster_name = module.params.get("edge_cluster_name")
        self.edge_cluster_id = module.params.get("edge_cluster_id")
        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )

    def get_all_edge_clusters(self):
        """Retrieves all NSX Edge clusters from SDDC Manager."""
        try:
            api_response = self.api_client.get_edge_clusters()
            return api_response.get("elements", [])
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error retrieving edge clusters: {e}")

    def get_edge_cluster_by_id(self, cluster_id):
        """Retrieves a specific NSX Edge cluster by ID."""
        try:
            api_response = self.api_client.get_edge_cluster_by_id(cluster_id)
            return api_response
        except VcfApiException as e:
            self.module.fail_json(
                msg=f"Error retrieving edge cluster with ID '{cluster_id}': {e}"
            )

    def get_edge_cluster_by_name(self, cluster_name):
        """Retrieves a specific NSX Edge cluster by name."""
        clusters = self.get_all_edge_clusters()

        for cluster in clusters:
            if cluster.get("name") == cluster_name:
                return cluster

        return None

    def run(self):
        """Retrieves NSX Edge cluster information."""
        # Get NSX Edge cluster by ID.
        if self.edge_cluster_id:
            cluster = self.get_edge_cluster_by_id(self.edge_cluster_id)

            if not cluster:
                self.module.fail_json(
                    msg=f"Edge cluster with ID '{self.edge_cluster_id}' not found in SDDC Manager {self.sddc_manager_hostname}."
                )

            self.module.exit_json(
                changed=False,
                edge_cluster=cluster,
            )

        # Get NSX Edge cluster by name.
        elif self.edge_cluster_name:
            cluster = self.get_edge_cluster_by_name(self.edge_cluster_name)

            if not cluster:
                self.module.fail_json(
                    msg=f"Edge cluster '{self.edge_cluster_name}' not found in SDDC Manager {self.sddc_manager_hostname}."
                )

            self.module.exit_json(
                changed=False,
                edge_cluster=cluster,
            )

        # Get all NSX Edge clusters.
        else:
            clusters = self.get_all_edge_clusters()

            self.module.exit_json(
                changed=False,
                edge_clusters=clusters,
            )


def main():
    """Main entry point for the Ansible module."""
    parameters = dict(
        sddc_manager_hostname=dict(required=True, type="str"),
        sddc_manager_user=dict(required=True, type="str"),
        sddc_manager_password=dict(required=True, type="str", no_log=True),
        edge_cluster_name=dict(required=False, type="str"),
        edge_cluster_id=dict(required=False, type="str"),
    )

    module = AnsibleModule(
        argument_spec=parameters,
        supports_check_mode=True,
        mutually_exclusive=[
            ["edge_cluster_name", "edge_cluster_id"],
        ],
    )

    edge_cluster_info = SddcManagerNsxEdgeClusterInfo(module)
    edge_cluster_info.run()


if __name__ == "__main__":
    main()
