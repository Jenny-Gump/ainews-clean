#!/usr/bin/env python3
"""
Complete Migration Script
Переносит ВСЕ недостающие данные из SQLite в Supabase
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import requests
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

SQLITE_DB = Path(__file__).parent.parent / 'data' / 'ainews.db'
SUPABASE_URL = f"https://{os.getenv('SUPABASE_PROJECT_REF')}.supabase.co"
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Use service role key for full access

headers = {
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'apikey': SUPABASE_KEY,
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'  # Don't return inserted data
}

def get_sqlite_connection():
    """Get SQLite connection"""
    return sqlite3.connect(SQLITE_DB)

def get_existing_ids(table_name, id_column):
    """Get existing IDs from Supabase"""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/{table_name}?select={id_column}",
        headers=headers
    )
    if response.status_code == 200:
        return set(item[id_column] for item in response.json())
    return set()

def migrate_articles():
    """Migrate missing articles"""
    print("\n=== Migrating Articles ===")
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    # Get existing article IDs in Supabase
    existing_ids = get_existing_ids('articles', 'article_id')
    print(f"Existing articles in Supabase: {len(existing_ids)}")
    
    # Get all articles from SQLite
    cursor.execute("SELECT * FROM articles")
    columns = [desc[0] for desc in cursor.description]
    articles = cursor.fetchall()
    print(f"Total articles in SQLite: {len(articles)}")
    
    # Prepare missing articles for migration
    missing_articles = []
    for row in articles:
        article = dict(zip(columns, row))
        if article['article_id'] not in existing_ids:
            # Convert datetime fields
            for field in ['published_date', 'created_at', 'parsed_at', 'deleted_at']:
                if article.get(field):
                    try:
                        dt = datetime.fromisoformat(article[field])
                        article[field] = dt.isoformat()
                    except:
                        pass
            missing_articles.append(article)
    
    print(f"Missing articles to migrate: {len(missing_articles)}")
    
    if missing_articles:
        # Batch insert (Supabase handles up to 1000 at once)
        batch_size = 500
        for i in range(0, len(missing_articles), batch_size):
            batch = missing_articles[i:i+batch_size]
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/articles",
                headers=headers,
                json=batch
            )
            if response.status_code == 201:
                print(f"Migrated batch {i//batch_size + 1}: {len(batch)} articles")
            else:
                print(f"Error migrating batch: {response.text}")
    
    conn.close()
    return len(missing_articles)

def migrate_media_files():
    """Migrate missing media files"""
    print("\n=== Migrating Media Files ===")
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    existing_ids = get_existing_ids('media_files', 'media_id')
    print(f"Existing media files in Supabase: {len(existing_ids)}")
    
    cursor.execute("SELECT * FROM media_files")
    columns = [desc[0] for desc in cursor.description]
    media_files = cursor.fetchall()
    print(f"Total media files in SQLite: {len(media_files)}")
    
    missing_media = []
    for row in media_files:
        media = dict(zip(columns, row))
        if media['media_id'] not in existing_ids:
            # Remove 'id' column as it's auto-generated in Supabase
            if 'id' in media:
                del media['id']
            # Ensure wp_media_id is integer if present
            if 'wp_media_id' in media and media['wp_media_id'] is not None:
                media['wp_media_id'] = int(media['wp_media_id'])
            # Convert datetime fields
            for field in ['created_at', 'wp_uploaded_at']:
                if media.get(field):
                    try:
                        dt = datetime.fromisoformat(media[field])
                        media[field] = dt.isoformat()
                    except:
                        pass
            missing_media.append(media)
    
    print(f"Missing media files to migrate: {len(missing_media)}")
    
    if missing_media:
        batch_size = 500
        for i in range(0, len(missing_media), batch_size):
            batch = missing_media[i:i+batch_size]
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/media_files",
                headers=headers,
                json=batch
            )
            if response.status_code == 201:
                print(f"Migrated batch {i//batch_size + 1}: {len(batch)} media files")
            else:
                print(f"Error migrating batch: {response.text}")
    
    conn.close()
    return len(missing_media)

def migrate_wordpress_articles():
    """Migrate missing WordPress articles"""
    print("\n=== Migrating WordPress Articles ===")
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    # Check existing
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/wordpress_articles?select=article_id",
        headers=headers
    )
    existing_ids = set()
    if response.status_code == 200:
        existing_ids = set(item['article_id'] for item in response.json())
    print(f"Existing WordPress articles in Supabase: {len(existing_ids)}")
    
    cursor.execute("SELECT * FROM wordpress_articles")
    columns = [desc[0] for desc in cursor.description]
    wp_articles = cursor.fetchall()
    print(f"Total WordPress articles in SQLite: {len(wp_articles)}")
    
    missing_wp = []
    for row in wp_articles:
        wp = dict(zip(columns, row))
        if wp['article_id'] not in existing_ids:
            # Ensure wp_post_id is integer
            if 'wp_post_id' in wp and wp['wp_post_id'] is not None:
                wp['wp_post_id'] = int(wp['wp_post_id'])
            # Convert datetime fields
            for field in ['created_at', 'wp_published_at', 'wp_modified_at']:
                if wp.get(field):
                    try:
                        dt = datetime.fromisoformat(wp[field])
                        wp[field] = dt.isoformat()
                    except:
                        pass
            missing_wp.append(wp)
    
    print(f"Missing WordPress articles to migrate: {len(missing_wp)}")
    
    if missing_wp:
        batch_size = 100
        for i in range(0, len(missing_wp), batch_size):
            batch = missing_wp[i:i+batch_size]
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/wordpress_articles",
                headers=headers,
                json=batch
            )
            if response.status_code == 201:
                print(f"Migrated batch {i//batch_size + 1}: {len(batch)} WordPress articles")
            else:
                print(f"Error migrating batch: {response.text}")
    
    conn.close()
    return len(missing_wp)

def migrate_small_tables():
    """Migrate smaller tables"""
    tables = [
        ('related_links', 'id'),  # Correct column name
        ('tracked_articles', 'article_id'),
        ('tracked_urls', 'url'),
        ('pipeline_operations', 'operation_id'),
        ('global_config', 'config_key')
    ]
    
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    migrated_counts = {}
    
    for table_name, id_column in tables:
        print(f"\n=== Migrating {table_name} ===")
        
        # Get existing IDs
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{table_name}?select={id_column}",
            headers=headers
        )
        existing_ids = set()
        if response.status_code == 200:
            existing_ids = set(item[id_column] for item in response.json())
        print(f"Existing in Supabase: {len(existing_ids)}")
        
        # Get all from SQLite
        cursor.execute(f"SELECT * FROM {table_name}")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        print(f"Total in SQLite: {len(rows)}")
        
        # Prepare missing records
        missing_records = []
        for row in rows:
            record = dict(zip(columns, row))
            if record.get(id_column) not in existing_ids:
                # Remove auto-generated id columns if they exist
                if 'id' in record and table_name != 'related_links':
                    del record['id']
                # Convert datetime fields
                for key, value in record.items():
                    if value and ('date' in key.lower() or 'at' in key.lower()):
                        try:
                            dt = datetime.fromisoformat(str(value))
                            record[key] = dt.isoformat()
                        except:
                            pass
                missing_records.append(record)
        
        print(f"Missing records to migrate: {len(missing_records)}")
        migrated_counts[table_name] = len(missing_records)
        
        if missing_records:
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/{table_name}",
                headers=headers,
                json=missing_records
            )
            if response.status_code == 201:
                print(f"Successfully migrated {len(missing_records)} records")
            else:
                print(f"Error migrating: {response.text}")
    
    conn.close()
    return migrated_counts

def verify_migration():
    """Verify migration completeness"""
    print("\n" + "="*60)
    print("VERIFICATION RESULTS")
    print("="*60)
    
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    tables = [
        'articles', 'sources', 'media_files', 'wordpress_articles',
        'related_links', 'tracked_articles', 'tracked_urls',
        'pipeline_operations', 'global_config'
    ]
    
    results = []
    for table in tables:
        # SQLite count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        sqlite_count = cursor.fetchone()[0]
        
        # Supabase count
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{table}?select=count",
            headers={'Authorization': f'Bearer {SUPABASE_KEY}', 'apikey': SUPABASE_KEY, 'Prefer': 'count=exact'}
        )
        supabase_count = 0
        if response.status_code == 200:
            supabase_count = int(response.headers.get('content-range', '0/0').split('/')[-1])
        
        status = "✓" if sqlite_count == supabase_count else "✗"
        results.append({
            'table': table,
            'sqlite': sqlite_count,
            'supabase': supabase_count,
            'diff': sqlite_count - supabase_count,
            'status': status
        })
    
    conn.close()
    
    # Print results table
    print(f"{'Table':<25} {'SQLite':>10} {'Supabase':>10} {'Diff':>10} {'Status':>8}")
    print("-" * 65)
    for r in results:
        print(f"{r['table']:<25} {r['sqlite']:>10} {r['supabase']:>10} {r['diff']:>10} {r['status']:>8}")
    
    return results

def main():
    print("="*60)
    print("COMPLETE MIGRATION TO SUPABASE")
    print("="*60)
    
    # Migrate each table
    articles_migrated = migrate_articles()
    media_migrated = migrate_media_files()
    wp_migrated = migrate_wordpress_articles()
    small_tables_migrated = migrate_small_tables()
    
    print("\n" + "="*60)
    print("MIGRATION SUMMARY")
    print("="*60)
    print(f"Articles migrated: {articles_migrated}")
    print(f"Media files migrated: {media_migrated}")
    print(f"WordPress articles migrated: {wp_migrated}")
    for table, count in small_tables_migrated.items():
        print(f"{table} migrated: {count}")
    
    # Verify final state
    verify_migration()

if __name__ == "__main__":
    main()