#!/usr/bin/env python3
"""
Browser-like login that mimics the JavaScript behavior
"""

import asyncio
import aiohttp
import json
from dotenv import load_dotenv
import os

load_dotenv()

async def browser_like_login():
    """Login that mimics browser behavior"""
    
    async with aiohttp.ClientSession() as session:
        print("🌐 Simulating browser login...")
        
        # Step 1: Load the main page first
        async with session.get('https://www.hellojob.az') as response:
            print(f"Main page: {response.status}")
        
        # Step 2: Load login page
        async with session.get('https://www.hellojob.az/account/login') as response:
            print(f"Login page: {response.status}")
            cookies = response.cookies
            print(f"Got cookies: {len(cookies)} cookies")
        
        # Step 3: Try to get CSRF token from a separate endpoint
        csrf_endpoints = [
            'https://www.hellojob.az/sanctum/csrf-cookie',
            'https://www.hellojob.az/csrf-token',
            'https://www.hellojob.az/api/csrf-token'
        ]
        
        csrf_token = None
        for endpoint in csrf_endpoints:
            try:
                async with session.get(endpoint) as response:
                    if response.status == 200:
                        print(f"CSRF endpoint {endpoint}: {response.status}")
                        # Check if it's JSON with token
                        try:
                            data = await response.json()
                            if 'token' in data:
                                csrf_token = data['token']
                                break
                        except:
                            pass
                        # Check cookies for XSRF-TOKEN
                        for cookie in response.cookies:
                            if cookie.key == 'XSRF-TOKEN':
                                csrf_token = cookie.value
                                break
                        if csrf_token:
                            break
            except:
                continue
        
        print(f"CSRF token from endpoints: {'Found' if csrf_token else 'Not found'}")
        
        # Step 4: Try login with proper headers
        login_data = {
            'email': os.getenv('login'),
            'password': os.getenv('password'),
            'remember': 'on'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',  # Important for AJAX requests
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.hellojob.az/account/login'
        }
        
        if csrf_token:
            headers['X-CSRF-TOKEN'] = csrf_token
            login_data['_token'] = csrf_token
        
        # Try the login
        async with session.post(
            'https://www.hellojob.az/account/login',
            data=login_data,
            headers=headers,
            allow_redirects=False
        ) as response:
            print(f"Login attempt: {response.status}")
            
            if response.status == 200:
                try:
                    result = await response.json()
                    print(f"Login response: {result}")
                except:
                    text = await response.text()
                    print(f"Login response (text): {text[:200]}...")
            
            # Test HR access
            async with session.get('https://www.hellojob.az/hr/cv-pool') as hr_response:
                print(f"HR access: {hr_response.status}")
                hr_text = await hr_response.text()
                
                if 'data-id=' in hr_text and 'cv-pool' in hr_text:
                    print("✅ Successfully logged in and accessed HR area!")
                    
                    # Get some sample data
                    import re
                    candidate_ids = re.findall(r'data-id="(\d+)"', hr_text)
                    print(f"Found {len(candidate_ids)} candidates")
                    
                    if candidate_ids:
                        # Test phone endpoint
                        test_id = candidate_ids[0]
                        async with session.get(f'https://www.hellojob.az/hr/cv-pool/cv/{test_id}/show-phone') as phone_response:
                            print(f"Phone test ({test_id}): {phone_response.status}")
                            if phone_response.status == 200:
                                try:
                                    phone_data = await phone_response.json()
                                    print(f"Phone API works: {phone_data}")
                                    return True
                                except:
                                    print("Phone endpoint returned non-JSON")
                    
                elif 'login' in hr_text.lower():
                    print("❌ Still not logged in")
                else:
                    print("❌ Unexpected HR response")
                    # Save response for debugging
                    with open('hr_response.html', 'w', encoding='utf-8') as f:
                        f.write(hr_text)
        
        return False

if __name__ == "__main__":
    success = asyncio.run(browser_like_login())
    if success:
        print("🎉 Login test successful! Ready to run full scraper.")
    else:
        print("❌ Login test failed. Need to debug further.")