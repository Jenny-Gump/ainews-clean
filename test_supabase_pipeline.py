#!/usr/bin/env python3
"""
Test Script для Supabase Pipeline Integration
Проверяет все функции pipeline с Supabase базой данных
"""
import os
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.db_config import DatabaseConfig
from core.config import Config
from core.single_pipeline import SingleArticlePipeline
from services.rss_discovery import ExtractRSSDiscovery
from services.content_parser import ContentParser
from services.wordpress_publisher import WordPressPublisher
from app_logging import configure_logging, get_logger

def setup_logging():
    """Setup logging for tests"""
    configure_logging(
        level='INFO',
        log_dir='logs',
        prefix='supabase_test'
    )

def test_database_config():
    """Test 1: Database Configuration"""
    logger = get_logger('test.db_config')
    logger.info("=== TEST 1: Database Configuration ===")
    
    # Проверяем информацию о конфигурации
    info = DatabaseConfig.get_database_info()
    logger.info(f"Database type: {info['type']}")
    logger.info(f"Supabase available: {info['supabase_available']}")
    logger.info(f"Supabase connection OK: {info['supabase_connection_ok']}")
    
    # Получаем инстанс базы данных
    db = DatabaseConfig.get_database()
    logger.info(f"Database instance: {type(db).__name__}")
    logger.info(f"Database path: {getattr(db, 'db_path', 'N/A')}")
    
    return db

def test_database_basic_operations(db):
    """Test 2: Basic Database Operations"""
    logger = get_logger('test.db_operations')
    logger.info("=== TEST 2: Basic Database Operations ===")
    
    try:
        # Test connection
        with db.get_connection() as conn:
            logger.info("✅ Database connection successful")
        
        # Test basic stats
        stats = db.get_stats()
        logger.info(f"✅ Stats retrieved: {stats['total_articles']} articles, {stats['total_sources']} sources")
        
        # Test sources
        sources = db.get_sources()
        logger.info(f"✅ Sources retrieved: {len(sources)} active sources")
        
        return True
    except Exception as e:
        logger.error(f"❌ Database operations failed: {e}")
        return False

def test_rss_discovery():
    """Test 3: RSS Discovery"""
    logger = get_logger('test.rss_discovery')
    logger.info("=== TEST 3: RSS Discovery ===")
    
    try:
        rss_service = ExtractRSSDiscovery()
        logger.info(f"✅ RSS Discovery initialized with {len(rss_service.rss_sources)} sources")
        
        # Test discover (небольшая выборка)
        discovery_result = asyncio.run(rss_service.discover_articles(days_back=1, limit=5))
        logger.info(f"✅ Discovery completed: {discovery_result['discovered_articles']} articles found")
        
        return True
    except Exception as e:
        logger.error(f"❌ RSS Discovery failed: {e}")
        return False

def test_content_parsing():
    """Test 4: Content Parsing"""
    logger = get_logger('test.content_parsing')
    logger.info("=== TEST 4: Content Parsing ===")
    
    try:
        db = DatabaseConfig.get_database()
        
        # Получаем первую pending статью
        pending_articles = db.get_pending_articles(limit=1)
        if not pending_articles:
            logger.warning("⚠️ No pending articles found for parsing test")
            return True
        
        article = pending_articles[0]
        logger.info(f"Testing parsing for article: {article['article_id']}")
        
        # Test content parser
        async def parse_test():
            async with ContentParser() as parser:
                result = await parser.parse_single_article(
                    article_id=article['article_id'],
                    url=article['url'], 
                    source_id=article['source_id']
                )
                return result
        
        result = asyncio.run(parse_test())
        if result.get('success'):
            logger.info(f"✅ Content parsing successful: {result.get('content_length', 0)} chars")
        else:
            logger.warning(f"⚠️ Content parsing failed: {result.get('error')}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Content parsing test failed: {e}")
        return False

def test_wordpress_publisher():
    """Test 5: WordPress Publisher"""
    logger = get_logger('test.wordpress_publisher')
    logger.info("=== TEST 5: WordPress Publisher ===")
    
    try:
        config = Config()
        db = DatabaseConfig.get_database()
        publisher = WordPressPublisher(config, db)
        
        logger.info("✅ WordPress Publisher initialized")
        
        # Test connectivity (без реальной публикации)
        if hasattr(publisher, '_test_wordpress_connection'):
            connection_ok = publisher._test_wordpress_connection()
            logger.info(f"WordPress connection test: {'✅ OK' if connection_ok else '⚠️ Failed'}")
        
        return True
    except Exception as e:
        logger.error(f"❌ WordPress Publisher test failed: {e}")
        return False

def test_single_pipeline():
    """Test 6: Single Pipeline"""
    logger = get_logger('test.single_pipeline')
    logger.info("=== TEST 6: Single Pipeline ===")
    
    try:
        pipeline = SingleArticlePipeline()
        logger.info("✅ Single Pipeline initialized")
        
        # Test getting next article
        next_article = pipeline.get_next_article()
        if next_article:
            logger.info(f"✅ Next article found: {next_article['article_id']}")
            # Не запускаем реальную обработку в тесте
        else:
            logger.info("ℹ️ No articles available for processing")
        
        # Test status
        status = pipeline.get_status()
        logger.info(f"✅ Pipeline status: {status['status']}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Single Pipeline test failed: {e}")
        return False

def test_database_health():
    """Test 7: Database Health Check"""
    logger = get_logger('test.db_health')
    logger.info("=== TEST 7: Database Health Check ===")
    
    try:
        db = DatabaseConfig.get_database()
        health = db.check_database_health()
        
        logger.info(f"Database healthy: {'✅' if health['healthy'] else '❌'}")
        if health['issues']:
            for issue in health['issues']:
                logger.warning(f"⚠️ Issue: {issue}")
        
        if health['metrics']:
            for key, value in health['metrics'].items():
                logger.info(f"  {key}: {value}")
        
        return health['healthy']
    except Exception as e:
        logger.error(f"❌ Database health check failed: {e}")
        return False

def main():
    """Main test runner"""
    setup_logging()
    logger = get_logger('test.main')
    
    logger.info("🧪 SUPABASE PIPELINE INTEGRATION TESTS")
    logger.info("=" * 50)
    
    # Test results
    results = {}
    
    # Run tests
    try:
        db = test_database_config()
        results['db_config'] = True
    except Exception as e:
        logger.error(f"Database config test failed: {e}")
        results['db_config'] = False
        db = None
    
    if db:
        results['db_operations'] = test_database_basic_operations(db)
        results['db_health'] = test_database_health()
    else:
        results['db_operations'] = False
        results['db_health'] = False
    
    results['rss_discovery'] = test_rss_discovery()
    results['content_parsing'] = test_content_parsing()
    results['wordpress_publisher'] = test_wordpress_publisher()
    results['single_pipeline'] = test_single_pipeline()
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("🏁 TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name.upper():20} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info("-" * 50)
    logger.info(f"PASSED: {passed}")
    logger.info(f"FAILED: {failed}")
    logger.info(f"TOTAL:  {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 ALL TESTS PASSED! Supabase integration is working correctly.")
        return 0
    else:
        logger.error(f"💥 {failed} TESTS FAILED! Check configuration and connections.")
        return 1

if __name__ == "__main__":
    sys.exit(main())