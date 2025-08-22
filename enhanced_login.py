#!/usr/bin/env python3
"""
Enhanced login with proper session handling
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import json

load_dotenv()

async def enhanced_login():
    """Try different login approaches"""
    
    # Headers to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        print("🔍 Trying enhanced login...")
        
        # Step 1: Visit main page first to get initial session
        async with session.get('https://www.hellojob.az') as response:
            print(f"Main page status: {response.status}")
        
        # Step 2: Get login page with proper referrer
        headers['Referer'] = 'https://www.hellojob.az'
        async with session.get('https://www.hellojob.az/account/login', headers=headers) as response:
            print(f"Login page status: {response.status}")
            text = await response.text()
            
            # Save the login page for analysis
            with open('login_page.html', 'w', encoding='utf-8') as f:
                f.write(text)
            
            soup = BeautifulSoup(text, 'html.parser')
            
            # Look for meta CSRF token
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            csrf_token = csrf_meta.get('content') if csrf_meta else None
            print(f"Meta CSRF token: {'Found' if csrf_token else 'Not found'}")
            
            # Look for any form token
            form = soup.find('form')
            if form:
                print(f"Form action: {form.get('action', 'No action')}")
                print(f"Form method: {form.get('method', 'No method')}")
                
                # Get all form inputs
                inputs = form.find_all('input')
                form_data = {}
                for inp in inputs:
                    name = inp.get('name')
                    value = inp.get('value', '')
                    input_type = inp.get('type', 'text')
                    print(f"Input: {name} ({input_type}) = {value[:20]}...")
                    if name:
                        form_data[name] = value
        
        # Step 3: Try different login approaches
        
        # Approach 1: Standard POST
        print("\n🧪 Trying standard POST...")
        login_data = {
            'email': os.getenv('login'),
            'password': os.getenv('password')
        }
        
        if csrf_token:
            login_data['_token'] = csrf_token
        
        # Add X-CSRF-TOKEN header if we have it
        post_headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        if csrf_token:
            post_headers['X-CSRF-TOKEN'] = csrf_token
        
        async with session.post(
            'https://www.hellojob.az/account/login', 
            data=login_data,
            headers=post_headers,
            allow_redirects=False
        ) as response:
            print(f"Standard POST status: {response.status}")
            if response.status == 302:
                location = response.headers.get('Location', '')
                print(f"Redirect to: {location}")
            
            # Check if we can now access HR area
            async with session.get('https://www.hellojob.az/hr/cv-pool') as hr_response:
                print(f"HR access status: {hr_response.status}")
                hr_text = await hr_response.text()
                
                if 'data-id=' in hr_text:
                    print("✅ Found candidate data!")
                    import re
                    candidate_ids = re.findall(r'data-id="(\d+)"', hr_text)
                    print(f"Sample candidates found: {len(candidate_ids)}")
                    if candidate_ids[:3]:
                        print(f"First 3 IDs: {candidate_ids[:3]}")
                    return True
                elif 'login' in hr_text.lower():
                    print("❌ Still redirected to login")
                else:
                    print("❌ Unexpected response")
        
        # Approach 2: Try JSON login if standard fails
        print("\n🧪 Trying JSON login...")
        json_headers = {'Content-Type': 'application/json'}
        if csrf_token:
            json_headers['X-CSRF-TOKEN'] = csrf_token
        
        async with session.post(
            'https://www.hellojob.az/account/login',
            json=login_data,
            headers=json_headers,
            allow_redirects=False
        ) as response:
            print(f"JSON POST status: {response.status}")
            
            # Check HR access again
            async with session.get('https://www.hellojob.az/hr/cv-pool') as hr_response:
                hr_text = await hr_response.text()
                if 'data-id=' in hr_text:
                    print("✅ JSON login successful!")
                    return True
        
        return False

if __name__ == "__main__":
    asyncio.run(enhanced_login())