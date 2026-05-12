# Infrastructure as Code: IaC Loader

> :warning: This page provides some more details for the Infrastructure as Code (IaC) Loader as part of the IaC system.  
>
> Reading the [Infrastructure as Code](../infrastructure-as-code/index.md) page is a **prerequisite**.

## Define hierarchical structure

You can define hierarchical structure based on your needs. The Iac loader based framework is very flexible to support different hierarchical folder structure.

The following IaC structure is an example that is typical for the IaC loader

```bash
- iac_root 
    category-1 
        cat-1-item1
            category-2
                config
                    ...
                cat-2-item1
                    config
                        ...
                cat-2-item2
                    ....
                defaults
                    config
        cat-1-item2
            category-2
                ....
        defaults
            config
    
    category-2
        defaults
            ...
        ....
```

## Use IaC loader Ansible Role

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
    working_dir: "{{ playbook_dir }}/../infra-as-code/"
    iac_pattern: "global/regions/<region>/datacenters/<datacenter>/vcfs/<vcf>/domains/<domain>"
    vcf: gcp_lab1
```

- Note the ansible role is called `load_base_iac` under `roles/iac/load_base_iac`, it loads the configuration data of specific folder, such as `mgmt`. Specify the target folder name of a component when trying to retrieve the data from IaC.
- If you need to retrieve all the data from IaC, you can call the above role passing all the domain names one after another, you can then save the individual returned data to an array. This is also assuming you know all the domain names for the above `iac_pattern`.

The following is the folder structure which matches the code snippet above for accessing all the configuration data of `gcp_lab1`

```bash
./
└── global/
    └── regions/
        ├── amer/
        │   ├── config/
        │   │   └── ntp.yaml
        │   └── datacenters/
        │       └── dc1/
        │           └── vcfs/
        │               └── gcp_lab1/
        │                   ├── config/
        │                   └── domains/
        │                       └── mgmt/
        │                           └── config/
        │                               ├── action.yml
        │                               ├── cluster.yml
        │                               ├── dns.yaml
        │                               ├── dvs.yml
        │                               ├── license.yml
        │                               ├── nsx.yaml
        │                               ├── ntp.yml
        │                               ├── pod.yml
        │                               ├── proxy.yml
        │                               ├── sddc.yml
        │                               ├── vsan.yml
        │                               └── vsphere.yml
        └── defaults/
            └── config/
                └── ntp.yml

```

### IaC loader mechanism - Overlay & Inheritance

What the ansible role does is to:

1. load all files from the default directory `defaults\config`, store in a temp variable, if the default exists;
1. merges the temp variable with the overall iac vars, which is `all_iac_vars`;
1. load all files from the level directory of a specific component of its `config` folder, store in a temp variable;
1. merges the temp variable with the overall iac vars, which is `all_iac_vars`;
1. repeat the above step 1 to 4, but going down to the next level of the folder structure

Since it loads all the files, that does the inheritance; the merge does the overlay.

The ansible code for above mentioned process is under `roles/iac/load_base_iac/tasks/read_one_level.yml`

### Iac Pattern

- The `iac_pattern` specifies the iac folder structure with pre-defined variable pattern. Anything inside `< >` are the `variable` names which are used by code to access the location of data in the IaC. For example `vcf` is the variable name whose value should be specified.
- The pattern string itself needs to provide the deepest full path of a leaf of the IaC folder structure. In above case, it would be up to individual domain level.

``` YAML
    iac_pattern: "global/regions/<region>/datacenters/<datacenter>/vcfs/<vcf>/domains/<domain>"
    domain: mgmt
```

- If you don't need all the configuration data to the deepest folder, you can use a shorter `iac_pattern` which only matches up to the sub-folder you need. For example, if you use the following `iac_pattern` of `global/regions/<region_input>/datacenters/<datacenter_input>`, you will get configuration data for a specific `<datacenter_input>`. Normally you don't need to use a shorter pattern to get high level configuration data, as the lower level configuration data should include the higher level configuration data, assuming they are not overwritten.

### Configuration Files in IaC

- It is recommended to use YAML file in the configuration files in IaC.
- There are no limits on how many files under one IaC folder. However you should `NOT` have more than one file using the same key in the same IaC folder, because all the files under the same directory are loaded at once, if the same key in a dictionary exists in more than one file, only the first appearance of the key/value is retained, they are not `overlaid`
- The `overlay` happens for key/value pairs from different directory. The key/value pair will be
    - retained if the key is different
    - overwritten if the key is the same
- The overlay of nested dictionary is supported
- Currently the overlay of array/list is NOT supported.

### Wildcard Path with Partial Match

It is possible to only specify the last input variable in an `iac_pattern`, such as `domain` of `iac_pattern: global/regions/<region>/datacenters/<datacenter>/vcfs/<vcf>/domains/<domain>`, without providing values for `region`, `datacenter` and `vcf`. When not all inputs are provided, the path to retrieve the IaC data is a path with wildcards. The Ansible code will try to use the input(s) provided to find the directory, if the domain name is unique across the whole environment, then the final path to the IaC data can be found. Currently if there is more than one directory found based on the input(s), the playbook will fail.

## IaC load Ansible role

IaC loader Ansible role is named as `load_base_iac` under the `iac`.

```bash
iac
└── load_base_iac
    ├── defaults
    │   └── main.yml
    └── tasks
        ├── generate_full_path.yml
        ├── get_inputs_bypath.yml
        ├── main.yml
        ├── query_partial_paths.yml
        └── read_one_level.yml
```

The entry point to the role is the `main`.

### Load IaC data flow

- `main`

1. generate the full path by calling `generate_full_path.yml`
1. initial all iac vars and the default levels needed for reading the IaC data
1. load all vars by calling `read_one_level.yml` from each level of IaC pattern

- `generate full path`

1. Extract placeholders and variable names from the pattern
1. Replace variable placeholders with variable values in generated path
1. call `query_partial_paths.yml` if the path is a wildcard path
1. return the path

- `read one level data`

1. load all files from the default directory `defaults\config`, store in a temp variable, if the default exists;
1. merges the temp variable with the overall iac vars, which is `all_iac_vars`;
1. load all files from the level directory of a specific component of its `config` folder, store in a temp variable;
1. merges the temp variable with the overall iac vars, which is `all_iac_vars`;
1. repeat the above step 1 to 4, but going down to the next level of the folder structure

- `query partial paths`

1. Find all directories under working dir
1. filter directory based on existing generated wildcard path
1. process the all matched paths
1. find path separator from working_dir for returning the generated path
1. get new IaC path list
1. Reset generated full path from the path list
