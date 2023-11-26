# Домашнее задание к занятию «SQL. Часть 1» Свирин Марк

---

Задание можно выполнить как в любом IDE, так и в командной строке.

### Задание 1

Получите уникальные названия районов из таблицы с адресами, которые начинаются на “K” и заканчиваются на “a” и не содержат пробелов.
```
SELECT DISTINCT district
FROM sakila.address
WHERE district like 'K%a'
      and POSITION(' ' IN district) = 0;
```

![image](https://github.com/svmarkst/netology-hw/assets/110044256/a5e6ea20-7141-4d00-baf4-376b55814ae4)


### Задание 2

Получите из таблицы платежей за прокат фильмов информацию по платежам, которые выполнялись в промежуток с 15 июня 2005 года по 18 июня 2005 года **включительно** и стоимость которых превышает 10.00.

```
SELECT *
FROM sakila.payment
WHERE Date(payment_date) between '2005-06-15' and '2005-06-18'
		and amount > 10.0;
```
![image](https://github.com/svmarkst/netology-hw/assets/110044256/4643d275-0ea9-4a29-8a66-89c97b9c2df9)

### Задание 3

Получите последние пять аренд фильмов.
```
SELECT *
FROM sakila.rental
ORDER BY rental_date DESC
LIMIT 5;
```
![image](https://github.com/svmarkst/netology-hw/assets/110044256/e0bc1617-3756-4090-9554-d320b90f237e)

### Задание 4

Одним запросом получите активных покупателей, имена которых Kelly или Willie. 

Сформируйте вывод в результат таким образом:
- все буквы в фамилии и имени из верхнего регистра переведите в нижний регистр,
- замените буквы 'll' в именах на 'pp'.
```
SELECT REPLACE(LOWER(first_name), 'll', 'pp'), LOWER(last_name), active
FROM sakila.customer
WHERE first_name IN ('Kelly', 'Willie') and active = 1;
```
![image](https://github.com/svmarkst/netology-hw/assets/110044256/f69ba280-9b83-4c13-b832-ec2a875b1c71)

