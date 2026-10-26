# Proxmox Backup Monitor for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/EvgeniyShatalov/proxmox-backup-monitor.svg)](https://GitHub.com/EvgeniyShatalov/proxmox-backup-monitor/releases/)
[![License](https://img.shields.io/github/license/EvgeniyShatalov/proxmox-backup-monitor.svg)](LICENSE)

[English](#english) | [Русский](#russian)

---

<a name="english"></a>
## 🇬🇧 English

Custom integration for Home Assistant to monitor Proxmox VE backup tasks (`vzdump`), with real-time progress tracking and manual trigger support.

### ✨ Features
- **Real-time Stage Tracking:** See exactly what is happening (e.g., "🚀 Backup started", "✅ Stage 1 completed", "☁️ Uploading to cloud").
- **Sensors:** State, exit status, duration, last run, error count, and last VMID.
- **Manual Trigger:** Start the backup script directly from Home Assistant via a button or service.
- **API Token Auth:** Secure connection to Proxmox without storing your root password.
- **Automated Webhook Setup:** Generate a one-line `curl` command to automatically install the HTTP trigger on your Proxmox host.

### 📋 Prerequisites
- Home Assistant **2024.1.0** or newer.
- Proxmox VE **7.x / 8.x / 9.x**.
- Bash backup script located at `/usr/local/bin/proxmox-backup-upload.sh` on your Proxmox host.

### 📦 Installation
1. Open **HACS → Integrations**.
2. Click **⋮ → Custom repositories**.
3. Add URL: `https://github.com/EvgeniyShatalov/proxmox-backup-monitor` (Category: Integration).
4. Search for **Proxmox Backup Monitor**, download, and restart Home Assistant.

### ⚙️ Configuration
1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Proxmox Backup Monitor**.
3. Enter your Proxmox Host (e.g., `192.168.1.100`), User (`root@pam`), API Token ID, and Token Secret.

### 🔗 Host Setup (Webhook)
To enable the "Trigger Backup" button and real-time stages, you need to install a small HTTP server on Proxmox:
1. After adding the integration, find the sensor `sensor.proxmox_backup_monitor_host_setup_command`.
2. Click on its value to **copy** the generated `curl | bash` command.
3. Paste it into your Proxmox terminal and press Enter.
4. Go to the integration's **Configure** (Options) and set the **Trigger URL** (e.g., `http://192.168.1.100:8099`) and the **Trigger Token** (generated automatically).

### 🔔 Automations
Listen to the `proxmox_backup_stage` event to send notifications to Telegram, VK, or Mobile App:

```yaml
alias: Proxmox Backup Notifications
trigger:
  - platform: event
    event_type: proxmox_backup_stage
action:
  - service: notify.mobile_app_phone
    data:
      message: "{{ trigger.event.data.message }}"
```

---

<a name="russian"></a>
## 🇷🇺 Русский

Кастомная интеграция для Home Assistant, которая мониторит задачи резервного копирования Proxmox VE (`vzdump`), отслеживает этапы в реальном времени и позволяет запускать бэкапы вручную.

### ✨ Возможности
- **Этапы в реальном времени:** Сенсор `Current Stage` показывает, что происходит прямо сейчас (например, «🚀 Запущен бэкап», «✅ Stage 1 завершён», «☁️ Выгрузка в облако»).
- **Сенсоры:** Состояние, статус завершения, длительность, время последнего запуска, количество ошибок и ID последней VM.
- **Ручной запуск:** Кнопка **Trigger Backup** и сервис `proxmox_backup.trigger_backup` для запуска скрипта прямо из HA.
- **Безопасность:** Авторизация через API-токен Proxmox.
- **Автоматическая настройка хоста:** Интеграция генерирует готовую команду `curl`, которая в один клик устанавливает вебхук-сервер на ваш Proxmox.

### 📋 Требования
- Home Assistant **2024.1.0** или новее.
- Proxmox VE **7.x / 8.x / 9.x**.
- Bash-скрипт бэкапа, расположенный по пути `/usr/local/bin/proxmox-backup-upload.sh` на хосте Proxmox.

### 📦 Установка
1. Откройте **HACS → Интеграции**.
2. Нажмите **⋮ → Пользовательские репозитории** (Custom repositories).
3. Вставьте ссылку: `https://github.com/EvgeniyShatalov/proxmox-backup-monitor` (Категория: Интеграция).
4. Найдите **Proxmox Backup Monitor**, скачайте и перезагрузите Home Assistant.

### ⚙️ Настройка
1. Перейдите в **Настройки → Устройства и службы → Добавить интеграцию**.
2. Найдите **Proxmox Backup Monitor**.
3. Введите IP-адрес Proxmox, пользователя (`root@pam`), ID API-токена и секрет токена.
*(Создать токен можно в Proxmox: Datacenter → Permissions → API Tokens).*

### 🔗 Настройка вебхука (триггера)
Чтобы кнопка **Trigger Backup** работала, а этапы прилетали в HA мгновенно, нужно установить HTTP-триггер на Proxmox:
1. После добавления интеграции найдите сенсор `Host Setup Command` (Команда настройки хоста).
2. **Нажмите на его значение**, чтобы скопировать готовую команду `curl`.
3. Вставьте эту команду в терминал Proxmox и нажмите Enter.
4. Зайдите в **Настроить** (Configure) интеграции и укажите **Trigger URL** (например, `http://192.168.1.100:8099`). Токен там уже будет подставлен автоматически.

### 🔔 Уведомления
Интеграция генерирует событие `proxmox_backup_stage` при каждом этапе. Вы можете использовать его в автоматизациях для отправки уведомлений в Telegram, VK или приложение HA:

```yaml
alias: Уведомления о бэкапах Proxmox
trigger:
  - platform: event
    event_type: proxmox_backup_stage
action:
  - service: notify.mobile_app_phone
    data:
      message: "{{ trigger.event.data.message }}"
```
