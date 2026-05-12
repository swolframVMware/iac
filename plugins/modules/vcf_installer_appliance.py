#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2025-2026 Broadcom. All Rights Reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
---
module: vcf_installer_appliance
short_description: Deploys the VCF Installer OVA to a vSphere environment
description:
    - This module deploys the VCF Installer OVA to a vCenter instance or ESX host.
author:
    - Broadcom Professional Services (@broadcom)
options:
    hostname:
        description:
            - The FQDN or IP address of the vCenter instance or ESX host.
        type: str
        required: true
    username:
        description:
            - The username to authenticate with the vCenter instance or ESX host.
        type: str
        required: true
    password:
        description:
            - The password to authenticate with the vCenter instance or ESX host.
        type: str
        required: true
        no_log: true
    port:
        description:
            - The port number of the vCenter instance or ESX host.
        type: int
        default: 443
    validate_certs:
        description:
            - Whether to validate SSL certificates.
        type: bool
        default: true
    state:
        description:
            - Desired state of the VCF Installer appliance.
            - C(present) - Ensure the VCF Installer appliance is deployed. If it already exists, no changes are made.
            - C(absent) - Ensure the VCF Installer appliance is removed. If it doesn't exist, no changes are made.
            - C(validate) - Validate that target vSphere resources exist without deploying. Checks datacenter, cluster/ESX host, datastore, folder, and network.
        type: str
        choices:
            - present
            - absent
            - validate
        default: present
    name:
        description:
            - The name of the VCF Installer appliance will be deployed.
        type: str
        required: true
    datacenter:
        description:
            - The name of the vSphere datacenter where the VCF Installer appliance will be deployed.
        type: str
        default: ha-datacenter
    cluster:
        description:
            - The name of the vSphere cluster where the VCF Installer appliance will be deployed.
            - Required if O(esx_hostname) is not specified.
            - Mutually exclusive with O(esx_hostname).
        type: str
        required: false
    esx_hostname:
        description:
            - The FQDN of the ESX host where the VCF Installer appliance will be deployed.
            - Required if O(cluster) is not specified.
            - Mutually exclusive with O(cluster).
        type: str
        required: false
    datastore:
        description:
            - The name of the datastore where the VCF Installer appliance will be deployed.
            - Supports datastore clusters (automatically selects datastore with most free space).
        type: str
        default: ds01
        required: true
    folder:
        description:
            - The absolute path of the vSphere folder where the VCF Installer appliance will be deployed.
            - If not specified, defaults to the datacenter's folder.
            - 'Examples: /ha-datacenter/vm, /datacenter1/vm/folder1'
        type: str
        required: false
    resource_pool:
        description:
            - The name of the vSphere resource pool where the VCF Installer appliance will be deployed.
            - If not specified, defaults to root resource pool of the cluster.
        type: str
        default: Resources
        required: false
    ovf:
        description:
            - The path to the VCF Installer OVA file to deploy.
            - Required if O(url) is not specified.
            - Mutually exclusive with O(url).
        type: path
        aliases:
            - ova
        required: false
    url:
        description:
            - The URL of the VCF Installer OVA file to deploy.
            - Required if O(ovf) is not specified.
            - Mutually exclusive with O(ovf).
        type: str
        required: false
    url_username:
        description:
            - Username to authenticate to the O(url) when downloading the OVA.
            - Only used when O(url) is specified.
        type: str
        required: false
    url_password:
        description:
            - Password tio authenticate to the O(url) when downloading the OVA.
            - Only used when O(url) is specified.
        type: str
        required: false
        no_log: true
    networks:
        description:
            - The mapping of OVF network names to network names in the vSphere inventory.
            - 'Format: {"Network 1": "vSphere Port Group"}'
        type: dict
        default:
            Network 1: VM Network
    properties:
        description:
            - The vApp properties to set on the VCF Installer appliance.
            - These are specific to the VCF Installer OVA.
        type: dict
        required: false
    disk_provisioning:
        description:
            - The disk provisioning type to use for the VCF Installer appliance's disks.
        type: str
        choices:
            - thin
            - thick
            - eagerZeroedThick
        default: thin
    power_on:
        description:
            - Option to power on the VCF Installer appliance after deployment.
            - Only applicable when O(state=present).
        type: bool
        default: true
    wait_for_ip_address:
        description:
            - Option to wait for the VCF Installer appliance to get an IP address.
            - Only applicable when O(state=present).
            - Recommended for VCF Installer to ensure API is accessible.
        type: bool
        default: true
    force:
        description:
            - Force removal of the VCF Installer appliancee when O(state=absent).
            - If C(true), powers off the VCF Installer appliance if it's running before removal.
            - If C(false), fails if the VCF Installer appliance is powered on.
        type: bool
        default: false
    allow_duplicates:
        description:
            - Option to allow duplicate VCF Installer appliances with the same name.
            - If C(true), allows multiple VCF Installer appliances with the same name.
            - If C(false), fails if a VCF Installer appliance with the same name already exists..
        type: bool
        default: false
    fail_on_spec_warnings:
        description:
            - Option to fail the deployment if any warnings are reported.
        type: bool
        default: false
requirements:
    - python >= 3.12
    - PyVmomi
"""

EXAMPLES = r"""
- name: Deploy VCF Installer OVA from Local OVA File
  broadcom.vcf.vcf_installer_appliance:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: false
    state: present
    datacenter: dc01
    cluster: cl01
    datastore: ds01
    name: vcf-installer
    ovf: /path/to/vcf-installer.ova
    networks:
      "Network 1": "VM Network"
    properties:
      vami.hostname: vcf-installer.example.com
      vami.ip0.SDDC-Manager: 192.168.1.100
      vami.netmask0.SDDC-Manager: 255.255.255.0
      vami.gateway.SDDC-Manager: 192.168.1.1
      vami.DNS.SDDC-Manager: 192.168.1.10,192.168.1.11
      vami.domain.SDDC-Manager: example.com
      vami.searchpath.SDDC-Manager: example.com
      guestinfo.ntp: 192.168.1.12,192.168.1.13
      ROOT_PASSWORD: "<replace_me>"
      LOCAL_USER_PASSWORD: "<replace_me>"
    power_on: true
    wait_for_ip_address: true
  delegate_to: localhost

