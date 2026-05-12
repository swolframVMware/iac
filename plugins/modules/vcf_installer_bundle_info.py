# -*- coding: utf-8 -*-
#
# Copyright (c) Broadcom. All Rights Reserved.
# The term "Broadcom" refers solely to the Broadcom Inc. corporate affiliate that
# distributes this software.
#
# You are hereby granted a non-exclusive, worldwide, royalty-free license under
# Broadcom's copyrights to use, copy, modify, and distribute this software in source
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

__metaclass__ = type

DOCUMENTATION = r"""
---
module: vcf_installer_bundle_info
short_description: Retrieve bundle information from VCF Installer
description:
    - This module retrieves bundle information from VCF Installer for VMware Cloud Foundation.
version_added: "1.0.0"
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.vcf_installer
options:
    operation:
        description:
            - The type of bundle information to retrieve.
            - C(list) retrieves all bundles with optional filtering.
            - C(get_by_id) retrieves a specific bundle by its ID.
            - C(download_status) retrieves download status for bundles.
        required: true
        type: str
        choices: ['list', 'get_by_id', 'download_status']
    bundle_id:
        description:
            - The ID of the bundle to retrieve.
            - Required when operation is C(get_by_id).
            - Optional when operation is C(download_status) to filter by bundle ID.
        required: false
        type: str
    product_type:
        description:
            - Filter bundles by product type.
            - Only applicable when operation is C(list).
            - Supports both user-friendly names and API internal names.
            - "User-friendly names: vcenter, nsx, sddc-manager, vcf-automation, vcf-operations, vcf-operations-collector, vcf-operations-fleet"
            - "API names: VCENTER, NSX_T_MANAGER, SDDC_MANAGER, VRA, VROPS, VCF_OPS_CLOUD_PROXY, VRSLCM"
        required: false
        type: str
    is_compliant:
        description:
            - Filter bundles by compliance with the current VCF version.
            - Only applicable when operation is C(list).
        required: false
        type: bool
    bundle_type:
        description:
            - Filter bundles by bundle type.
            - Only applicable when operation is C(list).
            - Supports both user-friendly names and API internal names.
            - "User-friendly names: sddc-manager, vmware-software, vxrail"
            - "API names: SDDC_MANAGER, VMWARE_SOFTWARE, VXRAIL"
        required: false
        type: str
    release_version:
        description:
            - Filter by release version (e.g., "9.0.2.0").
            - Only applicable when operation is C(download_status).
        required: false
        type: str
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Get All Bundles
  broadcom.vcf.vcf_installer_bundle_info:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    operation: list
  register: all_bundles

- name: Get All INSTALL Bundles with Download Status
  broadcom.vcf.vcf_installer_bundle_info:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    operation: download_status
    image_type: INSTALL
  register: install_bundles

- name: Get Bundles for Specific Product Type
  broadcom.vcf.vcf_installer_bundle_info:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    operation: list
    product_type: VCENTER
  register: vcenter_bundles

- name: Get Compliant Bundles Only
  broadcom.vcf.vcf_installer_bundle_info:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    operation: list
    is_compliant: true
  register: compliant_bundles

- name: Get Specific Bundle by ID
  broadcom.vcf.vcf_installer_bundle_info:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    operation: get_by_id
    bundle_id: "e6ba8240-d9b7-11ef-bf62-63832c57ab1a"
  register: bundle_details

- name: Get Download Status for Specific Release
  broadcom.vcf.vcf_installer_bundle_info:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    operation: download_status
    release_version: "9.0.0.0"
  register: release_bundles

- name: Get Download Status for Specific Bundle
  broadcom.vcf.vcf_installer_bundle_info:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    operation: download_status
    bundle_id: "e6ba8240-d9b7-11ef-bf62-63832c57ab1a"
  register: bundle_status
"""

