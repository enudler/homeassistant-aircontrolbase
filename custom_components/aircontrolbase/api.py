"""AirControlBase API Client."""
import logging
import aiohttp
import async_timeout
from typing import Any, Dict, List, Optional
import time

_LOGGER = logging.getLogger(__name__)

class AirControlBaseAPI:
    """AirControlBase API Client."""

    def __init__(
        self,
        email: str,
        password: str,
        session: aiohttp.ClientSession,
        avoid_refresh_status_on_update_in_ms: int = 5000,
    ) -> None:
        """Initialize the API client."""
        self._email = email
        self._password = password
        self._session = session
        self._base_url = "https://www.aircontrolbase.com"
        self._user_id = None
        self._session_id = None
        self._last_update_time = 0
        self._avoid_refresh_status_on_update_in_ms = avoid_refresh_status_on_update_in_ms

    async def login(self) -> None:
        """Login to AirControlBase."""
        data = {
            "account": self._email,
            "password": self._password,
            "avoidRefreshStatusOnUpdateInMs": self._avoid_refresh_status_on_update_in_ms,
        }
        
        async with async_timeout.timeout(10):
            async with self._session.post(
                f"{self._base_url}/web/user/login",
                data=data,
            ) as response:
                result = await response.json()
                print("DEBUG: Login response:", result)  # Debug print
                if result.get("code") == 0 or result.get("code") == "200":
                    self._user_id = result["result"]["id"]
                    self._session_id = response.headers.get("set-cookie", [""])[0]
                    _LOGGER.info("Successfully logged in to AirControlBase")
                else:
                    raise Exception(f"Login failed: {result.get('message')}")

    async def control_device(self, control: Dict[str, Any], operation: Dict[str, Any]) -> None:
        """Control a device."""
        self._last_update_time = int(time.time() * 1000)
        data = {
            "userId": self._user_id,
            "control": control,
            "operation": operation,
        }
        
        async with async_timeout.timeout(10):
            async with self._session.post(
                f"{self._base_url}/web/device/control",
                data=data,
                headers={"Cookie": self._session_id},
            ) as response:
                result = await response.json()
                print("DEBUG: Control device response:", result)  # Debug print
                if result.get("code") != 0 and result.get("code") != "200":
                    raise Exception(f"Control failed: {result.get('message')}")

    async def get_devices(self) -> List[Dict[str, Any]]:
        """Get all devices."""
        if (
            self._last_update_time > 0
            and int(time.time() * 1000) - self._last_update_time
            < self._avoid_refresh_status_on_update_in_ms
        ):
            return []

        data = {"userId": self._user_id}
        
        async with async_timeout.timeout(10):
            async with self._session.post(
                f"{self._base_url}/web/userGroup/getDetails",
                data=data,
                headers={"Cookie": self._session_id},
            ) as response:
                result = await response.json()
                print("DEBUG: Get devices response:", result)  # Debug print
                if result.get("code") != 0 and result.get("code") != "200":
                    raise Exception(f"Failed to get devices: {result.get('message')}")
                
                all_devices = []
                if result.get("result", {}).get("areas"):
                    for area in result["result"]["areas"]:
                        all_devices.extend(area.get("data", []))
                return all_devices 