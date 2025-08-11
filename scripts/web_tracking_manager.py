#!/usr/bin/env python3
"""
Web Tracking Manager
Управление мониторингом веб-страниц (не RSS!) из sources.txt
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict
from urllib.parse import urlparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app_logging import get_logger
from core.database import Database
from services.web_monitor import WebMonitor


class WebTrackingManager:
    """Менеджер для отслеживания изменений на веб-страницах"""
    
    def __init__(self):
        self.logger = get_logger('scripts.web_tracking_manager')
        self.db = Database()
        self.monitor = WebMonitor()
        self.sources_file = Path('/Users/skynet/Desktop/sources.txt')
    
    def load_web_sources(self) -> List[str]:
        """Загружает URL из sources.txt"""
        if not self.sources_file.exists():
            self.logger.error(f"File not found: {self.sources_file}")
            return []
        
        urls = []
        with open(self.sources_file, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url and not url.startswith('#'):
                    urls.append(url)
        
        return urls
    
    def init_sources_in_db(self, urls: List[str]) -> Dict[str, int]:
        """Инициализирует источники в БД"""
        stats = {'added': 0, 'updated': 0, 'skipped': 0}
        
        for url in urls:
            try:
                # Генерируем source_id из URL
                parsed = urlparse(url)
                domain = parsed.netloc.replace('www.', '')
                source_id = domain.replace('.', '_')
                
                # Генерируем имя
                name = domain.replace('.', ' ').title()
                if parsed.path and len(parsed.path) > 1:
                    path_part = parsed.path.strip('/').replace('/', ' - ').replace('-', ' ').title()
                    name = f"{name} - {path_part}"
                
                # Проверяем существование
                with self.db.get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT source_id FROM sources WHERE source_id = ?",
                        (source_id,)
                    )
                    exists = cursor.fetchone()
                
                if not exists:
                    # Добавляем новый источник
                    with self.db.get_connection() as conn:
                        conn.execute("""
                            INSERT INTO sources (
                                source_id, name, url, type,
                                has_rss, validation_status
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            source_id, name, url, 'web',
                            0,  # has_rss = False (это веб-страницы, не RSS)
                            'active'
                        ))
                    stats['added'] += 1
                    self.logger.info(f"✅ Added source: {name}")
                else:
                    stats['skipped'] += 1
                    self.logger.debug(f"⏭️ Source exists: {name}")
                    
            except Exception as e:
                self.logger.error(f"Error processing {url}: {e}")
        
        return stats
    
    async def monitor_all_sources(self, limit: int = 10) -> Dict:
        """Мониторит все веб-страницы из sources.txt"""
        urls = self.load_web_sources()
        
        if not urls:
            self.logger.error("No URLs found in sources.txt")
            return {'error': 'No URLs found'}
        
        self.logger.info(f"Monitoring {len(urls[:limit])} web pages...")
        
        # Мониторим страницы (ограничиваем количество)
        results = await self.monitor.monitor_multiple_pages(urls[:limit])
        
        return results
    
    async def monitor_single_source(self, url: str) -> Dict:
        """Мониторит одну веб-страницу"""
        self.logger.info(f"Monitoring single webpage: {url}")
        return await self.monitor.monitor_webpage(url)
    
    async def export_articles(self) -> Dict:
        """Экспортирует найденные статьи в основную БД"""
        return await self.monitor.export_to_main()
    
    def get_stats(self) -> Dict:
        """Получает статистику"""
        stats = {}
        
        with self.db.get_connection() as conn:
            # Всего отслеживаемых страниц
            cursor = conn.execute("SELECT COUNT(*) FROM tracked_articles")
            stats['total_tracked'] = cursor.fetchone()[0]
            
            # По статусам
            cursor = conn.execute("""
                SELECT change_status, COUNT(*) 
                FROM tracked_articles 
                GROUP BY change_status
            """)
            stats['by_status'] = dict(cursor.fetchall())
            
            # Не экспортированные
            cursor = conn.execute("""
                SELECT COUNT(*) FROM tracked_articles 
                WHERE change_detected = 1 AND exported_to_main = 0
            """)
            stats['pending_export'] = cursor.fetchone()[0]
            
            # Источники без RSS (веб-страницы)
            cursor = conn.execute("""
                SELECT COUNT(*) FROM sources 
                WHERE has_rss = 0 AND validation_status = 'active'
            """)
            stats['web_sources'] = cursor.fetchone()[0]
        
        return stats


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Web Tracking Manager')
    parser.add_argument('--init', action='store_true', 
                       help='Initialize web sources from sources.txt')
    parser.add_argument('--monitor', type=str, 
                       help='Monitor specific webpage URL')
    parser.add_argument('--monitor-all', action='store_true',
                       help='Monitor all sources from sources.txt')
    parser.add_argument('--limit', type=int, default=10,
                       help='Limit number of pages to monitor (default: 10)')
    parser.add_argument('--export', action='store_true',
                       help='Export found articles to main DB')
    parser.add_argument('--stats', action='store_true',
                       help='Show statistics')
    parser.add_argument('--full-cycle', action='store_true',
                       help='Run full cycle: monitor + export')
    
    args = parser.parse_args()
    
    manager = WebTrackingManager()
    
    if args.init:
        print("\n📚 Initializing web sources from sources.txt...")
        urls = manager.load_web_sources()
        
        if urls:
            print(f"Found {len(urls)} URLs in sources.txt")
            stats = manager.init_sources_in_db(urls)
            print(f"\n✅ Results:")
            print(f"  Added: {stats['added']}")
            print(f"  Skipped: {stats['skipped']}")
        else:
            print("❌ No URLs found in sources.txt")
    
    elif args.monitor:
        print(f"\n🔍 Monitoring webpage: {args.monitor}")
        results = await manager.monitor_single_source(args.monitor)
        
        print(f"\n📊 Results:")
        print(f"  Status: {results.get('status')}")
        print(f"  Articles found: {len(results.get('articles_found', []))}")
        print(f"  Changes detected: {len(results.get('changes_detected', []))}")
        
        if results.get('articles_found'):
            print(f"\n📰 Found articles:")
            for i, article in enumerate(results['articles_found'][:5], 1):
                print(f"  {i}. {article['title'][:60]}")
                print(f"     {article['url']}")
    
    elif args.monitor_all:
        print(f"\n🔍 Monitoring all sources (limit: {args.limit})...")
        results = await manager.monitor_all_sources(limit=args.limit)
        
        print(f"\n📊 Summary:")
        print(f"  Pages monitored: {results['total_monitored']}")
        print(f"  Articles found: {results['total_articles']}")
        print(f"  Changes detected: {results['total_changes']}")
        print(f"  Errors: {results['total_errors']}")
        
        if results.get('details'):
            print(f"\n📋 Per page breakdown:")
            for detail in results['details'][:10]:
                if detail.get('status') == 'error':
                    print(f"  ❌ {detail['url']}: ERROR")
                else:
                    print(f"  • {detail['url'][:50]}...")
                    print(f"    Articles: {len(detail.get('articles_found', []))}, "
                          f"Changes: {len(detail.get('changes_detected', []))}")
    
    elif args.export:
        print("\n📤 Exporting articles to main database...")
        results = await manager.export_articles()
        
        print(f"\n✅ Export results:")
        print(f"  Exported: {results['exported']}")
        print(f"  Duplicates: {results['duplicates']}")
        print(f"  Errors: {results['errors']}")
    
    elif args.stats:
        print("\n📊 WEB TRACKING STATISTICS:")
        stats = manager.get_stats()
        
        print(f"\n📄 Tracked Pages:")
        print(f"  Total tracked: {stats.get('total_tracked', 0)}")
        print(f"  Pending export: {stats.get('pending_export', 0)}")
        print(f"  Web sources: {stats.get('web_sources', 0)}")
        
        if stats.get('by_status'):
            print(f"\n📊 By Status:")
            for status, count in stats['by_status'].items():
                print(f"  {status}: {count}")
    
    elif args.full_cycle:
        print("\n🔄 Running full cycle: monitor + export")
        
        # Monitor
        print(f"\n1️⃣ Monitoring web pages (limit: {args.limit})...")
        monitor_results = await manager.monitor_all_sources(limit=args.limit)
        print(f"  Found {monitor_results['total_articles']} articles")
        print(f"  Detected {monitor_results['total_changes']} changes")
        
        # Export
        if monitor_results['total_articles'] > 0 or monitor_results['total_changes'] > 0:
            print("\n2️⃣ Exporting to main database...")
            export_results = await manager.export_articles()
            print(f"  Exported {export_results['exported']} articles")
        else:
            print("\n2️⃣ No articles to export")
        
        # Stats
        print("\n3️⃣ Final statistics:")
        stats = manager.get_stats()
        print(f"  Total tracked: {stats.get('total_tracked', 0)}")
        print(f"  Pending export: {stats.get('pending_export', 0)}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    asyncio.run(main())