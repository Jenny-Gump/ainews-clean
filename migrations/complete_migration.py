#!/usr/bin/env python3
"""
Complete migration script from SQLite to Supabase
Migrates all remaining data with proper error handling and logging
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database paths
SQLITE_DB = '/Users/skynet/Desktop/AI DEV/ainews-clean/data/ainews.db'
MONITORING_DB = '/Users/skynet/Desktop/AI DEV/ainews-clean/data/monitoring.db'

class DataMigrator:
    def __init__(self):
        self.sqlite_conn = sqlite3.connect(SQLITE_DB)
        self.sqlite_conn.row_factory = sqlite3.Row
        self.monitoring_conn = sqlite3.connect(MONITORING_DB)
        self.monitoring_conn.row_factory = sqlite3.Row
        
        self.stats = {
            'articles': {'total': 0, 'migrated': 0, 'errors': 0},
            'sources': {'total': 0, 'migrated': 0, 'errors': 0},
            'media_files': {'total': 0, 'migrated': 0, 'errors': 0},
            'wordpress_articles': {'total': 0, 'migrated': 0, 'errors': 0},
            'monitoring': {'total': 0, 'migrated': 0, 'errors': 0}
        }
    
    def get_missing_articles(self, existing_ids: List[str]) -> List[Dict]:
        """Get articles that are not yet in Supabase"""
        cursor = self.sqlite_conn.cursor()
        
        if existing_ids:
            placeholders = ','.join('?' * len(existing_ids))
            query = f"""
                SELECT * FROM articles 
                WHERE article_id NOT IN ({placeholders})
                ORDER BY created_at
            """
            cursor.execute(query, existing_ids)
        else:
            cursor.execute("SELECT * FROM articles ORDER BY created_at")
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_missing_sources(self, existing_ids: List[str]) -> List[Dict]:
        """Get sources that are not yet in Supabase"""
        cursor = self.sqlite_conn.cursor()
        
        if existing_ids:
            placeholders = ','.join('?' * len(existing_ids))
            query = f"""
                SELECT * FROM sources 
                WHERE source_id NOT IN ({placeholders})
                ORDER BY created_at
            """
            cursor.execute(query, existing_ids)
        else:
            cursor.execute("SELECT * FROM sources ORDER BY created_at")
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_media_files(self) -> List[Dict]:
        """Get all media files from SQLite"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT * FROM media_files ORDER BY created_at")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_wordpress_articles(self) -> List[Dict]:
        """Get all wordpress articles from SQLite"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT * FROM wordpress_articles ORDER BY created_at")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_monitoring_data(self, limit: int = 1000) -> Dict[str, List]:
        """Get recent monitoring data from monitoring.db"""
        cursor = self.monitoring_conn.cursor()
        
        monitoring_data = {}
        
        # Get table names
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        tables = [row['name'] for row in cursor.fetchall()]
        
        for table in tables:
            try:
                # Get recent records
                cursor.execute(f"""
                    SELECT * FROM {table} 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
                monitoring_data[table] = [dict(row) for row in cursor.fetchall()]
                logger.info(f"Found {len(monitoring_data[table])} records in monitoring.{table}")
            except Exception as e:
                logger.warning(f"Could not read monitoring table {table}: {e}")
                monitoring_data[table] = []
        
        return monitoring_data
    
    def prepare_article_batch(self, articles: List[Dict]) -> List[Dict]:
        """Prepare articles for batch insert to Supabase"""
        batch = []
        for article in articles:
            # Convert datetime strings if needed
            for date_field in ['published_date', 'created_at', 'parsed_at', 'deleted_at']:
                if article.get(date_field):
                    # Ensure it's in proper format
                    if isinstance(article[date_field], str) and 'T' not in article[date_field]:
                        article[date_field] = article[date_field].replace(' ', 'T')
            
            batch.append(article)
        
        return batch
    
    def prepare_media_batch(self, media_files: List[Dict]) -> List[Dict]:
        """Prepare media files for batch insert to Supabase"""
        batch = []
        for media in media_files:
            # Store original integer ID for reference
            media_copy = media.copy()
            media_copy['id_integer'] = media.get('id')
            
            # Remove the integer id field as Supabase uses UUID
            if 'id' in media_copy:
                del media_copy['id']
            
            # Convert datetime
            if media_copy.get('created_at'):
                if isinstance(media_copy['created_at'], str) and 'T' not in media_copy['created_at']:
                    media_copy['created_at'] = media_copy['created_at'].replace(' ', 'T')
            
            if media_copy.get('wp_uploaded_at'):
                if isinstance(media_copy['wp_uploaded_at'], str) and 'T' not in media_copy['wp_uploaded_at']:
                    media_copy['wp_uploaded_at'] = media_copy['wp_uploaded_at'].replace(' ', 'T')
            
            batch.append(media_copy)
        
        return batch
    
    def prepare_wordpress_batch(self, wp_articles: List[Dict]) -> List[Dict]:
        """Prepare wordpress articles for batch insert to Supabase"""
        batch = []
        for wp in wp_articles:
            wp_copy = wp.copy()
            
            # Store original integer ID
            wp_copy['id_integer'] = wp.get('id')
            
            # Remove integer id
            if 'id' in wp_copy:
                del wp_copy['id']
            
            # Map fields to Supabase schema
            wp_copy['title'] = wp.get('title', '')
            wp_copy['content'] = wp.get('content', '')
            wp_copy['excerpt'] = wp.get('excerpt', '')
            
            # Parse JSON fields if they're strings
            for json_field in ['categories', 'tags', 'images_data']:
                if wp_copy.get(json_field) and isinstance(wp_copy[json_field], str):
                    try:
                        wp_copy[json_field] = json.loads(wp_copy[json_field])
                    except:
                        logger.warning(f"Could not parse JSON field {json_field} for article {wp_copy.get('article_id')}")
            
            # Convert datetime fields
            for date_field in ['translated_at', 'created_at', 'updated_at']:
                if wp_copy.get(date_field):
                    if isinstance(wp_copy[date_field], str) and 'T' not in wp_copy[date_field]:
                        wp_copy[date_field] = wp_copy[date_field].replace(' ', 'T')
            
            batch.append(wp_copy)
        
        return batch
    
    def generate_migration_sql(self):
        """Generate SQL commands for migration - to be executed via MCP"""
        
        logger.info("Starting migration SQL generation...")
        
        # Get existing IDs from Supabase (you'll need to provide these)
        existing_article_ids = []  # Will be filled from Supabase query
        existing_source_ids = []   # Will be filled from Supabase query
        
        sql_commands = []
        
        # 1. Migrate missing sources
        logger.info("Preparing sources migration...")
        sources = self.get_missing_sources(existing_source_ids)
        self.stats['sources']['total'] = len(sources)
        
        for source in sources:
            values = [
                source['source_id'], source['name'], source['url'],
                source.get('type'), source.get('category'), 
                source.get('language'), source.get('is_active', 1),
                source.get('check_frequency', 3600), source.get('last_checked'),
                source.get('last_error'), source.get('error_count', 0),
                source.get('created_at'), source.get('updated_at'),
                source.get('metadata'), source.get('feed_format'),
                source.get('requires_js', 0), source.get('selector_config'),
                source.get('is_manual', 0), source.get('priority', 5),
                source.get('max_articles_per_fetch', 10)
            ]
            sql_commands.append({
                'table': 'sources',
                'sql': """INSERT INTO sources (source_id, name, url, type, category, 
                         language, is_active, check_frequency, last_checked, last_error,
                         error_count, created_at, updated_at, metadata, feed_format,
                         requires_js, selector_config, is_manual, priority, max_articles_per_fetch)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                         ON CONFLICT (source_id) DO NOTHING""",
                'values': values
            })
        
        # 2. Migrate missing articles
        logger.info("Preparing articles migration...")
        articles = self.get_missing_articles(existing_article_ids)
        self.stats['articles']['total'] = len(articles)
        
        article_batch = self.prepare_article_batch(articles)
        for article in article_batch:
            sql_commands.append({
                'table': 'articles',
                'article': article
            })
        
        # 3. Migrate ALL media_files (since currently 0 in Supabase)
        logger.info("Preparing media_files migration...")
        media_files = self.get_all_media_files()
        self.stats['media_files']['total'] = len(media_files)
        
        media_batch = self.prepare_media_batch(media_files)
        for media in media_batch:
            sql_commands.append({
                'table': 'media_files',
                'media': media
            })
        
        # 4. Migrate ALL wordpress_articles
        logger.info("Preparing wordpress_articles migration...")
        wp_articles = self.get_all_wordpress_articles()
        self.stats['wordpress_articles']['total'] = len(wp_articles)
        
        wp_batch = self.prepare_wordpress_batch(wp_articles)
        for wp in wp_batch:
            sql_commands.append({
                'table': 'wordpress_articles',
                'wordpress': wp
            })
        
        return sql_commands
    
    def close(self):
        """Close database connections"""
        self.sqlite_conn.close()
        self.monitoring_conn.close()
    
    def print_stats(self):
        """Print migration statistics"""
        logger.info("\n" + "="*50)
        logger.info("MIGRATION STATISTICS")
        logger.info("="*50)
        
        for table, stats in self.stats.items():
            logger.info(f"\n{table.upper()}:")
            logger.info(f"  Total to migrate: {stats['total']}")
            logger.info(f"  Successfully migrated: {stats['migrated']}")
            logger.info(f"  Errors: {stats['errors']}")
            
            if stats['total'] > 0:
                success_rate = (stats['migrated'] / stats['total']) * 100
                logger.info(f"  Success rate: {success_rate:.1f}%")
        
        logger.info("\n" + "="*50)

