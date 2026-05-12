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
module: vcf_installer_bundle_sync
short_description: Trigger and monitor INSTALL bundle downloads for VCF releases
description:
    - Downloads installation bundles for one or more specified release versions.
    - Skips bundles that are already downloaded, actively in progress, or not downloadable.
    - Polls download status and retries failures until all bundles reach a
      terminal state or the timeout is exceeded.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.vcf_installer
options:
    releases:
        description:
            - List of release configurations to synchronize bundles for.
        required: true
        type: list
        elements: dict
        suboptions:
            release_version:
                description: The release version to download bundles for (e.g., "9.0.2.0").
                required: true
                type: str
            download_all:
                description: Download all components. When false, only C(components) are downloaded.
                required: false
                type: bool
                default: true
            components:
                description:
                    - List of component types to download when C(download_all) is false.
                    - Accepts friendly names or API names.
                    - Friendly names include: C(vcenter), C(nsx), C(sddc-manager), C(vcf-automation), C(vcf-operations), C(vcf-operations-collector), C(vcf-operations-fleet).
                    - API names include: C(VCENTER), C(NSX_T_MANAGER), C(SDDC_MANAGER), C(VCF_AUTOMATION), C(VCF_OPERATIONS), C(VCF_OPERATIONS_COLLECTOR), C(VCF_OPERATIONS_FLEET).
                required: false
                type: list
                elements: str
                default: []
    poll_interval:
        description: Seconds to wait between status polls.
        required: false
        type: int
        default: 60
    retries:
        description: Number of times to retry bundles that transition to FAILED.
        required: false
        type: int
        default: 3
    timeout:
        description: Total seconds to wait before giving up on in-progress downloads.
        required: false
        type: int
        default: 7200
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Download all bundles for a specific release version.
  broadcom.vcf.vcf_installer_bundle_sync:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    releases:
      - release_version: "9.0.2.0"
        download_all: true
  register: sync_result

- name: Download specific components for a specific release version, with custom polling and retries.
  broadcom.vcf.vcf_installer_bundle_sync:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    releases:
      - release_version: "9.0.0.0"
        download_all: false
        components:
          - vcenter
          - nsx
          - sddc-manager
    poll_interval: 30
    retries: 5
    timeout: 14400
  register: sync_result
"""

RETURN = r"""
changed:
    description: Whether any bundle downloads were initiated this run.
    returned: always
    type: bool
summary:
    description: Final download status counts across all releases.
    returned: always
    type: dict
    sample:
        successful: 6
        in_progress: 0
        pending: 0
        failed: 0
        skipped: 1
        total: 7
initiated:
    description: Bundle IDs where a download was triggered this run.
    returned: always
    type: list
skipped:
    description: Bundle IDs skipped (already done, active, or not downloadable).
    returned: always
    type: list
failed:
    description: Bundle IDs that are still FAILED after all retries exhausted.
    returned: always
    type: list
msg:
    description: Human-readable result summary.
    returned: always
    type: str
