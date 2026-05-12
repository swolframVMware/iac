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
module: sddc_manager_cluster_info
short_description: Retrieves cluster information from SDDC Manager.
description:
    - This module retrieves cluster information from SDDC Manager in VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    cluster_name:
        description:
            - The name of the cluster to retrieve information for.
            - Mutually exclusive with I(cluster_id).
        required: false
        type: str
    cluster_id:
        description:
            - The ID of the cluster to retrieve information for.
            - Mutually exclusive with I(cluster_name).
        required: false
        type: str
requirements:
    - python >= 3.12
notes:
    - If neither I(cluster_name) nor I(cluster_id) is specified, returns all clusters.
    - I(cluster_name) and I(cluster_id) are mutually exclusive.
"""

EXAMPLES = r"""
- name: Get specific cluster by name
  broadcom.vcf.sddc_manager_cluster_info:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    cluster_name: w01-cl01
  register: cluster

- name: Get specific cluster by ID
  broadcom.vcf.sddc_manager_cluster_info:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    cluster_id: 12345678-1234-1234-1234-123456789012
  register: cluster
  
- name: Get all clusters
  broadcom.vcf.sddc_manager_cluster_info:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
  register: all_clusters
"""

RETURN = r"""
clusters:
    description: List of clusters (when no specific cluster is requested)
    returned: when neither cluster_name nor cluster_id is specified
    type: list
    elements: dict
    sample:
        - id: "12345678-1234-1234-1234-123456789012"
          name: "w01-cl01"
          status: "ACTIVE"
cluster:
    description: Single cluster (when cluster_name or cluster_id is specified)
    returned: when cluster_name or cluster_id is provided
    type: dict
    sample:
        id: "12345678-1234-1234-1234-123456789012"
        name: "w01-cl01"
        status: "ACTIVE"
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


class SddcManagerClusterInfo:
    """This class retrieves cluster information from SDDC Manager."""

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params["sddc_manager_hostname"]
        self.sddc_manager_user = module.params["sddc_manager_user"]
        self.sddc_manager_password = module.params["sddc_manager_password"]
        self.cluster_name = module.params.get("cluster_name")
        self.cluster_id = module.params.get("cluster_id")
        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )

    def get_all_clusters(self):
        """Retrieves all clusters from SDDC Manager."""
        try:
            api_response = self.api_client.get_clusters_all_clusters()
            return api_response.get("elements", [])
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error retrieving clusters: {e}")

    def get_cluster_by_id(self, cluster_id):
        """Retrieves a specific cluster by ID (direct API call if available)."""
        try:
            # If the API client has a direct method, use it
            # Otherwise, fall back to searching through all clusters
            clusters = self.get_all_clusters()
            for cluster in clusters:
                if cluster.get("id") == cluster_id:
                    return cluster
            return None
        except VcfApiException as e:
            self.module.fail_json(
                msg=f"Error retrieving cluster with ID '{cluster_id}': {e}"
            )

    def get_cluster_by_name(self, cluster_name):
        """Retrieves a specific cluster by name (requires listing all)."""
        clusters = self.get_all_clusters()

        for cluster in clusters:
            if cluster.get("name") == cluster_name:
                return cluster

        return None

    def run(self):
        """Retrieves cluster information."""
        # Get cluster by ID.
        if self.cluster_id:
            cluster = self.get_cluster_by_id(self.cluster_id)

            if not cluster:
                self.module.fail_json(
                    msg=f"Cluster with ID '{self.cluster_id}' not found in SDDC Manager {self.sddc_manager_hostname}."
                )

            self.module.exit_json(
                changed=False,
                cluster=cluster,
            )

        # Get cluster by name.
        elif self.cluster_name:
            cluster = self.get_cluster_by_name(self.cluster_name)

            if not cluster:
                self.module.fail_json(
                    msg=f"Cluster '{self.cluster_name}' not found in SDDC Manager {self.sddc_manager_hostname}."
                )

            self.module.exit_json(
                changed=False,
                cluster=cluster,
            )

        # Get all clusters.
        else:
            clusters = self.get_all_clusters()

            self.module.exit_json(
                changed=False,
                clusters=clusters,
            )


def main():
    """Main entry point for the Ansible module."""
    parameters = dict(
        sddc_manager_hostname=dict(required=True, type="str"),
        sddc_manager_user=dict(required=True, type="str"),
        sddc_manager_password=dict(required=True, type="str", no_log=True),
        cluster_name=dict(required=False, type="str"),
        cluster_id=dict(required=False, type="str"),
    )

    module = AnsibleModule(
        argument_spec=parameters,
        supports_check_mode=True,
        mutually_exclusive=[
            ["cluster_name", "cluster_id"],
        ],
    )

    cluster_info = SddcManagerClusterInfo(module)
    cluster_info.run()


if __name__ == "__main__":
    main()
