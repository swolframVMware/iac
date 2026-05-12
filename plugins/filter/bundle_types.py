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

"""Jinja2 filter plugins for VCF bundle product type mappings."""

from ansible_collections.broadcom.vcf.plugins.module_utils.bundle_types import (
    get_display_name,
    get_friendly_name,
    normalize_product_type,
)


class FilterModule:
    def filters(self):
        return {
            "vcf_api_type": normalize_product_type,
            "vcf_display_name": get_display_name,
            "vcf_friendly_name": get_friendly_name,
        }
