#!/usr/bin/env python3
"""
Batch migration script for remaining data
Uses direct SQL to migrate media_files and wordpress_articles
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
import os
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connections
SQLITE_DB = '/Users/skynet/Desktop/AI DEV/ainews-clean/data/ainews.db'

# Supabase connection string - you'll need to update with actual credentials
SUPABASE_CONNECTION = {
    'host': 'aws-0-us-east-1.pooler.supabase.com',
    'database': 'postgres',
    'user': 'postgres.mtguynupyltlqiwhmilc',
    'password': os.environ.get('SUPABASE_PASSWORD', ''),  # Set this in env
    'port': 6543
}

def migrate_media_files():
    """Migrate all media_files from SQLite to Supabase"""
    logger.info("Starting media_files migration...")
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()
    
    # Get all media files
    cursor.execute("SELECT * FROM media_files ORDER BY id")
    media_files = [dict(row) for row in cursor.fetchall()]
    logger.info(f"Found {len(media_files)} media files to migrate")
    
    # Connect to Supabase
    pg_conn = psycopg2.connect(**SUPABASE_CONNECTION)
    pg_cursor = pg_conn.cursor()
    
    # Prepare batch insert
    insert_query = """
        INSERT INTO media_files (
            article_id, url, type, file_path, media_id, source_id,
            file_size, mime_type, width, height, alt_text, status, error,
            source, caption, wp_media_id, wp_upload_status, wp_uploaded_at,
            alt_text_ru, caption_ru, image_order, processing_session_id,
            wp_source_url, id_integer, created_at
        ) VALUES (
            %(article_id)s, %(url)s, %(type)s, %(file_path)s, %(media_id)s, %(source_id)s,
            %(file_size)s, %(mime_type)s, %(width)s, %(height)s, %(alt_text)s, %(status)s, %(error)s,
            %(source)s, %(caption)s, %(wp_media_id)s, %(wp_upload_status)s, %(wp_uploaded_at)s,
            %(alt_text_ru)s, %(caption_ru)s, %(image_order)s, %(processing_session_id)s,
            %(wp_source_url)s, %(id_integer)s, %(created_at)s
        )
    """
    
    # Process in batches
    batch_size = 50
    migrated = 0
    
    for i in range(0, len(media_files), batch_size):
        batch = media_files[i:i+batch_size]
        
        # Prepare batch data
        batch_data = []
        for media in batch:
            media_copy = media.copy()
            media_copy['id_integer'] = media.get('id')
            
            # Convert datetime fields
            for date_field in ['created_at', 'wp_uploaded_at']:
                if media_copy.get(date_field):
                    if isinstance(media_copy[date_field], str) and 'T' not in media_copy[date_field]:
                        media_copy[date_field] = media_copy[date_field].replace(' ', 'T')
            
            batch_data.append(media_copy)
        
        try:
            execute_batch(pg_cursor, insert_query, batch_data)
            pg_conn.commit()
            migrated += len(batch)
            logger.info(f"Migrated {migrated}/{len(media_files)} media files")
        except Exception as e:
            logger.error(f"Error migrating batch: {e}")
            pg_conn.rollback()
    
    pg_cursor.close()
    pg_conn.close()
    sqlite_conn.close()
    
    logger.info(f"Media files migration complete: {migrated} records migrated")
    return migrated

def migrate_wordpress_articles():
    """Migrate all wordpress_articles from SQLite to Supabase"""
    logger.info("Starting wordpress_articles migration...")
    
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()
    
    # Get all wordpress articles
    cursor.execute("SELECT * FROM wordpress_articles ORDER BY id")
    wp_articles = [dict(row) for row in cursor.fetchall()]
    logger.info(f"Found {len(wp_articles)} wordpress articles to migrate")
    
    # Connect to Supabase
    pg_conn = psycopg2.connect(**SUPABASE_CONNECTION)
    pg_cursor = pg_conn.cursor()
    
    # Prepare batch insert
    insert_query = """
        INSERT INTO wordpress_articles (
            article_id, title, content, excerpt, slug, categories, tags,
            _yoast_wpseo_title, _yoast_wpseo_metadesc, focus_keyword,
            featured_image_index, images_data, translation_status,
            translation_error, translated_at, published_to_wp, wp_post_id,
            source_language, target_language, llm_model, created_at,
            updated_at, processing_session_id, id_integer
        ) VALUES (
            %(article_id)s, %(title)s, %(content)s, %(excerpt)s, %(slug)s,
            %(categories)s::jsonb, %(tags)s::jsonb, %(_yoast_wpseo_title)s,
            %(_yoast_wpseo_metadesc)s, %(focus_keyword)s, %(featured_image_index)s,
            %(images_data)s, %(translation_status)s, %(translation_error)s,
            %(translated_at)s, %(published_to_wp)s, %(wp_post_id)s,
            %(source_language)s, %(target_language)s, %(llm_model)s,
            %(created_at)s, %(updated_at)s, %(processing_session_id)s, %(id_integer)s
        )
    """
    
    # Process in batches
    batch_size = 25
    migrated = 0
    
    for i in range(0, len(wp_articles), batch_size):
        batch = wp_articles[i:i+batch_size]
        
        # Prepare batch data
        batch_data = []
        for wp in batch:
            wp_copy = wp.copy()
            wp_copy['id_integer'] = wp.get('id')
            
            # Convert datetime fields
            for date_field in ['translated_at', 'created_at', 'updated_at']:
                if wp_copy.get(date_field):
                    if isinstance(wp_copy[date_field], str) and 'T' not in wp_copy[date_field]:
                        wp_copy[date_field] = wp_copy[date_field].replace(' ', 'T')
            
            # Ensure JSON fields are properly formatted
            import json
            for json_field in ['categories', 'tags']:
                if wp_copy.get(json_field):
                    if isinstance(wp_copy[json_field], str):
                        try:
                            wp_copy[json_field] = json.dumps(json.loads(wp_copy[json_field]))
                        except:
                            wp_copy[json_field] = '[]'
                else:
                    wp_copy[json_field] = '[]'
            
            batch_data.append(wp_copy)
        
        try:
            execute_batch(pg_cursor, insert_query, batch_data)
            pg_conn.commit()
            migrated += len(batch)
            logger.info(f"Migrated {migrated}/{len(wp_articles)} wordpress articles")
        except Exception as e:
            logger.error(f"Error migrating batch: {e}")
            pg_conn.rollback()
    
    pg_cursor.close()
    pg_conn.close()
    sqlite_conn.close()
    
    logger.info(f"WordPress articles migration complete: {migrated} records migrated")
    return migrated

def main():
    """Main migration function"""
    logger.info("="*50)
    logger.info("Starting batch migration to Supabase")
    logger.info("="*50)
    
    stats = {
        'media_files': 0,
        'wordpress_articles': 0
    }
    
    # Check for password
    if not os.environ.get('SUPABASE_PASSWORD'):
        logger.error("SUPABASE_PASSWORD environment variable not set!")
        logger.info("Set it with: export SUPABASE_PASSWORD='your_password'")
        return
    
    try:
        # Migrate media files
        stats['media_files'] = migrate_media_files()
        
        # Migrate wordpress articles
        stats['wordpress_articles'] = migrate_wordpress_articles()
        
        logger.info("\n" + "="*50)
        logger.info("MIGRATION COMPLETE")
        logger.info("="*50)
        logger.info(f"Media files migrated: {stats['media_files']}")
        logger.info(f"WordPress articles migrated: {stats['wordpress_articles']}")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())