"""

import json
import time

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.vcf_installer import (
    VcfInstallerApiClient,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.bundle_types import (
    PRODUCT_TYPE_FRIENDLY_TO_API,
    VALID_API_PRODUCT_TYPES,
)

ACTIVE_STATUSES = {"PENDING", "IN_PROGRESS", "SCHEDULED", "VALIDATING"}
DONE_STATUSES = {"SUCCESSFUL", "SUCCESS"}


def normalize_component(name):
    """Convert friendly component name to API format."""
    if name in VALID_API_PRODUCT_TYPES:
        return name
    return PRODUCT_TYPE_FRIENDLY_TO_API.get(name, name)


class VcfInstallerBundleSync:
    """This class manages INSTALL bundle download synchronization in VCF Installer.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        api_client (VcfInstallerApiClient): API client used for VCF Installer requests.
        releases (list[dict]): Release configurations used to select bundles.
        poll_interval (int): Seconds to wait between status polls.
        retries (int): Number of retry attempts for FAILED bundles.
        timeout (int): Maximum total wait time in seconds.
        initiated (list[str]): Bundle IDs whose downloads were initiated in this run.
        skipped (list[str]): Bundle IDs skipped due to state or API response.

    Methods:
        get_status_for_releases(self): Retrieves and optionally filters bundle
            download status elements.
        trigger_download(self, bundle_id): Starts download for one bundle when
            eligible.
        run(self): Executes trigger, poll, retry, and final reporting workflow.

    Raises:
        VcfApiException: If an unexpected API error occurs.
    """

    def __init__(self, module):
        self.module = module
        self.api_client = VcfInstallerApiClient(
            module.params["vcf_installer_hostname"],
            module.params["vcf_installer_user"],
            module.params["vcf_installer_password"],
        )
        self.releases = module.params["releases"]
        self.poll_interval = module.params["poll_interval"]
        self.retries = module.params["retries"]
        self.timeout = module.params["timeout"]
        self.initiated = []
        self.skipped = []

    def get_status_for_releases(self):
        """Fetch and filter download status elements across all configured releases."""
        elements = []
        for release in self.releases:
            response = self.api_client.get_bundle_download_status(
                release_version=release["release_version"],
                image_type="INSTALL",
            )
            release_elements = response.get("elements", [])

            # If download_all is false, filter to specified components. Otherwise include all.
            if not release.get("download_all", True):
                components = [
                    normalize_component(c) for c in release.get("components", [])
                ]
                if components:
                    release_elements = [
                        e
                        for e in release_elements
                        if e.get("componentType") in components
                    ]

            elements.extend(release_elements)
        return elements

    def trigger_download(self, bundle_id):
        """Attempt to trigger a download for a single bundle.

        Returns True if initiated, False if skipped.
        Raises VcfApiException for unexpected errors.
        """
        try:
            response = self.api_client.get_bundle_download_status(
                bundle_id=bundle_id,
                image_type="INSTALL",
            )
            elements = response.get("elements", [])
            current = elements[0] if elements else {}
            status = current.get("downloadStatus", "")
            is_downloadable = current.get("isDownloadable", True)

            # Terminal successful states.
            if status in DONE_STATUSES:
                self.skipped.append(bundle_id)
                return False

            # Active states; assume actively downloading or queued bundles are already being handled.
            if status in ACTIVE_STATUSES:
                self.skipped.append(bundle_id)
                return False

            # If not downloadable, skip.
            if not is_downloadable:
                self.skipped.append(bundle_id)
                return False

            self.api_client.download_bundle(
                bundle_id, json.dumps({"downloadNow": True})
            )
            self.initiated.append(bundle_id)
            return True

        except VcfApiException as e:
            # If the bundle is not found or not downloadable, skip it. Otherwise, raise the error.
            if "400" in str(e):
                self.skipped.append(bundle_id)
                return False
            raise

    def run(self):
        start_time = time.time()

        # -------------------------------------------------------------------
        # Step 1: Get current status and trigger anything that needs it.
        # -------------------------------------------------------------------
        all_elements = self.get_status_for_releases()

        for element in all_elements:
            status = element.get("downloadStatus", "")
            # Trigger anything not already successful or actively running.
            if status not in DONE_STATUSES and status not in ACTIVE_STATUSES:
                bundle_id = element["bundleId"]
                try:
                    self.trigger_download(bundle_id)
                except VcfApiException as e:
                    self.module.warn(f"Failed to trigger bundle {bundle_id}: {e}")

        # -------------------------------------------------------------------
        # Step 2: Poll status until all are done or timeout is reached,
        #         retrying failures as needed.
        # -------------------------------------------------------------------
        retry_count = 0

        while True:
            elapsed = time.time() - start_time
            if elapsed >= self.timeout:
                self.module.warn(
                    f"Timeout of {self.timeout}s reached. "
                    f"Some downloads may still be in progress."
                )
                break

            time.sleep(self.poll_interval)

            current_elements = self.get_status_for_releases()
            active = [
                e
                for e in current_elements
                if e.get("downloadStatus") in ACTIVE_STATUSES
            ]
            failed = [
                e for e in current_elements if e.get("downloadStatus") == "FAILED"
            ]

            # All bundles are in a terminal state.
            if not active and not failed:
                break

            # Retry explicitly failed bundles up to retries limit.
            if failed and retry_count < self.retries:
                retry_count += 1
                for element in failed:
                    bundle_id = element["bundleId"]
                    try:
                        self.trigger_download(bundle_id)
                    except VcfApiException as e:
                        self.module.warn(
                            f"Retry {retry_count} failed for bundle {bundle_id}: {e}"
                        )

            # If no active downloads and retries exhausted.
            elif not active:
                break

        # -------------------------------------------------------------------
        # Step 3: Compile final status and return results.
        # -------------------------------------------------------------------
        final_elements = self.get_status_for_releases()

        summary = {
            "successful": len(
                [e for e in final_elements if e.get("downloadStatus") == "SUCCESSFUL"]
            ),
            "in_progress": len(
                [
                    e
                    for e in final_elements
                    if e.get("downloadStatus") in ACTIVE_STATUSES
                ]
            ),
            "pending": len(
                [e for e in final_elements if e.get("downloadStatus") == "PENDING"]
            ),
            "failed": len(
                [e for e in final_elements if e.get("downloadStatus") == "FAILED"]
            ),
            "skipped": len(self.skipped),
            "total": len(final_elements),
        }

        failed_ids = [
            e["bundleId"] for e in final_elements if e.get("downloadStatus") == "FAILED"
        ]
        changed = len(self.initiated) > 0

        msg = (
            f"Bundle sync complete. "
            f"Initiated: {len(self.initiated)}, "
            f"Successful: {summary['successful']}, "
            f"In Progress: {summary['in_progress']}, "
            f"Pending: {summary['pending']}, "
            f"Failed: {summary['failed']}, "
            f"Skipped: {summary['skipped']}."
        )

        if failed_ids:
            self.module.fail_json(
                msg=msg,
                changed=changed,
                summary=summary,
                initiated=self.initiated,
                skipped=self.skipped,
                failed=failed_ids,
            )

        self.module.exit_json(
            msg=msg,
            changed=changed,
            summary=summary,
            initiated=self.initiated,
            skipped=self.skipped,
            failed=failed_ids,
        )


def main():
    parameters = dict(
        vcf_installer_hostname=dict(required=True, type="str"),
        vcf_installer_user=dict(required=True, type="str"),
        vcf_installer_password=dict(required=True, type="str", no_log=True),
        releases=dict(
            required=True,
            type="list",
            elements="dict",
            options=dict(
                release_version=dict(required=True, type="str"),
                download_all=dict(required=False, type="bool", default=True),
                components=dict(
                    required=False, type="list", elements="str", default=[]
                ),
            ),
        ),
        poll_interval=dict(required=False, type="int", default=60),
        retries=dict(required=False, type="int", default=3),
        timeout=dict(required=False, type="int", default=7200),
    )

    module = AnsibleModule(argument_spec=parameters, supports_check_mode=False)

    bundle_sync = VcfInstallerBundleSync(module)
    bundle_sync.run()


if __name__ == "__main__":
    main()
