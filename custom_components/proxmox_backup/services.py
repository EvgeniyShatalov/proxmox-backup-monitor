"""Services for Proxmox Backup Monitor."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.exceptions import ServiceValidationError

from .const import DOMAIN
from .coordinator import ProxmoxBackupCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_TRIGGER_BACKUP = "trigger_backup"
ATTR_ENTRY_ID = "entry_id"

SERVICE_TRIGGER_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTRY_ID): cv.string,
})


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register services."""

    async def _handle_trigger(call: ServiceCall) -> None:
        entry_id = call.data.get(ATTR_ENTRY_ID)
        entries = hass.config_entries.async_entries(DOMAIN)
        if entry_id:
            entries = [e for e in entries if e.entry_id == entry_id]
        if not entries:
            raise ServiceValidationError(
                "No matching Proxmox Backup config entry found"
            )

        for entry in entries:
            coordinator: ProxmoxBackupCoordinator = entry.runtime_data
            try:
                result = await coordinator.async_trigger_backup()
                _LOGGER.info("Backup trigger result: %s", result)
            except Exception as err:  # noqa: BLE001
                _LOGGER.error("Failed to trigger backup: %s", err)
                raise ServiceValidationError(str(err)) from err

    if not hass.services.has_service(DOMAIN, SERVICE_TRIGGER_BACKUP):
        hass.services.async_register(
            DOMAIN,
            SERVICE_TRIGGER_BACKUP,
            _handle_trigger,
            schema=SERVICE_TRIGGER_SCHEMA,
        )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unregister services."""
    if hass.services.has_service(DOMAIN, SERVICE_TRIGGER_BACKUP):
        hass.services.async_remove(DOMAIN, SERVICE_TRIGGER_BACKUP)