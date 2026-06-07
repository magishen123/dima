#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {"metadata_version": "1.1", "status": ["preview"], "supported_by": "network"}


DOCUMENTATION = """
---
module: esr_config
version_added: "2.8"
author: "Eltex"
short_description: Manage Eltex ESR configuration sections
description:
  - Eltex ESR configurations use a simple block indent file syntax
    for segmenting configuration into sections.  This module provides
    an implementation for working with ESR configuration sections in
    a deterministic way.
extends_documentation_fragment: esr
notes:
  - Tested on ESR firmware 1.24.0
  - To speed up configuration loading when using the C(src), it is recommended to use the C(use_sftp).
  - To use the sftp protocol to download the configuration, you must first create a user on the device to work with sftp,.
    specifying 'ip sftp enable' in the settings of this user. This functionality is available on ESR software version 1.6.2 or later.
  - Abbreviated commands are NOT idempotent, see
    L(Network FAQ,../network/user_guide/faq.html#why-do-the-config-modules-always-return-changed-true-with-abbreviated-commands).
options:
  after:
    description:
      - The ordered set of commands to append to the end of the command
        stack if a change needs to be made.  Just like with I(before) this
        allows the playbook designer to append a set of commands to be
        executed after the command set.
  apply_when:
    description:
      - This argument controls the sending of the commit command to the device.
        If apply_when is set to I(always), the commit command will be sent
        to the device regardless of the need to make changes.
        If apply_when is set to I(modified), the commit command
        will be sent to the device only if there are any modified lines.
        If apply_when is set to I(never), the commit command will not be sent to the device.
        If the commit command was sent to the device, the timer
        will be activated (by default 600 seconds), after which the device will
        automatically roll back to the previously valid configuration.
        To stop this timer and apply the changes made, you must use the C(save_when).
    choices: ['always', 'modified', 'never']
    default: 'modified'
  backup:
    description:
      - This argument will cause the module to create a full backup of
        the current running-config from the remote device before any
        changes are made.  The backup file is written to the C(backup)
        folder in the playbook root directory or role root directory, if
        playbook is part of an ansible role. If the directory does not exist,
        it is created.
    type: bool
    default: 'false'
  before:
    description:
      - The ordered set of commands to push on to the command stack if
        a change needs to be made.  This allows the playbook designer
        the opportunity to perform configuration commands prior to pushing
        any changes without affecting how the set of commands are matched
        against the system.
  lines:
    description:
      - The ordered set of commands that should be configured in the
        section.  The commands must be the exact same commands as found
        in the device running-config.  Be sure to note the configuration
        command syntax as some commands are automatically modified by the
        device config parser.
    aliases: ['commands']
  match:
    description:
      - Instructs the module on the way to perform the matching of
        the set of commands against the current device config.  If
        match is set to I(line), commands are matched line by line.  If
        match is set to I(strict), command lines are matched with respect
        to position.  If match is set to I(exact), command lines
        must be an equal match.  Finally, if match is set to I(none), the
        module will not attempt to compare the source configuration with
        the running configuration on the remote device.
    choices: ['line', 'strict', 'exact', 'none']
    default: 'line'
  parents:
    description:
      - The ordered set of parents that uniquely identify the section or hierarchy
        the commands should be checked against.  If the parents argument
        is omitted, the commands are checked against the set of top
        level or global commands.
  replace:
    description:
      - Instructs the module on the way to perform the configuration
        on the device.  If the replace argument is set to I(line) then
        the modified lines are pushed to the device in configuration
        mode.  If the replace argument is set to I(block) then the entire
        command block is pushed to the device in configuration mode if any
        line is not correct.
    default: 'line'
    choices: ['line', 'block']
  rollback:
    description:
      - This argument controls the sending of the rollback command to the device.
        If rollback is set to I(true), then the module send the rollback command before
        making changes. It rollback is set to I(false), then the rollback command will not be
        sent to the device
    default: 'true'
    choices: ['true', 'false']
  save_when:
    description:
      - This argument controls the sending of the confirm command to the device.
        If save_when is set to I(always), then the confirm command will be sent
        regardless of the changes applied. If save_when is set to I(applied),
        then the confirm command will be sent only if any changes were applied to the device
        in accordance with the C(apply_when). If save_when is set to I(never),
        then the confirm command will not be sent to the device and after a specified time (600 seconds)
        the device will automatically roll back to the previously valid configuration.
    choices: ['always', 'applied', 'never']
    default: 'never'
  sftp_user:
    description:
      - Specifies the username to authenticate connection to the remote device.
        This value is used to authenticate the SFTP session.
        Ignored if the C(use_sftp) is set to I(false)
  sftp_password:
    description:
      - Specifies the password to authenticate connection to the remote device.
        This value is used to authenticate the SFTP session.
        Ignored if the C(use_sftp) is set to I(false)
  src:
    description:
      - Specifies the source path to the file that contains the configuration
        or configuration template to load.  The path to the source file can
        either be the full path on the Ansible control host or a relative
        path from the playbook or role root directory.
  use_sftp:
    description:
      - Instructs the module to use sftp protocol to send the configuration
        to remote device. If use_sftp is set to I(false) the configuration will be sent with CLI.
    type: bool
    default: 'true'
  merge:
    description:
      - Resulting configuration will be a merge of running config and C(src).
    type: bool
    default: 'false'
"""

