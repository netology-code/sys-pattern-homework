# Домашнее задание к занятию 2. «SQL»

## Введение

Перед выполнением задания вы можете ознакомиться с 
[дополнительными материалами](https://github.com/netology-code/virt-homeworks/blob/virt-11/additional/README.md).

## Задача 1

Используя Docker, поднимите инстанс PostgreSQL (версию 12) c 2 volume, 
в который будут складываться данные БД и бэкапы.

Приведите получившуюся команду или docker-compose-манифест.

Задания 2 и 3 постарался выполнить тоже при первичной иннициализации БД.
### docker-compose.yml
```
version: "3.9"
services:
  postgres:
    container_name: postgres
    image: postgres:12
    environment:
      POSTGRES_DB: "test_db"
      POSTGRES_USER: "test-admin-user"
      POSTGRES_PASSWORD: "12345678"
      PGDATA: "/var/lib/postgresql/data/pgdata"
    volumes:
      - ./data:/var/lib/postgresql/data
      - ./arhive:/var/lib/postgresql/arhive
      - ./docker-entrypoint-initdb.d:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
```


## Задача 2

В БД из задачи 1: 

- создайте пользователя test-admin-user и БД test_db;
- в БД test_db создайте таблицу orders и clients (спeцификация таблиц ниже);
- предоставьте привилегии на все операции пользователю test-admin-user на таблицы БД test_db;
- создайте пользователя test-simple-user;
- предоставьте пользователю test-simple-user права на SELECT/INSERT/UPDATE/DELETE этих таблиц БД test_db.

Таблица orders:

- id (serial primary key);
- наименование (string);
- цена (integer).

Таблица clients:

- id (serial primary key);
- фамилия (string);
- страна проживания (string, index);
- заказ (foreign key orders).

### 01-init-db.sql
```
-- CREATE TABLE orders
DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
        order_id serial PRIMARY KEY,
        name VARCHAR ( 50 ) NOT NULL,
        price  integer 
);

-- CREATE TABLE clients
DROP TABLE IF EXISTS clients;
CREATE TABLE clients (
        client_id serial PRIMARY KEY,
        family VARCHAR ( 50 ) NOT NULL,
        country  VARCHAR ( 50 )  NOT NULL,
        orderId integer,
        FOREIGN KEY (orderId) REFERENCES orders (order_id)
);

-- CREATE user test-simple-user
CREATE USER "test-simple-user";

-- ADD PRIVILIGE user test-simple-user to test_db
GRANT SELECT,INSERT,UPDATE,DELETE ON orders, clients to "test-simple-user";
```
Приведите:
- итоговый список БД после выполнения пунктов выше;

```
test_db=# \l+
                                                                               List of databases
   Name    |      Owner      | Encoding |  Collate   |   Ctype    |            Access privileges            |  Size 
  | Tablespace |                Description                 
-----------+-----------------+----------+------------+------------+-----------------------------------------+-------
--+------------+--------------------------------------------
 postgres  | test-admin-user | UTF8     | en_US.utf8 | en_US.utf8 |                                         | 7969 k
B | pg_default | default administrative connection database
 template0 | test-admin-user | UTF8     | en_US.utf8 | en_US.utf8 | =c/"test-admin-user"                   +| 7825 k
B | pg_default | unmodifiable empty database
           |                 |          |            |            | "test-admin-user"=CTc/"test-admin-user" |       
  |            | 
 template1 | test-admin-user | UTF8     | en_US.utf8 | en_US.utf8 | =c/"test-admin-user"                   +| 7825 k
B | pg_default | default template for new databases
           |                 |          |            |            | "test-admin-user"=CTc/"test-admin-user" |       
  |            | 
 test_db   | test-admin-user | UTF8     | en_US.utf8 | en_US.utf8 |                                         | 8121 k
B | pg_default | 
(4 rows)
```
- описание таблиц (describe);
```
test_db=# SELECT table_name FROM information_schema.tables
WHERE table_schema NOT IN ('information_schema','pg_catalog');
 table_name 
------------
 orders
 clients
(2 rows)

test_db=#  \d+ orders
                                                           Table "public.orders"
  Column  |         Type          | Collation | Nullable |                 Default                  | Storage  | Sta
ts target | Description 
----------+-----------------------+-----------+----------+------------------------------------------+----------+----
----------+-------------
 order_id | integer               |           | not null | nextval('orders_order_id_seq'::regclass) | plain    |    
          | 
 name     | character varying(50) |           | not null |                                          | extended |    
          | 
 price    | integer               |           |          |                                          | plain    |    
          | 
Indexes:
    "orders_pkey" PRIMARY KEY, btree (order_id)
Referenced by:
    TABLE "clients" CONSTRAINT "clients_orderid_fkey" FOREIGN KEY (orderid) REFERENCES orders(order_id)
Access method: heap

test_db=# \d+ clients
                                                            Table "public.clients"
  Column   |         Type          | Collation | Nullable |                  Default                   | Storage  | 
Stats target | Description 
-----------+-----------------------+-----------+----------+--------------------------------------------+----------+-
-------------+-------------
 client_id | integer               |           | not null | nextval('clients_client_id_seq'::regclass) | plain    | 
             | 
 family    | character varying(50) |           | not null |                                            | extended | 
             | 
 country   | character varying(50) |           | not null |                                            | extended | 
             | 
 orderid   | integer               |           |          |                                            | plain    | 
             | 
Indexes:
    "clients_pkey" PRIMARY KEY, btree (client_id)
Foreign-key constraints:
    "clients_orderid_fkey" FOREIGN KEY (orderid) REFERENCES orders(order_id)
Access method: heap

```

- SQL-запрос для выдачи списка пользователей с правами над таблицами test_db;
```
test_db=# SELECT table_name,grantee,privilege_type 
FROM information_schema.table_privileges
WHERE table_schema NOT IN ('information_schema','pg_catalog');
 table_name |     grantee      | privilege_type 
------------+------------------+----------------
 orders     | test-admin-user  | INSERT
 orders     | test-admin-user  | SELECT
 orders     | test-admin-user  | UPDATE
 orders     | test-admin-user  | DELETE
 orders     | test-admin-user  | TRUNCATE
 orders     | test-admin-user  | REFERENCES
 orders     | test-admin-user  | TRIGGER
 clients    | test-admin-user  | INSERT
 clients    | test-admin-user  | SELECT
 clients    | test-admin-user  | UPDATE
 clients    | test-admin-user  | DELETE
 clients    | test-admin-user  | TRUNCATE
 clients    | test-admin-user  | REFERENCES
 clients    | test-admin-user  | TRIGGER
 orders     | test-simple-user | INSERT
 orders     | test-simple-user | SELECT
 orders     | test-simple-user | UPDATE
 orders     | test-simple-user | DELETE
 clients    | test-simple-user | INSERT
 clients    | test-simple-user | SELECT
 clients    | test-simple-user | UPDATE
 clients    | test-simple-user | DELETE
(22 rows)

```


## Задача 3

Используя SQL-синтаксис, наполните таблицы следующими тестовыми данными:

Таблица orders

|Наименование|цена|
|------------|----|
|Шоколад| 10 |
|Принтер| 3000 |
|Книга| 500 |
|Монитор| 7000|
|Гитара| 4000|

Таблица clients

|ФИО|Страна проживания|
|------------|----|
|Иванов Иван Иванович| USA |
|Петров Петр Петрович| Canada |
|Иоганн Себастьян Бах| Japan |
|Ронни Джеймс Дио| Russia|
|Ritchie Blackmore| Russia|

### 02-load-data.sql
```
-- LOAD DATAS orders
INSERT INTO orders(order_id, name,  price)
VALUES
    (1, 'Шоколад', 10),
    (2, 'Принтер', 3000),
    (3, 'Книга', 500),
    (4, 'Монитор', 7000), 
    (5, 'Гитара', 4000);


-- LOAD DATAS clients
INSERT INTO clients(client_id, family, country)
VALUES
    (1, 'Иванов Иван Иванович', 'USA'),
    (2, 'Петров Петр Петрович', 'Canada'),
    (3, 'Иоганн Себастьян Бах',  'Japan'),
    (4, 'Ронни Джеймс Дио', 'Russia'),
    (5, 'Ritchie Blackmore', 'Russia');
```
Используя SQL-синтаксис:
- вычислите количество записей для каждой таблицы.

```
test_db=# select count(*) from clients;
 count 
-------
     5
(1 row)

test_db=# select count(*) from orders;
 count 
-------
     5
(1 row)

```


## Задача 4

Часть пользователей из таблицы clients решили оформить заказы из таблицы orders.

Используя foreign keys, свяжите записи из таблиц, согласно таблице:

|ФИО|Заказ|
|------------|----|
|Иванов Иван Иванович| Книга |
|Петров Петр Петрович| Монитор |
|Иоганн Себастьян Бах| Гитара |


Приведите SQL-запросы для выполнения этих операций.
```
test_db=# UPDATE clients
SET orderId = (SELECT order_id FROM orders WHERE name = 'Книга')
WHERE family = 'Иванов Иван Иванович';

UPDATE clients
SET orderId = (SELECT order_id FROM orders WHERE name = 'Монитор')
WHERE family = 'Петров Петр Петрович';

UPDATE clients
SET orderId = (SELECT order_id FROM orders WHERE name = 'Гитара')
WHERE family = 'Иоганн Себастьян Бах';
UPDATE 1
UPDATE 1
UPDATE 1
```

Приведите SQL-запрос для выдачи всех пользователей, которые совершили заказ, а также вывод этого запроса.
```
test_db=# select * from clients;
 client_id |        family        | country | orderid 
-----------+----------------------+---------+---------
         4 | Ронни Джеймс Дио     | Russia  |        
         5 | Ritchie Blackmore    | Russia  |        
         1 | Иванов Иван Иванович | USA     |       3
         2 | Петров Петр Петрович | Canada  |       4
         3 | Иоганн Себастьян Бах | Japan   |       5
(5 rows)
```
 
Подсказка: используйте директиву `UPDATE`.

## Задача 5

Получите полную информацию по выполнению запроса выдачи всех пользователей из задачи 4 
(используя директиву EXPLAIN).

Приведите получившийся результат и объясните, что значат полученные значения.
```
test_db=# EXPLAIN select * from clients;
                         QUERY PLAN                         
------------------------------------------------------------
 Seq Scan on clients  (cost=0.00..13.00 rows=300 width=244)
(1 row)
```
Этот запрос не содержит предложения WHERE, поэтому он должен просканировать все строки таблицы, так что планировщик выбрал план простого последовательного сканирования. Числа, перечисленные в скобках (слева направо), имеют следующий смысл:

    Приблизительная стоимость запуска. Это время, которое проходит, прежде чем начнётся этап вывода данных, например для сортирующего узла это время сортировки.

    Приблизительная общая стоимость. Она вычисляется в предположении, что узел плана выполняется до конца, то есть возвращает все доступные строки. На практике родительский узел может досрочно прекратить чтение строк дочернего.

    Ожидаемое число строк, которое должен вывести этот узел плана. При этом так же предполагается, что узел выполняется до конца.

    Ожидаемый средний размер строк, выводимых этим узлом плана (в байтах).


## Задача 6

Создайте бэкап БД test_db и поместите его в volume, предназначенный для бэкапов (см. задачу 1).

```
root@2d45f64f820d:/# pg_dumpall -U test-admin-user -f test_db > /var/lib/postgresql/arhive/db-all.dump
```

Остановите контейнер с PostgreSQL, но не удаляйте volumes.
```
└─$ docker-compose down          
Stopping postgres ... done
Removing postgres ... done
Removing network 06-db-02-sql_default
```
Поднимите новый пустой контейнер с PostgreSQL.
Добавляем второй контейнер в docker-compose.yml
```
  postgres2:
    container_name: postgres2
    image: postgres:12
    environment:
      POSTGRES_DB: "test_db"
      POSTGRES_USER: "test-admin-user"
      POSTGRES_PASSWORD: "12345678"
      PGDATA: "/var/lib/postgresql/data/pgdata"
    volumes:
      - ./data2:/var/lib/postgresql/data
      - ./arhive:/var/lib/postgresql/arhive
#      - ./docker-entrypoint-initdb.d:/docker-entrypoint-initdb.d
    ports:
      - "54321:5432"
```
Поднимаем 2 контейнера
```
docker-compose up -d          
Creating network "06-db-02-sql_default" with the default driver
Creating postgres  ... done
Creating postgres2 ... done
```

Восстановите БД test_db в новом контейнере.

```
root@75739dcf1e6e:/# psql -U test-admin-user  -f /var/lib/postgresql/arhive/db-all.dump test_db
```

Приведите список операций, который вы применяли для бэкапа данных и восстановления. 

---

### Как cдавать задание

Выполненное домашнее задание пришлите ссылкой на .md-файл в вашем репозитории.

---

