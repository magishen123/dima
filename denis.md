# МОДУЛЬ 1. СЕТЕВКА

## Настройка ISP

Задаем адреса соединений

```
nano /etc/nftables/isp.nft

table inet nat {
        chain POSTROUTING {
        type nat hook postrouting priority srcnat;
        oifname "enp0s3" masquerade
        }
}
```

```
nano /etc/sysconfig/nftables.conf

Добавляем
include "/etc/nftables/isp.nft"

systemctl enable --now nftables
```

Настройка HQ-RTR

```
hostname hq-rtr.au-team.irpo

object-group network LOCAL_NET
  ip address-range 192.168.100.2-192.168.100.30
  ip address-range 192.168.200.2-192.168.200.14
  ip address-range 192.168.99.2-192.168.99.6
exit
object-group network PUBLIC_POOL
  ip address-range 172.16.1.3-172.16.1.7
exit

syslog max-files 3
syslog file-size 512
syslog file tmpsys:syslog/default
  severity info
exit

username admin
  password encrypted $6$OvDfMY5mz2anrLK/$yTf9DE/xOmg2wAZE8lwBfYbYumkzxVQtirgaQ9L2UyjcqZOP5tbpxXjIVLbZxuLhq1J3CSAp2EHokaTJ8q8N11
exit
username net_admin
  password encrypted $6$xk7eYiojvYCDlh0b$cSuQw8aN4xZHXUTdNNwMhQNCXSwxLtThW7Db1YntSXsyfjg/atxhU/1TR4Htlru0BTr6v8JB/UpMlB.Sd0bsr/
  privilege 15
exit

domain lookup enable

router ospf 1
  router-id 1.1.1.1
  redistribute connected
  area 0.0.0.0
    network 10.10.10.0/30
    network 192.168.100.0/27
    network 192.168.200.0/28
    network 192.168.99.0/29
    network 172.16.1.0/28
    enable
  exit
  enable
exit

interface gigabitethernet 1/0/1
  ip firewall disable
  ip address 172.16.1.2/28
  ip ospf instance 1
  ip ospf authentication key ascii-text encrypted CDE65039E5591FA3
  ip ospf authentication algorithm cleartext
  ip ospf network point-to-point
  ip ospf
  ip nat proxy-arp PUBLIC_POOL
exit
interface gigabitethernet 1/0/2
  ip firewall disable
  ip address 192.168.100.1/27
  ip ospf instance 1
  ip ospf authentication key ascii-text encrypted CDE65039E5591FA3
  ip ospf authentication algorithm cleartext
  ip ospf network point-to-point
  ip ospf
exit
interface gigabitethernet 1/0/3
  ip firewall disable
  ip address 192.168.200.1/28
  ip ospf instance 1
  ip ospf authentication key ascii-text encrypted CDE65039E5591FA3
  ip ospf authentication algorithm cleartext
  ip ospf network point-to-point
  ip ospf
exit
interface gigabitethernet 1/0/4
  ip firewall disable
  ip address 192.168.99.1/29
  ip ospf instance 1
  ip ospf authentication key ascii-text encrypted CDE65039E5591FA3
  ip ospf authentication algorithm cleartext
  ip ospf network point-to-point
  ip ospf
exit

tunnel gre 1
  ttl 64
  ip firewall disable
  local address 172.16.1.2
  remote address 172.16.2.2
  ip address 10.10.10.1/30
  ip ospf instance 1
  ip ospf authentication key ascii-text encrypted CDE65039E5591FA3
  ip ospf authentication algorithm cleartext
  ip ospf network point-to-point
  ip ospf
  enable
exit

security passwords default-expired

nat source
  pool TRANSLATE_ADDRESS
    ip address-range 172.16.1.3-172.16.1.7
  exit
  ruleset SNAT
    to interface gigabitethernet 1/0/1
    rule 1
      match source-address object-group LOCAL_NET
      action source-nat pool TRANSLATE_ADDRESS
      enable
    exit
  exit
exit

ip dhcp-server
ip dhcp-server pool CLI_POOL
  network 192.168.200.0/28
  domain-name au-team.irpo
  address-range 192.168.200.3-192.168.200.14
  default-router 192.168.200.1
  dns-server 192.168.100.2
exit

ip route 0.0.0.0/0 172.16.1.1
ip route 192.168.30.0/28 172.16.1.1

ip ssh server

ntp enable
ntp broadcast-client enable

licence-manager
  host address elm.eltex-co.ru
exit


## Настройка BR-RTR

hostname br-rtr.au-team.irpo

object-group network LOCAL_NET
  ip address-range 192.168.30.2-192.168.30.14
exit
object-group network PUBLIC_POOL
  ip address-range 172.16.2.3-172.16.2.7
exit

syslog max-files 3
syslog file-size 512
syslog file tmpsys:syslog/default
  severity info
exit

username admin
  password encrypted $6$HIUk/YlQLgWaPBqU$Olu/kJqrPPTru9kCONtktjC3LgN43tu/JN3yAqccL8ScqcHIg93jHmGCtE0CCR4/Hgbvop3gzKB0RHjW1gQLh0
exit
username net_admin
  password encrypted $6$n88rHTpa1gZpR1YU$2TO2CwKrX0jBIw2QWIEqnOb4vAl2vTwusUVQcELoA72Bip6oL6Y6dJ8AXRiaPg2er0YHuNADSWtrqEoVDZAfy1
  privilege 15
exit

domain lookup enable

router ospf 1
  router-id 2.2.2.2
  redistribute connected
  area 0.0.0.0
    network 10.10.10.0/30
    network 192.168.30.0/28
    network 172.16.2.0/28
    enable
  exit
  enable
exit

interface gigabitethernet 1/0/2
  ip firewall disable
  ip address 192.168.30.1/28
  ip ospf instance 1
  ip ospf authentication key ascii-text encrypted CDE65039E5591FA3
  ip ospf authentication algorithm cleartext
  ip ospf network point-to-point
  ip ospf
exit
interface gigabitethernet 1/0/3
  ip firewall disable
  ip address 172.16.2.2/28
  ip ospf instance 1
  ip ospf authentication key ascii-text encrypted CDE65039E5591FA3
  ip ospf authentication algorithm cleartext
  ip ospf network point-to-point
  ip ospf
  ip nat proxy-arp PUBLIC_POOL
exit

tunnel gre 1
  ttl 64
  ip firewall disable
  local address 172.16.2.2
  remote address 172.16.1.2
  ip address 10.10.10.2/30
  ip ospf instance 1
  ip ospf authentication key ascii-text encrypted CDE65039E5591FA3
  ip ospf authentication algorithm cleartext
  ip ospf network point-to-point
  ip ospf
  enable
exit

security passwords default-expired

nat source
  pool TRANSLATE_ADDRESS
    ip address-range 172.16.2.3-172.16.2.7
  exit
  ruleset SNAT
    to interface gigabitethernet 1/0/3
    rule 1
      match source-address object-group LOCAL_NET
      action source-nat pool TRANSLATE_ADDRESS
      enable
    exit
  exit
exit

ip route 0.0.0.0/0 172.16.2.1
ip route 192.168.100.0/27 172.16.2.1
ip route 192.168.200.0/28 172.16.2.1
ip route 192.168.99.0/29 172.16.2.1

ip ssh server

ntp enable
ntp broadcast-client enable

licence-manager
  host address elm.eltex-co.ru
exit
```

