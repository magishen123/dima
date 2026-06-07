# Настройка стенда — sirius-exam.org

## Пакеты

**ISP:** `dnf install -y nftables nginx httpd-tools chrony`
**HQ-SRV:** `dnf install -y bind bind-utils chrony mdadm nfs-utils nfs4-acl-tools httpd php php-mysqlnd mariadb-server mariadb`
**HQ-CLI:** `dnf install -y chrony nfs-utils samba-client`
**BR-SRV:** `dnf install -y chrony docker-ce docker-ce-cli docker-compose-plugin docker-compose samba nginx openssl`

---

## Все хосты Linux (ISP, HQ-SRV, HQ-CLI, BR-SRV)

```bash
hostnamectl hostname <FQDN>   # isp/hq-srv/hq-cli/br-srv .sirius-exam.org
timedatectl set-timezone Europe/Moscow
setenforce 0
```
`/etc/selinux/config`
```
...
SELINUX=disabled
...
```
`/etc/systemd/resolved.conf.d/dns.conf`:
```ini
[Resolve]
DNS=192.168.100.2 77.88.8.7
FallbackDNS=77.88.8.3
Domains=sirius-exam.org
```
`systemctl restart systemd-resolved`

---

## ISP

### IP Forwarding + NAT

```bash
sysctl -w net.ipv4.ip_forward=1
`/etc/sysctl.conf`
```conf
...
net.ipv4.ip_forward=1
```
`mkdir -p /etc/nftables`

`/etc/nftables/isp.nft`:
```
table inet nat {
        chain POSTROUTING {
        type nat hook postrouting priority srcnat;
        oifname "ens18" masquerade
        }
}
```
В `/etc/sysconfig/nftables.conf` добавить: `include "/etc/nftables/isp.nft"`
`systemctl enable --now nftables && systemctl restart nftables`
```bash
nmcli connection modify ens19 ipv4.routes "192.168.100.0/27 172.16.1.2, 192.168.200.0/28 172.16.1.2"
nmcli connection modify ens20 ipv4.routes "192.168.30.0/28 172.16.2.2"
nmcli connection up ens19 && nmcli connection up ens20
```

```bash
useradd net_admin
echo 'net_admin:P@ssw0rd' | chpasswd
usermod -aG wheel net_admin

