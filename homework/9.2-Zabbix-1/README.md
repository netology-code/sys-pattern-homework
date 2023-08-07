# Домашнее задание к занятию "Система мониторинга Zabbix" - Пешева Ирина


### Задание 1
Установите Zabbix Server с веб-интерфейсом.

#### Процесс выполнения
1. Выполняя ДЗ сверяйтесь с процессом отражённым в записи лекции.
2. Установите PostgreSQL. Для установки достаточна та версия что есть в системном репозитороии Debian 11
3. Пользуясь конфигуратором комманд с официального сайта, составьте набор команд для установки последней версии Zabbix с поддержкой PostgreSQL и Apache
4. Выполните все необходимые команды для установки Zabbix Server и Zabbix Web Server

#### Требования к результаты 
1. Прикрепите в файл README.md скриншот авторизации в админке
2. Приложите в файл README.md текст использованных команд в GitHub
### Решение 1
#### Установка

```bash
apt update && apt upgrade

apt install postgresql

wget https://repo.zabbix.com/zabbix/6.0/debian/pool/main/z/zabbix-release/zabbix-release_6.0-4+debian11_all.deb
dpkg -i zabbix-release_6.0-4+debian11_all.deb
apt update

apt install zabbix-server-pgsql zabbix-frontend-php php7.4-pgsql zabbix-apache-conf zabbix-sql-scripts

sudo -u postgres createuser --pwprompt zabbix
sudo -u postgres createdb -O zabbix zabbix 

cat /usr/share/zabbix-sql-scripts/postgresql/server.sql.gz | sudo -u zabbix psql zabbix

nano /etc/zabbix/zabbix_server.conf

systemctl restart zabbix-server apache2
systemctl enable zabbix-server apache2
```
#### Проверка

Сервер сконфигурирован:

![Alt text](img/1.png)

Установка прошла успешно:

![Alt text](img/2.png)



---
### Задание 2
Установите Zabbix Agent на два хоста.

#### Процесс выполнения
1. Выполняя ДЗ сверяйтесь с процессом отражённым в записи лекции.
2. Установите Zabbix Agent на 2 виртмашины, одной из них может быть ваш Zabbix Server
3. Добавьте Zabbix Server в список разрешенных серверов ваших Zabbix Agentов
4. Добавьте Zabbix Agentов в раздел Configuration > Hosts вашего Zabbix Servera
5. Проверьте что в разделе Latest Data начали появляться данные с добавленных агентов

#### Требования к результаты 
1. Приложите в файл README.md скриншот раздела Configuration > Hosts, где видно, что агенты подключены к серверу
2. Приложите в файл README.md скриншот лога zabbix agent, где видно, что он работает с сервером
3. Приложите в файл README.md скриншот раздела Monitoring > Latest data для обоих хостов, где видны поступающие от агентов данные.
4. Приложите в файл README.md текст использованных команд в GitHub
### Решение 2

#### Установка
Один агент установлен на локальной машине, другой — на отдельной машине. Приведём комманды для отдельной машины.

```bash
wget https://repo.zabbix.com/zabbix/6.0/debian/pool/main/z/zabbix-release/zabbix-release_6.0-4+debian11_all.deb
dpkg -i zabbix-release_6.0-4+debian11_all.deb
apt update 

apt install zabbix-agent

sed -i 's/Server=127.0.0.1/Server=158.160.29.223/g' /etc/zabbix/zabbix_agentd.conf

systemctl restart zabbix-agent
systemctl enable zabbix-agent
```
Добавим два агента. Тогда:

1. Раздел hosts

![Alt text](img/3.png)

2. Лог zabbix agent (в данном случае, работоспособность можно определить по отсутствию ошибок подключения от сервера):

![Alt text](img/4.png)

![Alt text](img/5.png)

Можно также увидеть, что агент активно собирает информацию, также без особых проблем:

![Alt text](img/7.png)

3. Данные с обеих машин:

![Alt text](img/6.png)