### Назначение статического ip-адреса машинам

```
nmcli connection show
nmcli connection modify "Проводное подключение 1" ipv4.addresses 192.168.57.2/24
nmcli connection modify "Проводное соединение 1" ipv4.gateway 192.168.57.1
nmcli connection modify "Проводное соединение 1" ipv4.dns "192.168.57.2"
nmcli connection modify "Проводное соединение 1" ipv4.method manual
nmcli connection down "Проводное соединение 1"
nmcli connection up "Проводное соединение 1"
```

### Изменяем название машины

```
hostnamectl hostname first-srv
```

### Конфигурируем время

```
timedatectl set-timezone Europe/Moscow
timedatectl – проверка времени
```

### Создаем пользователя sshuser

```
useradd sshuser -u 1010
passwd sshuser - задаст новый пароль
sudo usermod -a -G wheel sshuser
```

### Отключение selinux

```
sudo nano /etc/selinux/config
Изменяем параметр на
SELINUX=disabled
sudo reboot
getenforce - проверка, что отключен
```

### Настраиваем ssh

```
nano /etc/ssh/sshd_config

ДОБАВЛЯЕМ В ФАЙЛ

	Port 2024
	MaxAuthTries 2
	AllowUsers sshuser
	PermitRootLogin no
	Banner /root/banner
```

```
nano /root/banner
	ПИШЕМ В ФАЙЛ
	Authorized access only
```
```
systemctl restart sshd
```

### Задание DNS


1. Устанавливаем bind dns-сервер:

```
sudo dnf install bind
systemctl enable named –now
systemctl status named
```



2. Изменяем параметры конфигурации dns-сервера:

```
sudo nano /etc/named.conf
```

Отредактировать или добавить следующие параметры
```
listen-on port 53 { 127.0.0.1; 192.168.0.1; };
listen-on-v6 port 53 { none; };
allow-query { any; };
forward first;
forwarders { 8.8.8.8; };
```

Объявить прямую зону
```
zone "it-sirius.any" {

	type master;

	file "master/it-sirius.any";

};
```

Полный файл. Если хотите просто копировать-вставить

```
//
// named.conf
//
// Provided by Red Hat bind package to configure the ISC BIND named(8) DNS
// server as a caching only nameserver (as a localhost DNS resolver only).
//
// See /usr/share/doc/bind*/sample/ for example named configuration files.
//

options {
	listen-on port 53 { any; };
	listen-on-v6 port 53 { none; };
	directory 	"/var/named";
	dump-file 	"/var/named/data/cache_dump.db";
	statistics-file "/var/named/data/named_stats.txt";
	memstatistics-file "/var/named/data/named_mem_stats.txt";
	secroots-file	"/var/named/data/named.secroots";
	recursing-file	"/var/named/data/named.recursing";
	allow-query     { any; };

	/*
	 - If you are building an AUTHORITATIVE DNS server, do NOT enable recursion.
	 - If you are building a RECURSIVE (caching) DNS server, you need to enable
	   recursion.
	 - If your recursive DNS server has a public IP address, you MUST enable access
	   control to limit queries to your legitimate users. Failing to do so will
	   cause your server to become part of large scale DNS amplification
	   attacks. Implementing BCP38 within your network would greatly
	   reduce such attack surface
	*/
	recursion yes;

	dnssec-validation yes;
	forward first;

	forwarders { 8.8.8.8; };

	managed-keys-directory "/var/named/dynamic";
	geoip-directory "/usr/share/GeoIP";

	pid-file "/run/named/named.pid";
	session-keyfile "/run/named/session.key";

	/* https://fedoraproject.org/wiki/Changes/CryptoPolicy */
	include "/etc/crypto-policies/back-ends/bind.config";
};

logging {
        channel default_debug {
                file "data/named.run";
                severity dynamic;
        };
};

zone "." IN {
	type hint;
	file "named.ca";
};

zone "it-sirius.any" {

	type master;

	file "master/it-sirius.any";

};

include "/etc/named.rfc1912.zones";
include "/etc/named.root.key";
```


3. Создаем директорию с мастер-зонами

```
sudo mkdir /var/named/master
```


4. Копируем файл-шаблон зоны

```
sudo cp /var/named/named.localhost /var/named/master/it-sirius.any
```

5. Открываем файл на редактирование

```
sudo nano /var/named/master/it-sirius.any
```

Редактируем и приводим значения зоны к примеру ниже. Либо просто копировать-вставить. НО СЛЕДИТЕ ЗА АДРЕСАЦИЕЙ, У ВАС МОЖЕТ БЫТЬ НЕ 192.168.57.0, А ДРУГАЯ СЕТЬ


