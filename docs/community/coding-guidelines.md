# Coding Guidelines

## Overview

This document will cover the Ansible and Python Coding Guidelines we'll use. 

Some of the items include:

- Code Organization
- Ansible
- Python
- Credentials
- Procedural Approach

Once you've read through this document, you will be ready to start developing Ansible and Python code

## Code Organization

The code in this repository is primarily written in Python, with a focus on automation using Ansible. This includes Ansible playbooks, roles, collections, custom modules, and plugins. While Python is used for logic and tooling, Ansible provides the orchestration framework. Referencing components like Collections, Plugins, and module_utils to structure and execute tasks cleanly.

### Ansible Collections

Ansible collections in the `VCF with Ansible` repo are used to organize and distribute Ansible content in a modular way, especially plugins.

### Ansible Plugins

- Plugins augment Ansible's core functionality with logic and features that are accessible to all modules. Ansible collections include a number of handy plugins, and you can easily write your own. All plugins must:
    - [ ] be written in Python
    - [ ] raise errors
    - [ ] return strings in unicode
    - [ ] conform to Ansible's configuration and documentation standards

### Hierarchy and Placement of Ansible Components

- Playbooks: `playbooks\`
- Roles: `roles\`
- Action Plugins: `playbooks\action_plugins`
- Modules: `plugins\modules\`
- Module Utils: `plugins\module_utils\`

## Ansible

This section outlines core Ansible components: Playbooks, Roles, Modules, Module Utils, and Action Plugins. It includes what each component does, how to use them effectively, and key best practices and considerations to guide clean and maintainable automation.

### Playbooks

**Overview:**

- All Ansible playbooks are located in the `root` directory of the repository. They are not placed under a `playbooks/` subdirectory because AAP (Ansible Automation Platform) currently does not detect playbooks in subfolders, even when configured via `ansible.cfg`.
- Each playbook serves as an entry point for executing automation tasks.

**Best Practices:**

- Always define a `name:` for the play itself (top-level), not just for tasks.
- Follow a consistent naming convention for playbooks (e.g., `create_*.yml`, `add_*.yml`) for quick identification.
- Include `hosts: localhost` for controller-only automation (_all of our current playbooks are written like this_).
- Use either the tasks or roles section in playbooks, not both
    - A playbook can contain `pre_tasks`, `roles`, `tasks` and `post_tasks` sections.
    - Avoid using both `roles` and `tasks` sections, the latter possibly containing `import_role` or `include_role` tasks.
    - The order of execution between roles and tasks isn't obvious, and hence mixing them should be avoided.
- Keep your playbooks as simple as possible
    - Don't put too much logic in your playbook, put it in your roles (or even in custom modules), and try to limit your playbooks to a list of roles.
    - Roles are meant to be re-used and the structure helps you to make your code re-usable. The more code you put in roles, the higher the chances you, or others, can reuse it.

### Roles

**Overview:**

All ansible roles are located in the `roles/` folder of the repo. The `roles/` folder includes sub-folders so different categories of the roles reside in their own directories. There are:

| Role              | Description                          |
| ----------------- | ------------------------------------ |
| vcf installer     | VCF Installer tasks                  |
| iac               | Infrastructure as Code related tasks |
| ops               | Prep hosts tasks                     |
| prechecks         | ESX precheck tasks                  |
| schema            | JSON schema validation               |
| sddc manager      | All SDDC related tasks               |

**Best Practices:**

- Use the standard role structure (`defaults/`, `vars/`, `tasks/`, etc.) to keep roles modular and predictable.
- Create a meaningful README file for every role (_if not already covered by the HLD, LLD, or Feature page_)
    - The documentation is essential for the success of the content. Place the `README` file in the `root` directory of the role. The README file exists to introduce the user to the purpose of the role and any important information on how to use it, such as credentials that are required.
- Break complex logic into multiple files inside `tasks/`, then include them via `main.yml` to maintain readability.
- Prefix task names in sub-tasks files of roles
    - It is a common practice to have `tasks/main.yml` file including other tasks files, which we'll call sub-tasks files. Make sure that the tasks' names in these sub-tasks files are prefixed with a shortcut reminding of the sub-tasks file's name.
    - Especially in a complex role with multiple (sub-)tasks file, it becomes difficult to understand which task belongs to which file. Adding a prefix, in combination with the role's name automatically added by Ansible, makes it a lot easier to follow and troubleshoot a role play.
    - Example:

    ```YAML
    - name: sub | Some task description
      mytask: [...]
    ```

- Python scripts will typically be called from an Ansible `role`, but can be called directly from `playbooks` for testing
- In the example below, you can see that we're looking for `sddc_manager_dns_configuration` in the `broadcom.vcf` directory.

    ```YAML
    ---
    - name: "Getting DNS Configuration for {{ sddc_manager_hostname }}"
      broadcom.vcf.sddc_manager_dns_configuration:
        sddc_manager_hostname: "{{ sddc_manager_hostname }}"
        sddc_manager_user: "{{ sddc_manager_username }}"
        sddc_manager_password: "{{ sddc_manager_password }}"
      register: dns_config

    - debug: var=dns_config
    ```

### Filter Plugins

**Overview:**

- `filter_plugins` let you define custom filters that can be used in Ansible playbooks, roles, and templates.
- These filters run on the control node and are used to manipulate data such as strings, lists, dictionaries, and nested structures.
- They're used in Jinja2 expressions (e.g., `{{ var | my_filter }}`) and evaluated during template rendering, including in `set_fact`, `template`, `debug`, and variable definitions.
- They extend the built-in Jinja2 filters (like `lower`, `replace`, `length`) with Ansible specific or custom logic to make playbooks more flexible and DRY (Don't Repeat Yourself).
- Refer to the Ansible documentation for more information:
    - [Filter Plugins](https://docs.ansible.com/ansible/latest/plugins/filter.html#filter-plugins)
    - [Using filters to manipulate data](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_filters.html#playbooks-filters)

**Best Practices:**

- Use `filter_plugins` to isolate complex or reusable logic instead of repeating Jinja everywhere.
- Filters should return a value, not print or perform actions.
- Organize them in the `filter_plugins/` directory at the root, role, or collection level.
- Name filters clearly to reflect what they do (e.g., `extract_cluster_networking`).

**Important Considerations:**

- Filter plugins execute locally on the control node, never on the remote target.
- They must define a `FilterModule` class with a `filters()` method that returns a dictionary of `{ filter_name: function }`.
- Can be used anywhere Jinja2 filters are valid, including `set_fact`, `debug`, `vars`, `with_items`, `template`, etc.
- You do not need to import them manually. Ansible loads filters from `filter_plugins/` automatically when running.

### Action Plugins

**Overview:**

- `action_plugins` allow you to customize the behavior of a module before it runs on the target system. These plugins execute on the control node (where Ansible is invoked) and can modify parameters, perform validations, or handle logic that doesn't need to run remotely.
- They are useful when additional processing or decision-making is required before calling a module. For example, to preprocess inputs, apply conditional logic, or gather data from the control environment.
- Custom action plugins are used to extend or override the behavior of built-in modules. By handling local logic separately from remote execution, they help keep modules clean and focused on their primary purpose.
- Refer to the Ansible documentation for more information: [Action Plugins](https://docs.ansible.com/ansible/latest/dev_guide/developing_plugins.html#action-plugins)

**Best Practices:**

- Action Plugins should handle controller-side logic (e.g., preprocessing parameters, file generation, or local validations) before the module is executed on the target.
- Avoid putting core business logic in the action plugin; delegate execution to the module whenever possible.
- Follow consistent naming patterns for clarity (e.g., `<module_name>.py`).
- Use `self._execute_module()` to invoke the actual module after any local logic is complete.
- Only use action plugins if there's a clear justification that can't be handled by the module alone.
- Place all action plugins under the `action_plugins` directory of `vcf_main` since we're only using custom action plugins.

**Important Considerations:**

- Action plugin cannot call another action plugin directly.
- Module cannot call an action plugin
- Action plugin can call a module
- tmp (Temporary Directory)
    - Used mainly when executing remote modules.
    - Often ignored in action plugins because they run on the control node, not the remote target.
- task_vars (Task Variables)
    - Holds all variables related to the current task, including playbook and inventory variables.
    - Can be used inside the action plugin to access dynamic values passed by the user.
    - task_vars is useful if you need access to playbook/global variables, beyond just task arguments.
    - If your plugin only needs the task parameters passed in the playbook, then task_vars is unnecessary and `self._task.args.get()` is sufficient (_This will be primarily what we use_).
    - If you want to access global playbook or inventory variables, then `task_vars` is useful

### Modules

**Overview:**

- A `module` is a reusable, standalone script that Ansible runs on your behalf, either locally or remotely. Modules interact with your local machine, an API, or a remote system to perform specific tasks like changing a database password or spinning up a cloud instance. Each `module` can be used by the Ansible API, or by the `ansible` or `ansible-playbook` programs. A `module` provides a defined interface, accepts arguments, and returns information to Ansible by printing a JSON string to stdout before exiting.
- Simply put, a module is a file consisting of Python code. It can define functions, classes, and variables and can also include runnable code. Any Python file can be referenced as a `module`. A file containing Python code, for example: `sddc_manager_dns_configuration.py`, is called a `module`, and its name would be `sddc_manager_dns_configuration`

**Best Practices:**

- Modules will call the `class` in the `module_util` python script and then call the `function` for the API call.
- Returning structured data to Ansible using `exit_json()`, `fail_json()`..
    - Please see [Ansible Module Utils](https://docs.ansible.com/ansible/latest/reference_appendices/module_utils.html) for more information
- Use consistent output keys (e.g., `changed`, `msg`, `data`) to allow predictability in playbooks.
- Wrap all logic in try/except blocks to catch and report errors gracefully.
- Provide inline documentation for module parameters, return values, and behavior.
- All modules should live under the `modules` directory of the Ansible collection.

**Important Considerations:**

- Modules cannot call other modules, they are independent
- Don't orchestrate multi-step workflows, modules should focus on one job.
- Avoid calling action plugins, they can't be triggered by modules anyway.

### Module Utils

**Overview:**

- In an Ansible collection, `module_utils` are a set of helper modules and utilities designed to assist with the development of custom Ansible modules. They provide common functionality that can be reused across different modules to avoid code duplication and streamline the development process
- When developing a custom module in an Ansible collection, you can include a `module_utils/` directory and place your shared code there. Then, you can import and use these utilities in your modules to maintain modularity and reduce redundancy. This organization helps in managing larger codebase and makes it easier to maintain and update your modules.
- All `module_utils` are stored under the `module_utils` directory of the ansible collection folder.

**Best Practices:**

- Module Utils will contain the API calls, reusable logic, and utility methods to avoid duplication across modules.
- Use descriptive names for utility functions and classes (e.g., `ESXHostConnection`, `get_esx_content()`).
- Place shared logic that spans multiple modules in its own file for clarity and discoverability.
- Located under the `module_utils` directory of the Ansible collection

**Important Considerations:**

- Don't include Ansible context-dependent logic (e.g., calling `exit_json()`, using `task_vars`, or accessing the control node's environment).
- Avoid using them for orchestration or sequencing, focus on pure logic and data handling.
- Don't write anything that has side effects on import (e.g., opening files, setting global config).

### Module Logging

**Overview:**

- Module logging utilities allow you to capture and return detailed logs from your custom Ansible modules for debugging and traceability.
- The log format is:
  
  ```python
  formatter = logging.Formatter('%(levelname)s: %(module)s.%(funcName)s: %(message)s')
  ```

  This prints the log level, module name, function name, and the message, e.g.:
  
  `<LEVEL>: <module>.<function>: <message>`

**Example Output:**

```json
"logs": [
    "DEBUG: network_spec_payload_generator.generate_cluster_network_spec_payload: Generating network spec payload for cluster: w01-cl01",
    "DEBUG: network_spec_payload_generator.get_cluster_networking: Looking up cluster_networking for cluster: w01-cl01",
    "DEBUG: network_spec_payload_generator.get_cluster_networking: Found cluster_networking for cluster: w01-cl01",
    "ERROR: network_spec_payload_generator.generate_cluster_network_spec_payload: Error generating network spec payload for cluster w01-cl01: Cluster networking configuration not found for cluster: w01-cl01"
]
```

**Best Practices:**

- Always initialize the `logs` list and the logger using `get_logger(logs)` at the top level of your Ansible module (the custom modules).
- Pass the logger instance to all utility classes and functions.
- Do **not** create new loggers or log lists inside module_utils or helper functions—this will break and not appear in the Ansible output.

**How to Use:**

```python
    # At the top of your Ansible module (custom module):
    logs = []
    logger = get_logger(logs, name="your_module_name")
    # Pass `logger` to all utility classes/functions that need logging.
    # At the end, return `logs` in your module's output (example: exit_json or fail_json).
