"""Button entities for Proxmox Backup Monitor."""
from __future__ import annotations

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_TRIGGER_URL, DOMAIN
from .coordinator import ProxmoxBackupCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities."""
    if not entry.options.get(CONF_TRIGGER_URL):
        return
    coordinator: ProxmoxBackupCoordinator = entry.runtime_data
    async_add_entities([ProxmoxTriggerBackupButton(coordinator, entry)])


class ProxmoxTriggerBackupButton(
    CoordinatorEntity[ProxmoxBackupCoordinator], ButtonEntity
):
    """Button to manually trigger the Proxmox backup script."""

    _attr_has_entity_name = True
    _attr_name = "Trigger Backup"
    _attr_icon = "mdi:play-circle-outline"
    _attr_device_class = ButtonDeviceClass.RESTART

    def __init__(
        self,
        coordinator: ProxmoxBackupCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_trigger_backup"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Proxmox Backup Monitor",
        )

    async def async_press(self) -> None:
        """Trigger backup on press."""
        await self.coordinator.async_trigger_backup()