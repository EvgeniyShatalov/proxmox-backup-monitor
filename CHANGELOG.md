# Changelog

## [1.2.3] - 2026-10-25

### Fixed
- Fixed `get_url` crash in webhook (replaced `prefer_internal` with `allow_external=False`)
- Fixed incorrect duration and last run timestamp calculation in coordinator
- Added sleep in trigger method to avoid race condition with Proxmox API

### Added
- New `Current Stage` sensor that listens to webhook events and displays the live progress (e.g., "🚀 Запущен цикл бэкапа...", "✅ Stage 1...").

## [1.2.0] - 2026-10-25
*(...)*