RETURN = r"""
bundles:
    description: The bundle information (list or single bundle).
    returned: when operation is 'list' or 'get_by_id'
    type: dict
    sample:
        elements:
            - id: "e6ba8240-d9b7-11ef-bf62-63832c57ab1a"
              type: "VMWARE_SOFTWARE"
              description: "VMware vCenter Server 8.0.2"
              version: "8.0.2.00000-21216066"
              downloadStatus: "SUCCESSFUL"
              isCompliant: true
              sizeMB: 9876.5
              components:
                - name: "VMware vCenter Server"
                  type: "VCENTER"
download_status:
    description: Bundle download status information.
    returned: when operation is 'download_status'
    type: dict
    sample:
        elements:
            - bundleId: "e6ba8240-d9b7-11ef-bf62-63832c57ab1a"
              downloadStatus: "SUCCESSFUL"
              downloadId: "task-123"
              downloadedSize: 10355998720
              isDownloadCancellable: false
changed:
    description: Whether the module made changes (always false for info modules).
    returned: always
    type: bool
    sample: false
msg:
    description: A status message about the operation.
    returned: always
    type: str
    sample: "Retrieved 25 bundles."
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.vcf_installer import (
    VcfInstallerApiClient,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.bundle_types import (
    PRODUCT_TYPE_CHOICES,
    BUNDLE_TYPE_CHOICES,
    normalize_product_type,
    normalize_bundle_type,
)


class VcfInstallerBundleInfo:
    """This class handles bundle information retrieval in VCF Installer.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        vcf_installer_hostname (str): The hostname or IP address of the VCF Installer
            instance.
        vcf_installer_user (str): The username for authenticating with the VCF
            installer instance.
        vcf_installer_password (str): The password for authenticating with the VCF
            installer instance.
        operation (str): The requested info operation (list, get_by_id,
            or download_status).
        api_client (VcfInstallerApiClient): API client used for VCF Installer requests.

    Methods:
        list_bundles(self): Retrieves all bundles with optional filters.
        get_bundle_by_id(self): Retrieves a specific bundle by ID.
        get_download_status(self): Retrieves bundle download status with optional
            release and bundle filters.
        run(self): Runs the bundle information retrieval process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.vcf_installer_hostname = module.params["vcf_installer_hostname"]
        self.vcf_installer_user = module.params["vcf_installer_user"]
        self.vcf_installer_password = module.params["vcf_installer_password"]
        self.operation = module.params["operation"]
        self.api_client = VcfInstallerApiClient(
            self.vcf_installer_hostname,
            self.vcf_installer_user,
            self.vcf_installer_password,
        )

    def list_bundles(self):
        """Retrieves all bundles with optional filters from VCF Installer."""
        try:
            product_type = self.module.params.get("product_type")
            is_compliant = self.module.params.get("is_compliant")
            bundle_type = self.module.params.get("bundle_type")

            # Normalize product_type from friendly name to API name
            if product_type:
                try:
                    product_type = normalize_product_type(product_type)
                except ValueError as e:
                    self.module.fail_json(msg=str(e))

            # Normalize bundle_type from friendly name to API name
            if bundle_type:
                try:
                    bundle_type = normalize_bundle_type(bundle_type)
                except ValueError as e:
                    self.module.fail_json(msg=str(e))

            api_response = self.api_client.get_bundles(
                product_type=product_type,
                is_compliant=is_compliant,
                bundle_type=bundle_type,
            )

            bundle_count = len(api_response.get("elements", []))
            filters = []
            if product_type:
                filters.append(f"product_type={product_type}")
            if is_compliant is not None:
                filters.append(f"is_compliant={is_compliant}")
            if bundle_type:
                filters.append(f"bundle_type={bundle_type}")

            filter_msg = f" with filters: {', '.join(filters)}" if filters else ""
            msg = f"Retrieved {bundle_count} bundle(s){filter_msg}."

            self.module.exit_json(changed=False, bundles=api_response, msg=msg)

        except VcfApiException as e:
            self.module.fail_json(msg=f"Error retrieving bundles: {e}")

    def get_bundle_by_id(self):
        """Retrieves a specific bundle by ID from VCF Installer."""
        bundle_id = self.module.params.get("bundle_id")

        if not bundle_id:
            self.module.fail_json(
                msg="bundle_id is required when operation is 'get_by_id'"
            )

        try:
            api_response = self.api_client.get_bundle_by_id(bundle_id)
            msg = f"Retrieved bundle: {bundle_id}"

            self.module.exit_json(changed=False, bundles=api_response, msg=msg)

        except VcfApiException as e:
            self.module.fail_json(msg=f"Error retrieving bundle {bundle_id}: {e}")

    def get_download_status(self):
        """Retrieves bundle download status from VCF Installer."""
        try:
            bundle_id = self.module.params.get("bundle_id")
            release_version = self.module.params.get("release_version")
            # VCF Installer only supports INSTALL bundles (not PATCH)
            image_type = "INSTALL"

            api_response = self.api_client.get_bundle_download_status(
                release_version=release_version,
                bundle_id=bundle_id,
                image_type=image_type,
            )

            status_count = len(api_response.get("elements", []))
            filters = []
            if release_version:
                filters.append(f"release_version={release_version}")
            if bundle_id:
                filters.append(f"bundle_id={bundle_id}")
            if image_type:
                filters.append(f"image_type={image_type}")

            filter_msg = f" with filters: {', '.join(filters)}" if filters else ""
            msg = f"Retrieved download status for {status_count} bundle(s){filter_msg}."

            self.module.exit_json(changed=False, download_status=api_response, msg=msg)

        except VcfApiException as e:
            self.module.fail_json(msg=f"Error retrieving bundle download status: {e}")

    def run(self):
        """Runs the bundle information retrieval process."""
        if self.operation == "list":
            self.list_bundles()
        elif self.operation == "get_by_id":
            self.get_bundle_by_id()
        elif self.operation == "download_status":
            self.get_download_status()
        else:
            self.module.fail_json(msg=f"Unsupported operation: {self.operation}")


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = dict(
        vcf_installer_hostname=dict(required=True, type="str"),
        vcf_installer_user=dict(required=True, type="str"),
        vcf_installer_password=dict(required=True, type="str", no_log=True),
        operation=dict(
            required=True, type="str", choices=["list", "get_by_id", "download_status"]
        ),
        bundle_id=dict(required=False, type="str"),
        product_type=dict(
            required=False,
            type="str",
            choices=PRODUCT_TYPE_CHOICES,  # Accepts both friendly and API names
        ),
        is_compliant=dict(required=False, type="bool"),
        bundle_type=dict(
            required=False,
            type="str",
            choices=BUNDLE_TYPE_CHOICES,  # Accepts both friendly and API names
        ),
        release_version=dict(required=False, type="str"),
    )

    module = AnsibleModule(argument_spec=parameters, supports_check_mode=True)

    bundle_info = VcfInstallerBundleInfo(module)
    bundle_info.run()


if __name__ == "__main__":
    main()
