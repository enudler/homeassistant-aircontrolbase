import os
import asyncio
import aiohttp
import pytest
import ssl
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from custom_components.aircontrolbase.api import AirControlBaseAPI

EMAIL = os.environ.get("AIRCONTROLBASE_EMAIL")
PASSWORD = os.environ.get("AIRCONTROLBASE_PASSWORD")

@pytest.mark.asyncio
async def test_login():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        api = AirControlBaseAPI(email=EMAIL, password=PASSWORD, session=session)
        await api.login()
        assert api._user_id is not None
        assert api._session_id is not None

@pytest.mark.asyncio
async def test_list_devices():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        api = AirControlBaseAPI(email=EMAIL, password=PASSWORD, session=session)
        await api.login()
        devices = await api.get_devices()
        assert isinstance(devices, list)
        for device in devices:
            print(f"Device: {device.get('name')}, Working: {device.get('power')}, Temp: {device.get('factTemp')}, Wind: {device.get('wind')}, Mode: {device.get('mode')}")

@pytest.mark.asyncio
async def test_device_control():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        api = AirControlBaseAPI(email=EMAIL, password=PASSWORD, session=session)
        await api.login()
        devices = await api.get_devices()
        if not devices:
            pytest.skip("No devices found")
        device = devices[0]
        control_data = {
            "id": device['id'],
            "groupId": device['groupId'],
            "deviceNumber": device['deviceNumber'],
            "cid": device['cid'],
            "aid": device['aid']
        }
        operation_data = {
            "mode": "off",
            "power": "n",
            "wind": device['wind'],
            "setTemp": device['setTemp'],
            "swing": device['swing'],
            "other": device['other']
        }
        await api.control_device(control_data, operation_data)
        await asyncio.sleep(2)
        # Turn on and change temp/wind
        operation_data["mode"] = device["mode"]
        operation_data["power"] = "y"
        operation_data["setTemp"] = device["setTemp"] + 1 if isinstance(device["setTemp"], int) else 23
        operation_data["wind"] = "high" if device["wind"] != "high" else "low"
        await api.control_device(control_data, operation_data)
        await asyncio.sleep(2)
        # Fetch status again
        updated_devices = await api.get_devices()
        updated = next((d for d in updated_devices if d["id"] == device["id"]), None)
        assert updated is not None
        print(f"Updated Device: {updated.get('name')}, Power: {updated.get('power')}, Temp: {updated.get('setTemp')}, Wind: {updated.get('wind')}") 