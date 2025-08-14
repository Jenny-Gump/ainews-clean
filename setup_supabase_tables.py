"""
Setup Supabase tables using RPC function
Run this AFTER creating the execute_sql function in Supabase Dashboard
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials
url = os.getenv('SUPABASE_URL')
service_key = os.getenv('SUPABASE_SERVICE_KEY')

print(f"🔗 Connecting to Supabase: {url}")
supabase = create_client(url, service_key)

# SQL for creating all tables
create_tables_sql = """
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Articles table
CREATE TABLE IF NOT EXISTS articles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    article_id TEXT UNIQUE NOT NULL,
    source_id TEXT,
    url TEXT NOT NULL,
    title TEXT,
    content TEXT,
    summary TEXT,
    published_at TIMESTAMP,
    content_status TEXT DEFAULT 'pending',
    media_status TEXT DEFAULT 'pending',
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Media files table
CREATE TABLE IF NOT EXISTS media_files (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    article_id TEXT REFERENCES articles(article_id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    local_path TEXT,
    alt_text TEXT,
    alt_text_ru TEXT,
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    mime_type TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- WordPress articles table
CREATE TABLE IF NOT EXISTS wordpress_articles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    article_id TEXT REFERENCES articles(article_id) ON DELETE CASCADE,
    wordpress_id INTEGER UNIQUE,
    title_ru TEXT,
    content_ru TEXT,
    excerpt_ru TEXT,
    tags TEXT[],
    categories INTEGER[],
    featured_image_id INTEGER,
    status TEXT DEFAULT 'draft',
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sources table
CREATE TABLE IF NOT EXISTS sources (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    source_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    url TEXT,
    feed_url TEXT,
    language TEXT DEFAULT 'en',
    category TEXT,
    active BOOLEAN DEFAULT true,
    last_checked TIMESTAMP,
    error_count INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(content_status);
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source_id);
CREATE INDEX IF NOT EXISTS idx_articles_created ON articles(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_media_article ON media_files(article_id);
CREATE INDEX IF NOT EXISTS idx_wp_article ON wordpress_articles(article_id);
CREATE INDEX IF NOT EXISTS idx_sources_active ON sources(active);
"""

try:
    print("\n📝 Creating tables via RPC function...")
    
    # Call the RPC function to create tables
    result = supabase.rpc('execute_sql', {'query': create_tables_sql}).execute()
    
    if result.data == 'SQL executed successfully':
        print("✅ All tables created successfully!")
        
        # Test by inserting sample data
        print("\n🧪 Testing tables...")
        
        # Insert test source
        test_source = {
            'source_id': 'test_source',
            'name': 'Test Source',
            'url': 'http://example.com',
            'feed_url': 'http://example.com/rss',
            'active': True
        }
        
        source_result = supabase.table('sources').insert(test_source).execute()
        print("✅ Test source inserted:", source_result.data[0]['source_id'])
        
        # Insert test article
        test_article = {
            'article_id': 'test_article_001',
            'source_id': 'test_source',
            'url': 'http://example.com/article',
            'title': 'Test Article',
            'content': 'This is a test article content',
            'content_status': 'pending'
        }
        
        article_result = supabase.table('articles').insert(test_article).execute()
        print("✅ Test article inserted:", article_result.data[0]['article_id'])
        
        # Get statistics
        print("\n📊 Database Statistics:")
        
        # Count tables
        sources_count = supabase.table('sources').select('*', count='exact').execute()
        articles_count = supabase.table('articles').select('*', count='exact').execute()
        
        print(f"  Sources: {sources_count.count}")
        print(f"  Articles: {articles_count.count}")
        
        # Clean up test data
        print("\n🧹 Cleaning up test data...")
        supabase.table('articles').delete().eq('article_id', 'test_article_001').execute()
        supabase.table('sources').delete().eq('source_id', 'test_source').execute()
        print("✅ Test data cleaned up")
        
    else:
        print(f"⚠️ Result: {result.data}")
        
except Exception as e:
    if "not find the function" in str(e):
        print("❌ RPC function 'execute_sql' not found!")
        print("\n📋 Please create the function first:")
        print("1. Go to Supabase Dashboard > SQL Editor")
        print("2. Run this SQL:")
        print("-" * 50)
        print("""
CREATE OR REPLACE FUNCTION execute_sql(query text)
RETURNS text AS $$
DECLARE
    result_msg text;
BEGIN
    EXECUTE query;
    result_msg := 'SQL executed successfully';
    RETURN result_msg;
EXCEPTION
    WHEN OTHERS THEN
        RETURN 'Error: ' || SQLERRM;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION execute_sql(text) TO service_role;
        """)
        print("-" * 50)
    else:
        print(f"❌ Error: {e}")

print("\n✅ Setup complete!")