```
`/etc/sudoers.d/net_admin`:
```
net_admin ALL=(ALL) NOPASSWD: ALL
```
`chmod 440 /etc/sudoers.d/net_admin`

### Chrony (сервер)

`/etc/chrony.conf`:
```
server ntp1.vniiftri.ru iburst prefer
local stratum 5
allow 0.0.0.0/0
driftfile /var/lib/chrony/drift
makestep 1.0 3
rtcsync
logdir /var/log/chrony
```
`systemctl enable --now chronyd && systemctl restart chronyd`

### Nginx reverse proxy

`/etc/nginx/conf.d/web.conf`:
```nginx
server {
    listen 80;
    server_name web.sirius-exam.org;
    location / {
        proxy_pass http://172.16.1.2:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP $remote_addr;
        auth_basic "Restricted area";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
```

`/etc/nginx/conf.d/docker.conf`:
```nginx
server {
    listen 80;
    server_name docker.sirius-exam.org;
    location / {
        proxy_pass http://172.16.2.2:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

SSL для Nextcloud:
```bash
mkdir -p /etc/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/nginx/ssl/nextcloud.key -out /etc/nginx/ssl/nextcloud.crt -subj "/C=RU/ST=Moscow/L=Moscow/O=Sirius/OU=IT/CN=nextcloud.sirius-exam.org"
```

`/etc/nginx/conf.d/nextcloud.conf`:
```nginx
server {
    listen 443 ssl http2;
    server_name nextcloud.sirius-exam.org;
    ssl_certificate /etc/nginx/ssl/nextcloud.crt;
    ssl_certificate_key /etc/nginx/ssl/nextcloud.key;
    client_max_body_size 512M;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    location / {
        proxy_pass http://172.16.2.2:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_request_buffering off;
    }
}
```

### htpasswd + запуск

```bash
echo 'P@ssw0rd' | htpasswd -i -c /etc/nginx/.htpasswd WEB
nginx -t
systemctl enable --now nginx
systemctl restart nginx
```

---

## HQ-RTR (Eltex ESR)

```
configure

hostname hq-rtr.sirius-exam.org

username net_admin
password P@ssw0rd
privilege 15
exit

domain lookup enable
domain nameserver 192.168.100.2
domain nameserver 77.88.8.7
domain name sirius-exam.org
security passwords default-expired
ip ssh server
ntp enable
ntp broadcast-client enable

interface gigabitethernet 1/0/3
ip firewall disable
ip address 172.16.1.2/28
exit

interface gigabitethernet 1/0/2
ip firewall disable
ip address 192.168.100.1/27
exit

interface gigabitethernet 1/0/1
ip firewall disable
ip address 192.168.200.1/28
exit

key-chain auth_ospf
key 1
key-string ascii-text P@ssw0rd
exit
exit

tunnel gre 1
ttl 64
local address 172.16.1.2
remote address 172.16.2.2
ip address 10.10.10.1/30
ip firewall disable
ip ospf instance 1
ip ospf authentication key-chain auth_ospf
ip ospf authentication algorithm md5
ip ospf
enable
exit

router ospf 1
router-id 1.1.1.1
area 0.0.0.0
network 192.168.100.0/27
network 192.168.200.0/28
enable
exit
enable

object-group network LOCAL_NET
ip address-range 192.168.100.2-192.168.100.30
ip address-range 192.168.200.2-192.168.200.14
exit
object-group network PUBLIC_POOL
ip address-range 172.16.1.3-172.16.1.7
exit

interface gigabitethernet 1/0/3
ip nat proxy-arp PUBLIC_POOL
exit

nat source
pool TRANSLATE_ADDRESS
ip address-range 172.16.1.3-172.16.1.7
exit
ruleset SNAT
to interface gigabitethernet 1/0/3
rule 1
match source-address object-group network LOCAL_NET
action source-nat pool TRANSLATE_ADDRESS
enable
exit
exit
exit

ip dhcp-server
ip dhcp-server pool CLI_POOL
network 192.168.200.0/28
domain-name sirius-exam.org
address-range 192.168.200.2-192.168.200.14
default-router 192.168.200.1
dns-server 192.168.100.2
exit
exit

object-group service HTTP_PORT
port-range 8080
exit
object-group service SSH_PORT
port-range 2026
exit

nat destination
pool HQ_WEB_POOL
ip address 192.168.100.2
ip port 80
exit
pool HQ_SSH_POOL
ip address 192.168.100.2
ip port 2026
exit
ruleset DNAT
from default
rule 10
match destination-address address-range 172.16.1.2
match protocol tcp
match destination-port object-group HTTP_PORT
action destination-nat pool HQ_WEB_POOL
enable
exit
rule 20
match destination-address address-range 172.16.1.2
match protocol tcp
match destination-port object-group SSH_PORT
action destination-nat pool HQ_SSH_POOL
enable
exit
exit
exit

ip route 0.0.0.0/0 172.16.1.1 200

commit
confirm
```

---

## BR-RTR (Eltex ESR)

```
configure

hostname br-rtr.sirius-exam.org

username net_admin
password P@ssw0rd
privilege 15
exit

domain lookup enable
domain nameserver 192.168.100.2
domain nameserver 77.88.8.7
domain name sirius-exam.org
security passwords default-expired
ip ssh server
ntp enable
ntp broadcast-client enable

interface gigabitethernet 1/0/3
ip firewall disable
ip address 172.16.2.2/28
exit

interface gigabitethernet 1/0/2
ip firewall disable
ip address 192.168.30.1/28
exit

key-chain auth_ospf
key 1
key-string ascii-text P@ssw0rd
exit
exit

tunnel gre 1
ttl 64
local address 172.16.2.2
remote address 172.16.1.2
ip address 10.10.10.2/30
ip firewall disable
ip ospf instance 1
ip ospf authentication key-chain auth_ospf
ip ospf authentication algorithm md5
ip ospf
enable
exit

router ospf 1
router-id 2.2.2.2
area 0.0.0.0
network 192.168.30.0/28
enable
exit
enable

object-group network LOCAL_NET
ip address-range 192.168.30.2-192.168.30.14
exit
object-group network PUBLIC_POOL
ip address-range 172.16.2.3-172.16.2.7
exit

interface gigabitethernet 1/0/3
ip nat proxy-arp PUBLIC_POOL
exit

nat source
pool TRANSLATE_ADDRESS
ip address-range 172.16.2.3-172.16.2.7
exit
ruleset SNAT
to interface gigabitethernet 1/0/3
rule 1
match source-address object-group network LOCAL_NET
action source-nat pool TRANSLATE_ADDRESS
enable
exit
exit
exit

object-group service HTTP_PORT
port-range 8080
exit
object-group service SSH_PORT
port-range 2026
exit

nat destination
pool BR_WEB_POOL
ip address 192.168.30.2
ip port 8080
exit
pool BR_SSH_POOL
ip address 192.168.30.2
ip port 2026
exit
ruleset DNAT
from default
rule 10
match destination-address address-range 172.16.2.2
match protocol tcp
match destination-port object-group HTTP_PORT
action destination-nat pool BR_WEB_POOL
enable
exit
rule 20
match destination-address address-range 172.16.2.2
match protocol tcp
match destination-port object-group SSH_PORT
action destination-nat pool BR_SSH_POOL
enable
exit
exit
exit

ip route 0.0.0.0/0 172.16.2.1 200

commit
confirm
```

---

## HQ-SRV

### sshuser + SSH

```bash
useradd -u 2026 sshuser
usermod -aG wheel sshuser
echo 'sshuser:P@ssw0rd' | chpasswd
echo 'sshuser ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/sshuser
chmod 440 /etc/sudoers.d/sshuser
```

В `/etc/ssh/sshd_config` изменить:
```
Port 2026
MaxAuthTries 2
AllowUsers sshuser
PasswordAuthentication yes
Banner /etc/ssh/banner
```

`echo 'Authorized access only' > /etc/ssh/banner`
`systemctl restart sshd`

### Chrony (клиент)

`/etc/chrony.conf`:
```
server 172.16.1.1 iburst
driftfile /var/lib/chrony/drift
makestep 1.0 3
rtcsync
logdir /var/log/chrony
```
`systemctl enable --now chronyd`
`systemctl restart chronyd`

### BIND DNS

`/etc/named.conf`:
```
options {
	listen-on port 53 { any; };
	listen-on-v6 port 53 { none; };
	directory "/var/named";
	dump-file "/var/named/data/cache_dump.db";
	statistics-file "/var/named/data/named_stats.txt";
	memstatistics-file "/var/named/data/named_mem_stats.txt";
	secroots-file "/var/named/data/named.secroots";
	recursing-file "/var/named/data/named.recursing";
	allow-query { any; };
	recursion yes;
	dnssec-validation no;
	forward first;
	forwarders { 77.88.8.7; };
	managed-keys-directory "/var/named/dynamic";
	pid-file "/run/named/named.pid";
	session-keyfile "/run/named/session.key";
};
logging { channel default_debug { file "data/named.run"; severity dynamic; }; };
zone "." IN { type hint; file "named.ca"; };
zone "sirius-exam.org" { type master; file "master/sirius-exam.org"; };
zone "100.168.192.in-addr.arpa" { type master; file "master/100.168.192.in-addr.arpa"; };
zone "200.168.192.in-addr.arpa" { type master; file "master/200.168.192.in-addr.arpa"; };
zone "30.168.192.in-addr.arpa" { type master; file "master/30.168.192.in-addr.arpa"; };
include "/etc/named.rfc1912.zones";
include "/etc/named.root.key";
```

```bash
mkdir -p /var/named/master
chown root:named /var/named/master
chmod 750 /var/named/master
```

`/var/named/master/sirius-exam.org`:
```
$TTL 604800
sirius-exam.org. IN SOA ns01.sirius-exam.org. root.sirius-exam.org. (2026052801 600 3600 1w 360)
        IN NS ns01.sirius-exam.org.
ns01    IN A  192.168.100.2
hq-srv  IN A  192.168.100.2
hq-rtr  IN A  192.168.100.1
hq-cli  IN A  192.168.200.2
br-srv  IN A  192.168.30.2
br-rtr  IN A  192.168.30.1
isp     IN A  172.16.1.1
web     IN CNAME isp.sirius-exam.org.
docker  IN CNAME isp.sirius-exam.org.
```

`/var/named/master/100.168.192.in-addr.arpa`:
```
$TTL 604800
100.168.192.in-addr.arpa. IN SOA ns01.sirius-exam.org. root.sirius-exam.org. (2026052801 600 3600 1w 360)
        IN NS ns01.sirius-exam.org.
2       IN PTR hq-srv.sirius-exam.org.
1       IN PTR hq-rtr.sirius-exam.org.
```

`/var/named/master/200.168.192.in-addr.arpa`:
```
$TTL 604800
200.168.192.in-addr.arpa. IN SOA ns01.sirius-exam.org. root.sirius-exam.org. (2026052801 600 3600 1w 360)
        IN NS ns01.sirius-exam.org.
2       IN PTR hq-cli.sirius-exam.org.
1       IN PTR hq-rtr.sirius-exam.org.
```

`/var/named/master/30.168.192.in-addr.arpa`:
```
$TTL 604800
30.168.192.in-addr.arpa. IN SOA ns01.sirius-exam.org. root.sirius-exam.org. (2026052801 600 3600 1w 360)
        IN NS ns01.sirius-exam.org.
2       IN PTR br-srv.sirius-exam.org.
1       IN PTR br-rtr.sirius-exam.org.
```

```bash
chown root:named /var/named/master/* && chmod 640 /var/named/master/*
systemctl enable --now named && systemctl restart named
```

После запуска BIND — перенастроить resolved на HQ-SRV:

`/etc/systemd/resolved.conf.d/dns.conf`:
```ini
[Resolve]
DNS=127.0.0.1
FallbackDNS=77.88.8.7
Domains=sirius-exam.org
```
`systemctl restart systemd-resolved`

### RAID 0

```bash
# Определить диски: lsblk (sdb+sdc или vdb+vdc)
mdadm --create /dev/md0 --level=0 --raid-devices=2 /dev/sdb /dev/sdc --run
mdadm --detail --scan >> /etc/mdadm.conf
mkfs.ext4 /dev/md0
mkdir -p /raid
mount /dev/md0 /raid
echo '/dev/md0  /raid  ext4  defaults  0  2' >> /etc/fstab
```

### NFS-сервер

```bash
mkdir -p /raid/nfs
chmod 777 /raid/nfs
```

`/etc/exports`:
```
/raid/nfs       192.168.200.0/28(rw,no_root_squash)
```

`systemctl enable --now nfs-server && systemctl restart nfs-server && exportfs -arv`

### Apache + MariaDB (веб-приложение)

```bash
mkdir -p /mnt/cdrom
mount -o ro /dev/sr0 /mnt/cdrom
cp -r /mnt/cdrom/web/ /home/user/web/

systemctl enable --now mariadb
mysql -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'P@ssw0rd';"
mysql -u root -pP@ssw0rd -e "DELETE FROM mysql.user WHERE User=''; DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost','127.0.0.1','::1'); DROP DATABASE IF EXISTS test; FLUSH PRIVILEGES;"
mysql -u root -pP@ssw0rd -e "CREATE DATABASE IF NOT EXISTS webdb; CREATE USER IF NOT EXISTS 'web'@'%' IDENTIFIED BY 'P@ssw0rd'; GRANT ALL PRIVILEGES ON webdb.* TO 'web'@'%'; FLUSH PRIVILEGES;"
mysql -u root -pP@ssw0rd webdb < /home/user/web/dump.sql

cp /home/user/web/index.php /home/user/web/logo.png /var/www/html/
chown -R apache:apache /var/www/html/
```

Отредактировать `nano /var/www/html/index.php` — найти и заменить параметры подключения к БД:
```php
$servername = "localhost";
$username = "web";
$password = "P@ssw0rd";
$dbname = "webdb";
```

```bash
systemctl enable --now httpd && systemctl restart httpd
```

---

## HQ-CLI

### Chrony (клиент)

`/etc/chrony.conf` — аналогично HQ-SRV (server 172.16.1.1 iburst).

### sshuser + SSH — аналогично HQ-SRV (если требуется)

### NFS-клиент

```bash
mkdir -p /mnt/nfs && chmod 777 /mnt/nfs
echo '192.168.100.2:/raid/nfs  /mnt/nfs  nfs  auto  0 0' >> /etc/fstab
mount -a
```

### Пользователи и группы (Мод2)

```bash
groupadd Work
groupadd Job
groupadd labor
useradd -G Work User1
useradd -G Work User2
useradd -G Job User3
useradd -G Job User4
useradd -G labor User5
mkdir -p /home/Folder
mkdir /home/Folder/work_shared
chown root:Work /home/Folder/work_shared
chmod 770 /home/Folder/work_shared
mkdir /home/Folder/job_readonly
chown root:Job /home/Folder/job_readonly
chmod 750 /home/Folder/job_readonly
```

---

## BR-SRV

### sshuser + SSH — аналогично HQ-SRV

### Chrony (клиент) — аналогично HQ-SRV

### Монтирование CD

```bash
mkdir -p /mnt/cdrom
mount -o ro /dev/sr0 /mnt/cdrom
cp -r /mnt/cdrom/docker/ /home/user/docker/
```

### Samba

```bash
groupadd hq
useradd -G hq hquser1
echo -e "P@ssw0rd\nP@ssw0rd" | smbpasswd -a -s hquser1
useradd -G hq hquser2
echo -e "P@ssw0rd\nP@ssw0rd" | smbpasswd -a -s hquser2
useradd -G hq hquser3
echo -e "P@ssw0rd\nP@ssw0rd" | smbpasswd -a -s hquser3
useradd -G hq hquser4
echo -e "P@ssw0rd\nP@ssw0rd" | smbpasswd -a -s hquser4
useradd -G hq hquser5
echo -e "P@ssw0rd\nP@ssw0rd" | smbpasswd -a -s hquser5
```

`/etc/samba/smb.conf`:
```ini
[global]
  workgroup = SIRIUSEXAM
  server string = BR-SRV Samba Server
  netbios name = BR-SRV
  security = user
  map to guest = Bad User
  dns proxy = no
  realm = SIRIUS-EXAM.ORG
```

`systemctl enable --now smb nmb && systemctl restart smb nmb`

### Docker — загрузка образов

```bash
systemctl enable --now docker
docker load < /home/user/docker/site_latest.tar
docker load < /home/user/docker/mariadb_latest.tar
```

### Docker — Testapp

`/root/web.yaml`:
```yaml
version: '3.8'
services:
  db:
    image: mariadb:10.11
    container_name: db
    restart: always
    environment:
      MARIADB_ROOT_PASSWORD: P@ssw0rd
      DB_NAME: testdb
      DB_USER: test
      DB_PASSW: P@ssw0rd
    volumes:
      - db_data:/var/lib/mysql
    networks:
      - testapp
  testapp:
    image: site:latest
    container_name: testapp
    restart: always
    ports:
      - "8080:8000"
    depends_on:
      - db
    environment:
      DB_HOST: db
      DB_NAME: testdb
      DB_USER: test
      DB_PASS: P@ssw0rd
      DB_TYPE: maria
    networks:
      - testapp
volumes:
  db_data:
networks:
  testapp:
    driver: bridge
```

```bash
cd /root && docker-compose -f web.yaml up -d
# Подождать ~30 сек, затем:
docker exec db mysql -u root -pP@ssw0rd -e "CREATE DATABASE IF NOT EXISTS testdb; CREATE USER IF NOT EXISTS 'test'@'%' IDENTIFIED BY 'P@ssw0rd'; GRANT ALL PRIVILEGES ON testdb.* TO 'test'@'%'; FLUSH PRIVILEGES;"
docker-compose -f web.yaml restart
```

### Docker — Nextcloud

```bash
mkdir -p /opt/nextcloud/db_data /opt/nextcloud/nextcloud_data
```

`/opt/nextcloud/docker-compose.yml`:
```yaml
version: '3.8'
services:
  db:
    image: mariadb:10.11
    container_name: nextcloud-db
    restart: always
    command: --transaction-isolation=READ-COMMITTED --log-bin=binlog --binlog-format=ROW
    volumes:
      - /opt/nextcloud/db_data:/var/lib/mysql
    environment:
      MARIADB_ROOT_PASSWORD: P@ssw0rd
      MARIADB_DATABASE: nextcloud
      MARIADB_USER: nextcloud
      MARIADB_PASSWORD: P@ssw0rd
    networks:
      - nextcloud
  nextcloud:
    image: nextcloud:latest
    container_name: nextcloud-app
    restart: always
    depends_on:
      - db
    ports:
      - "8081:80"
    volumes:
      - /opt/nextcloud/nextcloud_data:/var/www/html
    environment:
      MYSQL_HOST: db
      MYSQL_DATABASE: nextcloud
      MYSQL_USER: nextcloud
      MYSQL_PASSWORD: P@ssw0rd
      NEXTCLOUD_ADMIN_USER: admin
      NEXTCLOUD_ADMIN_PASSWORD: P@ssw0rd
      NEXTCLOUD_TRUSTED_DOMAINS: "*"
      OVERWRITEPROTOCOL: https
    networks:
      - nextcloud
networks:
  nextcloud:
    driver: bridge
```

```bash
cd /opt/nextcloud
docker-compose up -d
```

### Nginx + SSL на BR-SRV (для Nextcloud)

```bash
mkdir -p /etc/nginx/ssl /etc/nginx/sites-available /etc/nginx/sites-enabled
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/nginx/ssl/nextcloud.key -out /etc/nginx/ssl/nextcloud.crt -subj "/C=RU/ST=Moscow/L=Moscow/O=Sirius/OU=IT/CN=127.0.0.1"
```

`/etc/nginx/sites-available/nextcloud.conf`:
```nginx
server {
    listen 443 ssl http2;
    server_name 127.0.0.1;
    ssl_certificate /etc/nginx/ssl/nextcloud.crt;
    ssl_certificate_key /etc/nginx/ssl/nextcloud.key;
    client_max_body_size 512M;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_request_buffering off;
    }
}
```

```bash
ln -sf /etc/nginx/sites-available/nextcloud.conf /etc/nginx/sites-enabled/nextcloud.conf
```

В `/etc/nginx/nginx.conf` добавить в блок http: `include /etc/nginx/sites-enabled/*.conf;`

```bash
rm -f /etc/nginx/conf.d/default.conf
nginx -t && systemctl enable --now nginx && systemctl restart nginx
```
