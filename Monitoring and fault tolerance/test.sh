#!/bin/bash

USER_NAME=root

NAME=$(id -nu)
if [ "$NAME" != "$USER_NAME" ]; then
 echo "(root!!!)"
 exit 1
fi

apt update && apt upgrade -y
apt install postgresql -y
wget https://repo.zabbix.com/zabbix/6.0/debian/pool/main/z/zabbix-release/zabbix-release_6.0-4%2Bdebian11_all.deb
dpkg -i zabbix-release_6.0-4+debian11_all.deb
apt update
apt install zabbix-server-pgsql zabbix-frontend-php php7.4-pgsql zabbix-nginx-conf zabbix-sql-scripts zabbix-agent -y
su - postgres -c 'psql --command "CREATE USER zabbix WITH PASSWORD '\'88888\'';"'
su - postgres -c 'psql --command "CREATE DATABASE zabbix OWNER zabbix;"'
zcat /usr/share/zabbix-sql-scripts/postgresql/server.sql.gz | sudo -u zabbix psql zabbix
sed -i 's/# DBPassword=/DBPassword=88888/g' /etc/zabbix/zabbix_server.conf
sed -i 's/#        listen          8080;/         listen          8080;/g' /etc/zabbix/nginx.conf
systemctl restart zabbix-server zabbix-agent nginx php7.4-fpm
systemctl enable zabbix-server zabbix-agent nginx php7.4-fpm