```

**Verbosity:**
If you don't want to display the logs for each output for exit_json or fail_json you can update your outputs in order to only deploy the logs at a cert verbosity level.

```python
# To only display logs when Ansible is run with high verbosity (e.g., -vvv), check the module's verbosity:
result = {
    "msg": "Payload generated successfully!",
    "payload": payload
}
if module._verbosity >= 3:
    result["logs"] = logs
module.exit_json(**result)
except Exception as e:
    result = {
        "msg": "Failed to generate payload",
        "error": str(e)
    }
```

### Vars

The `vars` folder contains configuration values that define the behavior of the automation code. These are not runtime or operational inputs, but rather internal settings used to control how the code executes.

Example: `preconfig_prechecks.yml`

```yaml
esx_hosts: ['w01-esx01.example.com']
esx_host_user: root
esx_host_password: "{{ vault_esx_host_password }}"
esx_service_name_ssh: TSM-SSH
esx_service_name_ntp: ntpd
esx_service_state: start
esx_ntp_servers: ['192.168.100.3','192.168.100.4']
validate_certs: False
```

**Note:** _All operational and environment-specific data is now managed through the Infrastructure as Code (IaC) repo. The vars files are now optional and can be used if needed._

## Python

This section covers key Python practices including naming conventions, code organization, reusable functions, and error handling. It outlines common patterns, practical tips, and helpful examples to support writing clear, consistent, and maintainable Python code.

### Naming Conventions

- Naming conventions will also help keep your code consistent and easy to understand and maintain. Python outlines established conventions for naming variables, functions, classes, and modules in their PEP8 guidelines. Names should be self-explanatory, and describe the information in a descriptive way. Some of the Python coding standards and best practices for naming conventions include:  

- Variables & Functions: use all lowercase letters and separate words with underscores.
- Classes: use CapWords/CamelCase, using a capital letter for each new word but not separating the words by spaces or underscores.  

| Type                       | Description                                                                                            |
| -------------------------- |--------------------------------------------------------------------------------------------------------|
| **Constants**              | use all caps                                                                                           |
| **Modules**                | use all lowercase. Add underscores between words if it improves readability.                           |
| **Methods**                | use the function naming rules but indicate internal use methods by adding an underscore before the name. |
| **Single-Character Names** | avoid using these altogether                                                                           |
| **Built-In Names**         | avoid using the Python built-in names, such as naming a variable "list."                                |

### Organizing Code

- As your projects get larger and more complex, organizing your code becomes even more important. This involves thoughtfully structuring your files and directories, using modules and packages effectively, and following established design patterns. Following the Python best practices for organization will help ensure your code maintains readability and is easier to debug and modify.

| Suggestion                              | Description                                                                                                                                                                                        |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Group Related Files**                 | Use modules and packages to organize your code into different groups. A module is a file that will house Python code while a package groups related modules together.                              |
| **Use Import Statements**               | Import statements allow you to use code from one module to another. This is useful for splitting your codebase into logical groups.                                                                |
| **D.R.Y. Code (Don't Repeat Yourself)** | If you find yourself writing the same code in multiple places, you should organize it into a function or class that can be reused more efficiently while also reducing the probability for errors. |
| **Use a Defined Structure**             | Structuring larger projects also helps keep them organized                                                                                                                                         |
| **Relative Imports**                    | Relative imports let you reference code from one module to another                                                                                                                                 |

### Common Functions

#### filter()

- Purpose: Selects elements from an iterable based on a condition.
- Input: A function that returns True or False, and an iterable.
- Output: An iterator with only the items for which the function returned True.

For Loop vs Filter:

```python
for sub in subject_list: 
    if 'CN=' in sub:
        return sub.strip('CN=')
