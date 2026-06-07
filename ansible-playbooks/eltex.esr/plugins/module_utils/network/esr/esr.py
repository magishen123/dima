# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2016 Red Hat Inc.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
import json
import os
import re
import tempfile

import paramiko
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.connection import Connection, ConnectionError
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.config import NetworkConfig, _obj_to_raw
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.config import dumps as dumps_ex
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import to_list

ESR_VERSION_RE = (re.compile(r"\d+\.\d+\.(\d+|x)(-#?\w+)?(\(\w+\))?"),)

ESR_ERRORS = [
    {"unknown_command": r"Unknown command"},
    {"illegal_command": r"Illegal command"},
    {"illegal_parameter": r"Illegal parameter"},
    {"command_not_found": r"command not found"},
    {"uncompleted_command": r"command is not completed|Incompleted command"},
    {"login_incorrect": r"Login incorrect"},
    {"account_locked": r"Account locked due to [0-9]+ failed logins"},
    {"impossible_commit": r"error - can't commit configuration."},
    {"impossible_commit_ztp": r"Can[']t.+commit.*synchronization"},
    {"client_error_timeout": r"Client error: timeout"},
    {"error_unknown": r"[uU]nknown error"},
    {"error_invalid_path": r"File-mgr: Invalid source path."},
    {"error_busy": r"File-mgr: Operation source path is busy."},
    {"error_file_mgr": r"File-mgr: Internal error"},
    {"choice_time_expired": r"Time of confirmation has expired"},
    {"conf_pars_fail": r"Configuration parsing failed"},
    {"network_unreachable": r"connect: Network is unreachable"},
    {"connection_refused": r"[ssh|SSH].*: Connection refused"},
    {"key_failed": r"Host key verification failed."},
    {"tftp_error_uboot": r"TFTP error: 'File not found'"},
    {"copy_file_not_found": r".+[Ff]ile not found"},
    {"error_internal": r"Internal error"},
    {"error_unknown_host": r"Unknown host"},
    {"error_syslog_kernel": r"%.+-E-KERNEL.+:"},
    {"alarm_syslog": r"%.+-A-.+:"},
    {"int_dont_exist": r"\S+ \.+ does not exist in system"},
    {"vlan_not_created": r"vlan with id .+ does not exist"},
    {"invalid_range": r"Invalid range"},
    {"console_blocked": r"respawning too fast"},
    {"critical_syslog": r"%\.+-C-\.+:"},
    {"boot_image_failed": r"Boot image set failed"},
    {"kernel_panic": r"end Kernel panic"},
    {"program_error": r"\*\*\* PROGRAM ERROR"},
    {"kernel_trace": r"---\[ end trace"},
    {"error_xload": r"XLOAD ERROR:-1"},
    {"error_pma": r"PMA controller not ready"},
    {"error_secure_boot": r"ErrorStatus = 000001cc"},
    {"error_better_reboot": r"Best choice - restart the device"},
    {"error_disabled_file_mgr": r"File-mgr disabled"},
    {"error_empty_memory": r"EMPTY"},
    {"error_other": r"error - "},
]

CONFIG_PREAMBULE_RE = (
    r"^[#]([!][\/\w]+)\n"  # shebang
    r"^[#]([\d]+)\n"  # version
    r"^[#]([^\n]+)\n"  # name
    r"^[#](\d\d[/]\d\d[/]\d\d\d\d)\n"  # date
    r"^[#](\d\d[:]\d\d[:]\d\d)"  # time
)

ESR_COPY_TRIES = 5

ESR_CONFIG_CAND_MODE = 0o666

ESR_SFTP_FILEPATH = "data/ansible_candidate_config"

CMD_FILE_APPLY_CONFIG = {
    "sendonly": False,
    "prompt": "Do you really want to continue?",
    "check_all": False,
    "command": "copy flash:data/ansible_candidate_config system:candidate-config",
    "answer": "y",
}
CMD_FILE_MERGE_CONFIG = dict(CMD_FILE_APPLY_CONFIG)
CMD_FILE_MERGE_CONFIG.update({"command": "merge flash:data/ansible_candidate_config system:candidate-config"})
CMD_FILE_ROLLBACK_CONFIG = {
    "sendonly": False,
    "command": "rollback",
}
CMD_FILE_DELETE_CONFIG = {
    "sendonly": False,
    "command": "delete flash:data/ansible_candidate_config",
}

_DEVICE_CONFIGS = {}