EXAMPLES = """
- name: get full backup from ESR device
  esr_config:
    backup: true

- name: upload config from src to ESR device whith sftp and confirm
  esr_config:
    src: esr-1000.cfg
    use_sftp: true
    sftp_user: sftpuser
    sftp_password: sftppassword
    save_when: applied

- name: render a Jinja2 template onto a ESR device
  esr_config:
    src: esr-config.j2
    save_when: applied

- name: add sftp user
  esr_config:
    save_when: applied
    parents:
      - username sftpuser
    lines:
      - password sftppassword
      - ip sftp enable

- name: configure ip helpers on multiple interfaces
  esr_config:
    save_when: applied
    lines:
      - ip helper-address 192.168.0.10
    parents: "{{ item }}"
  with_items:
    - bridge 1
    - bridge 2
    - bridge 3

 - name: configure nat section
   esr_config:
     save_when: applied
     parents:
       - nat source
       - ruleset NAT_ALL
       - rule 100
     lines:
       - match protocol tcp
       - match source-address any
       - action source-nat pool nat_ip
       - enable

- name: load new rule to existing access-list
  esr_config:
    save_when: applied
    match: exact
    before:
      - ip access-list extended ip-acl
      - no rule 1
    parents:
      - ip access-list extended ip-acl
      - rule 1
    lines:
      - action permit
      - match protocol tcp
      - match destination-port 443
      - enable

- name: for idempotency, use full-form commands
  esr_config:
    parents:
      # - br 6
      - bridge 6
    lines:
      # - ip help 192.168.0.10
      - ip helper-address 192.168.0.10
"""

RETURN = """
updates:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['hostname esr-1000', 'ip ssh server', 'ip telnet server']
commands:
  description: The set of commands that will be pushed to the remote device
  returned: always
  type: list
  sample: ['hostname esr-1000', 'ip ssh server', 'ip telnet server']
backup_path:
  description: The full path to the backup file
  returned: when backup is yes
  type: string
  sample: /playbooks/ansible/backup/esr_config.2019-02-16@22:28:34
"""

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import ConnectionError
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.config import \
    NetworkConfig
from ansible_collections.eltex.esr.plugins.module_utils.network.esr.esr import (
    ESR_ARGUMENT_SPEC)
from ansible_collections.eltex.esr.plugins.module_utils.network.esr.esr import \
    check_args as esr_check_args
from ansible_collections.eltex.esr.plugins.module_utils.network.esr.esr import (
    edit_config, get_candidate_config, get_connection, get_extended_flag,
    get_running_config, rollback_config, run_commands, save_config)


def check_args(module):
    esr_check_args(module)
    if module.params["multiline_delimiter"]:
        if len(module.params["multiline_delimiter"]) != 1:
            module.fail_json(msg="multiline_delimiter value can only be a " "single character")


