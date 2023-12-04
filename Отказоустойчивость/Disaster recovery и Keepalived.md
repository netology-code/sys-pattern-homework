# Домашнее задание к занятию 1 «Disaster recovery и Keepalived» Свирин Марк


------


### Задание 1
- Дана [схема](1/hsrp_advanced.pkt) для Cisco Packet Tracer, рассматриваемая в лекции.
- На данной схеме уже настроено отслеживание интерфейсов маршрутизаторов Gi0/1 (для нулевой группы)
- Необходимо аналогично настроить отслеживание состояния интерфейсов Gi0/0 (для первой группы).
- Для проверки корректности настройки, разорвите один из кабелей между одним из маршрутизаторов и Switch0 и запустите ping между PC0 и Server0.
- На проверку отправьте получившуюся схему в формате pkt и скриншот, где виден процесс настройки маршрутизатора.

![image](https://github.com/svmarkst/netology-hw/assets/110044256/fc81e07a-1964-4ee8-a0e9-3123fa92bcb1)
![image](https://github.com/svmarkst/netology-hw/assets/110044256/58bf3cf5-cfba-47ca-9751-c1b0a97aa1ee)
![image](https://github.com/svmarkst/netology-hw/assets/110044256/fead7381-b0b8-4c1e-bd12-d43d9262161d)

https://github.com/svmarkst/netology-hw/blob/main/svirinmark.pkt 

------


### Задание 2
- Запустите две виртуальные машины Linux, установите и настройте сервис Keepalived как в лекции, используя пример конфигурационного [файла](1/keepalived-simple.conf).
- Настройте любой веб-сервер (например, nginx или simple python server) на двух виртуальных машинах
- Напишите Bash-скрипт, который будет проверять доступность порта данного веб-сервера и существование файла index.html в root-директории данного веб-сервера.
- Настройте Keepalived так, чтобы он запускал данный скрипт каждые 3 секунды и переносил виртуальный IP на другой сервер, если bash-скрипт завершался с кодом, отличным от нуля (то есть порт веб-сервера был недоступен или отсутствовал index.html). Используйте для этого секцию vrrp_script
- На проверку отправьте получившейся bash-скрипт и конфигурационный файл keepalived, а также скриншот с демонстрацией переезда плавающего ip на другой сервер в случае недоступности порта или файла index.html

![image](https://github.com/svmarkst/netology-hw/assets/110044256/71357ccf-acc7-4dc2-bfa3-12fd667829a1)

![image](https://github.com/svmarkst/netology-hw/assets/110044256/d916455f-2e41-4d2e-96e9-35767a9ade3d)

![image](https://github.com/svmarkst/netology-hw/assets/110044256/f551f4e3-b4a4-47fc-b3da-cb405705ef02)

![image](https://github.com/svmarkst/netology-hw/assets/110044256/f696ef48-c708-4a31-a1b7-6823bceab680)

------
