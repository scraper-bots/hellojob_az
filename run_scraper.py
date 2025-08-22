#!/usr/bin/env python3
"""
Quick runner script for HelloJob.az scraper with configuration options
"""

import asyncio
import argparse
import sys
from hellojob_scraper import HelloJobScraper
import logging

def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('scraper.log')
        ]
    )

async def run_scraper(max_pages: int = None, output_file: str = "hellojob_candidates.csv"):
    """Run the scraper with optional page limit"""
    async with HelloJobScraper() as scraper:
        if max_pages:
            # Modify scraper to limit pages
            original_get_total_pages = scraper.get_total_pages
            async def limited_get_total_pages():
                total = await original_get_total_pages()
                return min(total, max_pages)
            scraper.get_total_pages = limited_get_total_pages
        
        candidates = await scraper.scrape_all_candidates()
        scraper.export_to_csv(output_file)
        print(f"✅ Successfully scraped {len(candidates)} candidates to {output_file}")
        return len(candidates)

def main():
    parser = argparse.ArgumentParser(description='HelloJob.az Candidate Scraper')
    parser.add_argument('--max-pages', type=int, help='Maximum number of pages to scrape')
    parser.add_argument('--output', default='hellojob_candidates.csv', help='Output CSV file name')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--test', action='store_true', help='Test mode - scrape only first 2 pages')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    max_pages = args.max_pages
    if args.test:
        max_pages = 2
        print("🧪 Running in test mode - will scrape only first 2 pages")
    
    try:
        count = asyncio.run(run_scraper(max_pages, args.output))
        print(f"🎉 Scraping completed! {count} candidates exported.")
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()