#!/usr/bin/env python3
"""
Test Crawl API with status checking
"""
import asyncio
import aiohttp
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

async def test_crawl_with_status():
    api_key = os.getenv('FIRECRAWL_API_KEY')
    
    url = "https://openai.com/news/"
    
    # 1. Start crawl
    payload = {
        "url": url,
        "limit": 5,
        "maxDepth": 2
    }
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print(f"Starting crawl of: {url}")
    
    async with aiohttp.ClientSession() as session:
        # Start crawl
        async with session.post(
            'https://api.firecrawl.dev/v1/crawl',
            headers=headers,
            json=payload
        ) as response:
            if response.status != 200:
                print(f"Error starting crawl: {response.status}")
                print(await response.text())
                return
            
            data = await response.json()
            crawl_id = data.get('id')
            status_url = data.get('url')
            
            print(f"Crawl started with ID: {crawl_id}")
            print(f"Status URL: {status_url}")
        
        # 2. Check status
        print("\nChecking status...")
        
        for i in range(30):  # Check for up to 30 seconds
            await asyncio.sleep(2)
            
            async with session.get(
                status_url,
                headers={'Authorization': f'Bearer {api_key}'}
            ) as response:
                if response.status != 200:
                    print(f"Error checking status: {response.status}")
                    break
                
                status_data = await response.json()
                status = status_data.get('status')
                
                print(f"Status: {status}")
                
                if status == 'completed':
                    print("\nCrawl completed!")
                    print(f"Total pages: {status_data.get('total', 0)}")
                    
                    # Get the data
                    if 'data' in status_data:
                        pages = status_data['data']
                        print(f"Pages found: {len(pages)}")
                        
                        # Show first few pages
                        for j, page in enumerate(pages[:3], 1):
                            print(f"\n{j}. URL: {page.get('url')}")
                            if 'metadata' in page:
                                print(f"   Title: {page['metadata'].get('title', 'N/A')}")
                            if 'markdown' in page:
                                content_preview = page['markdown'][:200].replace('\n', ' ')
                                print(f"   Content: {content_preview}...")
                    break
                    
                elif status == 'failed':
                    print(f"Crawl failed: {status_data.get('error')}")
                    break
                    
                else:
                    # Still processing
                    completed = status_data.get('completed', 0)
                    total = status_data.get('total', 0)
                    print(f"  Progress: {completed}/{total} pages")

if __name__ == '__main__':
    asyncio.run(test_crawl_with_status())