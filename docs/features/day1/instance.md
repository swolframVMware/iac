# Day 1: Deploy VCF Instance

## Overview

Deploys a new VMware Cloud Foundation instance.

Supported operations:

- Validate the VCF Instance payload.
- Deploy the VCF Instance.
- Retry a failed VCF Instance deployment.

The role is controlled via the `validate_only` variable:

- `false` (default) — validate and deploy the VCF Instance.
- `true` — validate the payload only; skip deployment.

## Prerequisites

Before you begin, make sure:

1. [Deployment prerequisites](./deployment-prerequisites.md) are met.
2. [Prechecks](./precheck/precheck.md) have passed.
3. VCF Installer is deployed and operational.
4. Infrastructure-as-Code (IaC) data is defined under `./infra-as-code/`.
5. All required passwords are available.

## Configuration Requirements

The following configuration must be provided under `./infra-as-code/`:

- VCF Installer hostname and admin credentials.
- VCF Instance configuration referenced by the payload template (networking,
  storage, DNS, NTP, credentials, etc.).

The role uses IaC data (via `broadcom.vcf.iac.generate_api_payload`) to render
an API payload.

### Instance Configuration Flag

The VCF Instance payload also supports the following IaC flag under `instance`:

- `skip_gateway_ping_validation` - Optional. Controls the rendered
  `skipGatewayPingValidation` API property. Default: `false`.

Set this in the shared defaults file when you want the default applied broadly:

```yaml
infra-as-code/global/regions/defaults/config/instance.yml
```

Override it per VCF Instance when needed:

```yaml
infra-as-code/global/regions/<region>/datacenters/<dc>/azs/<az>/vcfs/<vcf>/config/instance.yml
```

Example:

```yaml
instance:
  skip_gateway_ping_validation: true
```

## Role Interface

### Role: `broadcom.vcf.vcf_installer.instance`

#### Variables

Key variables:

- `validate_only` - Controls whether the role validates only or validates and deploys.
    - `false` (default) - Validate the payload and deploy the VCF Instance.
    - `true` - Validate the payload only; skip deployment.

Polling and Timeout variables:

The module uses timeouts and polling to monitor the deployment status.

| Variable                    | Default        | Description                                                           |
|-----------------------------|----------------|-----------------------------------------------------------------------|
| `deployment_timeout`        | `43200` (12hr) | Seconds to wait for deployment completion before timing out.          |
| `deployment_poll_interval`  | `30`           | Seconds between deployment status polls.                              |
| `validation_timeout`        | `1800` (30m)   | Seconds to wait for payload validation to complete before timing out. |
| `validation_poll_interval`  | `30`           | Seconds between validation status polls.                              |

!!! tip "Nested Lab Environments"
    Deployments in nested labs can take a considerable amount of time.
    The default `deployment_timeout` covers most cases. However,
    you can override the default with `deployment_timeout: 0` to wait
    indefinitely until the deployment completes or fails.

    ```yaml
    - name: Deploy VCF Instance
      hosts: localhost
      vars:
        deployment_timeout: 0
        deployment_poll_interval: 30
      roles:
        - role: broadcom.vcf.vcf_installer.instance
    ```

#### Return Values

- `changed` — Boolean indicating if changes were made.
- `msg` — Status message describing the operation result.
- `meta` — The final API response from the VCF Installer.
- `warnings` — Non-fatal validation warnings (when present).

Additional inputs are drawn from your IaC structure, e.g. `all_iac_vars`:

- `all_iac_vars.vcf_installer.hostname`
- `all_iac_vars.vcf_installer.username`
- `all_iac_vars.vcf_installer.password` or overrides

## Execution

### Deploy VCF Instance (`validate_only: false`)

Example playbook snippet:

```yaml
- name: Deploy VCF Instance
  hosts: localhost
  roles:
    - role: broadcom.vcf.vcf_installer.instance
```

Behavior:

1. Generate VCF Instance payload (`generate_payload.yml`):
    - Invokes `broadcom.vcf.iac.generate_api_payload` to render `api_payload_json`
      from the `vcf_bringup.j2` Jinja2 template.

2. Deploy VCF Instance (`deploy.yml`):
    - Calls `vcf_installer_instance` with `validate_only: false`, which:
        - Submits the payload to `POST /v1/sddcs/validations` and polls
          `GET /v1/sddcs/validations/{id}` until validation completes.
        - Fails if validation returns errors.
        - Submits the bring-up request to `POST /v1/sddcs` and polls
          `GET /v1/sddcs/{id}` using wall-clock timeout (default 12 hours).
        - Continues polling regardless of how long individual subtasks
          take — only stops on success, failure, or `deployment_timeout` expiry.
        - Fails if any subtask reports a failure state.

#### Check Mode Behavior: Deploy

- No API calls are made.
- The module detects check mode and returns `changed: true` with a message:

  ```
  Check Mode: VCF Instance would be deployed; no changes were performed.
  ```