def main():
    """Main migration function"""
    
    logger.info("Starting complete data migration from SQLite to Supabase")
    logger.info(f"SQLite database: {SQLITE_DB}")
    logger.info(f"Monitoring database: {MONITORING_DB}")
    
    migrator = DataMigrator()
    
    try:
        # Generate migration data
        migration_data = migrator.generate_migration_sql()
        
        # Save to JSON for MCP processing
        output_file = '/Users/skynet/Desktop/AI DEV/ainews-clean/migrations/migration_data.json'
        with open(output_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'stats': migrator.stats,
                'total_commands': len(migration_data)
            }, f, indent=2)
        
        logger.info(f"\nMigration data prepared:")
        logger.info(f"  Sources to migrate: {migrator.stats['sources']['total']}")
        logger.info(f"  Articles to migrate: {migrator.stats['articles']['total']}")
        logger.info(f"  Media files to migrate: {migrator.stats['media_files']['total']}")
        logger.info(f"  WordPress articles to migrate: {migrator.stats['wordpress_articles']['total']}")
        logger.info(f"\nMigration data saved to: {output_file}")
        logger.info("\nNow execute the migration via MCP tools to complete the process")
        
        # Print final statistics
        migrator.print_stats()
        
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return 1
    
    finally:
        migrator.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())