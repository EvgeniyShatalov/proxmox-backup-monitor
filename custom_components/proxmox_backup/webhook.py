"""Webhook receiver for Proxmox Backup stages."""
from __future__ import annotations

import logging

from aiohttp.web_request import Request
from homeassistant.components.webhook import async_register, async_unregister
from homeassistant.core import HomeAssistant
from homeassistant.helpers.network import get_url

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_webhook(hass: HomeAssistant, entry) -> str:
    """Register a webhook and return its full URL."""
    webhook_id = entry.entry_id

    async def handle_webhook(
        hass: HomeAssistant, webhook_id: str, request: Request
    ) -> None:
        """Handle incoming stage events from Proxmox."""
        try:
            data = await request.json()
            stage = data.get("stage", "unknown")
            message = data.get("message", "")
            _LOGGER.info("Proxmox Backup stage: %s - %s", stage, message)
            hass.bus.async_fire(
                f"{DOMAIN}_stage",
                {"stage": stage, "message": message},
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("Webhook error: %s", err)

    async_register(hass, DOMAIN, "Backup Stages", webhook_id, handle_webhook)

    base_url = get_url(hass, require_ssl=False, allow_external=False)
    return f"{base_url}/api/webhook/{webhook_id}"


async def async_unload_webhook(hass: HomeAssistant, entry) -> None:
    """Unregister the webhook."""
    async_unregister(hass, entry.entry_id)