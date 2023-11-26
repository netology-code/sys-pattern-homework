# Домашнее задание к занятию «SQL. Часть 2»

---

Задание можно выполнить как в любом IDE, так и в командной строке.

### Задание 1

Одним запросом получите информацию о магазине, в котором обслуживается более 300 покупателей, и выведите в результат следующую информацию: 
- фамилия и имя сотрудника из этого магазина;
- город нахождения магазина;
- количество пользователей, закреплённых в этом магазине.

```
SELECT	CONCAT(stf.first_name , ' ', stf.last_name) as 'employee',
		c.city,
		COUNT(cus.customer_id) as 'buyers'		
FROM sakila.store st
JOIN sakila.staff stf ON stf.store_id = st.store_id 
JOIN sakila.customer cus ON cus.store_id = st.store_id
JOIN sakila.address ad ON ad.address_id = st.address_id 
JOIN sakila.city c ON c.city_id = ad.city_id 
GROUP BY stf.staff_id, c.city_id 
HAVING COUNT(cus.customer_id) > 300;
```
![image](https://github.com/svmarkst/netology-hw/assets/110044256/dd40cf76-748c-486a-8a3f-6e659dffc3ef)

### Задание 2

Получите количество фильмов, продолжительность которых больше средней продолжительности всех фильмов.
```
SELECT COUNT(f.title)
FROM sakila.film f  
WHERE f.`length` > (SELECT AVG(`length`) 
                    FROM sakila.film);
```
![image](https://github.com/svmarkst/netology-hw/assets/110044256/bc44b1ff-53c1-406c-86c7-6431b4650c0d)

### Задание 3

Получите информацию, за какой месяц была получена наибольшая сумма платежей, и добавьте информацию по количеству аренд за этот месяц.
