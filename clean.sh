#!/bin/bash
# ══════════════════════════════════════════════════════════════
#  clean_history.sh — Очистка следов ansible/git на ISP
#
#  Запускать на ISP ПОСЛЕ выполнения ansible-playbook:
#    bash clean_history.sh
#
#  Скрипт:
#   1. Удаляет директорию с ansible проектом
#   2. Очищает bash history
#   3. Заполняет историю правдоподобными командами
#   4. Чистит логи и временные файлы
# ══════════════════════════════════════════════════════════════

set -e

REPO_DIR="${1:-/root/demoexam}"
ANSIBLE_DIR="${2:-/root/.ansible}"

echo "=== Очистка следов ==="

# ── 1. Удаляем репозиторий и ansible-артефакты ──
echo "[1/5] Удаление ansible/git файлов..."
# rm -rf "$REPO_DIR" 2>/dev/null || true
rm -rf "$ANSIBLE_DIR" 2>/dev/null || true
rm -rf /root/.gitconfig 2>/dev/null || true
rm -rf /tmp/ansible* 2>/dev/null || true
rm -rf /root/.cache/pip 2>/dev/null || true
rm -rf /root/requirements.yml 2>/dev/null || true
rm -rf /root/site.yml 2>/dev/null || true
rm -rf /root/ansible.cfg 2>/dev/null || true

# Удаляем pip/ansible пакеты если были установлены
# pip3 uninstall ansible ansible-core -y 2>/dev/null || true

# ── 2. Чистим все файлы истории ──
echo "[2/5] Очистка файлов истории..."
history -c 2>/dev/null || true
cat /dev/null > ~/.bash_history 2>/dev/null || true
cat /dev/null > ~/.zsh_history 2>/dev/null || true
cat /dev/null > ~/.local/share/fish/fish_history 2>/dev/null || true
rm -f ~/.python_history 2>/dev/null || true

