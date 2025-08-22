#!/usr/bin/env python3
"""
HelloJob.az Candidate Scraper
High-speed async scraper for extracting candidate data from hellojob.az
"""

import asyncio
import aiohttp
import csv
import json
import os
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin, parse_qs, urlparse
from bs4 import BeautifulSoup
from dataclasses import dataclass
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Candidate:
    phone: str
    name: str
    age: int
    position: str
    salary: str
    location: str
    completion_percentage: str
    posted_date: str
    cv_id: str
    cv_url: str
    birth_date: Optional[str] = None
    education: List[str] = None
    languages: List[str] = None
    experience: List[str] = None
    skills: List[str] = None
    
    def __post_init__(self):
        if self.education is None:
            self.education = []
        if self.languages is None:
            self.languages = []
        if self.experience is None:
            self.experience = []
        if self.skills is None:
            self.skills = []

class HelloJobScraper:
    def __init__(self):
        self.base_url = "https://www.hellojob.az"
        self.login_url = f"{self.base_url}/account/login"
        self.cv_pool_url = f"{self.base_url}/hr/cv-pool"
        self.session: Optional[aiohttp.ClientSession] = None
        self.login_email = os.getenv('login')
        self.password = os.getenv('password')
        self.scraped_candidates: List[Candidate] = []
        self.concurrent_requests = 10
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=50, limit_per_host=20)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def login(self) -> bool:
        """Login to hellojob.az"""
        try:
            # First get the login page to extract CSRF token or any hidden fields
            async with self.session.get(self.login_url) as response:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                
                # Look for CSRF token or any hidden inputs
                csrf_token = None
                csrf_input = soup.find('input', {'name': '_token'})
                if csrf_input:
                    csrf_token = csrf_input.get('value')
            
            # Prepare login data
            login_data = {
                'email': self.login_email,
                'password': self.password
            }
            
            if csrf_token:
                login_data['_token'] = csrf_token
            
            # Attempt login
            async with self.session.post(self.login_url, data=login_data, allow_redirects=False) as response:
                if response.status in [302, 301]:
                    # Check if redirected to dashboard/hr area
                    location = response.headers.get('Location', '')
                    if '/hr/' in location or response.status == 302:
                        logger.info("Successfully logged in")
                        return True
                elif response.status == 200:
                    # Check if we're on the HR dashboard
                    text = await response.text()
                    if '/hr/cv-pool' in text or 'CV hovuzu' in text:
                        logger.info("Successfully logged in")
                        return True
                
                logger.error(f"Login failed with status {response.status}")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    async def get_total_pages(self) -> int:
        """Get total number of pages from the CV pool"""
        try:
            async with self.session.get(f"{self.cv_pool_url}?page=1") as response:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                
                # Find pagination links
                pagination = soup.find('ul', class_='pagination')
                if pagination:
                    page_links = pagination.find_all('a', class_='pagination__link')
                    if page_links:
                        last_page_link = page_links[-1]['href']
                        page_match = re.search(r'page=(\d+)', last_page_link)
                        if page_match:
                            return int(page_match.group(1))
                
                # Fallback: look for page numbers in text
                page_pattern = re.compile(r'(\d+)\s*və\s*\d+\s*arası\s*göstərilir')
                match = page_pattern.search(text)
                if match:
                    return int(match.group(1))
                
                return 633  # Default based on your example
        except Exception as e:
            logger.error(f"Error getting total pages: {e}")
            return 1
    
    async def extract_candidate_ids_from_page(self, page_num: int) -> List[str]:
        """Extract candidate IDs from a CV pool page"""
        try:
            url = f"{self.cv_pool_url}?page={page_num}"
            async with self.session.get(url) as response:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                
                candidate_ids = []
                
                # Find all candidate items
                candidate_items = soup.find_all('div', class_='vacancies__item--custom')
                
                for item in candidate_items:
                    data_id = item.get('data-id')
                    if data_id:
                        candidate_ids.append(data_id)
                
                logger.info(f"Page {page_num}: Found {len(candidate_ids)} candidates")
                return candidate_ids
                
        except Exception as e:
            logger.error(f"Error extracting candidates from page {page_num}: {e}")
            return []
    
    async def get_candidate_phone(self, cv_id: str) -> Optional[str]:
        """Get candidate phone number from the show-phone endpoint"""
        try:
            phone_url = f"{self.base_url}/hr/cv-pool/cv/{cv_id}/show-phone"
            async with self.session.get(phone_url) as response:
                data = await response.json()
                if not data.get('error', True) and 'phone' in data:
                    return data['phone']
                return None
        except Exception as e:
            logger.error(f"Error getting phone for CV {cv_id}: {e}")
            return None
    
    async def scrape_candidate_details(self, cv_id: str) -> Optional[Candidate]:
        """Scrape detailed information for a single candidate"""
        try:
            cv_url = f"{self.base_url}/hr/cv-pool/cv/{cv_id}"
            
            # Get candidate page and phone number concurrently
            candidate_task = self.session.get(cv_url)
            phone_task = self.get_candidate_phone(cv_id)
            
            async with candidate_task as response:
                text = await response.text()
                phone = await phone_task
                
                soup = BeautifulSoup(text, 'html.parser')
                
                # Extract basic information
                name_elem = soup.find('h1', class_='section-title')
                name = name_elem.text.strip() if name_elem else "N/A"
                
                # Extract age from title
                age_pattern = re.search(r'\((\d+)\)', text)
                age = int(age_pattern.group(1)) if age_pattern else 0
                
                # Extract position
                position_elem = soup.find('p', class_='cv__user__position')
                position = position_elem.text.strip() if position_elem else "N/A"
                
                # Extract location
                location_elem = soup.find('div', class_='cv__user__address')
                location = location_elem.get_text(strip=True).replace('Bakı', '').strip() if location_elem else "N/A"
                
                # Extract salary
                salary = "N/A"
                salary_items = soup.find_all('p', class_='cv__details__item')
                for item in salary_items:
                    if 'AZN' in item.text:
                        salary = item.get_text(strip=True).split('\n')[-1].strip()
                        break
                
                # Extract posted date
                posted_date = "N/A"
                date_elem = soup.find('p', class_='cv__user__date')
                if date_elem:
                    posted_date = date_elem.text.strip().replace('Yerləşdirildi:', '').strip()
                
                # Extract completion percentage from the list page (we'll need to get this differently)
                completion_percentage = "N/A"
                
                # Extract birth date
                birth_date = None
                birth_items = soup.find_all('p', class_='cv__details__item')
                for item in birth_items:
                    if 'Doğum tarixi' in item.text:
                        birth_date = item.get_text().split(':')[-1].strip()
                        break
                
                # Extract education
                education = []
                education_sections = soup.find_all('div', class_='cv__item--sub')
                for section in education_sections:
                    title_elem = section.find('h2', class_='cv__title')
                    if title_elem:
                        education.append(title_elem.text.strip())
                
                # Extract languages
                languages = []
                lang_sections = soup.find_all('div', class_='cv__item')
                for section in lang_sections:
                    if section.find_parent('div', class_='page-spacing'):
                        parent = section.find_parent('div', class_='page-spacing')
                        if parent and parent.find('h2', string=lambda text: text and 'Dil bilikləri' in text):
                            title_elem = section.find('h2', class_='cv__title')
                            if title_elem:
                                languages.append(title_elem.text.strip())
                
                candidate = Candidate(
                    phone=phone or "N/A",
                    name=name,
                    age=age,
                    position=position,
                    salary=salary,
                    location=location,
                    completion_percentage=completion_percentage,
                    posted_date=posted_date,
                    cv_id=cv_id,
                    cv_url=cv_url,
                    birth_date=birth_date,
                    education=education,
                    languages=languages
                )
                
                logger.info(f"Scraped candidate: {name} (ID: {cv_id})")
                return candidate
                
        except Exception as e:
            logger.error(f"Error scraping candidate {cv_id}: {e}")
            return None
    
    async def scrape_page_batch(self, page_numbers: List[int]) -> List[Candidate]:
        """Scrape multiple pages concurrently"""
        candidates = []
        
        # First, get all candidate IDs from all pages
        id_tasks = [self.extract_candidate_ids_from_page(page) for page in page_numbers]
        page_results = await asyncio.gather(*id_tasks, return_exceptions=True)
        
        all_candidate_ids = []
        for result in page_results:
            if isinstance(result, list):
                all_candidate_ids.extend(result)
        
        # Then scrape candidate details in batches
        semaphore = asyncio.Semaphore(self.concurrent_requests)
        
        async def scrape_with_semaphore(cv_id):
            async with semaphore:
                return await self.scrape_candidate_details(cv_id)
        
        # Process candidates in batches to avoid overwhelming the server
        batch_size = self.concurrent_requests
        for i in range(0, len(all_candidate_ids), batch_size):
            batch_ids = all_candidate_ids[i:i + batch_size]
            tasks = [scrape_with_semaphore(cv_id) for cv_id in batch_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Candidate):
                    candidates.append(result)
            
            # Small delay between batches
            await asyncio.sleep(1)
        
        return candidates
    
    async def scrape_all_candidates(self) -> List[Candidate]:
        """Scrape all candidates from all pages"""
        if not await self.login():
            logger.error("Failed to login")
            return []
        
        total_pages = await self.get_total_pages()
        logger.info(f"Found {total_pages} pages to scrape")
        
        # Process pages in batches
        page_batch_size = 10
        all_candidates = []
        
        for i in range(1, total_pages + 1, page_batch_size):
            page_batch = list(range(i, min(i + page_batch_size, total_pages + 1)))
            logger.info(f"Processing pages {page_batch[0]} to {page_batch[-1]}")
            
            candidates = await self.scrape_page_batch(page_batch)
            all_candidates.extend(candidates)
            
            logger.info(f"Total candidates scraped so far: {len(all_candidates)}")
            
            # Delay between page batches
            await asyncio.sleep(2)
        
        self.scraped_candidates = all_candidates
        return all_candidates
    
    def export_to_csv(self, filename: str = "hellojob_candidates.csv"):
        """Export scraped candidates to CSV file"""
        if not self.scraped_candidates:
            logger.error("No candidates to export")
            return
        
        # Ensure phone is the first column
        fieldnames = ['phone', 'name', 'age', 'position', 'salary', 'location', 
                     'completion_percentage', 'posted_date', 'cv_id', 'cv_url', 
                     'birth_date', 'education', 'languages']
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for candidate in self.scraped_candidates:
                row = {
                    'phone': candidate.phone,
                    'name': candidate.name,
                    'age': candidate.age,
                    'position': candidate.position,
                    'salary': candidate.salary,
                    'location': candidate.location,
                    'completion_percentage': candidate.completion_percentage,
                    'posted_date': candidate.posted_date,
                    'cv_id': candidate.cv_id,
                    'cv_url': candidate.cv_url,
                    'birth_date': candidate.birth_date,
                    'education': '; '.join(candidate.education) if candidate.education else '',
                    'languages': '; '.join(candidate.languages) if candidate.languages else ''
                }
                writer.writerow(row)
        
        logger.info(f"Exported {len(self.scraped_candidates)} candidates to {filename}")

async def main():
    async with HelloJobScraper() as scraper:
        candidates = await scraper.scrape_all_candidates()
        scraper.export_to_csv()
        print(f"Successfully scraped {len(candidates)} candidates")

if __name__ == "__main__":
    asyncio.run(main())