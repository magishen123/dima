# Eltex ESR Collection

The Ansible Eltex ESR collection includes a variety of Ansible content to help automate the management of Eltex ESR network appliances.

## Supported ESR

ALL

<!--start requires_ansible-->
## Ansible version compatibility

This collection has been tested against following Ansible versions: **>=2.18.1**.

Plugins and modules within a collection may be tested with only specific Ansible versions.
A collection may contain metadata that identifies these versions.
PEP440 is the schema used to describe the versions of Ansible.
<!--end requires_ansible-->

### Supported connections

The Eltex ESR collection supports ``network_cli`` connections.

## Included content

<!--start collection content-->
### Cliconf plugins

Name | Description
---  | ---
[eltex.esr.esr](todo)|Use ESR cliconf to run command on Eltex ESR

### Modules

Name        | Description
---         | ---
esr_config  | module for configuring devices
esr_command | module for send cli command on devices
<!--end collection content-->

<!--start installation-->
## Installing dependencies for this collection
```sh
cd /path/to/ansible-playbooks/
pip install -r requirements.txt
```
<!--end installation-->

<!--start installation-->
## Installing this collection with archive
```sh
cd /path/to/ansible-playbooks/eltex.esr
ansible-galaxy collection build --force .
ansible-galaxy collection install --force eltex-esr-2.1.0.tar.gz
```

## Installing this collection from git repository
Default:
```sh
ansible-galaxy collection install git@github.com:organization/repo_name.git
```
With indication on branch/commit/tag
```sh
ansible-galaxy collection install git@github.com:organization/repo_name.git,develop
```
<!--end installation-->

<!--start example-->

### Example of using modules from the Eltex ESR collection in your playbooks
```yaml
- name: show_system_data
  esr_command:
    commands: show system
```
<!--end example-->

<!--start run_playbooks-->

### Run playbooks
```sh
ansible-playbook <params> <path>
```
<!--end run_playbooks-->

## Release notes
<!--Add a link to a changelog.md file or an external docsite to cover this information. -->
Release notes are available [here](CHANGELOG.rst).

## More information

* [Ansible network resources](https://docs.ansible.com/ansible/latest/network/getting_started/network_resources.html)
* [Ansible Collection overview](https://github.com/ansible-collections/overview)
* [Ansible User guide](https://docs.ansible.com/ansible/latest/user_guide/index.html)
* [Ansible Using collections](https://docs.ansible.com/ansible/latest/user_guide/collections_using.html)
* [Ansible Developer guide](https://docs.ansible.com/ansible/latest/dev_guide/index.html)
* [Ansible Community code of conduct](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)
