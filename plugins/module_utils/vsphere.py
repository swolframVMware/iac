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

"""VMware/vSphere utility functions for Ansible modules.

This module provides common utilities for interacting with vCenter Server and ESXi hosts
using PyVmomi. It includes functions for:
- Connecting to vSphere APIs
- Finding vSphere objects (datacenter, cluster, host, datastore, network, VM)
- Managing virtual machines (power state, facts, IP waiting)
- Task management
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import time
import atexit
from ansible.module_utils.basic import env_fallback

try:
    from pyVim import connect
    from pyVmomi import vim, vmodl

    HAS_PYVMOMI = True
except ImportError:
    HAS_PYVMOMI = False
    vim = None
    vmodl = None


def get_connection_spec():
    """Return the argument specification for VMware modules.

    Returns:
        dict: Dictionary containing common VMware connection parameters including
              hostname, username, password, port, and validate_certs with appropriate
              fallbacks to environment variables.
    """
    return dict(
        hostname=dict(
            type="str", required=True, fallback=(env_fallback, ["VMWARE_HOST"])
        ),
        username=dict(
            type="str", required=True, fallback=(env_fallback, ["VMWARE_USER"])
        ),
        password=dict(
            type="str",
            required=True,
            no_log=True,
            fallback=(env_fallback, ["VMWARE_PASSWORD"]),
        ),
        port=dict(type="int", default=443, fallback=(env_fallback, ["VMWARE_PORT"])),
        validate_certs=dict(
            type="bool",
            default=True,
            fallback=(env_fallback, ["VMWARE_VALIDATE_CERTS"]),
        ),
    )


def connect_to_api(module, disconnect_atexit=True, return_si=False):
    """Connect to vCenter or ESXi host API.

    Args:
        module (AnsibleModule): The Ansible module instance containing connection parameters.
        disconnect_atexit (bool, optional): Whether to register disconnect at exit. Defaults to True.
        return_si (bool, optional): Whether to return ServiceInstance or content. Defaults to False.

    Returns:
        ServiceInstance or ServiceContent: Returns ServiceInstance if return_si=True,
                                          otherwise returns ServiceContent object.

    Raises:
        AnsibleModule.fail_json: If connection fails or credentials are invalid.
    """
    hostname = module.params["hostname"]
    username = module.params["username"]
    password = module.params["password"]
    port = module.params.get("port", 443)
    validate_certs = module.params.get("validate_certs", True)

    if not HAS_PYVMOMI:
        module.fail_json(msg="PyVmomi is required for this module")

    try:
        service_instance = connect.SmartConnect(
            host=hostname,
            user=username,
            pwd=password,
            port=port,
            disableSslCertValidation=not validate_certs,
        )
        if disconnect_atexit:
            atexit.register(connect.Disconnect, service_instance)
        if return_si:
            return service_instance
        return service_instance.RetrieveContent()
    except vim.fault.InvalidLogin as e:
        module.fail_json(msg=f"Unable to log on to vSphere API: {e.msg}")
    except Exception as e:
        module.fail_json(msg=f"Unable to connect to vSphere API: {str(e)}")


def wait_for_task(task):
    """Wait for a vCenter task to complete.

    Args:
        task: vSphere task object to monitor.

    Returns:
        Any: Task result if successful.

    Raises:
        Exception: Task error if task fails.
    """
    while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
        time.sleep(0.5)
    if task.info.state == vim.TaskInfo.State.error:
        raise task.info.error
    return task.info.result


def find_obj(content, vimtype, name, folder=None):
    """Find a vSphere managed object by name and type.

    Args:
        content (ServiceContent): vSphere service content object.
        vimtype: The vSphere object type to search for (e.g., vim.Datacenter).
        name (str): Name of the object to find.
        folder (optional): Folder to search within. Defaults to None (search all).

    Returns:
        ManagedObject or None: The found object or None if not found.
    """
    if folder is None:
        folder = content.rootFolder
    container = content.viewManager.CreateContainerView(folder, [vimtype], True)
    try:
        for obj in container.view:
            if obj.name == name:
                return obj
        return None
    finally:
        container.Destroy()


def find_datacenter_by_name(content, datacenter_name):
    """Find a datacenter by name.

    Args:
        content (ServiceContent): vSphere service content object.
        datacenter_name (str): Name of the datacenter.

    Returns:
        vim.Datacenter or None: Datacenter object or None if not found.
    """
    return find_obj(content, vim.Datacenter, datacenter_name)


def find_cluster_by_name(content, cluster_name, datacenter=None):
    """Find a cluster by name.

    Args:
        content (ServiceContent): vSphere service content object.
        cluster_name (str): Name of the cluster.
        datacenter (vim.Datacenter, optional): Datacenter to search within. Defaults to None.

    Returns:
        vim.ClusterComputeResource or None: Cluster object or None if not found.
    """
    folder = datacenter.hostFolder if datacenter else content.rootFolder
    return find_obj(content, vim.ClusterComputeResource, cluster_name, folder)


def find_hostsystem_by_name(content, hostname, datacenter=None):
    """Find an ESXi host by name.

    Args:
        content (ServiceContent): vSphere service content object.
        hostname (str): Name of the ESXi host.
        datacenter (vim.Datacenter, optional): Datacenter to search within. Defaults to None.

    Returns:
        vim.HostSystem or None: Host system object or None if not found.
    """
    folder = datacenter.hostFolder if datacenter else content.rootFolder
    return find_obj(content, vim.HostSystem, hostname, folder)


def find_datastore_by_name(content, datastore_name, datacenter=None):
    """Find a datastore by name.

    Args:
        content (ServiceContent): vSphere service content object.
        datastore_name (str): Name of the datastore.
        datacenter (vim.Datacenter, optional): Datacenter to search within. Defaults to None.

    Returns:
        vim.Datastore or None: Datastore object or None if not found.
    """
    folder = datacenter.datastoreFolder if datacenter else content.rootFolder
    return find_obj(content, vim.Datastore, datastore_name, folder)


def find_datastore_cluster_by_name(content, datastore_cluster_name, datacenter=None):
    """Find a datastore cluster by name.

    Args:
        content (ServiceContent): vSphere service content object.
        datastore_cluster_name (str): Name of the datastore cluster.
        datacenter (vim.Datacenter, optional): Datacenter to search within. Defaults to None.

    Returns:
        vim.StoragePod or None: Datastore cluster object or None if not found.
    """
    folder = datacenter.datastoreFolder if datacenter else content.rootFolder
    return find_obj(content, vim.StoragePod, datastore_cluster_name, folder)


def find_resource_pool_by_name(content, resource_pool_name, folder=None):
    """Find a resource pool by name.

    Args:
        content (ServiceContent): vSphere service content object.
        resource_pool_name (str): Name of the resource pool.
        folder (optional): Folder to search within. Defaults to None.

    Returns:
        vim.ResourcePool or None: Resource pool object or None if not found.
    """
    return find_obj(content, vim.ResourcePool, resource_pool_name, folder)


def find_resource_pool_by_cluster(content, resource_pool_name, cluster):
    """Find a resource pool within a specific cluster.

    Args:
        content (ServiceContent): vSphere service content object.
        resource_pool_name (str): Name of the resource pool.
        cluster (vim.ClusterComputeResource): Cluster to search within.

    Returns:
        vim.ResourcePool or None: Resource pool object or None if not found.
    """
    if resource_pool_name == "Resources":
        return cluster.resourcePool
    return find_resource_pool_by_name(content, resource_pool_name, cluster)


def find_network_by_name(content, network_name, datacenter=None):
    """Find a network by name (returns first match).

    Args:
        content (ServiceContent): vSphere service content object.
        network_name (str): Name of the network.
        datacenter (vim.Datacenter, optional): Datacenter to search within. Defaults to None.

    Returns:
        vim.Network or None: Network object or None if not found.
    """
    folder = datacenter.networkFolder if datacenter else content.rootFolder
    return find_obj(content, vim.Network, network_name, folder)


def find_all_networks_by_name(content, network_name, datacenter=None):
    """Find all networks matching a given name.

    Args:
        content (ServiceContent): vSphere service content object.
        network_name (str): Name of the network.
        datacenter (vim.Datacenter, optional): Datacenter to search within. Defaults to None.

    Returns:
        list: List of network objects matching the name.
    """
    folder = datacenter.networkFolder if datacenter else content.rootFolder
    container = content.viewManager.CreateContainerView(folder, [vim.Network], True)
    networks = []
    try:
        for network in container.view:
            if network.name == network_name:
                networks.append(network)
        return networks
    finally:
        container.Destroy()


def find_vm_by_name(content, vm_name, folder=None):
    """Find a virtual machine by name.

    Args:
        content (ServiceContent): vSphere service content object.
        vm_name (str): Name of the virtual machine.
        folder (optional): Folder to search within. Defaults to None.

    Returns:
        vim.VirtualMachine or None: Virtual machine object or None if not found.
    """
    return find_obj(content, vim.VirtualMachine, vm_name, folder)


def gather_vm_facts(content, vm):
    """Gather facts about a virtual machine.

    Args:
        content (ServiceContent): vSphere service content object.
        vm (vim.VirtualMachine): Virtual machine object.

    Returns:
        dict: Dictionary containing VM facts including name, power state, guest info,
              network information, CPU, memory, and other properties.
    """
    facts = {
        "hw_name": vm.config.name,
        "hw_power_status": vm.runtime.powerState,
        "hw_guest_full_name": vm.config.guestFullName,
        "hw_guest_id": vm.config.guestId,
        "hw_product_uuid": vm.config.uuid,
        "instance_uuid": vm.config.instanceUuid,
        "hw_processor_count": vm.config.hardware.numCPU,
        "hw_memtotal_mb": vm.config.hardware.memoryMB,
    }
    if vm.guest and vm.guest.ipAddress:
        facts["ipv4"] = vm.guest.ipAddress
    if vm.guest and vm.guest.net:
        facts["hw_interfaces"] = []
        for nic in vm.guest.net:
            if nic.ipConfig and nic.ipConfig.ipAddress:
                for ip_addr in nic.ipConfig.ipAddress:
                    facts["hw_interfaces"].append(ip_addr.ipAddress)
    return facts


def wait_for_vm_ip(content, vm, timeout=300):
    """Wait for a virtual machine to obtain an IP address.

    Args:
        content (ServiceContent): vSphere service content object.
        vm (vim.VirtualMachine): Virtual machine object.
        timeout (int, optional): Maximum time to wait in seconds. Defaults to 300.

    Returns:
        dict or None: Dictionary with ipv4 key if obtained within timeout, None otherwise.
    """
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        if vm.guest and vm.guest.ipAddress:
            return {"ipv4": vm.guest.ipAddress}
        time.sleep(2)
    return None


def set_vm_power_state(content, vm, state, force=False):
    """Set the power state of a virtual machine.

    Args:
        content (ServiceContent): vSphere service content object.
        vm (vim.VirtualMachine): Virtual machine object.
        state (str): Desired power state ('poweredon' or 'poweredoff').
        force (bool, optional): Force the power operation. Defaults to False.

    Returns:
        dict: Dictionary containing result information with changed status and instance facts.
    """
    if vm is None:
        raise ValueError(
            "VM object is None. Cannot set power state on a non-existent VM."
        )

    if not hasattr(vm, "runtime") or vm.runtime is None:
        raise ValueError(
            f"VM object does not have valid runtime information. VM may be in an invalid state."
        )

    current_state = vm.runtime.powerState
    if state == "poweredon":
        if current_state == "poweredOn":
            return {"changed": False, "instance": gather_vm_facts(content, vm)}
        task = vm.PowerOn()
        wait_for_task(task)
    elif state == "poweredoff":
        if current_state == "poweredOff":
            return {"changed": False, "instance": gather_vm_facts(content, vm)}
        task = vm.PowerOff() if force else vm.ShutdownGuest()
        wait_for_task(task)
    elif state == "restarted":
        task = vm.Reset() if force else vm.RebootGuest()
        wait_for_task(task)
    elif state == "suspended":
        if current_state == "suspended":
            return {"changed": False, "instance": gather_vm_facts(content, vm)}
        task = vm.Suspend()
        wait_for_task(task)
    return {"changed": True, "instance": gather_vm_facts(content, vm)}


class PyVmomi:
    """Base class for PyVmomi operations.

    Provides common methods for vSphere object lookup operations.
    All methods wrap the module-level functions for convenience.
    """

    def __init__(self, module):
        """Initialize PyVmomi base class.

        Args:
            module (AnsibleModule): Ansible module instance.

        Raises:
            AnsibleModule.fail_json: If PyVmomi is not installed.
        """
        self.module = module
        self.si = None
        self.content = None
        if not HAS_PYVMOMI:
            module.fail_json(msg="PyVmomi Python module required")
        self.content = connect_to_api(module, return_si=False)
        self.si = connect_to_api(module, return_si=True, disconnect_atexit=False)

    def find_datacenter_by_name(self, datacenter_name):
        """Find datacenter by name."""
        return find_datacenter_by_name(self.content, datacenter_name)

    def find_cluster_by_name(self, cluster_name, datacenter_name=None):
        """Find cluster by name."""
        datacenter = None
        if datacenter_name:
            datacenter = (
                datacenter_name
                if not isinstance(datacenter_name, str)
                else find_datacenter_by_name(self.content, datacenter_name)
            )
        return find_cluster_by_name(self.content, cluster_name, datacenter)

    def find_hostsystem_by_name(self, hostname, datacenter=None):
        """Find ESXi host by name."""
        return find_hostsystem_by_name(self.content, hostname, datacenter)

    def find_datastore_by_name(self, datastore_name, datacenter_name=None):
        """Find datastore by name."""
        datacenter = None
        if datacenter_name:
            datacenter = (
                datacenter_name
                if not isinstance(datacenter_name, str)
                else find_datacenter_by_name(self.content, datacenter_name)
            )
        return find_datastore_by_name(self.content, datastore_name, datacenter)

    def find_datastore_cluster_by_name(self, datastore_cluster_name, datacenter=None):
        """Find datastore cluster by name."""
        return find_datastore_cluster_by_name(
            self.content, datastore_cluster_name, datacenter
        )

    def find_resource_pool_by_name(self, resource_pool_name, folder=None):
        """Find resource pool by name."""
        return find_resource_pool_by_name(self.content, resource_pool_name, folder)

    def find_resource_pool_by_cluster(self, resource_pool_name, cluster):
        """Find resource pool within a cluster."""
        return find_resource_pool_by_cluster(self.content, resource_pool_name, cluster)

    def find_network_by_name(self, network_name, datacenter=None):
        """Find network by name (first match)."""
        return find_network_by_name(self.content, network_name, datacenter)

    def find_all_networks_by_name(self, network_name, datacenter=None):
        """Find all networks matching name."""
        return find_all_networks_by_name(self.content, network_name, datacenter)

    def get_vm(self):
        """Get VM by name from module params."""
        if "name" in self.module.params and self.module.params["name"]:
            return find_vm_by_name(self.content, self.module.params["name"])
        return None
