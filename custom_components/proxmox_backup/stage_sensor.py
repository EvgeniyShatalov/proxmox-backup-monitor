"""Stage sensor for Proxmox Backup Monitor."""
from __future__ import annotations

from datetime import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up stage sensor."""
    async_add_entities([ProxmoxBackupStageSensor(hass, entry)])


class ProxmoxBackupStageSensor(SensorEntity):
    """Sensor showing the current backup stage from webhooks."""

    _attr_has_entity_name = True
    _attr_name = "Current Stage"
    _attr_icon = "mdi:progress-clock"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._attr_unique_id = f"{entry.entry_id}_stage"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Proxmox Backup Monitor",
        )
        self._state = "Не запущен"
        self._attr_extra_attributes = {}

    async def async_added_to_hass(self) -> None:
        """Subscribe to webhook events."""
        self.async_on_remove(
            self.hass.bus.async_listen(f"{DOMAIN}_stage", self._handle_stage_event)
        )

    @callback
    def _handle_stage_event(self, event) -> None:
        """Update stage when event comes."""
        stage = event.data.get("stage", "unknown")
        message = event.data.get("message", "")
        
        # Обновляем состояние и атрибуты
        self._state = message
        self._attr_extra_attributes["stage_id"] = stage
        self._attr_extra_attributes["last_update"] = datetime.now().isoformat()
        
        # Перерисовываем карточку в HA
        self.async_write_ha_state()

    @property
    def native_value(self) -> str:
        """Return the stage message."""
        return self._state