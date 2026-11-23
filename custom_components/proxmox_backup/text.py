"""Text entities for Proxmox Backup Monitor."""
from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_TRIGGER_TOKEN
from .coordinator import ProxmoxBackupCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up text entities."""
    coordinator: ProxmoxBackupCoordinator = entry.runtime_data
    async_add_entities([ProxmoxSetupText(coordinator, entry)])


class ProxmoxSetupText(TextEntity):
    """Текстовое поле с командой установки."""

    _attr_has_entity_name = True
    _attr_name = "Host Setup Command"
    _attr_icon = "mdi:console"
    _attr_mode = TextMode.PASSWORD  # Скрывает текст точками для безопасности
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: ProxmoxBackupCoordinator, entry: ConfigEntry) -> None:
        self.coordinator = coordinator
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_setup_command"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Proxmox Backup Monitor",
        )

    @property
    def native_value(self) -> str:
        """Генерирует команду."""
        url = getattr(self.coordinator, "webhook_url", "URL_NOT_READY")
        token = self.entry.options.get(CONF_TRIGGER_TOKEN, "TOKEN_NOT_READY")
        
        # Добавляем sed 's/\r$//' прямо в команду! Это спасет от ошибок Windows.
        return (
            f'curl -sL https://raw.githubusercontent.com/EvgeniyShatalov/proxmox-backup-monitor/main/scripts/install-proxmox-backup.sh '
            f'| sed \'s/\\r$//\' | bash -s -- "{url}" "{token}"'
        )

    async def async_set_value(self, value: str) -> None:
        """Запрещаем менять значение вручную."""
        pass