```

```python
list(filter(lambda sub: 'CN=' in sub, subject_list))
```

In the two examples above, you will see the difference between using a for loop and filter. Filter() is a one liner that keeps only the strings in subject_list that contain 'CN='. List() converts the results to a list to be used later.

#### map()

- Purpose: Applies a transformation to each element in an iterable.
- Input: A function and an iterable.
- Output: An iterator with the transformed elements.

Example:

```python
map(lambda sub: sub.strip().removeprefix('CN='), ...)
```

Example with Filter:

```python
list(map(lambda sub: sub.strip().removeprefix('CN='), 
    filter(lambda sub: 'CN=' in sub, subject_list))
)
```

This takes the filtered cert subjects and strips whitespace from each and removes the 'CN=' prefix. List() converts the results to a list to be used later.

### Raising Errors

- You should return errors encountered during plugin execution by using `fail_json`
    - Please see [Ansible Module Utils](https://docs.ansible.com/ansible/latest/reference_appendices/module_utils.html) for more information around `exit_json`, `fail_json`, etc.
- Make sure to use exceptions like `ValueError`, `ConnectionRefused`, etc instead of just always referencing the base `Exception`. Check out the below example of a multiple `except` block
    - Please see [Built-in Exceptions](https://docs.python.org/3/library/exceptions.html) on some possible exceptions

```python
except vim.fault.HostConfigFault as ntp_error:
    raise ValueError(f"Invalid NTP server(s) provided! Please check NTP server(s) provided '{ntp_servers}' and verify they are correct!")
