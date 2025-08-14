#!/usr/bin/env python3
"""Debug script to understand pipeline issue"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.single_pipeline import SingleArticlePipeline
from services.supabase_client import SupabaseClient

def main():
    pipeline = SingleArticlePipeline()
    db = SupabaseClient()
    
    print("=" * 60)
    print("DEBUG: Checking get_next_article()")
    print("=" * 60)
    
    # Test get_next_article
    article = pipeline.get_next_article()
    
    if article:
        print(f"✅ Found article: {article['article_id']}")
        print(f"   Title: {article['title'][:50]}")
        print(f"   Status: {article['content_status']}")
        print(f"   Media: {article.get('media_status', 'N/A')}")
    else:
        print("❌ get_next_article() returned None")
        
        # Check database directly
        with db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) as count FROM articles 
                WHERE content_status IN ('pending', 'parsed')
                  AND (content_status = 'pending' OR media_status IN ('pending', 'ready'))
            """)
            count = cursor.fetchone()['count']
            print(f"   But database has {count} matching articles!")
            
            # Try to get one directly
            cursor = conn.execute("""
                SELECT article_id, title, content_status, media_status
                FROM articles 
                WHERE content_status IN ('pending', 'parsed')
                  AND (content_status = 'pending' OR media_status IN ('pending', 'ready'))
                ORDER BY created_at ASC
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                print(f"   Direct query found: {row['article_id']}")
                print(f"   Title: {row['title'][:50]}")

if __name__ == "__main__":
    main()