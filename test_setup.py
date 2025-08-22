#!/usr/bin/env python3
"""
Test script to validate the scraper setup
"""

import asyncio
import os
from pathlib import Path

async def test_imports():
    """Test if all required packages can be imported"""
    try:
        import aiohttp
        import asyncio
        from bs4 import BeautifulSoup
        from dotenv import load_dotenv
        print("✅ All required packages imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_env_file():
    """Test if .env file exists and has required variables"""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ .env file not found")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    login = os.getenv('login')
    password = os.getenv('password')
    
    if not login or not password:
        print("❌ Login credentials not found in .env file")
        return False
    
    print(f"✅ .env file found with login: {login[:3]}***@{login.split('@')[1] if '@' in login else '***'}")
    return True

async def test_basic_connection():
    """Test basic connection to hellojob.az"""
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get('https://www.hellojob.az', timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    print("✅ Successfully connected to hellojob.az")
                    return True
                else:
                    print(f"⚠️  hellojob.az returned status {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

async def main():
    print("🧪 Testing HelloJob.az Scraper Setup...\n")
    
    # Test imports
    imports_ok = await test_imports()
    
    # Test env file
    env_ok = test_env_file()
    
    # Test connection
    connection_ok = await test_basic_connection()
    
    print("\n" + "="*50)
    if imports_ok and env_ok and connection_ok:
        print("🎉 Setup validation PASSED! Ready to scrape.")
        print("\nNext steps:")
        print("  • Test mode: python run_scraper.py --test")
        print("  • Full scrape: python run_scraper.py")
    else:
        print("❌ Setup validation FAILED!")
        if not imports_ok:
            print("  • Install requirements: pip install -r requirements.txt")
        if not env_ok:
            print("  • Create .env file with login and password")
        if not connection_ok:
            print("  • Check internet connection")

if __name__ == "__main__":
    asyncio.run(main())