def extract_commands(module, result):
    """Get diff and build commands from diff and module params"""
    config_diff = None
    commands = []
    running = get_running_config(module)
    candidate = get_candidate_config(module)

    if any((module.params["lines"], module.params["src"])):
        match = module.params["match"]
        replace = module.params["replace"]
        path = module.params["parents"]
        diff_ignore_lines = module.params["diff_ignore_lines"]
        connection = get_connection(module)

        try:
            response = connection.get_diff(
                candidate=candidate,
                running=running,
                diff_match=match,
                diff_ignore_lines=diff_ignore_lines,
                path=path,
                diff_replace=replace,
            )
        except ConnectionError as exc:
            return module.fail_json(msg=to_text(exc, errors="surrogate_then_replace"))

        config_diff = response["config_diff"]

        if config_diff:
            commands = module.params["lines"]

            if module.params["before"]:
                commands[:0] = module.params["before"]

            if module.params["after"]:
                commands.extend(module.params["after"])

            result["commands"] = commands
            result["updates"] = commands

    return commands, config_diff


def main():
    """main entry point for module execution"""
    argument_spec = dict(
        src=dict(type="path"),
        lines=dict(aliases=["commands"], type="list"),
        parents=dict(type="list"),
        before=dict(type="list"),
        after=dict(type="list"),
        match=dict(default="line", choices=["line", "strict", "exact", "none"]),
        replace=dict(default="line", choices=["line", "block"]),
        multiline_delimiter=dict(default="@"),
        defaults=dict(type="bool", default=False),
        backup=dict(type="bool", default=False),
        rollback=dict(type="bool", default=True),
        apply_when=dict(choices=["always", "never", "modified"], default="modified"),
        save_when=dict(choices=["always", "never", "applied"], default="never"),
        diff_ignore_lines=dict(type="list"),
        use_sftp=dict(type="bool", default=True),
        sftp_user=dict(),
        sftp_password=dict(no_log=True),
        merge=dict(type="bool", default=False),
    )

    argument_spec.update(ESR_ARGUMENT_SPEC)

    mutually_exclusive = [("lines", "src"), ("parents", "src")]

    required_if = [
        ("match", "strict", ["lines"]),
        ("match", "exact", ["lines"]),
        ("replace", "block", ["lines"]),
        ("merge", True, ["src"]),
    ]

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=mutually_exclusive,
        required_if=required_if,
        supports_check_mode=True,
    )

    result = {"changed": False}

    check_args(module)
    warnings = list()
    result["warnings"] = warnings

    def faildown(warning=None):
        """Update json before exit"""
        if warning:
            warnings.append(warning)
        result.update({"failed": True})
        module.exit_json(**result)

    diff_ignore_lines = module.params["diff_ignore_lines"]
    config = {
        "running": NetworkConfig(indent=2, contents=get_running_config(module), ignore_lines=diff_ignore_lines),
        "candidate": NetworkConfig(indent=2, contents=get_candidate_config(module), ignore_lines=diff_ignore_lines),
    }

    if module.params["backup"]:
        flags = get_extended_flag(module)
        result["__backup__"] = get_running_config(module, flags=flags)

    if not module.check_mode and module.params["rollback"]:
        if not rollback_config(module):
            faildown("Can't rollback candidate configuration")
            return

    commands, config_diff = extract_commands(module, result)

    replace_conf = module.params.get("src", False) and not module.params.get("merge", False)

    if replace_conf:
        # Compare sha1 couse of config_diff represent only addition commands
        if config["candidate"].sha1 != config["running"].sha1:
            config_diff = True

        commands = get_candidate_config(module).split("\n")

    if config_diff:
        if not module.check_mode:
            response, warning = edit_config(module, candidate=commands, replace=replace_conf)

            if warning:
                warnings.append(warning)
            if not response:
                faildown()
                return
        else:
            result.update({"changed": True})

        if module._diff:
            if config_diff:
                result.update(
                    {"diff": {"before": str(config["running"]) + "\n", "after": str(config["candidate"]) + "\n"}}
                )
                if module.check_mode:
                    module.warn("Unable to perform onboard diff!")
                else:
                    output = run_commands(module, ["show configuration changes"])
                    diff = output[0]
                    result["diff"].update({"onboard_diff": diff})

    save_config(module, result)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
