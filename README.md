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

**bacula-dir.conf**

```java
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
 
JobDefs {
    Name = "DefaultJob"
    Type = Backup
    Level = Incremental
    Client = bacula-fd
    FileSet = "Full Set"
    Schedule = "WeeklyCycle"
    Storage = File
    Messages = Standard
    Pool = File
    Priority = 10
    Write Bootstrap = "/var/db/bacula/%c.bsr"
}

JobDefs {
    Name = "DefaultJob"
    Type = Backup
    Level = Incremental
    Client = node2-fd
    FileSet = "Full Set"
    Schedule = "WeeklyCycle"
    Storage = File
    Messages = Standard
    Pool = File
    Priority = 10
    Write Bootstrap = "/var/db/bacula/%c.bsr"
}
 
Job {
    Name = "BackupCatalog"
    JobDefs = "DefaultJob"
    Level = Full
    FileSet="Catalog"
    Schedule = "WeeklyCycleAfterBackup"
    RunBeforeJob = "/usr/local/share/bacula/make_catalog_backup.pl MyCatalog"
    RunAfterJob  = "/usr/local/share/bacula/delete_catalog_backup"
    Write Bootstrap = "/var/db/bacula/%n.bsr"
    Priority = 11
}
  
FileSet {
    Name = "Full Set"
    Include {
        Options {
            signature = MD5
        }
        File = /etc
        File = /root
        File = /usr/local/etc
}
 
    Exclude {
    }
}
 
Schedule {
    Name = "WeeklyCycle"
    Run = Full 1st sun at 23:05
    Run = Differential 2nd-5th sun at 23:05
    Run = Incremental mon-sat at 23:05
}
 
Schedule {
    Name = "WeeklyCycleAfterBackup"
    Run = Full sun-sat at 23:10
}
 
FileSet {
    Name = "Catalog"
    Include {
        Options {
            signature = MD5
        }
        File = "/var/db/bacula/bacula.sql"
    }
}
 
Client {
    Name = bacula-fd
    Address = localhost
    FDPort = 9102
    Catalog = MyCatalog
    Password = "pass1"
    File Retention = 30 days
    Job Retention = 6 months
    AutoPrune = yes
}

Client {
    Name = node2-fd
    Address = 192.168.1.101
    FDPort = 9102
    Catalog = MyCatalog
    Password = "pass1"
    File Retention = 30 days
    Job Retention = 6 months
    AutoPrune = yes
}
 
Storage {
    Name = File
    Address = 192.168.1.100
    SDPort = 9103
    Password = "pass1
    Device = FileStorage
    Media Type = File
}
 
Catalog {
    Name = MyCatalog
    dbdriver = "dbi:sqlite3";
    dbname = "bacula"; DB Address = "localhost"; dbuser = "bacula"; dbpassword = "pass1"
}
 
Messages {
    Name = Standard
    mailcommand = "/usr/local/sbin/bsmtp -h localhost -f \"\(Bacula\) \<%r\>\" -s \"Bacula: %t %e of %c %l\" %r"
    operatorcommand = "/usr/local/sbin/bsmtp -h localhost -f \"\(Bacula\) \<%r\>\" -s \"Bacula: Intervention needed for %j\" %r"
    mail = root@localhost = all, !skipped            
    operator = root@localhost = mount
    console = all, !skipped, !saved
    append = "/var/log/bacula/bacula.log" = all, !skipped
    catalog = all
}
 
Messages {
    Name = Daemon
    mailcommand = "/usr/local/sbin/bsmtp -h localhost -f \"\(Bacula\) \<%r\>\" -s \"Bacula daemon message\" %r"
    mail = root@localhost = all, !skipped            
    console = all, !skipped, !saved
    append = "/var/log/bacula/bacula.log" = all, !skipped
}
 
Pool {
    Name = Backup
    Pool Type = Backup
    Recycle = yes
    AutoPrune = yes
    Volume Retention = 65 days
    LabelFormat = "Backup-${Year}_${Month}_${Day}"
    Maximum Volume Bytes = 100G
    Maximum Volumes = 100
}

@/etc/bacula/client-conf/client-dir-node2.conf
```

**bacula-fd.conf**

