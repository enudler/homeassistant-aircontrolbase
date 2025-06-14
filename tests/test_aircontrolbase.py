import os
import asyncio
import aiohttp
import pytest
import ssl
import sys
import json
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from custom_components.aircontrolbase.api import AirControlBaseAPI

# Set up logging to see debug output
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

EMAIL = os.environ.get("AIRCONTROLBASE_EMAIL")
PASSWORD = os.environ.get("AIRCONTROLBASE_PASSWORD")

class DebugSession:
    """Wrapper around aiohttp.ClientSession to log requests and responses."""
    
    def __init__(self, session):
        self._session = session
    
    def post(self, url, **kwargs):
        return DebugRequest(self._session.post(url, **kwargs), url, kwargs)
    
    def __getattr__(self, name):
        return getattr(self._session, name)

class DebugRequest:
    """Wrapper to log request and response details."""
    
    def __init__(self, request_coro, url, kwargs):
        self._request_coro = request_coro
        self._url = url
        self._kwargs = kwargs
    
    async def __aenter__(self):
        print(f"\n🌐 HTTP REQUEST:")
        print(f"   URL: {self._url}")
        print(f"   Method: POST")
        
        if 'headers' in self._kwargs:
            print(f"   Headers: {json.dumps(dict(self._kwargs['headers']), indent=6)}")
        
        if 'data' in self._kwargs:
            print(f"   Form Data: {self._kwargs['data']}")
        
        if 'json' in self._kwargs:
            print(f"   JSON Data: {json.dumps(self._kwargs['json'], indent=6)}")
        
        print("   Sending request...")
        
        self._response = await self._request_coro.__aenter__()
        
        print(f"\n📡 HTTP RESPONSE:")
        print(f"   Status: {self._response.status}")
        print(f"   Headers: {json.dumps(dict(self._response.headers), indent=6)}")
        
        try:
            # Read the response content
            response_text = await self._response.text()
            print(f"   Raw Response: {response_text}")
            
            # Try to parse as JSON
            try:
                response_json = json.loads(response_text)
                print(f"   JSON Response: {json.dumps(response_json, indent=6)}")
            except json.JSONDecodeError:
                print(f"   Non-JSON Response: {response_text}")
                
        except Exception as e:
            print(f"   Error reading response: {e}")
        
        return self._response
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self._request_coro.__aexit__(exc_type, exc_val, exc_tb)

@pytest.mark.asyncio
async def test_login_detailed():
    """Test login with detailed request/response logging."""
    if not EMAIL or not PASSWORD:
        pytest.skip("AIRCONTROLBASE_EMAIL and AIRCONTROLBASE_PASSWORD environment variables required")
    
    print(f"\n🔐 TESTING LOGIN FOR: {EMAIL}")
    print("=" * 60)
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        # Wrap session with debug logging
        debug_session = DebugSession(session)
        
        api = AirControlBaseAPI(email=EMAIL, password=PASSWORD, session=debug_session)
        
        try:
            await api.login()
            
            print(f"\n✅ LOGIN SUCCESSFUL!")
            print(f"   User ID: {api._user_id}")
            print(f"   Session ID Present: {'Yes' if api._session_id else 'No'}")
            print(f"   Session ID Length: {len(api._session_id) if api._session_id else 0}")
            
            assert api._user_id is not None, "User ID should not be None"
            assert api._session_id is not None, "Session ID should not be None"
            
        except Exception as e:
            print(f"\n❌ LOGIN FAILED!")
            print(f"   Error: {e}")
            print(f"   Error Type: {type(e).__name__}")
            
            # Re-raise the exception so pytest can handle it
            raise

@pytest.mark.asyncio
async def test_login_simple():
    """Simple login test without debugging."""
    if not EMAIL or not PASSWORD:
        pytest.skip("AIRCONTROLBASE_EMAIL and AIRCONTROLBASE_PASSWORD environment variables required")
    
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
async def test_raw_login_endpoint():
    """Test the raw login endpoint directly to understand the API."""
    if not EMAIL or not PASSWORD:
        pytest.skip("AIRCONTROLBASE_EMAIL and AIRCONTROLBASE_PASSWORD environment variables required")
    
    print(f"\n🔬 TESTING RAW LOGIN ENDPOINT")
    print("=" * 50)
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    base_url = "https://www.aircontrolbase.com"
    login_url = f"{base_url}/web/user/login"
    
    data = {
        "account": EMAIL,
        "password": PASSWORD,
        "avoidRefreshStatusOnUpdateInMs": 5000,
    }
    
    async with aiohttp.ClientSession(connector=connector) as session:
        print(f"🌐 Testing JSON request to: {login_url}")
        print(f"   Data: {data}")
        
        # Test with JSON data
        try:
            async with session.post(
                login_url,
                json=data,
                headers={"Content-Type": "application/json"}
            ) as response:
                print(f"\n📡 JSON Response:")
                print(f"   Status: {response.status}")
                print(f"   Headers: {dict(response.headers)}")
                
                response_text = await response.text()
                print(f"   Raw Response: {response_text}")
                
                try:
                    result = json.loads(response_text)
                    print(f"   JSON Response: {json.dumps(result, indent=4)}")
                    
                    if response.status == 200 and (result.get("code") == 0 or result.get("success")):
                        print("   ✅ JSON request successful!")
                    else:
                        print("   ❌ JSON request failed")
                        
                except json.JSONDecodeError as e:
                    print(f"   ❌ Failed to parse JSON: {e}")
                    
        except Exception as e:
            print(f"   ❌ JSON request error: {e}")
        
        print(f"\n🌐 Testing Form data request to: {login_url}")
        
        # Test with form data
        try:
            async with session.post(
                login_url,
                data=data
            ) as response:
                print(f"\n📡 Form Data Response:")
                print(f"   Status: {response.status}")
                print(f"   Headers: {dict(response.headers)}")
                
                response_text = await response.text()
                print(f"   Raw Response: {response_text}")
                
                try:
                    result = json.loads(response_text)
                    print(f"   JSON Response: {json.dumps(result, indent=4)}")
                    
                    if response.status == 200 and (result.get("code") == 0 or result.get("success")):
                        print("   ✅ Form data request successful!")
                        return result
                    else:
                        print("   ❌ Form data request failed")
                        
                except json.JSONDecodeError as e:
                    print(f"   ❌ Failed to parse JSON: {e}")
                    
        except Exception as e:
            print(f"   ❌ Form data request error: {e}")

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