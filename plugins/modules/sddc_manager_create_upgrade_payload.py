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
module: sddc_manager_create_upgrade_payload
short_description: Creates an upgrade payload for SDDC Manager.
description:
    - This module creates an upgrade payload in SDDC Manager for VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    target_versions_with_bundles:
        description:
            - The target upgrade payload.
        required: true
        type: dict
    upgrade_component:
        description:
            - The component to upgrade.
        required: true
        type: str
        choices:
            - sddc_manager
            - vcenter
            - nsx
            - host
    domain_info:
        description:
            - The domain information.
        required: true
        type: dict
    nsxt_cluster_info:
        description:
            - The NSX cluster information.
        required: false
        type: dict
    upgraded_edge_cluster:
        description:
            - Whether to upgrade the NSX Edge cluster.
        required: false
        type: bool
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Create upgrade payload for SDDC Manager
  broadcom.vcf.sddc_manager_create_upgrade_payload:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    upgrade_component: sddc_manager
    target_versions_with_bundles:
      sddc_manager:
        software_install_bundleId: 12345678-1234-1234-1234-123456789012
    domain_info:
      id: 12345678-1234-1234-1234-123456789012

- name: Create upgrade payload for NSX
  broadcom.vcf.sddc_manager_create_upgrade_payload:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    upgrade_component: nsx
    upgraded_edge_cluster: true
    target_versions_with_bundles:
      nsx:
        bundleId: 12345678-1234-1234-1234-123456789012
    domain_info:
      id: 12345678-1234-1234-1234-123456789012
      clusters:
        - id: 12345678-1234-1234-1234-123456789012

- name: Create upgrade payload for ESX hosts in a cluster
  broadcom.vcf.sddc_manager_create_upgrade_payload:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    upgrade_component: host
    target_versions_with_bundles:
      host:
        bundleId: 12345678-1234-1234-1234-123456789012
        host_image:
          personalityId: 12345678-1234-1234-1234-123456789012
    domain_info:
      clusters:
        - id: cluster-1
        - id: cluster-2
"""

RETURN = r"""
msg:
    description: Error message when operation fails.
    returned: on failure
    type: str
    sample: "Error: Not a valid upgrade component."
meta:
    description: The generated upgrade payload or API response metadata for the requested operation.
    returned: on success
    type: dict
    sample:
        bundleId: "bundle-123"
        resourceType: "DOMAIN"
        resourceUpgradeSpecs:
          - resourceId: "12345678-1234-1234-1234-123456789012"
            upgradeNow: true
        nsxtUpgradeUserInputSpecs:
          - nsxtHostClusterUpgradeSpecs:
              - hostClusterId: "12345678-1234-1234-1234-123456789012"
                liveUpgrade: false
            nsxtUpgradeOptions:
              isEdgeOnlyUpgrade: false
              isHostClustersUpgradeParallel: false
              isEdgeClustersUpgradeParallel: false
changed:
    description: Whether the module made changes or a change would be performed.
    returned: always
    type: bool
    sample: true
