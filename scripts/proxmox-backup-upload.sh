#!/bin/bash
#
# Proxmox backup — единый скрипт с вебхуками в Home Assistant
# ============================================================
set -uo pipefail

# ============================================================
# КОНФИГУРАЦИЯ (Изменяется под ваши нужды)
# ============================================================
VMS_TO_BACKUP=(100 103 104)
FRIGATE_CT=200
STORAGE=arhiv-backup
LOCAL_DIR=/mnt/backup/dump
REMOTE=mailru:dump
LOG=/var/log/proxmox-backup-upload.log
RCLONE_LOG=/var/log/rclone-mailru.log
LOCK=/var/run/proxmox-backup-upload.lock
CLOUD_KEEP=3

# Эта переменная будет автоматически заменена установщиком
WEBHOOK_URL="WEBHOOK_URL_PLACEHOLDER"

# ============================================================
# ЗАЩИТА ОТ ПАРАЛЛЕЛЬНОГО ЗАПУСКА
# ============================================================
exec 9>"$LOCK"
if ! flock -n 9; then
    echo "$(date '+%F %T') ERROR: another instance is running, exiting" >> "$LOG"
    exit 1
fi

# ============================================================
# ЛОГИРОВАНИЕ
# ============================================================
exec >> "$LOG" 2>&1
echo ""
echo "============================================================"
echo "=== START $(date '+%F %T') ==="
echo "============================================================"

START_TIME=$(date +%s)
ERRORS=0

mark_error() {
    echo "!!! ERROR: $*"
    ERRORS=$((ERRORS + 1))
}

notify_stage() {
    local stage="$1"
    local message="$2"
    if [ "$WEBHOOK_URL" != "WEBHOOK_URL_PLACEHOLDER" ]; then
        curl -s -X POST "$WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"stage\": \"$stage\", \"message\": \"$message\"}" \
            --max-time 5 >/dev/null 2>&1 || true
    fi
}

notify_stage "start" "🚀 Запущен цикл бэкапа VM: ${VMS_TO_BACKUP[*]}"

# ============================================================
# 1. БЭКАП VM ЧЕРЕЗ vzdump
# ============================================================
echo ""
echo "--- Stage 1: vzdump backups ---"
STAGE1_OK=0
for VMID in "${VMS_TO_BACKUP[@]}"; do
    echo ">>> Backing up VM $VMID"
    if vzdump "$VMID" \
        --storage "$STORAGE" \
        --mode snapshot \
        --compress zstd \
        --notes-template '{{guestname}}'; then
        echo ">>> VM $VMID backup OK"
        STAGE1_OK=$((STAGE1_OK + 1))
    else
        mark_error "vzdump $VMID failed"
    fi
done

if [ "$ERRORS" -eq 0 ]; then
    notify_stage "stage1" "✅ Stage 1: vzdump завершён ($STAGE1_OK/${#VMS_TO_BACKUP[@]} VM)"
else
    notify_stage "stage1_error" "⚠️ Stage 1: vzdump с ошибками ($ERRORS)"
fi

# ============================================================
# 2. БЭКАП КОНФИГА FRIGATE
# ============================================================
echo ""
echo "--- Stage 2: Frigate config backup ---"
FRIGATE_DATE=$(date +%F)
FRIGATE_OUT="$LOCAL_DIR/frigate-config-${FRIGATE_DATE}.tar.zst"
FRIGATE_TMP="$(mktemp /tmp/frigate-config.XXXXXX.tar)"

set +o pipefail
pct exec "$FRIGATE_CT" -- tar -cf - \
    --warning=no-file-changed \
    --warning=no-file-removed \
    /opt/frigate/config \
    /opt/frigate/docker-compose.yml \
    /opt/frigate/watchtower-compose.yml \
    /opt/frigate/update_frigate.sh \
    > "$FRIGATE_TMP" 2>/dev/null
TAR_EXIT=$?
set -o pipefail

if [ "$TAR_EXIT" -gt 1 ] || [ ! -s "$FRIGATE_TMP" ]; then
    mark_error "Frigate tar failed"
    rm -f "$FRIGATE_TMP"
    notify_stage "stage2_error" "❌ Stage 2: Frigate tar упал"
else
    zstd -q -f -o "$FRIGATE_OUT" "$FRIGATE_TMP"
    ZSTD_EXIT=$?
    rm -f "$FRIGATE_TMP"
    if [ "$ZSTD_EXIT" -eq 0 ] && zstd -t "$FRIGATE_OUT" >/dev/null 2>&1; then
        FRIGATE_SIZE=$(du -h "$FRIGATE_OUT" | cut -f1)
        notify_stage "stage2" "✅ Stage 2: Frigate config ($FRIGATE_SIZE)"
    else
        mark_error "Frigate zstd failed"
        notify_stage "stage2_error" "❌ Stage 2: Frigate архив повреждён"
    fi
fi

# ============================================================
# 3. БЭКАП КОНФИГУРАЦИИ ХОСТА PROXMOX
# ============================================================
echo ""
echo "--- Stage 3: Host config backup ---"
HOSTNAME_SHORT=$(hostname -s)
HOST_CFG_OUT="$LOCAL_DIR/pve-config-${HOSTNAME_SHORT}-$(date +%F).tar.zst"
HOST_CFG_TMP="$(mktemp /tmp/pve-config.XXXXXX.tar)"