```
$TTL 604800       ;

it-sirius.any.    IN      SOA     ns01.it-sirius.any. root.it-sirius.any. (

                1 ; Serial

                600 ; Refresh

                3600 ; Retry

                1w ; Expire

                360 ; Minimum TTL

                )

        IN      NS ns01.it-sirius.any.

ns01    IN      A 192.168.57.2
it-sirius.any.  IN      A       192.168.57.2
first-srv    IN      A 192.168.57.2

```

6. Задаем права и владельца файлов

```
sudo chown -R root:named /var/named/master
sudo chmod 0640 /var/named/master/*
```


7. Перезапустите службу

```
systemctl restart named
```

8. Выполним проверку работы DNS

```
nslookup it-sirius.any
```

Должны получить выывод

```
Server:		127.0.0.53
Address:	127.0.0.53#53

Non-authoritative answer:
Name:	first-srv.it-sirius.any
Address: 192.168.57.2

```




# МОДУЛЬ 2. АДМИНИСТРИРОВАНИЕ

### Задание 1

Самбу поднимаем в последний момент. По баллам весит мало, заморочек много

### Задание 2 Выполняем на HQ-SRV

Создание RAID-массива

Выполните команду - lsblk

В случае отсутствия ЗАРАНЕЕ подготовленных разделов для создания RAID, создаем файл-диски. Если разделы по 1 гб у вас есть, то переходим сразу к созданию RAID-массива.

1. Создай файлы-диски
```
sudo dd if=/dev/zero of=/root/disk1.img bs=1M count=1024
sudo dd if=/dev/zero of=/root/disk2.img bs=1M count=1024
```
2. Подключи как устройства
```
sudo losetup -f /root/disk1.img
sudo losetup -f /root/disk2.img
```

3. Выполни lsblk, чтобы убедится в создании разделов

В выводе должен увидеть два loop0 и loop1 - это и есть наши диски.

```
NAME   MAJ:MIN RM  SIZE RO TYPE  MOUNTPOINTS
loop0    7:0    0    1G  0 loop
loop1    7:1    0    1G  0 loop
```

4. Создай RAID 0

```
sudo mdadm --create /dev/md0 --level=0 --raid-devices=2 /dev/loop0 /dev/loop1
```

5. Форматируй и монтируй

```
sudo mkfs.ext4 /dev/md0
sudo mkdir -p /raid
sudo mount /dev/md0 /raid
```

6. Добавь в автомонтирование

```
echo '/dev/md0  /raid  ext4  defaults  0  2' | sudo tee -a /etc/fstab
```

### Задание 3 Выполняем на HQ-SRV

Делаем на сервере:

```
dnf install nfs4-acl-tools nfs-utils -y

mkdir /raid/nfs

chmod -R 777 /raid/nfs

nano /etc/exports
/raid/nfs       192.168.2.0/28(rw,no_root_squash)

systemctl enable --now nfs-server.service

exportfs -arv
```

В выводе должно быть

```
exporting 192.168.57.0/24:/raid/nfs
```

Делаем на клиенте:

```
dnf install nfs-utils
mkdir /mnt/nfs
chmod –R 777 /mnt/nfs

nano /etc/fstab
192.168.1.2:/raid/nfs        /mnt/nfs    nfs     auto    0 0

mount -av
df -h

touch /raid/nfs/test.txt
```

Делаем на сервере:
```
ls /raid/nfs
```



### Задание 4 Выполняем на ISP в качестве сервера и HQ-SRV, HQ-CLI, BR-RTR, BR-SRV в качестве клиентов

Делаем на ISP:

```
nano /etc/chrony.conf

server ntp1.vniiftri.ru iburst prefer
#server ntp2.vniiftri.ru iburst
#server ntp3.vniiftri.ru iburst
#server ntp4.vniiftri.ru iburst

local stratum 5
allow 0.0.0.0/0

```

