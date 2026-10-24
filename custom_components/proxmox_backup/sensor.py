"""Sensors for Proxmox Backup Monitor."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ProxmoxBackupCoordinator

@dataclass(frozen=True, kw_only=True)
class ProxmoxBackupSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]

SENSORS = (
    ProxmoxBackupSensorDescription(key="state", name="Backup State", icon="mdi:backup-restore", value_fn=lambda d: d.get("state", "unknown")),
    ProxmoxBackupSensorDescription(key="exitstatus", name="Backup Exit Status", icon="mdi:check-circle-outline", value_fn=lambda d: d.get("exitstatus", "unknown")),
    ProxmoxBackupSensorDescription(key="duration", name="Backup Duration", icon="mdi:timer-outline", native_unit_of_measurement=UnitOfTime.SECONDS, device_class=SensorDeviceClass.DURATION, state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: d.get("duration", 0)),
    ProxmoxBackupSensorDescription(key="last_run", name="Backup Last Run", icon="mdi:clock-outline", device_class=SensorDeviceClass.TIMESTAMP, value_fn=lambda d: datetime.fromtimestamp(d["last_run"]) if d.get("last_run") else None),
    ProxmoxBackupSensorDescription(key="errors", name="Backup Errors (24h)", icon="mdi:alert-circle-outline", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda d: d.get("errors", 0)),
    ProxmoxBackupSensorDescription(key="last_vmid", name="Backup Last VMID", icon="mdi:server", value_fn=lambda d: str(d.get("last_vmid") or "")),
)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities(ProxmoxBackupSensor(coordinator, entry, desc) for desc in SENSORS)

class ProxmoxBackupSensor(CoordinatorEntity[ProxmoxBackupCoordinator], SensorEntity):
    entity_description: ProxmoxBackupSensorDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator: ProxmoxBackupCoordinator, entry: ConfigEntry, description: ProxmoxBackupSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)}, name="Proxmox Backup Monitor",
            manufacturer="Proxmox VE", model="vzdump", configuration_url=f"https://{entry.data.get('host', '')}:8006",
        )

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data or {})