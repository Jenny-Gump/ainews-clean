#!/usr/bin/env python3
"""
Fix Remaining Migration Issues
Исправляет оставшиеся проблемы с миграцией
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import requests
import json
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

SQLITE_DB = Path(__file__).parent.parent / 'data' / 'ainews.db'
SUPABASE_URL = f"https://{os.getenv('SUPABASE_PROJECT_REF')}.supabase.co"
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'apikey': SUPABASE_KEY,
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

def fix_wordpress_articles():
    """Fix WordPress articles migration"""
    print("\n=== Fixing WordPress Articles ===")
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    
    # Get existing
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/wordpress_articles?select=article_id",
        headers=headers
    )
    existing_ids = set()
    if response.status_code == 200:
        existing_ids = set(item['article_id'] for item in response.json())
    
    cursor.execute("SELECT * FROM wordpress_articles")
    columns = [desc[0] for desc in cursor.description]
    wp_articles = cursor.fetchall()
    
    missing_wp = []
    for row in wp_articles:
        wp = dict(zip(columns, row))
        if wp['article_id'] not in existing_ids:
            # Add UUID for id field
            wp['id'] = str(uuid.uuid4())
            
            # Remove SQLite id if exists
            if 'id_integer' in wp:
                del wp['id_integer']
            
            # Ensure wp_post_id is integer
            if 'wp_post_id' in wp and wp['wp_post_id'] is not None:
                wp['wp_post_id'] = int(wp['wp_post_id'])
            
            # Convert datetime fields
            datetime_fields = ['created_at', 'wp_published_at', 'wp_modified_at', 
                             'published_at', 'translated_at', 'updated_at']
            for field in datetime_fields:
                if wp.get(field):
                    try:
                        dt = datetime.fromisoformat(wp[field])
                        wp[field] = dt.isoformat()
                    except:
                        wp[field] = None
            
            # Rename fields to match Supabase schema
            if 'wp_published_at' in wp:
                wp['published_at'] = wp.pop('wp_published_at', None)
            if 'wp_modified_at' in wp:
                wp['updated_at'] = wp.pop('wp_modified_at', None)
            
            # Map wp_post_id to wordpress_id if needed
            if 'wordpress_id' not in wp and 'wp_post_id' in wp:
                wp['wordpress_id'] = wp['wp_post_id']
            
            missing_wp.append(wp)
    
    print(f"Missing WordPress articles to migrate: {len(missing_wp)}")
    
    if missing_wp:
        # Process in smaller batches
        batch_size = 10
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
                print(f"Error in batch {i//batch_size + 1}: {response.text}")
                # Try individual inserts for this batch
                for article in batch:
                    response = requests.post(
                        f"{SUPABASE_URL}/rest/v1/wordpress_articles",
                        headers=headers,
                        json=article
                    )
                    if response.status_code != 201:
                        print(f"Failed article {article.get('article_id')}: {response.text[:200]}")
    
    conn.close()
    return len(missing_wp)

def fix_related_links():
    """Fix related links - check if article exists first"""
    print("\n=== Fixing Related Links ===")
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    
    # Get articles in Supabase
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/articles?select=article_id",
        headers=headers
    )
    supabase_articles = set()
    if response.status_code == 200:
        supabase_articles = set(item['article_id'] for item in response.json())
    
    cursor.execute("SELECT * FROM related_links")
    columns = [desc[0] for desc in cursor.description]
    links = cursor.fetchall()
    
    valid_links = []
    for row in links:
        link = dict(zip(columns, row))
        # Check if article exists in Supabase
        if link['article_id'] in supabase_articles:
            # Add UUID
            link['id'] = str(uuid.uuid4())
            # Convert datetime
            if link.get('created_at'):
                try:
                    dt = datetime.fromisoformat(link['created_at'])
                    link['created_at'] = dt.isoformat()
                except:
                    pass
            valid_links.append(link)
        else:
            print(f"Skipping link for non-existent article: {link['article_id']}")
    
    print(f"Valid related links to migrate: {len(valid_links)}")
    
    if valid_links:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/related_links",
            headers=headers,
            json=valid_links
        )
        if response.status_code == 201:
            print(f"Successfully migrated {len(valid_links)} related links")
        else:
            print(f"Error migrating: {response.text}")
    
    conn.close()
    return len(valid_links)

def fix_tracked_articles():
    """Fix tracked articles - check if source exists first"""
    print("\n=== Fixing Tracked Articles ===")
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    
    # Get sources in Supabase
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/sources?select=source_id",
        headers=headers
    )
    supabase_sources = set()
    if response.status_code == 200:
        supabase_sources = set(item['source_id'] for item in response.json())
    
    cursor.execute("SELECT * FROM tracked_articles")
    columns = [desc[0] for desc in cursor.description]
    tracked = cursor.fetchall()
    
    valid_tracked = []
    for row in tracked:
        track = dict(zip(columns, row))
        # Check if source exists in Supabase
        if track.get('source_id') in supabase_sources:
            # Convert datetime fields
            for field in ['discovered_at', 'processed_at']:
                if track.get(field):
                    try:
                        dt = datetime.fromisoformat(track[field])
                        track[field] = dt.isoformat()
                    except:
                        pass
            valid_tracked.append(track)
        else:
            print(f"Skipping tracked article for non-existent source: {track.get('source_id')}")
    
    print(f"Valid tracked articles to migrate: {len(valid_tracked)}")
    
    if valid_tracked:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/tracked_articles",
            headers=headers,
            json=valid_tracked
        )
        if response.status_code == 201:
            print(f"Successfully migrated {len(valid_tracked)} tracked articles")
        else:
            print(f"Error migrating: {response.text}")
    
    conn.close()
    return len(valid_tracked)

def verify_final_migration():
    """Final verification"""
    print("\n" + "="*60)
    print("FINAL VERIFICATION")
    print("="*60)
    
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    
    tables = [
        'articles', 'sources', 'media_files', 'wordpress_articles',
        'related_links', 'tracked_articles', 'tracked_urls',
        'pipeline_operations', 'global_config'
    ]
    
    results = []
    all_match = True
    
    for table in tables:
        # SQLite count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        sqlite_count = cursor.fetchone()[0]
        
        # Supabase count
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{table}?select=count",
            headers={'Authorization': f'Bearer {SUPABASE_KEY}', 
                    'apikey': SUPABASE_KEY, 
                    'Prefer': 'count=exact'}
        )
        supabase_count = 0
        if response.status_code == 200:
            supabase_count = int(response.headers.get('content-range', '0/0').split('/')[-1])
        
        match = sqlite_count == supabase_count
        if not match:
            all_match = False
        
        status = "✅" if match else f"❌ (-{sqlite_count - supabase_count})"
        results.append({
            'table': table,
            'sqlite': sqlite_count,
            'supabase': supabase_count,
            'diff': sqlite_count - supabase_count,
            'status': status
        })
    
    conn.close()
    
    # Print results table
    print(f"{'Table':<25} {'SQLite':>10} {'Supabase':>10} {'Diff':>10} {'Status'}")
    print("-" * 70)
    for r in results:
        print(f"{r['table']:<25} {r['sqlite']:>10} {r['supabase']:>10} {r['diff']:>10} {r['status']}")
    
    print("\n" + "="*60)
    if all_match:
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("All tables have been fully migrated to Supabase.")
    else:
        print("⚠️ MIGRATION PARTIALLY COMPLETE")
        print("Some tables still have differences. Check the status above.")
    print("="*60)
    
    return results

def main():
    print("="*60)
    print("FIXING REMAINING MIGRATION ISSUES")
    print("="*60)
    
    # Fix each problematic table
    wp_fixed = fix_wordpress_articles()
    links_fixed = fix_related_links()
    tracked_fixed = fix_tracked_articles()
    
    print("\n" + "="*60)
    print("FIX SUMMARY")
    print("="*60)
    print(f"WordPress articles fixed: {wp_fixed}")
    print(f"Related links fixed: {links_fixed}")
    print(f"Tracked articles fixed: {tracked_fixed}")
    
    # Final verification
    verify_final_migration()

if __name__ == "__main__":
    main()