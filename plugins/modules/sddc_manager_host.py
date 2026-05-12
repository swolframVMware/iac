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
module: sddc_manager_host
short_description: Manages ESX hosts in SDDC Manager.
description:
    - This module manages ESX hosts in SDDC Manager for VMware Cloud Foundation.
    - It provides functionality to commission and decommission ESX hosts.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    hosts_payload:
        description:
            - The list of hosts (including network pool, username, password, storage
              type) to be commissioned or decommissioned.
        required: true
        type: list
        elements: dict
    validate:
        description:
            - Whether to validate the hosts before commissioning or decommissioning.
        required: false
        type: bool
        default: false
    state:
        description:
            - The state of the hosts.
        required: true
        type: str
        choices:
            - present
            - absent
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Validate hosts for commissioning
  broadcom.vcf.sddc_manager_host:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: commission
    validate: true
    hosts_payload:
      HostCommissionSpec:
        - fqdn: esx-01a.example.com
          username: root
          password: password
          networkPoolId: 12345678-1234-1234-1234-123456789012
          storageType: VSAN
- name: Commission hosts
  broadcom.vcf.sddc_manager_host:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: present
    validate: false
    hosts_payload:
      HostCommissionSpec:
        - fqdn: esx-01a.example.com
          username: root
          password: password
          networkPoolId: 12345678-1234-1234-1234-123456789012
          storageType: VSAN
- name: Decommission hosts
  broadcom.vcf.sddc_manager_host:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    state: absent
    validate: false
    hosts_payload:
      HostCommissionSpec:
        - fqdn: esx-01a.example.com
"""

RETURN = r"""
msg:
    description: Error message when operation fails
    returned: on failure
    type: str
    sample: >
        Error: ESX host esx-01a.example.com in payload is not valid for decommission.
meta:
    description: The response from the ESX host commission or decommission operation
    returned: on success
    type: dict
changed:
    description: Whether the module made changes
    returned: always
    type: bool
    sample: true
