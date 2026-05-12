# Infrastructure as Code

## Overview

There needs to be a simple way to configure and make changes in a large environment, as well as a simple way to provide inputs to the automation workflow.  Infrastructure as Code (IaC) is the mechanism used to achieve this.

IaC is used for storing VCF configuration data and settings related to the VCF Bring-up automation and the infrastructure the VCF automation is targeting.  Using IaC aids with simplifying and codifying the system configuration and settings, eases the tracking of changes, reduces _snowflakes_, minimizes environmental drift, and helps maintain consistency in configuration and setup.

All code must execute against (at most) a single VCF domain, or components within it. Thus, the IaC which is passed to the code must represent a VCF domain and all associated configuration for that domain.

IaC is a system which consists of:

- the [Configuration](#configuration)
    - simple [YAML configuration files](#individual-yaml-configuration-file-structure)
    - organized across a [hierarchical folder structure](#hierarchical-structure-features)
- the [IaC Loader](#iac-loader) code
    - has inputs (the region, datacenter, VCF instance, and domain) representing which portions of the hierarchy to choose
    - consumes the configuration across multiple hierarchical layers to combine it
    - outputs a single configuration spec used by automation, representing the domain-specific configuration

## Configuration

The configuration exists under `./infra-as-code/` as [individual YAML files](#individual-yaml-configuration-file-structure).

The configuration structure follows a specific configurable pattern and approach which is [structured hierarchically](#hierarchical-structure-features).  This pattern and approach is used by the [IaC Loader](#iac-loader) to work in conjunction with it, so that the data for a specific VCF instance (or component of that instance) can be loaded from multiple hierarchical levels.

### Individual YAML Configuration File Structure

- Variable files are created in [YAML format](https://docs.ansible.com/ansible/latest/reference_appendices/YAMLSyntax.html), with a `.yml` file extension
- Groups of variables are divided into logical product and functional dictionaries (vSphere, NSX, etc)
- A file is specific for each product/service, Ex: `vsphere.yml`, `nsx.yml`, etc
- Each file has a top-level dictionary (_container object_) of the same name as the YAML config file.  The dictionary name should not appear in any another file. Example: `vsphere.yml` has the root (line 1) dictionary as `vsphere:`, and `vsphere:` can only be in a `vsphere.yml` file
- Use _functional_ dictionary groupings below the product. Example: vSphere networking would go under `vsphere.networking`
- Keys should use underscores for word separation, and not camel case.  Ex: `standard_switch_name` instead of `standardSwitchName`
- Under the _functional_ dictionary grouping will be the key-value pairs. Example: `vsphere.networking.standard_switch_name: vSwitch0`
    - The nested dictionaries are important to avoid duplicate variable names
- Comments (as needed) should be added to the end of the field, after the value. Ex: `standard_switch_name: vSwitch0 # my comment`

This is a snippet of a `vsphere.yml` as an example:

```YAML
vsphere:
  networking: 
    standard_switch: # standard switch that's present on the hosts before configuring distributed switch
      name: vSwitch0
      mtu: 8900
```

### Hierarchical Structure Features

In order to minimize having to specify every configuration multiple times for each component, the IaC system supports two key features when constructing the final domain-specific configuration.

- **Configuration Inheritance**
    - provides a way to define common settings at a higher level without the need to repeat them at a lower level
        - ex: regional NTP settings can be defined at just the regional level, and be available during the final domain-specific config
    - a few terms are used to define these higher-level settings, including _base_ and _defaults_
        - ex: global _defaults_; AMER region _defaults_, etc.
- **Configuration Overlays / Overwrites**
    - provides a way for lower-level component settings to overwrite matching higher-level default settings
        - ex: regional NTP settings can be defined at the regional level, but specifying domain-specific NTP settings will overwrite the configuration to use those instead
    - mechanistically, this is achieved by matching keys from the different YAML dictionaries; if there is a match, the value is overwritten
        - overlays support matching keys within nested dictionaries (ex: `vsphere.networking.standard_switch_name` can be setup globally and overwritten at any level below, including a specific domain)
        - overlays DO NOT support matching keys of objects/dictionaries in arrays.  A list from a higher level configuration will be completely overwritten by the list from the lower level configuration (where keys match)

These features allow us to reduce redundancy, increase flexibility, and makes managing complex infrastructure setups much more efficient.

#### Defining the Hierarchical Structure

At the heart of IaC are machine-readable and human readable definition files. The design goal of this IaC Loader is to load the data from any IaC structure without having a _FIXED_ folder structure. There is no hard-coded structure other than "defaults" in the IaC Loader - you can define hierarchical structure based on your needs. The IaC Loader based framework is very flexible to support different hierarchical folder structure.

The following is how the VCF configurations under `./infra-as-code/` are structured, with an example of showing right down to the Broadcom `gcp_lab1` lab. Common settings are at higher levels, which also means that naming conventions used favor least variability between objects in order to help just define them once.  For example, `vsphere.networking.dvs_switches` under `vsphere.yml` at the `global\defaults` lists two switches at the vCenter level (which would be the most common config for each vCenter deployment).

```bash
./
└── global/
    ├── defaults/
    |   └── config/  # Global "Defaults" configuration.  Highest level configuration which is most common
    |       └── nsx.yml
    |       └── sddc.yml
    |       └── vsphere.yml
    |       └── proxy.yml
    └── regions/
        └── amer/
            ├── config/ # Region "Defaults" configuration.  Mid-level configuration, specific to a region 
            │   └── ntp.yml
            └── datacenters/
                └── dc1/ 
                    └── azs/
                        └── az1/
                            └── vcfs/
                                └── gcp_lab/ 
                                    ├── config/ # VCF-specific configuration.  Empty in this case.
                                    └── domains/
                                        └── mgmt/  # Domain-specific configuration
                                            └── config/
                                                ├── dns.yaml
                                                ├── license.yml
                                                ├── nsx.yaml
                                                ├── ntp.yml
                                                └── vsphere.yml
```

- All config:
    - must exist under a (configurable) `config` folder in YAML file(s)
- Higher-level config ("defaults")
    - must exist under a (configurable) "config" folder in YAML files(s)
    - (configurable) "config" folder must exist under a "defaults" folder, and be under a specific category folder, such as `region, datacenter, vcf, domain`  
        - ex: `AMER\defaults\config\`
        - this is because the `defaults` apply to all the items under the `category`, instead of one specific item under the category
        - must _not_ go directly inside the region specific name itself (ex: `AMER`, `EMEA`, `DC-1`, `vcf1`)

```YAML
default_type_folder: config
```

## IaC Loader

The IaC Loader is the code which takes the [configuration](#configuration) and merges it into a single configuration spec, which results in the [hierarchical structure features](#hierarchical-structure-features)

For more details of how the IaC Loader works, look at the [Low-Level Design](../../design/infrastructure-as-code/iac-loader.md).

### Use IaC Loader Ansible Role

Use the IaC Ansible role along with the IaC folder.

Normally you only need to call the role once to retrieve all the IaC data specified for the target component. The following 3 things are needed:

- [ ] specific `iac_pattern`
- [ ] call `roles/iac/load_base_iac`
- [ ] use var return, which is `all_iac_vars`

```YAML
- name: load setting from iac
  include_role:
    name: iac/load_base_iac
  vars:
    working_dir: "{{ playbook_dir }}/../../infra-as-code/"
    iac_pattern: "global/regions/<region>/datacenters/<datacenter>/vcfs/<vcf>/domains/<domain>"
    vcf: gcp_lab
```
