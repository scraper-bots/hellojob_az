#!/usr/bin/env python3
"""
Debug script to test login process
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv()

async def debug_login():
    """Debug the login process"""
    async with aiohttp.ClientSession() as session:
        print("🔍 Testing login process...")
        
        # Step 1: Get login page
        async with session.get('https://www.hellojob.az/account/login') as response:
            print(f"Login page status: {response.status}")
            text = await response.text()
            soup = BeautifulSoup(text, 'html.parser')
            
            # Look for CSRF token
            csrf_input = soup.find('input', {'name': '_token'})
            csrf_token = csrf_input.get('value') if csrf_input else None
            print(f"CSRF token found: {'Yes' if csrf_token else 'No'}")
            
            # Look for any other hidden inputs
            hidden_inputs = soup.find_all('input', type='hidden')
            print(f"Hidden inputs found: {len(hidden_inputs)}")
            for inp in hidden_inputs:
                print(f"  - {inp.get('name', 'no-name')}: {inp.get('value', 'no-value')[:20]}...")
        
        # Step 2: Attempt login
        login_data = {
            'email': os.getenv('login'),
            'password': os.getenv('password')
        }
        
        if csrf_token:
            login_data['_token'] = csrf_token
        
        print(f"\n📤 Attempting login with email: {login_data['email'][:3]}***")
        
        async with session.post(
            'https://www.hellojob.az/account/login', 
            data=login_data,
            allow_redirects=False
        ) as response:
            print(f"Login response status: {response.status}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status == 302:
                location = response.headers.get('Location', '')
                print(f"Redirect location: {location}")
            
            # Try to access HR area
            async with session.get('https://www.hellojob.az/hr/cv-pool?page=1') as hr_response:
                print(f"HR area access status: {hr_response.status}")
                hr_text = await hr_response.text()
                
                if 'CV hovuzu' in hr_text or 'cv-pool' in hr_text:
                    print("✅ Successfully accessed HR area!")
                    
                    # Quick test - get first few candidate IDs
                    import re
                    candidate_ids = re.findall(r'data-id="(\d+)"', hr_text)
                    print(f"Found {len(candidate_ids)} candidates on page 1")
                    if candidate_ids:
                        print(f"First 3 IDs: {candidate_ids[:3]}")
                        
                        # Test phone endpoint for first candidate
                        if candidate_ids:
                            test_id = candidate_ids[0]
                            async with session.get(f'https://www.hellojob.az/hr/cv-pool/cv/{test_id}/show-phone') as phone_response:
                                print(f"Phone endpoint status: {phone_response.status}")
                                try:
                                    phone_data = await phone_response.json()
                                    print(f"Phone data: {phone_data}")
                                except:
                                    phone_text = await phone_response.text()
                                    print(f"Phone response: {phone_text[:200]}...")
                    
                    return True
                else:
                    print("❌ Could not access HR area")
                    print(f"Response contains: {'login' if 'login' in hr_text.lower() else 'other content'}")
                    return False

if __name__ == "__main__":
    asyncio.run(debug_login())