HOST_BACKUP_LIST=(
    /etc/pve/ /etc/network/interfaces /etc/hosts /etc/hostname
    /etc/resolv.conf /etc/lvm/ /etc/ssh/ /etc/vzdump.conf
    /etc/sysctl.conf /var/lib/pve-cluster/config.db /root/.ssh/
)

set +o pipefail
tar --ignore-failed-read -cf "$HOST_CFG_TMP" "${HOST_BACKUP_LIST[@]}" 2>/dev/null
TAR_EXIT=$?
set -o pipefail

if [ "$TAR_EXIT" -gt 1 ] || [ ! -s "$HOST_CFG_TMP" ]; then
    mark_error "Host config tar failed"
    rm -f "$HOST_CFG_TMP"
    notify_stage "stage3_config_error" "❌ Stage 3: Host config tar упал"
else
    zstd -q -f -o "$HOST_CFG_OUT" "$HOST_CFG_TMP"
    ZSTD_EXIT=$?
    rm -f "$HOST_CFG_TMP"
    if [ "$ZSTD_EXIT" -eq 0 ] && zstd -t "$HOST_CFG_OUT" >/dev/null 2>&1; then
        notify_stage "stage3_config" "✅ Stage 3: Host config готов"
    else
        mark_error "Host config zstd failed"
        notify_stage "stage3_config_error" "❌ Stage 3: Host config повреждён"
    fi
fi

# ============================================================
# 4. ВЫГРУЗКА В ОБЛАКО
# ============================================================
echo ""
echo "--- Stage 4: rclone upload ---"
notify_stage "stage4_start" "☁️ Stage 4: начинаю выгрузку в Mail.ru"

RCLONE_UPLOAD_OK=0
if rclone copy "$LOCAL_DIR/" "$REMOTE/" \
        --include "vzdump-*.vma.zst" --include "vzdump-*.tar.zst" \
        --include "vzdump-*.vma.zst.log" --include "vzdump-*.tar.zst.log" \
        --include "vzdump-*.vma.zst.notes" --include "vzdump-*.tar.zst.notes" \
        --include "frigate-config-*" --include "pve-config-*" \
        --transfers 4 --checkers 8 --retries 10 --low-level-retries 20 \
        --log-file "$RCLONE_LOG" --log-level INFO; then
    RCLONE_UPLOAD_OK=1
    notify_stage "stage4_done" "✅ Stage 4: выгрузка в Mail.ru завершена"
else
    mark_error "rclone upload failed"
    notify_stage "stage4_error" "❌ Stage 4: выгрузка в Mail.ru упала"
fi

# ============================================================
# 5. ЛОКАЛЬНАЯ ЧИСТКА (оставляем 1)
# ============================================================
if [ "$RCLONE_UPLOAD_OK" -eq 1 ]; then
    for VMID in "${VMS_TO_BACKUP[@]}"; do
        OLD=$(ls -1t "$LOCAL_DIR"/vzdump-qemu-${VMID}-*.* 2>/dev/null | grep -E '\.(vma\.zst|tar\.zst)$' | tail -n +2)
        if [ -n "$OLD" ]; then echo "$OLD" | while read -r f; do rm -f "$f" "${f%.*}.log" "${f%.*}.notes"; done; fi
    done
    ls -1t "$LOCAL_DIR"/frigate-config-*.tar.zst 2>/dev/null | tail -n +2 | xargs -r rm -f
    ls -1t "$LOCAL_DIR"/pve-config-*.tar.zst 2>/dev/null | tail -n +2 | xargs -r rm -f
fi

# ============================================================
# 6. ЧИСТКА ОБЛАКА (оставляем CLOUD_KEEP)
# ============================================================
PREFIXES=()
for VMID in "${VMS_TO_BACKUP[@]}"; do PREFIXES+=("vzdump-qemu-${VMID}-"); done
PREFIXES+=("frigate-config-" "pve-config-")

for PREFIX in "${PREFIXES[@]}"; do
    OLD=$(rclone lsf "$REMOTE/" --files-only 2>/dev/null | grep "^${PREFIX}" | grep -E '\.(vma\.zst|tar\.zst)$' | sort -r | tail -n +$((CLOUD_KEEP + 1)))
    if [ -n "$OLD" ]; then
        echo "$OLD" | while read -r f; do
            BASE="${f%.vma.zst}"; BASE="${BASE%.tar.zst}"
            rclone deletefile "$REMOTE/$f" 2>/dev/null
            rclone deletefile "$REMOTE/${BASE}.log" 2>/dev/null
            rclone deletefile "$REMOTE/${BASE}.notes" 2>/dev/null
        done
    fi
done

# ============================================================
# 7. ИТОГ
# ============================================================
END_TIME=$(date +%s)
DURATION_HUMAN=$(printf '%dm %ds' $(((END_TIME - START_TIME) / 60)) $(((END_TIME - START_TIME) % 60)))

if [ "$ERRORS" -eq 0 ]; then
    notify_stage "done" "🏁 Бэкап успешно завершён за $DURATION_HUMAN"
    exit 0
else
    notify_stage "done" "🔴 Бэкап завершён с ошибками ($ERRORS) за $DURATION_HUMAN"
    exit 1
fi