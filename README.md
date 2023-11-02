# Домашнее задание к занятию "`Git" - `Тихун Вадим`


### Инструкция по выполнению домашнего задания

   1. Сделайте `fork` данного репозитория к себе в Github и переименуйте его по названию или номеру занятия, например, https://github.com/имя-вашего-репозитория/git-hw или  https://github.com/имя-вашего-репозитория/7-1-ansible-hw.
   2. Выполните клонирование данного репозитория к себе на ПК с помощью команды `git clone`.
   3. Выполните домашнее задание и заполните у себя локально этот файл README.md:
      - впишите вверху название занятия и вашу фамилию и имя
      - в каждом задании добавьте решение в требуемом виде (текст/код/скриншоты/ссылка)
      - для корректного добавления скриншотов воспользуйтесь [инструкцией "Как вставить скриншот в шаблон с решением](https://github.com/netology-code/sys-pattern-homework/blob/main/screen-instruction.md)
      - при оформлении используйте возможности языка разметки md (коротко об этом можно посмотреть в [инструкции  по MarkDown](https://github.com/netology-code/sys-pattern-homework/blob/main/md-instruction.md))
   4. После завершения работы над домашним заданием сделайте коммит (`git commit -m "comment"`) и отправьте его на Github (`git push origin`);
   5. Для проверки домашнего задания преподавателем в личном кабинете прикрепите и отправьте ссылку на решение в виде md-файла в вашем Github.
   6. Любые вопросы по выполнению заданий спрашивайте в чате учебной группы и/или в разделе “Вопросы по заданию” в личном кабинете.
   
Желаем успехов в выполнении домашнего задания!
   
### Дополнительные материалы, которые могут быть полезны для выполнения задания

1. [Руководство по оформлению Markdown файлов](https://gist.github.com/Jekins/2bf2d0638163f1294637#Code)

---

### Задание 1

1. У меня был уже зарегистророван аккаунт, поэтому этот этап пропущу
2. Клонирую задание  себе на компьютер
```bash
vadim@vadim:~$ git clone https://github.com/netology-code/sys-pattern-homework
Клонирование в «sys-pattern-homework»...
remote: Enumerating objects: 73, done.
remote: Counting objects: 100% (3/3), done.
remote: Compressing objects: 100% (3/3), done.
remote: Total 73 (delta 0), reused 0 (delta 0), pack-reused 70
Получение объектов: 100% (73/73), 3.58 МиБ | 1.83 МиБ/с, готово.
Определение изменений: 100% (27/27), готово.
```


4. Указал своё имя и почту
```bash
vadim@vadim:~$ git config --global user.name sailent9
vadim@vadim:~$ git config --global user.email silent912@gmail.com
```
5. Выполнил команду:
```bash
vadim@vadim:~$ git status
Текущая ветка: main
Неотслеживаемые файлы:
(используйте «git add <файл>...», чтобы добавить в то, что будет включено в коммит)
индекс пуст, но есть неотслеживаемые файлы
(используйте «git add», чтобы проиндексировать их)
```

6. Вывод команды git status 
```bash
vadim@vadim:~/git-homework$ git status
Текущая ветка: main
Эта ветка соответствует «origin/main».

Неотслеживаемые файлы:
  (используйте «git add <файл>...», чтобы добавить в то, что будет включено в коммит)
        img/vscode.png

индекс пуст, но есть неотслеживаемые файлы
(используйте «git add», чтобы проиндексировать их)
```
7. Выполнил команды: `git diff` и `diff --staged`  У команды `git diff`  был слишком подробный вывод и сюда прикреплять я его не стал
```bash
vadim@vadim:~/git-homework$ git diff --staged
diff --git a/img/vscode.png b/img/vscode.png
new file mode 100644
index 0000000..80e8494
Binary files /dev/null and b/img/vscode.png differ
vadim@vadim:~/git-homework$ 
```
9. Всё "запушил".



---

 2

1. Создал файл `./gitignore` из меню VSCode
2. Добавил файл в ветку


```bash
vadim@vadim:~/git-homework$ git add .gitignore
vadim@vadim:~/git-homework$ git status
Текущая ветка: main
Ваша ветка опережает «origin/main» на 1 коммит.
  (используйте «git push», чтобы опубликовать ваши локальные коммиты)

Изменения, которые будут включены в коммит:
  (используйте «git restore --staged <файл>...», чтобы убрать из индекса)
        новый файл:    .gitignore