ESR_PROVIDER_SPEC = {
    "host": dict(),
    "port": dict(type="int"),
    "username": dict(fallback=(env_fallback, ["ANSIBLE_NET_USERNAME"])),
    "password": dict(fallback=(env_fallback, ["ANSIBLE_NET_PASSWORD"]), no_log=True),
    "ssh_keyfile": dict(fallback=(env_fallback, ["ANSIBLE_NET_SSH_KEYFILE"]), type="path"),
    "authorize": dict(fallback=(env_fallback, ["ANSIBLE_NET_AUTHORIZE"]), type="bool"),
    "auth_pass": dict(fallback=(env_fallback, ["ANSIBLE_NET_AUTH_PASS"]), no_log=True),
    "timeout": dict(type="int"),
}
ESR_ARGUMENT_SPEC = {
    "provider": dict(type="dict", options=ESR_PROVIDER_SPEC),
}


_CONFIGS_TEXT = {}


_REGS = {"ESR_VERSIONED_VARS__prepared": False}


class ESRError(Exception):
    """Exception for catching errors on ESR"""

    def __init__(self, output):
        self.error = "Unknown error"
        self.output = output

    def detect_error(self):
        for errors in ESR_ERRORS:
            for error_name, error_pattern in errors.items():
                if re.search(error_pattern, self.output):
                    self.error = error_name
                    break
        return self.error


def get_provider_argspec():
    """Getter for argspec"""
    return ESR_PROVIDER_SPEC


def get_connection(module):
    """Getter for connection"""
    if hasattr(module, "_esr_connection"):
        return module._esr_connection

    capabilities = get_capabilities(module)
    network_api = capabilities.get("network_api")
    if network_api == "cliconf":
        module._esr_connection = Connection(module._socket_path)
    else:
        module.fail_json(msg="Invalid connection type %s" % network_api)

    return module._esr_connection


def get_capabilities(module):
    """Getter for board capabilities"""
    if hasattr(module, "_esr_capabilities"):
        return module._esr_capabilities
    try:
        capabilities = Connection(module._socket_path).get_capabilities()
    except ConnectionError as exc:
        return module.fail_json(msg=ESRError(output=to_text(exc)).detect_error())
    module._esr_capabilities = json.loads(capabilities)
    return module._esr_capabilities


def check_args(module):
    if module.params.get("use_sftp", False):
        if not module.params.get("sftp_user", False) or not module.params.get("sftp_password", False):
            module.warn("SFTP will not be used due to unpresented credentials!")
            module.params["use_sftp"] = False


def get_extended_flag(module):
    connection = get_connection(module)
    try:
        out = connection.get_extended_flag()
    except ConnectionError as exc:
        return module.fail_json(msg=ESRError(output=to_text(exc)).detect_error())
    return out


def get_config(module, source="running", flags=None):
    flag_str = " ".join(to_list(flags))

    try:
        return _DEVICE_CONFIGS[source][flag_str]
    except KeyError:
        connection = get_connection(module)
        try:
            out = connection.get_config(source=source, flags=flags)
        except ConnectionError as exc:
            return module.fail_json(msg=ESRError(output=to_text(exc)).detect_error())

        cfg = to_text(out, errors="surrogate_then_replace").strip()

        try:
            _DEVICE_CONFIGS[source][flag_str] = cfg
        except KeyError:
            _DEVICE_CONFIGS[source] = {flag_str: cfg}

        return cfg


def _append_childs(items, objs):
    if not objs:
        return
    for obj in objs:
        items.append(obj)
        _append_childs(items, obj._children)


def _obj_to_block(objects):
    items = list()

    for obj in objects:
        if not obj._parents:
            items.append(obj)
            _append_childs(items, obj._children)

    return _obj_to_raw(items)


def dumps(objects, output="block", comments=False):
    """We need no 'end' at end of config and 'exit' at end of block.
    But dumping to text stands beside of NetworkConfig,
    so i can't just override some method.
    """
    if output == "block":
        try:
            items = _obj_to_block(objects)
        except RuntimeError as err:
            if err.args[0] != "maximum recursion depth exceeded":
                raise
            raise Exception("Can't dump config object to text")
        return "\n".join(items)

    if output == "block_ex":
        output = "block"

    return dumps_ex(objects=objects, output=output, comments=comments)


def get_running_config(module, flags=None):
    """Load running configuration text from board"""
    key = "running" + str(flags)
    if not _CONFIGS_TEXT.get(key, False):
        _CONFIGS_TEXT.update({key: get_config(module, flags=flags)})

    return _CONFIGS_TEXT[key]


