# Домашнее задание к занятию 2 «Кластеризация и балансировка нагрузки» Свирин Марк




------



### Задание 1
- Запустите два simple python сервера на своей виртуальной машине на разных портах
- Установите и настройте HAProxy, воспользуйтесь материалами к лекции по [ссылке](2/)
- Настройте балансировку Round-robin на 4 уровне.
- На проверку направьте конфигурационный файл haproxy, скриншоты, где видно перенаправление запросов на разные серверы при обращении к HAProxy.

Запущенные python сервера:
![image](https://github.com/svmarkst/netology-hw/assets/110044256/3a6d8fc1-546d-428a-880a-32a8ee0dd7c5)
![image](https://github.com/svmarkst/netology-hw/assets/110044256/c7f6860d-7834-48fa-b0da-c952153b2e85)

https://github.com/svmarkst/netology-hw/blob/main/haproxy.cfg 
------

### Задание 2
- Запустите три simple python сервера на своей виртуальной машине на разных портах
- Настройте балансировку Weighted Round Robin на 7 уровне, чтобы первый сервер имел вес 2, второй - 3, а третий - 4
- HAproxy должен балансировать только тот http-трафик, который адресован домену example.local
- На проверку направьте конфигурационный файл haproxy, скриншоты, где видно перенаправление запросов на разные серверы при обращении к HAProxy c использованием домена example.local и без него.

![image](https://github.com/svmarkst/netology-hw/assets/110044256/dcd79c0b-4a11-46fd-a220-4df1e5b63741)
https://github.com/svmarkst/netology-hw/blob/main/haproxy2.cfg 

------
