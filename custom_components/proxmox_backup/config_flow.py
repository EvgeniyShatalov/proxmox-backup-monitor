"""Config flow for Proxmox Backup Monitor."""
from __future__ import annotations

import logging
from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from proxmoxer import ProxmoxAPI

from .const import (
    DOMAIN, CONF_HOST, CONF_USER, CONF_TOKEN_ID, CONF_TOKEN_SECRET,
    CONF_VERIFY_SSL, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DEFAULT_VERIFY_SSL,
)

_LOGGER = logging.getLogger(__name__)

class ProxmoxBackupConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                await self.hass.async_add_executor_job(self._test_connection, user_input)
            except Exception as err:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title=f"Proxmox Backup ({user_input[CONF_HOST]})", data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_HOST, default="192.168.1.100"): str,
            vol.Required(CONF_USER, default="root@pam"): str,
            vol.Required(CONF_TOKEN_ID, default="ha-backup"): str,
            vol.Required(CONF_TOKEN_SECRET): str,
            vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
        })
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    def _test_connection(self, data: dict[str, Any]) -> None:
        client = ProxmoxAPI(
            data[CONF_HOST], user=data[CONF_USER], token_name=data[CONF_TOKEN_ID],
            token_value=data[CONF_TOKEN_SECRET], verify_ssl=data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL), timeout=10,
        )
        client.version.get()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return ProxmoxBackupOptionsFlow()

class ProxmoxBackupOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        data_schema = vol.Schema({vol.Optional(CONF_SCAN_INTERVAL, default=current): vol.All(int, vol.Range(min=1, max=1440))})
        return self.async_show_form(step_id="init", data_schema=data_schema)