"""

"""
Sample Payload:
{
    "bundleId": "string",
    "resourceType": "One among: DOMAIN, CLUSTER, UNASSIGNED_HOST",
    "parallelUpgrade": false,
    "draftMode": false,
    "resourceUpgradeSpecs": [
        {
            "resourceId": "string",
            "shutdownVms": false,
            "toVersion": "string",
            "scheduledTimestamp": "string",
            "upgradeNow": false,
            "personalitySpec": {
                "personalityId": "string",
                "hardwareSupportSpecs": [
                    {
                        "name": "string",
                        "packageSpec": {
                            "name": "string",
                            "version": "string"
                        }
                    }
                ]
            },
            "customIsoSpec": {
                "id": "string"
            },
            "enableQuickboot": false,
            "evacuateOfflineVms": false,
            "esxUpgradeOptionsSpec": {
                "esxUpgradeFailureAction": {
                    "retryDelay": 0,
                    "retryCount": 0,
                    "action": "FAIL, RETRY"
                },
                "enforceHclValidation": false,
                "enableQuickPatch": false,
                "enableQuickboot": false,
                "evacuateOfflineVms": false,
                "disableHac": false,
                "disableDpm": false,
                "preRemediationPowerAction": (
                    "POWER_OFF_VMS, SUSPEND_VMS, "
                    "DO_NOT_CHANGE_VMS_POWER_STATE, "
                    "SUSPEND_VMS_TO_MEMORY"
                )
            }
        }
    ],
    "nsxtUpgradeUserInputSpecs": [
        {
            "nsxtHostClusterUpgradeSpecs": [
                {
                    "hostClusterId": "string",
                    "hostParallelUpgrade": false,
                    "liveUpgrade": false
                }
            ],
            "nsxtEdgeClusterUpgradeSpecs": [
                {
                    "edgeClusterId": "string",
                    "edgeParallelUpgrade": false
                }
            ],
            "nsxtUpgradeOptions": {
                "isEdgeOnlyUpgrade": false,
                "isHostClustersUpgradeParallel": false,
                "isEdgeClustersUpgradeParallel": false
            },
            "nsxtId": "string"
        }
    ],
    "vcenterUpgradeUserInputSpecs": [
        {
            "resourceId": "string",
            "upgradeMechanism": "One among: ReducedDowntimeMigration, InPlace",
            "startSwitchoverTimestamp": "string",
            "temporaryNetwork": {
                "networkMode": "One among: STATIC, AUTOMATIC",
                "ipAddress": "string",
                "subnetMask": "string",
                "gateway": "string"
            }
        }
    ]
}
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