except Exception as ntp_error:
    raise Exception(f"Unexpected error while updating NTP config! Error: {ntp_error}")
```

- In the example `get_dns_configuration` function below, we try `api_client.get_dns_configuration()` and if there are errors or something fails, we'll hit the exception. We'll then return the error back with `fail_json`.

```python
def get_dns_configuration(self):
    try:
        api_response = self.api_client.get_dns_configuration()
        payload_data = api_response.data
        self.module.exit_json(changed=True, meta=payload_data)
    except VcfApiException as e:
        self.module.fail_json(msg=f"Error: {e}", status_code=e.status_code)
```

## Credentials

### Lab

- Credentials **CAN** be stored in clear text in the vars or in Infrastructure as Code (IaC) in the VMware lab
- Credentials must be removed from the var files or IaC files before pushing to develop

### Prod

- Credentials **CANNOT** be stored in clear text!
- Credentials will be stored in [Ansible Vault](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.4/html/getting_started_with_automation_controller/controller-credentials#controller-credentials)

### Exposing Credential and Secret via debug

When using `debug` (`ansible.builtin.debug`) in the ansible role and playbook, there is a high chance to expose the credential and secret, especially when printing out VCF API `payload` or IaC data.

To avoid exposing password in debug, use `redact_debug` custom action module, instead of `debug`. The `redact_debug` can simply replace the `debug` in the most cases.

``` YAML
- broadcom.vcf.redact_debug:
    var: my_vars

- broadcom.vcf.redact_debug:
    msg: "{{ my_vars }}"

- broadcom.vcf.redact_debug:
    msg: "This is my vars: {{ my_vars }}"
```

The following regex will be used to mask the secret:

```YAML
"password", "pwd", ".*_password", "secret", ".*pwd", ".*passwrd", ".*token"
```

Note: more than one variable with passwords in a single `msg` with additional static text is not supported, meaning password will be exposed when there are two or more variables with password in the same `msg`, such as this:

``` YAML
# Not support, secret will display
- broadcom.vcf.redact_debug:
    msg: "Those are 2 vars: {{ my_vars1 }}, {{ my_vars2 }}"

```

## Procedural Approach

- We're not going to worry about re-runs for this first iteration
- If there's failures, we'll have to start the process over
- If we do have time, we may look at being able to re-run at failed stages
