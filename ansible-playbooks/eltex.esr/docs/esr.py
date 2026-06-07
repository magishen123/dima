#
# (c) 2015, Peter Sprygada <psprygada@ansible.com>
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


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = """
options:
  authorize:
    description:
      - B(Deprecated)
      - "Starting with Ansible 2.5 we recommend using C(connection: network_cli) and C(become: yes)."
      - HORIZONTALLINE
      - Instructs the module to enter privileged mode on the remote device
        before sending any commands.  If not specified, the device will
        attempt to execute all commands in non-privileged mode. If the value
        is not specified in the task, the value of environment variable
        C(ANSIBLE_NET_AUTHORIZE) will be used instead.
    type: bool
    default: 'no'
  auth_pass:
    description:
      - B(Deprecated)
      - "Starting with Ansible 2.5 we recommend using C(connection: network_cli) and C(become: yes) with C(become_pass)."
      - HORIZONTALLINE
      - Specifies the password to use if required to enter privileged mode
        on the remote device.  If I(authorize) is false, then this argument
        does nothing. If the value is not specified in the task, the value of
        environment variable C(ANSIBLE_NET_AUTH_PASS) will be used instead.
notes:
  - For more information on using Ansible to manage network devices see the :ref:`Ansible Network Guide <network_guide>`_.
"""
