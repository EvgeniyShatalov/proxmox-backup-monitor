# Proxmox Backup Monitor for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/EvgeniyShatalov/proxmox-backup-monitor.svg)](https://GitHub.com/EvgeniyShatalov/proxmox-backup-monitor/releases/)
[![License](https://img.shields.io/github/license/EvgeniyShatalov/proxmox-backup-monitor.svg)](LICENSE)

Custom integration for Home Assistant to monitor Proxmox VE backup tasks (`vzdump`) via the Proxmox API.

## ✨ Features
- 📊 **Sensors** for backup state, duration, last run, error count, and last VM ID
- ⏱️ **Configurable polling interval** (default: 15 min)
- 🔐 **API token** authentication
- 🌍 **Multi-language** (English, Russian)

## 🔑 Create an API Token in Proxmox VE
1. Log in to Proxmox VE web UI
2. **Datacenter → Permissions → API Tokens → Add**
3. Select user (e.g. `root@pam`), Token ID (e.g. `ha-backup`)
4. Uncheck "Privilege Separation"
5. Copy the secret

## 📦 Installation
1. HACS → Integrations → Custom repositories
2. Add URL: `https://github.com/EvgeniyShatalov/proxmox-backup-monitor`
3. Category: Integration
4. Download and restart Home Assistant

## ⚙️ Configuration
1. Settings → Devices & Services → Add Integration
2. Search for **Proxmox Backup Monitor**
3. Enter Host, User, Token ID, and Secret.