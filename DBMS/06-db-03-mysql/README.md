# Домашнее задание к занятию 3. «MySQL»

## Введение

Перед выполнением задания вы можете ознакомиться с 
[дополнительными материалами](https://github.com/netology-code/virt-homeworks/blob/virt-11/additional/README.md).

## Задача 1

Используя Docker, поднимите инстанс MySQL (версию 8). Данные БД сохраните в volume.

Изучите [бэкап БД](https://github.com/netology-code/virt-homeworks/tree/virt-11/06-db-03-mysql/test_data) и 
восстановитесь из него.

### docker-compose.yml
```
version: "3.9"
services:
  mysql_db:
    container_name: mysql
    image: mysql:8
    restart: always
    environment:
      MYSQL_DATABASE: test_db
      MYSQL_ROOT_PASSWORD: 12345678
    volumes:
      - ./data:/var/lib/mysql/
      - ./my.cnf:/etc/mysql/conf.d/my.cnf
      - ./docker-entrypoint-initdb.d:/docker-entrypoint-initdb.d

    ports:
      - "3306:3306"
```
### 02-init.sh
```
    #!/bin/bash
    #dump.sh
    mysql -uroot -p12345678 test_db < /docker-entrypoint-initdb.d/test_dump.sql
    #end of dump.sh
```
Перейдите в управляющую консоль `mysql` внутри контейнера.

Используя команду `\h`, получите список управляющих команд.

Найдите команду для выдачи статуса БД и **приведите в ответе** из её вывода версию сервера БД.
```
mysql> \s
--------------
mysql  Ver 8.0.33 for Linux on x86_64 (MySQL Community Server - GPL)

Connection id:          8
Current database:
Current user:           root@localhost
SSL:                    Not in use
Current pager:          stdout
Using outfile:          ''
Using delimiter:        ;
Server version:         8.0.33 MySQL Community Server - GPL
Protocol version:       10
Connection:             Localhost via UNIX socket
Server characterset:    utf8mb4
Db     characterset:    utf8mb4
Client characterset:    latin1
Conn.  characterset:    latin1
UNIX socket:            /var/run/mysqld/mysqld.sock
Binary data as:         Hexadecimal
Uptime:                 48 sec

Threads: 2  Questions: 5  Slow queries: 0  Opens: 119  Flush tables: 3  Open tables: 38  Queries per second avg: 0.104
--------------
```

Подключитесь к восстановленной БД и получите список таблиц из этой БД.

**Приведите в ответе** количество записей с `price` > 300.

```
mysql> select count(*) from orders where price>300;
+----------+
| count(*) |
+----------+
|        1 |
+----------+
1 row in set (0.00 sec)
```

В следующих заданиях мы будем продолжать работу с этим контейнером.

## Задача 2

Создайте пользователя test в БД c паролем test-pass, используя:

- плагин авторизации mysql_native_password
- срок истечения пароля — 180 дней 
- количество попыток авторизации — 3 
- максимальное количество запросов в час — 100
- аттрибуты пользователя:
    - Фамилия "Pretty"
    - Имя "James".

Предоставьте привелегии пользователю `test` на операции SELECT базы `test_db`.
### 01-init-db.sql
```
-- CREATE user test-simple-user
CREATE USER 'test' IDENTIFIED WITH mysql_native_password BY 'testpass'
     WITH MAX_QUERIES_PER_HOUR 100 PASSWORD EXPIRE INTERVAL 180 DAY FAILED_LOGIN_ATTEMPTS 3
     ATTRIBUTE '{"surname": "Pretty", "name": "James"}';

-- ADD PRIVILIGE user test-simple-user to test_db
GRANT SELECT on test_db.* TO test;
```
    
Используя таблицу INFORMATION_SCHEMA.USER_ATTRIBUTES, получите данные по пользователю `test` и 
**приведите в ответе к задаче**.
```
mysql> select * from INFORMATION_SCHEMA.USER_ATTRIBUTES;
+------------------+-----------+----------------------------------------+
| USER             | HOST      | ATTRIBUTE                              |
+------------------+-----------+----------------------------------------+
| root             | %         | NULL                                   |
| test             | %         | {"name": "James", "surname": "Pretty"} |
| mysql.infoschema | localhost | NULL                                   |
| mysql.session    | localhost | NULL                                   |
| mysql.sys        | localhost | NULL                                   |
| root             | localhost | NULL                                   |
+------------------+-----------+----------------------------------------+
6 rows in set (0.01 sec)
```

## Задача 3

Установите профилирование `SET profiling = 1`.
Изучите вывод профилирования команд `SHOW PROFILES;`.
```
mysql> SET profiling = 1
    -> ;
Query OK, 0 rows affected, 1 warning (0.00 sec)

mysql> SHOW PROFILES;
Empty set, 1 warning (0.00 sec)
```
Увидел предупреждение и решил посмотреть о чем оно:
```
mysql> show warnings
    -> ;
+---------+------+--------------------------------------------------------------------------------------------------------------+
| Level   | Code | Message                                                                                                      |
+---------+------+--------------------------------------------------------------------------------------------------------------+
| Warning | 1287 | 'SHOW PROFILES' is deprecated and will be removed in a future release. Please use Performance Schema instead |
+---------+------+--------------------------------------------------------------------------------------------------------------+
1 row in set (0.00 sec)
```
Думал в процессе автоматичской иннициализации БД или добавления my.cnf что то сломалось, но все оказалось хорошо.

Исследуйте, какой `engine` используется в таблице БД `test_db` и **приведите в ответе**.
```
mysql> show table status\G
*************************** 1. row ***************************
           Name: orders
         Engine: InnoDB
```
Измените `engine` и **приведите время выполнения и запрос на изменения из профайлера в ответе**:
- на `MyISAM`,
```
mysql> alter table orders engine=MyISAM;
Query OK, 5 rows affected (0.05 sec)
Records: 5  Duplicates: 0  Warnings: 0
```
- на `InnoDB`.
```
mysql> alter table orders engine=InnoDB;
Query OK, 5 rows affected (0.05 sec)
Records: 5  Duplicates: 0  Warnings: 0
```
```
mysql> show profiles;
+----------+------------+----------------------------------+
| Query_ID | Duration   | Query                            |
+----------+------------+----------------------------------+
|        1 | 0.00022600 | show warnings                    |
|        2 | 0.05278850 | alter table orders engine=MyISAM |
|        3 | 0.05195700 | alter table orders engine=InnoDB |
+----------+------------+----------------------------------+
3 rows in set, 1 warning (0.00 sec)

mysql> show profile for query 2;
+--------------------------------+----------+
| Status                         | Duration |
+--------------------------------+----------+
| starting                       | 0.000107 |
| Executing hook on transaction  | 0.000015 |
| starting                       | 0.000035 |
| checking permissions           | 0.000015 |
| checking permissions           | 0.000013 |
| init                           | 0.000023 |
| Opening tables                 | 0.000543 |
| setup                          | 0.000256 |
| creating table                 | 0.001562 |
| waiting for handler commit     | 0.000024 |
| waiting for handler commit     | 0.003998 |
| After create                   | 0.002089 |
| System lock                    | 0.000027 |
| copy to tmp table              | 0.000290 |
| waiting for handler commit     | 0.000022 |
| waiting for handler commit     | 0.000029 |
| waiting for handler commit     | 0.000085 |
| rename result table            | 0.000143 |
| waiting for handler commit     | 0.017233 |
| waiting for handler commit     | 0.000031 |
| waiting for handler commit     | 0.010947 |
| waiting for handler commit     | 0.000016 |
| waiting for handler commit     | 0.007375 |
| waiting for handler commit     | 0.000023 |
| waiting for handler commit     | 0.002233 |
| end                            | 0.003505 |
| query end                      | 0.002069 |
| closing tables                 | 0.000017 |
| waiting for handler commit     | 0.000025 |
| freeing items                  | 0.000025 |
| cleaning up                    | 0.000017 |
+--------------------------------+----------+
31 rows in set, 1 warning (0.00 sec)

mysql> show profile for query 3;
+--------------------------------+----------+
| Status                         | Duration |
+--------------------------------+----------+
| starting                       | 0.000118 |
| Executing hook on transaction  | 0.000017 |
| starting                       | 0.000036 |
| checking permissions           | 0.000015 |
| checking permissions           | 0.000013 |
| init                           | 0.000024 |
| Opening tables                 | 0.000349 |
| setup                          | 0.000100 |
| creating table                 | 0.000173 |
| After create                   | 0.020196 |
| System lock                    | 0.000012 |
| copy to tmp table              | 0.000065 |
| rename result table            | 0.000492 |
| waiting for handler commit     | 0.000008 |
| waiting for handler commit     | 0.009830 |
| waiting for handler commit     | 0.000013 |
| waiting for handler commit     | 0.012843 |
| waiting for handler commit     | 0.000012 |
| waiting for handler commit     | 0.002951 |
| waiting for handler commit     | 0.000007 |
| waiting for handler commit     | 0.002383 |
| end                            | 0.000256 |
| query end                      | 0.002000 |
| closing tables                 | 0.000007 |
| waiting for handler commit     | 0.000015 |
| freeing items                  | 0.000015 |
| cleaning up                    | 0.000010 |
+--------------------------------+----------+
27 rows in set, 1 warning (0.00 sec)

```



## Задача 4 

Изучите файл `my.cnf` в директории /etc/mysql.

Измените его согласно ТЗ (движок InnoDB):

- скорость IO важнее сохранности данных;
- нужна компрессия таблиц для экономии места на диске;
- размер буффера с незакомиченными транзакциями 1 Мб;
- буффер кеширования 30% от ОЗУ;
- размер файла логов операций 100 Мб.

Приведите в ответе изменённый файл `my.cnf`.
### my.cnf
```
# нужна компрессия таблиц для экономии места на диске;
innodb_file_per_table=1

#размер буффера с незакомиченными транзакциями 1 Мб;
innodb_log_buffer_size=1M

#буффер кеширования 30% от ОЗУ (16GB);
innodb_buffer_pool_size=4.8G

#размер файла логов операций 100 Мб.
innodb_log_file_size=100M   

#скорость IO важнее сохранности данных;
innodb_flush_method = O_DSYNC 
```
---

### Как оформить ДЗ

Выполненное домашнее задание пришлите ссылкой на .md-файл в вашем репозитории.

---

