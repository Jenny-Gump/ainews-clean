#!/usr/bin/env python3
"""
Test Map API for quick URL discovery
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.firecrawl_client import FirecrawlClient


async def test_map():
    """Test Map API"""
    
    urls_to_test = [
        "https://openai.com/news/",
        "https://www.anthropic.com/news",
        "https://huggingface.co/blog"
    ]
    
    client = FirecrawlClient()
    
    async with client:
        for url in urls_to_test:
            print(f"\n{'='*60}")
            print(f"Testing Map API with: {url}")
            print(f"{'='*60}")
            
            try:
                result = await client.map_website(url)
                
                if result.get('success'):
                    links = result.get('links', [])
                    print(f"✅ Success! Found {len(links)} URLs")
                    print(f"Time: {result.get('map_time', 0):.2f}s")
                    
                    # Filter for news/blog articles
                    article_keywords = ['2024', '2025', 'blog', 'news', 'post', 'article']
                    article_links = [
                        link for link in links 
                        if any(kw in link.lower() for kw in article_keywords)
                    ]
                    
                    print(f"\nPotential articles: {len(article_links)}")
                    
                    # Show first few
                    for i, link in enumerate(article_links[:5], 1):
                        print(f"{i}. {link}")
                    
                    if len(article_links) > 5:
                        print(f"... and {len(article_links) - 5} more")
                else:
                    print(f"❌ Failed: {result}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")


if __name__ == '__main__':
    asyncio.run(test_map())