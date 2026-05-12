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

import logging
import json
from json import JSONDecodeError
from typing import Dict, Optional
from datetime import datetime, timedelta

import requests
from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)

API_VERSION = "v1"
AUTH_RESPONSE_FIELD = "accessToken"
TOKEN_CACHE_MAX_AGE_MINUTES = 50
HTTP_SUCCESS_MIN = 200
HTTP_SUCCESS_MAX = 299


class VcfInstallerApiClient:
    """A class representing a client for interacting with the VCF Installer API.

    Args:
        vcf_installer_hostname (str): The hostname or IP address of the VCF Installer instance.
        vcf_installer_user (str): The username for authenticating with the VCF Installer instance.
        vcf_installer_password (str): The password for authenticating with the VCF Installer instance.
        ssl_verify (bool, optional): Whether to verify SSL certificates. Defaults to
            False.
        logger (logging.Logger, optional): The logger object for logging. Defaults to
            None.

    Raises:
        VcfApiException: If an error occurs during the API call.

    Methods:
        Token Operations:
            get_vcf_installer_token: Retrieves the access token for authenticating with the VCF Installer instance.

        Appliance Information:
            get_appliance_info: Retrieves the VCF Installer appliance information.

        Task Operations:
            get_tasks: Retrieves all tasks.
            get_task_by_id: Retrieves a task by its resource ID.
            cancel_task_by_id: Cancels a task by its resource ID.
            retry_task_by_id: Retry a task by its resource ID.

        SDDC Operations:
            create_sddc: Creates an SDDC from a provided configuration.
            get_sddc: Retrieves information about an SDDC.

        Validation Operations:
            validate_sddc: Validates an SDDC configuration.
            get_sddc_validation: Retrieves information about an SDDC validation.

        Retry Operations:
            retry_sddc: Retries an SDDC deployment operation.
            retry_sddc_validation: Retries an SDDC validation operation.

        CEIP Operations:
            get_ceip_status: Retrieves CEIP (Customer Experience Improvement Program) status.
            update_ceip_status: Updates CEIP (Customer Experience Improvement Program) status.

        System Configuration Operations::
            get_depot_settings: Retrieves the depot configuration.
            get_depot_settings_machine_details: Retrieves the machine details from the depot configuration.
            update_depot_settings: Updates the depot configuration.
            delete_depot_settings: Deletes the depot configuration.
            get_depot_sync_info: Retrieves the depot sync information.
            sync_depot_metadata: Syncs depot metadata such as bundle manifest.
            get_proxy_configuration: Retrieves the current proxy configuration.
            update_proxy_configuration: Updates the proxy configuration.

        Bundle Operations:
            get_bundles: Retrieves a list of bundles with optional filters.
            get_bundle_by_id: Retrieves a specific bundle by its ID.
            get_bundle_download_status: Retrieves download status of bundles for a
                specific release.
            download_bundle: Starts, schedules, or cancels a bundle download.
            delete_bundle: Deletes a bundle by its ID.

        Trusted Certificate Operations:
            get_trusted_certificates: Retrieves all trusted certificates from the appliance.
            add_trusted_certificate: Adds a trusted certificate to the appliance's trust store.
            delete_trusted_certificate: Deletes a trusted certificate from the appliance's trust store by alias.
    """

    def __init__(
        self,
        vcf_installer_hostname: str,
        vcf_installer_user: str,
        vcf_installer_password: str,
        ssl_verify: bool = False,
        logger: Optional[logging.Logger] = None,
    ):
        self.vcf_installer_hostname = vcf_installer_hostname
        self.vcf_installer_user = vcf_installer_user
        self.vcf_installer_password = vcf_installer_password
        self.url = f"https://{self.vcf_installer_hostname}/{API_VERSION}"
        self.logger = logger or logging.getLogger(__name__)
        self.ssl_verify = ssl_verify
        if not self.ssl_verify:
            requests.packages.urllib3.disable_warnings()

        # Token caching attributes
        self._cached_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._token_lifetime_minutes: int = TOKEN_CACHE_MAX_AGE_MINUTES

    # =============================================================================
    # VCF Installer: Token
    # =============================================================================

    def get_vcf_installer_token(self) -> str:
        """Retrieves the access token for authenticating with the VCF Installer instance.

        Returns:
            str: The access token.

        Raises:
            VcfApiException: If token retrieval fails.
        """

        if self._cached_token and self._token_expiry:
            if datetime.now() < self._token_expiry:
                return self._cached_token

        token_url = f"{self.url}/tokens"
        headers = {"Content-Type": "application/json"}
        body = {
            "username": self.vcf_installer_user,
            "password": self.vcf_installer_password,
        }

        try:
            response = requests.post(
                url=token_url,
                headers=headers,
                json=body,
                verify=self.ssl_verify,
            )
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed during token acquisition: {e}")
            raise VcfApiException(f"Error: {e}")

        if not self._is_success_status(response.status_code):
            raise VcfApiException(f"{response.status_code}: {response.reason}")

        try:
            data_out = response.json()
        except (ValueError, JSONDecodeError) as e:
            self.logger.error("Failed to parse JSON response for token")
            raise VcfApiException("Bad JSON in response") from e

        if AUTH_RESPONSE_FIELD not in data_out:
            raise VcfApiException(
                f"Response missing required key: {AUTH_RESPONSE_FIELD}"
            )

        self._cached_token = data_out[AUTH_RESPONSE_FIELD]
        self._token_expiry = datetime.now() + timedelta(
            minutes=self._token_lifetime_minutes
        )

        return self._cached_token

    # =============================================================================
    # VCF Installer: Appliance Information
    # =============================================================================

    def get_appliance_info(self) -> Dict:
        """Retrieves the VCF Installer appliance information.

        Returns:
            dict: Appliance information containing:
                - role (str): Appliance role (e.g., "VcfInstaller", "SddcManager")
                - version (str): Appliance version (e.g., "9.0.2.0.25151285")

        Raises:
            VcfApiException: If the request fails.
        """
        return self._api_request("GET", "system/appliance-info")

    # =============================================================================
    # SDDC Manager: Tasks Operations
    # =============================================================================

    def get_tasks(self) -> Dict:
        """Retrieves all tasks.

        Returns:
            Dict: All tasks information.
        """
        return self._api_request("GET", "tasks")

    def get_task_by_id(self, resource_id: str) -> Dict:
        """Retrieves a task by its resource ID.

        Args:
            resource_id (str): The ID of the task.

        Returns:
            Dict: The task information.
        """
        return self._api_request("GET", f"tasks/{resource_id}")

    def cancel_task_by_id(self, resource_id: str) -> Dict:
        """Cancels a task by its resource ID.

        Args:
            resource_id (str): The ID of the task to cancel.

        Returns:
            Dict: The cancellation result.
        """
        return self._api_request("DELETE", f"tasks/{resource_id}")

    def retry_task_by_id(self, resource_id: str) -> Dict:
        """Retry a task by its resource ID.

        Args:
            resource_id (str): The ID of the task to retry.

        Returns:
            Dict: The retry result.
        """
        return self._api_request("PATCH", f"tasks/{resource_id}")

    # =============================================================================
    # VCF Installer: SDDC Operations
    # =============================================================================

    def create_sddc(self, body: str) -> Dict:
        """Creates an SDDC from a provided configuration.

        Args:
            body (str): The SDDC configuration as a JSON string.

        Returns:
            Dict: The created SDDC information.
        """
        return self._api_request("POST", "sddcs", body)

    def get_sddc(self, sddc_id: str) -> Dict:
        """Retrieves information about an SDDC.

        Args:
            sddc_id (str): The ID of the SDDC.

        Returns:
            Dict: The SDDC information.
        """
        return self._api_request("GET", f"sddcs/{sddc_id}")

    # =============================================================================
    # VCF Installer: Validation Operations
    # =============================================================================

    def validate_sddc(self, body: str) -> Dict:
        """Validates an SDDC configuration.

        Args:
            body (str): The SDDC configuration to validate as a JSON string.

        Returns:
            Dict: The validation result.
        """
        return self._api_request("POST", "sddcs/validations", body)

    def get_sddc_validation(self, sddc_id: str) -> Dict:
        """Retrieves information about an SDDC validation.

        Args:
            sddc_id (str): The ID of the SDDC validation.

        Returns:
            Dict: The SDDC validation information.
        """
        return self._api_request("GET", f"sddcs/validations/{sddc_id}")

    # =============================================================================
    # VCF Installer: Retry Operations
    # =============================================================================

    def retry_sddc(self, deployment_id: str) -> Dict:
        """Retries an SDDC deployment operation.

        Args:
            deployment_id (str): The ID of the deployment to retry.

        Returns:
            Dict: The retry operation result.
        """
        return self._api_request("PATCH", f"sddcs/{deployment_id}")

    def retry_sddc_validation(self, sddc_id: str, body: Optional[str] = None) -> Dict:
        """Retries an SDDC validation operation.

        Args:
            sddc_id (str): The ID of the SDDC validation to retry.
            body (Optional[str]): The validation payload as a JSON string.

        Returns:
            Dict: The retry validation result.

        Note:
            This method has not been fully tested in production.
        """
        return self._api_request("PATCH", f"sddcs/validations/{sddc_id}", body)

    # =============================================================================
    # VCF Installer: Customer Experience Improvement Program Operations
    # =============================================================================

    def get_ceip_status(self) -> Dict:
        """Retrieves CEIP (Customer Experience Improvement Program) status.

        Returns:
            Dict: The CEIP status information containing status and instanceId.
        """
        return self._api_request("GET", "system/ceip")

    def update_ceip_status(self, body: str) -> Dict:
        """Updates CEIP (Customer Experience Improvement Program) status.

        Args:
            body (str): The CEIP configuration as a JSON string containing status
                (ENABLE or DISABLE).

        Returns:
            Dict: The task information for the CEIP status update.
        """
        return self._api_request("PATCH", "system/ceip", body)

    # =============================================================================
    # VCF Installer: System Configuration Operations
    # =============================================================================

    def get_depot_settings(self) -> Dict:
        """Retrieves the depot configuration.

        Returns:
            Dict: The depot configuration information.
        """
        return self._api_request("GET", "system/settings/depot")

    def get_depot_settings_machine_details(self) -> Dict:
        """Retrieves the machine details from the depot configuration.

        Returns:
            Dict: The machine details information from the depot configuration.

        Note:
            API supported from VCF 9.1.0.0.
        """
        return self._api_request("GET", "system/settings/depot/machine-details")

    def update_depot_settings(self, body: str) -> Dict:
        """Updates the depot configuration.

        Args:
            body (str): The depot settings as a JSON string.

        Returns:
            Dict: The depot settings information.
        """
        return self._api_request("PUT", "system/settings/depot", body)

    def delete_depot_settings(self) -> Dict:
        """Deletes the depot configuration.

        Returns:
            Dict: Empty dict on successful deletion.
        """
        return self._api_request("DELETE", "system/settings/depot")

    def get_depot_sync_info(self) -> Dict:
        """Retrieves the depot sync information.

        Returns:
            Dict: The depot sync information.
        """
        return self._api_request("GET", "system/settings/depot/depot-sync-info")

    def sync_depot_metadata(self) -> Dict:
        """Syncs depot metadata such as bundle manifest, pvc.

        Returns:
            Dict: The depot sync information after triggering the sync.
        """
        return self._api_request("PATCH", "system/settings/depot/depot-sync-info")

    def get_proxy_configuration(self) -> Dict:
        """Retrieves the current proxy configuration.

        Returns:
            Dict: The proxy configuration information.
        """
        return self._api_request("GET", "system/proxy-configuration")

    def update_proxy_configuration(self, body: str) -> Dict:
        """Updates the proxy configuration.

        Args:
            body (str): The proxy configuration as a JSON string.

        Returns:
            Dict: The task information for the proxy configuration update.
        """
        return self._api_request("PATCH", "system/proxy-configuration", body)

    # =============================================================================
    # VCF Installer: Bundle Operations
    # =============================================================================

    def get_bundles(
        self,
        product_type: Optional[str] = None,
        is_compliant: Optional[bool] = None,
        bundle_type: Optional[str] = None,
    ) -> Dict:
        """Retrieves a list of bundles.

        Args:
            product_type (Optional[str]): The type of the product.
            is_compliant (Optional[bool]): Filter bundles by compliance with current
                VCF version.
            bundle_type (Optional[str]): The type of the bundle. Valid values:
                SDDC_MANAGER, VMWARE_SOFTWARE, VXRAIL.

        Returns:
            Dict: The list of bundles with pagination information.
        """
        params = []
        if product_type:
            params.append(f"productType={product_type}")
        if is_compliant is not None:
            params.append(f"isCompliant={str(is_compliant).lower()}")
        if bundle_type:
            params.append(f"bundleType={bundle_type}")

        api_path = "bundles"
        if params:
            api_path += "?" + "&".join(params)

        return self._api_request("GET", api_path)

    def get_bundle_by_id(self, bundle_id: str) -> Dict:
        """Retrieves a specific bundle by its ID.

        Args:
            bundle_id (str): The ID of the bundle.

        Returns:
            Dict: The bundle information.
        """
        return self._api_request("GET", f"bundles/{bundle_id}")

    def get_bundle_download_status(
        self,
        release_version: Optional[str] = None,
        bundle_id: Optional[str] = None,
        image_type: Optional[str] = None,
    ) -> Dict:
        """Retrieves download status for bundles.

        Args:
            release_version (Optional[str]): Retrieves download status of bundles for a
                specific release.
            bundle_id (Optional[str]): Get the download status for a specific bundle.
            image_type (Optional[str]): The image type of the bundle

        Returns:
            Dict: The download status information for bundles matching the criteria.
        """
        params = []
        if release_version:
            params.append(f"releaseVersion={release_version}")
        if bundle_id:
            params.append(f"bundleId={bundle_id}")
        if image_type:
            params.append(f"imageType={image_type}")

        api_path = "bundles/download-status"
        if params:
            api_path += "?" + "&".join(params)

        return self._api_request("GET", api_path)

    def download_bundle(self, bundle_id: str, body: str) -> Dict:
        """Starts, schedules, or cancels a bundle download.

        Args:
            bundle_id (str): The ID of the bundle.
            body (str): The bundle download specification as a JSON string.
                Should contain one of:
                - downloadNow: true (to start download immediately)
                - scheduledTimestamp: "2025-01-24T10:00:00Z" (to schedule)
                - cancelNow: true (to cancel download)

        Returns:
            Dict: The task information for the bundle download operation.
        """
        try:
            payload = json.loads(body)
        except (TypeError, ValueError, JSONDecodeError) as e:
            raise VcfApiException(f"Invalid bundle payload JSON: {e}")

        if "bundleDownloadSpec" not in payload:
            payload = {"bundleDownloadSpec": payload}

        return self._api_request("PATCH", f"bundles/{bundle_id}", json.dumps(payload))

    def delete_bundle(
        self, bundle_id: str, binary_files_only: Optional[bool] = None
    ) -> Dict:
        """Deletes a bundle by its ID.

        Args:
            bundle_id (str): The ID of the bundle to delete.
            binary_files_only (Optional[bool]): If true, only binary files from
                storage will be deleted.

        Returns:
            Dict: Empty dict on successful deletion.
        """
        api_path = f"bundles/{bundle_id}"
        if binary_files_only is not None:
            api_path += f"?binaryFilesOnly={str(binary_files_only).lower()}"

        return self._api_request("DELETE", api_path)

    # =============================================================================
    # VCF Installer: Trusted Certificate Operations
    # =============================================================================

    def get_trusted_certificates(self) -> Dict:
        """Retrieves all trusted certificates from the appliance.

        Returns:
            Dict: A page of trusted certificates with pagination information.
        """
        return self._api_request("GET", "sddc-manager/trusted-certificates")

    def add_trusted_certificate(self, body: str) -> Dict:
        """Adds a trusted certificate to the appliance's trust store.

        Args:
            body (str): The trusted certificate specification as a JSON string.

        Returns:
            Dict: A page of trusted certificates including the newly added certificate.

        Raises:
            VcfApiException: If the certificate already exists (409) or the request
                is invalid (400).
        """
        return self._api_request("POST", "sddc-manager/trusted-certificates", body)

    def delete_trusted_certificate(self, alias: str) -> Dict:
        """Deletes a trusted certificate from the appliance's trust store by alias.

        Args:
            alias (str): The alias of the certificate to delete.

        Returns:
            Dict: Empty dict on successful deletion (204 No Content).

        Raises:
            VcfApiException: If the certificate is not found (404) or an error occurs.
        """
        return self._api_request("DELETE", f"sddc-manager/trusted-certificates/{alias}")

    # =============================================================================
    # VCF Installer: Helper Methods
    # =============================================================================

    def _api_request(
        self,
        http_method: str,
        api_path: str,
        body: Optional[str] = None,
    ) -> Dict:
        """Sends an API request to the VCF Installer instance.

        Args:
            http_method (str): The HTTP method (GET, POST, PATCH, etc.).
            api_path (str): The API path relative to the base URL.
            body (Optional[str]): The JSON string request body for POST/PATCH operations.

        Returns:
            Dict: The response data.

        Raises:
            VcfApiException: If the API request fails.
        """
        vcf_installer_url = f"{self.url}/{api_path}"
        vcf_installer_token = self.get_vcf_installer_token()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {vcf_installer_token}",
        }

        log_line_pre = f"method={http_method}, url={vcf_installer_url}"
        log_line_post = ", ".join(
            (log_line_pre, "success={}, status_code={}, message={}")
        )

        try:
            self.logger.debug(log_line_pre)
            response = requests.request(
                method=http_method,
                url=vcf_installer_url,
                headers=headers,
                verify=self.ssl_verify,
                data=body,
            )
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            raise VcfApiException(f"Error: {e}")

        is_success = self._is_success_status(response.status_code)
        log_line = log_line_post.format(
            is_success, response.status_code, response.reason
        )

        if not is_success:
            error_message = self._extract_error_message(response)
            log_line += f", error_message={error_message}"
            self.logger.error(log_line)
            raise VcfApiException(
                f"{response.status_code}: {response.reason}, {error_message}"
            )

        # Handle responses with no content.
        if not response.content or len(response.content) == 0:
            self.logger.debug(log_line)
            return {}

        try:
            data_out = response.json()
        except (ValueError, JSONDecodeError) as e:
            self.logger.error(log_line_post.format(False, None, e))
            raise VcfApiException("Bad JSON in response") from e

        self.logger.debug(log_line)
        return data_out

    @staticmethod
    def _is_success_status(status_code: int) -> bool:
        """Checks if the HTTP status code indicates success.

        Args:
            status_code (int): The HTTP status code.

        Returns:
            bool: True if status code is between 200-299, False otherwise.
        """
        return HTTP_SUCCESS_MIN <= status_code <= HTTP_SUCCESS_MAX

    @staticmethod
    def _extract_error_message(response: requests.Response) -> str:
        """Extracts error message from response.

        Args:
            response (requests.Response): The HTTP response object.

        Returns:
            str: The error message, or empty string if not found.
        """
        try:
            data = response.json()
            if isinstance(data, dict):
                return data.get("message", "")
        except (ValueError, JSONDecodeError):
            pass
        return ""