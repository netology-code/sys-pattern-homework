# Домашнее задание к занятию "Git" - Пешева Ирина


### Задание 1
**Что нужно сделать:**

1. Зарегистрируйте аккаунт на [GitHub](https://github.com/).
1. Создайте публичный репозиторий. Обязательно поставьте галочку в поле «Initialize this repository with a README».
2. Склонируйте репозиторий, используя https протокол `git clone ...`.
3. Перейдите в каталог с клоном репозитория.
1. Произведите первоначальную настройку Git, указав своё настоящее имя и email: `git config --global user.name` и `git config --global user.email johndoe@example.com`.
1. Выполните команду `git status` и запомните результат.
1. Отредактируйте файл README.md любым удобным способом, переведя файл в состояние Modified.
1. Ещё раз выполните `git status` и продолжайте проверять вывод этой команды после каждого следующего шага.
1. Посмотрите изменения в файле README.md, выполнив команды `git diff` и `git diff --staged`.
1. Переведите файл в состояние staged или, как говорят, добавьте файл в коммит, командой `git add README.md`.
1. Ещё раз выполните команды `git diff` и `git diff --staged`.
1. Теперь можно сделать коммит `git commit -m 'First commit'`.
1. Сделайте `git push origin master`.

В качестве ответа добавьте ссылку на этот коммит в ваш md-файл с решением.

### Решение 1
Клонируем репозиторий, устанавливаем начальные настройки – имя и почту.

![Screenshot](https://github.com/RedRatInTheHat/8.1-Git-HM/blob/main/img/1.png)

Проверяем статус:

![Screenshot](https://github.com/RedRatInTheHat/8.1-Git-HM/blob/main/img/2.png)

Никаких изменений.
Вносим изменения в README.md

![Screenshot](https://github.com/RedRatInTheHat/8.1-Git-HM/blob/main/img/3.png)

Появились изменения, пока не отслеживаемые в рамках создания коммита.
Проверяем изменения:

![Screenshot](https://github.com/RedRatInTheHat/8.1-Git-HM/blob/main/img/4.png)

Изменения есть, но в коммит они пока не попадут.
После добавления файла в “область видимости” всё наоборот.

![Screenshot](https://github.com/RedRatInTheHat/8.1-Git-HM/blob/main/img/5.png)

Создаём коммит и пушим его в GitHub.

![Screenshot](https://github.com/RedRatInTheHat/8.1-Git-HM/blob/main/img/6.png)

![README.md](https://github.com/RedRatInTheHat/8.1-Git/blob/main/README.md)


---
### Задание 2
**Что нужно сделать:**

1. Создайте файл .gitignore (обратите внимание на точку в начале файла) и проверьте его статус сразу после создания.
1. Добавьте файл .gitignore в следующий коммит `git add...`.
1. Напишите правила в этом файле, чтобы игнорировать любые файлы `.pyc`, а также все файлы в директории `cache`.
1. Сделайте коммит и пуш.

В качестве ответа добавьте ссылку на этот коммит в ваш md-файл с решением.

### Решение 2
Создан файл .gitignore

![Screenshot](https://github.com/RedRatInTheHat/8.1-Git-HM/blob/main/img/7.png)

Добавляем его в коммит, редактируем, снова добавляем в коммит.

![Screenshot](https://github.com/RedRatInTheHat/8.1-Git-HM/blob/main/img/8.png)

![Screenshot](https://github.com/RedRatInTheHat/8.1-Git-HM/blob/main/img/9.png)

Коммитим, пушим.

![Screenshot](https://github.com/RedRatInTheHat/8.1-Git-HM/blob/main/img/10.png)

Напоследок проверяем gitignore очистки совести для.

![Screenshot](https://github.com/RedRatInTheHat/8.1-Git-HM/blob/main/img/11.png)

Файлы не отслеживаются.

[Commit](https://github.com/RedRatInTheHat/8.1-Git/commit/106063a859da774cb74b667c11ae6cb62fc147d1)


---
### Задание 3
**Что нужно сделать:**

1. Создайте новую ветку dev и переключитесь на неё.
1. Создайте файл test.sh с произвольным содержимым.
1. Сделайте несколько коммитов и пушей, имитируя активную работу над этим файлом.
1. Сделайте мердж этой ветки в основную. Сначала нужно переключиться на неё, а потом вызывать `git merge`.
1. Сделайте коммит и пуш.
2. Не удаляйте ветку dev.

В качестве ответа прикрепите ссылку на граф коммитов https://github.com/ваш-логин/ваш-репозиторий/network в ваш md-файл с решением.

### Решение 3
Создаём dev.

![Screenshot](https://github.com/RedRatInTheHat/8.1-Git-HM/blob/main/img/12.png)

Добавляем файл и модифицируем его пару раз.

![Screenshot](https://github.com/RedRatInTheHat/8.1-Git-HM/blob/main/img/13.png)

Сливаем всё в main и пушим в GitHub.

![Screenshot](https://github.com/RedRatInTheHat/8.1-Git-HM/blob/main/img/14.png)

[История слияний](https://github.com/RedRatInTheHat/8.1-Git/network) 

---

## Дополнительные задания (со звездочкой*)

Эти задания дополнительные (не обязательные к выполнению) и никак не повлияют на получение вами зачета по этому домашнему заданию. Вы можете их выполнить, если хотите глубже и/или шире разобраться в материале.

### Задание 4
Сэмулируем конфликт. Перед выполнением изучите [документацию](https://git-scm.com/book/ru/v2/%D0%98%D0%BD%D1%81%D1%82%D1%80%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B-Git-%D0%9F%D1%80%D0%BE%D0%B4%D0%B2%D0%B8%D0%BD%D1%83%D1%82%D0%BE%D0%B5-%D1%81%D0%BB%D0%B8%D1%8F%D0%BD%D0%B8%D0%B5).

**Что нужно сделать:**

1. Создайте ветку conflict и переключитесь на неё.
2. Внесите изменения в файл test.sh. 
3. Сделайте коммит и пуш.
4. Переключитесь на основную ветку.
5. Измените ту же самую строчку в файле test.sh.
6. Сделайте коммит и пуш.
7. Сделайте мердж ветки conflict в основную ветку и решите конфликт так, чтобы в результате в файле оказался код из ветки conflict.

В качестве ответа на задание прикрепите ссылку на граф коммитов https://github.com/ваш-логин/ваш-репозиторий/network в ваш md-файл с решением.
### Решение 4
Создаём конфликт и получаем закономерный результат.

![Screenshot](https://github.com/RedRatInTheHat/8.1-Git-HM/blob/main/img/15.png)

Исправляем его, приняв сторону ветки conflict, добавляем файл в коммит, коммитим, а дальше он сам.

![Screenshot](https://github.com/RedRatInTheHat/8.1-Git-HM/blob/main/img/16.png)

[Network](https://github.com/RedRatInTheHat/8.1-Git/network) 


