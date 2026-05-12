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

"""Bundle product type mappings for VCF Installer.

This module provides mappings between user-friendly names and VCF API internal names
for product types, bundle types, and image types.
"""

# ==============================================================================
# Product Type Mappings
# ==============================================================================

# Mapping from user-friendly names to API internal names
PRODUCT_TYPE_FRIENDLY_TO_API = {
    # User-friendly name: API internal name
    "avi-lb": "NSX_ALB",
    "cloud-proxy": "VCF_OPS_CLOUD_PROXY",
    "fleet-lcm": "VCF_FLEET_LCM",
    "identity-broker": "VIDB",
    "license-server": "VCF_LICENSE_SERVER",
    "migration-services-engine": "VCF_SERVICE_VCD_MIGRATION_BACKEND",
    "nsx": "NSX_T_MANAGER",
    "salt-master": "VCF_SALT",
    "salt-raas": "VCF_SALT_RAAS",
    "sddc-lcm": "VCF_SDDC_LCM",
    "sddc-manager": "SDDC_MANAGER",
    "software-depot": "DEPOT_SERVICE",
    "telemetry": "TELEMETRY_ACCEPTOR",
    "vcenter": "VCENTER",
    "vcf-automation": "VRA",
    "vcf-operations": "VROPS",
    "vcf-operations-fleet": "VRSLCM",
    "vcf-operations-hcx": "HCX",
    "vcf-service-runtime": "VSP",
}

# Reverse mapping from API internal names to user-friendly names
PRODUCT_TYPE_API_TO_FRIENDLY = {v: k for k, v in PRODUCT_TYPE_FRIENDLY_TO_API.items()}

# Display names for products (what users see in UI)
PRODUCT_TYPE_DISPLAY_NAMES = {
    "DEPOT_SERVICE": "Software Depot",
    "HCX": "VCF Operations HCX",
    "NSX_ALB": "Avi Load Balancer",
    "NSX_T_MANAGER": "NSX",
    "SDDC_MANAGER": "SDDC Manager",
    "TELEMETRY_ACCEPTOR": "Telemetry",
    "VCENTER": "vCenter",
    "VCF_FLEET_LCM": "Fleet Lifecycle",
    "VCF_LICENSE_SERVER": "License Server",
    "VCF_OPS_CLOUD_PROXY": "Cloud Proxy",
    "VCF_SALT": "Salt Master",
    "VCF_SALT_RAAS": "Salt RaaS",
    "VCF_SDDC_LCM": "SDDC Lifecycle",
    "VCF_SERVICE_VCD_MIGRATION_BACKEND": "Migration Service Engine",
    "VIDB": "Identity Broker",
    "VRA": "VCF Automation",
    "VROPS": "VCF Operations",
    "VRSLCM": "VCF Operations Fleet Management",
    "VSP": "VCF Services Runtime",
}

# All valid API product types
VALID_API_PRODUCT_TYPES = [
    "DEPOT_SERVICE",
    "HCX",
    "NSX_ALB",
    "NSX_T_MANAGER",
    "SDDC_MANAGER",
    "TELEMETRY_ACCEPTOR",
    "VCENTER",
    "VCF_FLEET_LCM",
    "VCF_LICENSE_SERVER",
    "VCF_OPS_CLOUD_PROXY",
    "VCF_SALT",
    "VCF_SALT_RAAS",
    "VCF_SDDC_LCM",
    "VCF_SERVICE_VCD_MIGRATION_BACKEND",
    "VIDB",
    "VRA",
    "VROPS",
    "VRSLCM",
    "VSP",
]

# All valid user-friendly product types
VALID_FRIENDLY_PRODUCT_TYPES = list(PRODUCT_TYPE_FRIENDLY_TO_API.keys())

# Combined list for Ansible choices (both friendly and API names accepted)
PRODUCT_TYPE_CHOICES = VALID_FRIENDLY_PRODUCT_TYPES + VALID_API_PRODUCT_TYPES


def normalize_product_type(product_type):
    """Convert user-friendly or API product type to API format.

    Args:
        product_type (str): Product type in either friendly or API format.

    Returns:
        str: Product type in API format (e.g., "NSX_T_MANAGER").

    Raises:
        ValueError: If product_type is not recognized.
    """
    if not product_type:
        raise ValueError("Product type cannot be empty")

    # Already in API format
    if product_type in VALID_API_PRODUCT_TYPES:
        return product_type

    # Convert from friendly format
    if product_type in PRODUCT_TYPE_FRIENDLY_TO_API:
        return PRODUCT_TYPE_FRIENDLY_TO_API[product_type]

    raise ValueError(
        f"Unknown product type: {product_type}. "
        f"Valid friendly names: {', '.join(VALID_FRIENDLY_PRODUCT_TYPES)}. "
        f"Valid API names: {', '.join(VALID_API_PRODUCT_TYPES)}"
    )


