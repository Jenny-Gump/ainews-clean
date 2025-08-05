#!/usr/bin/env python3
"""
Test script for FirecrawlClient service
Quick verification that the new client works correctly
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from services.firecrawl_client import FirecrawlClient, extract_article_content


async def test_firecrawl_client():
    """Test the FirecrawlClient with a simple article URL"""
    
    print("Testing FirecrawlClient...")
    
    # Test URL - a simple news article
    test_url = "https://techcrunch.com/2024/01/01/ai-trends-2024/"
    
    try:
        # Test basic client usage
        print(f"\n1. Testing basic client with URL: {test_url}")
        
        async with FirecrawlClient() as client:
            result = await client.extract_content(test_url)
            
            print("✅ Basic extraction successful!")
            print(f"   Title: {result.get('title', 'N/A')[:100]}...")
            print(f"   Content length: {len(result.get('content', ''))} chars")
            print(f"   Images found: {len(result.get('images', []))}")
            
            # Test statistics
            stats = client.get_statistics()
            print(f"   Client stats: {stats}")
            
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False
    
    try:
        # Test convenience function
        print(f"\n2. Testing convenience function...")
        
        result = await extract_article_content(test_url)
        
        print("✅ Convenience function successful!")
        print(f"   Title: {result.get('title', 'N/A')[:100]}...")
        print(f"   Content length: {len(result.get('content', ''))} chars")
        
    except Exception as e:
        print(f"❌ Convenience function test failed: {e}")
        return False
    
    try:
        # Test retry functionality with a potentially problematic URL
        print(f"\n3. Testing retry functionality...")
        
        async with FirecrawlClient() as client:
            # This might fail but should handle gracefully
            result = await client.extract_with_retry("https://example.com/nonexistent", max_retries=1)
            print("✅ Retry test completed")
            
    except Exception as e:
        print(f"⚠️  Retry test failed as expected: {e}")
        # This is expected for a non-existent URL
    
    print("\n✅ All tests completed!")
    return True


if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv('FIRECRAWL_API_KEY'):
        print("❌ FIRECRAWL_API_KEY not found in environment variables")
        print("   Please set your Firecrawl API key in .env file")
        sys.exit(1)
    
    print("🚀 Starting FirecrawlClient tests...")
    
    try:
        success = asyncio.run(test_firecrawl_client())
        if success:
            print("\n🎉 All tests passed! FirecrawlClient is working correctly.")
        else:
            print("\n❌ Some tests failed. Check the implementation.")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        sys.exit(1)