```
systemctl restart chronyd

chronyc sources
```

Делаем на HQ-SRV, HQ-CLI, BR-RTR, BR-SRV:

```
nano /etc/chrony.conf

server 192.168.57.2 iburst

systemctl restart chronyd
```

```
chronyc sources

MS Name/IP address         Stratum Poll Reach LastRx Last sample
===============================================================================
^* 192.168.57.2                  2   6   377    38    +40us[ -981us] +/-   39ms

```

Делаем на ISP:

```
chronyc clients

Hostname                      NTP   Drop Int IntL Last     Cmd   Drop Int  Last
===============================================================================
192.168.57.3                  331      0   6   -     6       0      0   -     -

```


### Задание 5
Ansible. У вас его не будет. Скипаем


### Задание 6 Выполняем на HQ-SRV

На клиенте:
https://disk.yandex.ru/d/0MGlkrp2B9nXDw - скачиваем iso откуда берем образы докер

разархивируем на клиенте в директорию /home

копируем директории docker и web на сервер через scp

На сервере:
```
dnf install docker-ce docker-ce-cli docker-compose -y
systemctl enable docker --now
systemctl status docker
docker load < ./docker/site_latest.tar
docker load < ./docker/mariadb_latest.tar
docker images ls
docker images

nano web.yaml
```

Содержимое docker-compose
```
services:
  testapp:
    container_name: testapp
    image: site:latest
    restart: always
    ports:
      - "8080:8000"
    environment:
      DB_HOST: "192.168.57.2"
      DB_PORT: "3306"
      DB_NAME: testdb
      DB_USER: test
      DB_PASS: P@ssw0rd
      DB_TYPE: maria
    depends_on:
      - db

  db:
    container_name: db
    image: mariadb:10.11
    restart: always
    ports:
      - "3306:3306"
    environment:
      DB_USER: test
      DB_PASS: P@ssw0rd
      DB_NAME: testdb
      MARIADB_ROOT_PASSWORD: P@ssw0rd
```

```
docker-compose -f web.yaml up -d
```

```
docker exec -it db mysql -u root -p

    CREATE DATABASE testdb;
    CREATE USER 'test'@'%' IDENTIFIED BY 'P@ssw0rd';
    GRANT ALL PRIVILEGES ON testdb.* TO 'test'@'%';
    FLUSH PRIVILEGES;
    \q
```

```
docker-compose -f web.yaml stop -d
docker-compose -f web.yaml up -d
```

### Задание 7 Выполняем на BR-SRV

```
dnf install httpd

dnf install php php-mysqlnd

dnf install mariadb-server mariadb

systemctl enable mariadb --now
```

```
mysql_secure_installation
Устанавливаем пароль root для mariadb . Во всех пунктах вводим Y (Yes)
```

```
mysql -u root -p

CREATE DATABASE webdb;

После подключения к БД создаем пользователя

CREATE USER ‘web’@’%’ IDENTIFIED BY 'P@ssw0rd';

GRANT ALL PRIVILEGES ON webdb.* TO 'web'@'%';

FLUSH PRIVILEGES;
```

```
systemctl restart mariadb

mysql webdb < /home/user/web/dump.sql

cp /home/user/web/index.php /var/www/html/

cp /home/user/web/logo.png /var/www/html/
```

```
nano /var/www/html/index.php

<?php
$servername = "localhost";
$username = "web";
$password = "P@ssw0rd";
$dbname = "webdb";
```

```
systemctl restart httpd
```

Открываем браузер на клиенте и вводим ip-адрес-машины в строку поиска


### Задание 9 Выполняем на ISP

Настройка nginx

```
dnf install nginx -y
systemctl enable --now nginx
```

```
cat /etc/nginx/nginx.conf
проверить в конфиге наличие в блоке http строчки include /etc/nginx/conf.d/*.conf 
Данная ссылка будет ссылаться на все конфиги в папке conf.d с конфигами
```

```
cd /etc/nginx/conf.d
```

