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
        
        _LOGGER.debug("Attempting login to AirControlBase with email: %s", self._email)
        
        try:
            async with async_timeout.timeout(10):
                async with self._session.post(
                    f"{self._base_url}/web/user/login",
                    json=data,  # Try JSON instead of form data
                    headers={"Content-Type": "application/json"},
                ) as response:
                    _LOGGER.debug("Login response status: %s", response.status)
                    _LOGGER.debug("Login response headers: %s", dict(response.headers))
                    
                    if response.status != 200:
                        raise Exception(f"HTTP error {response.status}")
                    
                    try:
                        result = await response.json()
                    except Exception as e:
                        text_result = await response.text()
                        _LOGGER.error("Failed to parse JSON response: %s. Raw response: %s", e, text_result)
                        raise Exception(f"Invalid response format: {e}")
                    
                    _LOGGER.debug("Login response: %s", result)
                    
                    # Check multiple possible success indicators
                    if (result.get("code") == 0 or 
                        result.get("code") == "0" or 
                        result.get("code") == 200 or 
                        result.get("code") == "200" or
                        result.get("success") is True or
                        result.get("status") == "success"):
                        
                        # Extract user ID
                        if "result" in result and "id" in result["result"]:
                            self._user_id = result["result"]["id"]
                        elif "user_id" in result:
                            self._user_id = result["user_id"]
                        elif "userId" in result:
                            self._user_id = result["userId"]
                        else:
                            _LOGGER.error("No user ID found in response: %s", result)
                            raise Exception("No user ID in response")
                        
                        # Extract session cookie
                        cookies = response.headers.getall('Set-Cookie', [])
                        if cookies:
                            self._session_id = '; '.join(cookies)
                        else:
                            _LOGGER.warning("No session cookies found, trying without")
                            self._session_id = ""
                        
                        _LOGGER.info("Successfully logged in to AirControlBase (User ID: %s)", self._user_id)
                    else:
                        error_msg = result.get('message') or result.get('error') or f"Unknown error (code: {result.get('code')})"
                        _LOGGER.error("Login failed: %s", error_msg)
                        raise Exception(f"Login failed: {error_msg}")
                        
        except Exception as e:
            _LOGGER.error("Login exception: %s", e)
            # Try with form data as fallback
            try:
                _LOGGER.debug("Retrying login with form data")
                async with async_timeout.timeout(10):
                    async with self._session.post(
                        f"{self._base_url}/web/user/login",
                        data=data,  # Form data
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            _LOGGER.debug("Fallback login response: %s", result)
                            
                            if (result.get("code") == 0 or result.get("code") == "0" or 
                                result.get("success") is True):
                                self._user_id = result.get("result", {}).get("id") or result.get("user_id")
                                cookies = response.headers.getall('Set-Cookie', [])
                                self._session_id = '; '.join(cookies) if cookies else ""
                                _LOGGER.info("Fallback login successful")
                                return
                                
            except Exception as fallback_error:
                _LOGGER.error("Fallback login also failed: %s", fallback_error)
            
            raise Exception(f"Authentication failed: {e}")

    async def control_device(self, control: Dict[str, Any], operation: Dict[str, Any]) -> None:
        """Control a device."""
        if not self._user_id:
            raise Exception("Not authenticated - please login first")
            
        self._last_update_time = int(time.time() * 1000)
        data = {
            "userId": self._user_id,
            "control": control,
            "operation": operation,
        }
        
        _LOGGER.debug("Controlling device with data: %s", data)
        
        try:
            async with async_timeout.timeout(10):
                headers = {"Content-Type": "application/json"}
                if self._session_id:
                    headers["Cookie"] = self._session_id
                
                async with self._session.post(
                    f"{self._base_url}/web/device/control",
                    json=data,
                    headers=headers,
                ) as response:
                    _LOGGER.debug("Control device response status: %s", response.status)
                    
                    if response.status != 200:
                        raise Exception(f"HTTP error {response.status}")
                    
                    result = await response.json()
                    _LOGGER.debug("Control device response: %s", result)
                    
                    if not (result.get("code") == 0 or result.get("code") == "0" or 
                            result.get("success") is True):
                        error_msg = result.get('message') or result.get('error') or "Unknown error"
                        raise Exception(f"Control failed: {error_msg}")
                        
        except Exception as e:
            _LOGGER.error("Control device failed: %s", e)
            # Try fallback with form data
            try:
                async with async_timeout.timeout(10):
                    headers = {"Cookie": self._session_id} if self._session_id else {}
                    async with self._session.post(
                        f"{self._base_url}/web/device/control",
                        data=data,
                        headers=headers,
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            if result.get("code") == 0:
                                return
            except Exception as fallback_error:
                _LOGGER.error("Fallback control device also failed: %s", fallback_error)
            
            raise Exception(f"Device control failed: {e}")

    async def get_devices(self) -> List[Dict[str, Any]]:
        """Get all devices."""
        if (
            self._last_update_time > 0
            and int(time.time() * 1000) - self._last_update_time
            < self._avoid_refresh_status_on_update_in_ms
        ):
            return []

        if not self._user_id:
            raise Exception("Not authenticated - please login first")

        data = {"userId": self._user_id}
        
        try:
            async with async_timeout.timeout(10):
                headers = {}
                if self._session_id:
                    headers["Cookie"] = self._session_id
                
                async with self._session.post(
                    f"{self._base_url}/web/userGroup/getDetails",
                    json=data,  # Try JSON first
                    headers={**headers, "Content-Type": "application/json"},
                ) as response:
                    _LOGGER.debug("Get devices response status: %s", response.status)
                    
                    if response.status != 200:
                        raise Exception(f"HTTP error {response.status}")
                    
                    result = await response.json()
                    _LOGGER.debug("Get devices response: %s", result)
                    
                    if (result.get("code") == 0 or result.get("code") == "0" or 
                        result.get("success") is True):
                        all_devices = []
                        if result.get("result", {}).get("areas"):
                            for area in result["result"]["areas"]:
                                all_devices.extend(area.get("data", []))
                        return all_devices
                    else:
                        error_msg = result.get('message') or result.get('error') or "Unknown error"
                        raise Exception(f"Failed to get devices: {error_msg}")
                        
        except Exception as e:
            _LOGGER.error("Get devices failed: %s", e)
            # Try fallback with form data
            try:
                async with async_timeout.timeout(10):
                    headers = {"Cookie": self._session_id} if self._session_id else {}
                    async with self._session.post(
                        f"{self._base_url}/web/userGroup/getDetails",
                        data=data,
                        headers=headers,
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            if result.get("code") == 0:
                                all_devices = []
                                if result.get("result", {}).get("areas"):
                                    for area in result["result"]["areas"]:
                                        all_devices.extend(area.get("data", []))
                                return all_devices
            except Exception as fallback_error:
                _LOGGER.error("Fallback get devices also failed: %s", fallback_error)
            
            raise Exception(f"Failed to get devices: {e}")

    async def test_connection(self) -> bool:
        """Test if the connection and authentication are working."""
        try:
            await self.login()
            # Try to get devices to fully test the connection
            await self.get_devices()
            return True
        except Exception as e:
            _LOGGER.error("Connection test failed: %s", e)
            return False 