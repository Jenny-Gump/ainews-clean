#!/usr/bin/env python3
"""
Regular Scan Runner
Скрипт для регулярного сканирования источников
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Добавляем корневую папку в PATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from change_tracking import ChangeMonitor


async def run_full_scan(batch_size: int = 5, max_sources: int = None):
    """Run full scan of all sources"""
    monitor = ChangeMonitor()
    
    print(f"🚀 Starting Change Tracking Scan")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📦 Batch size: {batch_size}")
    if max_sources:
        print(f"🔢 Max sources: {max_sources}")
    print("=" * 60)
    
    # Запускаем сканирование
    results = await monitor.scan_sources_batch(
        batch_size=batch_size,
        limit=max_sources
    )
    
    # Выводим результаты
    print(f"\n✅ Scan completed!")
    print(f"📊 Results:")
    print(f"  📋 Total scanned: {results['total']}")
    print(f"  🆕 New pages: {results['new']}")
    print(f"  🔄 Changed pages: {results['changed']}")
    print(f"  ⚪ Unchanged pages: {results['unchanged']}")
    print(f"  ❌ Errors: {results['errors']}")
    
    # Показываем детали новых и измененных
    new_and_changed = [
        detail for detail in results['details']
        if detail['status'] in ['new', 'changed']
    ]
    
    if new_and_changed:
        print(f"\n🔥 New and Changed ({len(new_and_changed)}):")
        for detail in new_and_changed:
            status_icon = '🆕' if detail['status'] == 'new' else '🔄'
            url_display = detail['url'][:50] + '...' if len(detail['url']) > 50 else detail['url']
            print(f"  {status_icon} {url_display}")
            if detail.get('article_id'):
                print(f"     📝 Article ID: {detail['article_id']}")
    
    # Показываем ошибки
    errors = [detail for detail in results['details'] if detail['status'] == 'error']
    if errors:
        print(f"\n❌ Errors ({len(errors)}):")
        for detail in errors:
            url_display = detail['url'][:50] + '...' if len(detail['url']) > 50 else detail['url']
            error_short = detail.get('error', '')[:100] + '...' if len(detail.get('error', '')) > 100 else detail.get('error', '')
            print(f"  ❌ {url_display}")
            print(f"     {error_short}")
    
    return results


async def export_changes():
    """Export changes to main pipeline"""
    monitor = ChangeMonitor()
    
    print(f"📤 Checking for changes to export...")
    
    changed_articles = monitor.get_changed_articles()
    
    if not changed_articles:
        print("ℹ️ No changes to export.")
        return
    
    print(f"🔄 Found {len(changed_articles)} changed articles:")
    for article in changed_articles[:5]:  # Show first 5
        print(f"  📄 {article['title'][:50]}...")
        print(f"     🌐 {article['url'][:60]}...")
    
    if len(changed_articles) > 5:
        print(f"  ... and {len(changed_articles) - 5} more")
    
    # Export to main pipeline - use --change-tracking --export-articles command
    print(f"⚠️ Export to main pipeline not implemented yet")
    print(f"💡 Articles will remain marked as non-exported")


def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Change Tracking Scanner')
    parser.add_argument('--batch-size', type=int, default=5, help='Batch size for scanning')
    parser.add_argument('--max-sources', type=int, help='Maximum number of sources to scan')
    parser.add_argument('--export', action='store_true', help='Export changes after scan')
    parser.add_argument('--export-only', action='store_true', help='Only export, skip scanning')
    
    args = parser.parse_args()
    
    async def run():
        if args.export_only:
            await export_changes()
        else:
            # Run scan
            await run_full_scan(
                batch_size=args.batch_size,
                max_sources=args.max_sources
            )
            
            # Export if requested
            if args.export:
                print("\n" + "="*60)
                await export_changes()
    
    asyncio.run(run())


if __name__ == "__main__":
    main()