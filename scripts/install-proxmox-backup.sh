#!/bin/bash
set -e

WEBHOOK_URL="$1"
TRIGGER_TOKEN="$2"

if [ -z "$WEBHOOK_URL" ] || [ -z "$TRIGGER_TOKEN" ]; then
    echo "Ошибка: не переданы URL вебхука или токен."
    exit 1
fi

echo ">>> Установка зависимостей (если нет)..."
apt-get update -qq && apt-get install -y -qq curl zstd rclone > /dev/null

echo ">>> Скачивание скрипта бэкапа..."
curl -sL https://raw.githubusercontent.com/EvgeniyShatalov/proxmox-backup-monitor/main/scripts/proxmox-backup-upload.sh -o /usr/local/bin/proxmox-backup-upload.sh
chmod +x /usr/local/bin/proxmox-backup-upload.sh

echo ">>> Внедрение URL вебхука в скрипт..."
sed -i "s|WEBHOOK_URL_PLACEHOLDER|$WEBHOOK_URL|g" /usr/local/bin/proxmox-backup-upload.sh

echo ">>> Создание службы и таймера systemd (запуск по понедельникам в 03:00)..."
cat > /etc/systemd/system/proxmox-backup-upload.service <<'EOF'
[Unit]
Description=Proxmox VM backup + upload
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=root
ExecStart=/usr/local/bin/proxmox-backup-upload.sh
TimeoutStartSec=6h
EOF

cat > /etc/systemd/system/proxmox-backup-upload.timer <<'EOF'
[Unit]
Description=Weekly Proxmox backup

[Timer]
OnCalendar=Mon *-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now proxmox-backup-upload.timer

echo ">>> Настройка HTTP-триггера для HA..."
curl -sL https://raw.githubusercontent.com/EvgeniyShatalov/proxmox-backup-monitor/main/scripts/install-trigger.sh | bash -s -- "$WEBHOOK_URL" "$TRIGGER_TOKEN"

echo ">>> ГОТОВО! Скрипт бэкапа установлен и будет запускаться каждый понедельник в 03:00."