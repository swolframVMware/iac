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
module: sddc_manager_perform_config_reconciliation
short_description: Performs configuration reconciliation in SDDC Manager.
description:
    - This module performs configuration reconciliation in SDDC Manager for VMware Cloud Foundation.
author:
    - Broadcom Professional Services (@broadcom)
extends_documentation_fragment:
    - broadcom.vcf.sddc_manager
options:
    resource_id:
        description:
            - The ID of the resource to reconcile.
        required: true
        type: str
requirements:
    - python >= 3.12
"""

EXAMPLES = r"""
- name: Perform configuration reconciliation
  broadcom.vcf.sddc_manager_perform_config_reconciliation:
    sddc_manager_hostname: sddc-manager.example.com
    sddc_manager_user: admin
    sddc_manager_password: password
    resource_id: 12345678-1234-1234-1234-123456789012
"""

RETURN = r"""
meta:
    description: The reconciliation task result
    returned: always
    type: dict
msg:
    description: Error message when applicable
    returned: always
    type: str
changed:
    description: Whether any changes were made
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
            resource_id=dict(required=True, type="str"),
        )
    )
    sddc_manager_hostname = module.params.get("sddc_manager_hostname")
    sddc_manager_user = module.params.get("sddc_manager_user")
    sddc_manager_password = module.params.get("sddc_manager_password")
    resource_id = module.params.get("resource_id")

    payload = {
        "reconciliationForResources": [{"resourceId": resource_id, "applyAll": True}]
    }

    try:
        api_client = SddcManagerApiClient(
            sddc_manager_hostname, sddc_manager_user, sddc_manager_password
        )

        try:
            result = api_client.perform_config_drift_reconciliation(json.dumps(payload))
            payload_data = result
        except VcfApiException as e:
            module.fail_json(
                changed=False, msg="Error performing upgrade: ", meta=f"Error: {e}"
            )

        module.exit_json(
            changed=False,
            status_code=result.status_code,
            message=result.message,
            meta=payload_data,
        )

    except VcfApiException as e:
        module.fail_json(
            changed=False, msg="Unexpected error occurred.", meta=f"Error: {e}"
        )


if __name__ == "__main__":
    main()
