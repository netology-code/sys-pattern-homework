# Домашнее задание к занятию 4. «PostgreSQL»

## Задача 1

Используя Docker, поднимите инстанс PostgreSQL (версию 13). Данные БД сохраните в volume.
### docker-compose.yml
```
version: "3.9"
services:
  postgres:
    container_name: postgres
    image: postgres:13
    environment:
      POSTGRES_DB: "test_database"
#      POSTGRES_USER: "admin_pg"
      POSTGRES_PASSWORD: "12345678"
      PGDATA: "/var/lib/postgresql/data/pgdata"
    volumes:
      - ./data:/var/lib/postgresql/data
      - ./docker-entrypoint-initdb.d:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"

```

Подключитесь к БД PostgreSQL, используя `psql`.

Воспользуйтесь командой `\?` для вывода подсказки по имеющимся в `psql` управляющим командам.

**Найдите и приведите** управляющие команды для:

- вывода списка БД,
  - \l[+]   [PATTERN]      list databases
- подключения к БД,
  - \c[onnect] {[DBNAME|- USER|- HOST|- PORT|-] | conninfo}
                           connect to new database (currently "postgres")
- вывода списка таблиц,
  - \d[S+]                 list tables, views, and sequences
  - \dp     [PATTERN]      list table, view, and sequence access privileges
  - \dt[S+] [PATTERN]      list tables
- вывода описания содержимого таблиц,
  - \d[S+]                 list tables, views, and sequences
  - \dt[S+] [PATTERN]      list tables
- выхода из psql
  - \q                     quit psql

## Задача 2

Используя `psql`, создайте БД `test_database`.

Изучите [бэкап БД](https://github.com/netology-code/virt-homeworks/tree/virt-11/06-db-04-postgresql/test_data).

Восстановите бэкап БД в `test_database`.
```
База данных создается автоматически и восстанавливается из каталога /docker-entrypoint-initdb.d в автоматическом режиме.
```
Перейдите в управляющую консоль `psql` внутри контейнера.

Подключитесь к восстановленной БД и проведите операцию ANALYZE для сбора статистики по таблице.

Используя таблицу [pg_stats](https://postgrespro.ru/docs/postgresql/12/view-pg-stats), найдите столбец таблицы `orders` 
с наибольшим средним значением размера элементов в байтах.

**Приведите в ответе** команду, которую вы использовали для вычисления, и полученный результат.
```
test_database=# ANALYZE VERBOSE public.orders;
INFO:  analyzing "public.orders"
INFO:  "orders": scanned 1 of 1 pages, containing 8 live rows and 0 dead rows; 8 rows in sample, 8 estimated total rows
ANALYZE
test_database=# SELECT tablename, attname, avg_width FROM pg_stats WHERE tablename='orders' ORDER BY avg_width DESC LIMIT 1;
 tablename | attname | avg_width 
-----------+---------+-----------
 orders    | title   |        16
(1 row)
```

## Задача 3

Архитектор и администратор БД выяснили, что ваша таблица orders разрослась до невиданных размеров и
поиск по ней занимает долгое время. Вам как успешному выпускнику курсов DevOps в Нетологии предложили
провести разбиение таблицы на 2: шардировать на orders_1 - price>499 и orders_2 - price<=499.

Предложите SQL-транзакцию для проведения этой операции.
```
CREATE TABLE orders_1 (CHECK (price < 499)) INHERITS (orders);
CREATE TABLE orders_2 (CHECK (price >= 499)) INHERITS (orders);

```
Можно ли было изначально исключить ручное разбиение при проектировании таблицы orders?
```
Да, можно было избежать разбиения таблицы вручную, необходимо было определить тип на моменте проектирования и создания - partitioned table
```

## Задача 4

Используя утилиту `pg_dump`, создайте бекап БД `test_database`.
```
root@521d2db25fd6:/# pg_dump -U postgres -d test_database > /var/lib/postgresql/data/db_dump.sql
root@521d2db25fd6:/# ls /var/lib/postgresql/data/
db_dump.sql  pgdata
```

Как бы вы доработали бэкап-файл, чтобы добавить уникальность значения столбца `title` для таблиц `test_database`?
Добавить параметр UNIQUE
```
--
-- Name: orders; Type: TABLE; Schema: public; Owner: postgres
--
CREATE TABLE public.orders (
    id integer NOT NULL,
    title character varying(80) UNIQUE NOT NULL,
    price integer DEFAULT 0
);
```
---

### Как cдавать задание

Выполненное домашнее задание пришлите ссылкой на .md-файл в вашем репозитории.

---

