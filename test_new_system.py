#!/usr/bin/env python3
"""
Test script for the new global last_parsed system
"""
import sys
import os
import asyncio

# Add core directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import Database
from services.rss_discovery import ExtractRSSDiscovery
from datetime import datetime, timezone

async def test_new_system():
    """Test the new global system"""
    print("🧪 Testing New Global Last_Parsed System...")
    
    # Test database global config
    print("\n1. Testing Database Global Config:")
    db = Database()
    
    # Get current global last_parsed
    current_global = db.get_global_last_parsed()
    print(f"   Current global last_parsed: {current_global}")
    
    # Test RSS Discovery
    print("\n2. Testing RSS Discovery with Global System:")
    discovery = ExtractRSSDiscovery()
    
    # Get available sources
    sources = discovery.load_sources()
    print(f"   Available RSS sources: {len(sources)}")
    
    # Test discovery on a small subset
    test_sources = ['openai', 'google_ai'] if len(sources) >= 2 else [sources[0]['id']] if sources else []
    
    if test_sources:
        print(f"   Testing discovery on sources: {test_sources}")
        
        # Set global last_parsed to a recent time to limit results
        recent_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        recent_str = recent_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        db.set_global_last_parsed(recent_str)
        print(f"   Set global last_parsed to: {recent_str}")
        
        # Run discovery
        stats = await discovery.discover_from_sources(test_sources)
        print(f"   Discovery results: {stats}")
        
        # Check if global timestamp was updated
        new_global = db.get_global_last_parsed()
        print(f"   New global last_parsed: {new_global}")
        
        if stats['new_articles'] > 0:
            print("   ✅ System found new articles and updated global timestamp")
        else:
            print("   ℹ️ No new articles found (expected with recent timestamp)")
            
    else:
        print("   ❌ No RSS sources available for testing")
    
    print("\n3. Testing API Integration:")
    # Test the Extract API endpoints
    try:
        from monitoring.extract_api import router
        print("   ✅ Extract API router loaded successfully")
    except Exception as e:
        print(f"   ❌ Error loading Extract API: {e}")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_new_system())