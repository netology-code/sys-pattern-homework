# Домашнее задание к занятию 10.4 "`Резервное копирование`" - `Тимохин Максим`


### Задание 1

В чём разница между:

- полным резервным копированием,
- дифференциальным резервным копированием,
- инкрементным резервным копированием.

*Приведите ответ в свободной форме.*

Ответ:

`При полном бэкапе каждый раз создается полная копия всей системы,  точнее, всех тех данных, которые мы определили для резервного  копирования при постановке задачи. Для уменьшения итогового объема  резервной копии все данные сжимаются в архив. 
Инкрементальный обрабатывает файлы, измененные или созданные с момента выполнения предыдущего бэкапа;
Дифференциальный обрабатывает файлы, измененные или созданные с момента выполнения предыдущего полного бэкапа.`

---

### Задание 2

Установите программное обеспечении Bacula, настройте bacula-dir, bacula-sd,  bacula-fd. Протестируйте работу сервисов.

*Пришлите:*   
*- конфигурационные файлы для bacula-dir, bacula-sd,  bacula-fd,*   
*- скриншот, подтверждающий успешное прохождение резервного копирования.*

Ответ:

![1](https://github.com/MrAgrippa/8-03-hw/blob/main/1.JPG)
![2](https://github.com/MrAgrippa/8-03-hw/blob/main/2.JPG)
bacula-dir.conf
```
Director {
  Name = bacula-main
  DIRport = 9101
  QueryFile = "/etc/bacula/scripts/query.sql"
  WorkingDirectory = "/var/lib/bacula"
  PidDirectory = "/var/run/bacula"
  Maximum Concurrent Jobs = 1
  Password = "pass1"  
  Messages = Daemon
  DirAddress = 192.168.1.100
}

Messages {
Name = Daemon
append = "/var/log/bacula/bacula.log" = all, !skipped
}

Console {
  Name = bacula-main
  Password = "pass1"
  CommandACL = status, .status
}

Messages {
  Name = Standard
  mailcommand = "/usr/sbin/bsmtp -h localhost -f \"\(Bacula\) \<%r\>\" -s \"Bacula: %t %e of %c %l\" %r"
  operatorcommand = "/usr/sbin/bsmtp -h localhost -f \"\(Bacula\) \<%r\>\" -s \"Bacula: Intervention needed for %j\" %r"
  mail = root = all, !skipped            
  operator = root = mount
  console = all, !skipped, !saved
  append = "/var/log/bacula/bacula.log" = all, !skipped
  catalog = all
}

Catalog {
  Name = MyCatalog
  dbname = "bacula"; DB Address = ""; dbuser = "bacula"; dbpassword = "SQL_pass"
}

@/etc/bacula/client-conf/client-dir-node2.conf
```

---

### Задание 3

Установите программное обеспечении Rsync. Настройте синхронизацию на двух нодах. Протестируйте работу сервиса.

*Пришлите рабочую конфигурацию сервера и клиента Rsync блоком кода в вашем md-файле.*

Ответ:
![6](https://github.com/MrAgrippa/8-03-hw/blob/main/6.JPG)
![4](https://github.com/MrAgrippa/8-03-hw/blob/main/4.JPG)
![5](https://github.com/MrAgrippa/8-03-hw/blob/main/5.JPG)
---

### Задание со звёздочкой*
Это задание дополнительное. Его можно не выполнять. На зачёт это не повлияет. Вы можете его выполнить, если хотите глубже разобраться в материале.

---

### Задание 4*

Настройте резервное копирование двумя или более методами, используя одну из рассмотренных команд для папки /etc/default. Проверьте резервное копирование.

*Пришлите рабочую конфигурацию выбранного сервиса по поставленной задаче.*

`При необходимости прикрепитe сюда скриншоты
![Название скриншота](ссылка на скриншот)`
