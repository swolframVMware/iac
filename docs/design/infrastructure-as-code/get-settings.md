# Infrastructure as Code: Get Settings

> :warning: This page provides some more details for the Infrastructure as Code (IaC) Loader as part of the IaC system.  
>
> Reading the [Infrastructure as Code](../infrastructure-as-code/index.md) page is a **prerequisite**.

The Infrastructure-as-code (IaC) resides in the main repo, it must be consolidated before it can be used by additional automation. This activity is handledModule: `a _common_ `get_settings` role.

`get_settings` performs the following:

1. clones the repo down locally
    - the IaC repo location and connection details are configurable (_if splitting out IaC and Main repos_)
1. uses the IaC loader to combine config into a single resolved set for a specific region, datacenter, VCF instance, and domain
    - the region, datacenter, VCF instance, and domain are required inputs
1. loads the variables from the YAML files into memory
    - use [IaC loader](iac-loader.md) to load the variables from the YAML files

## Get Settings Inputs

The `get_settings` role requires two sets of inputs:

1. IaC repo information (if split out from main repo)
1. IaC targets

### IaC repo information

#### Combined IaC Repo

The current configuration has IaC and the main data in the same repo. If you'd like to split out IaC, please reference [Separate IaC Repo](#separate-iac-repo)

#### Separate IaC Repo

1. IaC repo git address, using SSH or HTTPs
1. IaC repo branch
1. IaC repo credential

By default, the IaC repo information will be defined under `/vars/automation_settings.yml` in the main VCF code repo.

```YAML
iac_gitrepo_address: ssh://git@<url>/<repo>.git
iac_getrepo_branch: <branch_name>
```

The user of `get_settings` role can update this `/vars/automation_settings.yml` file in the code repo if desired. If updating the code repo vars setting file is not desired, the user can pass the same parameters as `external variables` to the playbook, those paramaters will overwrite the values from the `/vars/automation_settings.yml` file.

- `iac_gitrepo_address`
- `iac_getrepo_branch`

### IaC targets

IaC targets are the locations in IaC to retrieve the specific component information and its associated IaC pattern.

For example, provided IaC pattern `global/regions/<region>/datacenters/<datacenter>/azs/<az>/vcfs/<vcf>/domains/<domain>`, the following inputs are needed:

1. `region`
1. `datacenter`
1. `az`
1. `vcf`
1. `domain`

## Get Setting Outputs

The `get_settings` role returns `all_iac_vars` variable.

## Process - clone of IaC repo

> This method is used if you're IaC repo is split out from the main repo

The clone of IaC repo uses `ansible.builtin.git` Ansible module, which requires:

1. `repo`
1. `dest`
1. `version`
1. `accpt_hostkey`: to enable `StrictHostkeyChecking`

`repo` variable specifies SSH or HTTP(S) protocol address of the git repository

### Supporting both SSH and HTTPs

Depending on the `execution environment`, such as the AAP, it may require supporting both SSH and HTTPS protocols. With that, the code needs to pass in different parameters to the `git` module. A `if-else` statement is required depending on the git address string in the `/vars/mgmt_automation_settings.yml`

For HTTPs, the address would look like this: `https://<token_name>:<token>@<url>/<repo>.git`

## How to use get settings role

Use this test playbook as an example to run `get_settings` role:

```YAML
- name: Testing get iac setting
  hosts: localhost
  gather_facts: true
  environment:
    no_proxy: "*"

  tasks:
    - name: get setting
      include_role:
        name: iac/get_settings
      vars:
        region: amer
        datacenter: dc1
        az: az1
        vcf: gcp_lab
        domain: mgmt
```

You can pass `iac_gitrepo_address` and `iac_getrepo_branch` as `--extra-vars` during run time if you need to overwrite the setting under `vars/mgmt_automation_settings.yml` mentioned above.

> This can only be used if you're IaC repo is split out from the main repo
