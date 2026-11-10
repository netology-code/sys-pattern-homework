# Домашнее задание к занятию «Disaster recovery и Keepalived» — Корченко Леонид Владиславович

---

### Задание 1

_в работе_

---

### Задание 2

Стенд: две виртуальные машины KVM с Ubuntu 24.04 — `node1` (192.168.122.14) и `node2` (192.168.122.178), интерфейс `enp1s0`. Виртуальный IP — `192.168.122.250`.

На обеих машинах установлены nginx и Keepalived:

```bash
sudo apt install -y nginx keepalived
```

Для наглядности у машин разные стартовые страницы (`/var/www/html/index.html`): `<h1>node1</h1>` и `<h1>node2</h1>`.

#### Скрипт проверки

`/etc/keepalived/check_web.sh` — проверяет, что порт nginx отвечает и в root-директории есть `index.html`. Код 0 — веб-сервер исправен, иначе — нет.

```bash
#!/bin/bash
# Проверка веб-сервера для Keepalived:
# порт nginx отвечает и в root-директории есть index.html

PORT=80
INDEX=/var/www/html/index.html

# 1. Отвечает ли порт веб-сервера
if ! nc -z -w 2 127.0.0.1 "$PORT"; then
    exit 1
fi

# 2. Существует ли index.html
if [ ! -f "$INDEX" ]; then
    exit 2
fi

exit 0
```

```bash
sudo chmod +x /etc/keepalived/check_web.sh
```

#### Конфигурация Keepalived

`/etc/keepalived/keepalived.conf` на `node1`:

```
global_defs {
    enable_script_security
    script_user root
}

vrrp_script check_web {
    script "/etc/keepalived/check_web.sh"
    interval 3
}

vrrp_instance VI_1 {
    state MASTER
    interface enp1s0
    virtual_router_id 15
    priority 150
    advert_int 1

    virtual_ipaddress {
        192.168.122.250/24
    }

    track_script {
        check_web
    }
}
```

На `node2` конфигурация такая же, кроме `state BACKUP` и `priority 100`.

Скрипт запускается каждые 3 секунды (`interval 3`). Если он завершается с кодом, отличным от 0, экземпляр VRRP переходит в состояние FAULT и отдаёт виртуальный IP — его забирает `node2`.

#### Проверка

На `node1` убран `index.html` (`sudo mv /var/www/html/index.html /var/www/html/index.html.bak`). Скрипт вернул ошибку, `node1` перешёл в FAULT, виртуальный IP переехал на `node2`: `curl 192.168.122.250` стал отвечать `node2`.

![Переезд виртуального IP](img/task2-failover.png)
