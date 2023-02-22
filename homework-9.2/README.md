# Домашнее задание к занятию 9.2"`Обзор систем IT-мониторинга`" - `Konstantin Frolov`




### Задание 1

  https://ibb.co/55jdmYK

# sudo apt install postgresql

# wget https://repo.zabbix.com/zabbix/6.0/debian/pool/main/z/zabbix-release/zabbix-release_6.0-4%2Bdebian11_all.deb
# dpkg -i zabbix-release_6.0-4+debian11_all.deb
# apt update

# apt install zabbix-server-pgsql zabbix-frontend-php php7.4-pgsql zabbix-apache-conf zabbix-sql-scripts zabbix-agent

# sudo -u postgres createuser --pwprompt zabbix
# sudo -u postgres createdb -O zabbix zabbix

# zcat /usr/share/zabbix-sql-scripts/postgresql/server.sql.gz | sudo -u zabbix psql zabbix

# sudo nano /etc/zabbix/zabbix_server.conf
    DBPassword=password

# systemctl restart zabbix-server zabbix-agent apache2
# systemctl enable zabbix-server zabbix-agent apache2    

---


### Задание 2


# apt install -y zabbix-agent
# nano /etc/zabbix/zabbix_agentd.conf
    Server=192.168.1.6

https://ibb.co/k689k9b

https://ibb.co/3RLTnRL












---

