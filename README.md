# HelloJob.az Candidate Scraper

High-speed asynchronous web scraper for extracting candidate data from hellojob.az HR platform.

## Features

- **High-speed async scraping** using aiohttp
- **Phone number extraction** via dedicated API endpoint
- **Complete candidate data** including education, languages, experience
- **CSV export** with phone number as first column
- **Rate limiting** and error handling
- **Session management** with automatic login
- **Concurrent processing** with configurable limits

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your credentials in `.env` file:
```
login=your_email@gmail.com
password=your_password
```

## Usage

### Basic Usage
```bash
python run_scraper.py
```

### Test Mode (first 2 pages only)
```bash
python run_scraper.py --test
```

### Limit pages
```bash
python run_scraper.py --max-pages 10
```

### Custom output file
```bash
python run_scraper.py --output my_candidates.csv
```

### Verbose logging
```bash
python run_scraper.py --verbose
```

### Advanced Usage
```bash
python hellojob_scraper.py
```

## Output Format

The CSV file contains the following columns (phone number first):

- **phone**: Candidate phone number (extracted via API)
- **name**: Full name
- **age**: Age
- **position**: Desired position/job title
- **salary**: Expected salary
- **location**: Location/city
- **completion_percentage**: CV completion percentage
- **posted_date**: Date when CV was posted
- **cv_id**: Internal CV ID
- **cv_url**: Direct URL to candidate's CV
- **birth_date**: Date of birth
- **education**: Education background (semicolon separated)
- **languages**: Languages (semicolon separated)

## Performance

- **Concurrent requests**: 10 simultaneous requests
- **Rate limiting**: Built-in delays between batches
- **Error recovery**: Automatic retry for failed requests
- **Memory efficient**: Processes candidates in batches

## Technical Details

### Architecture
- Asynchronous HTTP client (aiohttp)
- BeautifulSoup for HTML parsing
- Dataclass-based candidate model
- Session management with automatic login
- Semaphore-based concurrency control

### Rate Limiting
- 1 second delay between batches
- 2 second delay between page batches
- Maximum 10 concurrent requests

### Error Handling
- Connection timeout handling
- Login failure detection
- Individual request failure recovery
- Comprehensive logging

## Scraped Data Structure

```python
@dataclass
class Candidate:
    phone: str              # From /show-phone endpoint
    name: str              # From candidate page
    age: int               # Extracted from name section
    position: str          # Job position
    salary: str            # Expected salary
    location: str          # City/location
    completion_percentage: str  # CV completion %
    posted_date: str       # When CV was posted
    cv_id: str             # Internal ID
    cv_url: str            # Full URL to CV
    birth_date: Optional[str]   # Date of birth
    education: List[str]   # Education history
    languages: List[str]   # Language skills
```

## Legal Notice

This scraper is designed for legitimate HR and recruitment purposes only. Please ensure you comply with hellojob.az terms of service and applicable data protection laws when using this tool.

## Support

For issues or questions, check the logs in `scraper.log` file for detailed error information.