def normalize_product_types(product_types):
    """Convert a list of product types to API format.

    Args:
        product_types (list): List of product types in friendly or API format.

    Returns:
        list: List of product types in API format.
    """
    if not product_types:
        return []

    return [normalize_product_type(pt) for pt in product_types]


def get_display_name(api_product_type):
    """Get the display name for a product type.

    Args:
        api_product_type (str): Product type in API format.

    Returns:
        str: Display name for the product.
    """
    return PRODUCT_TYPE_DISPLAY_NAMES.get(api_product_type, api_product_type)


def get_friendly_name(api_product_type):
    """Get the friendly name for a product type.

    Args:
        api_product_type (str): Product type in API format.

    Returns:
        str: Friendly name for the product.
    """
    return PRODUCT_TYPE_API_TO_FRIENDLY.get(api_product_type, api_product_type)


# ==============================================================================
# Bundle Type Mappings
# ==============================================================================

# Mapping from user-friendly names to API internal names
BUNDLE_TYPE_FRIENDLY_TO_API = {
    "sddc-manager": "SDDC_MANAGER",
    "vmware-software": "VMWARE_SOFTWARE",
    "vxrail": "VXRAIL",
}

# Reverse mapping
BUNDLE_TYPE_API_TO_FRIENDLY = {v: k for k, v in BUNDLE_TYPE_FRIENDLY_TO_API.items()}

# All valid API bundle types
VALID_API_BUNDLE_TYPES = ["SDDC_MANAGER", "VMWARE_SOFTWARE", "VXRAIL"]

# All valid user-friendly bundle types
VALID_FRIENDLY_BUNDLE_TYPES = list(BUNDLE_TYPE_FRIENDLY_TO_API.keys())

# Combined list for Ansible choices
BUNDLE_TYPE_CHOICES = VALID_FRIENDLY_BUNDLE_TYPES + VALID_API_BUNDLE_TYPES


def normalize_bundle_type(bundle_type):
    """Convert user-friendly or API bundle type to API format.

    Args:
        bundle_type (str): Bundle type in either friendly or API format.

    Returns:
        str: Bundle type in API format (e.g., "VMWARE_SOFTWARE").

    Raises:
        ValueError: If bundle_type is not recognized.
    """
    if not bundle_type:
        raise ValueError("Bundle type cannot be empty")

    # Already in API format
    if bundle_type in VALID_API_BUNDLE_TYPES:
        return bundle_type

    # Convert from friendly format
    if bundle_type in BUNDLE_TYPE_FRIENDLY_TO_API:
        return BUNDLE_TYPE_FRIENDLY_TO_API[bundle_type]

    raise ValueError(
        f"Unknown bundle type: {bundle_type}. "
        f"Valid friendly names: {', '.join(VALID_FRIENDLY_BUNDLE_TYPES)}. "
        f"Valid API names: {', '.join(VALID_API_BUNDLE_TYPES)}"
    )


# ==============================================================================
# Image Type Mappings
# ==============================================================================

# Mapping from user-friendly names to API internal names
IMAGE_TYPE_FRIENDLY_TO_API = {
    "install": "INSTALL",
    "patch": "PATCH",
}

# Reverse mapping
IMAGE_TYPE_API_TO_FRIENDLY = {v: k for k, v in IMAGE_TYPE_FRIENDLY_TO_API.items()}

# All valid API image types
VALID_API_IMAGE_TYPES = ["INSTALL", "PATCH"]

# All valid user-friendly image types
VALID_FRIENDLY_IMAGE_TYPES = list(IMAGE_TYPE_FRIENDLY_TO_API.keys())

# Combined list for Ansible choices
IMAGE_TYPE_CHOICES = VALID_FRIENDLY_IMAGE_TYPES + VALID_API_IMAGE_TYPES


def normalize_image_type(image_type):
    """Convert user-friendly or API image type to API format.

    Args:
        image_type (str): Image type in either friendly or API format.

    Returns:
        str: Image type in API format (e.g., "INSTALL").

    Raises:
        ValueError: If image_type is not recognized.
    """
    if not image_type:
        raise ValueError("Image type cannot be empty")

    # Already in API format
    if image_type in VALID_API_IMAGE_TYPES:
        return image_type

    # Convert from friendly format
    if image_type in IMAGE_TYPE_FRIENDLY_TO_API:
        return IMAGE_TYPE_FRIENDLY_TO_API[image_type]

    raise ValueError(
        f"Unknown image type: {image_type}. "
        f"Valid friendly names: {', '.join(VALID_FRIENDLY_IMAGE_TYPES)}. "
        f"Valid API names: {', '.join(VALID_API_IMAGE_TYPES)}"
    )