def get_candidate_config(module):
    """Build candidate configuration text"""
    if _CONFIGS_TEXT.get("candidate", False):
        return _CONFIGS_TEXT["candidate"]

    merge = module.params.get("merge", False)
    lines = module.params.get("lines", False)
    src = module.params.get("src", False)

    if lines:
        contents = get_running_config(module)
    elif src:
        contents = src
        for line in contents.split("\n"):
            indent = len(line) - len(line.lstrip())
            if indent % 2 != 0:
                raise Exception("Bad indent. Please, check your source configuration file")
    else:
        # Case for only apply/save task
        contents = get_config(module, source="candidate")

    candidate_obj = NetworkConfig(indent=2, contents=contents)

    # If merge then append src to running config and push it as candidate config
    if merge:
        running_obj = NetworkConfig(indent=2, contents=get_running_config(module))
        for obj in candidate_obj:
            if not obj._children:
                running_obj.add([obj.text], parents=[x.text for x in obj._parents])
        candidate_obj = running_obj
    elif lines:
        parents = module.params.get("parents", list())
        candidate_obj.add(lines, parents=parents)

    _CONFIGS_TEXT.update({"candidate": dumps(candidate_obj, "block")})
    return _CONFIGS_TEXT["candidate"]


def run_commands(module, commands, check_rc=True):
    """Execute array of commands"""
    connection = get_connection(module)
    try:
        return connection.run_commands(commands=commands, check_rc=check_rc)
    except ConnectionError as exc:
        return module.fail_json(msg=ESRError(output=to_text(exc)).detect_error())


def rollback_config(module):
    """Rollback configuration on remote device"""
    if module.check_mode:
        return True
    output = run_commands(module, ["rollback"])
    if not re.search("Configuration has been successfully rolled back", output[0]):
        return False
    return True


