#!/usr/bin/env python3
"""
Simple authentication test script for AirControlBase API
"""
import asyncio
import aiohttp
import ssl
import json
import os

async def test_aircontrolbase_login():
    """Test AirControlBase authentication with detailed logging."""
    
    # Get credentials from environment
    email = os.environ.get("AIRCONTROLBASE_EMAIL")
    password = os.environ.get("AIRCONTROLBASE_PASSWORD")
    
    if not email or not password:
        print("❌ AIRCONTROLBASE_EMAIL and AIRCONTROLBASE_PASSWORD environment variables required")
        return False
    
    print(f"🔐 TESTING LOGIN FOR: {email}")
    print("=" * 60)
    
    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    base_url = "https://www.aircontrolbase.com"
    login_url = f"{base_url}/web/user/login"
    
    data = {
        "account": email,
        "password": password,
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
                        return True
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
                        return True
                    else:
                        print("   ❌ Form data request failed")
                        error_msg = result.get('message') or result.get('error') or 'Unknown error'
                        print(f"   Error message: {error_msg}")
                        
                except json.JSONDecodeError as e:
                    print(f"   ❌ Failed to parse JSON: {e}")
                    
        except Exception as e:
            print(f"   ❌ Form data request error: {e}")
    
    return False

def main():
    """Main function."""
    print("🏠 AirControlBase Authentication Test")
    print("=" * 40)
    
    try:
        result = asyncio.run(test_aircontrolbase_login())
        
        print("\n" + "=" * 60)
        if result:
            print("🎉 Authentication successful! Integration should work in Home Assistant.")
        else:
            print("💥 Authentication failed. Check the error messages above.")
            
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user.")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
