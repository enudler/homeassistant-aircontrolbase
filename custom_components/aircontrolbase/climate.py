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
        self._attr_min_temp = 16
        self._attr_max_temp = 30
        self._attr_fan_modes = ["low", "mid", "high", "auto"]

    @property
    def _device(self) -> Dict[str, Any]:
        """Return the latest device data from the coordinator."""
        device_id = int(self._attr_unique_id.split("_")[1])
        device = next(
            (device for device in self.coordinator.data if device["id"] == device_id),
            None,
        )
        if device is None:
            _LOGGER.error("Device with ID %s not found in coordinator data", device_id)
            return {}
        _LOGGER.debug("Device data for ID %s: %s", device_id, device)
        return device

    @property
    def current_temperature(self) -> Optional[float]:
        """Return the current temperature."""
        return self._device.get("factTemp")

    @property
    def target_temperature(self) -> Optional[float]:
        """Return the target temperature."""
        return self._device.get("setTemp")

    @property
    def hvac_mode(self) -> str:
        """Return the current HVAC mode."""
        if not self.is_on:
            return HVACMode.OFF
        mode = self._device.get("mode")
        if mode == "cool":
            return HVACMode.COOL
        elif mode == "heat":
            return HVACMode.HEAT
        elif mode == "fan_only":
            return HVACMode.FAN_ONLY
        elif mode == "dry":
            return HVACMode.DRY
        return HVACMode.OFF

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

    @property
    def is_on(self) -> bool:
        """Return whether the device is on."""
        power_state = self._device.get("power")
        _LOGGER.debug("Device %s power state: %s", self._attr_unique_id, power_state)
        return power_state == "y"

    @property
    def fan_mode(self) -> Optional[str]:
        """Return the current fan mode."""
        return self._device.get("wind")

    @property
    def fan_modes(self) -> List[str]:
        """Return the list of available fan modes."""
        return ["auto", "low", "medium", "high"]

    @property
    def swing_mode(self) -> Optional[str]:
        """Return the swing setting."""
        return self._device.get("swingMode")

    @property
    def swing_modes(self) -> List[str]:
        """Return the list of available swing modes."""
        return ["off", "vertical", "horizontal", "both"]

    async def async_update(self):
        """Fetch the latest data from the coordinator."""
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            _LOGGER.error("No temperature provided to set_temperature")
            return

        control_data = {
            "id": self._device.get("id"),
            "groupId": self._device.get("groupId"),
            "deviceNumber": self._device.get("deviceNumber"),
            "cid": self._device.get("cid"),
            "aid": self._device.get("aid"),
        }

        operation_data = {
            "mode": self.hvac_mode,
            "power": "y",
            "setTemp": temperature,
            "wind": self._device.get("windMode"),
            "swing": self._device.get("swingMode"),
            "other": self._device.get("otherSettings"),
        }

        try:
            await self._api.control_device(control_data, operation_data)
            _LOGGER.info("Successfully set temperature to %s for device %s", temperature, self._device.get("id"))

            # Trigger a state refresh after sending the command
            await self.coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.error("Failed to set temperature: %s", e)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        mode_map = {
            HVACMode.OFF: "off",
            HVACMode.COOL: "cool",
            HVACMode.HEAT: "heat",
            HVACMode.DRY: "dry",
            HVACMode.FAN_ONLY: "fan",
        }
        
        operation_data = self._device.copy()  # Start with all device data
        operation_data.update({"mode": mode_map[hvac_mode]})
        if hvac_mode == HVACMode.OFF:
            operation_data["power"] = "n"  # Explicitly turn off the device
        else:
            operation_data["power"] = "y"  # Ensure the device is on for other modes

        control_data = {"control": "mode"}  # Specify the change being made

        _LOGGER.debug("Sending control command to server: %s", operation_data)

        await self._api.control_device(
            control_data,
            operation_data,
        )
        await self.coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set the fan mode."""
        if fan_mode not in ["low", "mid", "high", "auto"]:
            _LOGGER.error("Invalid fan mode: %s", fan_mode)
            return

        await self._api.set_device_property(self._device["id"], "wind", fan_mode)
        self._device["wind"] = fan_mode
        self.async_write_ha_state()

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new target swing mode."""
        await self._api.control_device(
            self._device["id"],
            {"swingMode": swing_mode},
        )
        await self.coordinator.async_request_refresh()