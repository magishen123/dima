#
# (c) 2016 Red Hat Inc.
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
from ansible.module_utils._text import to_bytes, to_text
from ansible.plugins.terminal import TerminalBase
from ansible.utils.display import Display

display = Display()


class TerminalModule(TerminalBase):

    terminal_stdout_re = [
        re.compile(rb"[\r\n]?\S+\(?\S*\)?\w+# ?$"),
        re.compile(rb"[\r\n]\S+\(config\)#"),
        re.compile(rb"[\r\n]\S+#"),
        re.compile(rb"[\r\n]\S+\(config\S+\)#"),
        re.compile(rb"[\r\n]?\(acs-?.*\)$"),
        re.compile(rb"[\r\n]\$"),
        re.compile(rb"~]"),
        re.compile(rb"\(y/N\)"),
    ]

    terminal_stderr_re = [
        re.compile(rb"Unknown command"),
        re.compile(rb"Illegal command"),
        re.compile(rb"Illegal parameter"),
        re.compile(rb"command not found"),
        re.compile(rb"command is not completed|Incompleted command"),
        re.compile(rb"Login incorrect"),
        re.compile(rb"Account locked due to [0-9]+ failed logins"),
        re.compile(rb"error - can't commit configuration."),
        re.compile(rb"Can[']t.+commit.*synchronization"),
        re.compile(rb"Client error: timeout"),
        re.compile(rb"[uU]nknown error"),
        re.compile(rb"File-mgr: Invalid source path."),
        re.compile(rb"File-mgr: Operation source path is busy."),
        re.compile(rb"File-mgr: Internal error"),
        re.compile(rb"Time of confirmation has expired"),
        re.compile(rb"Configuration parsing failed"),
        re.compile(rb"connect: Network is unreachable"),
        re.compile(rb"[ssh|SSH].*: Connection refused"),
        re.compile(rb"Host key verification failed."),
        re.compile(rb"TFTP error: 'File not found'"),
        re.compile(rb".+[Ff]ile not found"),
        re.compile(rb"Internal error"),
        re.compile(rb"Unknown host"),
        re.compile(rb"%.+-E-KERNEL.+:"),
        re.compile(rb"%.+-A-.+:"),
        re.compile(rb"\S+ \.+ does not exist in system"),
        re.compile(rb"vlan with id .+ does not exist"),
        re.compile(rb"Invalid range"),
        re.compile(rb"respawning too fast"),
        re.compile(rb"%\.+-C-\.+:"),
        re.compile(rb"Boot image set failed"),
        re.compile(rb"end Kernel panic"),
        re.compile(rb"\*\*\* PROGRAM ERROR"),
        re.compile(rb"---\[ end trace"),
        re.compile(rb"XLOAD ERROR:-1"),
        re.compile(rb"PMA controller not ready"),
        re.compile(rb"ErrorStatus = 000001cc"),
        re.compile(rb"Best choice - restart the device"),
        re.compile(rb"File-mgr disabled"),
        re.compile(rb"EMPTY"),
        re.compile(rb"error - "),
    ]

    def on_open_shell(self):
        self._exec_cli_command(b"terminal datadump")

    def on_become(self, passwd=None):
        if self._get_prompt().strip().endswith(b"#"):
            return
        cmd = {"command": "enable"}
        if passwd:
            # Note: python-3.5 cannot combine u"" and r"" together.  Thus make
            # an r string and use to_text to ensure it's text on both py2 and py3.
            cmd["prompt"] = to_text(r"[\r\n]Password: ?$", errors="surrogate_or_strict")
            cmd["answer"] = passwd
            cmd["prompt_retry_check"] = True
        try:
            self._exec_cli_command(to_bytes(json.dumps(cmd), errors="surrogate_or_strict"))
            prompt = self._get_prompt()
            if prompt is None or not prompt.endswith(b"#"):
                raise AnsibleConnectionFailure(
                    "failed to elevate privilege to enable mode still at prompt [%s]" % prompt
                )
        except AnsibleConnectionFailure as e:
            prompt = self._get_prompt()
            raise AnsibleConnectionFailure(
                "unable to elevate privilege to enable mode, at prompt [%s] with error: %s" % (prompt, e.message)
            )

    def on_unbecome(self):
        prompt = self._get_prompt()
        if prompt is None:
            # if prompt is None most likely the terminal is hung up at a prompt
            return

        if b"(config" in prompt:
            self._exec_cli_command(b"exit")

        if prompt.endswith(b"#"):
            self._exec_cli_command(b"logout")
