# -*- coding: utf-8 -*-
#
# Copyright (c) Broadcom. All Rights Reserved.
# The term “Broadcom” refers solely to the Broadcom Inc. corporate affiliate that
# distributes this software.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import absolute_import, division, print_function

import logging
from json import JSONDecodeError
from typing import Dict, List, Optional

import requests
from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)

API_BASE_PATH = "suite-api"
SESSION_RESPONSE_FIELD = "token"
HTTP_SUCCESS_MIN = 200
HTTP_SUCCESS_MAX = 299


class VcfOperationsApiClient:
    """A client for interacting with the VCF Operations API.

    Args:
        vcf_operations_ip (str): The hostname or IP address of the VCF Operations
            deployment.
        vcf_operations_user (str): The username for authenticating with VCF Operations.
        vcf_operations_password (str): The password for authenticating with VCF
            Operations.
        ssl_verify (bool, optional): Whether to verify the SSL certificate of VCF
            Operations. Defaults to False.
        logger (logging.Logger, optional): The logger to use for logging. Defaults to
            None.
    """

    def __init__(
        self,
        vcf_operations_ip: str,
        vcf_operations_user: str,
        vcf_operations_password: str,
        ssl_verify: bool = False,
        logger: Optional[logging.Logger] = None,
    ):
        self.vcf_operations_ip = vcf_operations_ip
        self.vcf_operations_user = vcf_operations_user
        self.vcf_operations_password = vcf_operations_password
        self.url = f"https://{self.vcf_operations_ip}/{API_BASE_PATH}"
        self.logger = logger or logging.getLogger(__name__)
        self.ssl_verify = ssl_verify
        if not self.ssl_verify:
            requests.packages.urllib3.disable_warnings()

    # =============================================================================
    # VCF Operations: Token
    # =============================================================================

    def get_vcf_operations_token(self) -> str:
        """Retrieves the access token for authenticating with the VCF Operations API.

        Returns:
            str: The access token.

        Raises:
            VcfApiException: If token retrieval fails.
        """
        vcf_operations_url = f"{self.url}/api/auth/token/acquire"
        headers = {"Content-Type": "application/json"}
        payload = {
            "username": self.vcf_operations_user,
            "password": self.vcf_operations_password,
        }

        try:
            response = requests.post(
                url=vcf_operations_url,
                headers=headers,
                json=payload,
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

        if SESSION_RESPONSE_FIELD not in data_out:
            raise VcfApiException(
                f"Response missing required key: {SESSION_RESPONSE_FIELD}"
            )

        return data_out[SESSION_RESPONSE_FIELD]

    # =============================================================================
    # VCF Operations: Internal Adapters
    # =============================================================================

    def get_vcf_operations_internal_adapters(self) -> Dict:
        """Retrieves internal adapters raw response for VCF domain tree.

        Returns:
            Dict: The raw internal adapters payload.
        """
        return self._api_request(
            http_method="GET",
            api_path="internal/adapters/vcf/domaintree",
        )

    # =============================================================================
    # VCF Operations: Helper Methods
    # =============================================================================

    def _api_request(
        self,
        http_method: str,
        api_path: str,
        body: Optional[str] = None,
    ) -> Dict:
        """Sends an API request to the VCF Operations API.

        Args:
            http_method (str): The HTTP method (GET, POST, PATCH, etc.).
            api_path (str): The API path relative to the base URL.
            body (Optional[str]): The JSON string request body.

        Returns:
            Dict: The response data.

        Raises:
            VcfApiException: If the API request fails.
        """
        vcf_operations_url = f"{self.url}/{api_path}"
        vcf_token = self.get_vcf_operations_token()

        headers = {
            "accept": "application/json",
            "X-Ops-API-use-unsupported": "true",
            "Authorization": f"OpsToken {vcf_token}",
            "Content-Type": "application/json",
        }

        log_line_pre = f"method={http_method}, url={vcf_operations_url}"
        log_line_post = ", ".join(
            (log_line_pre, "success={}, status_code={}, message={}")
        )

        try:
            self.logger.debug(log_line_pre)
            response = requests.request(
                method=http_method,
                url=vcf_operations_url,
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
