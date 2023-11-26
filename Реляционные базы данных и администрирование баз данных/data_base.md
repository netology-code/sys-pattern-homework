# Домашнее задание к занятию `«12.1 «Базы данных»»` - `Васильев Николай`

---
## Задание 1.

Составил диаграмму на ресурсе [dbdesigner](https://dbdesigner.page.link/WBBxV6jEvJVZbCvy6), не получалось все это представить в голове.

### Описание

````
employee (
	employee_id integer pk increments unique > hiring.employe_id
	last_name varchar(75)
	first_name varchar
	patronymic varchar(40) null
)

address (
	address_id integer pk increments unique *> hiring.address_id
	region varchar(30)
	city varchar(25)
	street varchar(150)
	home varchar(5)
)

hiring (
	hiring_id integer pk increments unique
	date_hiring date
	employe_id integer > employee.employee_id
	salary integer
	address_id integer
	unit_id integer
	project_id integer
)

unit_type (
	id_unit_type integer pk increments unique *> unit.id_unit_type
	name_unit_type varchar(20)
)

Structural_unit (
	id_structural_unit integer pk increments unique *> unit.id_structural_unit
	name_structural_unit varchar(100)
)

unit (
	unit_id integer pk increments unique *> hiring.unit_id
	id_unit_type integer
	id_structural_unit integer
	id_position integer
)

position (
	id_position integer pk increments unique *> unit.id_position
	name_position varchar(50)
)

project (
	project_id integer pk increments unique *> hiring.project_id
	name_project varchar(50)
)
````