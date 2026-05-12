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
from json import JSONDecodeError
from typing import Dict, Optional

import requests
from ansible_collections.broadcom.vcf.plugins.module_utils.exceptions import (
    VcfApiException,
)

API_VERSION = "v1"
AUTH_RESPONSE_FIELD = "accessToken"
HTTP_SUCCESS_MIN = 200
HTTP_SUCCESS_MAX = 299


class SddcManagerApiClient:
    """A class representing a client for interacting with the SDDC Manager API.

    Args:
        sddc_manager_hostname (str): The hostname or IP address of the SDDC Manager.
        sddc_manager_user (str): The username for authenticating with the SDDC Manager.
        sddc_manager_password (str): The password for authenticating with the SDDC Manager.
        ssl_verify (bool, optional): Whether to verify SSL certificates. Defaults to
            False.
        logger (logging.Logger, optional): The logger object for logging. Defaults to
            None.

    Raises:
        VcfApiException: If an error occurs during the API call.

    Methods:
        Token Operations:
            get_sddc_manager_token: Retrieves the access token for authenticating with the SDDC Manager.

        Task Operations:
            get_sddc_manager_task_by_id: Retrieves a specific SDDC Manager task by its resource ID.
            get_all_sddc_manager_tasks: Retrieves all SDDC Manager tasks.
            cancel_sddc_manager_tasks: Cancels a specific SDDC Manager task by its resource ID.
            retry_sddc_manager_tasks: Retries a specific SDDC Manager task by its resource ID.

        SDDC Manager Info Operations:
            get_sddc_manager_info: Retrieves SDDC Manager information.
            get_vcenters_info: Retrieves vCenter information.

        Edge Cluster Operations:
            validate_edge_cluster: Validates an edge cluster.
            edge_cluster_validation_status: Retrieves the validation status of an edge cluster.
            create_edge_cluster: Creates an edge cluster.
            expand_or_shrink_edge_cluster: Expands or shrinks an edge cluster.
            validate_update_edge_cluster: Validates an edge cluster update configuration
            get_edge_clusters: Retrieves all edge clusters.
            get_edge_cluster_by_id: Retrieves a specific edge cluster by its resource ID.

        AVN Operations:
            get_avns: Retrieves all AVNs (Application Virtual Networks).
            validate_avns: Validates AVNs.
            create_avns: Creates AVNs.

        Network Pool Operations:
            get_network_pools: Retrieves all network pools.
            get_network_pool_by_id: Retrieves a specific network pool by its resource ID.
            create_network_pools: Creates network pools.
            update_network_pools: Updates a specific network pool by its resource ID.
            delete_network_pools: Deletes a specific network pool by its resource ID.

        Host Operations:
            get_all_hosts: Retrieves all hosts.
            get_host_by_id: Retrieves a specific host by its resource ID.
            get_hosts_by_fqdn: Retrieves hosts by FQDN.
            get_hosts_by_status: Retrieves hosts by their status.
            validate_hosts: Validates hosts configuration.
            get_validate_hosts_status: Retrieves the validation status of hosts.
            commission_hosts: Commissions hosts.
            decommission_hosts: Decommissions hosts.

        Cluster Operations:
            get_clusters_all_clusters: Retrieves all clusters.
            get_cluster_by_id: Retrieves a specific cluster by its ID.
            validate_clusters: Validates clusters configuration.
            create_clusters: Creates clusters.
            validate_update_cluster: Validates cluster update configuration.
            update_cluster: Updates a cluster (add/remove hosts or stretch/unstretch).
            mount_datastore_on_cluster: Mounts a datastore on a cluster.
            validate_mount_datastore_on_cluster: Validates datastore mount configuration.
            unmount_datastore_on_cluster: Unmounts a datastore from a cluster.
            get_vsan_remote_hci_datastore_from_cluster: Retrieves vSAN remote HCI datastores from a cluster.
            delete_cluster: Deletes a cluster.

        Workload Domain Operations:
            get_all_domains: Retrieves all workload domains.
            get_domain_by_id: Retrieves a specific domain by its resource ID.
            validate_domains: Validates domain configuration.
            get_domain_validation_status: Retrieves the validation status of a domain.
            create_domains: Creates a workload domain.
            update_domains: Updates a workload domain.
            delete_domains: Deletes a workload domain.

        Upgrade Operations:
            get_sddc_manager_upgrades: Retrieves all SDDC Manager upgrades.
            get_sddc_manager_upgrade_by_id: Retrieves a specific SDDC Manager upgrade by its resource ID.
            perform_sddc_manager_upgrade_prechecks: Performs SDDC Manager upgrade prechecks.
            get_sddc_manager_precheck_details: Retrieves SDDC Manager precheck details.
            perform_sddc_manager_upgrade: Performs an SDDC Manager upgrade.
            commit_reschedule_sddc_manager_upgrade: Commits or reschedules an SDDC Manager upgrade.
            get_releases_by_version: Retrieves releases by VCF version.

        NSX Operations:
            get_all_nsx_clusters: Retrieves all NSX clusters.
            get_nsx_cluster_by_id: Retrieves a specific NSX cluster by its resource ID.

        VASA Provider Operations:
            get_all_vasa_providers: Retrieves all VASA providers.
            get_vasa_provider_by_id: Retrieves a specific VASA provider by its resource ID.
            validate_vasa_provider: Validates VASA provider configuration.
            create_vasa_provider: Creates a VASA provider.
            update_vasa_provider: Updates a VASA provider.
            delete_vasa_provider: Deletes a VASA provider.
            get_vsas_provider_storage_containers: Retrieves VASA provider storage containers.
            add_vsas_provider_storage_containters: Adds storage containers to a VASA provider.
            delete_vasa_provider_stroage_container: Deletes a storage container from a VASA provider.
            get_vsas_provider_users: Retrieves VASA provider users.
            add_vsas_provider_users: Adds users to a VASA provider.

        Lifecycle Manager Image Operations:
            get_all_lifecycle_manager_images: Retrieves all lifecycle manager images.
            upload_life_cycle_manager_image: Uploads a lifecycle manager image.
            get_lifecycle_manager_image_by_id: Retrieves a specific lifecycle manager image by its resource ID.
            get_lifecycle_manager_image_by_name: Retrieves a lifecycle manager image by name.
            delete_lifecycle_manager_image: Deletes a lifecycle manager image.
            upload_lifecycle_image_files: Uploads lifecycle manager image files.

        CEIP Operations:
            get_ceip_status: Retrieves CEIP (Customer Experience Improvement Program) status.
            update_ceip_status: Updates CEIP status.

        Certificate Authority Operations:
            get_certificate_authority: Retrieves a list of certificate authorities.
            set_certificate_authority: Sets the configuration of a certificate authority.
            update_certificate_authority: Updates the configuration of a certificate authority.

        Trusted Certificate Operations:
            get_trusted_certificates: Retrieve all trusted certificates from the appliance.
            add_trusted_certificate: Add a trusted certificate to the appliance's trust storee.
            delete_trusted_certificate: Deletes a trusted certificate from the appliance's trust store by alias.

        Services Configuration Operations:
            get_services_configuration: Retrieves the services configuration.

        System Configuration Operations:
            get_ntp_configuration: Retrieves the NTP configuration.
            update_ntp_configuration: Updates the NTP configuration.
            validate_ntp_configuration: Validates NTP configuration.
            get_ntp_configuration_validations: Retrieves a list of NTP configuration validations.
            get_dns_configuration: Retrieves the DNS configuration.
            update_dns_configuration: Updates the DNS configuration.
            validate_dns_configuration: Validates DNS configuration.
            get_dns_configuration_validations: Retrieves a list of DNS configuration validations.
            get_backup_configuration: Retrieves the backup configuration.
            set_backup_configuration: Configures the initial backup configuration.
            update_backup_configuration: Updates the backup configuration.
            validate_backup_configuration: Validates the backup configuration.
            get_depot_settings: Retrieves the depot configuration.
            get_depot_settings_machine_details: Retrieves the machine details from the depot configuration.
            update_depot_settings: Updates the depot configuration.
            delete_depot_settings: Deletes the depot configuration.
            get_proxy_configuration: Retrieves the current proxy configuration.
            update_proxy_configuration: Updates the proxy configuration.

        Upgradables Operations:
            get_all_upgradables: Retrieves all upgradables.
            get_upgradable_for_domain: Retrieves upgradables for a specific domain.
            get_upgradable_for_domain_for_specific_version: Retrieves upgradables for a specific domain and version.
            get_upgradable_for_cluster_by_version: Retrieves upgradables for clusters by version.
            get_upgradable_for_nsxt_by_version: Retrieves upgradables for NSX by version.
            get_upgradable_for_cluster: Retrieves upgradables for clusters.
            get_upgradable_for_nsxt: Retrieves upgradables for NSX-T.
            get_sddc_manager_upgradables: Retrieves SDDC Manager upgradables.

        Bundle Operations:
            get_all_bundles: Retrieves all bundles.
            get_a_bundle: Retrieves a specific bundle by its resource ID.
            upload_bundle: Uploads a bundle.
            upload_a_bundle_for_downloading: Uploads a bundle for downloading.

        User Operations:
            add_user: Adds a user.
            get_all_users: Retrieves all users.
            delete_user: Deletes a user.
            get_all_roles: Retrieves all roles.
            get_sso_domain: Retrieves SSO domain information.
            get_sso_domain_entities: Retrieves SSO domain entities.

        License Key Operations:
            get_all_license_keys: Retrieves all license keys.
            get_license_key_by_id: Retrieves a specific license key by its resource ID.
            create_license_key: Creates a license key.
            delete_license_key: Deletes a license key.

        Advanced Load Balancer Operations:
            get_all_advanced_load_balancer_clusters: Retrieves all advanced load balancer clusters.
            get_advanced_load_balancer_cluster_by_id: Retrieves a specific advanced load balancer cluster by its resource ID.
            validate_advanced_load_balancer_cluster: Validates advanced load balancer cluster configuration.
            validate_advanced_load_balancer_cluster_compatibility: Validates advanced load balancer cluster compatibility.
            delete_advanced_load_balancer_cluster: Deletes an advanced load balancer cluster.

        Check-Set (System Precheck) Operations:
            create_sddc_manager_check_set: Creates an SDDC Manager check-set query.
            trigger_sddc_manager_check_set_run: Triggers an SDDC Manager check-set run.
            get_sddc_manager_check_set_status: Retrieves the status of an SDDC Manager check-set.

        Config Reconciler Operations:
            perform_config_drift_reconciliation: Performs configuration drift reconciliation.
            get_reconciliation_task: Retrieves a reconciliation task.
    """

    def __init__(
        self,
        sddc_manager_hostname: str,
        sddc_manager_user: str,
        sddc_manager_password: str,
        ssl_verify: bool = False,
        logger: Optional[logging.Logger] = None,
    ):
        self.sddc_manager_hostname = sddc_manager_hostname
        self.sddc_manager_user = sddc_manager_user
        self.sddc_manager_password = sddc_manager_password
        self.url = f"https://{self.sddc_manager_hostname}/{API_VERSION}"
        self.logger = logger or logging.getLogger(__name__)
        self.ssl_verify = ssl_verify
        if not self.ssl_verify:
            requests.packages.urllib3.disable_warnings()

    # =============================================================================
    # SDDC Manager: Token
    # =============================================================================

    def get_sddc_manager_token(self) -> str:
        """Retrieves the access token for authenticating with the SDDC Manager.

        Returns:
            str: The access token.

        Raises:
            VcfApiException: If token retrieval fails.
        """
        token_url = f"{self.url}/tokens"
        headers = {"Content-Type": "application/json"}
        body = {
            "username": self.sddc_manager_user,
            "password": self.sddc_manager_password,
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

        return data_out[AUTH_RESPONSE_FIELD]

    # =============================================================================
    # SDDC Manager: Tasks Operations
    # =============================================================================

    def get_sddc_manager_task_by_id(self, resource_id: str) -> Dict:
        """Retrieves a specific SDDC Manager task by its resource ID.

        Args:
            resource_id (str): The ID of the task.

        Returns:
            Dict: The task information.
        """
        return self._api_request("GET", f"tasks/{resource_id}")

    def get_all_sddc_manager_tasks(self) -> Dict:
        """Retrieves all SDDC Manager tasks.

        Returns:
            Dict: All tasks information.
        """
        return self._api_request("GET", "tasks")

    def cancel_sddc_manager_tasks(self, resource_id: str) -> Dict:
        """Cancels a specific SDDC Manager task by its resource ID.

        Args:
            resource_id (str): The ID of the task to cancel.

        Returns:
            Dict: The cancellation result.
        """
        return self._api_request("DELETE", f"tasks/{resource_id}")

    def retry_sddc_manager_tasks(self, resource_id: str) -> Dict:
        """Retries a specific SDDC Manager task by its resource ID.

        Args:
            resource_id (str): The ID of the task to retry.

        Returns:
            Dict: The retry result.
        """
        return self._api_request("PATCH", f"tasks/{resource_id}")

    # =============================================================================
    # SDDC Manager: Info Operations
    # =============================================================================

    def get_sddc_manager_info(self) -> Dict:
        """Retrieves SDDC Manager information.

        Returns:
            Dict: The SDDC Manager information.
        """
        return self._api_request("GET", "sddc-managers")

    # =============================================================================
    # SDDC Manager: vCenter Operations
    # =============================================================================

    def get_vcenters_info(self) -> Dict:
        """Retrieves vCenter information.

        Returns:
            Dict: The vCenter information.
        """
        return self._api_request("GET", "vcenters")

    # =============================================================================
    # SDDC Manager: Edge Cluster Operations
    # =============================================================================

    def validate_edge_cluster(self, body: str) -> Dict:
        """Validates an edge cluster configuration.

        Args:
            body (str): The edge cluster configuration to validate as a JSON string.

        Returns:
            Dict: The validation result.
        """
        return self._api_request("POST", "edge-clusters/validations", body)

    def edge_cluster_validation_status(self, resource_id: str) -> Dict:
        """Retrieves the validation status of an edge cluster.

        Args:
            resource_id (str): The ID of the edge cluster validation.

        Returns:
            Dict: The validation status.
        """
        return self._api_request("GET", f"edge-clusters/validations/{resource_id}")

    def create_edge_cluster(self, body: str) -> Dict:
        """Creates an edge cluster.

        Args:
            body (str): The edge cluster configuration as a JSON string.

        Returns:
            Dict: The created edge cluster information.
        """
        return self._api_request("POST", "edge-clusters", body)

    def expand_or_shrink_edge_cluster(self, resource_id: str, body: str) -> Dict:
        """Expands or shrinks an edge cluster.

        Args:
            resource_id (str): The ID of the edge cluster.
            body (str): The edge cluster update configuration as a JSON string.

        Returns:
            Dict: The update result.
        """
        return self._api_request("PATCH", f"edge-clusters/{resource_id}", body)

    def validate_update_edge_cluster(self, resource_id: str, body: str) -> Dict:
        """Validates an edge cluster update configuration.

        Args:
            resource_id (str): The ID of the edge cluster.
            body (str): The edge cluster update configuration to validate as a JSON string.

        Returns:
            Dict: The validation result.
        """
        return self._api_request(
            "POST", f"edge-clusters/{resource_id}/validations", body
        )

    def get_edge_clusters(self) -> Dict:
        """Retrieves all edge clusters.

        Returns:
            Dict: All edge clusters information.
        """
        return self._api_request("GET", "edge-clusters")

    def get_edge_cluster_by_id(self, resource_id: str) -> Dict:
        """Retrieves a specific edge cluster by its resource ID.

        Args:
            resource_id (str): The ID of the edge cluster.

        Returns:
            Dict: The edge cluster information.
        """
        return self._api_request("GET", f"edge-clusters/{resource_id}")

    # =============================================================================
    # SDDC Manager: AVN Operations
    # =============================================================================

    def get_avns(self) -> Dict:
        """Retrieves all AVNs (Application Virtual Networks).

        Returns:
            Dict: All AVNs information.
        """
        return self._api_request("GET", "avns")

    def validate_avns(self, body: str) -> Dict:
        """Validates AVNs configuration.

        Args:
            body (str): The AVNs configuration to validate as a JSON string.

        Returns:
            Dict: The validation result.
        """
        return self._api_request("POST", "avns/validations", body)

    def create_avns(self, body: str) -> Dict:
        """Creates AVNs.

        Args:
            body (str): The AVNs configuration as a JSON string.

        Returns:
            Dict: The created AVNs information.
        """
        return self._api_request("POST", "avns", body)

    # =============================================================================
    # SDDC Manager: Network Pool Operations
    # =============================================================================

    def get_network_pools(self) -> Dict:
        """Retrieves all network pools.

        Returns:
            Dict: All network pools information.
        """
        return self._api_request("GET", "network-pools")

    def get_network_pool_by_id(self, resource_id: str) -> Dict:
        """Retrieves a specific network pool by its resource ID.

        Args:
            resource_id (str): The ID of the network pool.

        Returns:
            Dict: The network pool information.
        """
        return self._api_request("GET", f"network-pools/{resource_id}")

    def create_network_pools(self, body: str) -> Dict:
        """Creates network pools.

        Args:
            body (str): The network pool configuration as a JSON string.

        Returns:
            Dict: The created network pool information.
        """
        return self._api_request("POST", "network-pools", body)

    def update_network_pools(self, resource_id: str, body: str) -> Dict:
        """Updates a specific network pool by its resource ID.

        Args:
            resource_id (str): The ID of the network pool.
            body (str): The network pool update configuration as a JSON string.

        Returns:
            Dict: The update result.
        """
        return self._api_request("PATCH", f"network-pools/{resource_id}", body)

    def delete_network_pools(self, resource_id: str) -> Dict:
        """Deletes a specific network pool by its resource ID.

        Args:
            resource_id (str): The ID of the network pool to delete.

        Returns:
            Dict: Confirmation of deletion.
        """
        result = self._api_request("DELETE", f"network-pools/{resource_id}")
        # If empty response, return confirmation
        if not result:
            return {"status": "deleted", "id": resource_id}
        return result

    # =============================================================================
    # SDDC Manager: Host Operations
    # =============================================================================

    def get_all_hosts(self) -> Dict:
        """Retrieves all hosts.

        Returns:
            Dict: All hosts information.
        """
        return self._api_request("GET", "hosts")

    def get_host_by_id(self, resource_id: str) -> Dict:
        """Retrieves a specific host by its resource ID.

        Args:
            resource_id (str): The ID of the host.

        Returns:
            Dict: The host information.
        """
        return self._api_request("GET", f"hosts/{resource_id}")

    def get_hosts_by_fqdn(self, fqdn: str) -> Dict:
        """Retrieves hosts by FQDN.

        Args:
            fqdn (str): The FQDN of the host.

        Returns:
            Dict: The hosts information.
        """
        return self._api_request("GET", f"hosts?fqdn={fqdn}")

    def get_hosts_by_status(self, status: str) -> Dict:
        """Retrieves hosts by their status.

        Args:
            status (str): The status to filter by. Can be one of:
                - UNASSIGNED_USEABLE
                - UNASSIGNED_UNUSEABLE
                - ASSIGNED

        Returns:
            Dict: The hosts information.
        """
        return self._api_request("GET", f"hosts?status={status}")

    def validate_hosts(self, body: str) -> Dict:
        """Validates hosts configuration.

        Args:
            body (str): The hosts configuration to validate as a JSON string.

        Returns:
            Dict: The validation result.
        """
        return self._api_request("POST", "hosts/validations", body)

    def get_validate_hosts_status(self, resource_id: str) -> Dict:
        """Retrieves the validation status of hosts.

        Args:
            resource_id (str): The ID of the hosts validation.

        Returns:
            Dict: The validation status.
        """
        return self._api_request("GET", f"hosts/validations/{resource_id}")

    def commission_hosts(self, body: str) -> Dict:
        """Commissions hosts.

        Args:
            body (str): The hosts configuration as a JSON string.

        Returns:
            Dict: The commission result.
        """
        return self._api_request("POST", "hosts", body)

    def decommission_hosts(self, body: str) -> Dict:
        """Decommissions hosts.

        Args:
            body (str): The hosts configuration as a JSON string.

        Returns:
            Dict: The decommission result.
        """
        return self._api_request("DELETE", "hosts", body)

    # =============================================================================
    # SDDC Manager: Cluster Operations
    # =============================================================================

    def get_clusters_all_clusters(self) -> Dict:
        """Retrieves all clusters.

        Returns:
            Dict: All clusters information.
        """
        return self._api_request("GET", "clusters")

    def get_cluster_by_id(self, cluster_id: str) -> Dict:
        """Retrieves a specific cluster by its ID.

        Args:
            cluster_id (str): The ID of the cluster.

        Returns:
            Dict: The cluster information.
        """
        return self._api_request("GET", f"clusters/{cluster_id}")

    def validate_clusters(self, body: str) -> Dict:
        """Validates clusters configuration.

        Args:
            body (str): The clusters configuration to validate as a JSON string.

        Returns:
            Dict: The validation result.
        """
        return self._api_request("POST", "clusters/validations", body)

    def create_clusters(self, body: str) -> Dict:
        """Creates clusters.

        Args:
            body (str): The clusters configuration as a JSON string.

        Returns:
            Dict: The created clusters information.
        """
        return self._api_request("POST", "clusters", body)

    def validate_update_cluster(self, cluster_id: str, body: str) -> Dict:
        """Validates cluster update configuration.

        Args:
            cluster_id (str): The ID of the cluster.
            body (str): The cluster update configuration to validate as a JSON string.

        Returns:
            Dict: The validation result.
        """
        return self._api_request("POST", f"clusters/{cluster_id}/validations", body)

    def update_cluster(self, cluster_id: str, body: str) -> Dict:
        """Updates a cluster. Can add/remove hosts or stretch/unstretch cluster.

        Args:
            cluster_id (str): The ID of the cluster.
            body (str): The cluster update configuration as a JSON string.

        Returns:
            Dict: The update result.
        """
        return self._api_request("PATCH", f"clusters/{cluster_id}", body)

    def mount_datastore_on_cluster(self, cluster_id: str, body: str) -> Dict:
        """Mounts a datastore on a cluster.

        Args:
            cluster_id (str): The ID of the cluster.
            body (str): The datastore mount configuration as a JSON string.

        Returns:
            Dict: The mount result.
        """
        return self._api_request("POST", f"clusters/{cluster_id}/datastores", body)

    def validate_mount_datastore_on_cluster(self, cluster_id: str, body: str) -> Dict:
        """Validates datastore mount configuration.

        Args:
            cluster_id (str): The ID of the cluster.
            body (str): The datastore mount configuration to validate as a JSON string.

        Returns:
            Dict: The validation result.
        """
        return self._api_request(
            "POST", f"clusters/{cluster_id}/datastores/validation", body
        )

    def unmount_datastore_on_cluster(self, cluster_id: str, datastore_id: str) -> Dict:
        """Unmounts a datastore from a cluster.

        Args:
            cluster_id (str): The ID of the cluster.
            datastore_id (str): The ID of the datastore.

        Returns:
            Dict: The unmount result.
        """
        return self._api_request(
            "DELETE", f"clusters/{cluster_id}/datastores/{datastore_id}"
        )

    def get_vsan_remote_hci_datastore_from_cluster(self, cluster_id: str) -> Dict:
        """Retrieves vSAN remote HCI datastores from a cluster.

        Args:
            cluster_id (str): The ID of the cluster.

        Returns:
            Dict: The vSAN remote HCI datastores information.
        """
        return self._api_request(
            "GET", f"clusters/{cluster_id}/datastores/criteria/VSAN_REMOTE_DATASTORES"
        )

    def delete_cluster(self, cluster_id: str) -> Dict:
        """Deletes a cluster.

        Args:
            cluster_id (str): The ID of the cluster to delete.

        Returns:
            Dict: The deletion result.
        """
        return self._api_request("DELETE", f"clusters/{cluster_id}")

    # =============================================================================
    # SDDC Manager: Workload Domain Operations
    # =============================================================================

    def get_all_domains(self) -> Dict:
        """Retrieves all workload domains.

        Returns:
            Dict: All domains information.
        """
        return self._api_request("GET", "domains")

    def get_domain_by_id(self, resource_id: str) -> Dict:
        """Retrieves a specific domain by its resource ID.

        Args:
            resource_id (str): The ID of the domain.

        Returns:
            Dict: The domain information.
        """
        return self._api_request("GET", f"domains/{resource_id}")

    def validate_domains(self, body: str) -> Dict:
        """Validates domain configuration.

        Args:
            body (str): The domain configuration to validate as a JSON string.

        Returns:
            Dict: The validation result.
        """
        return self._api_request("POST", "domains/validations", body)

    def get_domain_validation_status(self, resource_id: str) -> Dict:
        """Retrieves the validation status of a domain.

        Args:
            resource_id (str): The ID of the domain validation.

        Returns:
            Dict: The validation status.
        """
        return self._api_request("GET", f"domains/validations/{resource_id}")

    def create_domains(self, body: str) -> Dict:
        """Creates a workload domain.

        Args:
            body (str): The domain configuration as a JSON string.

        Returns:
            Dict: The created domain information.
        """
        return self._api_request("POST", "domains", body)

    def update_domains(self, resource_id: str, body: str) -> Dict:
        """Updates a workload domain.

        Args:
            resource_id (str): The ID of the domain.
            body (str): The domain update configuration as a JSON string.

        Returns:
            Dict: The update result.
        """
        return self._api_request("PATCH", f"domains/{resource_id}", body)

    def delete_domains(self, resource_id: str) -> Dict:
        """Deletes a workload domain.

        Args:
            resource_id (str): The ID of the domain to delete.

        Returns:
            Dict: The deletion result.
        """
        return self._api_request("DELETE", f"domains/{resource_id}")

    # =============================================================================
    # SDDC Manager: Upgrade Operations
    # =============================================================================

    def get_sddc_manager_upgrades(self) -> Dict:
        """Retrieves all SDDC Manager upgrades.

        Returns:
            Dict: All upgrades information.
        """
        return self._api_request("GET", "upgrades")

    def get_sddc_manager_upgrade_by_id(self, resource_id: str) -> Dict:
        """Retrieves a specific SDDC Manager upgrade by its resource ID.

        Args:
            resource_id (str): The ID of the upgrade.

        Returns:
            Dict: The upgrade information.
        """
        return self._api_request("GET", f"upgrades/{resource_id}")

    def perform_sddc_manager_upgrade_prechecks(
        self, resource_id: str, body: str
    ) -> Dict:
        """Performs SDDC Manager upgrade prechecks.

        Args:
            resource_id (str): The ID of the upgrade.
            body (str): The precheck configuration as a JSON string.

        Returns:
            Dict: The precheck result.
        """
        return self._api_request("POST", f"upgrades/{resource_id}/prechecks", body)

    def get_sddc_manager_precheck_details(
        self, resource_id: str, precheck_id: str
    ) -> Dict:
        """Retrieves SDDC Manager precheck details.

        Args:
            resource_id (str): The ID of the upgrade.
            precheck_id (str): The ID of the precheck.

        Returns:
            Dict: The precheck details.
        """
        return self._api_request(
            "GET", f"upgrades/{resource_id}/prechecks/{precheck_id}"
        )

    def perform_sddc_manager_upgrade(self, body: str) -> Dict:
        """Performs an SDDC Manager upgrade.

        Args:
            body (str): The upgrade configuration as a JSON string.

        Returns:
            Dict: The upgrade result.
        """
        return self._api_request("POST", "upgrades", body)

    def commit_reschedule_sddc_manager_upgrade(
        self, resource_id: str, body: str
    ) -> Dict:
        """Commits or reschedules an SDDC Manager upgrade.

        Args:
            resource_id (str): The ID of the upgrade.
            body (str): The commit/reschedule configuration as a JSON string.

        Returns:
            Dict: The operation result.
        """
        return self._api_request("PATCH", f"upgrades/{resource_id}", body)

    def get_releases_by_version(self, vcf_version: str) -> Dict:
        """Retrieves releases by VCF version.

        Args:
            vcf_version (str): The VCF version.

        Returns:
            Dict: The releases information.
        """
        return self._api_request("GET", f"releases?versionEq={vcf_version}")

    # =============================================================================
    # SDDC Manager: NSX Operations
    # =============================================================================

    def get_all_nsx_clusters(self) -> Dict:
        """Retrieves all NSX clusters.

        Returns:
            Dict: All NSX clusters information.
        """
        return self._api_request("GET", "nsxt-clusters")

    def get_nsx_cluster_by_id(self, resource_id: str) -> Dict:
        """Retrieves a specific NSX cluster by its resource ID.

        Args:
            resource_id (str): The ID of the NSX cluster.

        Returns:
            Dict: The NSX cluster information.
        """
        return self._api_request("GET", f"nsxt-clusters/{resource_id}")

    # =============================================================================
    # SDDC Manager: VASA Provider Operations
    # =============================================================================

    def get_all_vasa_providers(self) -> Dict:
        """Retrieves all VASA providers.

        Returns:
            Dict: All VASA providers information.
        """
        return self._api_request("GET", "vasa-providers")

    def get_vasa_provider_by_id(self, resource_id: str) -> Dict:
        """Retrieves a specific VASA provider by its resource ID.

        Args:
            resource_id (str): The ID of the VASA provider.

        Returns:
            Dict: The VASA provider information.
        """
        return self._api_request("GET", f"vasa-providers/{resource_id}")

    def validate_vasa_provider(self, body: str) -> Dict:
        """Validates VASA provider configuration.

        Args:
            body (str): The VASA provider configuration to validate as a JSON string.

        Returns:
            Dict: The validation result.
        """
        return self._api_request("POST", "vasa-providers/validations", body)

    def create_vasa_provider(self, body: str) -> Dict:
        """Creates a VASA provider.

        Args:
            body (str): The VASA provider configuration as a JSON string.

        Returns:
            Dict: The created VASA provider information.
        """
        return self._api_request("POST", "vasa-providers", body)

    def update_vasa_provider(self, resource_id: str, body: str) -> Dict:
        """Updates a VASA provider.

        Args:
            resource_id (str): The ID of the VASA provider.
            body (str): The VASA provider update configuration as a JSON string.

        Returns:
            Dict: The update result.
        """
        return self._api_request("PATCH", f"vasa-providers/{resource_id}", body)

    def delete_vasa_provider(self, resource_id: str) -> Dict:
        """Deletes a VASA provider.

        Args:
            resource_id (str): The ID of the VASA provider to delete.

        Returns:
            Dict: The deletion result.
        """
        return self._api_request("DELETE", f"vasa-providers/{resource_id}")

    def get_vsas_provider_storage_containers(self, resource_id: str) -> Dict:
        """Retrieves VASA provider storage containers.

        Args:
            resource_id (str): The ID of the VASA provider.

        Returns:
            Dict: The storage containers information.
        """
        return self._api_request(
            "GET", f"vasa-providers/{resource_id}/storage-containers"
        )

    def add_vsas_provider_storage_containters(
        self, resource_id: str, body: str
    ) -> Dict:
        """Adds storage containers to a VASA provider.

        Args:
            resource_id (str): The ID of the VASA provider.
            body (str): The storage containers configuration as a JSON string.

        Returns:
            Dict: The add result.
        """
        return self._api_request(
            "POST", f"vasa-providers/{resource_id}/storage-containers", body
        )

    def delete_vasa_provider_stroage_container(
        self, resource_id: str, storage_container_id: str
    ) -> Dict:
        """Deletes a storage container from a VASA provider.

        Args:
            resource_id (str): The ID of the VASA provider.
            storage_container_id (str): The ID of the storage container.

        Returns:
            Dict: The deletion result.
        """
        return self._api_request(
            "DELETE",
            f"vasa-providers/{resource_id}/storage-containers/{storage_container_id}",
        )

    def get_vsas_provider_users(self, resource_id: str) -> Dict:
        """Retrieves VASA provider users.

        Args:
            resource_id (str): The ID of the VASA provider.

        Returns:
            Dict: The users information.
        """
        return self._api_request("GET", f"vasa-providers/{resource_id}/users")

    def add_vsas_provider_users(self, resource_id: str, body: str) -> Dict:
        """Adds users to a VASA provider.

        Args:
            resource_id (str): The ID of the VASA provider.
            body (str): The users configuration as a JSON string.

        Returns:
            Dict: The add result.
        """
        return self._api_request("POST", f"vasa-providers/{resource_id}/users", body)

    # =============================================================================
    # SDDC Manager: Lifecycle Manager Image Operations
    # =============================================================================

    def get_all_lifecycle_manager_images(self) -> Dict:
        """Retrieves all lifecycle manager images.

        Returns:
            Dict: All lifecycle manager images information.
        """
        return self._api_request("GET", "personalities")

    def upload_life_cycle_manager_image(self, body: str) -> Dict:
        """Uploads a lifecycle manager image.

        Args:
            body (str): The lifecycle manager image configuration as a JSON string.

        Returns:
            Dict: The upload result.
        """
        return self._api_request("POST", "personalities", body)

    def get_lifecycle_manager_image_by_id(self, resource_id: str) -> Dict:
        """Retrieves a specific lifecycle manager image by its resource ID.

        Args:
            resource_id (str): The ID of the lifecycle manager image.

        Returns:
            Dict: The lifecycle manager image information.
        """
        return self._api_request("GET", f"personalities/{resource_id}")

    def get_lifecycle_manager_image_by_name(self, image_name: str) -> Dict:
        """Retrieves a lifecycle manager image by name.

        Args:
            image_name (str): The name of the lifecycle manager image.

        Returns:
            Dict: The lifecycle manager image information.
        """
        return self._api_request("GET", f"personalities?personalityName={image_name}")

    def delete_lifecycle_manager_image(self, resource_id: str) -> Dict:
        """Deletes a lifecycle manager image.

        Args:
            resource_id (str): The ID of the lifecycle manager image to delete.

        Returns:
            Dict: The deletion result.
        """
        return self._api_request("DELETE", f"personalities/{resource_id}")

    def upload_lifecycle_image_files(self, files) -> requests.Response:
        """Uploads lifecycle manager image files.

        Args:
            files: The files to upload.

        Returns:
            requests.Response: The upload response.
        """
        return self._api_file_request("PUT", "personalities/files", files)

    # =============================================================================
    # SDDC Manager: Customer Experience Improvement Program Operations
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
    # SDDC Manager: Certificate Authority Operations
    # =============================================================================

    def get_certificate_authority(self) -> Dict:
        """Retrieves a list of certificate authorities.

        Returns:
            Dict: The certificate authorities information.
        """
        return self._api_request("GET", "certificate-authorities")

    def set_certificate_authority(self, body: str) -> Dict:
        """Sets the configuration of a certificate authority.

        Args:
            body (str): The certificate authority configuration as a JSON string.

        Returns:
            Dict: The certificate authority information.
        """
        return self._api_request("PUT", "certificate-authorities", body)

    def update_certificate_authority(self, body: str) -> Dict:
        """Updates the configuration of a certificate authority.

        Args:
            body (str): The certificate authority configuration as a JSON string.

        Returns:
            Dict: The updated certificate authority information.
        """
        return self._api_request("PATCH", "certificate-authorities", body)

    # =============================================================================
    # SDDC Manager: Trusted Certificate Operations
    # =============================================================================

    def get_trusted_certificates(self) -> Dict:
        """Retrieve all trusted certificates from the appliance.

        Returns:
            Dict: A page of trusted certificates with pagination information.
        """
        return self._api_request("GET", "sddc-manager/trusted-certificates")

    def add_trusted_certificate(self, body: str) -> Dict:
        """Add a trusted certificate to the appliance's trust storee.

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
    # SDDC Manager: Services Configuration Operations
    # =============================================================================

    def get_services_configuration(self) -> Dict:
        """Retrieves the services configuration.

        Returns:
            Dict: The services configuration information.

        Note:
            API supported from VCF 9.1.0.0.
        """
        return self._api_request("GET", "system/services-config")

    # =============================================================================
    # SDDC Manager: System Configuration Operations
    # =============================================================================

    def get_ntp_configuration(self) -> Dict:
        """Retrieves the NTP configuration.

        Returns:
            Dict: The NTP configuration information.
        """
        return self._api_request("GET", "system/ntp-configuration")

    def update_ntp_configuration(self, body: str) -> Dict:
        """Updates the NTP configuration.

        Args:
            body (str): The NTP configuration as a JSON string.

        Returns:
            Dict: The update result (task information).
        """
        return self._api_request("PUT", "system/ntp-configuration", body)

    def validate_ntp_configuration(self, body: str) -> Dict:
        """Validates NTP configuration.

        Args:
            body (str): The NTP configuration to validate as a JSON string.

        Returns:
            Dict: The validation result.
        """
        return self._api_request("POST", "system/ntp-configuration/validations", body)

    def get_ntp_configuration_validations(self, execution_status: str = None) -> Dict:
        """Retrieves a list of NTP configuration validations.

        Args:
            execution_status (str, optional): Filter by execution status.

        Returns:
            Dict: The list of NTP configuration validations.
        """
        endpoint = "system/ntp-configuration/validations"
        if execution_status:
            endpoint += f"?executionStatus={execution_status}"
        return self._api_request("GET", endpoint)

    def get_dns_configuration(self) -> Dict:
        """Retrieves the DNS configuration.

        Returns:
            Dict: The DNS configuration information.
        """
        return self._api_request("GET", "system/dns-configuration")

    def update_dns_configuration(self, body: str) -> Dict:
        """Updates the DNS configuration.

        Args:
            body (str): The DNS configuration as a JSON string.

        Returns:
            Dict: The update result (task information).
        """
        return self._api_request("PUT", "system/dns-configuration", body)

    def validate_dns_configuration(self, body: str) -> Dict:
        """Validates DNS configuration.

        Args:
            body (str): The DNS configuration to validate as a JSON string.

        Returns:
            Dict: The validation result.
        """
        return self._api_request("POST", "system/dns-configuration/validations", body)

    def get_dns_configuration_validations(self, execution_status: str = None) -> Dict:
        """Retrieves a list of DNS configuration validations.

        Args:
            execution_status (str, optional): Filter by execution status.

        Returns:
            Dict: The list of DNS configuration validations.
        """
        endpoint = "system/dns-configuration/validations"
        if execution_status:
            endpoint += f"?executionStatus={execution_status}"
        return self._api_request("GET", endpoint)

    def get_dns_configuration_validation_by_id(self, resource_id: str) -> Dict:
        """Retrieves DNS configuration validation result by ID.

        Args:
            resource_id (str): The validation ID.

        Returns:
            Dict: The validation result.
        """
        return self._api_request(
            "GET", f"system/dns-configuration/validations/{resource_id}"
        )

    def get_backup_configuration(self) -> Dict:
        """Retrieves the backup configuration.

        Returns:
            Dict: The backup configuration information.
        """
        return self._api_request("GET", "system/backup-configuration")

    def set_backup_configuration(self, body: str) -> Dict:
        """Configures the initial backup configuration.

        Args:
            body (str): The backup configuration as a JSON string.

        Returns:
            Dict: The task information for the backup configuration.
        """
        return self._api_request("PUT", "system/backup-configuration", body)

    def update_backup_configuration(self, body: str) -> Dict:
        """Updates the backup configuration.

        Args:
            body (str): The backup configuration as a JSON string.

        Returns:
            Dict: The task information for the backup configuration update.
        """
        return self._api_request("PATCH", "system/backup-configuration", body)

    def validate_backup_configuration(self, body: str) -> Dict:
        """Validates backup configuration.

        Args:
            body (str): The backup configuration to validate as a JSON string.

        Returns:
            Dict: The validation result.
        """
        return self._api_request(
            "POST", "system/backup-configuration/validations", body
        )

    def get_depot_settings(self) -> Dict:
        """Retrieves the depot configuration.

        Returns:
            Dict: The depot configuration information.

        Note:
            API not supported from VCF 9.1.0.0. Use get_services_configuration instead.
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
    # SDDC Manager: Upgradables Operations
    # =============================================================================

    def get_all_upgradables(self) -> Dict:
        """Retrieves all upgradables.

        Returns:
            Dict: All upgradables information.
        """
        return self._api_request("GET", "system/upgradables")

    def get_upgradable_for_domain(self, resource_id: str) -> Dict:
        """Retrieves upgradables for a specific domain.

        Args:
            resource_id (str): The ID of the domain.

        Returns:
            Dict: The upgradables information.
        """
        return self._api_request("GET", f"upgradables/domains/{resource_id}")

    def get_upgradable_for_domain_for_specific_version(
        self, resource_id: str, version: str
    ) -> Dict:
        """Retrieves upgradables for a specific domain and version.

        Args:
            resource_id (str): The ID of the domain.
            version (str): The target version.

        Returns:
            Dict: The upgradables information.
        """
        return self._api_request(
            "GET", f"upgradables/domains/{resource_id}?targetVersion={version}"
        )

    def get_upgradable_for_cluster_by_version(
        self, resource_id: str, version: str
    ) -> Dict:
        """Retrieves upgradables for clusters by version.

        Args:
            resource_id (str): The ID of the domain.
            version (str): The target version.

        Returns:
            Dict: The upgradables information.
        """
        return self._api_request(
            "GET", f"upgradables/domains/{resource_id}/clusters?targetVersion={version}"
        )

    def get_upgradable_for_nsxt_by_version(
        self, resource_id: str, version: str
    ) -> Dict:
        """Retrieves upgradables for NSX by version.

        Args:
            resource_id (str): The ID of the domain.
            version (str): The target version.

        Returns:
            Dict: The upgradables information.
        """
        return self._api_request(
            "GET", f"upgradables/domains/{resource_id}/nsxt?targetVersion={version}"
        )

    def get_upgradable_for_cluster(self, resource_id: str) -> Dict:
        """Retrieves upgradables for clusters.

        Args:
            resource_id (str): The ID of the domain.

        Returns:
            Dict: The upgradables information.
        """
        return self._api_request("GET", f"upgradables/domains/{resource_id}/clusters")

    def get_upgradable_for_nsxt(self, resource_id: str) -> Dict:
        """Retrieves upgradables for NSX-T.

        Args:
            resource_id (str): The ID of the domain.

        Returns:
            Dict: The upgradables information.
        """
        return self._api_request("GET", f"upgradables/domains/{resource_id}/nsxt")

    def get_sddc_manager_upgradables(self) -> Dict:
        """Retrieves SDDC Manager upgradables.

        Returns:
            Dict: The SDDC Manager upgradables information.
        """
        return self._api_request("GET", "sddc-manager/upgradables")

    # =============================================================================
    # SDDC Manager: Bundle Operations
    # =============================================================================

    def get_all_bundles(self) -> Dict:
        """Retrieves all bundles.

        Returns:
            Dict: All bundles information.
        """
        return self._api_request("GET", "bundles")

    def get_a_bundle(self, resource_id: str) -> Dict:
        """Retrieves a specific bundle by its resource ID.

        Args:
            resource_id (str): The ID of the bundle.

        Returns:
            Dict: The bundle information.
        """
        return self._api_request("GET", f"bundles/{resource_id}")

    def upload_bundle(self, body: str) -> Dict:
        """Uploads a bundle.

        Args:
            body (str): The bundle configuration as a JSON string.

        Returns:
            Dict: The upload result.
        """
        return self._api_request("POST", "bundles", body)

    def upload_a_bundle_for_downloading(
        self, resource_id: str, target_version: str
    ) -> Dict:
        """Uploads a bundle for downloading.

        Args:
            resource_id (str): The ID of the bundle.
            target_version (str): The target version.

        Returns:
            Dict: The upload result.
        """
        import json

        bundle_payload = {"bundleDownloadSpec": {"downloadNow": True}}
        return self._api_request(
            "POST",
            f"bundles/{resource_id}?targetVersion={target_version}",
            json.dumps(bundle_payload),
        )

    # =============================================================================
    # SDDC Manager: User Operations
    # =============================================================================

    def add_user(self, body: str) -> Dict:
        """Adds a user.

        Args:
            body (str): The user configuration as a JSON string.

        Returns:
            Dict: The created user information.
        """
        return self._api_request("POST", "users", body)

    def get_all_users(self) -> Dict:
        """Retrieves all users.

        Returns:
            Dict: All users information.
        """
        return self._api_request("GET", "users")

    def delete_user(self, resource_id: str) -> Dict:
        """Deletes a user.

        Args:
            resource_id (str): The ID of the user to delete.

        Returns:
            Dict: The deletion result.
        """
        return self._api_request("DELETE", f"users/{resource_id}")

    def get_all_roles(self) -> Dict:
        """Retrieves all roles.

        Returns:
            Dict: All roles information.
        """
        return self._api_request("GET", "roles")

    def get_sso_domain(self) -> Dict:
        """Retrieves SSO domain information.

        Returns:
            Dict: The SSO domain information.
        """
        return self._api_request("GET", "sso-domains")

    def get_sso_domain_entities(self, resource_id: str, entity_name: str) -> Dict:
        """Retrieves SSO domain entities.

        Args:
            resource_id (str): The ID of the SSO domain.
            entity_name (str): The entity name.

        Returns:
            Dict: The SSO domain entities information.
        """
        return self._api_request(
            "GET", f"sso-domains/{resource_id}/entities?entityName={entity_name}"
        )

    # =============================================================================
    # SDDC Manager: License Key Operations
    # =============================================================================

    def get_all_license_keys(self) -> Dict:
        """Retrieves all license keys.

        Returns:
            Dict: All license keys information.
        """
        return self._api_request("GET", "license-keys")

    def get_license_key_by_id(self, resource_id: str) -> Dict:
        """Retrieves a specific license key by its resource ID.

        Args:
            resource_id (str): The ID of the license key.

        Returns:
            Dict: The license key information.
        """
        return self._api_request("GET", f"license-keys/{resource_id}")

    def create_license_key(self, body: str) -> Dict:
        """Creates a license key.

        Args:
            body (str): The license key configuration as a JSON string.

        Returns:
            Dict: The created license key information.
        """
        return self._api_request("POST", "license-keys", body)

    def delete_license_key(self, resource_id: str) -> Dict:
        """Deletes a license key.

        Args:
            resource_id (str): The ID of the license key to delete.

        Returns:
            Dict: The deletion result.
        """
        return self._api_request("DELETE", f"license-keys/{resource_id}")

    # =============================================================================
    # SDDC Manager: Advanced Load Balancer Operations
    # =============================================================================

    def get_all_advanced_load_balancer_clusters(self) -> Dict:
        """Retrieves all advanced load balancer clusters.

        Returns:
            Dict: All advanced load balancer clusters information.
        """
        return self._api_request("GET", "nsx-alb-clusters")

    def get_advanced_load_balancer_cluster_by_id(self, resource_id: str) -> Dict:
        """Retrieves a specific advanced load balancer cluster by its resource ID.

        Args:
            resource_id (str): The ID of the advanced load balancer cluster.

        Returns:
            Dict: The advanced load balancer cluster information.
        """
        return self._api_request("GET", f"nsx-alb-clusters/{resource_id}")

    def validate_advanced_load_balancer_cluster(self, body: str) -> Dict:
        """Validates advanced load balancer cluster configuration.

        Args:
            body (str): The advanced load balancer cluster configuration to validate as a JSON string.

        Returns:
            Dict: The validation result.
        """
        return self._api_request("POST", "nsx-alb-clusters/validations", body)

    def validate_advanced_load_balancer_cluster_compatibility(self) -> Dict:
        """Validates advanced load balancer cluster compatibility.

        Returns:
            Dict: The validation result.
        """
        return self._api_request("POST", "nsx-alb-clusters/validations/version")

    def delete_advanced_load_balancer_cluster(self, resource_id: str) -> Dict:
        """Deletes an advanced load balancer cluster.

        Args:
            resource_id (str): The ID of the advanced load balancer cluster to delete.

        Returns:
            Dict: The deletion result.
        """
        return self._api_request("DELETE", f"nsx-alb-clusters/{resource_id}")

    # =============================================================================
    # SDDC Manager: Check-Set (System Precheck) Operations
    # =============================================================================

    def create_sddc_manager_check_set(self, body: str) -> Dict:
        """Creates an SDDC Manager check-set query.

        Args:
            body (str): The check-set configuration as a JSON string.

        Returns:
            Dict: The check-set query result.
        """
        return self._api_request("POST", "system/check-sets/queries", body)

    def trigger_sddc_manager_check_set_run(self, body: str) -> Dict:
        """Triggers an SDDC Manager check-set run.

        Args:
            body (str): The check-set configuration as a JSON string.

        Returns:
            Dict: The check-set run result.
        """
        return self._api_request("POST", "system/check-sets", body)

    def get_sddc_manager_check_set_status(self, resource_id: str) -> Dict:
        """Retrieves the status of an SDDC Manager check-set.

        Args:
            resource_id (str): The ID of the check-set.

        Returns:
            Dict: The check-set status.
        """
        return self._api_request("GET", f"system/check-sets/{resource_id}")

    # =============================================================================
    # SDDC Manager: Config Reconciler Operations
    # =============================================================================

    def perform_config_drift_reconciliation(self, body: str) -> Dict:
        """Performs configuration drift reconciliation.

        Args:
            body (str): The reconciliation configuration as a JSON string.

        Returns:
            Dict: The reconciliation result.
        """
        return self._api_request("POST", "config-drift-reconciliations", body)

    def get_reconciliation_task(self, resource_id: str) -> Dict:
        """Retrieves a reconciliation task.

        Args:
            resource_id (str): The ID of the reconciliation task.

        Returns:
            Dict: The reconciliation task information.
        """
        return self._api_request("GET", f"config-drift-reconciliations/{resource_id}")

    # =============================================================================
    # SDDC Manager: Helper Methods
    # =============================================================================

    def _api_request(
        self,
        http_method: str,
        api_path: str,
        body: Optional[str] = None,
    ) -> Dict:
        """Sends an API request to the SDDC Manager.

        Args:
            http_method (str): The HTTP method (GET, POST, PATCH, DELETE, etc.).
            api_path (str): The API path relative to the base URL.
            body (Optional[str]): The JSON string request body for POST/PATCH operations.

        Returns:
            Dict: The response data.

        Raises:
            VcfApiException: If the API request fails.
        """
        sddc_manager_url = f"{self.url}/{api_path}"
        sddc_manager_token = self.get_sddc_manager_token()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {sddc_manager_token}",
        }

        log_line_pre = f"method={http_method}, url={sddc_manager_url}"
        log_line_post = ", ".join(
            (log_line_pre, "success={}, status_code={}, message={}")
        )

        try:
            self.logger.debug(log_line_pre)
            response = requests.request(
                method=http_method,
                url=sddc_manager_url,
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

        # Handle 204 No Content or empty responses.
        if response.status_code == 204 or not response.content:
            self.logger.debug(log_line)
            return {}

        try:
            data_out = response.json()
        except (ValueError, JSONDecodeError) as e:
            self.logger.error(log_line_post.format(False, None, e))
            raise VcfApiException("Bad JSON in response") from e

        self.logger.debug(log_line)
        return data_out

    def _api_file_request(
        self,
        http_method: str,
        api_path: str,
        files,
    ) -> requests.Response:
        """Sends a file upload API request to the SDDC Manager.

        Args:
            http_method (str): The HTTP method (PUT, POST, etc.).
            api_path (str): The API path relative to the base URL.
            files: The files to upload.

        Returns:
            requests.Response: The HTTP response.

        Raises:
            VcfApiException: If the API request fails.
        """
        sddc_manager_url = f"{self.url}/{api_path}"
        sddc_manager_token = self.get_sddc_manager_token()

        headers = {"Authorization": f"Bearer {sddc_manager_token}"}

        log_line_pre = f"method={http_method}, url={sddc_manager_url}"
        log_line_post = ", ".join(
            (log_line_pre, "success={}, status_code={}, message={}")
        )

        try:
            self.logger.debug(log_line_pre)
            response = requests.request(
                method=http_method,
                url=sddc_manager_url,
                headers=headers,
                verify=self.ssl_verify,
                files=files,
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

        self.logger.debug(log_line)
        return response

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
