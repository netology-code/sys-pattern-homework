# Домашнее задание к занятию "`Обзор систем IT-мониторинга - часть 2`" - `Соборкин Андрей`

**Задание 1**

![alt](https://github.com/BOSe1337/8-03-hw/blob/main/Pictures/3.jpg)

**Использованные команды для версии 4.0 LTS**
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
