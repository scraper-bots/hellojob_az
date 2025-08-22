#!/usr/bin/env python3
"""
Working scraper that bypasses login issues by using direct access if possible
"""

import asyncio
import aiohttp
import csv
import json
import re
from typing import List, Dict
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import base64

load_dotenv()

class WorkingHelloJobScraper:
    def __init__(self):
        self.session = None
        self.base_url = "https://www.hellojob.az"
        
    async def __aenter__(self):
        # Try with different user agents and headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,az;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        
        connector = aiohttp.TCPConnector(limit=30, limit_per_host=15)
        timeout = aiohttp.ClientTimeout(total=30)
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            connector=connector,
            timeout=timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def try_direct_access(self):
        """Try to access CV pool directly to see if it works without login"""
        try:
            async with self.session.get(f"{self.base_url}/hr/cv-pool") as response:
                print(f"Direct CV pool access: {response.status}")
                text = await response.text()
                
                if 'data-id=' in text and response.status == 200:
                    print("✅ Direct access works! No login needed.")
                    return True
                else:
                    print("❌ Direct access blocked, login required")
                    return False
        except Exception as e:
            print(f"Direct access error: {e}")
            return False
    
    async def alternative_login(self):
        """Try alternative login methods"""
        
        # Method 1: Try with session persistence
        jar = aiohttp.CookieJar(unsafe=True)
        self.session._cookie_jar = jar
        
        try:
            # Get main page first
            async with self.session.get(self.base_url) as response:
                pass
            
            # Get login page and extract all possible tokens
            async with self.session.get(f"{self.base_url}/account/login") as response:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                
                # Look for Laravel session token in any form
                laravel_session = None
                for cookie in response.cookies:
                    if 'session' in cookie.key.lower():
                        laravel_session = cookie.value
                        break
                
                # Try to extract any hidden form values
                form = soup.find('form', id='login-form')
                if form:
                    all_inputs = form.find_all('input')
                    form_data = {}
                    for inp in all_inputs:
                        name = inp.get('name')
                        value = inp.get('value', '')
                        if name and name not in ['email', 'password']:
                            form_data[name] = value
                
                # Prepare login data
                login_data = {
                    'email': os.getenv('login'),
                    'password': os.getenv('password'),
                    'remember': 'on'
                }
                
                # Add any hidden form fields
                if 'form_data' in locals():
                    login_data.update(form_data)
                
                # Try login with various header combinations
                for attempt in range(3):
                    headers = {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Referer': f"{self.base_url}/account/login",
                        'Origin': self.base_url
                    }
                    
                    if attempt == 1:
                        headers['X-Requested-With'] = 'XMLHttpRequest'
                    elif attempt == 2:
                        headers['Accept'] = 'application/json'
                    
                    async with self.session.post(
                        f"{self.base_url}/account/login",
                        data=login_data,
                        headers=headers,
                        allow_redirects=True
                    ) as login_response:
                        print(f"Login attempt {attempt + 1}: {login_response.status}")
                        
                        # Check if we can now access HR area
                        async with self.session.get(f"{self.base_url}/hr/cv-pool") as hr_response:
                            hr_text = await hr_response.text()
                            if 'data-id=' in hr_text and hr_response.status == 200:
                                print(f"✅ Login successful on attempt {attempt + 1}!")
                                return True
                
                return False
                
        except Exception as e:
            print(f"Alternative login error: {e}")
            return False
    
    async def scrape_sample_data(self):
        """Scrape a small sample to test functionality"""
        print("🧪 Testing with sample data extraction...")
        
        # Try direct access first
        if await self.try_direct_access():
            logged_in = True
        else:
            logged_in = await self.alternative_login()
        
        if not logged_in:
            print("❌ Could not access HR area. Trying public pages...")
            # Maybe try to access some public candidate pages directly if they exist
            return []
        
        # Get first page
        try:
            async with self.session.get(f"{self.base_url}/hr/cv-pool?page=1") as response:
                text = await response.text()
                
                # Extract candidate IDs
                candidate_ids = re.findall(r'data-id="(\d+)"', text)
                print(f"Found {len(candidate_ids)} candidate IDs")
                
                if not candidate_ids:
                    print("❌ No candidate IDs found")
                    return []
                
                # Test with first few candidates
                sample_ids = candidate_ids[:3]
                candidates = []
                
                for cv_id in sample_ids:
                    try:
                        # Get candidate page
                        candidate_url = f"{self.base_url}/hr/cv-pool/cv/{cv_id}"
                        async with self.session.get(candidate_url) as cv_response:
                            if cv_response.status != 200:
                                continue
                                
                            cv_text = await cv_response.text()
                            soup = BeautifulSoup(cv_text, 'html.parser')
                            
                            # Extract basic info
                            name_elem = soup.find('h1', class_='section-title')
                            name = name_elem.text.strip() if name_elem else "N/A"
                            
                            # Extract age
                            age_match = re.search(r'\((\d+)\)', cv_text)
                            age = age_match.group(1) if age_match else "N/A"
                            
                            # Try to get phone number
                            phone_url = f"{self.base_url}/hr/cv-pool/cv/{cv_id}/show-phone"
                            phone = "N/A"
                            try:
                                async with self.session.get(phone_url) as phone_response:
                                    if phone_response.status == 200:
                                        phone_data = await phone_response.json()
                                        if not phone_data.get('error', True):
                                            phone = phone_data.get('phone', "N/A")
                            except:
                                pass
                            
                            candidate = {
                                'phone': phone,
                                'name': name,
                                'age': age,
                                'cv_id': cv_id,
                                'cv_url': candidate_url
                            }
                            
                            candidates.append(candidate)
                            print(f"  ✅ {name} (ID: {cv_id}) - Phone: {phone}")
                    
                    except Exception as e:
                        print(f"  ❌ Error processing {cv_id}: {e}")
                        continue
                
                return candidates
                
        except Exception as e:
            print(f"Sample scraping error: {e}")
            return []
    
    def export_sample_csv(self, candidates, filename="sample_candidates.csv"):
        """Export sample data to CSV"""
        if not candidates:
            print("No candidates to export")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['phone', 'name', 'age', 'cv_id', 'cv_url']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(candidates)
        
        print(f"✅ Exported {len(candidates)} candidates to {filename}")

async def test_working_scraper():
    async with WorkingHelloJobScraper() as scraper:
        candidates = await scraper.scrape_sample_data()
        scraper.export_sample_csv(candidates)
        return len(candidates)

if __name__ == "__main__":
    count = asyncio.run(test_working_scraper())
    print(f"\n🎉 Test completed! Found {count} candidates")
    if count > 0:
        print("✅ Scraper is working! You can now scale it up.")
    else:
        print("❌ Need to resolve access issues first.")