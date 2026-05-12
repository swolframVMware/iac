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

import json
import re

from ansible.errors import AnsibleUndefinedVariable
from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.six import string_types
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    """Custom debug plugin to display messages with sensitive data redaction."""

    TRANSFERS_FILES = False
    _VALID_ARGS = frozenset(("msg", "var", "verbosity"))
    _requires_connection = False

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        # Validate arguments.
        validation_result, new_module_args = self.validate_argument_spec(
            argument_spec={
                "msg": {"type": "raw", "default": "Hello world!"},
                "var": {"type": "raw"},
                "verbosity": {"type": "int", "default": 0},
            },
            mutually_exclusive=(("msg", "var"),),
        )
        # Define sensitive keys to redact
        module_args = self._task.args.copy()
        sensitive_keys1 = [
            "password",
            "pwd",
            ".*_password",
            "secret",
            ".*pwd",
            ".*passwrd",
            ".*token",
            ".*Password",
        ]
        sensitive_keys = module_args.get("sensitive_keys", sensitive_keys1)

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp

        # Get task verbosity.
        verbosity = new_module_args["verbosity"]

        def redact_sensitive_data(data, patterns):
            """Redact sensitive data from a dictionary or list."""
            if isinstance(data, dict):
                return {
                    key: redact_sensitive_data(
                        (
                            "[REDACTED]"
                            if any(
                                re.match(pattern, key, re.IGNORECASE)
                                for pattern in patterns
                            )
                            else value
                        ),
                        patterns,
                    )
                    for key, value in data.items()
                }
            elif isinstance(data, list):
                return [redact_sensitive_data(item, patterns) for item in data]
            elif isinstance(data, string_types):
                # Redact sensitive patterns inside strings.
                for pattern in patterns:
                    data = re.sub(
                        rf"({pattern})\s*[:=]\s*([^\s,]+)",
                        r"\1=[REDACTED]",
                        data,
                        flags=re.IGNORECASE,
                    )
                return data
            else:
                return data

        def resolve_and_redact(resolved_msg, patterns):
            """Resolves and redacts variables in a message."""
            try:
                # If resolved message is a dictionary or list, redact directly.
                if isinstance(resolved_msg, (dict, list)):
                    return redact_sensitive_data(resolved_msg, patterns)

                # If resolved message is a string, try parsing JSON-like structure.
                if isinstance(resolved_msg, string_types):
                    # Find the indices of the first and last { and }.
                    first_brace = resolved_msg.find("{")
                    last_brace = resolved_msg.rfind("}")

                    # Extract the substring before the JSON object.
                    if first_brace != -1 and last_brace != -1:
                        before_json = resolved_msg[:first_brace]

                        # Extract the substring between the first and last { and }.
                        json_string = resolved_msg[first_brace : last_brace + 1]

                        # Extract the substring after the JSON object.
                        after_json = resolved_msg[last_brace:]

                        # Remove the leading and trailing whitespace.
                        json_string = json_string.strip()

                        # self._display.display(f"DEBUG: {json_string}")
                        # Replace all single quotes with double quotes.
                        json_string = json_string.replace("'", '"')

                        # Convert the JSON string to a JSON object.
                        json_data = json.loads(json_string)
                        process_data = redact_sensitive_data(json_data, patterns)
                        return f"{before_json} {process_data} {after_json}"
                    else:
                        return resolved_msg

                return resolved_msg
            except Exception as e:
                self._display.display(f"String parse error: {to_text(e)}")
                return resolved_msg

        if verbosity <= self._display.verbosity:
            if new_module_args["var"]:
                try:
                    results = self._templar.template(new_module_args["var"])
                    if results == new_module_args["var"]:
                        if not isinstance(results, string_types):
                            raise AnsibleUndefinedVariable
                        if results in task_vars:
                            results = self._templar.template(task_vars[results])
                        else:
                            results = self._templar.template("{{ " + results + " }}")

                    results = redact_sensitive_data(results, sensitive_keys)

                except AnsibleUndefinedVariable as e:
                    results = "VARIABLE IS NOT DEFINED!"
                    if self._display.verbosity > 0:
                        results += ": %s" % to_text(e)

                if isinstance(new_module_args["var"], (list, dict)):
                    result[to_text(type(new_module_args["var"]))] = results
                else:
                    result[new_module_args["var"]] = results
            else:
                # Resolve and redact sensitive data from 'msg'.
                msg = new_module_args["msg"]
                # self._display.display("DEBUG: Original msg = %s" % msg).
                redacted_msg = resolve_and_redact(msg, sensitive_keys)
                result["msg"] = redacted_msg

            # Force flag to make debug output module always verbose.
            result["_ansible_verbose_always"] = True
        else:
            result["skipped_reason"] = "Verbosity threshold not met."
            result["skipped"] = True

        result["failed"] = False
        return result
