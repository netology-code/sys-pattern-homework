# Домашнее задание к занятию 9.2 «Zabbix. Часть 1» Умаров Азиз


### Задание 1
Установите Zabbix Server с веб-интерфейсом.

Приложите скриншот авторизации в админке. Приложите текст использованных команд в GitHub.
![alt text](https://github.com/UmarovAM/sys-homework/blob/c0c68ec38067632a4df660fca1936c427c47d75a/ADMIN.PNG)
![alt text](https://github.com/UmarovAM/sys-homework/blob/f512456cd0b4669222ba5de8d973010087bc57e4/ADMIN2.PNG)
![image](https://user-images.githubusercontent.com/118117183/215325605-b7b7619f-1e39-433c-9611-985e4d83b2e3.png)
17  wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
   18  sudo apt-get update
   19  sudo apt-get -y install postgresql
   20  sudo apt list --installed | grep postgresql
   21  wget https://repo.zabbix.com/zabbix/6.0/debian/pool/main/z/zabbix-release/zabbix-release_6.0-4%2Bdebian10_all.deb
   22  dpkg -i zabbix-release_6.0-4+debian10_all.deb
   23  apt update
   24  apt install zabbix-server-pgsql zabbix-frontend-php php7.3-pgsql zabbix-apache-conf zabbix-sql-scripts zabbix-agent
  
   11  sudo -u postgres createuser --pwprompt zabbix
   12  sudo -u postgres createdb -O zabbix zabbix
   13  zcat /usr/share/zabbix-sql-scripts/postgresql/server.sql.gz | sudo -u zabbix psql zabbix
   14  sudo nano /etc/zabbix/zabbix_server.conf
   15  systemctl restart zabbix-server zabbix-agent apache2
   16  sudo systemctl restart zabbix-server zabbix-agent apache2
   17  sudo systemctl enable zabbix-server zabbix-agent apache2
   18  sudo /etc/locale.gen
   19  sudo nano /etc/locale.gen
   20  sudo systemctl restart zabbix-server zabbix-agent apache2
   21  sudo nano /etc/locale.gen
   22  locale-gen
   23  sudo locale-gen
   24  sudo systemctl restart zabbix-server zabbix-agent apache2





### Задание 2
Установите Zabbix Agent на два хоста.

Приложите скриншот раздела Configuration > Hosts, где видно, что агенты подключены к серверу. Приложите скриншот лога zabbix agent, где видно, что он работает с сервером. Приложите скриншот раздела Monitoring > Latest data для обоих хостов, где видны поступающие от агентов данные. Приложите текст использованных команд в GitHub.