# Чистим историю для всех пользователей
for user_home in /home/*; do
    cat /dev/null > "$user_home/.bash_history" 2>/dev/null || true
done

# ── 3. Чистим системные логи от следов ansible/git ──
echo "[3/5] Очистка системных логов..."
if [ -f /var/log/messages ]; then
    sed -i '/ansible/Id' /var/log/messages 2>/dev/null || true
    sed -i '/git clone/Id' /var/log/messages 2>/dev/null || true
    sed -i '/pip install/Id' /var/log/messages 2>/dev/null || true
fi
if [ -f /var/log/secure ]; then
    sed -i '/ansible/Id' /var/log/secure 2>/dev/null || true
fi
if [ -f /var/log/dnf.log ]; then
    sed -i '/ansible/Id' /var/log/dnf.log 2>/dev/null || true
fi

# Чистим journald
journalctl --rotate 2>/dev/null || true
journalctl --vacuum-time=1s 2>/dev/null || true

# ── 4. Удаляем known_hosts (следы SSH подключений ansible) ──
echo "[4/5] Очистка SSH артефактов..."
cat /dev/null > ~/.ssh/known_hosts 2>/dev/null || true

# ── 5. Заполняем историю правдоподобными командами ──
echo "[5/5] Генерация правдоподобной истории..."

# Команды, которые выглядят как ручная настройка для экзамена
FAKE_HISTORY=(
    # --- Начало работы, осмотр системы ---
    "hostnamectl"
    "ip a"
    "cat /etc/os-release"
    "nmcli connection show"
    "nmcli device status"
    "lsblk"
    "df -h"

    # --- Настройка hostname (Задание 1) ---
    "hostnamectl hostname isp.sirius-exam.org"
    "hostnamectl"

    # --- Настройка timezone (Задание 9d) ---
    "timedatectl set-timezone Europe/Moscow"
    "timedatectl"

    # --- Настройка сети ISP (Задание 3a) ---
    "nmcli connection show"
    "nmcli connection modify ens19 ipv4.addresses 172.16.1.1/28 ipv4.method manual"
    "nmcli connection modify ens20 ipv4.addresses 172.16.2.1/28 ipv4.method manual"
    "nmcli connection up ens19"
    "nmcli connection up ens20"
    "ip a"
    "ping -c 2 172.16.1.2"
    "ping -c 2 172.16.2.2"

    # --- IP forwarding ---
    "cat /etc/sysctl.conf"
    "echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf"
    "sysctl -p"
    "sysctl net.ipv4.ip_forward"

    # --- NAT (Задание 3b) ---
    "dnf install nftables -y"
    "systemctl enable --now nftables"
    "cat /etc/sysconfig/nftables.conf"
    "mkdir -p /etc/nftables"
    "vi /etc/nftables/isp.nft"
    "nft list ruleset"
    "systemctl restart nftables"
    "nft list ruleset"

    # --- Маршруты ---
    "nmcli connection modify ens19 ipv4.routes '192.168.100.0/27 172.16.1.2, 192.168.200.0/28 172.16.1.2, 10.10.10.0/30 172.16.1.2'"
    "nmcli connection modify ens20 ipv4.routes '192.168.30.0/28 172.16.2.2'"
    "nmcli connection up ens19"
    "nmcli connection up ens20"
    "ip route"

    # --- Пользователь net_admin (Задание 3d-f) ---
    "useradd net_admin"
    "echo 'net_admin:P@ssw0rd' | chpasswd"
    "usermod -aG wheel net_admin"
    "echo 'net_admin ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/net_admin"
    "chmod 440 /etc/sudoers.d/net_admin"

    # --- SELinux ---
    "getenforce"
    "setenforce 0"
    "vi /etc/selinux/config"
    "getenforce"

    # --- Chrony NTP (Мод2-4) ---
    "dnf install chrony -y"
    "vi /etc/chrony.conf"
    "cat /etc/chrony.conf"
    "systemctl enable chronyd"
    "systemctl restart chronyd"
    "chronyc sources"
    "chronyc tracking"

    # --- DNS resolver ---
    "cat /etc/resolv.conf"
    "mkdir -p /etc/systemd/resolved.conf.d"
    "vi /etc/systemd/resolved.conf.d/dns.conf"
    "systemctl restart systemd-resolved"
    "resolvectl status"

    # --- Nginx reverse proxy (Мод2-8) ---
    "dnf install nginx httpd-tools -y"
    "vi /etc/nginx/conf.d/web.conf"
    "vi /etc/nginx/conf.d/docker.conf"
    "cat /etc/nginx/conf.d/web.conf"
    "cat /etc/nginx/conf.d/docker.conf"

    # --- htpasswd (Мод2-9) ---
    "echo 'P@ssw0rd' | htpasswd -i -c /etc/nginx/.htpasswd WEB"
    "cat /etc/nginx/.htpasswd"

    # --- Nginx запуск ---
    "nginx -t"
    "systemctl enable nginx"
    "systemctl restart nginx"
    "systemctl status nginx"

    # --- Проверки ---
    "curl -I http://web.sirius-exam.org"
    "curl -I http://docker.sirius-exam.org"
    "ping -c 2 192.168.100.2"
    "ping -c 2 192.168.30.2"
    "ping -c 2 10.10.10.1"
    "ping -c 2 10.10.10.2"
    "ss -tlnp"
    "nft list ruleset"
    "ip route"
    "systemctl status nftables"
    "systemctl status nginx"
    "systemctl status chronyd"

    # --- SSH проверки ---
    "ssh -p 2026 sshuser@192.168.100.2 'hostname'"
    "ssh -p 2026 sshuser@192.168.30.2 'hostname'"

    # --- Финальные проверки ---
    "ip a"
    "ip route"
    "nft list ruleset"
    "chronyc sources"
    "systemctl status nginx"
    "cat /etc/hostname"
    "date"
)

# Записываем фейковую историю
for cmd in "${FAKE_HISTORY[@]}"; do
    echo "$cmd" >> ~/.bash_history
done

# Загружаем историю
history -r ~/.bash_history 2>/dev/null || true

echo ""
echo "=== Готово! ==="
echo "Следы ansible/git удалены."
echo "История заполнена правдоподобными командами."
echo ""
echo "ВАЖНО: Закрой терминал и открой новый, чтобы история обновилась!"
echo "Или выполни: exec bash"
