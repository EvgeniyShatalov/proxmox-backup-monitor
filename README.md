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
- **Automated Setup:** Generate a one-line `curl` command to automatically install the backup script, systemd timer, and HTTP trigger on your Proxmox host.

### 📦 Installation
1. Open **HACS → Integrations**.
2. Click **⋮ → Custom repositories**.
3. Add URL: `https://github.com/EvgeniyShatalov/proxmox-backup-monitor` (Category: Integration).
4. Search for **Proxmox Backup Monitor**, download, and restart Home Assistant.

### 🔗 Proxmox Host Setup (Automatic)
The backup script and webhook trigger are hosted in the `scripts/` folder of this repository.
1. After adding the integration, go to the device page and find the sensor `Host Setup Command`.
2. Click on its value to **copy** the generated `curl | bash` command.
3. Paste it into your Proxmox terminal and press Enter. This will:
   - Download `proxmox-backup-upload.sh` to `/usr/local/bin/`.
   - Configure a `systemd` timer to run it every Monday at 03:00.
   - Install the HTTP trigger server for manual starts from HA.
4. Go to the integration's **Configure** (Options) and set the **Trigger URL** (e.g., `http://192.168.1.100:8099`) and the **Trigger Token** (already generated).

---

<a name="russian"></a>
## 🇷🇺 Русский

Кастомная интеграция для Home Assistant, которая мониторит задачи резервного копирования Proxmox VE (`vzdump`), отслеживает этапы в реальном времени и позволяет запускать бэкапы вручную.

### ✨ Возможности
- **Этапы в реальном времени:** Сенсор `Current Stage` показывает, что происходит прямо сейчас (например, «🚀 Запущен бэкап», «✅ Stage 1 завершён», «☁️ Выгрузка в облако»).
- **Сенсоры:** Состояние, статус завершения, длительность, время последнего запуска, количество ошибок и ID последней VM.
- **Ручной запуск:** Кнопка **Trigger Backup** и сервис `proxmox_backup.trigger_backup`.
- **Полная автоматизация:** Интеграция генерирует одну команду, которая сама скачивает скрипт бэкапа, настраивает systemd таймер и устанавливает вебхук-сервер на Proxmox.

### 📦 Установка
1. Откройте **HACS → Интеграции**.
2. Нажмите **⋮ → Пользовательские репозитории** (Custom repositories).
3. Вставьте ссылку: `https://github.com/EvgeniyShatalov/proxmox-backup-monitor` (Категория: Интеграция).
4. Найдите **Proxmox Backup Monitor**, скачайте и перезагрузите Home Assistant.

### 🐧 Настройка хоста Proxmox (Автоматически)
**Где взять скрипт?** Он уже лежит в папке `scripts/` этого репозитория. Вам не нужно создавать его вручную.
1. После добавления интеграции найдите сенсор **`Host Setup Command`** (Команда настройки хоста).
2. **Нажмите на его значение**, чтобы скопировать готовую команду `curl`.
3. Вставьте эту команду в терминал Proxmox и нажмите Enter. Скрипт автоматически:
   - Скачает `proxmox-backup-upload.sh` в `/usr/local/bin/`.
   - Настроит запуск каждый понедельник в 03:00 через `systemd`.
   - Установит HTTP-триггер для кнопки «Trigger Backup».
4. Зайдите в **Настроить** (Configure) интеграции и укажите **Trigger URL** (например, `http://192.168.1.100:8099`). Токен подставится сам.