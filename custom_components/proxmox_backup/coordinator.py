"""DataUpdateCoordinator for Proxmox Backup Monitor."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from proxmoxer import ProxmoxAPI
from proxmoxer.core import ResourceException

from .const import (
    DOMAIN, CONF_HOST, CONF_USER, CONF_TOKEN_ID, CONF_TOKEN_SECRET,
    CONF_VERIFY_SSL, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DEFAULT_VERIFY_SSL,
)

_LOGGER = logging.getLogger(__name__)

class ProxmoxBackupCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls the Proxmox VE API for backup task status."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass, _LOGGER, name=DOMAIN,
            update_interval=timedelta(minutes=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
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

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.hass.async_add_executor_job(self._fetch_backup_data)
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

    def _fetch_backup_data(self) -> dict[str, Any]:
        nodes = self.proxmox.nodes.get()
        all_tasks: list[dict[str, Any]] = []

        for node in nodes:
            node_name = node["node"]
            tasks = self.proxmox.nodes(node_name).tasks.get(typefilter="vzdump", limit=50)
            for task in tasks:
                task["node"] = node_name
                all_tasks.append(task)

        if not all_tasks:
            return {"state": "unknown", "exitstatus": "no_tasks", "duration": 0, "last_run": None, "errors": 0, "last_vmid": None}

        all_tasks.sort(key=lambda x: x.get("starttime", 0), reverse=True)
        latest = all_tasks[0]

        status = self.proxmox.nodes(latest["node"]).tasks(latest["upid"]).status.get()
        task_status = status.get("status", "unknown")
        exitstatus = status.get("exitstatus", "unknown")

        duration = 0
        if isinstance(task_status, str) and task_status.startswith("stopped:"):
            try:
                duration = int(task_status.split(":", 1)[1].strip().split()[0])
            except (ValueError, IndexError):
                pass

        state = "running" if task_status == "running" else ("ok" if exitstatus == "OK" else "error")

        return {
            "state": state,
            "exitstatus": exitstatus,
            "duration": duration,
            "last_run": latest.get("starttime", 0),
            "last_vmid": latest.get("id"),
            "errors": sum(1 for t in all_tasks if t.get("status") not in (None, "running", "OK") and t.get("endtime", 0) > (latest.get("starttime", 0) - 86400)),
        }