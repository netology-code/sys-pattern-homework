#!/usr/bin/env bash
# VPN Bot Lite — установка и обслуживание.
#   ./vpn.sh install [BOT_TOKEN] [ADMIN_ID]   установка (Docker, настройки ядра, автообновление)
#   ./vpn.sh update                           обновить бота из git и пересобрать
#   ./vpn.sh https [ПОРТ]                     подписки по https (бесплатный адрес IP.nip.io + Let's Encrypt; ПОРТ — публичный, например текущий 2097)
#   ./vpn.sh https-cert CERT KEY              подписки по https с готовым сертификатом (например, от старого vpnbot)
#   ./vpn.sh import-awg wg0|wg1 [--apply]     перенести AmneziaWG из старого vpnbot (без --apply — только проверка)
#   ./vpn.sh doctor                           вся диагностика одним выводом (без секретов) — пришлите его целиком
#   ./vpn.sh restart | stop | status | logs
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
UNIT=vpnbot-lite-update

log() { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31mОшибка:\033[0m %s\n' "$*" >&2; exit 1; }
need_root() { [ "$(id -u)" -eq 0 ] || die "запустите от root (sudo $0 $*)"; }
env_get() { grep -E "^$1=" .env 2>/dev/null | tail -1 | cut -d= -f2- || true; }
env_port() { local v; v="$(env_get "$1")"; echo "${v:-$2}"; }  # env_port VAR default
env_del() { sed -i "/^$1=/d" .env; }
env_set() {
    if grep -qE "^$1=" .env; then sed -i "s|^$1=.*|$1=$2|" .env; else echo "$1=$2" >> .env; fi
}
ask() {  # ask VAR "prompt" — читает из терминала, даже если скрипт запущен через pipe
    local value=""
    while [ -z "$value" ]; do read -r -p "$2: " value < /dev/tty; done
    env_set "$1" "$value"
}

install_docker() {
    if command -v docker >/dev/null && docker compose version >/dev/null 2>&1; then return; fi
    log "Устанавливаю Docker"
    curl -fsSL https://get.docker.com | sh
    systemctl enable --now docker
}

tune_kernel() {
    log "Включаю BBR, форвардинг (AmneziaWG) и увеличиваю UDP-буферы (Hysteria2)"
    cat > /etc/sysctl.d/99-vpnbot-lite.conf <<'EOF'
net.ipv4.ip_forward=1
net.core.default_qdisc=fq
net.ipv4.tcp_congestion_control=bbr
net.core.rmem_max=16777216
net.core.wmem_max=16777216
net.ipv4.tcp_fastopen=3
EOF
    sysctl --system >/dev/null || true
}

open_firewall() {
    command -v ufw >/dev/null && ufw status | grep -q "Status: active" || return 0
    log "Открываю порты в ufw"
    ufw allow "$(env_port XRAY_PORT 443)/tcp"
    [ "$(env_port XHTTP_PORT 8443)" = 0 ] || ufw allow "$(env_port XHTTP_PORT 8443)/tcp"
    ufw allow "$(env_port HY2_PORT 443)/udp"
    ufw allow "$(env_port AWG_PORT 51820)/udp"
    ufw allow "$(env_port SUB_PORT 2096)/tcp"
    [ "$(env_port MTPROTO_PORT 8444)" = 0 ] || ufw allow "$(env_port MTPROTO_PORT 8444)/tcp"
}

version_url() {  # raw-ссылка на VERSION в GitHub, чтобы бот видел новые версии
    local remote branch prefix slug
    remote="$(git remote get-url origin 2>/dev/null || true)"
    [[ "$remote" == *github.com* ]] || return 0
    branch="$(git rev-parse --abbrev-ref HEAD)"
    prefix="$(git rev-parse --show-prefix)"
    slug="$(echo "$remote" | sed -E 's#^(git@github.com:|https://github.com/)##; s#\.git$##')"
    echo "https://raw.githubusercontent.com/$slug/$branch/${prefix}VERSION"
}

install_update_unit() {
    log "Включаю обновление бота по кнопке в Telegram"
    cat > /etc/systemd/system/$UNIT.path <<EOF
[Unit]
Description=VPN Bot Lite: update requested from Telegram

[Path]
PathExists=$DIR/data/update.request

[Install]
WantedBy=multi-user.target
EOF
    cat > /etc/systemd/system/$UNIT.service <<EOF
[Unit]
Description=VPN Bot Lite: update

[Service]
Type=oneshot
ExecStart=$DIR/vpn.sh update
EOF
    systemctl daemon-reload
    systemctl enable --now $UNIT.path
}

check_ports() {
    local port
    for port in "$(env_port XRAY_PORT 443)" "$(env_port XHTTP_PORT 8443)" "$(env_port SUB_PORT 2096)" \
                "$(env_port MTPROTO_PORT 8444)"; do
        [ "$port" = 0 ] && continue
        if ss -ltnH "sport = :$port" 2>/dev/null | grep -q . && ! docker ps --format '{{.Names}}' | grep -q '^vpnbot-lite$'; then
            echo "⚠️  Порт $port/tcp уже занят другим процессом:"; ss -ltnpH "sport = :$port" || true
            echo "   Освободите его или поменяйте порт в .env"
        fi
    done
}

cmd_install() {
    need_root "$@"
    [ -f .env ] || cp .env.example .env
    [ -n "$(env_get AWG_PORT)" ] || env_set AWG_PORT 51820  # .env от версии без AmneziaWG
    [ -n "${1:-}" ] && env_set BOT_TOKEN "$1"
    [ -n "${2:-}" ] && env_set ADMIN_IDS "$2"
    [ -n "$(env_get BOT_TOKEN)" ] || ask BOT_TOKEN "Токен бота от @BotFather"
    [ -n "$(env_get ADMIN_IDS)" ] || ask ADMIN_IDS "Ваш Telegram ID (узнать: @userinfobot)"
    [ -n "$(env_get BOT_VERSION_URL)" ] || env_set BOT_VERSION_URL "$(version_url)"
    mkdir -p data
    install_docker
    tune_kernel
    open_firewall
    check_ports
    install_update_unit
    log "Собираю и запускаю"
    docker compose up -d --build
    log "Готово! Откройте бота в Telegram и нажмите /start"
}

cmd_https() {
    need_root "$@"
    local ip domain port url old_url
    old_url="$(env_get SUB_URL)"
    ip="$(env_get SERVER_HOST)"
    [[ "$ip" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || ip="$(curl -4 -fsS --max-time 10 https://api.ipify.org)"
    domain="$(echo "$ip" | tr . -).nip.io"  # бесплатное имя, которое указывает на этот IP
    port="${1:-$(env_port SUB_HTTPS_PORT 2443)}"
    url="https://$domain"
    [ "$port" = 443 ] || url="$url:$port"
    if ss -ltnH "sport = :80" 2>/dev/null | grep -q . && ! docker ps --format '{{.Names}}' | grep -q '^vpnbot-lite-caddy$'; then
        echo "⚠️  Порт 80 занят — Let's Encrypt проверяет адрес через него, сертификат не выпустится:"
        ss -ltnpH "sport = :80" || true
        die "освободите порт 80 (например, остановите старый vpnbot: cd /root/vpnbot && make d) и повторите"
    fi
    # Caddy takes the public port; the bot's subscription server moves behind it (plain http on localhost).
    # Keeping the public port keeps every subscription link the apps already have.
    if [ "$port" = "$(env_port SUB_PORT 2096)" ]; then
        if [ "$port" = 2096 ]; then env_set SUB_PORT 2095; else env_set SUB_PORT 2096; fi
    fi
    env_set SUB_LISTEN 127.0.0.1
    env_del SUB_CERT
    env_del SUB_KEY
    env_del SUB_CERT_DIR
    env_set SUB_DOMAIN "$domain"
    env_set SUB_HTTPS_PORT "$port"
    env_set SUB_URL "$url"
    env_set COMPOSE_PROFILES https
    if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
        ufw allow 80/tcp
        ufw allow "$port/tcp"
    fi
    log "Включаю HTTPS для подписок: $url"
    docker compose up -d --force-recreate
    log "Получаю сертификат (до 2 минут)…"
    for _ in $(seq 24); do
        if curl -fsS --max-time 5 "$url/health" >/dev/null 2>&1; then
            log "Готово! Подписки открываются по $url/sub/… (сертификат Let's Encrypt, продлевается сам)"
            if [ "$url" != "$old_url" ]; then log "Адрес подписок изменился — новые ссылки в боте: Пользователи → Ключи и QR"; fi
            return
        fi
        sleep 5
    done
    echo "Сертификат пока не получен. Проверьте, открыт ли порт 80 у хостера, и посмотрите логи:"
    echo "  docker compose logs caddy --tail 30"
}

cmd_https_cert() {
    need_root "$@"
    local cert="${1:-}" key="${2:-}" domain url port
    [ -f "$cert" ] && [ -f "$key" ] || die "укажите файлы сертификата и ключа: ./vpn.sh https-cert CERT KEY"
    [ "$(dirname "$cert")" = "$(dirname "$key")" ] || die "сертификат и ключ должны лежать в одной папке"
    domain="$(openssl x509 -in "$cert" -noout -ext subjectAltName 2>/dev/null | grep -o 'DNS:[^,]*' | head -1 | cut -d: -f2)"
    [ -n "$domain" ] || die "в сертификате нет доменного имени"
    openssl x509 -in "$cert" -noout -checkend 0 >/dev/null || die "сертификат просрочен"
    port="$(env_port SUB_PORT 2096)"
    url="https://$domain"
    [ "$port" = 443 ] || url="$url:$port"
    env_set SUB_CERT_DIR "$(cd "$(dirname "$cert")" && pwd)"
    env_set SUB_CERT "/certs/$(basename "$cert")"
    env_set SUB_KEY "/certs/$(basename "$key")"
    env_set SUB_URL "$url"
    log "Подписки будут по $url (сертификат $(openssl x509 -in "$cert" -noout -enddate | cut -d= -f2))"
    docker compose up -d --force-recreate vpnbot
    for _ in $(seq 12); do
        if curl -fsS --max-time 5 --resolve "$domain:$port:127.0.0.1" "$url/health" >/dev/null 2>&1; then
            log "Готово! Новые ссылки — в боте: Пользователи → пользователь → Ключи и QR"
            return
        fi
        sleep 5
    done
    echo "Не отвечает по https. Логи: ./vpn.sh logs"
}

cmd_import_awg() {
    need_root "$@"
    local src="${1:-}" mode="${2:-}" old=/root/vpnbot/config conf clients out port subnet
    case "$src" in
        wg0) conf="$old/wg0.conf"; clients="$old/clients.json" ;;
        wg1) conf="$old/wg1.conf"; clients="$old/clients1.json" ;;
        *) die "укажите, что переносить: ./vpn.sh import-awg wg0 (порт 51820) или wg1 (порт 51821)" ;;
    esac
    [ -s "$conf" ] || die "не найден $conf"
    mkdir -p data/import
    cp "$conf" data/import/server.conf
    if [ -s "$clients" ]; then cp "$clients" data/import/clients.json; else rm -f data/import/clients.json; fi
    trap 'rm -rf "$DIR/data/import"' EXIT  # keys must not stay lying around

    log "Читаю $conf"
    out="$(docker compose run --rm --no-deps -T --name vpnbot-lite-import vpnbot python -m app.import_awg \
        /data/import/server.conf /data/import/clients.json)" || { echo "$out"; die "не удалось прочитать конфиг"; }
    echo "$out" | grep -v '^ENV '
    port="$(echo "$out" | sed -n 's/^ENV AWG_PORT=//p')"
    subnet="$(echo "$out" | sed -n 's/^ENV AWG_SUBNET=//p')"
    if [ "$mode" != "--apply" ]; then
        echo
        echo "Это проверка, ничего не изменено. Чтобы перенести: ./vpn.sh import-awg $src --apply"
        return
    fi

    if ss -lunpH "sport = :$port" 2>/dev/null | grep -v amneziawg | grep -q .; then
        ss -lunpH "sport = :$port"
        die "порт $port/udp занят (старый бот ещё работает?) — остановите его: cd /root/vpnbot && make d"
    fi
    log "Переношу (бот перезапустится)"
    env_set AWG_PORT "$port"
    env_set AWG_SUBNET "$subnet"
    docker compose stop vpnbot
    docker compose run --rm --no-deps -T --name vpnbot-lite-import vpnbot python -m app.import_awg \
        /data/import/server.conf /data/import/clients.json --apply | grep -v '^ENV '
    docker compose up -d vpnbot
    if command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then ufw allow "$port/udp"; fi
    log "Готово: AmneziaWG на порту $port/udp. Роутеры и телефоны со старыми конфигами переподключатся сами."
}

cmd_doctor() {
    # everything usually asked for when something breaks; secrets are masked
    local mask='s/(secret=|PrivateKey *= *|PresharedKey *= *|password[=:] *|BOT_TOKEN=)[^ &"]+/\1<скрыто>/Ig'
    section() { printf '\n===== %s =====\n' "$1"; }
    (
        set +e +o pipefail  # show everything even when some checks fail
        section "Версия"
        echo "бот $(cat VERSION), git $(git log -1 --format='%h %cd' --date=short 2>/dev/null)"
        section "Контейнеры"
        docker compose ps --format '{{.Name}}: {{.Status}}' 2>&1
        section "Настройки (.env без токена и ID)"
        grep -vE '^(BOT_TOKEN|ADMIN_IDS)=' .env
        section "Порты"
        ss -ltnupH 2>/dev/null | grep -E "xray|hysteria|amneziawg|telemt|caddy|python" | awk '{print $1, $5, $7}'
        section "Ядра"
        docker exec vpnbot-lite sh -c 'for b in xray hysteria telemt amneziawg-go; do
            p=/data/bin/$b; [ -x "$p" ] || p=/opt/bin/$b
            printf "%s: " "$b"; case $b in xray) $p version | head -1;; hysteria) $p version | grep -i "^version";;
            *) $p --version 2>&1 | head -1;; esac; done' 2>&1
        section "AmneziaWG"
        docker exec vpnbot-lite sh -c 'now=$(date +%s); /opt/bin/awg show awg0 latest-handshakes 2>&1 |
            awk -v now="$now" "NF == 2 && \$2 ~ /^[0-9]+\$/ {n++; if (\$2 > 0 && now - \$2 < 180) a++} END {print n+0, \"клиентов, на связи за 3 минуты:\", a+0}"' 2>&1
        echo "ip_forward=$(cat /proc/sys/net/ipv4/ip_forward), congestion=$(cat /proc/sys/net/ipv4/tcp_congestion_control)"
        section "Сертификат подписки"
        if [ -n "$(env_get SUB_DOMAIN)" ]; then
            echo | openssl s_client -connect "127.0.0.1:$(env_port SUB_HTTPS_PORT 2443)" \
                -servername "$(env_get SUB_DOMAIN)" 2>/dev/null | openssl x509 -noout -issuer -enddate 2>&1
        else
            echo "https для подписок не включён (./vpn.sh https)"
        fi
        section "Система"
        uptime
        free -h | head -2
        df -h / | tail -1
        timedatectl 2>/dev/null | grep -E "Universal time|synchronized"
        section "Лог бота (последние 30 строк)"
        docker compose logs --tail 30 --no-log-prefix vpnbot 2>&1
        for f in data/logs/*.log; do
            [ -f "$f" ] || continue
            section "Лог $(basename "$f" .log) (последние 20 строк)"
            tail -n 20 "$f"
        done
    ) 2>&1 | sed -E "$mask"
}

image_ref() {  # ghcr.io/<owner>/vpnbot-lite:<branch> — built by GitHub Actions from this repository
    local remote branch owner
    remote="$(git remote get-url origin 2>/dev/null || true)"
    [[ "$remote" == *github.com* ]] || return 0
    owner="$(echo "$remote" | sed -E 's#^(git@github.com:|https://github.com/)##; s#/.*##' | tr '[:upper:]' '[:lower:]')"
    branch="$(git rev-parse --abbrev-ref HEAD | tr '/' '-')"
    echo "ghcr.io/$owner/vpnbot-lite:$branch"
}

get_image() {
    local image ver
    image="$(env_get VPNBOT_IMAGE)"
    if [ -n "$image" ] && [ "$image" != "vpnbot-lite:local" ] && docker compose pull -q vpnbot 2>/dev/null; then
        ver="$(docker run --rm --entrypoint cat "$image" /srv/VERSION 2>/dev/null)"
        if [ "$ver" = "$(cat VERSION)" ]; then
            log "Скачан готовый образ $ver"
            return
        fi
        log "Готовый образ ещё не обновился на GitHub (там ${ver:-?}, нужна $(cat VERSION)) — собираю сам"
    else
        log "Готового образа нет — собираю на сервере (10–20 минут)"
    fi
    docker compose build --pull
}

cmd_update() {
    rm -f data/update.request
    if [ -d .git ] || git rev-parse --git-dir >/dev/null 2>&1; then
        log "Скачиваю новую версию"
        git pull --ff-only
    fi
    if [ "$(id -u)" -eq 0 ]; then  # новые версии могут требовать новых портов/настроек ядра
        [ -n "$(env_get AWG_PORT)" ] || env_set AWG_PORT 51820
        tune_kernel
        open_firewall
    fi
    [ -n "$(env_get VPNBOT_IMAGE)" ] || env_set VPNBOT_IMAGE "$(image_ref)"
    get_image
    docker compose up -d
    docker image prune -f >/dev/null || true
    log "Обновлено до $(cat VERSION)"
}

case "${1:-}" in
    install) shift; cmd_install "$@" ;;
    update) cmd_update ;;
    https) shift; cmd_https "$@" ;;
    https-cert) shift; cmd_https_cert "$@" ;;
    doctor) cmd_doctor ;;
    import-awg) shift; cmd_import_awg "$@" ;;
    restart) docker compose up -d --force-recreate ;;  # пересоздать: подхватывает изменения .env
    stop) docker compose down ;;
    status) docker compose ps ;;
    logs) docker compose logs -f --tail=200 ;;
    *) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;;
esac