- The role displays this message without submitting validation or deployment requests.

This lets you confirm the play will reach the deploy step without making any changes.

### Validate Only (`validate_only: true`)

To validate the payload without deploying, set `validate_only: true`:

```yaml
- name: Validate VCF Instance Payload
  hosts: localhost
  vars:
    validate_only: true
  roles:
    - role: broadcom.vcf.vcf_installer.instance
```

Behavior:

1. Generates the VCF Instance payload from the IaC template.
2. Calls `vcf_installer_instance` with `validate_only: true`, which:
    - Submits the payload to `POST /v1/sddcs/validations`.
    - Polls `GET /v1/sddcs/validations/{id}` until validation completes.
    - Returns `changed: false` and the full validation report.
    - Fails if validation returns errors.

Non-fatal warnings (if any) are surfaced in `warnings` without failing.

### Retry a Failed Deployment

If a previous deployment attempt failed, retry it by passing the SDDC ID:

```yaml
- name: Retry VCF Instance Deployment
  hosts: localhost
  roles:
    - role: broadcom.vcf.vcf_installer.instance
      tasks_from: retry.yml
```

Behavior:

1. Calls `vcf_installer_instance` with `sddc_id`, which:
    - Issues `PATCH /v1/sddcs/{id}` to retry the failed deployment.
    - Polls `GET /v1/sddcs/{id}` using the timeout.
    - Continues polling regardless of how long individual subtasks take.
    - Fails if the deployment reports a terminal failure state.

#### Check Mode Behavior: Retry

- No API calls are made.
- The module returns `changed: true` with a message:

  ```
  Check Mode: VCF Instance '<sddc_id>' would be retried; no changes were performed.
  ```

## SDK / API Calls

The following VCF Installer endpoints are used by the module utility
`plugins/module_utils/vcf_installer.py`:

For validation:

- `POST /v1/sddcs/validations` — Submits the VCF Instance payload for validation.
- `GET /v1/sddcs/validations/{id}` — Polls the status of the validation process.

For deployment:

- `POST /v1/sddcs` — Starts the VCF Instance deployment.
- `GET /v1/sddcs/{id}` — Polls the status of the VCF Instance deployment.

For retry:

- `PATCH /v1/sddcs/{id}` — Retries a failed VCF Instance deployment.

## Ansible Components

- Module Utils:
    - `plugins/module_utils/vcf_installer.py`
    - `plugins/module_utils/exceptions.py`

- Modules:
    - `plugins/modules/vcf_installer_instance.py`

- Roles:
    - `roles/vcf_installer/instance`

- Playbooks:
    - `playbooks/deploy_instance.yml`
    - `playbooks/retry_instance.yml`

## Usage Examples

### Example 1: Deploy VCF Instance Using Vars File

=== ":material-ansible: Ansible CLI"

    ```bash
    ansible-playbook playbooks/deploy_instance.yml \
      -e @examples/lab/vars/mgmt_automation_settings.yml
    ```

### Example 2: Deploy VCF Instance Using Inline Variables

```bash
ansible-playbook playbooks/deploy_instance.yml \
  -e "region=amer datacenter=dc01 az=az01 vcf=lab domain=m01"
```

### Example 3: Validate Payload Without Deploying

```bash
ansible-playbook playbooks/deploy_instance.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "validate_only=true"
```

### Example 4: Simulate Deployment with Check Mode

```bash
ansible-playbook playbooks/deploy_instance.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  --check
```

### Example 5: Retry a Failed Deployment

```bash
ansible-playbook playbooks/retry_instance.yml \
  -e @examples/lab/vars/mgmt_automation_settings.yml \
  -e "sddc_id=12345678-1234-1234-1234-123456789012"
```

!!! tip "Ansible Automation Platform (AAP)"
    When running under AAP, provide passwords as Ansible credentials (Machine, Vault,
    or other) attached to the job template rather than as extra variables.
    See [Manage Vaulted Passwords](../utilities/ansible-vault.md) for the
    `vault_*` sample variable workflow.

## Workflow Sequence

### Deploy VCF Instance Workflow

1. `playbooks/deploy_instance.yml` is triggered.
2. `iac/get_settings` combines all IaC data into `all_iac_vars`.
3. `vcf_installer/instance` role executes with `validate_only: false`:
    - Renders the VCF Instance payload from the `vcf_bringup.j2` template.
    - Validates the payload with the VCF Installer API.
    - Deploys the VCF Instance.
    - Polls until `COMPLETED_WITH_SUCCESS` or `deployment_timeout` is reached.

### Retry VCF Instance Workflow

1. `playbooks/retry_instance.yml` is triggered.
2. `iac/get_settings` combines all IaC data into `all_iac_vars`.
3. `vcf_installer/instance` role executes via `tasks_from: retry.yml`:
    - Retries the failed deployment identified by `sddc_id`.
    - Polls until `COMPLETED_WITH_SUCCESS` or `deployment_timeout` is reached.
