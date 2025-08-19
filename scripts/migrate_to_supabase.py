#!/usr/bin/env python3
"""
Migration script to copy all data from SQLite to Supabase
Both ainews-clean and context_enrichment systems
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.database import Database
from services.supabase_client import SupabaseClient
from dateutil.parser import parse as parse_date
from datetime import datetime
import json

def migrate_articles():
    """Migrate articles table from SQLite to Supabase"""
    print("🔄 Migrating articles table...")
    
    # SQLite connection
    sqlite_db = Database('data/ainews.db')
    
    # Supabase connection  
    supabase = SupabaseClient()
    
    with sqlite_db.get_connection() as conn:
        cursor = conn.execute('SELECT * FROM articles')
        articles = cursor.fetchall()
        
    print(f"Found {len(articles)} articles in SQLite")
    
    migrated = 0
    for article in articles:
        try:
            # Convert datetime strings to proper format
            published_date = None
            if article['published_date']:
                try:
                    dt = parse_date(article['published_date'])
                    published_date = dt.isoformat()
                except:
                    published_date = None
                    
            created_at = None
            if article['created_at']:
                try:
                    dt = parse_date(article['created_at'])
                    created_at = dt.isoformat()
                except:
                    created_at = datetime.now().isoformat()
                    
            parsed_at = None
            if article['parsed_at']:
                try:
                    dt = parse_date(article['parsed_at'])
                    parsed_at = dt.isoformat()
                except:
                    parsed_at = None
                    
            deleted_at = None
            if article['deleted_at']:
                try:
                    dt = parse_date(article['deleted_at'])
                    deleted_at = dt.isoformat()
                except:
                    deleted_at = None
            
            # Prepare data for Supabase
            article_data = {
                'article_id': article['article_id'],
                'source_id': article['source_id'],
                'url': article['url'],
                'title': article['title'],
                'content': article['content'],
                'published_date': published_date,
                'created_at': created_at,
                'content_status': article['content_status'],
                'content_error': article['content_error'],
                'parsed_at': parsed_at,
                'media_count': article['media_count'],
                'media_status': article['media_status'],
                'description': article['description'],
                'discovered_via': article['discovered_via'],
                'llm_content_raw': article['llm_content_raw'],
                'llm_translation_raw': article['llm_translation_raw'],
                'llm_tags_raw': article['llm_tags_raw'],
                'is_deleted': bool(article['is_deleted']),  # Convert 0/1 to boolean
                'deleted_at': deleted_at,
                'deleted_by': article['deleted_by']
            }
            
            # Insert to Supabase (upsert)
            result = supabase.client.table('articles').upsert(article_data, on_conflict='article_id').execute()
            migrated += 1
            
            if migrated % 10 == 0:
                print(f"  ✅ Migrated {migrated} articles...")
                
        except Exception as e:
            print(f"  ❌ Failed to migrate article {article['article_id']}: {e}")
            continue
    
    print(f"✅ Articles migration complete: {migrated}/{len(articles)} migrated")

def migrate_sources():
    """Migrate sources table"""
    print("🔄 Migrating sources table...")
    
    sqlite_db = Database('data/ainews.db')
    supabase = SupabaseClient()
    
    with sqlite_db.get_connection() as conn:
        cursor = conn.execute('SELECT * FROM sources')
        sources = cursor.fetchall()
    
    print(f"Found {len(sources)} sources in SQLite")
    
    migrated = 0
    for source in sources:
        try:
            # Convert datetime
            created_at = None
            if source['created_at']:
                try:
                    dt = parse_date(source['created_at'])
                    created_at = dt.isoformat()
                except:
                    created_at = datetime.now().isoformat()
                    
            updated_at = None
            if source['updated_at']:
                try:
                    dt = parse_date(source['updated_at'])
                    updated_at = dt.isoformat()
                except:
                    updated_at = datetime.now().isoformat()
                    
            last_checked = None
            if source['last_checked']:
                try:
                    dt = parse_date(source['last_checked'])
                    last_checked = dt.isoformat()
                except:
                    last_checked = None
            
            source_data = {
                'source_id': source['source_id'],
                'name': source['name'],
                'url': source['url'],
                'feed_url': source['feed_url'],
                'language': source['language'],
                'category': source['category'],
                'active': source['active'],
                'last_checked': last_checked,
                'error_count': source['error_count'],
                'metadata': source['metadata'],
                'created_at': created_at,
                'updated_at': updated_at
            }
            
            # Create sources table if not exists
            supabase.client.rpc('execute_sql', {
                'query': '''
                CREATE TABLE IF NOT EXISTS sources (
                    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
                    source_id text NOT NULL UNIQUE,
                    name text NOT NULL,
                    url text,
                    feed_url text,
                    language text DEFAULT 'en',
                    category text,
                    active boolean DEFAULT true,
                    last_checked timestamp,
                    error_count integer DEFAULT 0,
                    metadata jsonb,
                    created_at timestamp DEFAULT now(),
                    updated_at timestamp DEFAULT now()
                );
                '''
            }).execute()
            
            result = supabase.client.table('sources').upsert(source_data, on_conflict='source_id').execute()
            migrated += 1
            
        except Exception as e:
            print(f"  ❌ Failed to migrate source {source['source_id']}: {e}")
            continue
    
    print(f"✅ Sources migration complete: {migrated}/{len(sources)} migrated")

def migrate_media_files():
    """Migrate media_files table"""
    print("🔄 Migrating media_files table...")
    
    sqlite_db = Database('data/ainews.db')
    supabase = SupabaseClient()
    
    with sqlite_db.get_connection() as conn:
        cursor = conn.execute('SELECT * FROM media_files')
        media_files = cursor.fetchall()
    
    print(f"Found {len(media_files)} media files in SQLite")
    
    # Create media_files table if not exists
    try:
        supabase.client.rpc('execute_sql', {
            'query': '''
            CREATE TABLE IF NOT EXISTS media_files (
                id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
                article_id text REFERENCES articles(article_id),
                url text NOT NULL,
                local_path text,
                alt_text text,
                alt_text_ru text,
                width integer,
                height integer,
                file_size integer,
                mime_type text,
                created_at timestamp DEFAULT now()
            );
            '''
        }).execute()
    except:
        pass
    
    migrated = 0
    for media in media_files:
        try:
            created_at = None
            if media['created_at']:
                try:
                    dt = parse_date(media['created_at'])
                    created_at = dt.isoformat()
                except:
                    created_at = datetime.now().isoformat()
            
            media_data = {
                'article_id': media['article_id'],
                'url': media['url'],
                'local_path': media['local_path'],
                'alt_text': media['alt_text'],
                'alt_text_ru': media['alt_text_ru'],
                'width': media['width'],
                'height': media['height'],
                'file_size': media['file_size'],
                'mime_type': media['mime_type'],
                'created_at': created_at
            }
            
            result = supabase.client.table('media_files').insert(media_data).execute()
            migrated += 1
            
        except Exception as e:
            print(f"  ❌ Failed to migrate media: {e}")
            continue
    
    print(f"✅ Media files migration complete: {migrated}/{len(media_files)} migrated")

def migrate_wordpress_articles():
    """Migrate wordpress_articles table"""
    print("🔄 Migrating wordpress_articles table...")
    
    sqlite_db = Database('data/ainews.db')
    supabase = SupabaseClient()
    
    with sqlite_db.get_connection() as conn:
        cursor = conn.execute('SELECT * FROM wordpress_articles')
        wp_articles = cursor.fetchall()
    
    print(f"Found {len(wp_articles)} WordPress articles in SQLite")
    
    # Create wordpress_articles table if not exists
    try:
        supabase.client.rpc('execute_sql', {
            'query': '''
            CREATE TABLE IF NOT EXISTS wordpress_articles (
                id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
                article_id text REFERENCES articles(article_id),
                wordpress_id integer UNIQUE,
                title_ru text,
                content_ru text,
                excerpt_ru text,
                tags text[],
                categories integer[],
                featured_image_id integer,
                status text DEFAULT 'draft',
                published_at timestamp,
                created_at timestamp DEFAULT now()
            );
            '''
        }).execute()
    except:
        pass
    
    migrated = 0
    for wp_article in wp_articles:
        try:
            created_at = None
            if wp_article['created_at']:
                try:
                    dt = parse_date(wp_article['created_at'])
                    created_at = dt.isoformat()
                except:
                    created_at = datetime.now().isoformat()
                    
            published_at = None
            if wp_article['published_at']:
                try:
                    dt = parse_date(wp_article['published_at'])
                    published_at = dt.isoformat()
                except:
                    published_at = None
            
            # Parse tags JSON
            tags = []
            if wp_article['tags']:
                try:
                    tags = json.loads(wp_article['tags'])
                except:
                    tags = []
                    
            # Parse categories JSON
            categories = []
            if wp_article['categories']:
                try:
                    categories = json.loads(wp_article['categories'])
                except:
                    categories = []
            
            wp_data = {
                'article_id': wp_article['article_id'],
                'wordpress_id': wp_article['wordpress_id'],
                'title_ru': wp_article['title_ru'],
                'content_ru': wp_article['content_ru'],
                'excerpt_ru': wp_article['excerpt_ru'],
                'tags': tags,
                'categories': categories,
                'featured_image_id': wp_article['featured_image_id'],
                'status': wp_article['status'],
                'published_at': published_at,
                'created_at': created_at
            }
            
            result = supabase.client.table('wordpress_articles').upsert(wp_data, on_conflict='wordpress_id').execute()
            migrated += 1
            
        except Exception as e:
            print(f"  ❌ Failed to migrate WP article: {e}")
            continue
    
    print(f"✅ WordPress articles migration complete: {migrated}/{len(wp_articles)} migrated")

def main():
    """Main migration function"""
    print("🚀 Starting migration from SQLite to Supabase...")
    print(f"Time: {datetime.now().isoformat()}")
    print("-" * 50)
    
    try:
        # Test Supabase connection
        supabase = SupabaseClient()
        test = supabase.client.table('articles').select('count').execute()
        print("✅ Supabase connection successful")
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return
    
    # Run migrations
    migrate_articles()
    migrate_sources()
    migrate_media_files()
    migrate_wordpress_articles()
    
    print("-" * 50)
    print("✅ Migration completed!")
    print("🔍 Verify data in Supabase dashboard:")
    print("   https://supabase.com/dashboard/project/mtguynupyltlqiwhmilc")

if __name__ == "__main__":
    main()