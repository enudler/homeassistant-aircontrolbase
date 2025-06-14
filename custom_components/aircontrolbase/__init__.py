"""The AirControlBase integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AirControlBaseAPI
from .const import (
    CONF_AVOID_REFRESH_STATUS_ON_UPDATE_IN_MS,
    DEFAULT_AVOID_REFRESH_STATUS_ON_UPDATE_IN_MS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CLIMATE]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AirControlBase from a config entry."""
    session = async_get_clientsession(hass)
    api = AirControlBaseAPI(
        entry.data["email"],
        entry.data["password"],
        session,
        entry.data.get(
            CONF_AVOID_REFRESH_STATUS_ON_UPDATE_IN_MS,
            DEFAULT_AVOID_REFRESH_STATUS_ON_UPDATE_IN_MS,
        ),
    )

    await api.login()

    async def async_update_data() -> list[dict[str, Any]]:
        """Fetch data from API."""
        try:
            await api.ensure_authenticated()  # Ensure the API client is authenticated
            devices = await api.getDetails()  # Use getDetails for status updates
            _LOGGER.debug("Coordinator fetched devices: %s", devices)
            return devices
        except Exception as err:
            _LOGGER.error("Error fetching data: %s", err)
            raise UpdateFailed(f"Error fetching data: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=30),  # Refresh every 30 seconds
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok