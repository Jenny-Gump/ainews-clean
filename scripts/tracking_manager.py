#!/usr/bin/env python3
"""
Tracking Manager - управление системой отслеживания изменений
Интегрирует sources.txt и tracking_sources.json с системой ChangeMonitor
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app_logging import get_logger
from core.database import Database
from services.change_monitor import ChangeMonitor


class TrackingManager:
    """Менеджер для управления отслеживанием изменений"""
    
    def __init__(self):
        self.logger = get_logger('scripts.tracking_manager')
        self.db = Database()
        self.monitor = ChangeMonitor()
        self.sources_file = Path(__file__).parent.parent / 'data' / 'tracking_sources.json'
        
    def load_tracking_sources(self) -> Dict:
        """Загружает источники из tracking_sources.json"""
        if not self.sources_file.exists():
            self.logger.error(f"File not found: {self.sources_file}")
            return {"tracking_sources": [], "settings": {}}
            
        with open(self.sources_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def add_sources_to_db(self, sources: List[Dict]) -> int:
        """Добавляет источники в БД если их там нет"""
        added = 0
        
        for source in sources:
            try:
                # Check if source exists
                with self.db.get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT source_id FROM sources WHERE source_id = ?",
                        (source['source_id'],)
                    )
                    exists = cursor.fetchone()
                
                if not exists:
                    # Add new source
                    with self.db.get_connection() as conn:
                        conn.execute("""
                            INSERT INTO sources (
                                source_id, name, url, type, has_rss, rss_url, 
                                category, validation_status
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            source['source_id'],
                            source['name'],
                            source['url'],
                            source.get('type', 'web'),
                            1,  # has_rss
                            source.get('rss_url', ''),
                            source.get('category', 'general'),
                            'active'
                        ))
                    added += 1
                    self.logger.info(f"Added source: {source['name']}")
                else:
                    # Update RSS URL if needed
                    if source.get('rss_url'):
                        with self.db.get_connection() as conn:
                            conn.execute("""
                                UPDATE sources 
                                SET rss_url = ?, has_rss = 1
                                WHERE source_id = ?
                            """, (source['rss_url'], source['source_id']))
                        self.logger.debug(f"Updated RSS URL for: {source['name']}")
                        
            except Exception as e:
                self.logger.error(f"Error adding source {source.get('name', 'unknown')}: {e}")
                
        return added
    
    async def scan_all_sources(self, limit_per_source: int = 20) -> Dict:
        """Сканирует все активные источники с RSS"""
        results = {
            'sources_scanned': 0,
            'total_new': 0,
            'total_changed': 0,
            'total_unchanged': 0,
            'total_errors': 0,
            'details': []
        }
        
        # Get all sources with RSS
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT source_id, name, rss_url 
                FROM sources 
                WHERE has_rss = 1 
                AND rss_url IS NOT NULL 
                AND rss_url != ''
                AND validation_status = 'active'
            """)
            sources = cursor.fetchall()
        
        self.logger.info(f"Found {len(sources)} active sources with RSS")
        
        for source_id, name, rss_url in sources:
            self.logger.info(f"Scanning: {name}")
            
            try:
                # Scan source
                scan_results = await self.monitor.scan_source(rss_url, limit=limit_per_source)
                
                # Update totals
                results['sources_scanned'] += 1
                results['total_new'] += len(scan_results['new'])
                results['total_changed'] += len(scan_results['changed'])
                results['total_unchanged'] += len(scan_results['unchanged'])
                results['total_errors'] += len(scan_results['errors'])
                
                # Add details
                results['details'].append({
                    'source_id': source_id,
                    'name': name,
                    'new': len(scan_results['new']),
                    'changed': len(scan_results['changed']),
                    'unchanged': len(scan_results['unchanged']),
                    'errors': len(scan_results['errors'])
                })
                
                # Update source last check
                with self.db.get_connection() as conn:
                    conn.execute("""
                        UPDATE sources 
                        SET last_rss_check = CURRENT_TIMESTAMP
                        WHERE source_id = ?
                    """, (source_id,))
                
                # Small delay between sources
                await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error scanning {name}: {e}")
                results['details'].append({
                    'source_id': source_id,
                    'name': name,
                    'error': str(e)
                })
        
        return results
    
    async def export_ready_articles(self) -> Dict:
        """Экспортирует все готовые статьи в основную БД"""
        return await self.monitor.export_to_main()
    
    def get_stats(self) -> Dict:
        """Получает статистику системы отслеживания"""
        stats = self.monitor.get_tracking_stats()
        
        # Add source stats
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM sources 
                WHERE has_rss = 1 AND validation_status = 'active'
            """)
            stats['active_sources'] = cursor.fetchone()[0]
            
            cursor = conn.execute("""
                SELECT COUNT(*) FROM sources 
                WHERE has_rss = 1
            """)
            stats['total_sources'] = cursor.fetchone()[0]
        
        return stats


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Tracking Manager')
    parser.add_argument('--init', action='store_true', help='Initialize sources from JSON')
    parser.add_argument('--scan', action='store_true', help='Scan all sources')
    parser.add_argument('--scan-limit', type=int, default=20, help='Articles per source (default: 20)')
    parser.add_argument('--export', action='store_true', help='Export ready articles')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--full-cycle', action='store_true', help='Run full cycle: scan + export')
    
    args = parser.parse_args()
    
    manager = TrackingManager()
    
    if args.init:
        print("\n📚 Initializing sources from tracking_sources.json...")
        data = manager.load_tracking_sources()
        sources = data.get('tracking_sources', [])
        
        if sources:
            added = manager.add_sources_to_db(sources)
            print(f"✅ Added {added} new sources to database")
            print(f"📊 Total sources: {len(sources)}")
        else:
            print("❌ No sources found in tracking_sources.json")
    
    elif args.scan:
        print(f"\n🔍 Scanning all active sources (limit: {args.scan_limit} per source)...")
        results = await manager.scan_all_sources(limit_per_source=args.scan_limit)
        
        print(f"\n📊 SCAN RESULTS:")
        print(f"  Sources scanned: {results['sources_scanned']}")
        print(f"  ✅ New articles:  {results['total_new']}")
        print(f"  🔄 Changed:       {results['total_changed']}")
        print(f"  ⚪ Unchanged:     {results['total_unchanged']}")
        print(f"  ❌ Errors:        {results['total_errors']}")
        
        if results['details']:
            print("\n📋 Per source breakdown:")
            for detail in results['details']:
                if 'error' in detail:
                    print(f"  ❌ {detail['name']}: ERROR - {detail['error']}")
                else:
                    print(f"  • {detail['name']}: "
                          f"new={detail['new']}, "
                          f"changed={detail['changed']}, "
                          f"unchanged={detail['unchanged']}")
    
    elif args.export:
        print("\n📤 Exporting ready articles to main database...")
        results = await manager.export_ready_articles()
        
        print(f"\n✅ Exported: {results['total_exported']} articles")
        if results['duplicates']:
            print(f"⚠️  Duplicates skipped: {len(results['duplicates'])}")
        if results['errors']:
            print(f"❌ Errors: {len(results['errors'])}")
    
    elif args.stats:
        print("\n📊 TRACKING SYSTEM STATISTICS:")
        stats = manager.get_stats()
        
        print(f"\n📚 Sources:")
        print(f"  Total sources:    {stats.get('total_sources', 0)}")
        print(f"  Active sources:   {stats.get('active_sources', 0)}")
        
        print(f"\n📄 Tracked Articles:")
        print(f"  Total tracked:    {stats.get('total_tracked', 0)}")
        print(f"  Pending export:   {stats.get('pending_export', 0)}")
        
        if stats.get('by_status'):
            print(f"\n📊 By Status:")
            for status, count in stats['by_status'].items():
                print(f"  {status}: {count}")
        
        if stats.get('by_source'):
            print(f"\n📋 By Source:")
            for source, count in sorted(stats['by_source'].items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {source}: {count}")
    
    elif args.full_cycle:
        print("\n🔄 Running full cycle: scan + export")
        
        # Scan
        print("\n1️⃣ Scanning sources...")
        scan_results = await manager.scan_all_sources(limit_per_source=args.scan_limit)
        print(f"  ✅ Found {scan_results['total_new']} new articles")
        print(f"  🔄 Found {scan_results['total_changed']} changed articles")
        
        # Export
        if scan_results['total_new'] > 0 or scan_results['total_changed'] > 0:
            print("\n2️⃣ Exporting to main database...")
            export_results = await manager.export_ready_articles()
            print(f"  ✅ Exported {export_results['total_exported']} articles")
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