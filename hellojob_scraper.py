#!/usr/bin/env python3
"""
HelloJob.az Working Scraper
Uses the proven working approach from test
"""
import asyncio
import aiohttp
import csv
import re
from urllib.parse import unquote
from dotenv import load_dotenv
import os
import time

load_dotenv()

async def scrape_hellojob(start_page: int = 1, max_pages: int = 10):
    """Main scraping function using the working approach"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,az;q=0.6'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        print("🔐 Authenticating with HelloJob.az...")
        
        # Login
        async with session.get("https://www.hellojob.az/account/login") as response:
            xsrf_token = None
            for name, morsel in response.cookies.items():
                if name == 'XSRF-TOKEN':
                    xsrf_token = unquote(morsel.value)
                    break
        
        if not xsrf_token:
            print("❌ Authentication failed")
            return []
        
        login_data = {
            'email': os.getenv('login'),
            'password': os.getenv('password'),
            'remember': 'on'
        }
        
        login_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'X-XSRF-TOKEN': xsrf_token,
            'Origin': 'https://www.hellojob.az',
            'Referer': 'https://www.hellojob.az/account/login'
        }
        
        async with session.post("https://www.hellojob.az/account/login", data=login_data, headers=login_headers) as response:
            result = await response.json()
            print(f"✅ Login: {result.get('message', 'Success')}")
        
        # Get total pages
        async with session.get("https://www.hellojob.az/hr/cv-pool") as response:
            html = await response.text()
            page_numbers = re.findall(r'page=(\d+)', html)
            total_pages = max(int(p) for p in page_numbers) if page_numbers else 633
        
        end_page = min(start_page + max_pages - 1, total_pages)
        print(f"🚀 Scraping pages {start_page} to {end_page} (Total available: {total_pages})")
        
        all_candidates = []
        start_time = time.time()
        
        # Scrape each page
        for page in range(start_page, end_page + 1):
            try:
                page_url = "https://www.hellojob.az/hr/cv-pool" if page == 1 else f"https://www.hellojob.az/hr/cv-pool?page={page}"
                
                async with session.get(page_url) as response:
                    if response.status != 200:
                        print(f"❌ Page {page} failed: {response.status}")
                        continue
                    
                    html = await response.text()
                    
                    # Extract candidate items
                    item_pattern = r'<div class="vacancies__item vacancies__item--custom" data-id="(\d+)"[^>]*>(.*?)</div>\s*</div>\s*</div>'
                    matches = re.findall(item_pattern, html, re.DOTALL)
                    
                    print(f"📄 Page {page}: {len(matches)} candidates found")
                    
                    for cv_id, item_content in matches:
                        try:
                            # Extract position/title
                            title_match = re.search(r'class="vacancies__title[^"]*"[^>]*>([^<]+)</a>', item_content)
                            position = title_match.group(1).strip() if title_match else ""
                            
                            # Extract name and age
                            company_match = re.search(r'class="vacancies__company"[^>]*>([^<]+)</div>', item_content)
                            name = ""
                            age = ""
                            if company_match:
                                company_text = company_match.group(1).strip()
                                name_age_match = re.match(r'(.+?)\s*\((\d+)\)', company_text)
                                if name_age_match:
                                    name = name_age_match.group(1).strip()
                                    age = name_age_match.group(2)
                                else:
                                    name = company_text
                            
                            # Extract completion percentage
                            completion_match = re.search(r'(\d+)%\s*tamamlandı', item_content)
                            completion = f"{completion_match.group(1)}%" if completion_match else ""
                            
                            # Extract salary
                            salary_match = re.search(r'(\d+)\s*AZN', item_content)
                            salary = f"{salary_match.group(1)} AZN" if salary_match else ""
                            
                            # Extract location
                            location_patterns = [
                                r'svg-pin[^>]*>.*?</svg>\s*([A-Za-zəüöğışçÜÖĞIŞÇƏ\s]+)',
                                r'</svg>\s*([A-Za-zəüöğışçÜÖĞIŞÇƏ]+)\s*</li>'
                            ]
                            
                            location = ""
                            for pattern in location_patterns:
                                location_match = re.search(pattern, item_content)
                                if location_match:
                                    location = location_match.group(1).strip()
                                    break
                            
                            # Extract posted date
                            date_patterns = [
                                r'(\d{1,2}\s+\w+\s+\d{4})',
                                r'Yerləşdirildi:\s*(\d{1,2}\s+\w+\s+\d{4})'
                            ]
                            
                            posted_date = ""
                            for pattern in date_patterns:
                                date_match = re.search(pattern, item_content)
                                if date_match:
                                    posted_date = date_match.group(1)
                                    break
                            
                            # Check for downloadable CV
                            has_download = 'svg-download2' in item_content
                            
                            candidate = {
                                'cv_id': cv_id,
                                'name': name,
                                'age': age,
                                'position': position,
                                'salary': salary,
                                'location': location,
                                'completion_percentage': completion,
                                'posted_date': posted_date,
                                'has_cv_file': 'Yes' if has_download else 'No',
                                'cv_url': f"https://www.hellojob.az/hr/cv-pool/cv/{cv_id}",
                                'phone': ''
                            }
                            
                            all_candidates.append(candidate)
                            
                        except Exception as e:
                            print(f"  ❌ Error parsing candidate {cv_id}: {e}")
                            continue
                
                # Small delay between pages
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error processing page {page}: {e}")
                continue
        
        print(f"👥 Total candidates extracted: {len(all_candidates)}")
        
        if not all_candidates:
            return []
        
        # Get phone numbers
        print(f"📱 Getting phone numbers for {len(all_candidates)} candidates...")
        
        semaphore = asyncio.Semaphore(30)
        
        async def get_phone(candidate):
            async with semaphore:
                try:
                    async with session.get(f"https://www.hellojob.az/hr/cv-pool/cv/{candidate['cv_id']}/show-phone") as response:
                        if response.status == 200:
                            data = await response.json()
                            if not data.get('error', True):
                                candidate['phone'] = data.get('phone', '')
                                if candidate['phone']:
                                    print(f"  ✅ {candidate['name']} - {candidate['phone']}")
                                return candidate
                except:
                    pass
                return candidate
        
        # Process phones in batches
        batch_size = 50
        for i in range(0, len(all_candidates), batch_size):
            batch = all_candidates[i:i + batch_size]
            tasks = [get_phone(candidate) for candidate in batch]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            progress = min(i + batch_size, len(all_candidates))
            with_phones = sum(1 for c in all_candidates if c.get('phone'))
            print(f"📊 Progress: {progress}/{len(all_candidates)} - {with_phones} phone numbers found")
            
            await asyncio.sleep(0.3)
        
        elapsed = time.time() - start_time
        print(f"⏱️ Total scraping time: {elapsed:.1f} seconds")
        
        return all_candidates

def export_to_csv(candidates, filename=None):
    """Export candidates to CSV with phone as first column"""
    if not candidates:
        print("❌ No candidates to export")
        return
    
    if filename is None:
        timestamp = int(time.time())
        filename = f"hellojob_export_{timestamp}.csv"
    
    fieldnames = [
        'phone', 'name', 'age', 'position', 'salary', 'location',
        'completion_percentage', 'posted_date', 'has_cv_file', 'cv_id', 'cv_url'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(candidates)
    
    with_phone = sum(1 for c in candidates if c.get('phone'))
    print(f"\n💾 ✅ Exported {len(candidates)} candidates to {filename}")
    print(f"📊 {with_phone}/{len(candidates)} candidates have phone numbers ({with_phone/len(candidates)*100:.1f}%)")
    
    return filename

async def main():
    import sys
    
    start_page = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    
    if len(sys.argv) > 2:
        if sys.argv[2].lower() == 'all':
            max_pages = 633
        else:
            max_pages = int(sys.argv[2])
    else:
        max_pages = 10
    
    print("🌟 HelloJob.az Working Scraper")
    print("=" * 60)
    print(f"🔑 Login: {os.getenv('login', 'Not configured')}")
    print(f"📄 Scraping pages {start_page} to {start_page + max_pages - 1}")
    print("-" * 60)
    
    candidates = await scrape_hellojob(start_page, max_pages)
    
    if candidates:
        filename = export_to_csv(candidates)
        
        print(f"\n📋 Sample of first 3 candidates:")
        print("-" * 60)
        for i, c in enumerate(candidates[:3], 1):
            print(f"{i}. {c['name']} ({c['age']} years) - {c['position']}")
            print(f"   📞 Phone: {c['phone'] or 'Not available'}")
            print(f"   💰 Salary: {c['salary'] or 'Not specified'}")
            print(f"   📍 Location: {c['location'] or 'Not specified'}")
            print(f"   📄 Completion: {c['completion_percentage'] or 'Unknown'}")
            print(f"   🗓️ Posted: {c['posted_date'] or 'Unknown'}")
            print()
        
        print(f"🎉 Scraping completed successfully!")
        print(f"✅ Exported {len(candidates)} candidates with phone numbers as first column")
        
        if max_pages < 50:
            print(f"\n🚀 Ready to scale up:")
            print(f"  • For 50 pages: python hellojob_scraper_working.py 1 50")
            print(f"  • For all pages: python hellojob_scraper_working.py 1 all")
    else:
        print("❌ No candidates extracted - check login credentials")

if __name__ == "__main__":
    asyncio.run(main())