- name: Deploy VCF Installer OVA from URL
  broadcom.vcf.vcf_installer_appliance:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: false
    state: present
    datacenter: dc01
    cluster: cl01
    datastore: ds01
    name: vcf-installer
    url: https://example.com/vcf-installer.ova
    networks:
      "Network 1": "VM Network"
    properties:
      vami.hostname: vcf-installer.example.com
      vami.ip0.SDDC-Manager: 192.168.1.100
      vami.netmask0.SDDC-Manager: 255.255.255.0
      vami.gateway.SDDC-Manager: 192.168.1.1
      vami.DNS.SDDC-Manager: 192.168.1.10,192.168.1.11
      vami.domain.SDDC-Manager: example.com
      vami.searchpath.SDDC-Manager: example.com
      guestinfo.ntp: 192.168.1.12,192.168.1.13
      ROOT_PASSWORD: "<replace_me>"
      LOCAL_USER_PASSWORD: "<replace_me>"
    power_on: true
    wait_for_ip_address: true
  delegate_to: localhost

- name: Deploy VCF Installer OVA from URL with Authentication
  broadcom.vcf.vcf_installer_appliance:
    hostname: "{{ vcenter_hostname }}"
    username: "{{ vcenter_username }}"
    password: "{{ vcenter_password }}"
    validate_certs: false
    state: present
    datacenter: dc01
    cluster: cl01
    datastore: ds01
    name: vcf-installer
    url: https://packages.example.com/VCF-SDDC-Manager-Appliance-9.x.x.x.xxxxxxxx.ova
    url_username: "<replace_me>"
    url_password: "<replace_me>"
    networks:
      "Network 1": "VM Network"
    properties:
      vami.hostname: vcf-installer.example.com
      vami.ip0.SDDC-Manager: 192.168.1.100
      vami.netmask0.SDDC-Manager: 255.255.255.0
      vami.gateway.SDDC-Manager: 192.168.1.1
      vami.DNS.SDDC-Manager: 192.168.1.10,192.168.1.11
      vami.domain.SDDC-Manager: example.com
      vami.searchpath.SDDC-Manager: example.com
      guestinfo.ntp: 192.168.1.12,192.168.1.13
      ROOT_PASSWORD: "<replace_me>"
      LOCAL_USER_PASSWORD: "<replace_me>"
    power_on: true
    wait_for_ip_address: true
  delegate_to: localhost
"""

RETURN = r"""
instance:
    description: Metadata about the deployed VCF Installer appliance.
    returned: on success when O(state=present)
    type: dict
    sample:
        hw_name: vcf-installer
        hw_power_status: poweredOn
        hw_guest_full_name: VMware Photon OS
        hw_guest_id: vmwarePhoton64Guest
        hw_product_uuid: "42123456-1234-1234-1234-123456789012"
        instance_uuid: "50123456-1234-1234-1234-123456789012"
        ipv4: 192.168.1.100
changed:
    description: Whether the deployment resulted in changes.
    returned: always
    type: bool
    sample: true
msg:
    description: Informational message about the operation result.
    returned: always
    type: str
    sample: "Successfully deployed VCF Installer appliance: 'vcf-installer'."
deployment_plan:
    description: Detailed deployment plan showing what would be deployed (check mode only).
    returned: in check mode when O(state=present) and VM would be created
    type: dict
    sample:
        vm_name: vcf-installer
        datacenter: dc01
        datastore: ds01
        resource_pool: Resources
        folder: /dc01/vm
        disk_provisioning: thin
        power_on_after_deployment: true
        wait_for_ip: true
        target_type: cluster
        target: cl01
        network_mappings:
            "Network 1": "VM Network"
        properties_configured: 10
        total_size_bytes: 12884901888
validation:
    description: vSphere resource validation results.
    returned: when O(state=validate)
    type: dict
    sample:
        valid: true
        datacenter:
            exists: true
            name: dc01
        cluster:
            exists: true
            name: cl01
        datastore:
            exists: true
            name: ds01
        folder:
            exists: true
            path: /dc01/vm
        network:
            exists: true
            name: VM Network
        missing_resources: []