```java
Director {
  Name = bacula-main
  Password = "pass1"
}

FileDaemon { 
  Name =  bacula-main
  FDport = 9102 
  WorkingDirectory = /var/lib/bacula
  Pid Directory = /var/run/bacula
  Maximum Concurrent Jobs = 20
  FDAddress = 192.168.1.100  
}

Messages {
  Name = Standard
  director = bacula-main = all, !skipped, !restored
}
```

**bacula-sd.conf**

```java
Storage { 
  Name = centre-sd 
  SDPort = 9103 
  WorkingDirectory = "/var/lib/bacula" 
  Pid Directory = "/var/run/bacula" 
  SDAddress = 192.168.1.100 
} 
Director {
  Name = bacula-main
  Password = "pass1"
}

Device {
  Name = FileStorage
  Media Type = File
  Archive Device = /var/bacula_backups
  LabelMedia = yes;
  Random Access = Yes;
  AutomaticMount = yes;
  RemovableMedia = no;
  AlwaysOpen = no;
}
```
![bacula](https://github.com/MrAgrippa/8-03-hw/blob/main/bacula.JPG)
![status](https://github.com/MrAgrippa/8-03-hw/blob/main/dir.JPG)
![bacula-work](https://github.com/MrAgrippa/8-03-hw/blob/main/dir3.JPG)

---

### Задание 3

Установите программное обеспечении Rsync. Настройте синхронизацию на двух нодах. Протестируйте работу сервиса.

*Пришлите рабочую конфигурацию сервера и клиента Rsync блоком кода в вашем md-файле.*

Ответ:
Конфиг файл node1 ***/etc/rsyncd.conf***

```java
pid file = /var/run/rsyncd.pid
log file = /var/log/rsyncd.log
transfer logging = true
munge symlinks = yes

[data]
    path = /root/
    uid = root
    comment = Data backup folders
    read only = yes
    list = yes
    auth users = backup
    secrets file = /usr/local/etc/rsyncd.scrt

[new]
    path = /etc/
    uid = root
    comment = Data backup
    read only = yes
    list = yes
    auth users = backup
    secrets file = /usr/local/etc/rsyncd.scrt
```
Конфиг файл node 2  ***/etc/rsyncd.conf***

```java
pid file = /var/run/rsyncd.pid
log file = /var/log/rsyncd.log
transfer logging = true
munge symlinks = yes

[data]
    path = /root/
    uid = root
    comment = Data backup folders
    read only = yes
    list = yes
    auth users = backup
    secrets file = /usr/local/etc/rsyncd.scrt

[new]
    path = /etc/
    uid = root
    comment = Data backup
    read only = yes
    list = yes
    auth users = backup
    secrets file = /usr/local/etc/rsyncd.scrt
```

Скрипт который запускает бекапирование 

```bash
#!/bin/bash
date
# Папка, куда будем складывать архивы — ее либо сразу создать либо не создавать а положить в уже существующие
syst_dir=/backup/
# Имя сервера, который архивируем
srv_name=node1 #из тестовой конфигурации
# Адрес сервера, который архивируем
srv_ip=192.168.1.101
# Пользователь rsync на сервере, который архивируем
srv_user=backup
# Ресурс на сервере для бэкапа
srv_dir=data
echo "Start backup ${srv_name}"
# Создаем папку для инкрементных бэкапов
mkdir -p ${syst_dir}${srv_name}/increment/
/usr/bin/rsync -avz --progress --delete
--password-file=/etc/rsyncd.scrt ${srv_user}@${srv_ip}::${srv_dir}
${syst_dir}${srv_name}/current/ --backup
--backup-dir=${syst_dir}${srv_name}/increment/`date +%Y-%m-%d`/
/usr/bin/find ${syst_dir}${srv_name}/increment/ -maxdepth 1 -type d
-mtime +30 -exec rm -rf {} \;
date
echo "Finish backup ${srv_name}"
```

Результат работы скрипта и rsync:
![rsync](https://github.com/MrAgrippa/8-03-hw/blob/main/rsync1.JPG)

---

### Задание со звёздочкой*
Это задание дополнительное. Его можно не выполнять. На зачёт это не повлияет. Вы можете его выполнить, если хотите глубже разобраться в материале.

---

### Задание 4*

Настройте резервное копирование двумя или более методами, используя одну из рассмотренных команд для папки /etc/default. Проверьте резервное копирование.

*Пришлите рабочую конфигурацию выбранного сервиса по поставленной задаче.*

`При необходимости прикрепитe сюда скриншоты
![Название скриншота](ссылка на скриншот)`
