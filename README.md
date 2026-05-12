# Ansible Collection for VMware Cloud Foundation

The Ansible Collection for VMware Cloud Foundation (`broadcom.vcf`) includes
the modules, plugins, roles, and playbooks developed by Broadcom Professional
Services.

## VMware Cloud Foundation Version Compatibility

This collection supports the following VNware Cloud Foundation versions:

- 9.0.x

## Python Version Compatibility

This collection requires the following Python version:

- 3.12 or later

## Ansible Version Compatibility

This collection supports the following Ansible versions: 

- 2.15.0 or later

## Required Command-Line Tools

- `openssl`
- `ssh-keyscan`
- `ssh-keygen`
- `jq`

## Required Dependencies

To use the collection, you must install the Python library dependencies. 

To install the core dependencies, run the following command:

```shell
make install-deps
```

If you are working on developing and/or testing the collection, additional
dependencies are required.

To install the dependencies, run the following command:

```shell
make install-deps-dev
```

## Support

The Ansible Collection for VMware Cloud Foundation is supported by Broadcom 
Professional Services, not by Broadcom Support.

## License

Copyright (c) Broadcom. All Rights Reserved.

The term "Broadcom" refers solely to the Broadcom Inc. corporate affiliate
that distributes this software.

You are hereby granted a non-exclusive, worldwide, royalty-free license under
Broadcom's copyrights to use, copy, modify, and distribute this software in
source code or binary form for use in connection with Broadcom products.

This copyright notice shall be included in all copies or substantial portions
of the software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
