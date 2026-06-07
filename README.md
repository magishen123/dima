0. На ISP установить git и склонировать репозиторий (это надо заучить):
```bash
dnf install -y git
```
```bash
git clone https://gitflic.ru/project/conty111/demoexam
```
1. На ISP: `./isp.sh`
2. Прописать на всех ВМках IP адреса для интерфейсов:

       ISP:

       - интерфейс в инет (auto)
       - интерфейс в HQ-RTR 172.16.1.1/28
       - интерфейс в BR-RTR 172.16.2.1/28

       HQ-RTR:
       ip firewall disabled
       - интерфейс в ISP 172.16.1.2/28
       - интерфейс в HQ-SRV 192.168.100.1/27 
       - интерфейс в HQ-CLI 192.168.200.1/28

       BR-RTR:

       - интерфейс в ISP 172.16.2.2/28
       - интерфейс в BR-SRV 192.168.30.1/28

       HQ-SRV:

       - интерфейс в HQ-RTR 192.168.100.2/27

       BR-SRV:

       - интерфейс в BR-RTR 192.168.30.2/28

2.1. На ISP еще переименовать подключения через nmtui:
- ens18 для интерфейса в инет
- ens19 для интерфейса в HQ-RTR
- ens20 для интерфейса в BR-RTR

3. На всех ВМках задать пароль
- На РЕД ОС: залогиниться, `passwd`, ввести пароль `P@ssw0rd` 2 раза
- На Eltex ESR: залогиниться, `password P@ssw0rd`

4. В файле `inventory/hosts.yml` вверху для ISP указать название интерфейса (не коннекта), а внизу указать нумерацию интерфейсов для eltex:
```
isp_wan_iface: enp7s1
```
```
iface_uplink: gigabitethernet 1/0/3   # to ISP
iface_srv: gigabitethernet 1/0/2      # to HQ-SRV
iface_cli: gigabitethernet 1/0/1      # to HQ-CLI
# И для br-rtr тоже ниже
```
5. На ISP запустить playbook-и:
```bash
ansible-playbook playbooks/01-network.yml
```
И так далее по 1 плэйбуку проверяя выполнение.

> Для docker-а нужно дополнительно убедиться, что предзагружены образа.
> Если не будет образа nextcloud - то найти, где лежит этот образ и загрузить командой `docker load < путь_до_архива_nextcloud.tar` или спуллить самостоятельно (`docker pull nextcloud:latest`)
6. Последний плэйбук `10-ssh.yml` выполнять последним, т.к. после него запустить ansible не получиться.
7. На всякий случай выполните `./clean.sh ; history -d $(history 1)`, чтобы почистить историю команд.