class CreateUpgradePayload:
    """This class represents the upgrade payload in SDDC Manager.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager
            instance.
        sddc_manager_user (str): The username for authenticating with the SDDC Manager.
        sddc_manager_password (str): The password for authenticating with the SDDC
            Manager.
        target_versions_with_bundles (dict): The target upgrade payload.
        upgrade_component (str): The component to upgrade. One of 'sddc_manager',
            'vcenter', 'nsx', or 'host'.
        domain_info (dict): The domain information.
        nsxt_cluster_info (dict): The NSX cluster information.
        upgraded_edge_cluster (bool): Whether to upgrade the NSX Edge cluster.
        api_client (object): The SDDC Manager API client object.

        Methods:
        get_edge_cluster_by_nsxt_id(nsxt_id): Retrieves the NSX Edge cluster information
            from SDDC Manager based on ID.
        transform_payload(self): Transforms the upgrade payload based on the upgrade
            component.
    """

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params.get("sddc_manager_hostname")
        self.sddc_manager_user = module.params.get("sddc_manager_user")
        self.sddc_manager_password = module.params.get("sddc_manager_password")
        self.target_versions_with_bundles = module.params.get(
            "target_versions_with_bundles"
        )
        self.upgrade_component = module.params.get("upgrade_component")
        self.domain_info = module.params.get("domain_info")
        self.nsxt_cluster_info = module.params.get("nsxt_cluster_info")
        self.upgraded_edge_cluster = module.params.get("upgraded_edge_cluster")
        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )

    def get_edge_cluster_by_nsxt_id(self, nsxt_id):
        """Retrieves the NSX Edge cluster information from SDDC Manager based on ID."""
        try:
            edge_clusters = self.api_client.get_edge_clusters().data["elements"]
            for edge_cluster in edge_clusters:
                if edge_cluster["nsxtCluster"]["id"] == nsxt_id:
                    return edge_cluster
        except VcfApiException as e:
            self.module.fail_json(
                changed=False, msg=f"Error getting NSX Edge clusters: {e}"
            )

    def transform_payload(self):
        """Transforms the upgrade payload based on the upgrade component."""
        upgrade_payload = {}
        if self.upgrade_component == "sddc_manager":
            bundle_id = self.target_versions_with_bundles["sddc_manager"][
                "software_install_bundleId"
            ]
            resource_type = "DOMAIN"
            resource_upgrade_specs = [
                {"resourceId": self.domain_info["id"], "upgradeNow": True}
            ]
            upgrade_payload.update(
                {
                    "bundleId": bundle_id,
                    "resourceType": resource_type,
                    "draftMode": False,
                    "resourceUpgradeSpecs": resource_upgrade_specs,
                }
            )
            return upgrade_payload
        elif self.upgrade_component == "vcenter":
            bundle_id = self.target_versions_with_bundles["vcenter"]["bundleId"]
            resource_type = "DOMAIN"
            resource_upgrade_specs = [
                {"resourceId": self.domain_info["id"], "upgradeNow": True}
            ]
            upgrade_payload.update(
                {
                    "bundleId": bundle_id,
                    "resourceType": resource_type,
                    "draftMode": False,
                    "resourceUpgradeSpecs": resource_upgrade_specs,
                }
            )
            for vcenter in self.domain_info["vcenters"]:
                vcenter_id = vcenter["id"]
                vcenter_upgrade_user_input_spec = {
                    "resourceId": vcenter_id,
                    "upgradeMechanism": "InPlace",
                }
                upgrade_payload["vcenterUpgradeUserInputSpecs"] = [
                    vcenter_upgrade_user_input_spec
                ]

            return upgrade_payload
        elif self.upgrade_component == "nsx":
            bundle_id = self.target_versions_with_bundles["nsx"]["bundleId"]
            resource_type = "DOMAIN"
            resource_upgrade_specs = [
                {"resourceId": self.domain_info["id"], "upgradeNow": True}
            ]
            nsxt_host_cluster_upgrade_specs = []
            for cluster in self.domain_info["clusters"]:
                cluster_id = cluster["id"]
                nsxt_host_cluster_upgrade_specs.append(
                    {"hostClusterId": cluster_id, "liveUpgrade": False}
                )
            nsxt_upgrade_user_input_spec = {
                "nsxtHostClusterUpgradeSpecs": (nsxt_host_cluster_upgrade_specs)
            }

            if self.upgraded_edge_cluster:
                upgrade_edge_with_host = {
                    "isEdgeClustersUpgradeParallel": False,
                    "isEdgeOnlyUpgrade": False,
                    "isHostClustersUpgradeParallel": False,
                }
                nsxt_upgrade_user_input_spec["nsxtUpgradeOptions"] = (
                    upgrade_edge_with_host
                )

            upgrade_payload.update(
                {
                    "bundleId": bundle_id,
                    "resourceType": resource_type,
                    "draftMode": False,
                    "resourceUpgradeSpecs": resource_upgrade_specs,
                    "nsxtUpgradeUserInputSpecs": [nsxt_upgrade_user_input_spec],
                }
            )
            return upgrade_payload

        elif self.upgrade_component == "host":
            domain_clusters = self.domain_info["clusters"]
            bundle_id = self.target_versions_with_bundles["host"]["bundleId"]
            resource_type = "CLUSTER"

            resource_upgrade_specs = []
            for cluster in domain_clusters:
                cluster_id = cluster["id"]
                resource_upgrade_specs.append(
                    {
                        "resourceId": cluster_id,
                        "upgradeNow": True,
                        "personalitySpec": {
                            "personalityId": self.target_versions_with_bundles["host"][
                                "host_image"
                            ]["personalityId"]
                        },
                        "esxUpgradeOptionsSpec": {
                            "enableQuickboot": True,
                            "evacuateOfflineVms": True,
                            "enableQuickPatch": False,
                        },
                    }
                )

            upgrade_payload.update(
                {
                    "bundleId": bundle_id,
                    "resourceType": resource_type,
                    "parallelUpgrade": True,
                    "draftMode": False,
                    "resourceUpgradeSpecs": resource_upgrade_specs,
                }
            )
            return upgrade_payload
        else:
            self.module.fail_json(changed=False, msg="Not a valid upgrade component.")
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
            target_versions_with_bundles=dict(required=True, type="dict"),
            upgrade_component=dict(
                required=True,
                type="str",
                choices=["sddc_manager", "vcenter", "nsx", "host"],
            ),
            domain_info=dict(required=True, type="dict"),
            nsxt_cluster_info=dict(required=False, type="dict"),
            upgraded_edge_cluster=dict(required=False, type=bool),
        )
    )

    try:
        payload_creator = CreateUpgradePayload(module)
        upgrade_payload = payload_creator.transform_payload()
        module.log(f"Upgrade Payload: {upgrade_payload}")
        module.exit_json(changed=False, meta=upgrade_payload)
    except VcfApiException as e:
        module.fail_json(
            changed=False, msg="Unexpected error occurred.", meta=f"Error: {e}"
        )


if __name__ == "__main__":
    main()
