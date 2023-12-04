# Домашнее задание к занятию «Система мониторинга Zabbix» - Свирин Марк

---

### Задание 1 

Установите Zabbix Server с веб-интерфейсом.

#### Процесс выполнения
1. Выполняя ДЗ, сверяйтесь с процессом отражённым в записи лекции.
2. Установите PostgreSQL. Для установки достаточна та версия, что есть в системном репозитороии Debian 11.
3. Пользуясь конфигуратором команд с официального сайта, составьте набор команд для установки последней версии Zabbix с поддержкой PostgreSQL и Apache.
4. Выполните все необходимые команды для установки Zabbix Server и Zabbix Web Server.

#### Требования к результатам 
1. Прикрепите в файл README.md скриншот авторизации в админке.
2. Приложите в файл README.md текст использованных команд в GitHub.

#### Ответ
1. Скриншот авторизации в админке:
![image](https://github.com/svmarkst/netology-hw/assets/110044256/c6485256-be3d-4248-a106-a07a6fa27385)

2. Использованные команды:
установка PostgreSQL `apt install postgresql`
добавление репозитория zabbix и обновление кэша репозиториев `wget https://repo.zabbix.com/zabbix/6.0/ubuntu/pool/main/z/zabbix-release/zabbix-release_6.0-4+ubuntu22.04_all.deb`
                                                             `dpkg -i zabbix-release_6.0-4+ubuntu22.04_all.deb`
                                                             `apt update`
установка zabbix `apt install zabbix-server-pgsql zabbix-frontend-php php8.1-pgsql zabbix-apache-conf zabbix-sql-scripts`
создание БД `sudo -u postgres createuser --pwprompt zabbix`
            `sudo -u postgres createdb -O zabbix zabbix`
импорт схемы и данных на сервер: `zcat /usr/share/zabbix-sql-scripts/postgresql/server.sql.gz | sudo -u zabbix psql zabbix`
рестарт сервера и добавление в запуск при старте ОС: `systemctl restart zabbix-server apache2`
                                                     `systemctl enable zabbix-server apache2`
---

### Задание 2 

Установите Zabbix Agent на два хоста.

#### Процесс выполнения
1. Выполняя ДЗ, сверяйтесь с процессом отражённым в записи лекции.
2. Установите Zabbix Agent на 2 вирт.машины, одной из них может быть ваш Zabbix Server.
3. Добавьте Zabbix Server в список разрешенных серверов ваших Zabbix Agentов.
4. Добавьте Zabbix Agentов в раздел Configuration > Hosts вашего Zabbix Servera.
5. Проверьте, что в разделе Latest Data начали появляться данные с добавленных агентов.

#### Требования к результаты 
1. Приложите в файл README.md скриншот раздела Configuration > Hosts, где видно, что агенты подключены к серверу
2. Приложите в файл README.md скриншот лога zabbix agent, где видно, что он работает с сервером
3. Приложите в файл README.md скриншот раздела Monitoring > Latest data для обоих хостов, где видны поступающие от агентов данные.
4. Приложите в файл README.md текст использованных команд в GitHub

#### Ответ
![image](https://github.com/svmarkst/netology-hw/assets/110044256/f647db53-5433-4e62-82c0-90a14d04804a)
![image](https://github.com/svmarkst/netology-hw/assets/110044256/62e12043-a6b8-4a68-a08e-c210783e55e5)
![image](https://github.com/svmarkst/netology-hw/assets/110044256/33e54414-b32d-45f8-bfda-5995faad17ba)
![image](https://github.com/svmarkst/netology-hw/assets/110044256/d197d144-29c4-4372-a1fa-a5ba595b50a3)

Команды:
на Zabbix Server: `apt install zabbix-agent` 
на vm2, куда ставил агент: 
`wget https://repo.zabbix.com/zabbix/6.0/ubuntu/pool/main/z/zabbix-release/zabbix-release_6.0-4+ubuntu22.04_all.deb`
`dpkg -i zabbix-release_6.0-4+ubuntu22.04_all.deb`
`apt update`
`apt install zabbix-agent` 
в `/etc/zabbix/zabbix-agentd.conf` в параметре Server указал `192.168.123.10/24`
![image](https://github.com/svmarkst/netology-hw/assets/110044256/aee3165e-bb11-4c47-ad50-7ddb04a4bbe1)

рестарт агента и добавление в запуск при старте ОС:
`systemctl restart zabbix-agent`
`systemctl enable zabbix-agent`

---
## Задание 3 со звёздочкой*
Установите Zabbix Agent на Windows (компьютер) и подключите его к серверу Zabbix.

#### Требования к результаты 
1. Приложите в файл README.md скриншот раздела Latest Data, где видно свободное место на диске C:
--- 

## Критерии оценки

1. Выполнено минимум 2 обязательных задания
2. Прикреплены требуемые скриншоты и тексты 
3. Задание оформлено в шаблоне с решением и опубликовано на GitHub
