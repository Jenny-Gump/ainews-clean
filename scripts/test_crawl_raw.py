#!/usr/bin/env python3
"""
Test raw Crawl API response
"""
import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def test_crawl_raw():
    api_key = os.getenv('FIRECRAWL_API_KEY')
    
    url = "https://openai.com/news/"
    
    payload = {
        "url": url,
        "limit": 5,
        "maxDepth": 2
    }
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print(f"Testing Crawl API with: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'https://api.firecrawl.dev/v1/crawl',
            headers=headers,
            json=payload
        ) as response:
            print(f"\nStatus: {response.status}")
            
            text = await response.text()
            print(f"Raw response: {text[:1000]}")
            
            if response.status == 200:
                data = json.loads(text)
                print(f"\nSuccess: {data.get('success')}")
                print(f"Data type: {type(data.get('data'))}")
                print(f"Data keys: {data.keys()}")
                
                if 'data' in data:
                    print(f"Data length: {len(data['data'])}")
                    if data['data']:
                        print(f"First item keys: {data['data'][0].keys() if isinstance(data['data'], list) and len(data['data']) > 0 else 'N/A'}")

if __name__ == '__main__':
    asyncio.run(test_crawl_raw())