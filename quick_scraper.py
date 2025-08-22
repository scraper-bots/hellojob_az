#!/usr/bin/env python3
"""
Ultra-fast HelloJob.az scraper optimized for maximum speed
"""

import asyncio
import aiohttp
import csv
import json
import re
from typing import List, Dict, Optional, Set
from bs4 import BeautifulSoup
import logging
from dotenv import load_dotenv
import os

load_dotenv()

class QuickHelloJobScraper:
    def __init__(self, max_concurrent: int = 20):
        self.base_url = "https://www.hellojob.az"
        self.session: Optional[aiohttp.ClientSession] = None
        self.max_concurrent = max_concurrent
        self.scraped_data: List[Dict] = []
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        timeout = aiohttp.ClientTimeout(total=20)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def login(self) -> bool:
        """Quick login"""
        try:
            login_data = {
                'email': os.getenv('login'),
                'password': os.getenv('password')
            }
            
            async with self.session.post(f"{self.base_url}/account/login", data=login_data) as response:
                return response.status in [200, 302]
        except:
            return False
    
    async def get_candidate_ids(self, page: int) -> List[str]:
        """Fast extraction of candidate IDs"""
        try:
            async with self.session.get(f"{self.base_url}/hr/cv-pool?page={page}") as response:
                text = await response.text()
                return re.findall(r'data-id="(\d+)"', text)
        except:
            return []
    
    async def get_candidate_data(self, cv_id: str) -> Dict:
        """Get candidate data with phone number"""
        tasks = [
            self.session.get(f"{self.base_url}/hr/cv-pool/cv/{cv_id}"),
            self.session.get(f"{self.base_url}/hr/cv-pool/cv/{cv_id}/show-phone")
        ]
        
        try:
            results = await asyncio.gather(*tasks)
            page_response, phone_response = results
            
            # Parse page
            text = await page_response.text()
            soup = BeautifulSoup(text, 'html.parser')
            
            # Get phone
            phone = "N/A"
            try:
                phone_data = await phone_response.json()
                if not phone_data.get('error', True):
                    phone = phone_data.get('phone', "N/A")
            except:
                pass
            
            # Quick extraction
            name = soup.find('h1', class_='section-title')
            name = name.text.strip() if name else "N/A"
            
            age_match = re.search(r'\((\d+)\)', text)
            age = age_match.group(1) if age_match else "N/A"
            
            position = soup.find('p', class_='cv__user__position')
            position = position.text.strip() if position else "N/A"
            
            # Extract salary
            salary_match = re.search(r'(\d+)\s*AZN', text)
            salary = f"{salary_match.group(1)} AZN" if salary_match else "N/A"
            
            # Extract location  
            location_elem = soup.find('div', class_='cv__user__address')
            location = location_elem.get_text(strip=True) if location_elem else "N/A"
            location = re.sub(r'^[^A-Za-zəüöğışçÜÖĞIŞÇƏ]*', '', location).strip()
            
            return {
                'phone': phone,
                'name': name,
                'age': age,
                'position': position,
                'salary': salary,
                'location': location,
                'cv_id': cv_id,
                'cv_url': f"{self.base_url}/hr/cv-pool/cv/{cv_id}"
            }
            
        except Exception as e:
            print(f"Error processing {cv_id}: {e}")
            return None
    
    async def scrape_fast(self, max_pages: int = None) -> List[Dict]:
        """Ultra-fast scraping"""
        print("🚀 Starting ultra-fast scrape...")
        
        if not await self.login():
            print("❌ Login failed")
            return []
        
        # Get total pages quickly
        async with self.session.get(f"{self.base_url}/hr/cv-pool?page=1") as response:
            text = await response.text()
            page_match = re.findall(r'page=(\d+)', text)
            total_pages = max([int(p) for p in page_match] + [1])
            
        if max_pages:
            total_pages = min(total_pages, max_pages)
        
        print(f"📄 Found {total_pages} pages")
        
        # Get all candidate IDs fast
        print("🔍 Extracting candidate IDs...")
        id_tasks = [self.get_candidate_ids(page) for page in range(1, total_pages + 1)]
        all_ids = []
        for ids in await asyncio.gather(*id_tasks, return_exceptions=True):
            if isinstance(ids, list):
                all_ids.extend(ids)
        
        # Remove duplicates
        unique_ids = list(set(all_ids))
        print(f"👥 Found {len(unique_ids)} unique candidates")
        
        # Process candidates with semaphore
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_with_limit(cv_id):
            async with semaphore:
                return await self.get_candidate_data(cv_id)
        
        print("📱 Extracting candidate data...")
        tasks = [process_with_limit(cv_id) for cv_id in unique_ids]
        
        results = []
        completed = 0
        for coro in asyncio.as_completed(tasks):
            result = await coro
            if result:
                results.append(result)
            completed += 1
            if completed % 50 == 0:
                print(f"   ✅ Processed {completed}/{len(unique_ids)} candidates")
        
        self.scraped_data = results
        return results
    
    def export_csv(self, filename: str = "hellojob_fast.csv"):
        """Export to CSV with phone first"""
        if not self.scraped_data:
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'phone', 'name', 'age', 'position', 'salary', 
                'location', 'cv_id', 'cv_url'
            ])
            writer.writeheader()
            writer.writerows(self.scraped_data)
        
        print(f"💾 Exported {len(self.scraped_data)} candidates to {filename}")

async def quick_scrape(max_pages: int = None):
    """Quick scraper function"""
    async with QuickHelloJobScraper(max_concurrent=25) as scraper:
        candidates = await scraper.scrape_fast(max_pages)
        scraper.export_csv()
        return len(candidates)

if __name__ == "__main__":
    import sys
    max_pages = int(sys.argv[1]) if len(sys.argv) > 1 else None
    count = asyncio.run(quick_scrape(max_pages))
    print(f"🎉 Completed! Scraped {count} candidates")