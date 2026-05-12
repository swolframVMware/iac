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
module: sddc_manager_get_software_upgrade_bundles
short_description: Retrieves the software upgrade bundles from SDDC Manager.
description:
    - This module retrieves the software upgrade bundles from SDDC Manager for VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    upgrade_targets:
        description:
            - The upgrade targets for the VMware Cloud Foundation upgrade.
        required: true
        type: dict
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Get software upgrade bundles from SDDC Manager
  broadcom.vcf.sddc_manager_get_software_upgrade_bundles:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    upgrade_targets:
        sddc_manager: 9.0.0.0-12345678
        vcenter: 9.0.0.0-12345678
        nsx: 9.0.0.0-12345678
        host: 9.0.0.0-12345678
"""

RETURN = r"""
target_versions_with_bundles:
    description: Upgrade targets with their corresponding bundle IDs from SDDC Manager
    returned: on success
    type: dict
    sample:
        sddc_manager:
            version: "9.0.0.0-12345678"
            software_install_bundleId: "12345678-1234-1234-1234-123456789012"
            config_drift_bundleId: "12345678-1234-1234-1234-123456789012"
        vcenter:
            version: "9.0.0.0-12345678"
            bundleId: "12345678-1234-1234-1234-123456789012"
        nsx:
            version: "9.0.0.0-12345678"
            bundleId: "12345678-1234-1234-1234-123456789012"
        host:
            version: "9.0.0.0-12345678"
            bundleId: "12345678-1234-1234-1234-123456789012"
msg:
    description: Error message when bundle retrieval fails
    returned: on failure
    type: str
    sample: "Bundle with product type SDDC_MANAGER and version 9.0.0.0-12345678 not found."
changed:
    description: Whether the module made changes
    returned: always
    type: bool
    sample: true
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


class AddBundleToUpgradePayload:
    """This class is responsible for retrieving the software upgrade bundles from SDDC
    Manager.
    """

    def __init__(
        self,
        module,
        sddc_manager_hostname,
        sddc_manager_user,
        sddc_manager_password,
        upgrade_targets,
    ):
        self.module = module
        self.sddc_manager_hostname = sddc_manager_hostname
        self.sddc_manager_user = sddc_manager_user
        self.sddc_manager_password = sddc_manager_password
        self.upgrade_targets = upgrade_targets
        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )
        self.bundles = self.get_all_bundles()

    def get_all_bundles(self):
        """Retrieves all bundles from SDDC Manager."""
        try:
            return self.api_client.get_all_bundles().data["elements"]
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error retrieving bundles for upgrade: {e}")

    def get_bundle(self, product_type, version, description_keyword):
        """Retrieves a bundle based on the product type, version, and description
        keyword from SDDC Manager.
        """
        product_type_mapping = {
            "sddc_manager": "SDDC_MANAGER",
            "vcenter": "VCENTER",
            "nsx": "NSX_T_MANAGER",
            "host": "HOST",
        }
        if product_type not in product_type_mapping:
            self.module.fail_json(msg=f"Invalid product type: {product_type}")

        mapped_product_type = product_type_mapping[product_type]

        for bundle in self.bundles:
            for bundle_component in bundle["components"]:
                if (
                    bundle_component["type"] == mapped_product_type
                    and bundle_component["toVersion"] == version
                    and bundle["downloadStatus"] == "SUCCESSFUL"
                    and description_keyword in bundle["description"]
                ):
                    return bundle
        self.module.fail_json(
            msg=f"Bundle with product type {mapped_product_type} and version {version} not found."
        )
        return None

    def get_sddc_upgrade_bundle(self, version):
        """Retrieves the upgrade bundle from SDDC Manager."""
        return self.get_bundle(
            "sddc_manager",
            version,
            "The upgrade bundle for VMware Cloud Foundation",
        )

    def get_sddc_upgrade_drift_bundle(self, version):
        """Retrives the configuration drift bundle from SDDC Manager."""
        return self.get_bundle(
            "sddc_manager",
            version,
            "The configuration drift bundle for VMware Cloud Foundation",
        )

    def get_bundle_by_product_type(self, product_type, version):
        """Retrieves a bundle based on the product type and version from SDDC Manager."""
        if product_type == "sddc_manager":
            sddc_manager_bundle = self.get_sddc_upgrade_bundle(version)
            sddc_manager_config_drift_bundle = self.get_sddc_upgrade_drift_bundle(
                version
            )
            return sddc_manager_bundle, sddc_manager_config_drift_bundle
        else:
            return self.get_bundle(product_type, version, "")

    def process_targets_upgrade(self):
        """Processes the upgrade targets and returns the updated targets."""
        if not self.upgrade_targets:
            self.module.fail_json(msg="No upgrade targets provided.")

        updated_targets = {}
        for product_type, target in self.upgrade_targets.items():
            if isinstance(target, str):
                target = {"version": target}
            if product_type == "sddc_manager":
                if isinstance(target, dict) and "version" in target:
                    sddc_manager_bundle, sddc_manager_config_drift_bundle = (
                        self.get_bundle_by_product_type(
                            "sddc_manager", target["version"]
                        )
                    )
                    target["software_install_bundleId"] = sddc_manager_bundle["id"]
                    target["config_drift_bundleId"] = sddc_manager_config_drift_bundle[
                        "id"
                    ]
                else:
                    self.module.fail_json(
                        msg=f"Invalid target structure for sddc_manager {target}."
                    )
            else:
                if isinstance(target, dict) and "version" in target:
                    bundle = self.get_bundle_by_product_type(
                        product_type, target["version"]
                    )
                    target["bundleId"] = bundle["id"]
                else:
                    self.module.fail_json(
                        msg=f"Invalid target structure for {product_type}."
                    )
            updated_targets[product_type] = target
        return updated_targets


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    module_args = dict(
        sddc_manager_hostname=dict(type="str", required=True),
        sddc_manager_user=dict(type="str", required=True),
        sddc_manager_password=dict(type="str", required=True, no_log=True),
        upgrade_targets=dict(type="dict", required=True),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    sddc_manager_hostname = module.params["sddc_manager_hostname"]
    sddc_manager_user = module.params["sddc_manager_user"]
    sddc_manager_password = module.params["sddc_manager_password"]
    upgrade_targets = module.params["upgrade_targets"]

    try:
        upgrade_payload_class = AddBundleToUpgradePayload(
            module,
            sddc_manager_hostname,
            sddc_manager_user,
            sddc_manager_password,
            upgrade_targets,
        )
        result = upgrade_payload_class.process_targets_upgrade()
        module.exit_json(changed=True, target_versions_with_bundles=result)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