def copy_config_sftp(module, source=None, destination=None):
    """Copies file over sftp to remote device"""
    remote_user = module.params["sftp_user"]
    password = module.params["sftp_password"]
    host = os.environ["ESR_SFTP_HOST"]
    port = int(os.environ["ESR_SFTP_PORT"])

    try:
        transport = paramiko.Transport((host, port))
        transport.connect(username=remote_user, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
    except paramiko.ssh_exception.AuthenticationException as err:
        module.warn("SFTP connection failed. " + str(err))
        return False

    success = True
    try:
        sftp.put(source, destination)
        sftp.chmod(destination, ESR_CONFIG_CAND_MODE)
    except OSError as err:
        module.warn("SFTP copying failed. " + str(err))
        success = False

    sftp.close()
    transport.close()
    return success


def delete_config_sftp(module, filepath=None):
    """Delete file over sftp on remote device"""
    remote_user = module.params["sftp_user"]
    password = module.params["sftp_password"]
    host = os.environ["ESR_SFTP_HOST"]
    port = int(os.environ["ESR_SFTP_PORT"])

    try:
        transport = paramiko.Transport((host, port))
        transport.connect(username=remote_user, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)
    except paramiko.ssh_exception.AuthenticationException:
        return False

    success = True
    try:
        sftp.remove(filepath)
    except OSError as err:
        module.warn("SFTP removing failed. " + str(err))
        success = False

    sftp.close()
    transport.close()
    return success


def need_to_save_or_apply(module, when):
    save = False if when == "never" else True
    save = save and when == "always"
    if not save and when in ("applied", "modified"):
        ignore_lines = module.params["diff_ignore_lines"]
        running = NetworkConfig(indent=2, contents=get_running_config(module), ignore_lines=ignore_lines)
        if module.check_mode:
            candidate = NetworkConfig(indent=2, contents=get_candidate_config(module), ignore_lines=ignore_lines)
        else:
            candidate = NetworkConfig(
                indent=2, contents=get_config(module, source="candidate"), ignore_lines=ignore_lines
            )

        save = running.sha1 != candidate.sha1

    return save


def save_config(module, result):
    """Apply and save configuration on board if conditions are met"""
    apply_cfg = need_to_save_or_apply(module, module.params["apply_when"])
    save_cfg = need_to_save_or_apply(module, module.params["save_when"])

    if apply_cfg:
        result["changed"] = True
        if module.check_mode:
            module.warn("Skipping applying configuration due to check_mode.")
        else:
            output = run_commands(module, "commit")
            if not re.search("Configuration has been successfully applied and saved to flash", output[0]):
                if re.search("Nothing to commit in configuration", output[0]):
                    result["changed"] = False
                    return
                warning = extract_warning("commit", output[0])
                if warning or re.search(r"can\'t commit configuration", output[0], flags=re.M | re.I):
                    rollback_config(module)

    if save_cfg:
        result["changed"] = True
        if module.check_mode:
            module.warn("Configuration not copied to non-volatile storage due to check mode.")
        else:
            output = run_commands(module, ["confirm"])
            if not re.search(r"Configuration has been (confirmed|successfully confirmed)", output[0]):
                if re.search("Nothing to confirm in configuration", output[0]):
                    result["changed"] = False
                    return
                warning = extract_warning("confirm", output[0])
                if warning:
                    run_commands(module, ["restore", "rollback"])


def is_able_to_use_sftp(module):
    """Check that board is configured for using SFTP"""
    user = module.params.get("sftp_user", None)
    if user:
        data = get_running_config(module)
        match = re.search(
            r"username " + user + r"(?:(?!exit.).)*(ip sftp enable).*?exit", data, flags=re.MULTILINE | re.DOTALL
        )

        if match and match.group(1):
            return True

    return False


def extract_warning(request, response):
    match = re.search(r"error", response, flags=re.M | re.I)
    if match:
        return r"[" + request + r"]:" + response
    return None


def get_version(module):
    """Get board's software version"""
    capabilities = get_capabilities(module)
    device_info = capabilities.get("device_info")
    version = device_info["network_os_version"]
    return version


def apply_config(module):
    """Apply config from user's data to candidate config"""
    use_merge = module.params.get("merge", False)
    cmd_apply_config = CMD_FILE_MERGE_CONFIG if use_merge else CMD_FILE_APPLY_CONFIG
    output = run_commands(module, cmd_apply_config["command"])[0]
    return output


def edit_config(module, candidate=None, commit=True, replace=None, comment=None, force_cli=False):
    """Upload configuration by SFTP if able or edit board configuration through CLI"""
    warning = ""

    connection = get_connection(module)
    try:
        use_sftp = module.params["use_sftp"]
        reasons = []
        if use_sftp and not force_cli:
            creds_present = bool(module.params.get("sftp_password", "")) and bool(module.params.get("sftp_user", ""))
            if not creds_present:
                reasons.append("unpresented SFTP credentials")
            if creds_present and not is_able_to_use_sftp(module):
                reasons.append("credentials is unpresented on board")
        if force_cli:
            reasons.append("error while trying to send file")
        if reasons:
            use_sftp = False

        if not use_sftp:
            if reasons:
                warning = "Unable to use SFTP! Using CLI instead. Reason: {}.".format(" and ".join(reasons))
            try:
                resp = connection.edit_config(candidate=candidate, commit=commit, replace=replace, comment=comment)
            except ConnectionError as exc:
                return False, module.fail_json(msg=ESRError(output=to_text(exc)).detect_error())

            if resp["warning"]:
                return False, warning + resp["warning"]

            return True, warning

        config_file = tempfile.NamedTemporaryFile(mode="w+", delete=False)
        os.chmod(config_file.name, ESR_CONFIG_CAND_MODE)

        config_file.write(CONFIG_PREAMBULE_RE)

        config_file.write("\n".join(candidate))
        config_file.close()

        status = copy_config_sftp(module, config_file.name, ESR_SFTP_FILEPATH)
        os.unlink(config_file.name)
        if not status:
            return edit_config(
                module, candidate=candidate, commit=commit, replace=replace, comment=comment, force_cli=True
            )

        output = apply_config(module)

        match = re.search(r"(?:(?!\n.).)*[Ee]rror.*", output, flags=re.M | re.S)
        if match and match.group(0):
            warning = "On copy: " + match.group(0)
            status = False
        else:
            match = re.search(r"Configuration loaded successfully.", output)
            if not match:
                match = re.search(r"((?:(?![|]\s*[|]\s*\d+% [(]\d+B[)].).)*)$", output)
                if match and match.group(1):
                    warning = match.group(1)
                else:
                    warning = "Configuration was loaded with unknown error"
                status = False

        if not status:
            run_commands(module, CMD_FILE_ROLLBACK_CONFIG)
        # There isn't cmd to delete files in this version
        run_commands(module, CMD_FILE_DELETE_CONFIG)

        return status, warning
    except ConnectionError as exc:
        return ESRError(output=to_text(exc)).detect_error()


INTERFACES_NAMES = {
    "gi": "GigabitEthernet",
    "te": "TenGigabitEthernet",
    "fa": "FastEthernet",
    "fo": "FortyGigabitEthernet",
    "et": "Ethernet",
    "vl": "Vlan",
    "lo": "loopback",
    "po": "port-channel",
    "nv": "nve",
}


def normalize_interface(name):
    """Return the normalized interface name
    NOTE: We don't use this yet, mb will be useful later
    """
    if not name:
        return None

    def _get_number(name):
        digits = ""
        for char in name:
            if char.isdigit() or char in "/.":
                digits += char
        return digits

    if_type = INTERFACES_NAMES.get(name.lower()[:2], None)

    number_list = name.split(" ")
    if len(number_list) == 2:
        if_number = number_list[-1].strip()
    else:
        if_number = _get_number(name)

    if if_type:
        proper_interface = if_type + if_number
    else:
        proper_interface = name

    return proper_interface