```
nano docker.conf


server {
    listen 80;
    server_name docker.it-sirius.any;

    location / {
        proxy_pass http://192.168.57.2:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```
nano web.conf


server {
    listen 80;
    server_name web.it-sirius.any;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```
sudo nginx -t
должен быть статус successful
```

```
systemctl restart nginx
```


Добавляем в конфигурацию DNS-сервера

```
nano /var/named/master/it-sirius.any

В конец файла добавляем запись о ISP

first-srv    IN      A 192.168.57.2

А также ниже добавляем CNAME записи

docker          IN      CNAME   isp.it-sirius.any.
web             IN      CNAME   isp.it-sirius.any.
```

```
systemctl restart named
```

### Задание 10 Выполняем на ISP

Web-based аутентификация

```
dnf install httpd-tools
htpasswd -h
htpasswd -c /etc/nginx/.htpasswd WEB
```

```
nano web.conf

Добавляем 

        auth_basic "Restricted area";
        auth_basic_user_file /etc/nginx/.htpasswd;

Полная конфига файла web.conf

server {
    listen 80;
    server_name web.it-sirius.any;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP $remote_addr;
        auth_basic "Restricted area";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
```

```
sudo nginx -t
должен быть статус successful
```

```
systemctl restart nginx
```



# МОДУЛЬ 3 Выполняем на BR-SRV

Требуется поднять и настроить Nextcloud

```
dnf install docker-ce docker-ce-cli docker-compose -y
systemctl enable docker --now
systemctl status docker
```

```
nano nextcloud.yaml

version: '2'

volumes:
  twnextcloud:
  db:

services:
  db:
    image: mysql
    restart: unless-stopped
    volumes:
      - /opt:/opt
      - db:/var/lib/mysql
    environment:
      - MYSQL_ROOT_PASSWORD=P@ssw0rd
      - MYSQL_PASSWORD=P@ssw0rd
      - MYSQL_DATABASE=nextcloud
      - MYSQL_USER=nextcloud

  app:
    image: nextcloud
    restart: unless-stopped
    ports:
      - "8081:80"
    links:
      - db
    volumes:
      - /opt:/opt
      - twnextcloud:/var/www/html
    environment:
      - MYSQL_PASSWORD=P@ssw0rd
      - MYSQL_DATABASE=nextcloud
      - MYSQL_USER=nextcloud
      - MYSQL_HOST=db
```

```
docker-compose -f nextcloud.yaml up -d
```

Открыть интерфейс nextcloud через бразуер. В строке поиска введите ip-адрес_сервера:8081

Если веб-страница некстклауд открылась. Переходим к настройке DNS и Nginx

Добавляем в конфигурацию DNS-сервера

```
nano /var/named/master/it-sirius.any

В конец файла добавляем запись о ISP

first-srv    IN      A 192.168.57.2

А также ниже добавляем CNAME записи

nextcloud       IN      CNAME   isp.it-sirius.any.
```

```
systemctl restart named
```

Создание сертификатов на ISP для nextcloud

```
sudo mkdir -p /etc/nginx/ssl
sudo cd /etc/nginx/ssl

openssl genrsa -out nextcloud.key 2048
openssl req -x509 -key nextcloud.key -days 365 -out nextcloud.crt
```

```
nano nextcloud.conf

server {
    listen 443 ssl;
    server_name mediawiki.it-sirius.any;
    ssl_certificate /etc/nginx/ssl/nextcloud.crt;
    ssl_certificate_key /etc/nginx/ssl/nextcloud.key;
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header SSL_PROTOCOL $ssl_protocol;
    }
}
```

```
sudo nginx -t
должен быть статус successful
```

```
systemctl restart nginx
```

Далее требуется произвести настройку Nextcloud согласно заданию ДЕМО

Создать пользователей User1, User2 в группе Work, User3, User4 в
группе Job, User5 в группе labor.

Создать каталог Folder. Внутри него создать подкаталог work_shared с правами для чтения и записи группы Work.
Создать подкаталог job_readonly с правами чтения группы Job.


