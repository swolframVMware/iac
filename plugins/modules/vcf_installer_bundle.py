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
module: vcf_installer_bundle
short_description: Manage bundle downloads and operations in VCF Installer.
description:
    - This module manages bundle downloads and operations in VCF Installer for VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.vcf_installer
options:
    state:
        description:
            - The desired state of the bundle.
            - C(present) will download the bundle immediately.
            - C(stopped) will stop an ongoing bundle download.
            - C(absent) will delete the bundle.
        required: true
        type: str
        choices: ['present', 'stopped', 'absent']
    bundle_id:
        description:
            - The ID of the bundle to manage.
        required: true
        type: str
    binary_files_only:
        description:
            - If true, only binary files from storage will be deleted.
            - Only applicable when state is C(absent).
        required: false
        type: bool
        default: false
    wait_for_completion:
        description:
            - Whether to wait for the download task to complete.
            - Only applicable when state is C(present) or C(stopped).
        required: false
        type: bool
        default: false
    timeout:
        description:
            - Maximum time in seconds to wait for task completion.
            - Only applicable when wait_for_completion is true.
        required: false
        type: int
        default: 3600
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Download Bundle
  broadcom.vcf.vcf_installer_bundle:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    state: present
    bundle_id: "e6ba8240-d9b7-11ef-bf62-63832c57ab1a"
  register: download_result

- name: Download Bundle and Wait for Completion
  broadcom.vcf.vcf_installer_bundle:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    state: present
    bundle_id: "e6ba8240-d9b7-11ef-bf62-63832c57ab1a"
    wait_for_completion: true
    timeout: 7200
  register: download_result

- name: Stop Bundle Download
  broadcom.vcf.vcf_installer_bundle:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    state: stopped
    bundle_id: "e6ba8240-d9b7-11ef-bf62-63832c57ab1a"
  register: stop_result

- name: Delete Bundle
  broadcom.vcf.vcf_installer_bundle:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    state: absent
    bundle_id: "e6ba8240-d9b7-11ef-bf62-63832c57ab1a"
  register: delete_result

- name: Delete Bundle Binary Files Only
  broadcom.vcf.vcf_installer_bundle:
    vcf_installer_hostname: vcf-installer.example.com
    vcf_installer_user: admin
    vcf_installer_password: password
    state: absent
    bundle_id: "e6ba8240-d9b7-11ef-bf62-63832c57ab1a"
    binary_files_only: true
  register: delete_result
"""

RETURN = r"""
changed:
    description: Whether the module made changes.
    returned: always
    type: bool
    sample: true
msg:
    description: A status message about the operation.
    returned: always
    type: str
    sample: "Bundle download initiated successfully."
    alternatives:
        - "Bundle download scheduled for 2026-03-01T02:00:00Z."
        - "Bundle download cancelled."
        - "Bundle deleted successfully."
        - "Bundle download completed successfully."
        - "Bundle download task is still running."
task:
    description: The task information for the operation.
    returned: when state is 'downloaded' or 'cancelled'
    type: dict
    sample:
        id: "task-123"
        status: "IN_PROGRESS"
        name: "Download Bundle"
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


