# Домашнее задание к занятию «Система мониторинга Zabbix» - `Фамилия Имя`

---

### Задание 1

Установка Zabbix Server 7.4 с веб-интерфейсом на Ubuntu 24.04.

> Примечание: вместо PostgreSQL и Apache использованы MySQL и Nginx. Команды составлены через конфигуратор на [zabbix.com/download](https://www.zabbix.com/download).

1. Получены права root.
2. Установлен репозиторий Zabbix 7.4.
3. Установлены Zabbix Server, веб-интерфейс и агент.
4. Создана база данных и пользователь `zabbix`, импортирована начальная схема.
5. В `/etc/zabbix/zabbix_server.conf` указан пароль к БД.
6. В `/etc/zabbix/nginx.conf` настроены `listen` и `server_name`.
7. Сервисы запущены и добавлены в автозагрузку.

```bash
# a. Права root
sudo -s

# b. Репозиторий Zabbix
wget https://repo.zabbix.com/zabbix/7.4/release/ubuntu/pool/main/z/zabbix-release/zabbix-release_latest_7.4+ubuntu24.04_all.deb
dpkg -i zabbix-release_latest_7.4+ubuntu24.04_all.deb
apt update

# c. Zabbix Server, веб-интерфейс и агент
apt install zabbix-server-mysql zabbix-frontend-php zabbix-nginx-conf zabbix-sql-scripts zabbix-agent

# d. База данных
mysql -uroot -p
```

```sql
create database zabbix character set utf8mb4 collate utf8mb4_bin;
create user zabbix@localhost identified by 'password';
grant all privileges on zabbix.* to zabbix@localhost;
set global log_bin_trust_function_creators = 1;
quit;
```

```bash
# Импорт начальной схемы и данных
zcat /usr/share/zabbix/sql-scripts/mysql/server.sql.gz | mysql --default-character-set=utf8mb4 -uzabbix -p zabbix

# Отключение log_bin_trust_function_creators после импорта
mysql -uroot -p -e "set global log_bin_trust_function_creators = 0;"

# e. Пароль к БД в /etc/zabbix/zabbix_server.conf
#    DBPassword=password

# f. Настройка /etc/zabbix/nginx.conf
#    listen 8080;
#    server_name example.com;

# g. Запуск и автозагрузка
systemctl restart zabbix-server zabbix-agent nginx php8.3-fpm
systemctl enable zabbix-server zabbix-agent nginx php8.3-fpm
```

Скриншот авторизации в админке:

![Авторизация в Zabbix](https://github.com/ProffeSOr24/solution-template/blob/main/img/zabbix-login.png)

---

### Задание 2

Zabbix Agent установлен на два хоста: `Zabbix server` (127.0.0.1) и `vm2` (158.160.229.50).

1. На `vm2` добавлен репозиторий Zabbix 7.4 и установлен `zabbix-agent`.
2. В `/etc/zabbix/zabbix_agentd.conf` в параметрах `Server` и `ServerActive` указан IP Zabbix Server.
3. Агент перезапущен и добавлен в автозагрузку.
4. В Data collection > Hosts добавлен хост `vm2` с шаблоном `Linux by Zabbix agent`.
5. В Monitoring > Latest data проверено поступление данных.

```bash
# На vm2
sudo -s
wget https://repo.zabbix.com/zabbix/7.4/release/ubuntu/pool/main/z/zabbix-release/zabbix-release_latest_7.4+ubuntu24.04_all.deb
dpkg -i zabbix-release_latest_7.4+ubuntu24.04_all.deb
apt update
apt install zabbix-agent

# Разрешаем подключение Zabbix Server
sed -i 's/^Server=127.0.0.1/Server=<IP_Zabbix_Server>/' /etc/zabbix/zabbix_agentd.conf
sed -i 's/^ServerActive=127.0.0.1/ServerActive=<IP_Zabbix_Server>/' /etc/zabbix/zabbix_agentd.conf

# Запуск и автозагрузка
systemctl restart zabbix-agent
systemctl enable zabbix-agent

# Лог агента
tail -f /var/log/zabbix/zabbix_agentd.log
```

Configuration > Hosts — оба агента подключены к серверу (статус ZBX зелёный):

![Hosts](https://github.com/ProffeSOr24/solution-template/blob/main/img/zabbix-hosts.png)

Лог Zabbix Agent:

![Agent log](https://github.com/ProffeSOr24/solution-template/blob/main/img/zabbix-agent-log.png)

Monitoring > Latest data для обоих хостов:

![Latest data](https://github.com/ProffeSOr24/solution-template/blob/main/img/zabbix-latest-data.png)

---

### Задание 3*

Установка Zabbix Agent на Windows.

1. С [zabbix.com/download_agents](https://www.zabbix.com/download_agents) скачан MSI-установщик Zabbix Agent (Windows, amd64, OpenSSL, версия 7.0).
2. При установке указаны: Host name — имя компьютера, Zabbix server IP/DNS и Server for active checks — IP Zabbix Server.
3. В брандмауэре Windows разрешён входящий TCP-порт 10050.
4. В веб-интерфейсе добавлен хост с шаблоном `Windows by Zabbix agent`.
5. В Monitoring > Latest data проверено свободное место на диске C:.

```powershell
# Тихая установка агента (PowerShell от администратора)
msiexec /l*v log.txt /i zabbix_agent-7.0-windows-amd64-openssl.msi /qn `
    SERVER=<IP_Zabbix_Server> SERVERACTIVE=<IP_Zabbix_Server> HOSTNAME=$env:COMPUTERNAME

# Разрешаем порт агента в брандмауэре
New-NetFirewallRule -DisplayName "Zabbix Agent" -Direction Inbound -Protocol TCP -LocalPort 10050 -Action Allow

# Проверка службы
Get-Service "Zabbix Agent"
```

Latest data — свободное место на диске C::

![Windows disk C](https://github.com/ProffeSOr24/solution-template/blob/main/img/zabbix-windows-disk-c.png)
