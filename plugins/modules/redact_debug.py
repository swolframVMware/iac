#!/usr/bin/python
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

from __future__ import annotations

DOCUMENTATION = r"""
---
module: redact_debug
short_description: Redact passwords and secrets from debug output.
description:
    - This module redacts passwords and secrets from output.
    - Works like the debug module but automatically redacts sensitive data.
author:
    - Broadcom Professional Services (@broadcom)
options:
    var:
        description: Variable to display.
        type: raw
    msg:
        description: Message to display.
        type: str
    verbosity:
        description: Verbosity level for output.
        type: int
        default: 0
"""

EXAMPLES = r"""
- name: Debug variable with password redaction
  broadcom.vcf.redact_debug:
    var: esx_certificate

- name: Debug message
  broadcom.vcf.redact_debug:
    msg: "Task completed"
"""

RETURN = r"""
msg:
    description: The message displayed with sensitive data redacted.
    returned: always
    type: str
"""

from ansible.module_utils.basic import AnsibleModule


def main():
    """Module execution is handled by the action plugin."""
    module = AnsibleModule(
        argument_spec=dict(
            var=dict(type="raw"),
            msg=dict(type="str"),
            verbosity=dict(type="int", default=0),
        ),
        supports_check_mode=True,
    )

    # Action plugin handles actual execution
    module.exit_json(msg="This module requires an action plugin")


if __name__ == "__main__":
    main()
