#!/usr/bin/env python3
"""
Test News Discovery with Crawl API
Тестирование системы обнаружения новостей через Firecrawl Crawl API
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app_logging import get_logger, configure_logging
from services.news_discovery import NewsDiscoveryService
from core.database import Database


async def test_single_source(source_url: str, limit: int = 5):
    """Тестирует обнаружение новостей с одного источника"""
    
    logger = get_logger('test_news_discovery')
    discovery = NewsDiscoveryService()
    
    print(f"\n{'='*80}")
    print(f"🔍 TESTING NEWS DISCOVERY: {source_url}")
    print(f"{'='*80}")
    print(f"Limit: {limit} pages")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    try:
        # Запускаем обнаружение
        results = await discovery.discover_news(
            source_url=source_url,
            limit=limit,
            max_depth=2  # Не уходим глубоко
        )
        
        # Показываем результаты
        print(f"\n📊 RESULTS:")
        print(f"{'='*80}")
        print(f"✅ Pages crawled: {results['total_crawled']}")
        print(f"🆕 New articles found: {len(results['new_articles'])}")
        print(f"📝 Existing articles: {len(results['existing_articles'])}")
        print(f"❌ Errors: {len(results['errors'])}")
        
        # Показываем новые статьи
        if results['new_articles']:
            print(f"\n🆕 NEW ARTICLES DISCOVERED:")
            print(f"{'-'*80}")
            for i, article in enumerate(results['new_articles'][:10], 1):
                print(f"\n{i}. {article['title'][:70]}")
                print(f"   URL: {article['url']}")
                print(f"   ID: {article['article_id']}")
                if article.get('content_preview'):
                    preview = article['content_preview'][:100].replace('\n', ' ')
                    print(f"   Preview: {preview}...")
        
        # Показываем существующие статьи
        if results['existing_articles']:
            print(f"\n📝 EXISTING ARTICLES (already tracked):")
            print(f"{'-'*80}")
            changed_count = sum(1 for a in results['existing_articles'] if a.get('changed'))
            print(f"Total: {len(results['existing_articles'])} (Changed: {changed_count})")
            
            # Показываем только измененные
            changed = [a for a in results['existing_articles'] if a.get('changed')]
            if changed:
                print(f"\n🔄 Changed articles:")
                for article in changed[:5]:
                    print(f"  • {article['title'][:60]}")
        
        # Показываем ошибки
        if results['errors']:
            print(f"\n❌ ERRORS:")
            print(f"{'-'*80}")
            for error in results['errors'][:5]:
                print(f"  • {error}")
        
        # Статистика из БД
        stats = discovery.get_discovery_stats()
        print(f"\n📈 DATABASE STATISTICS:")
        print(f"{'-'*80}")
        print(f"Total tracked articles: {stats['total_tracked']}")
        print(f"New pending export: {stats['new_pending_export']}")
        
        if stats.get('top_sources'):
            print(f"\nTop sources:")
            for source, count in list(stats['top_sources'].items())[:5]:
                print(f"  • {source}: {count} articles")
        
        if stats.get('latest_discoveries'):
            print(f"\nLatest discoveries:")
            for article in stats['latest_discoveries']:
                print(f"  • {article['title'][:60]}")
                print(f"    {article['created']}")
        
        return results
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_multiple_sources(limit_per_source: int = 3):
    """Тестирует обнаружение с нескольких источников"""
    
    # Тестовые источники
    test_sources = [
        "https://openai.com/news/",
        "https://www.anthropic.com/news",
        "https://huggingface.co/blog"
    ]
    
    print(f"\n{'='*80}")
    print(f"🔍 TESTING MULTIPLE SOURCES")
    print(f"{'='*80}")
    print(f"Sources: {len(test_sources)}")
    print(f"Limit per source: {limit_per_source}")
    print(f"{'='*80}\n")
    
    discovery = NewsDiscoveryService()
    
    try:
        results = await discovery.discover_multiple_sources(
            source_urls=test_sources,
            limit_per_source=limit_per_source
        )
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"{'='*80}")
        print(f"Total new articles: {results['total_new_articles']}")
        print(f"Total existing: {results['total_existing_articles']}")
        print(f"Total errors: {results['total_errors']}")
        
        print(f"\n📋 PER SOURCE:")
        for source_result in results['sources']:
            if isinstance(source_result, dict) and source_result.get('source_url'):
                url = source_result['source_url']
                new = len(source_result.get('new_articles', []))
                existing = len(source_result.get('existing_articles', []))
                print(f"  • {url}")
                print(f"    New: {new}, Existing: {existing}")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test News Discovery System')
    parser.add_argument('--url', type=str, 
                       help='Single source URL to test')
    parser.add_argument('--limit', type=int, default=5,
                       help='Pages limit per source (default: 5)')
    parser.add_argument('--multiple', action='store_true',
                       help='Test multiple sources')
    parser.add_argument('--stats', action='store_true',
                       help='Show statistics only')
    
    args = parser.parse_args()
    
    # Configure logging
    configure_logging()
    
    if args.stats:
        # Показать только статистику
        discovery = NewsDiscoveryService()
        stats = discovery.get_discovery_stats()
        
        print(f"\n📈 DISCOVERY STATISTICS:")
        print(f"{'='*80}")
        print(f"Total tracked: {stats['total_tracked']}")
        print(f"New pending: {stats['new_pending_export']}")
        
        if stats.get('top_sources'):
            print(f"\nTop sources:")
            for source, count in list(stats['top_sources'].items())[:10]:
                print(f"  {source}: {count}")
        
        if stats.get('latest_discoveries'):
            print(f"\nLatest discoveries:")
            for article in stats['latest_discoveries']:
                print(f"  • {article['title'][:60]}")
                print(f"    URL: {article['url']}")
                print(f"    Created: {article['created']}")
    
    elif args.multiple:
        # Тест с несколькими источниками
        await test_multiple_sources(limit_per_source=args.limit)
    
    elif args.url:
        # Тест с одним источником
        await test_single_source(args.url, limit=args.limit)
    
    else:
        # По умолчанию тестируем OpenAI
        default_url = "https://openai.com/news/"
        print(f"No URL specified, testing with default: {default_url}")
        await test_single_source(default_url, limit=args.limit)


if __name__ == '__main__':
    asyncio.run(main())