"""

import base64
import hashlib
import io
import os
import ssl
import sys
import tarfile
import time
import traceback

from threading import Thread

from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.basic import AnsibleModule
from urllib.request import Request, urlopen
from urllib.parse import urlsplit, urlunsplit
from ansible.module_utils.urls import generic_urlparse, open_url, urlparse, urlunparse

from ansible_collections.broadcom.vcf.plugins.module_utils.vsphere import (
    get_connection_spec,
    connect_to_api,
    wait_for_task,
    find_obj,
    find_datacenter_by_name,
    find_cluster_by_name,
    find_hostsystem_by_name,
    find_datastore_by_name,
    find_datastore_cluster_by_name,
    find_resource_pool_by_name,
    find_resource_pool_by_cluster,
    find_all_networks_by_name,
    find_vm_by_name,
    gather_vm_facts,
    wait_for_vm_ip,
    set_vm_power_state,
    PyVmomi,
    HAS_PYVMOMI,
)

try:
    from pyVmomi import vim, vmodl
except ImportError:
    vim = None
    vmodl = None


def path_exists(value):
    """Check if a file path exists.

    Args:
        value (str): File path to check.

    Returns:
        str: The validated path.

    Raises:
        ValueError: If the path does not exist or is not a valid file.
    """
    if not isinstance(value, str):
        value = str(value)
    value = os.path.expanduser(os.path.expandvars(value))
    if not os.path.exists(value):
        raise ValueError(f"'{value}' is not a valid path.")
    return value


def _split_url(url):
    """Parse and validate a URL.

    Accessing parsed.port forces urllib to validate the netloc and raises
    ValueError for malformed values such as nonnumeric ports.
    """
    try:
        parsed = urlsplit(url)
        parsed.port
        return parsed
    except ValueError as e:
        raise ValueError(
            "Invalid OVA URL '%s': %s. If credentials are embedded in the URL, "
            "move them to url_username/url_password or URL-encode special "
            "characters such as '@', ':', '/', '#', and '%%'." % (url, e)
        )


def _url_without_userinfo(parsed):
    """Build a URL from a parsed URL object without embedded credentials."""
    hostname = parsed.hostname or ""
    if ":" in hostname and not hostname.startswith("["):
        hostname = "[%s]" % hostname

    netloc = hostname
    if parsed.port:
        netloc += ":%s" % parsed.port

    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))



def _build_basic_auth_header(username, password):
    """Build an HTTP Basic Authentication header value.

    Args:
        username (str): Username for HTTP Basic Authentication.
        password (str): Password for HTTP Basic Authentication.

    Returns:
        str: The value to use for the ``Authorization`` header.
    """
    token = base64.b64encode(("%s:%s" % (username, password)).encode("utf-8")).decode("ascii")
    return "Basic %s" % token



class OvfOvaStreamReader(object):
    """Handle for downloading OVF/OVA files from HTTP/HTTPS URLs with range request support.

    This class provides file-like access to remote OVF/OVA files, supporting
    range requests for efficient streaming downloads.
    """

    def __init__(self, url, username=None, password=None):
        """Initialize OvfOvaStreamReader for a given URL.

        Args:
            url (str): The URL of the OVF/OVA file to download.

        Raises:
            FileNotFoundError: If the URL returns a non-200 status code.
            Exception: If content-length header is missing or range requests not supported.
        """
        parsed_url = _split_url(url)

        url_username = username if username is not None else parsed_url.username
        url_password = password if password is not None else parsed_url.password

        self.url = _url_without_userinfo(parsed_url)
        self.thumbprint = None
        self.ssl_context = None

        self.parsed_url = _split_url(self.url)
        self.https = self.parsed_url.scheme == "https"

        self.username = url_username
        self.password = url_password

        if self.https:
            self.ssl_context = ssl._create_default_https_context()
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE

            self.thumbprint = self._get_thumbprint(
                self.parsed_url.hostname, self.parsed_url.port or 443
            )
            r = urlopen(self._request("HEAD"), context=self.ssl_context)
        else:
            r = urlopen(self._request("HEAD"))

        if r.code != 200:
            raise FileNotFoundError(url)
        self.headers = self._headers_to_dict(r)

        if "content-length" not in self.headers:
            raise Exception("Missing content-length in response")
        self.st_size = int(self.headers["content-length"])

        if not self._supports_range_request():
            raise Exception(
                "Endpoint does not support HTTP range requests, which are required for streaming downloads."
            )

        self.offset = 0

    def _request_headers(self, extra_headers=None):
        """Build HTTP request headers.

        Args:
            extra_headers (dict, optional): Additional headers to include in the request. Defaults to None.

        Returns:
            dict: HTTP headers for the request.
        """
        headers = {}
        if self.username is not None:
            headers["Authorization"] = _build_basic_auth_header(
                self.username, self.password
            )
        if extra_headers:
            headers.update(extra_headers)
        return headers

    def _request(self, method, extra_headers=None):
        """Build HTTP request object.

        Args:
            method (str): HTTP method for the request.
            extra_headers (dict, optional): Additional headers to include in the request. Defaults to None.

        Returns:
            Request: HTTP request object.
        """
        return Request(self.url, method=method, headers=self._request_headers(extra_headers))

    def _supports_range_request(self):
        """Test if the server supports HTTP range requests.

        Returns:
            bool: True if server supports range requests (returns 206), False otherwise.
        """
        req = self._request("GET", {"Range": "bytes=0-0"})
        try:
            if self.ssl_context:
                r = urlopen(req, context=self.ssl_context)
            else:
                r = urlopen(req)
            return r.status == 206
        except Exception:
            return False

    def _get_thumbprint(self, hostname, port=443):
        """Get SSL certificate thumbprint for a hostname.

        Args:
            hostname (str): Hostname to get certificate thumbprint for.

        Returns:
            str or None: Colon-separated SHA1 thumbprint or None if unavailable.
        """
        pem = ssl.get_server_certificate((hostname, port))
        sha1 = hashlib.sha1(ssl.PEM_cert_to_DER_cert(pem)).hexdigest().upper()
        colon_notion = ":".join(sha1[i: i + 2] for i in range(0, len(sha1), 2))
        return None if sha1 is None else colon_notion

    def _headers_to_dict(self, r):
        """Convert HTTP response headers to a dictionary.

        Args:
            r: HTTP response object.

        Returns:
            dict: Dictionary of header names (lowercase) to values.
        """
        result = {}
        if hasattr(r, "getheaders"):
            for n, v in r.getheaders():
                result[n.lower()] = v.strip()
        else:
            for line in r.info().headers:
                if line.find(":") != -1:
                    n, v = line.split(": ", 1)
                    result[n.lower()] = v.strip()
        return result

    def tell(self):
        """Get current file position.

        Returns:
            int: Current offset in the file.
        """
        return self.offset

    def seek(self, offset, whence=0):
        """Seek to a position in the file.

        Args:
            offset (int): Offset to seek to.
            whence (int, optional): Reference point (0=start, 1=current, 2=end). Defaults to 0.

        Returns:
            int: New file position.
        """
        if whence == 0:
            self.offset = offset
        elif whence == 1:
            self.offset += offset
        elif whence == 2:
            self.offset = self.st_size - offset
        return self.offset

    def seekable(self):
        """Check if the file handle supports seeking.

        Returns:
            bool: Always returns True.
        """
        return True

    def read(self, amount):
        """Read a specified amount of data from the file.

        Args:
            amount (int): Number of bytes to read.

        Returns:
            bytes: Data read from the file.
        """
        start = self.offset
        end = self.offset + amount - 1
        req = self._request("GET", {"Range": "bytes=%d-%d" % (start, end)})
        r = (
            urlopen(req)
            if not self.ssl_context
            else urlopen(req, context=self.ssl_context)
        )
        self.offset += amount
        result = r.read(amount)
        r.close()
        return result

    def progress(self):
        """Calculate download progress percentage.

        Returns:
            int: Progress percentage (0-100).
        """
        return int(100.0 * self.offset / self.st_size)


class ProgressReader(io.FileIO):
    """File reader that tracks bytes read for progress reporting."""

    def __init__(self, name, mode="r", closefd=True):
        """Initialize ProgressReader.

        Args:
            name (str): File path to read.
            mode (str, optional): File open mode. Defaults to "r".
            closefd (bool, optional): Whether to close file descriptor. Defaults to True.
        """
        self.bytes_read = 0
        io.FileIO.__init__(self, name, mode=mode, closefd=closefd)

    def read(self, size=10240):
        """Read data from file and track bytes read.

        Args:
            size (int, optional): Number of bytes to read. Defaults to 10240.

        Returns:
            bytes: Data read from file.
        """
        chunk = io.FileIO.read(self, size)
        self.bytes_read += len(chunk)
        return chunk


class TarProgressReader(tarfile.ExFileObject):
    """Tar file member reader that tracks bytes read for progress reporting."""

    def __init__(self, *args):
        """Initialize TarProgressReader.

        Args:
            *args: Arguments passed to tarfile.ExFileObject.
        """
        self.bytes_read = 0
        tarfile.ExFileObject.__init__(self, *args)

    def __enter__(self):
        """Context manager entry.

        Returns:
            TarProgressReader: Self reference.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit with exception suppression.

        Args:
            exc_type: Exception type.
            exc_value: Exception value.
            traceback: Exception traceback.
        """
        try:
            self.close()
        except Exception:
            pass

    def read(self, size=10240):
        """Read data from tar member and track bytes read.

        Args:
            size (int, optional): Number of bytes to read. Defaults to 10240.

        Returns:
            bytes: Data read from tar member.
        """
        chunk = tarfile.ExFileObject.read(self, size)
        self.bytes_read += len(chunk)
        return chunk


class VmdkUploader(Thread):
    """Thread-based VMDK file uploader for OVF deployment."""

    def __init__(self, vmdk, url, validate_certs=True, tarinfo=None, create=False):
        """Initialize VMDK uploader thread.

        Args:
            vmdk: VMDK file path or tar file object.
            url (str): Upload destination URL.
            validate_certs (bool, optional): Whether to validate SSL certificates. Defaults to True.
            tarinfo (optional): TarInfo object if uploading from tar. Defaults to None.
            create (bool, optional): Whether this is a create operation (non-VMDK). Defaults to False.
        """
        Thread.__init__(self)

        self.vmdk = vmdk

        if tarinfo:
            self.size = tarinfo.size
        else:
            self.size = os.stat(vmdk).st_size

        self.url = url
        self.validate_certs = validate_certs
        self.tarinfo = tarinfo

        self.f = None
        self.e = None

        self._create = create

    @property
    def bytes_read(self):
        """Get number of bytes read so far.

        Returns:
            int: Bytes read or 0 if file handle not available.
        """
        try:
            return self.f.bytes_read
        except AttributeError:
            return 0

    def _request_opts(self):
        """Build HTTP request options for VMDK upload.

        VMDK files use POST with streamVmdk content type, while other files use PUT.

        Returns:
            dict: Dictionary containing HTTP method and headers.
        """
        headers = {
            "Content-Length": self.size,
            "Content-Type": "application/octet-stream",
        }

        if self._create:
            # Non-VMDK file creation operation.
            method = "PUT"
            headers["Overwrite"] = "t"
        else:
            # VMDK file upload operation.
            method = "POST"
            headers["Content-Type"] = "application/x-vnd.vmware-streamVmdk"

        return {
            "method": method,
            "headers": headers,
        }

    def _open_url(self):
        """Open URL connection and upload file data."""
        open_url(
            self.url,
            data=self.f,
            validate_certs=self.validate_certs,
            timeout=None, # No timeout when streaming uploads from the Ansible controller.
            **self._request_opts(),
        )

    def run(self):
        """Execute the upload in a separate thread.

        Opens the file (from tar or filesystem) and uploads it to the destination URL.
        Stores any exception in self.e for parent thread to handle.
        """
        if self.tarinfo:
            try:
                with TarProgressReader(self.vmdk, self.tarinfo) as self.f:
                    self._open_url()
            except Exception:
                self.e = sys.exc_info()
        else:
            try:
                with ProgressReader(self.vmdk, "rb") as self.f:
                    self._open_url()
            except Exception:
                self.e = sys.exc_info()


class OvfDeploymentHandler(PyVmomi):
    """Main class for deploying OVF/OVA files to vSphere.

    Handles the complete workflow of OVF deployment including validation,
    network mapping, property configuration, and file upload.
    """

    def __init__(self, module):
        """Initialize OvfDeploymentHandler.

        Args:
            module (AnsibleModule): Ansible module instance with deployment parameters.
        """
        super(OvfDeploymentHandler, self).__init__(module)
        self.module = module
        self.params = module.params

        self.handle = None
        self.datastore = None
        self.datacenter = None
        self.resource_pool = None
        self.network_mappings = []

        self.ovf_descriptor = None
        self.tar = None

        self.lease = None
        self.import_spec = None
        self.entity = None

    def get_objects(self):
        """Locate and validate all vSphere objects needed for deployment.

        Finds datacenter, cluster/host, resource pool, datastore, and networks
        based on module parameters.

        Returns:
            tuple: (datastore, datacenter, resource_pool, network_mappings)

        Raises:
            AnsibleModule.fail_json: If any required object cannot be located.
        """
        self.datacenter = self.find_datacenter_by_name(self.params["datacenter"])
        if self.datacenter is None:
            self.module.fail_json(
                msg=f"Unable to find datacenter '{self.params['datacenter']}'."
            )

        cluster = None
        if self.params["cluster"]:
            # Retrieve the cluster in the datacenter if a cluster is configured.
            cluster = self.find_cluster_by_name(
                self.params["cluster"], datacenter_name=self.datacenter
            )
            if cluster is None:
                self.module.fail_json(
                    msg=f"Unable to find cluster '{self.params['cluster']}'."
                )
            self.resource_pool = self.find_resource_pool_by_cluster(
                self.params["resource_pool"], cluster=cluster
            )
        elif self.params["esx_hostname"]:
            # Retrieve the ESX host in the datacenter if an ESX host is configured.
            host = self.find_hostsystem_by_name(
                self.params["esx_hostname"], datacenter=self.datacenter
            )
            if host is None:
                self.module.fail_json(
                    msg=f"Unable to find host '{self.params['esx_hostname']}'."
                )
            self.resource_pool = self.find_resource_pool_by_name(
                self.params["resource_pool"], folder=host.parent
            )
        else:
            # For multi-datacenter environments, use the datacenter's host folder.
            self.resource_pool = self.find_resource_pool_by_name(
                self.params["resource_pool"], folder=self.datacenter.hostFolder
            )

        if not self.resource_pool:
            self.module.fail_json(
                msg=f"Unable to find resource pool '{self.params['resource_pool']}'."
            )

        self.datastore = None
        datastore_cluster_obj = self.find_datastore_cluster_by_name(
            self.params["datastore"], datacenter=self.datacenter
        )
        if datastore_cluster_obj:
            datastore = None
            datastore_freespace = 0
            for ds in datastore_cluster_obj.childEntity:
                if (
                        isinstance(ds, vim.Datastore)
                        and ds.summary.freeSpace > datastore_freespace
                ):
                    # Filter out datastores that are in maintenance mode or not accessible.
                    if (
                            ds.summary.maintenanceMode != "normal"
                            or not ds.summary.accessible
                    ):
                        continue
                    datastore = ds
                    datastore_freespace = ds.summary.freeSpace
            if datastore:
                self.datastore = datastore
        else:
            self.datastore = self.find_datastore_by_name(
                self.params["datastore"], datacenter_name=self.datacenter
            )

        if self.datastore is None:
            self.module.fail_json(
                msg=f"Unable to find datastore '{self.params['datastore']}'."
            )

        for key, value in self.params["networks"].items():
            # Find all networks with the same name to handle multiple clusters with identically named networks.
            networks = find_all_networks_by_name(
                self.content, value, datacenter=self.datacenter
            )
            if not networks:
                self.module.fail_json(msg=f"Network '{value}' could not be located.")
            # Map the network that belongs to the specified cluster.
            network_found_in_cluster = False
            for network in networks:
                if cluster and network in cluster.network:
                    network_mapping = vim.OvfManager.NetworkMapping()
                    network_mapping.name = key
                    network_mapping.network = network
                    self.network_mappings.append(network_mapping)
                    network_found_in_cluster = True
                elif not cluster:
                    network_mapping = vim.OvfManager.NetworkMapping()
                    network_mapping.name = key
                    network_mapping.network = network
                    self.network_mappings.append(network_mapping)
                    network_found_in_cluster = True

            # If cluster specified but network not found in cluster, show helpful error
            if cluster and not network_found_in_cluster:
                available_networks = [net.name for net in cluster.network]
                self.module.fail_json(
                    msg=f"Network '{value}' exists in datacenter but is not associated with cluster '{cluster.name}'.\n"
                        f"Available networks in cluster: {', '.join(available_networks)}"
                )

        return (
            self.datastore,
            self.datacenter,
            self.resource_pool,
            self.network_mappings,
        )

    def get_ovf_descriptor(self):
        """Extract OVF descriptor from OVA file or URL.

        Reads the OVF descriptor XML from either a local OVA/OVF file or remote URL.

        Returns:
            str: OVF descriptor XML content.

        Raises:
            AnsibleModule.fail_json: If OVF file cannot be found or read.
        """
        if self.params["url"] is None:
            if self.params.get("url_username") or self.params.get("url_password"):
                self.module.fail_json(
                    msg="url_username and url_password can only be used when O(url) is specified."
                )
            try:
                path_exists(self.params["ovf"])
            except ValueError as e:
                self.module.fail_json(msg="%s" % e)

            if tarfile.is_tarfile(self.params["ovf"]):
                self.tar = tarfile.open(self.params["ovf"])
                ovf = None
                for candidate in self.tar.getmembers():
                    dummy, ext = os.path.splitext(candidate.name)
                    if ext.lower() == ".ovf":
                        ovf = candidate
                        break
                if not ovf:
                    self.module.fail_json(
                        msg="Could not locate OVF file in %(ovf)s" % self.params
                    )

                self.ovf_descriptor = to_native(self.tar.extractfile(ovf).read())
            else:
                with open(self.params["ovf"], encoding="utf-8") as f:
                    self.ovf_descriptor = f.read()

            return self.ovf_descriptor
        else:
            if bool(self.params.get("url_username")) ^ bool(
                    self.params.get("url_password")
            ):
                self.module.fail_json(
                    msg="Both url_username and url_password are required when using URL authentication."
                )

            try:
                self.handle = OvfOvaStreamReader(
                    self.params["url"],
                    self.params.get("url_username"),
                    self.params.get("url_password"),
                )
            except Exception as e:
                self.module.fail_json(
                    msg="Failed to access OVA URL '%s': %s"
                        % (self.params["url"], to_native(e))
                )
            self.tar = tarfile.open(fileobj=self.handle)
            ovffilename = list(
                filter(lambda x: x.endswith(".ovf"), self.tar.getnames())
            )[0]
            ovffile = self.tar.extractfile(ovffilename)
            self.ovf_descriptor = ovffile.read().decode()

            if self.ovf_descriptor:
                return self.ovf_descriptor
            else:
                self.module.fail_json(
                    msg="Could not locate OVF file in %(url)s" % self.params
                )

    def get_lease(self):
        """Create import spec and obtain HTTP NFC lease for deployment.

        Validates OVF descriptor, creates import specification with network
        and property mappings, and gets lease for file upload.

        In check mode, returns detailed deployment plan without creating lease.

        Returns:
            tuple: (lease, import_spec) - HTTP NFC lease and import specification.

        Raises:
            AnsibleModule.fail_json: If OVF validation fails or lease cannot be obtained.
        """
        datastore, datacenter, resource_pool, network_mappings = self.get_objects()

        params = {
            "diskProvisioning": self.params["disk_provisioning"],
        }
        if self.params["name"]:
            params["entityName"] = self.params["name"]
        if network_mappings:
            params["networkMapping"] = network_mappings
        if self.params["properties"]:
            params["propertyMapping"] = []
            for key, value in self.params["properties"].items():
                property_mapping = vim.KeyValue()
                property_mapping.key = key
                property_mapping.value = (
                    str(value) if isinstance(value, bool) else value
                )
                params["propertyMapping"].append(property_mapping)

        if self.params["folder"]:
            folder = self.content.searchIndex.FindByInventoryPath(self.params["folder"])
            if not folder:
                self.module.fail_json(
                    msg=f"Unable to find the specified folder {self.params['folder']}."
                )
        else:
            folder = datacenter.vmFolder

        spec_params = vim.OvfManager.CreateImportSpecParams(**params)

        ovf_descriptor = self.get_ovf_descriptor()

        self.import_spec = self.content.ovfManager.CreateImportSpec(
            ovf_descriptor, resource_pool, datastore, spec_params
        )

        errors = [to_native(e.msg) for e in getattr(self.import_spec, "error", [])]
        if self.params["fail_on_spec_warnings"]:
            errors.extend(
                (to_native(w.msg) for w in getattr(self.import_spec, "warning", []))
            )
        if errors:
            self.module.fail_json(
                msg=f"Failure validating OVF import spec: {'. '.join(errors)}"
            )

        for warning in getattr(self.import_spec, "warning", []):
            self.module.warn(
                f"Problem validating OVF import spec: {to_native(warning.msg)}"
            )

        name = self.params.get("name")
        if not self.params["allow_duplicates"]:
            name = self.import_spec.importSpec.configSpec.name
            match = find_vm_by_name(self.content, name, folder=folder)
            if match:
                self.module.exit_json(
                    msg=f"VCF Installer appliance '{name}' already exists; no changes made.",
                    instance=gather_vm_facts(self.content, match),
                    changed=False,
                )

        if self.module.check_mode:
            vm_name = name or self.import_spec.importSpec.configSpec.name
            check_msg = f"Check Mode: Would deploy VCF Installer appliance '{vm_name}'; no changes were performed."
            check_mode_result = {
                "changed": True,
                "msg": check_msg,
                "deployment_plan": {
                    "vm_name": name or self.import_spec.importSpec.configSpec.name,
                    "datacenter": self.params["datacenter"],
                    "datastore": self.params["datastore"],
                    "resource_pool": self.params["resource_pool"],
                    "folder": self.params.get(
                        "folder", f"{self.params['datacenter']}/vm"
                    ),
                    "disk_provisioning": self.params["disk_provisioning"],
                    "power_on_after_deployment": self.params["power_on"],
                    "wait_for_ip": self.params["wait_for_ip_address"],
                },
                "ovf_source": self.params.get("ovf") or self.params.get("url"),
                "network_mappings": {
                    key: value for key, value in self.params["networks"].items()
                },
                "properties_count": len(self.params.get("properties", {})),
            }

            if self.params.get("cluster"):
                check_mode_result["deployment_plan"]["target_type"] = "cluster"
                check_mode_result["deployment_plan"]["target"] = self.params["cluster"]
            elif self.params.get("esx_hostname"):
                check_mode_result["deployment_plan"]["target_type"] = "esxi_host"
                check_mode_result["deployment_plan"]["target"] = self.params[
                    "esx_hostname"
                ]

            if hasattr(self.import_spec, "warning") and self.import_spec.warning:
                check_mode_result["ovf_warnings"] = [
                    to_native(w.msg) for w in self.import_spec.warning
                ]

            if hasattr(self.import_spec, "fileItem") and self.import_spec.fileItem:
                check_mode_result["deployment_plan"]["files_to_upload"] = [
                    {
                        "path": item.path,
                        "size_bytes": item.size,
                        "device_id": item.deviceId,
                    }
                    for item in self.import_spec.fileItem
                ]
                check_mode_result["deployment_plan"]["total_size_bytes"] = sum(
                    item.size for item in self.import_spec.fileItem
                )

            self.module.exit_json(**check_mode_result)

        try:
            self.lease = resource_pool.ImportVApp(self.import_spec.importSpec, folder)
        except vmodl.fault.SystemError as err:
            self.module.fail_json(msg=f"Failed to start import: {to_native(err.msg)}")

        while self.lease.state != vim.HttpNfcLease.State.ready:
            time.sleep(0.1)

        self.entity = self.lease.info.entity

        return self.lease, self.import_spec

    def _normalize_url(self, url):
        """Normalize URLs from vCenter by replacing wildcard hostname.

        vCenter may return URLs with '*' as hostname, which needs to be
        replaced with the actual vCenter hostname.

        Args:
            url (str): URL to normalize.

        Returns:
            str: Normalized URL with correct hostname.
        """
        url_parts = generic_urlparse(urlparse(url))
        if url_parts.hostname == "*":
            if url_parts.port:
                url_parts.netloc = "%s:%d" % (self.params["hostname"], url_parts.port)
            else:
                url_parts.netloc = self.params["hostname"]

        return urlunparse(url_parts.as_list())

    def vm_existence_check(self):
        """Check if VM already exists and handle idempotency.

        If VM exists, returns existing VM facts with changed=False.
        In check mode, reports that VM exists without changes.
        If VM doesn't exist, allows deployment to proceed.

        Raises:
            AnsibleModule.exit_json: If VM already exists (idempotent case).
        """
        # In check mode, skip the VM existence check entirely to avoid vSphere API issues
        if self.module.check_mode:
            return

        vm_obj = self.get_vm()
        if vm_obj:
            vm_name = self.params.get("name")
            # Verify the VM object has the required runtime attribute
            if not hasattr(vm_obj, "runtime") or vm_obj.runtime is None:
                self.module.fail_json(
                    msg=f"Found VM '{vm_name}' but unable to access its runtime information. "
                        "The VM may be in an invalid state or vSphere connection may be incomplete."
                )
            self.entity = vm_obj
            facts = self.deploy()
            facts["changed"] = False
            facts["msg"] = (
                f"Virtual machine '{vm_name}' already exists; no changes made."
            )
            self.module.exit_json(**facts)

    def remove_vm(self):
        """Remove the virtual machine if it exists (state=absent).

        Handles complete virtual machine removal workflow.

        Raises:
            AnsibleModule.fail_json: If name parameter missing, virtual machine is powered on without force, or removal fails.
            AnsibleModule.exit_json: On successful removal or if virtual machine doesn't exist.
        """
        if not self.params.get("name"):
            self.module.fail_json(
                msg="Parameter 'name' is required when state is 'absent'."
            )

        vm_obj = find_vm_by_name(self.content, self.params["name"])

        vm_name = self.params["name"]
        if not vm_obj:
            no_exist_msg = f"VCF Installer appliance '{vm_name}' does not exist; no changes were performed."
            if self.module.check_mode:
                check_msg = f"Check Mode: {no_exist_msg}"
                self.module.exit_json(
                    changed=False, msg=check_msg, meta={"message": check_msg}
                )
            else:
                self.module.exit_json(
                    changed=False, msg=no_exist_msg, meta={"message": no_exist_msg}
                )

        if self.module.check_mode:
            vm_facts = gather_vm_facts(self.content, vm_obj)
            power_state = vm_obj.runtime.powerState
            if power_state == "poweredOn" and self.params.get("force", False):
                check_msg = f"Check Mode: Would power off and remove VCF Installer appliance '{vm_name}'; no changes were performed."
            else:
                check_msg = f"Check Mode: Would remove VCF Installer appliance '{vm_name}'; no changes were performed."
            self.module.exit_json(
                changed=True,
                msg=check_msg,
                instance=vm_facts,
                would_power_off=power_state == "poweredOn"
                                and self.params.get("force", False),
                meta={"message": check_msg},
            )

        power_state = vm_obj.runtime.powerState

        if power_state == "poweredOn":
            if not self.params.get("force", False):
                self.module.fail_json(
                    msg=f"VCF Installer appliance '{vm_name}' is powered on. Use 'force=true' to power off and remove."
                )
            try:
                task = vm_obj.PowerOff()
                wait_for_task(task)
            except Exception as e:
                self.module.fail_json(
                    msg=f"Failed to power off VCF Installer appliance '{vm_name}': {str(e)}"
                )

        try:
            task = vm_obj.Destroy_Task()
            wait_for_task(task)
            success_msg = f"Successfully removed VCF Installer appliance: '{vm_name}'."
            self.module.exit_json(
                changed=True, msg=success_msg, meta={"message": success_msg}
            )
        except Exception as e:
            self.module.fail_json(
                msg=f"Failed to remove VCF Installer appliance '{vm_name}': {str(e)}"
            )

    def upload(self):
        """Upload OVF/OVA files to vSphere.

        Handles two upload methods:
        1. URL-based: Uses HttpNfcLeasePullFromUrls for remote files.
        2. Local file: Uploads VMDK files using VmdkUploader threads.

        Raises:
            AnsibleModule.fail_json: If required files cannot be found or upload fails.
        """
        lease, import_spec = self.get_lease()

        # Path 1: URL
        if self.params["ovf"] is None:
            ssl_thumbprint = self.handle.thumbprint if self.handle.thumbprint else None

            # Build the Authorization header once if credentials were provided.
            auth_header = None
            if self.handle.username is not None:
                auth_kv = vim.KeyValue()
                auth_kv.key = "Authorization"
                auth_kv.value = _build_basic_auth_header(
                    self.handle.username, self.handle.password
                )
                auth_header = [auth_kv]

            source_files = []
            for file_item in import_spec.fileItem:
                source_file = vim.HttpNfcLease.SourceFile(
                    url=self.handle.url,
                    targetDeviceId=file_item.deviceId,
                    create=file_item.create,
                    size=file_item.size,
                    sslThumbprint=ssl_thumbprint,
                    memberName=file_item.path,
                )
                if auth_header:
                    source_file.httpHeaders = auth_header
                source_files.append(source_file)

            wait_for_task(lease.HttpNfcLeasePullFromUrls_Task(source_files))
            return

        # Path 2: Local file
        ovf_dir = os.path.dirname(self.params["ovf"])

        uploaders = []

        for file_item in import_spec.fileItem:
            device_upload_url = None
            for device_url in lease.info.deviceUrl:
                if file_item.deviceId == device_url.importKey:
                    device_upload_url = self._normalize_url(device_url.url)
                    break

            if not device_upload_url:
                lease.HttpNfcLeaseAbort(
                    vmodl.fault.SystemError(
                        reason=f"Failed to find deviceUrl for file '{file_item.path}'."
                    )
                )
                self.module.fail_json(
                    msg=f"Failed to find deviceUrl for file '{file_item.path}'."
                )

            vmdk_tarinfo = None
            if self.tar:
                # Local OVA – extract the file member from the tarfile.
                vmdk = self.tar
                try:
                    vmdk_tarinfo = self.tar.getmember(file_item.path)
                except KeyError:
                    lease.HttpNfcLeaseAbort(
                        vmodl.fault.SystemError(
                            reason=f"Failed to find VMDK file '{file_item.path}' in OVA."
                        )
                    )
                    self.module.fail_json(
                        msg=f"Failed to find VMDK file '{file_item.path}' in OVA."
                    )
            else:
                # Unpacked OVF directory – locate the companion VMDK file.
                vmdk = os.path.join(ovf_dir, file_item.path)
                try:
                    path_exists(vmdk)
                except ValueError:
                    lease.HttpNfcLeaseAbort(
                        vmodl.fault.SystemError(
                            reason=f"Failed to find VMDK file at '{vmdk}'."
                        )
                    )
                    self.module.fail_json(
                        msg=f"Failed to find VMDK file at '{vmdk}'."
                    )

            uploaders.append(
                VmdkUploader(
                    vmdk,
                    device_upload_url,
                    self.params["validate_certs"],
                    tarinfo=vmdk_tarinfo,
                    create=file_item.create,
                )
            )

        total_size = sum(u.size for u in uploaders)
        total_bytes_read = [0] * len(uploaders)
        for i, uploader in enumerate(uploaders):
            uploader.start()
            while uploader.is_alive():
                time.sleep(0.1)
                total_bytes_read[i] = uploader.bytes_read
                lease.HttpNfcLeaseProgress(
                    int(100.0 * sum(total_bytes_read) / total_size)
                )

            if uploader.e:
                lease.HttpNfcLeaseAbort(
                    vmodl.fault.SystemError(reason="%s" % to_native(uploader.e[1]))
                )
                self.module.fail_json(
                    msg="%s" % to_native(uploader.e[1]),
                    exception="".join(traceback.format_tb(uploader.e[2])),
                )

    def complete(self):
        """Complete the HTTP NFC lease after successful upload.

        Signals vCenter that all files have been uploaded successfully.
        Skips in check mode or if no lease exists.
        """
        if self.module.check_mode or not self.lease:
            return
        self.lease.HttpNfcLeaseComplete()

    def deploy(self):
        """Finalize VCF Installer deployment operations.

        Handles post-deployment tasks:
        - Powering on the virtual machine.
        - Waiting for IP address from the guest operating system.
        - Gathering the virtual machine facts.

        Returns:
            dict: Virtual machine facts including instance information.

        Raises:
            AnsibleModule.fail_json: If waiting for IP times out.
        """
        facts = {}

        if self.entity is None:
            self.module.fail_json(
                msg="Internal error: VM entity is not set. Cannot complete deployment operations."
            )

        if self.params["power_on"]:
            facts = set_vm_power_state(
                self.content, self.entity, "poweredon", force=False
            )
            if self.params["wait_for_ip_address"]:
                _facts = wait_for_vm_ip(self.content, self.entity)
                if not _facts:
                    self.module.fail_json(msg="Waiting for IP address timed out.")

        if not facts:
            facts.update(dict(instance=gather_vm_facts(self.content, self.entity)))

        return facts

    def validate_resources(self):
        """Validate that all required vSphere resources exist before deployment.

        This method checks for the existence of:
        - Datacenter
        - Cluster (or ESX host)
        - Datastore
        - Folder (if specified)
        - Network(s)

        Returns:
            dict: Validation results with structure:
                {
                    "validation": {
                        "valid": bool,
                        "datacenter": {"exists": bool, "id": str, "name": str},
                        "cluster": {"exists": bool, "id": str, "name": str},
                        "datastore": {"exists": bool, "id": str, "name": str},
                        "folder": {"exists": bool, "id": str, "path": str, "optional": bool},
                        "network": {"exists": bool, "id": str, "name": str}
                    },
                    "missing_resources": list
                }
        """
        validation = {
            "valid": True,
            "datacenter": {
                "exists": False,
                "id": None,
                "name": self.params.get("datacenter"),
            },
            "cluster": {
                "exists": False,
                "id": None,
                "name": self.params.get("cluster"),
            },
            "esx_host": {
                "exists": False,
                "id": None,
                "name": self.params.get("esx_hostname"),
            },
            "datastore": {
                "exists": False,
                "id": None,
                "name": self.params.get("datastore"),
            },
            "folder": {
                "exists": False,
                "id": None,
                "path": self.params.get("folder"),
                "optional": not bool(self.params.get("folder")),
            },
            "networks": {},
        }

        missing_resources = []
        datacenter_obj = None

        # Validate Datacenter
        try:
            datacenter_obj = self.find_datacenter_by_name(self.params["datacenter"])
            if datacenter_obj:
                validation["datacenter"]["exists"] = True
                validation["datacenter"]["id"] = str(datacenter_obj._moId)
            else:
                validation["valid"] = False
                missing_resources.append("datacenter")
                validation["datacenter"]["error"] = "Datacenter not found."
        except Exception as e:
            validation["valid"] = False
            missing_resources.append("datacenter")
            validation["datacenter"]["error"] = str(e)

        # Validate Cluster or ESX Host
        if self.params.get("cluster") and datacenter_obj:
            try:
                cluster_obj = self.find_cluster_by_name(
                    self.params["cluster"], datacenter_name=datacenter_obj
                )
                if cluster_obj:
                    validation["cluster"]["exists"] = True
                    validation["cluster"]["id"] = str(cluster_obj._moId)
                else:
                    validation["valid"] = False
                    missing_resources.append("cluster")
                    validation["cluster"]["error"] = "Cluster not found."
            except Exception as e:
                validation["valid"] = False
                missing_resources.append("cluster")
                validation["cluster"]["error"] = str(e)

        elif self.params.get("esx_hostname") and datacenter_obj:
            try:
                host_obj = self.find_hostsystem_by_name(
                    self.params["esx_hostname"], datacenter=datacenter_obj
                )
                if host_obj:
                    validation["esx_host"]["exists"] = True
                    validation["esx_host"]["id"] = str(host_obj._moId)
                else:
                    validation["valid"] = False
                    missing_resources.append("esx_host")
                    validation["esx_host"]["error"] = "ESX host not found."
            except Exception as e:
                validation["valid"] = False
                missing_resources.append("esx_host")
                validation["esx_host"]["error"] = str(e)

        # Validate Datastore
        if datacenter_obj:
            try:
                datastore_obj = self.find_datastore_by_name(
                    self.params["datastore"], datacenter_name=datacenter_obj
                )
                if datastore_obj:
                    validation["datastore"]["exists"] = True
                    validation["datastore"]["id"] = str(datastore_obj._moId)
                    validation["datastore"]["free_space_gb"] = round(
                        datastore_obj.summary.freeSpace / (1024 ** 3), 2
                    )
                    validation["datastore"]["capacity_gb"] = round(
                        datastore_obj.summary.capacity / (1024 ** 3), 2
                    )
                else:
                    validation["valid"] = False
                    missing_resources.append("datastore")
                    validation["datastore"]["error"] = "Datastore not found."
            except Exception as e:
                validation["valid"] = False
                missing_resources.append("datastore")
                validation["datastore"]["error"] = str(e)

        # Validate Folder
        if self.params.get("folder") and datacenter_obj:
            try:
                folder_obj = self.content.searchIndex.FindByInventoryPath(
                    self.params["folder"]
                )
                if folder_obj:
                    validation["folder"]["exists"] = True
                    validation["folder"]["id"] = str(folder_obj._moId)
                else:
                    if not validation["folder"]["optional"]:
                        validation["valid"] = False
                        missing_resources.append("folder")
                    validation["folder"]["error"] = "Folder not found."
            except Exception as e:
                if not validation["folder"]["optional"]:
                    validation["valid"] = False
                    missing_resources.append("folder")
                validation["folder"]["error"] = str(e)

        # Validate Networks
        if datacenter_obj:
            for ovf_network, vsphere_network in self.params.get("networks", {}).items():
                network_validation = {
                    "exists": False,
                    "id": None,
                    "ovf_name": ovf_network,
                    "vsphere_name": vsphere_network,
                }
                try:
                    networks = find_all_networks_by_name(
                        self.content, vsphere_network, datacenter=datacenter_obj
                    )
                    if networks and len(networks) > 0:
                        network_validation["exists"] = True
                        network_validation["id"] = str(networks[0]._moId)
                        if len(networks) > 1:
                            network_validation["note"] = (
                                f"Multiple networks found with name '{vsphere_network}'"
                            )
                    else:
                        validation["valid"] = False
                        missing_resources.append(f"network:{vsphere_network}")
                        network_validation["error"] = "Network not found."
                except Exception as e:
                    validation["valid"] = False
                    missing_resources.append(f"network:{vsphere_network}")
                    network_validation["error"] = str(e)

                validation["networks"][vsphere_network] = network_validation

        return {"validation": validation, "missing_resources": missing_resources}


def main():
    """Main entry point for the Ansible module.

    Defines module parameters, initializes the module, and executes the module logic.
    Handles parameter validation and orchestrates the module's workflow.
    """
    argument_spec = get_connection_spec()
    argument_spec.update(
        {
            "state": {
                "type": "str",
                "choices": ["present", "absent", "validate"],
                "default": "present",
            },
            "name": {"type": "str", "required": False},
            "datacenter": {"type": "str", "default": "ha-datacenter"},
            "cluster": {"type": "str"},
            "esx_hostname": {"type": "str"},
            "datastore": {"type": "str", "default": "datastore1"},
            "folder": {"type": "str"},
            "resource_pool": {"type": "str", "default": "Resources"},
            "ovf": {"type": "path", "aliases": ["ova"]},
            "url": {"type": "str"},
            "url_username": {"type": "str"},
            "url_password": {"type": "str", "no_log": True},
            "networks": {
                "type": "dict",
                "default": {"Network 1": "VM Network"},
            },
            "properties": {"type": "dict"},
            "disk_provisioning": {
                "type": "str",
                "choices": ["thin", "thick", "eagerZeroedThick"],
                "default": "thin",
            },
            "power_on": {"type": "bool", "default": True},
            "wait_for_ip_address": {"type": "bool", "default": True},
            "force": {"type": "bool", "default": False},
            "allow_duplicates": {"type": "bool", "default": False},
            "fail_on_spec_warnings": {"type": "bool", "default": False},
        }
    )

    required_if = [
        ["state", "present", ["ovf", "url"], True],
        ["state", "present", ["name"], False],
        ["state", "absent", ["name"], False],
    ]

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=required_if,
        mutually_exclusive=[["cluster", "esx_hostname"], ["ovf", "url"]],
    )

    deploy_ovf = OvfDeploymentHandler(module)

    # Handle validate state
    if module.params["state"] == "validate":
        result = deploy_ovf.validate_resources()
        validation_msg = "vSphere resource validation completed."
        if result["validation"]["valid"]:
            validation_msg += " All resources exist and are accessible."
        else:
            validation_msg += f" Missing or inaccessible resources: {', '.join(result['missing_resources'])}"

        result.update({"changed": False, "msg": validation_msg})
        module.exit_json(**result)
        return

    # Handle absent state
    if module.params["state"] == "absent":
        deploy_ovf.remove_vm()
        return

    # Handle present state
    deploy_ovf.vm_existence_check()
    deploy_ovf.upload()
    deploy_ovf.complete()

    facts = deploy_ovf.deploy()
    vm_name = module.params.get("name", "VCF Installer")
    success_msg = f"Successfully deployed VCF Installer appliance: '{vm_name}'."
    facts.update(changed=True, msg=success_msg)
    module.exit_json(**facts)


if __name__ == "__main__":
    main()
