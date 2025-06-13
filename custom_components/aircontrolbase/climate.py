"""Climate platform for AirControlBase integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    PRECISION_WHOLE,
    TEMP_CELSIUS,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import AirControlBaseAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the AirControlBase climate platform."""
    api: AirControlBaseAPI = hass.data[DOMAIN][config_entry.entry_id]["api"]
    coordinator: DataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    async_add_entities(
        AirControlBaseClimate(api, coordinator, device)
        for device in coordinator.data
    )

class AirControlBaseClimate(CoordinatorEntity, ClimateEntity):
    """Representation of an AirControlBase climate device."""

    def __init__(
        self,
        api: AirControlBaseAPI,
        coordinator: DataUpdateCoordinator,
        device: Dict[str, Any],
    ) -> None:
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._api = api
        self._device = device
        self._attr_unique_id = f"{DOMAIN}_{device['id']}"
        self._attr_name = device["name"]
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE |
            ClimateEntityFeature.FAN_MODE |
            ClimateEntityFeature.SWING_MODE
        )
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_precision = PRECISION_WHOLE
        self._attr_hvac_modes = [
            HVACMode.OFF,
            HVACMode.COOL,
            HVACMode.HEAT,
            HVACMode.DRY,
            HVACMode.FAN_ONLY,
        ]

    @property
    def current_temperature(self) -> Optional[float]:
        """Return the current temperature."""
        return self._device.get("currentTemperature")

    @property
    def target_temperature(self) -> Optional[float]:
        """Return the temperature we try to reach."""
        return self._device.get("targetTemperature")

    @property
    def hvac_mode(self) -> HVACMode:
        """Return hvac operation mode."""
        mode = self._device.get("mode", "off")
        return {
            "off": HVACMode.OFF,
            "cool": HVACMode.COOL,
            "heat": HVACMode.HEAT,
            "dry": HVACMode.DRY,
            "fan": HVACMode.FAN_ONLY,
        }.get(mode, HVACMode.OFF)

    @property
    def hvac_action(self) -> HVACAction:
        """Return the current running hvac operation."""
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        if self.hvac_mode == HVACMode.COOL:
            return HVACAction.COOLING
        if self.hvac_mode == HVACMode.HEAT:
            return HVACAction.HEATING
        if self.hvac_mode == HVACMode.DRY:
            return HVACAction.DRYING
        return HVACAction.FAN

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        await self._api.control_device(
            self._device["id"],
            {"targetTemperature": temperature},
        )
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        mode_map = {
            HVACMode.OFF: "off",
            HVACMode.COOL: "cool",
            HVACMode.HEAT: "heat",
            HVACMode.DRY: "dry",
            HVACMode.FAN_ONLY: "fan",
        }
        
        await self._api.control_device(
            self._device["id"],
            {"mode": mode_map[hvac_mode]},
        )
        await self.coordinator.async_request_refresh()

    @property
    def fan_mode(self) -> Optional[str]:
        """Return the fan setting."""
        return self._device.get("fanMode")

    @property
    def fan_modes(self) -> List[str]:
        """Return the list of available fan modes."""
        return ["auto", "low", "medium", "high"]

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        await self._api.control_device(
            self._device["id"],
            {"fanMode": fan_mode},
        )
        await self.coordinator.async_request_refresh()

    @property
    def swing_mode(self) -> Optional[str]:
        """Return the swing setting."""
        return self._device.get("swingMode")

    @property
    def swing_modes(self) -> List[str]:
        """Return the list of available swing modes."""
        return ["off", "vertical", "horizontal", "both"]

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new target swing mode."""
        await self._api.control_device(
            self._device["id"],
            {"swingMode": swing_mode},
        )
        await self.coordinator.async_request_refresh() 