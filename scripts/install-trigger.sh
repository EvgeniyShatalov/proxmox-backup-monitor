#!/bin/bash
# Скрипт автоматической установки HTTP-триггера для Home Assistant
set -e

WEBHOOK_URL="$1"
TOKEN="$2"

if [ -z "$WEBHOOK_URL" ] || [ -z "$TOKEN" ]; then
    echo "Ошибка: не переданы URL вебхука или токен."
    exit 1
fi

echo ">>> Создание Python-сервера..."
cat > /usr/local/bin/pve-backup-trigger.py <<'PYEOF'
#!/usr/bin/env python3
import hmac, os, subprocess, sys
from http.server import BaseHTTPRequestHandler, HTTPServer

TOKEN = os.environ.get("BACKUP_TRIGGER_TOKEN", "")
PORT = int(os.environ.get("BACKUP_TRIGGER_PORT", "8099"))
UNIT = "proxmox-backup-upload.service"

class Handler(BaseHTTPRequestHandler):
    def _check_auth(self) -> bool:
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "): return False
        return hmac.compare_digest(auth[7:].encode("utf-8"), TOKEN.encode("utf-8"))

    def _respond(self, code: int, body: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body.encode())

    def do_POST(self):
        if not self._check_auth(): return self._respond(401, "unauthorized\n")
        if self.path == "/trigger":
            active = subprocess.run(["systemctl", "is-active", "--quiet", UNIT], capture_output=True)
            if active.returncode == 0: return self._respond(409, "already running\n")
            subprocess.Popen(["systemctl", "start", "--no-block", UNIT])
            self._respond(202, "triggered\n")
        else: self._respond(404, "not found\n")

    def do_GET(self):
        if not self._check_auth(): return self._respond(401, "unauthorized\n")
        if self.path == "/status":
            res = subprocess.run(["systemctl", "is-active", UNIT], capture_output=True, text=True)
            self._respond(200, (res.stdout.strip() or "unknown") + "\n")
        else: self._respond(404, "not found\n")

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
PYEOF

chmod +x /usr/local/bin/pve-backup-trigger.py

echo ">>> Создание файла с токеном..."
cat > /etc/pve-backup-trigger.env <<EOF
BACKUP_TRIGGER_TOKEN=$TOKEN
BACKUP_TRIGGER_PORT=8099
EOF
chmod 600 /etc/pve-backup-trigger.env

echo ">>> Создание systemd сервиса..."
cat > /etc/systemd/system/pve-backup-trigger.service <<'EOF'
[Unit]
Description=Proxmox Backup HTTP trigger
After=network-online.target

[Service]
Type=simple
EnvironmentFile=/etc/pve-backup-trigger.env
ExecStart=/usr/local/bin/pve-backup-trigger.py
Restart=on-failure
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now pve-backup-trigger.service

echo ">>> Готово! Триггер установлен и запущен на порту 8099."
echo ">>> Не забудьте обновить скрипт бэкапа, подставив в него вебхук: $WEBHOOK_URL"