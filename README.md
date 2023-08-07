# Домашнее задание к занятию "`Обзор систем IT-мониторинга - часть 2`" - `Соборкин Андрей`

**Задание 1**

![alt](https://github.com/BOSe1337/8-03-hw/blob/main/Pictures/3.jpg)

**Использованные команды для версии 4.0 LTS**
# apt install postgresql postgresql-contrib -y
# wget https://repo.zabbix.com/zabbix/4.0/ubuntu/pool/main/z/zabbix-release/zabbix-release_4.0-3+focal_all.deb
# dpkg -i zabbix-release_4.0-3+focal_all.deb
# apt update
# apt install zabbix-server-pgsql zabbix-frontend-php php7.4-pgsql zabbix-agent
# sudo -u postgres createuser --pwprompt zabbix
# sudo -u postgres createdb -O zabbix zabbix
# zcat /usr/share/doc/zabbix-server-pgsql*/create.sql.gz | sudo -u zabbix psql zabbix
# php_value date.timezone Europe/Riga
# nano /etc/zabbix/zabbix-server.conf
# nano /etc/zabbix/zabbix-agentd.conf
# systemctl restart zabbix-server zabbix-agent apache2
# systemctl enable zabbix-server zabbix-agent apache2

**Задание 2**

![alt](https://github.com/BOSe1337/8-03-hw/blob/main/Pictures/4.jpg)

![alt](https://github.com/BOSe1337/8-03-hw/blob/main/Pictures/5.jpg)

![alt](https://github.com/BOSe1337/8-03-hw/blob/main/Pictures/6.jpg)

![alt](https://github.com/BOSe1337/8-03-hw/blob/main/Pictures/7.jpg)

![alt](https://github.com/BOSe1337/8-03-hw/blob/main/Pictures/8.jpg)

![alt](https://github.com/BOSe1337/8-03-hw/blob/main/Pictures/9.jpg)

![alt](https://github.com/BOSe1337/8-03-hw/blob/main/Pictures/10.jpg)

**Список использованных команд**
# nano /etc/zabbix/zabbix-agentd.conf - здесь меняем поле на Server=127.0.0.1, 192.168.0.26
# nano /etc/zabbix/zabbix-server.conf - здесь раскоментируем поле и пропишем пароль DBPassword=1234
# Latest data для обоих хостов, где видны поступающие от агентов данные

root@zabbix:/etc/zabbix# tail -f /var/log/zabbix/zabbix_agentd.log
 
 40775:20230807:152753.428 IPv6 support:          YES
 
 40775:20230807:152753.428 TLS support:           YES
 
 40775:20230807:152753.428 **************************
 
 40775:20230807:152753.428 using configuration file: /etc/zabbix/zabbix_agentd.conf
 
 40775:20230807:152753.429 agent #0 started [main process]

 40776:20230807:152753.431 agent #1 started [collector]
 
 40777:20230807:152753.434 agent #2 started [listener #1]
 
 40779:20230807:152753.436 agent #4 started [listener #3]
 
 40778:20230807:152753.440 agent #3 started [listener #2]
 
 40780:20230807:152753.445 agent #5 started [active checks #1]

 
 
 root@ansible:/home/ansible# tail -f /var/log/zabbix/zabbix_agentd.log
  
  2184:20230807:153602.422 TLS support:           YES
 
  2184:20230807:153602.422 **************************
  
  2184:20230807:153602.422 using configuration file: /etc/zabbix/zabbix_agentd.conf
  
  2184:20230807:153602.423 agent #0 started [main process]
  
  2185:20230807:153602.424 agent #1 started [collector]
  
  2186:20230807:153602.427 agent #2 started [listener #1]
  
  2187:20230807:153602.427 agent #3 started [listener #2]
  
  2188:20230807:153602.427 agent #4 started [listener #3]
  
  2189:20230807:153602.430 agent #5 started [active checks #1]
