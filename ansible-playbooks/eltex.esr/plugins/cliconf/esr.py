#
# (c) 2017 Red Hat Inc.
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
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import re

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_text
from ansible.module_utils.common._collections_compat import Mapping
from ansible.plugins.cliconf import CliconfBase, enable_mode
from ansible.utils.display import Display
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.config import NetworkConfig, dumps
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import to_list
from ansible_collections.eltex.esr.plugins.module_utils.network.esr.esr import extract_warning

display = Display()

CMD_RESET_CONFIG = {
    "sendonly": False,
    "prompt": "Do you really want to continue?",
    "check_all": False,
    "command": "copy {ESR_CONFIG_DEFPATH} {ESR_CONFIG_CANDPATH}",
    "answer": "y",
    "prompt_retry_check": False,
}
CMD_CONFIGURE = {"sendonly": False, "command": "configure"}
CMD_END = {"sendonly": False, "command": "end"}
CMD_ROLLBACK = {"sendonly": False, "command": "rollback"}
CMD_SIGINT = {"sendonly": True, "command": chr(3)}

ESR_SUPPORTED_FLAGS = "extended"


class Cliconf(CliconfBase):

    def send_command(self, **kwargs):
        """Executes a cli command and returns the results
        This method will execute the CLI command on the connection and return
        the results to the caller.  The command output will be returned as a
        string
        """
        try:
            resp = super(Cliconf, self).send_command(**kwargs)
        except Exception as err:
            # Check message due to exception is always Exception
            if "timeout" in str(err):
                super(Cliconf, self).send_command(**CMD_SIGINT)

            raise err

        if len(resp.split("\n")) > 1:
            output = resp.split("\n")[1:]
            regexp = re.compile(r"\d{4}\\-\d{2}\\-\d{2}T\d{2}\\:\d{2}\\:\d{2}\+\d{2}\\:\d{2}.*")

            output = [line for line in output if not regexp.search(line)]

            return "\n".join(output)

        return ""

    @enable_mode
    def get_config(self, source="running", flags=None):
        if not source or source not in ("running", "candidate"):
            raise ValueError("fetching configuration from %s is not supported" % source)

        if flags and flags not in ESR_SUPPORTED_FLAGS:
            raise ValueError("fetching configuration witch flag %s is not supported" % flags)

        resp = ""

        cmd = "show " + source + "-config"
        if flags is not None:
            cmd += " " + flags

        resp += self.send_command(command=cmd)

        return resp

    def get_diff(
        self, candidate=None, running=None, diff_match="line", diff_ignore_lines=None, path=None, diff_replace="line"
    ):
        """
        Generate diff between candidate and running configuration. If the
        remote host supports onbox diff capabilities ie. supports_onbox_diff in that case
        candidate and running configurations are not required to be passed as argument.
        In case if onbox diff capability is not supported candidate argument is mandatory
        and running argument is optional.
        :param candidate: The configuration which is expected to be present on remote host.
        :param running: The base configuration which is used to generate diff.
        :param diff_match: Instructs how to match the candidate configuration with current device configuration
                      Valid values are 'line', 'strict', 'exact', 'none'.
                      'line' - commands are matched line by line
                      'strict' - command lines are matched with respect to position
                      'exact' - command lines must be an equal match
                      'none' - will not compare the candidate configuration with the running configuration
        :param diff_ignore_lines: Use this argument to specify one or more lines that should be
                                  ignored during the diff.  This is used for lines in the configuration
                                  that are automatically updated by the system.  This argument takes
                                  a list of regular expressions or exact line matches.
        :param path: The ordered set of parents that uniquely identify the section or hierarchy
                     the commands should be checked against.  If the parents argument
                     is omitted, the commands are checked against the set of top
                    level or global commands.
        :param diff_replace: Instructs on the way to perform the configuration on the device.
                        If the replace argument is set to I(line) then the modified lines are
                        pushed to the device in configuration mode.  If the replace argument is
                        set to I(block) then the entire command block is pushed to the device in
                        configuration mode if any line is not correct.
        :return: Configuration diff in  json format.
               {
                   'config_diff': '',
               }

        """
        diff = {}
        device_operations = self.get_device_operations()
        option_values = self.get_option_values()

        if candidate is None and device_operations["supports_generate_diff"]:
            raise ValueError("candidate configuration is required to generate diff")

        if diff_match not in option_values["diff_match"]:
            raise ValueError(
                "'match' value %s in invalid, valid values are %s"
                % (diff_match, ", ".join(option_values["diff_match"]))
            )

        if diff_replace not in option_values["diff_replace"]:
            raise ValueError(
                "'replace' value %s in invalid, valid values are %s"
                % (diff_replace, ", ".join(option_values["diff_replace"]))
            )

        # prepare candidate configuration
        candidate_obj = NetworkConfig(indent=2)
        candidate_trim_config = "\n".join([line.lstrip() for line in candidate.split("\n")])
        candidate_obj.load(candidate_trim_config)

        if running and diff_match != "none":
            # running configuration
            running_trim_config = "\n".join([line.lstrip() for line in running.split("\n")])
            running_obj = NetworkConfig(indent=2, contents=running_trim_config, ignore_lines=diff_ignore_lines)
            configdiffobjs = candidate_obj.difference(running_obj, path=path, match=diff_match, replace=diff_replace)

        else:
            configdiffobjs = candidate_obj.items

        diff["config_diff"] = dumps(configdiffobjs, "commands") if configdiffobjs else ""
        return diff

    @enable_mode
    def edit_config(self, candidate=None, commit=True, replace=None, comment=None):
        resp = {"request": [], "response": []}
        operations = self.get_device_operations()
        self.check_edit_config_capability(operations, candidate, commit, replace, comment)

        def send_and_remember_command(cmd):
            output = self.send_command(**cmd)
            resp["request"].append(output)
            resp["response"].append(cmd["command"])
            return extract_warning(cmd["command"], output)

        if not commit:
            raise ValueError("check mode is not supported")

        if replace:
            send_and_remember_command(CMD_RESET_CONFIG)

        send_and_remember_command(CMD_CONFIGURE)

        for line in to_list(candidate):
            if not isinstance(line, Mapping):
                line = {"command": line}

            cmd = line["command"]
            if cmd != "end" and not cmd.startswith("#"):
                resp["warning"] = send_and_remember_command(line)
                if resp["warning"]:
                    break

        send_and_remember_command(CMD_END)
        if resp["warning"]:
            send_and_remember_command(CMD_ROLLBACK)

        return resp

    def get(self, **kwargs):
        if not kwargs.get("command"):
            raise ValueError("must provide value of command to execute")
        if kwargs.get("output"):
            raise ValueError("'output' value %s is not supported for get" % kwargs.get("output"))
        return self.send_command(**kwargs)

    def get_device_info(self):
        device_info = {}
        device_info["network_os"] = "esr"

        reply = self.get(command="show version")
        data = to_text(reply, errors="surrogate_or_strict").strip()

        match = re.search(r"SW version:\n\s+(\S+)", data)
        if match:
            device_info["network_os_version"] = match.group(1)

        return device_info

    def get_device_operations(self):
        supports = {
            "supports_diff_replace": True,
            "supports_commit": False,
            "supports_rollback": False,
            "supports_defaults": True,
            "supports_onbox_diff": False,
            "supports_commit_comment": False,
            "supports_multiline_delimiter": True,
            "supports_diff_match": True,
            "supports_diff_ignore_lines": True,
            "supports_generate_diff": True,
            "supports_replace": True,
            "supports_config_replace": False,
        }

        return supports

    def get_option_values(self):
        return {
            "format": ["text"],
            "diff_match": ["line", "strict", "exact", "none"],
            "diff_replace": ["line", "block"],
            "output": [],
        }

    def get_capabilities(self):
        result = dict()
        result["rpc"] = self.get_base_rpc() + ["get_diff", "run_commands", "get_extended_flag"]
        result["network_api"] = "cliconf"
        result["device_info"] = self.get_device_info()
        result["device_operations"] = self.get_device_operations()
        result.update(self.get_option_values())
        return json.dumps(result)

    def run_commands(self, commands=None, check_rc=True):
        if commands is None:
            raise ValueError("'commands' value is required")

        responses = list()
        for cmd in to_list(commands):
            if not isinstance(cmd, Mapping):
                cmd = {"command": cmd}

            output = cmd.pop("output", None)
            if output:
                raise ValueError("'output' value %s is not supported for run_commands" % output)

            try:
                out = self.send_command(**cmd)

            except AnsibleConnectionFailure as e:
                if check_rc:
                    raise
                out = getattr(e, "err", e)

            responses.append(out)

        return responses

    def get_extended_flag(self):
        """
        The method identifies the filter that should be used to fetch running-configuration
        with defaults.
        :return: valid default filter
        """
        out = self.get(command="show running-config ?")
        out = to_text(out, errors="surrogate_then_replace")
        self.get(command="\n")

        commands = set()
        for line in out.splitlines():
            if line.strip():
                commands.add(line.strip().split()[0])

        return "extended" if "extended" in commands else None
