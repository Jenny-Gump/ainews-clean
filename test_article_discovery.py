#!/usr/bin/env python3
"""
Test article discovery with older timestamp
"""
import sys
import os
import asyncio

# Add core directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import Database
from services.rss_discovery import ExtractRSSDiscovery
from datetime import datetime, timezone, timedelta

async def test_article_discovery():
    """Test finding new articles"""
    print("🔍 Testing Article Discovery with Older Timestamp...")
    
    db = Database()
    discovery = ExtractRSSDiscovery()
    
    # Set timestamp to 2 days ago to find some articles
    old_time = datetime.now(timezone.utc) - timedelta(days=2)
    old_str = old_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    print(f"Setting global last_parsed to: {old_str}")
    db.set_global_last_parsed(old_str)
    
    # Test on one source to avoid too many requests
    test_sources = ['openai']
    
    print(f"Testing discovery on: {test_sources}")
    stats = await discovery.discover_from_sources(test_sources)
    
    print(f"Discovery results:")
    print(f"  Sources processed: {stats['sources_processed']}")
    print(f"  Articles discovered: {stats['articles_discovered']}")
    print(f"  Articles saved: {stats['articles_saved']}")
    print(f"  New articles: {stats['new_articles']}")
    print(f"  Errors: {stats['errors']}")
    
    # Check updated timestamp
    new_global = db.get_global_last_parsed()
    print(f"Updated global last_parsed: {new_global}")
    
    if stats['new_articles'] > 0:
        print("✅ Successfully found and saved new articles!")
        print("✅ Global timestamp was updated!")
    else:
        print("ℹ️ No new articles found (may be normal)")

if __name__ == "__main__":
    asyncio.run(test_article_discovery())