class VcfInstallerBundle:
    """This class handles bundle management in VCF Installer.

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
        state (str): The desired bundle state (present, stopped, or absent).
        bundle_id (str): The bundle identifier to operate on.
        api_client (VcfInstallerApiClient): API client used for VCF Installer requests.

    Methods:
        download_bundle(self): Downloads or schedules a bundle download.
        cancel_bundle_download(self): Cancels an ongoing bundle download.
        delete_bundle(self): Deletes a bundle.
        wait_for_bundle_download_status(self): Polls until bundle download reaches a
            terminal status.
        run(self): Runs the bundle management process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.vcf_installer_hostname = module.params["vcf_installer_hostname"]
        self.vcf_installer_user = module.params["vcf_installer_user"]
        self.vcf_installer_password = module.params["vcf_installer_password"]
        self.state = module.params["state"]
        self.bundle_id = module.params["bundle_id"]
        self.api_client = VcfInstallerApiClient(
            self.vcf_installer_hostname,
            self.vcf_installer_user,
            self.vcf_installer_password,
        )

    def download_bundle(self):
        """Downloads a bundle in VCF Installer."""
        try:
            wait_for_completion = self.module.params.get("wait_for_completion", False)

            status_response = self.api_client.get_bundle_download_status(
                bundle_id=self.bundle_id,
                image_type="INSTALL",
            )
            elements = status_response.get("elements", [])
            current = elements[0] if elements else {}
            current_status = current.get("downloadStatus", "")
            is_downloadable = current.get("isDownloadable", True)

            if current_status in ("SUCCESSFUL", "SUCCESS"):
                self.module.exit_json(
                    changed=False,
                    msg="Bundle already downloaded successfully.",
                )

            if current_status in ("IN_PROGRESS", "SCHEDULED", "VALIDATING"):
                self.module.exit_json(
                    changed=False,
                    msg=f"Bundle download already active with status: {current_status}.",
                )

            if not is_downloadable:
                self.module.exit_json(
                    changed=False,
                    msg=f"Bundle is not downloadable (isDownloadable=false, status={current_status}).",
                )

            # If we reach here, it means we should trigger the download.
            body = {"downloadNow": True}

            # Intiate the download.
            api_response = self.api_client.download_bundle(
                self.bundle_id, json.dumps(body)
            )

            msg = "Bundle download initiated successfully."

            if wait_for_completion:
                final_status = self.wait_for_bundle_download_status()
                task_status = final_status.get("status", "UNKNOWN")

                if task_status in ["SUCCESSFUL", "SUCCESS"]:
                    msg = "Bundle download completed successfully."
                elif task_status in ["FAILED", "CANCELLED"]:
                    self.module.fail_json(
                        msg=f"Bundle download failed with status: {task_status}",
                        task=final_status,
                    )
                else:
                    msg = f"Bundle download task ended with status: {task_status}."

                self.module.exit_json(changed=True, msg=msg, task=final_status)
            else:
                self.module.exit_json(changed=True, msg=msg, task=api_response)


        except VcfApiException as e:
            if "400" in str(e):
                self.module.warn(
                    f"Bundle {self.bundle_id}: download trigger returned 400 — {e}"

                )
                self.module.exit_json(
                    changed=False,
                    msg=f"Bundle {self.bundle_id} could not be triggered (400): {e}",
                    skipped_reason=str(e),
                )
            self.module.fail_json(msg=f"Error downloading bundle: {e}")

    def cancel_bundle_download(self):
        """Cancels an ongoing bundle download in VCF Installer."""
        try:
            status_response = self.api_client.get_bundle_download_status(
                bundle_id=self.bundle_id,
                image_type="INSTALL",
            )
            elements = status_response.get("elements", [])
            current = elements[0] if elements else {}
            current_status = current.get("downloadStatus", "")
            download_id = current.get("downloadId")
            is_cancellable = current.get("isDownloadCancellable", False)

            if not download_id:
                self.module.exit_json(
                    changed=False,
                    msg=(
                        f"Bundle {self.bundle_id} has no downloadId in status "
                        f"(status={current_status}); nothing to cancel."
                    ),
                )

            if not is_cancellable:
                self.module.exit_json(
                    changed=False,
                    msg=(
                        f"Bundle {self.bundle_id} is not cancellable "
                        f"(status={current_status})."
                    ),
                )

            api_response = self.api_client.cancel_task_by_id(download_id)
            msg = "Bundle download cancelled."
            self.module.exit_json(
                changed=True,
                msg=msg,
                task={
                    "id": download_id,
                    "bundleId": self.bundle_id,
                    "status": "CANCEL_REQUESTED",
                    "response": api_response,
                },
            )

        except VcfApiException as e:
            if "400" in str(e):
                self.module.warn(
                    f"Bundle {self.bundle_id}: cancel trigger returned 400 - {e}"
                )
                self.module.exit_json(
                    changed=False,
                    msg=f"Bundle {self.bundle_id} could not be cancelled (400): {e}",
                    skipped_reason=str(e),
                )
            if "500" in str(e):
                self.module.warn(
                    f"Bundle {self.bundle_id}: cancel trigger returned 500 - {e}"
                )
                self.module.exit_json(
                    changed=False,
                    msg=f"Bundle {self.bundle_id} could not be cancelled (500): {e}",
                    skipped_reason=str(e),
                )
            self.module.fail_json(msg=f"Error cancelling bundle download: {e}")

    def delete_bundle(self):
        """Deletes a bundle from VCF Installer."""
        try:
            binary_files_only = self.module.params.get("binary_files_only", False)

            api_response = self.api_client.delete_bundle(
                self.bundle_id, binary_files_only=binary_files_only
            )

            if binary_files_only:
                msg = "Bundle binary files deleted successfully."
            else:
                msg = "Bundle deleted successfully."

            self.module.exit_json(changed=True, msg=msg)

        except VcfApiException as e:
            self.module.fail_json(msg=f"Error deleting bundle: {e}")

    def wait_for_bundle_download_status(self):
        """Waits for bundle download status to reach a terminal state.

        Returns:
            dict: Final status details for the bundle.
        """
        timeout = self.module.params.get("timeout", 3600)
        start_time = time.time()
        poll_interval = 10  # seconds

        while True:
            if time.time() - start_time > timeout:
                self.module.fail_json(
                    msg=(
                        f"Timeout waiting for bundle {self.bundle_id} download "
                        f"to complete after {timeout} seconds"
                    )
                )

            try:
                status_response = self.api_client.get_bundle_download_status(
                    bundle_id=self.bundle_id,
                    image_type="INSTALL",
                )
                elements = status_response.get("elements", [])
                current = elements[0] if elements else {}
                status = current.get("downloadStatus", "UNKNOWN")

                if status in ["SUCCESSFUL", "SUCCESS", "FAILED", "CANCELLED"]:
                    return {
                        "id": current.get("downloadId"),
                        "bundleId": self.bundle_id,
                        "status": status,
                        "details": current,
                    }

                time.sleep(poll_interval)

            except VcfApiException as e:
                self.module.fail_json(
                    msg=(
                        f"Error checking bundle download status for "
                        f"{self.bundle_id}: {e}"
                    )
                )

    def run(self):
        """Runs the bundle management process."""
        if self.state == "present":
            self.download_bundle()
        elif self.state == "stopped":
            self.cancel_bundle_download()
        elif self.state == "absent":
            self.delete_bundle()
        else:
            self.module.fail_json(msg=f"Unsupported state: {self.state}")


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = dict(
        vcf_installer_hostname=dict(required=True, type="str"),
        vcf_installer_user=dict(required=True, type="str"),
        vcf_installer_password=dict(required=True, type="str", no_log=True),
        state=dict(required=True, type="str", choices=["present", "stopped", "absent"]),
        bundle_id=dict(required=True, type="str"),
        binary_files_only=dict(required=False, type="bool", default=False),
        wait_for_completion=dict(required=False, type="bool", default=False),
        timeout=dict(required=False, type="int", default=3600),
    )

    module = AnsibleModule(argument_spec=parameters, supports_check_mode=False)

    bundle = VcfInstallerBundle(module)
    bundle.run()


if __name__ == "__main__":
    main()
