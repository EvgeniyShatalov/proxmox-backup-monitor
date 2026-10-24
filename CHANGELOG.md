# Changelog

## [1.1.0] - 2026-10-25

### Added
- **Button entity** "Trigger Backup" to start the backup script manually
- **Service** `proxmox_backup.trigger_backup` for automations
- Optional HTTP trigger configuration in the options flow
- New options: `trigger_url`, `trigger_token`

## [1.0.0] - 2026-10-25

### Added
- Initial release
- Sensors: state, exit status, duration, last run, error count, last VMID
- Config flow with API token authentication
- Options flow for polling interval
- Russian and English translations
- HACS compatibility