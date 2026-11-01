# Домашнее задание к занятию «Шаблоны и дашборды Zabbix» — Корченко

Стенд: Zabbix 7.4 (Ubuntu 24.04, MySQL, Nginx). Все действия выполнены через Zabbix API (`/api_jsonrpc.php`) и проверены в веб-интерфейсе.

---

### Задание 1

Создан шаблон `Zadanie_1` (видимое имя «Задание 1») в группе **Templates** с двумя элементами данных:

| Имя | Ключ | Тип | Интервал | Единицы |
|---|---|---|---|---|
| Загрузка CPU, % | `system.cpu.util[]` | Zabbix agent | 1m | % |
| Загрузка RAM, % | `vm.memory.size[pused]` | Zabbix agent | 1m | % |

Шаги:
1. *Data collection → Templates → Create template*: Template name `Zadanie_1`, Visible name `Задание 1`, Template groups `Templates`.
2. *Items → Create item* — два элемента из таблицы выше (тип Zabbix agent, тип информации Numeric (float), Update interval `1m`, Units `%`).

> Примечание про ключ CPU. На хостах уже привязан штатный шаблон **Linux by Zabbix agent**, в котором есть элемент с ключом `system.cpu.util` (зависимый элемент «CPU utilization»). Zabbix не позволяет унаследовать на хост два элемента с одинаковым ключом, поэтому шаблон с ключом `system.cpu.util` к хостам не привязывается (ошибка *Cannot inherit item with key "system.cpu.util" … already inherited from template "Linux by Zabbix agent"*). Чтобы не удалять существующие шаблоны, использован ключ `system.cpu.util[]`: это та же проверка агента с параметрами по умолчанию (`cpu=all`, `type=user`, `mode=avg1`), но строка ключа уникальна.

![Шаблон «Задание 1»](https://github.com/ProffeSOr24/solution-template/blob/main/zabbix_hw2/img/zadanie1-template.png)

---

### Задание 2 и Задание 3

**Задание 2.** Агенты Zabbix на обоих хостах уже установлены, в `/etc/zabbix/zabbix_agentd.conf` прописаны `Server` и `ServerActive` с адресом Zabbix-сервера. Хосты переименованы (поля *Host name* и *Visible name*):

| Было | Стало | Интерфейс агента |
|---|---|---|
| Zabbix server | `korchenko-1` | 127.0.0.1:10050 |
| vm2 | `korchenko-2` | 158.160.229.50:10050 |

**Задание 3.** К обоим хостам дополнительно привязан шаблон «Задание 1» (*Data collection → Hosts → хост → Templates → Link new templates*), ранее привязанные шаблоны (`Linux by Zabbix agent`, `Zabbix server health`) сохранены. Доступность агента — зелёный значок **ZBX**.

![Data collection → Hosts](https://github.com/ProffeSOr24/solution-template/blob/main/zabbix_hw2/img/zadanie3-hosts.png)

В *Monitoring → Latest data* по обоим хостам приходят значения элементов шаблона `system.cpu.util[]` и `vm.memory.size[pused]`:

![Monitoring → Latest data](https://github.com/ProffeSOr24/solution-template/blob/main/zabbix_hw2/img/zadanie3-latest-data.png)

---

### Задание 4

Создан дашборд «Задание 4» (*Dashboards → Create dashboard*) с двумя виджетами типа **Graph**:

- **Загрузка CPU, %**: наборы данных `korchenko-1` / `korchenko-2`, элемент «Загрузка CPU, %» (`system.cpu.util[]`);
- **Загрузка RAM, %**: наборы данных `korchenko-1` / `korchenko-2`, элемент «Загрузка RAM, %» (`vm.memory.size[pused]`).

Скриншот сделан после того, как на графиках накопились данные.

![Дашборд «Задание 4»](https://github.com/ProffeSOr24/solution-template/blob/main/zabbix_hw2/img/zadanie4-dashboard.png)
