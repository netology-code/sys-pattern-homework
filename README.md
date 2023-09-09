# `Домашнее задание к занятию 2 «Кластеризация и балансировка нагрузки»»`

# **Задание 1**

Запустите два simple python сервера на своей виртуальной машине на разных портах
Установите и настройте HAProxy, воспользуйтесь материалами к лекции по ссылке
Настройте балансировку Round-robin на 4 уровне.
На проверку направьте конфигурационный файл haproxy, скриншоты, где видно перенаправление запросов на разные серверы при обращении к HAProxy.

![alt text](https://github.com/BOSe1337/8-03-hw/blob/main/Pictures/ha1.jpg)

![alt text](https://github.com/BOSe1337/8-03-hw/blob/main/Pictures/ha2.jpg)

![alt text](https://github.com/BOSe1337/8-03-hw/blob/main/Pictures/ha3.jpg)

![alt text](https://github.com/BOSe1337/8-03-hw/blob/main/Pictures/ha4.jpg)

![alt text](https://github.com/BOSe1337/8-03-hw/blob/main/Pictures/ha5.jpg)


# **Задание 2**

Запустите три simple python сервера на своей виртуальной машине на разных портах
Настройте балансировку Weighted Round Robin на 7 уровне, чтобы первый сервер имел вес 2, второй - 3, а третий - 4
HAproxy должен балансировать только тот http-трафик, который адресован домену example.local
На проверку направьте конфигурационный файл haproxy, скриншоты, где видно перенаправление запросов на разные серверы при обращении к HAProxy c использованием домена example.local и без него.


![alt text](https://github.com/BOSe1337/8-03-hw/blob/main/Pictures/ha6.jpg)

![alt text](https://github.com/BOSe1337/8-03-hw/blob/main/Pictures/ha7.jpg)

![alt text](https://github.com/BOSe1337/8-03-hw/blob/main/Pictures/ha8.jpg)
