#!/bin/bash
# ══════════════════════════════════════════════
#  Bootstrap-скрипт для ISP
#  Устанавливает всё необходимое для запуска Ansible
#  Запуск: bash isp.sh
# ══════════════════════════════════════════════

set -e

dnf install -y wget git tar curl sshpass python3 python3-pip

dnf install -y ansible-core || pip3 install ansible-core

pip3 install paramiko netaddr jmespath

cd "$(dirname "$0")"
ansible-galaxy collection install -r requirements.yml --force

cd ./ansible-playbooks
pip3 install -r requirements.txt
cd eltex.esr
ansible-galaxy collection build --force .
ansible-galaxy collection install --force eltex-esr-2.1.0.tar.gz
rm eltex-esr-2.1.0.tar.gz
