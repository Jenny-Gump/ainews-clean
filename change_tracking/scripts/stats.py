#!/usr/bin/env python3
"""
Change Tracking Statistics
Просмотр статистики и управление данными
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Добавляем корневую папку в PATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from change_tracking import ChangeMonitor


def show_detailed_stats():
    """Show detailed statistics"""
    monitor = ChangeMonitor()
    stats = monitor.get_tracking_stats()
    
    print(f"{'='*80}")
    print(f"📊 CHANGE TRACKING STATISTICS")
    print(f"{'='*80}")
    print(f"⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if 'error' in stats:
        print(f"❌ Error getting stats: {stats['error']}")
        return
    
    # Общая статистика
    print(f"\n📋 OVERVIEW:")
    print(f"  📄 Total tracked pages: {stats.get('total_tracked', 0)}")
    
    # По статусам
    if stats.get('by_status'):
        print(f"\n📈 BY STATUS:")
        status_info = {
            'new': ('🆕', 'New pages discovered'),
            'changed': ('🔄', 'Pages with changes'),
            'unchanged': ('⚪', 'Pages without changes'),
            'unknown': ('❓', 'Unknown status')
        }
        
        total_status = sum(stats['by_status'].values())
        for status, count in stats['by_status'].items():
            icon, description = status_info.get(status, ('📄', 'Other'))
            percentage = (count / total_status * 100) if total_status > 0 else 0
            print(f"  {icon} {status.upper()}: {count} ({percentage:.1f}%) - {description}")
    
    # По источникам
    if stats.get('by_source'):
        print(f"\n🌐 BY SOURCE (Top 15):")
        sorted_sources = sorted(stats['by_source'].items(), key=lambda x: x[1], reverse=True)
        
        for i, (source, count) in enumerate(sorted_sources[:15], 1):
            print(f"  {i:2d}. {source}: {count} pages")
    
    # Последние изменения
    if stats.get('recent_changes'):
        print(f"\n🔥 RECENT CHANGES:")
        for i, change in enumerate(stats['recent_changes'], 1):
            url_display = change['url'][:60] + '...' if len(change['url']) > 60 else change['url']
            status_icon = '🆕' if change['status'] == 'new' else '🔄'
            
            # Парсим время
            try:
                if 'T' in change['checked']:  # ISO format
                    checked_time = datetime.fromisoformat(change['checked'].replace('Z', '+00:00'))
                else:  # Simple format
                    checked_time = datetime.fromisoformat(change['checked'])
                time_ago = datetime.now() - checked_time.replace(tzinfo=None)
                time_str = f"{time_ago.total_seconds() / 3600:.1f}h ago" if time_ago.total_seconds() > 3600 else f"{time_ago.total_seconds() / 60:.0f}m ago"
            except:
                time_str = change['checked']
            
            print(f"  {i:2d}. {status_icon} {url_display}")
            print(f"      ⏰ {time_str} ({change['status']})")


def show_changed_articles(limit: int = 20, show_content: bool = False):
    """Show articles with changes"""
    monitor = ChangeMonitor()
    changed = monitor.get_changed_articles(limit)
    
    print(f"{'='*80}")
    print(f"🔄 CHANGED ARTICLES ({len(changed)} found)")
    print(f"{'='*80}")
    
    if not changed:
        print("ℹ️ No changed articles found.")
        return
    
    for i, article in enumerate(changed, 1):
        print(f"\n{i}. 📄 {article['title']}")
        
        url_display = article['url'][:70] + '...' if len(article['url']) > 70 else article['url']
        print(f"   🌐 {url_display}")
        
        print(f"   🔄 Status: {article['change_status']}")
        print(f"   🆔 Article ID: {article['article_id']}")
        print(f"   🏷️ Source: {article['source_id']}")
        
        # Время
        try:
            if 'T' in article['last_checked']:
                checked_time = datetime.fromisoformat(article['last_checked'].replace('Z', '+00:00'))
                time_str = checked_time.strftime('%Y-%m-%d %H:%M')
            else:
                time_str = article['last_checked']
        except:
            time_str = str(article['last_checked'])
        
        print(f"   ⏰ Last checked: {time_str}")
        
        # Экспорт статус
        exported_icon = '✅' if article.get('exported_to_main') else '⏳'
        exported_text = 'Exported' if article.get('exported_to_main') else 'Not exported'
        print(f"   📤 Export: {exported_icon} {exported_text}")
        
        # Содержимое (если запрошено)
        if show_content and article.get('content'):
            content_preview = article['content'][:200] + '...' if len(article['content']) > 200 else article['content']
            print(f"   📝 Content preview: {content_preview}")


def cleanup_old_data(days: int = 30, dry_run: bool = True):
    """Clean up old tracking data"""
    monitor = ChangeMonitor()
    
    print(f"{'='*80}")
    print(f"🧹 CLEANUP OLD DATA")
    print(f"{'='*80}")
    print(f"🗓️ Removing records older than {days} days")
    
    if dry_run:
        print(f"⚠️ DRY RUN MODE - No data will be deleted")
        # Dry run logic not implemented - using real execution only
        print(f"💡 Use --execute to actually delete data")
    else:
        deleted_count = monitor.db.cleanup_old_records(days)
        print(f"✅ Deleted {deleted_count} old records")


def export_report(output_file: str = None):
    """Export statistics to file"""
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"change_tracking_report_{timestamp}.txt"
    
    monitor = ChangeMonitor()
    
    print(f"📄 Exporting report to: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Redirect stdout to file
        import contextlib
        
        with contextlib.redirect_stdout(f):
            show_detailed_stats()
            print("\n" + "="*80)
            show_changed_articles(limit=50)
    
    print(f"✅ Report exported successfully")


def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Change Tracking Statistics')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show detailed statistics')
    
    # Changed command
    changed_parser = subparsers.add_parser('changed', help='Show changed articles')
    changed_parser.add_argument('--limit', type=int, default=20, help='Number of articles to show')
    changed_parser.add_argument('--content', action='store_true', help='Show content preview')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old data')
    cleanup_parser.add_argument('--days', type=int, default=30, help='Days old to delete')
    cleanup_parser.add_argument('--execute', action='store_true', help='Actually delete (not dry run)')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export report to file')
    export_parser.add_argument('--output', type=str, help='Output filename')
    
    args = parser.parse_args()
    
    if args.command == 'stats' or not args.command:
        show_detailed_stats()
    elif args.command == 'changed':
        show_changed_articles(limit=args.limit, show_content=args.content)
    elif args.command == 'cleanup':
        cleanup_old_data(days=args.days, dry_run=not args.execute)
    elif args.command == 'export':
        export_report(args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()