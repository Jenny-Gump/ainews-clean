#!/usr/bin/env python3
"""
Data Migration Script: SQLite to Supabase PostgreSQL
Migrates data from local SQLite databases to Supabase
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import time
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client, Client
from core.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataMigrator:
    def __init__(self):
        """Initialize connections to SQLite and Supabase"""
        self.config = Config()
        
        # SQLite connections
        self.ainews_db = sqlite3.connect('../data/ainews.db')
        self.ainews_db.row_factory = sqlite3.Row
        self.monitoring_db = sqlite3.connect('../data/monitoring.db')
        self.monitoring_db.row_factory = sqlite3.Row
        
        # Supabase connection
        self.supabase: Client = create_client(
            self.config.SUPABASE_URL,
            self.config.SUPABASE_KEY
        )
        
        # Migration statistics
        self.stats = {
            'total_records': 0,
            'migrated_records': 0,
            'failed_records': 0,
            'tables': {}
        }
        
        self.start_time = time.time()
    
    def close_connections(self):
        """Close database connections"""
        self.ainews_db.close()
        self.monitoring_db.close()
    
    def convert_datetime(self, dt_string: Optional[str]) -> Optional[str]:
        """Convert SQLite datetime to PostgreSQL timestamp with timezone"""
        if not dt_string:
            return None
        try:
            # Handle various datetime formats
            if 'T' in dt_string:
                # ISO format
                dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            else:
                # SQLite format
                dt = datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
            return dt.isoformat() + 'Z'
        except Exception as e:
            logger.warning(f"Failed to convert datetime '{dt_string}': {e}")
            return dt_string
    
    def convert_json(self, json_string: Optional[str]) -> Optional[Dict]:
        """Convert JSON string to dictionary for JSONB"""
        if not json_string:
            return None
        try:
            if isinstance(json_string, str):
                return json.loads(json_string)
            return json_string
        except Exception as e:
            logger.warning(f"Failed to parse JSON: {e}")
            return None
    
    def batch_insert(self, table: str, records: List[Dict], batch_size: int = 100) -> Tuple[int, int]:
        """Insert records in batches to Supabase"""
        success_count = 0
        error_count = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            try:
                result = self.supabase.table(table).insert(batch).execute()
                success_count += len(batch)
                logger.info(f"  Inserted batch {i//batch_size + 1}: {len(batch)} records")
            except Exception as e:
                error_count += len(batch)
                logger.error(f"  Failed to insert batch {i//batch_size + 1}: {e}")
                # Try individual inserts for failed batch
                for record in batch:
                    try:
                        self.supabase.table(table).insert(record).execute()
                        success_count += 1
                        error_count -= 1
                    except Exception as e2:
                        logger.error(f"    Failed individual insert: {e2}")
        
        return success_count, error_count
    
    def migrate_sources(self) -> Dict[str, Any]:
        """Migrate sources table"""
        logger.info("Migrating sources...")
        cursor = self.ainews_db.cursor()
        
        # Get all sources
        cursor.execute("SELECT * FROM sources")
        sources = cursor.fetchall()
        
        records = []
        for source in sources:
            record = {
                'id': source['id'],
                'name': source['name'],
                'category': source['category'],
                'rss_url': source['rss_url'],
                'language': source['language'],
                'active': bool(source['active']),
                'priority': source['priority'],
                'check_frequency_minutes': source['check_frequency_minutes'],
                'last_checked': self.convert_datetime(source['last_checked']),
                'last_error': source['last_error'],
                'error_count': source['error_count'],
                'success_count': source['success_count'],
                'article_count': source['article_count'],
                'average_articles_per_day': source['average_articles_per_day'],
                'created_at': self.convert_datetime(source['created_at']),
                'updated_at': self.convert_datetime(source['updated_at'])
            }
            records.append(record)
        
        success, errors = self.batch_insert('sources', records)
        
        return {
            'table': 'sources',
            'total': len(sources),
            'migrated': success,
            'failed': errors
        }
    
    def migrate_articles(self) -> Dict[str, Any]:
        """Migrate articles table"""
        logger.info("Migrating articles...")
        cursor = self.ainews_db.cursor()
        
        # Get all articles
        cursor.execute("SELECT * FROM articles")
        articles = cursor.fetchall()
        
        records = []
        for article in articles:
            record = {
                'id': article['id'],
                'source_id': article['source_id'],
                'url': article['url'],
                'title': article['title'],
                'author': article['author'],
                'published_date': self.convert_datetime(article['published_date']),
                'discovered_at': self.convert_datetime(article['discovered_at']),
                'content_raw': article['content_raw'],
                'content_markdown': article['content_markdown'],
                'summary': article['summary'],
                'key_points': self.convert_json(article['key_points']),
                'sentiment_score': article['sentiment_score'],
                'category': article['category'],
                'tags': self.convert_json(article['tags']),
                'language': article['language'],
                'word_count': article['word_count'],
                'reading_time': article['reading_time'],
                'is_translated': bool(article['is_translated']) if article['is_translated'] is not None else False,
                'translated_title': article['translated_title'],
                'translated_content': article['translated_content'],
                'translated_summary': article['translated_summary'],
                'translated_key_points': self.convert_json(article['translated_key_points']),
                'translation_model': article['translation_model'],
                'translation_date': self.convert_datetime(article['translation_date']),
                'wordpress_id': article['wordpress_id'],
                'wordpress_url': article['wordpress_url'],
                'wordpress_status': article['wordpress_status'],
                'wordpress_published_date': self.convert_datetime(article['wordpress_published_date']),
                'wordpress_featured_media': article['wordpress_featured_media'],
                'processing_status': article['processing_status'],
                'processing_error': article['processing_error'],
                'processing_attempts': article['processing_attempts'],
                'metadata': self.convert_json(article['metadata']),
                'created_at': self.convert_datetime(article['created_at']),
                'updated_at': self.convert_datetime(article['updated_at'])
            }
            records.append(record)
        
        success, errors = self.batch_insert('articles', records)
        
        return {
            'table': 'articles',
            'total': len(articles),
            'migrated': success,
            'failed': errors
        }
    
    def migrate_media_files(self) -> Dict[str, Any]:
        """Migrate media_files table"""
        logger.info("Migrating media_files...")
        cursor = self.ainews_db.cursor()
        
        cursor.execute("SELECT * FROM media_files")
        media_files = cursor.fetchall()
        
        records = []
        for media in media_files:
            record = {
                'id': media['id'],
                'article_id': media['article_id'],
                'url': media['url'],
                'type': media['type'],
                'alt_text': media['alt_text'],
                'caption': media['caption'],
                'width': media['width'],
                'height': media['height'],
                'file_size': media['file_size'],
                'mime_type': media['mime_type'],
                'local_path': media['local_path'],
                'wordpress_media_id': media['wordpress_media_id'],
                'wordpress_url': media['wordpress_url'],
                'is_featured': bool(media['is_featured']) if media['is_featured'] is not None else False,
                'processing_status': media['processing_status'],
                'metadata': self.convert_json(media['metadata']),
                'created_at': self.convert_datetime(media['created_at'])
            }
            records.append(record)
        
        success, errors = self.batch_insert('media_files', records)
        
        return {
            'table': 'media_files',
            'total': len(media_files),
            'migrated': success,
            'failed': errors
        }
    
    def migrate_wordpress_articles(self) -> Dict[str, Any]:
        """Migrate wordpress_articles table"""
        logger.info("Migrating wordpress_articles...")
        cursor = self.ainews_db.cursor()
        
        cursor.execute("SELECT * FROM wordpress_articles")
        wp_articles = cursor.fetchall()
        
        records = []
        for wp in wp_articles:
            record = {
                'id': wp['id'],
                'article_id': wp['article_id'],
                'wordpress_id': wp['wordpress_id'],
                'wordpress_url': wp['wordpress_url'],
                'wordpress_slug': wp['wordpress_slug'],
                'wordpress_status': wp['wordpress_status'],
                'wordpress_categories': self.convert_json(wp['wordpress_categories']),
                'wordpress_tags': self.convert_json(wp['wordpress_tags']),
                'wordpress_featured_media': wp['wordpress_featured_media'],
                'wordpress_author': wp['wordpress_author'],
                'seo_title': wp['seo_title'],
                'seo_description': wp['seo_description'],
                'seo_keywords': self.convert_json(wp['seo_keywords']),
                'published_date': self.convert_datetime(wp['published_date']),
                'modified_date': self.convert_datetime(wp['modified_date']),
                'sync_status': wp['sync_status'],
                'last_sync': self.convert_datetime(wp['last_sync']),
                'metadata': self.convert_json(wp['metadata']),
                'created_at': self.convert_datetime(wp['created_at']),
                'updated_at': self.convert_datetime(wp['updated_at'])
            }
            records.append(record)
        
        success, errors = self.batch_insert('wordpress_articles', records)
        
        return {
            'table': 'wordpress_articles',
            'total': len(wp_articles),
            'migrated': success,
            'failed': errors
        }
    
    def migrate_related_links(self) -> Dict[str, Any]:
        """Migrate related_links table"""
        logger.info("Migrating related_links...")
        cursor = self.ainews_db.cursor()
        
        cursor.execute("SELECT * FROM related_links")
        links = cursor.fetchall()
        
        records = []
        for link in links:
            record = {
                'id': link['id'],
                'article_id': link['article_id'],
                'url': link['url'],
                'title': link['title'],
                'description': link['description'],
                'domain': link['domain'],
                'link_type': link['link_type'],
                'relevance_score': link['relevance_score'],
                'created_at': self.convert_datetime(link['created_at'])
            }
            records.append(record)
        
        success, errors = self.batch_insert('related_links', records)
        
        return {
            'table': 'related_links',
            'total': len(links),
            'migrated': success,
            'failed': errors
        }
    
    def migrate_tracked_articles(self) -> Dict[str, Any]:
        """Migrate tracked_articles table"""
        logger.info("Migrating tracked_articles...")
        cursor = self.ainews_db.cursor()
        
        cursor.execute("SELECT * FROM tracked_articles")
        tracked = cursor.fetchall()
        
        records = []
        for track in tracked:
            record = {
                'id': track['id'],
                'article_id': track['article_id'],
                'url': track['url'],
                'title': track['title'],
                'hash': track['hash'],
                'first_seen': self.convert_datetime(track['first_seen']),
                'last_seen': self.convert_datetime(track['last_seen']),
                'seen_count': track['seen_count'],
                'source_names': track['source_names'],
                'is_duplicate': bool(track['is_duplicate']) if track['is_duplicate'] is not None else False,
                'duplicate_of': track['duplicate_of'],
                'created_at': self.convert_datetime(track['created_at']),
                'updated_at': self.convert_datetime(track['updated_at'])
            }
            records.append(record)
        
        success, errors = self.batch_insert('tracked_articles', records)
        
        return {
            'table': 'tracked_articles',
            'total': len(tracked),
            'migrated': success,
            'failed': errors
        }
    
    def migrate_tracked_urls(self) -> Dict[str, Any]:
        """Migrate tracked_urls table"""
        logger.info("Migrating tracked_urls...")
        cursor = self.ainews_db.cursor()
        
        cursor.execute("SELECT * FROM tracked_urls")
        urls = cursor.fetchall()
        
        records = []
        for url in urls:
            record = {
                'id': url['id'],
                'url': url['url'],
                'normalized_url': url['normalized_url'],
                'domain': url['domain'],
                'path': url['path'],
                'query_params': url['query_params'],
                'first_seen': self.convert_datetime(url['first_seen']),
                'last_seen': self.convert_datetime(url['last_seen']),
                'seen_count': url['seen_count'],
                'source_ids': self.convert_json(url['source_ids']),
                'article_ids': self.convert_json(url['article_ids']),
                'is_article': bool(url['is_article']) if url['is_article'] is not None else False,
                'is_processed': bool(url['is_processed']) if url['is_processed'] is not None else False,
                'metadata': self.convert_json(url['metadata']),
                'created_at': self.convert_datetime(url['created_at']),
                'updated_at': self.convert_datetime(url['updated_at'])
            }
            records.append(record)
        
        success, errors = self.batch_insert('tracked_urls', records, batch_size=50)
        
        return {
            'table': 'tracked_urls',
            'total': len(urls),
            'migrated': success,
            'failed': errors
        }
    
    def migrate_pipeline_operations(self) -> Dict[str, Any]:
        """Migrate pipeline_operations table"""
        logger.info("Migrating pipeline_operations...")
        cursor = self.ainews_db.cursor()
        
        cursor.execute("SELECT * FROM pipeline_operations")
        operations = cursor.fetchall()
        
        records = []
        for op in operations:
            record = {
                'id': op['id'],
                'operation_type': op['operation_type'],
                'article_id': op['article_id'],
                'source_id': op['source_id'],
                'status': op['status'],
                'started_at': self.convert_datetime(op['started_at']),
                'completed_at': self.convert_datetime(op['completed_at']),
                'duration_seconds': op['duration_seconds'],
                'error_message': op['error_message'],
                'retry_count': op['retry_count'],
                'metadata': self.convert_json(op['metadata']),
                'created_at': self.convert_datetime(op['created_at'])
            }
            records.append(record)
        
        success, errors = self.batch_insert('pipeline_operations', records)
        
        return {
            'table': 'pipeline_operations',
            'total': len(operations),
            'migrated': success,
            'failed': errors
        }
    
    def migrate_global_config(self) -> Dict[str, Any]:
        """Migrate global_config table"""
        logger.info("Migrating global_config...")
        cursor = self.ainews_db.cursor()
        
        cursor.execute("SELECT * FROM global_config")
        configs = cursor.fetchall()
        
        records = []
        for config in configs:
            record = {
                'id': config['id'],
                'key': config['key'],
                'value': config['value'],
                'description': config['description'],
                'data_type': config['data_type'],
                'category': config['category'],
                'is_sensitive': bool(config['is_sensitive']) if config['is_sensitive'] is not None else False,
                'created_at': self.convert_datetime(config['created_at']),
                'updated_at': self.convert_datetime(config['updated_at'])
            }
            records.append(record)
        
        success, errors = self.batch_insert('global_config', records)
        
        return {
            'table': 'global_config',
            'total': len(configs),
            'migrated': success,
            'failed': errors
        }
    
    def migrate_monitoring_tables(self) -> List[Dict[str, Any]]:
        """Migrate all monitoring tables"""
        results = []
        
        monitoring_tables = [
            'performance_metrics',
            'source_metrics', 
            'article_stats',
            'memory_metrics',
            'system_metrics',
            'error_logs',
            'api_cost_tracking'
        ]
        
        for table_name in monitoring_tables:
            try:
                logger.info(f"Migrating {table_name}...")
                cursor = self.monitoring_db.cursor()
                
                # Get sample of recent records (last 7 days)
                if table_name in ['performance_metrics', 'source_metrics', 'system_metrics']:
                    cursor.execute(f"""
                        SELECT * FROM {table_name} 
                        WHERE datetime(timestamp) > datetime('now', '-7 days')
                        ORDER BY timestamp DESC
                        LIMIT 1000
                    """)
                else:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 1000")
                
                rows = cursor.fetchall()
                
                if not rows:
                    results.append({
                        'table': table_name,
                        'total': 0,
                        'migrated': 0,
                        'failed': 0
                    })
                    continue
                
                # Convert rows to records based on table structure
                records = []
                for row in rows:
                    record = {}
                    for key in row.keys():
                        value = row[key]
                        # Convert datetime fields
                        if 'timestamp' in key or 'date' in key or '_at' in key:
                            value = self.convert_datetime(value)
                        # Convert JSON fields
                        elif 'metadata' in key or 'data' in key or 'config' in key:
                            value = self.convert_json(value)
                        # Convert boolean fields
                        elif isinstance(value, int) and key in ['is_active', 'is_enabled', 'success']:
                            value = bool(value)
                        
                        record[key] = value
                    records.append(record)
                
                success, errors = self.batch_insert(table_name, records, batch_size=50)
                
                results.append({
                    'table': table_name,
                    'total': len(rows),
                    'migrated': success,
                    'failed': errors
                })
                
            except Exception as e:
                logger.error(f"Failed to migrate {table_name}: {e}")
                results.append({
                    'table': table_name,
                    'total': 0,
                    'migrated': 0,
                    'failed': 0,
                    'error': str(e)
                })
        
        return results
    
    def run_migration(self):
        """Run complete migration process"""
        logger.info("="*60)
        logger.info("Starting SQLite to Supabase Data Migration")
        logger.info("="*60)
        
        all_results = []
        
        try:
            # Phase 1: Independent tables
            logger.info("\n--- Phase 1: Independent Tables ---")
            all_results.append(self.migrate_sources())
            all_results.append(self.migrate_global_config())
            
            # Phase 2: Articles (depends on sources)
            logger.info("\n--- Phase 2: Articles ---")
            all_results.append(self.migrate_articles())
            
            # Phase 3: Dependent on articles
            logger.info("\n--- Phase 3: Article Dependencies ---")
            all_results.append(self.migrate_media_files())
            all_results.append(self.migrate_wordpress_articles())
            all_results.append(self.migrate_related_links())
            all_results.append(self.migrate_tracked_articles())
            
            # Phase 4: Other tables
            logger.info("\n--- Phase 4: Other Tables ---")
            all_results.append(self.migrate_tracked_urls())
            all_results.append(self.migrate_pipeline_operations())
            
            # Phase 5: Monitoring tables
            logger.info("\n--- Phase 5: Monitoring Tables ---")
            monitoring_results = self.migrate_monitoring_tables()
            all_results.extend(monitoring_results)
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            self.close_connections()
        
        # Calculate final statistics
        total_migrated = sum(r.get('migrated', 0) for r in all_results)
        total_failed = sum(r.get('failed', 0) for r in all_results)
        total_records = sum(r.get('total', 0) for r in all_results)
        
        elapsed_time = time.time() - self.start_time
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("MIGRATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Total Records: {total_records}")
        logger.info(f"Successfully Migrated: {total_migrated}")
        logger.info(f"Failed: {total_failed}")
        logger.info(f"Success Rate: {(total_migrated/total_records*100):.2f}%")
        logger.info(f"Total Time: {elapsed_time:.2f} seconds")
        logger.info("="*60)
        
        # Print table details
        logger.info("\nTable Details:")
        for result in all_results:
            table = result.get('table', 'unknown')
            total = result.get('total', 0)
            migrated = result.get('migrated', 0)
            failed = result.get('failed', 0)
            
            status = "✓" if failed == 0 else "✗"
            logger.info(f"  {status} {table}: {migrated}/{total} migrated, {failed} failed")
            
            if 'error' in result:
                logger.info(f"    Error: {result['error']}")
        
        return {
            'success': total_failed == 0,
            'statistics': {
                'total_records': total_records,
                'migrated': total_migrated,
                'failed': total_failed,
                'elapsed_time': elapsed_time
            },
            'tables': all_results
        }


if __name__ == "__main__":
    migrator = DataMigrator()
    result = migrator.run_migration()
    
    # Save results to file
    with open('migration_results.json', 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    if result['success']:
        logger.info("\n✅ Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n❌ Migration completed with errors!")
        sys.exit(1)