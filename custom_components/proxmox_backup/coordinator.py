"""DataUpdateCoordinator for Proxmox Backup Monitor."""
from __future__ import annotations

import logging
import time
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from proxmoxer import ProxmoxAPI

from .const import (
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    CONF_TOKEN_ID,
    CONF_TOKEN_SECRET,
    CONF_TRIGGER_TOKEN,
    CONF_TRIGGER_URL,
    CONF_USER,
    CONF_VERIFY_SSL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ProxmoxBackupCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls the Proxmox VE API for backup task status."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                minutes=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )
        self.config_entry = entry
        self.proxmox = ProxmoxAPI(
            entry.data[CONF_HOST],
            user=entry.data[CONF_USER],
            token_name=entry.data[CONF_TOKEN_ID],
            token_value=entry.data[CONF_TOKEN_SECRET],
            verify_ssl=entry.data.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
            timeout=30,
        )

    async def async_trigger_backup(self) -> dict[str, str]:
        """Trigger backup via HTTP webhook on Proxmox host."""
        url = (self.config_entry.options.get(CONF_TRIGGER_URL) or "").rstrip("/")
        token = self.config_entry.options.get(CONF_TRIGGER_TOKEN) or ""
        if not url or not token:
            raise ServiceValidationError(
                "Trigger URL or token is not configured in options"
            )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{url}/trigger",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    body = await resp.text()
        except aiohttp.ClientError as err:
            raise ServiceValidationError(f"Cannot reach trigger: {err}") from err

        if resp.status == 202:
            # Даем Proxmox 5 секунд, чтобы задача vzdump реально стартовала в API
            await self.hass.async_add_executor_job(time.sleep, 5)
            await self.async_request_refresh()
            return {"status": "triggered"}
        if resp.status == 409:
            return {"status": "already_running"}
        if resp.status == 401:
            raise ServiceValidationError("Trigger token is invalid")
        raise ServiceValidationError(f"Trigger failed: {resp.status} {body}")

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.hass.async_add_executor_job(self._fetch_backup_data)
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"Error fetching data: {err}") from err

    def _fetch_backup_data(self) -> dict[str, Any]:
        nodes = self.proxmox.nodes.get()
        all_tasks: list[dict[str, Any]] = []

        for node in nodes:
            node_name = node["node"]
            tasks = self.proxmox.nodes(node_name).tasks.get(
                typefilter="vzdump", limit=50
            )
            for task in tasks:
                task["node"] = node_name
                all_tasks.append(task)

        if not all_tasks:
            return {
                "state": "unknown",
                "exitstatus": "no_tasks",
                "duration": 0,
                "last_run": None,
                "errors": 0,
                "last_vmid": None,
            }

        all_tasks.sort(key=lambda x: x.get("starttime", 0), reverse=True)
        latest = all_tasks[0]

        # ВАЖНО: Запрашиваем детальный статус именно последней задачи, 
        # чтобы получить exitstatus (в списке задач его часто нет)
        try:
            status_data = (
                self.proxmox.nodes(latest["node"])
                .tasks(latest["upid"])
                .status.get()
            )
            task_status = status_data.get("status", "unknown")
            exitstatus = status_data.get("exitstatus", "unknown")
        except Exception:
            task_status = latest.get("status", "unknown")
            exitstatus = "unknown"

        starttime = latest.get("starttime", 0)
        endtime = latest.get("endtime")
        
        duration = 0
        if endtime and starttime:
            duration = endtime - starttime
        elif task_status == "running" and starttime:
            duration = int(time.time()) - starttime

        if task_status == "running":
            state = "running"
        elif exitstatus == "OK":
            state = "ok"
        else:
            state = "error"

        # Считаем ошибки. Если последняя задача упала, ставим 1. 
        # Точный подсчёт за 24 часа требует много запросов к API.
        recent_errors = 1 if state == "error" else 0

        return {
            "state": state,
            "exitstatus": exitstatus,
            "duration": duration,
            "last_run": starttime,
            "last_vmid": latest.get("id"),
            "errors": recent_errors,
        }