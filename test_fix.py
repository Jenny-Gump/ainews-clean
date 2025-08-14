#!/usr/bin/env python3
"""Test the fixed pipeline"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.single_pipeline import SingleArticlePipeline
from app_logging import get_logger

logger = get_logger('test_fix')

async def test_single_mode():
    """Test single mode"""
    logger.info("=" * 60)
    logger.info("TESTING FIXED PIPELINE - SINGLE MODE")
    logger.info("=" * 60)
    
    pipeline = SingleArticlePipeline()
    
    # Test single mode - should process 1 article
    result = await pipeline.run_pipeline(continuous_mode=False)
    
    logger.info(f"Result: {result}")
    
    if result.get('processed_count', 0) > 0:
        logger.info("✅ PIPELINE WORKS!")
    else:
        logger.error("❌ PIPELINE STILL BROKEN")
    
    return result

async def test_continuous_mode():
    """Test continuous mode with 3 articles"""
    logger.info("\n" + "=" * 60)
    logger.info("TESTING FIXED PIPELINE - CONTINUOUS MODE (3 articles)")
    logger.info("=" * 60)
    
    pipeline = SingleArticlePipeline()
    
    # Test continuous mode - should process up to 3 articles
    result = await pipeline.run_pipeline(
        continuous_mode=True,
        max_articles=3,
        delay_between=2
    )
    
    logger.info(f"Processed: {result.get('processed_count', 0)} articles")
    logger.info(f"Success: {result.get('success_count', 0)}")
    logger.info(f"Failed: {result.get('error_count', 0)}")
    
    if result.get('processed_count', 0) > 0:
        logger.info("✅ CONTINUOUS MODE WORKS!")
    else:
        logger.error("❌ CONTINUOUS MODE STILL BROKEN")
    
    return result

async def main():
    try:
        # Test single mode
        await test_single_mode()
        
        # Wait a bit
        await asyncio.sleep(3)
        
        # Test continuous mode
        await test_continuous_mode()
        
        logger.info("\n✅ ALL TESTS COMPLETED")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())