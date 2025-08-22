# HelloJob.az Complete Scraper

High-speed async web scraper for extracting complete candidate data from hellojob.az with phone numbers.

## Features

✅ **Phone Numbers First** - CSV exports with phone numbers as the first column  
✅ **Complete Data Extraction** - All candidate info from listing pages  
✅ **High-Speed Async** - Uses aiohttp for maximum performance  
✅ **All Pages Support** - Can scrape all 633+ pages  
✅ **Bypass Package Limits** - Works without visiting individual CV pages  
✅ **Phone API Integration** - Gets phone numbers via dedicated endpoint  

## Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure credentials in `.env`:**
```
login=your_email@gmail.com
password=your_password
```

3. **Run the scraper:**
```bash
# Default: 10 pages
python hellojob_scraper.py

# Specific page range
python hellojob_scraper.py 1 50

# All pages (633+)
python hellojob_scraper.py 1 all
```

## Usage Examples

```bash
# Test with first 5 pages
python hellojob_scraper.py 1 5

# Scrape pages 100-200
python hellojob_scraper.py 100 100

# Scrape all pages from beginning
python hellojob_scraper.py 1 all

# Start from page 50, scrape all remaining
python hellojob_scraper.py 50 all
```

## Output

The scraper generates CSV files with the following columns (phone number first):

| Column | Description |
|--------|-------------|
| **phone** | Phone number (from API) |
| **name** | Full name |
| **age** | Age |
| **position** | Job position/title |
| **salary** | Expected salary in AZN |
| **location** | City/location |
| **completion_percentage** | CV completion % |
| **posted_date** | Date when CV was posted |
| **has_cv_file** | Whether downloadable CV exists |
| **cv_id** | Internal CV ID |
| **cv_url** | Direct URL to CV page |

## Performance

- **Concurrent Processing**: 35 simultaneous requests
- **Speed**: ~90 candidates per 3 pages in ~30 seconds
- **Phone Success Rate**: ~87% of candidates have phone numbers
- **Memory Efficient**: Processes in batches

## Architecture

- **Async HTTP Client**: aiohttp for high-speed concurrent requests
- **Smart Parsing**: Regex-based data extraction from HTML
- **Session Management**: Automatic XSRF token authentication
- **Rate Limiting**: Built-in delays to respect server limits
- **Error Recovery**: Robust exception handling

## Data Extraction

The scraper extracts data directly from CV pool listing pages, avoiding the need to visit individual CV pages (which have package limitations). It then enriches the data with phone numbers via the `/show-phone` API endpoint.

### Sample Output:
```csv
phone,name,age,position,salary,location,completion_percentage,posted_date,has_cv_file,cv_id,cv_url
994773041724,Fatimə Mütəllimova,20,Satış məsləhətçisi,500 AZN,Bakı,85%,23 avqust 2025,No,208329,https://...
994519699646,Orxan Nemətli,28,Developer,1000 AZN,Xaçmaz,55%,23 avqust 2025,Yes,208320,https://...
```

## Requirements

- Python 3.7+
- aiohttp 3.9+
- python-dotenv
- Valid HelloJob.az HR account

## Legal Notice

This tool is designed for legitimate recruitment and HR purposes. Please ensure compliance with hellojob.az terms of service and applicable data protection laws.