"""

import json

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)
from ansible_collections.broadcom.vcf.plugins.module_utils.sddc_manager import (
    SddcManagerApiClient,
)


class SddcManagerHosts:
    """This class represents the ESX hosts in SDDC Manager.

    Args:
        module: The Ansible module object.

    Attributes:
        module (object): The Ansible module object.
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager
            instance.
        sddc_manager_user (str): The username for authenticating with the SDDC Manager.
        sddc_manager_password (str): The password for authenticating with the SDDC
            Manager.
        hosts_payload (list): The list of ESX hosts (including network pool, username,
            password, storage type) to be commissioned or decommissioned.
        api_client (object): An instance of the SddcManagerApiClient class.

    Methods:
        get_hosts_by_name_valid_for_commission(self): Retrieves the list of ESX hosts
            that are valid for commissioning.
        get_hosts_by_name_valid_for_decommission(self): Retrieves the list of ESX hosts
            that are valid for decommissioning.
        check_hosts_in_payload_are_valid_for_decommission(self): Checks if the ESX hosts
            in the payload are valid for decommissioning.
        host_commission_validate_hosts(self): Validates the ESX hosts for commissioning.
        host_commission_commission_hosts(self): Commissions the ESX hosts.
        host_commission_decommission_hosts(self): Decommissions the ESX hosts.
        run(self): Runs the ESX host commissioning/decomissioning process.

    Raises:
        VcfApiException: If an error occurs during the API call.
    """

    def __init__(self, module):
        self.module = module
        self.sddc_manager_hostname = module.params["sddc_manager_hostname"]
        self.sddc_manager_user = module.params["sddc_manager_user"]
        self.sddc_manager_password = module.params["sddc_manager_password"]
        self.hosts_payload = module.params["hosts_payload"]
        self.api_client = SddcManagerApiClient(
            self.sddc_manager_hostname,
            self.sddc_manager_user,
            self.sddc_manager_password,
        )

    def _exit_if_check_mode(self, *, changed, message, meta=None):
        """Exit early in check mode with a consistent payload."""
        if not self.module.check_mode:
            return
        payload = {"message": f"Check Mode: {message}; no changes were performed."}
        if meta:
            payload.update(meta)
        self.module.exit_json(changed=changed, meta=payload)

    def _commission_fqdns(self):
        """Return list of FQDNs in HostCommissionSpec payload (best-effort)."""
        spec = self.hosts_payload.get("HostCommissionSpec") or []
        return [h.get("fqdn") for h in spec if isinstance(h, dict) and h.get("fqdn")]

    def _decommission_fqdns(self):
        """Return list of FQDNs in HostDecommissionSpec payload (best-effort)."""
        spec = self.hosts_payload.get("HostDecommissionSpec") or []
        return [h.get("fqdn") for h in spec if isinstance(h, dict) and h.get("fqdn")]

    def check_hosts_in_payload_are_valid_for_decommission(self):
        """Checks if the ESX hosts in the payload are valid for decommissioning."""
        valid_fqdns = []

        try:
            api_response = self.api_client.get_hosts_by_status("UNASSIGNED_UNUSEABLE")
            if "elements" in api_response:
                valid_fqdns.extend(
                    [element["fqdn"] for element in api_response["elements"]]
                )
        except VcfApiException as e:
            self.module.fail_json(
                msg=f"Error retrieving UNASSIGNED_UNUSEABLE hosts: {e}"
            )

        try:
            api_response = self.api_client.get_hosts_by_status("UNASSIGNED_USEABLE")
            if "elements" in api_response:
                valid_fqdns.extend(
                    [element["fqdn"] for element in api_response["elements"]]
                )
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error retrieving UNASSIGNED_USEABLE hosts: {e}")

        for host in self.hosts_payload["HostDecommissionSpec"]:
            if host["fqdn"] not in valid_fqdns:
                try:
                    host_info = self.api_client.get_hosts_by_fqdn(host["fqdn"])
                    if "elements" in host_info and len(host_info["elements"]) > 0:
                        current_status = host_info["elements"][0].get(
                            "status", "UNKNOWN"
                        )
                        cluster_info = host_info["elements"][0].get("cluster", {})
                        cluster_name = (
                            cluster_info.get("name", "N/A") if cluster_info else "N/A"
                        )

                        if current_status == "ASSIGNED":
                            self.module.fail_json(
                                msg=f"Error: ESX host {host['fqdn']} cannot be decommissioned because it is currently assigned to cluster '{cluster_name}'."
                            )
                        else:
                            self.module.fail_json(
                                msg=f"Error: ESX host {host['fqdn']} is not valid for decommission. "
                                f"Current status: {current_status}. Required status: UNASSIGNED_UNUSEABLE or UNASSIGNED_USEABLE."
                            )
                    else:
                        self.module.fail_json(
                            msg=f"Error: ESX host {host['fqdn']} not found in SDDC Manager inventory."
                        )
                except VcfApiException:
                    self.module.fail_json(
                        msg=f"Error: ESX host {host['fqdn']} is not in a valid status for decommission. "
                        f"Hosts must be in an UNASSIGNED_UNUSEABLE or UNASSIGNED_USEABLE status for decommissioning."
                    )

    def host_commission_validate_hosts(self):
        """Validates the ESX hosts for commissioning."""
        try:
            api_response = self.api_client.validate_hosts(
                json.dumps(self.hosts_payload["HostCommissionSpec"])
            )
            payload_data = api_response
            return payload_data
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error: {e}")

    def host_commission_commission_hosts(self):
        """Commissions the ESX hosts."""
        try:
            api_response = self.api_client.commission_hosts(
                json.dumps(self.hosts_payload["HostCommissionSpec"])
            )
            payload_data = api_response
            return payload_data
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error: {e}")

    def host_commission_decommission_hosts(self):
        """Decommissions the ESX hosts."""
        self.check_hosts_in_payload_are_valid_for_decommission()

        try:
            api_response = self.api_client.decommission_hosts(
                json.dumps(self.hosts_payload["HostDecommissionSpec"])
            )
            payload_data = api_response
            return payload_data
        except VcfApiException as e:
            self.module.fail_json(msg=f"Error: {e}")

    def run(self):
        """Runs the ESX host commissioning/decomissioning process."""
        if self.module.check_mode:
            if self.module.params["state"] == "present":
                hosts = self._commission_fqdns()
                if self.module.params["validate"]:
                    self.module.exit_json(
                        changed=False,
                        msg=f"Check Mode: Would validate {len(hosts)} host(s) for commissioning: {', '.join(hosts)}.",
                    )
                else:
                    self.module.exit_json(
                        changed=True,
                        msg=f"Check Mode: Would commission {len(hosts)} host(s): {', '.join(hosts)}.",
                    )
            elif self.module.params["state"] == "absent":
                hosts = self._decommission_fqdns()
                if self.module.params["validate"]:
                    self.module.exit_json(
                        changed=False,
                        msg=f"Check Mode: Would validate {len(hosts)} host(s) for decommissioning: {', '.join(hosts)}.",
                    )
                else:
                    self.module.exit_json(
                        changed=True,
                        msg=f"Check Mode: Would decommission {len(hosts)} host(s): {', '.join(hosts)}.",
                    )

        if self.module.params["state"] == "present" and self.module.params["validate"]:
            result = self.host_commission_validate_hosts()
            hosts = self._commission_fqdns()
            self.module.exit_json(
                changed=False,
                msg=f"Successfully completed payload validation for {len(hosts)} host(s): {', '.join(hosts)}.",
                meta=result,
            )

        elif (
            self.module.params["state"] == "present"
            and not self.module.params["validate"]
        ):
            result = self.host_commission_commission_hosts()
            hosts = self._commission_fqdns()
            self.module.exit_json(
                changed=True,
                msg=f"Successfully submitted host commission task for {len(hosts)} host(s): {', '.join(hosts)}.",
                meta=result,
            )

        elif self.module.params["state"] == "absent" and self.module.params["validate"]:
            self.check_hosts_in_payload_are_valid_for_decommission()
            hosts = self._decommission_fqdns()
            self.module.exit_json(
                changed=False,
                msg=f"Successfully completed payload validation for {len(hosts)} host(s): {', '.join(hosts)}.",
            )

        elif (
            self.module.params["state"] == "absent"
            and not self.module.params["validate"]
        ):
            result = self.host_commission_decommission_hosts()
            hosts = self._decommission_fqdns()
            self.module.exit_json(
                changed=True,
                msg=f"Successfully submitted host decommission task for {len(hosts)} host(s): {', '.join(hosts)}.",
                meta=result,
            )

        else:
            self.module.fail_json(
                msg="Not a valid combination of state and validate parameters."
            )


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    parameters = dict(
        sddc_manager_hostname=dict(required=True, type="str"),
        sddc_manager_user=dict(required=True, type="str"),
        sddc_manager_password=dict(required=True, type="str", no_log=True),
        hosts_payload=dict(required=True, type="dict"),
        validate=dict(required=False, type="bool", default=False),
        state=dict(required=True, type="str", choices=["present", "absent"]),
    )

    module = AnsibleModule(argument_spec=parameters, supports_check_mode=True)

    host = SddcManagerHosts(module)
    host.run()


if __name__ == "__main__":
    main()
