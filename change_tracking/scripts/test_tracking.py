#!/usr/bin/env python3
"""
Test Change Tracking System
Объединенный тестовый скрипт для отслеживания изменений
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корневую папку в PATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from change_tracking import ChangeMonitor


async def test_single_page(url: str):
    """Test change tracking for single page"""
    monitor = ChangeMonitor()
    
    print(f"\n{'='*60}")
    print(f"Testing Change Tracking: {url}")
    print(f"{'='*60}")
    
    result = await monitor.scan_webpage(url)
    
    print(f"\nResult:")
    print(f"  Status: {result['status']}")
    print(f"  Change detected: {result['change_detected']}")
    if result.get('article_id'):
        print(f"  Article ID: {result['article_id']}")
    if result.get('error'):
        print(f"  Error: {result['error']}")
    
    return result


async def test_sources_file(limit: int = 3, batch_size: int = 2):
    """Test with sources from sources.txt"""
    monitor = ChangeMonitor()
    
    # Load sources
    urls = monitor.load_sources_from_file()
    
    if not urls:
        print("❌ No URLs found in change_tracking/sources.txt")
        return
    
    print(f"\n{'='*60}")
    print(f"Testing {limit} sources from sources.txt")
    print(f"Total sources available: {len(urls)}")
    print(f"Batch size: {batch_size}")
    print(f"{'='*60}")
    
    # Test with batching
    results = await monitor.scan_sources_batch(batch_size=batch_size, limit=limit)
    
    print_results_summary(results)
    print_results_details(results)


def print_results_summary(results: dict):
    """Print summary of results"""
    print(f"\n📊 Summary:")
    print(f"  Total: {results['total']}")
    print(f"  New: {results['new']}")
    print(f"  Changed: {results['changed']}")
    print(f"  Unchanged: {results['unchanged']}")
    print(f"  Errors: {results['errors']}")


def print_results_details(results: dict, show_all: bool = False):
    """Print detailed results"""
    print(f"\n📋 Details:")
    
    for detail in results['details']:
        url_display = detail['url'][:50] + '...' if len(detail['url']) > 50 else detail['url']
        status_icon = {
            'new': '🆕',
            'changed': '🔄',
            'unchanged': '⚪',
            'error': '❌'
        }.get(detail['status'], '❓')
        
        print(f"  {status_icon} {url_display}")
        print(f"    Status: {detail['status']}")
        
        if detail.get('article_id'):
            print(f"    Article ID: {detail['article_id']}")
        
        if detail.get('error') and (show_all or detail['status'] == 'error'):
            print(f"    Error: {detail['error'][:100]}...")


async def show_stats():
    """Show tracking statistics"""
    monitor = ChangeMonitor()
    stats = monitor.get_tracking_stats()
    
    print(f"\n{'='*60}")
    print(f"📊 TRACKING STATISTICS")
    print(f"{'='*60}")
    
    if 'error' in stats:
        print(f"❌ Error: {stats['error']}")
        return
    
    print(f"📋 Total tracked: {stats.get('total_tracked', 0)}")
    
    # By status
    if stats.get('by_status'):
        print(f"\n📈 By status:")
        status_icons = {
            'new': '🆕',
            'changed': '🔄',
            'unchanged': '⚪',
            'unknown': '❓'
        }
        for status, count in stats['by_status'].items():
            icon = status_icons.get(status, '📄')
            print(f"  {icon} {status}: {count}")
    
    # By source
    if stats.get('by_source'):
        print(f"\n🌐 By source:")
        for source, count in list(stats['by_source'].items())[:10]:  # Top 10
            print(f"  📰 {source}: {count}")
    
    # Recent changes
    if stats.get('recent_changes'):
        print(f"\n🔥 Recent changes:")
        for change in stats['recent_changes'][:5]:  # Last 5
            url_display = change['url'][:40] + '...' if len(change['url']) > 40 else change['url']
            print(f"  📄 {url_display}")
            print(f"    Status: {change['status']}, Checked: {change['checked']}")


async def show_changed_articles(limit: int = 10):
    """Show articles with changes"""
    monitor = ChangeMonitor()
    
    changed = monitor.get_changed_articles(limit)
    
    print(f"\n{'='*60}")
    print(f"🔄 CHANGED ARTICLES ({len(changed)})")
    print(f"{'='*60}")
    
    if not changed:
        print("No changed articles found.")
        return
    
    for article in changed:
        url_display = article['url'][:50] + '...' if len(article['url']) > 50 else article['url']
        print(f"\n📄 {article['title'][:60]}...")
        print(f"  🌐 {url_display}")
        print(f"  🔄 Status: {article['change_status']}")
        print(f"  🕒 Last checked: {article['last_checked']}")
        print(f"  🆔 Article ID: {article['article_id']}")


def print_sources_list():
    """Print list of sources"""
    monitor = ChangeMonitor()
    urls = monitor.load_sources_from_file()
    
    print(f"\n{'='*60}")
    print(f"📰 SOURCES LIST ({len(urls)} sources)")
    print(f"{'='*60}")
    
    for i, url in enumerate(urls, 1):
        print(f"{i:2d}. {url}")


async def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Change Tracking Test System')
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--url', type=str, help='Single URL to test')
    group.add_argument('--sources', action='store_true', help='Test with sources.txt')
    group.add_argument('--stats', action='store_true', help='Show statistics')
    group.add_argument('--changed', action='store_true', help='Show changed articles')
    group.add_argument('--list-sources', action='store_true', help='List all sources')
    
    parser.add_argument('--limit', type=int, default=3, help='Number of sources to test')
    parser.add_argument('--batch-size', type=int, default=2, help='Batch size for sources scan')
    parser.add_argument('--show-all', action='store_true', help='Show all details')
    
    args = parser.parse_args()
    
    if args.url:
        await test_single_page(args.url)
    elif args.sources:
        await test_sources_file(args.limit, args.batch_size)
    elif args.stats:
        await show_stats()
    elif args.changed:
        await show_changed_articles(args.limit)
    elif args.list_sources:
        print_sources_list()
    else:
        # Default behavior - show stats
        print("🔍 Default: Showing current statistics...")
        await show_stats()
        
        print(f"\n💡 Usage examples:")
        print(f"  Test single URL: python scripts/test_tracking.py --url 'https://openai.com/news/'")
        print(f"  Test sources: python scripts/test_tracking.py --sources --limit 5 --batch-size 3")
        print(f"  Show stats: python scripts/test_tracking.py --stats")
        print(f"  Show changed: python scripts/test_tracking.py --changed")
        print(f"  List sources: python scripts/test_tracking.py --list-sources")


if __name__ == "__main__":
    asyncio.run(main())