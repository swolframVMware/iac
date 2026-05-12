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

import atexit
import logging
import ssl

import requests
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim


class EsxHost:
    """A class for interacting with ESX.

    Args:
        esx_hostname (str):
            The hostname of the ESX Host.
        esx_host_user (str):
            The username to authenticate with the ESX host.
        esx_host_password (str):
            The password to authenticate with the ESX host.
        ssl_verify (bool, optional):
            Whether to verify the SSL certificate of the ESX host. Defaults to False.
        logger (logging.Logger, optional):
            The logger to use for logging. Defaults to None.

    Raises:
        Exception:
            All built-in, non-system-exiting exceptions are derived from this class.
            All user-defined exceptions should also be derived from this class.
        ValueError:
            Raised when an operation or function receives an argument that has the
            right type but an inappropriate value.

    Attributes:
        esx_hostname (str):
            The hostname of the ESX Host.
        esx_host_user (str):
            The username to authenticate with the ESX host.
        esx_host_password (str):
            The password to authenticate with the ESX host.
        api_extension (str):
            The API extension to use for making API requests.
        url (str):
            The URL of the ESX Host.
        logger (logging.Logger):
            The logger to use for logging.
        ssl_verify (bool):
            Whether to verify the SSL certificate of the ESX host.

    Methods:
        get_connection:
            Connects to the ESX Host using the provided credentials.
        can_connect:
            Checks if the connection can be established to the ESX host using the provided credentials.
        get_esx_content:
            Retrieves the content for an ESX host.
        check_esx_ui:
            Checks the accesibility of the ESX host user interface.
        filter_esx_host_by_name:
            Filters and retrieves the ESX host that matches the given hostname from the
            vSphere inventory.
        get_service_manager:
            Retrieves the service manager for managing services on an ESX host.
        get_service_status:
            Retrieves the service details for a specific service on an ESX host.
        get_date_time_manager:
            Retrieves the Date Time Manager for NTP configuration on an ESX host.
        configure_ntp_servers:
            Configures NTP servers on an ESX host.
        get_certificate_common_name:
            Retrieves the common name from the ESX host certificate.
        filter_virtual_standard_switch_by_name:
            Retrieves a specific standard switch from an ESX host.
        get_virtual_standard_switch_mtu:
            Retrieves the MTU value for a specific standard switch on an ESX host.
        update_virtual_standard_switch_mtu:
            Updates the MTU value for a specific standard switch on the ESX host.
    """

    def __init__(
        self,
        esx_hostname: str,
        esx_host_user: str,
        esx_host_password: str,
        ssl_verify: bool = False,
        logger: logging.Logger = None,
    ):
        self.esx_hostname = esx_hostname
        self.esx_host_user = esx_host_user
        self.esx_host_password = esx_host_password
        self.url = f"https://{self.esx_hostname}"
        self.logger = logger or logging.getLogger(__name__)
        self.ssl_verify = ssl_verify
        if not self.ssl_verify:
            requests.packages.urllib3.disable_warnings()
            self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            self.ssl_context.verify_mode = ssl.CERT_NONE

    # =============================================================================
    # Connection
    # =============================================================================
    def get_connection(self, host: str, username: str, password: str, port: int):
        """Connects to the ESX Host using the provided credentials."""
        try:
            esx_connection = SmartConnect(
                host=host,
                user=username,
                pwd=password,
                port=port,
                sslContext=self.ssl_context,
            )
            atexit.register(Disconnect, esx_connection)
            return esx_connection
        except Exception as err:
            raise Exception(f"Failed to connect to ESX host {host}: {err}")

    def can_connect(self, host: str, username: str, password: str, port: int):
        """Checks if the connection can be established to the ESX host using the
        provided credentials."""
        try:
            self.get_connection(host, username, password, port)
            return True
        except Exception:
            return False

    def get_esx_content(self, host: str, username: str, password: str, port: int):
        """Retrieves the content for an ESX host."""
        esx_connection = self.get_connection(host, username, password, port)
        return esx_connection.RetrieveContent()

    # =============================================================================
    # User Interface
    # =============================================================================
    def check_esx_ui(self):
        """Checks the accesibility of the ESX host user interface."""
        try:
            response = requests.get(f"{self.url}/ui", verify=self.ssl_verify)
            return response.status_code == 200
        except Exception:
            # Handle any request exceptions (e.g., connection errors, timeouts)
            return False

    # =============================================================================
    # Host Filtering
    # =============================================================================
    def filter_esx_host_by_name(self, content: dict):
        """Retrieves specific ESX host from an inventory."""
        # Get the ESX host object list.
        mob_list = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.HostSystem], True
        )

        # Use filter() to find the matching ESX host.
        # list(filter(...)) converts the filtered iterable into a list. If mob.name == self.esx_hostname, that host is
        # kept in the list. If it doesn't match, filter() excludes it from the list.
        filtered_hosts = list(
            filter(lambda mob: mob.name == self.esx_hostname, mob_list.view)
        )

        if not filtered_hosts:  # ESX host not found.
            raise Exception(f"ESX host '{self.esx_hostname}' not found!")
        else:
            return filtered_hosts[
                0
            ]  # Returning element 0 since there should only be 1 now.

    # =============================================================================
    # Services
    # =============================================================================
    def get_service_manager(self, content: dict):
        """Retrieves the service manager for managing services on an ESX host."""
        mob = self.filter_esx_host_by_name(content)

        return mob.configManager.serviceSystem

    def get_service_status(self, service_manager: dict, service_name: str):
        """Retrieves the service details for a specific service on an ESX host."""
        service_details = list(
            filter(lambda s: s.key == service_name, service_manager.serviceInfo.service)
        )

        return service_details

    # =============================================================================
    # NTP
    # =============================================================================
    def get_date_time_manager(self, content: dict):
        """Retrieves the Date Time Manager for NTP configuration on an ESX host."""
        mob = self.filter_esx_host_by_name(content)

        return mob.configManager.dateTimeSystem

    def configure_ntp_servers(self, date_time_manager: dict, ntp_servers: list):
        """Configures NTP servers on an ESX host."""
        try:
            ntp_config = vim.HostNtpConfig(server=ntp_servers)
            date_config = vim.HostDateTimeConfig(ntpConfig=ntp_config)
            date_time_manager.UpdateDateTimeConfig(config=date_config)
        except vim.fault.HostConfigFault:
            raise ValueError(
                f"Invalid NTP server(s) provided! Please check NTP server(s) provided '{ntp_servers}' and verify they are correct!"
            )
        except Exception as ntp_error:
            raise Exception(f"Unexpected error occured. Error: {ntp_error}")

    # =============================================================================
    # Certificates
    # =============================================================================
    def get_certificate_common_name(self, content: dict):
        """Retrieves the common name from the ESX host certificate."""
        mob = self.filter_esx_host_by_name(content)
        subject_list = (
            mob.configManager.certificateManager.certificateInfo.subject.split(",")
        )

        # Use filter() to find the matching cert subjects and map() to strip whitespace and remove the 'CN=' prefix
        #   from each filter(...) returns an iterable of subjects that contain 'CN=' — only those are kept
        # map(...) applies a transformation to each item in the filtered iterable: strips whitespace and removes 'CN='
        # list(...) collects the results from map into a final list of cleaned CN values
        filtered_cn = list(
            map(
                lambda sub: sub.strip().removeprefix("CN="),
                filter(lambda sub: "CN=" in sub, subject_list),
            )
        )

        if not filtered_cn:  # CN not found
            raise Exception(
                f"Unable to find certificate information for ESX host {self.esx_hostname}."
            )
        else:
            return filtered_cn[0]

    # =============================================================================
    # Standard Switches
    # =============================================================================
    def filter_virtual_standard_switch_by_name(
        self, virtual_standard_switch: dict, content: dict
    ):
        """Retrieves a specific standard switch from an ESX host."""
        mob = self.filter_esx_host_by_name(content)

        # Retrieve the virtual standard switch list safely.
        switches = getattr(mob.config.network, "vswitch", [])

        # Use filter() to find the matching standard switch.
        # list(filter(...)) converts the filtered iterable into a list. If v.name == virtual_standard_switch['name'],
        # that switch is kept in the list. If it doesn't match, filter() excludes it from the list.
        filtered_switches = list(
            filter(lambda v: v.name == virtual_standard_switch["name"], switches)
        )

        if not filtered_switches:  # Standard switch not found.
            raise Exception(
                f"Standard switch '{virtual_standard_switch['name']}' was not found on host '{self.esx_hostname}'."
            )
        elif (
            len(filtered_switches) > 1
        ):  # One or more standard switches found with the same name.
            raise Exception(
                f"Duplicate standard switches named '{virtual_standard_switch['name']}' were found on host '{self.esx_hostname}'."
            )
        else:
            return filtered_switches[
                0
            ]  # Returning element 0 since there should only be 1 now.

    def get_virtual_standard_switch_mtu(
        self, virtual_standard_switch: dict, content: dict
    ):
        """Retrieves the MTU value for a specific standard switch on an ESX host."""
        filtered_switch = self.filter_virtual_standard_switch_by_name(
            virtual_standard_switch, content
        )

        return {"name": filtered_switch.name, "mtu": filtered_switch.spec.mtu}

    def update_virtual_standard_switch_mtu(
        self, virtual_standard_switch: dict, content: dict
    ):
        """Updates the MTU value for a specific standard switch on the ESX host."""
        mob = self.filter_esx_host_by_name(content)
        filtered_switch = self.filter_virtual_standard_switch_by_name(
            virtual_standard_switch, content
        )

        try:
            # Create a new specification object.
            vswitch_spec = filtered_switch.spec
            vswitch_spec.mtu = virtual_standard_switch["mtu"]
            # Apply the updated specification.
            mob.configManager.networkSystem.UpdateVirtualSwitch(
                vswitchName=filtered_switch.name, spec=vswitch_spec
            )
        except (
            vim.fault.PlatformConfigFault
        ) as vss_update_mtu_error:  # Integer value out of range.
            error_details_full = list(
                filter(
                    lambda msg: msg.key == "com.vmware.esx.hostctl.default",
                    vss_update_mtu_error.faultMessage,
                )
            )
            raise ValueError(
                f"{error_details_full[0].message.split(':')[1]}. MTU provided: {virtual_standard_switch['mtu']}"
            )
        except Exception as vss_update_mtu_error:
            raise Exception(f"Failed to update MTU! Error: {vss_update_mtu_error}")
