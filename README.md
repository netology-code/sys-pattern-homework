# Домашнее задание к занятию «Уязвимости и атаки на информационные системы» - `Иванов Федор`

### Задание 1

Разверните GitLab локально, используя Vagrantfile и инструкцию, описанные в этом репозитории.
Создайте новый проект и пустой репозиторий в нём.
Зарегистрируйте gitlab-runner для этого проекта и запустите его в режиме Docker. Раннер можно регистрировать и запускать на той же виртуальной машине, на которой запущен GitLab.

`Приведите ответ в свободной форме........`

1. `запускаем vagrant и разворачиваем GitLab`
2. `Создаем новый проект projekt8.03, скриншот 1`
3. `Регистрируем gitlab-runner скриншот 2 и 3`


![Скриншот-1](https://github.com/zef33/DZ8.03/blob/sek/sek/1.jpg)
![Скриншот-2](https://github.com/zef33/DZ8.03/blob/main/img/скрин2.png)
![Скриншот-3](https://github.com/zef33/DZ8.03/blob/main/img/скрин3.png)


---

### Задание 2
Что нужно сделать:

Запушьте репозиторий на GitLab, изменив origin. Это изучалось на занятии по Git.
Создайте .gitlab-ci.yml, описав в нём все необходимые, на ваш взгляд, этапы.

1. Создаем в проекте projekt8.03 .gitlab-ci.yml
2. Запускаем задачи и проверяем работоспо собность

```
Поле для вставки кода...
stages:
  - test
  - build

test:
  stage: test
  image: golang:1.17
  script: 
   - go test .
  tags:
     - netology

static-analysis:
 stage: test
 image:
  name: sonarsource/sonar-scanner-cli
  entrypoint: [""]
 variables:
 script:
  - sonar-scanner -Dsonar.projectKey=netology -Dsonar.sources=. -Dsonar.host.url=http://gitlab.localdomain:9000 -Dsonar.login=sqp_9f0ab50a2ed92fa6e6af66061be9612ba57ed3f9
 tags:
     - netology

build:
  stage: build
  image: docker:latest
  script:
   - docker build .
  

build:
  stage: build
  image: docker:latest
  script:
   - docker build .
  tags:
      - netology

```
![Скриншот-4](https://github.com/zef33/DZ8.03/blob/main/img/скрин4.png)
![Скриншот-5](https://github.com/zef33/DZ8.03/blob/main/img/скрин5.png)
![Скриншот-6](https://github.com/zef33/DZ8.03/blob/main/img/скрин6.png)
