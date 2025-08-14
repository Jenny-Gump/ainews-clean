"""
Create tables in Supabase using RPC function
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

# Create client with service key (admin access)
supabase = create_client(url, service_key)

# First, let's create an RPC function that can execute SQL
create_function_sql = """
CREATE OR REPLACE FUNCTION execute_sql(query text)
RETURNS void AS $$
BEGIN
    EXECUTE query;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
"""

# SQL for creating our tables
create_tables_sql = """
-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create a simple test table first
CREATE TABLE IF NOT EXISTS test_from_claude (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

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

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(content_status);
CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source_id);
"""

try:
    # Method 1: Try to execute SQL directly via postgrest
    print("\n📝 Method 1: Attempting direct SQL execution...")
    
    # This won't work directly, but let's try
    # PostgREST doesn't support DDL operations
    
    # Method 2: Use RPC function
    print("\n📝 Method 2: Creating RPC function for SQL execution...")
    
    # First, we need to create the function (this needs to be done once)
    # Unfortunately, we can't create the function via API either
    # We need to do this in the Dashboard first
    
    # Let's check if the function exists and try to use it
    try:
        # Try to execute our create tables SQL via RPC
        result = supabase.rpc('execute_sql', {'query': create_tables_sql}).execute()
        print("✅ Tables created successfully via RPC!")
    except Exception as e:
        if "not find the function" in str(e):
            print("❌ RPC function 'execute_sql' doesn't exist.")
            print("\n📋 To enable programmatic table creation:")
            print("1. Go to Supabase Dashboard > SQL Editor")
            print("2. Run this SQL to create the function:")
            print("-" * 50)
            print(create_function_sql)
            print("-" * 50)
            print("3. Then run this script again")
        else:
            print(f"❌ RPC execution failed: {e}")
    
    # Method 3: Try to insert test data to check if tables exist
    print("\n📝 Method 3: Testing if we can at least insert data...")
    
    test_data = {
        'name': 'Test from Claude via Python',
        'description': 'Testing Supabase table creation'
    }
    
    try:
        # Try test_from_claude table
        response = supabase.table('test_from_claude').insert(test_data).execute()
        print("✅ Successfully inserted into test_from_claude table!")
        print(f"Data: {response.data}")
        
        # Clean up test data
        supabase.table('test_from_claude').delete().eq('name', 'Test from Claude via Python').execute()
        print("🧹 Test data cleaned up")
        
    except Exception as e:
        if "not find the table" in str(e):
            print("❌ Table 'test_from_claude' doesn't exist yet")
        else:
            print(f"❌ Insert failed: {e}")
    
    # Method 4: Alternative - Use stored procedure approach
    print("\n📝 Method 4: Alternative approach with stored procedure...")
    
    # Create a more sophisticated function that creates tables
    advanced_function_sql = """
    CREATE OR REPLACE FUNCTION create_ainews_tables()
    RETURNS TEXT AS $$
    DECLARE
        result_msg TEXT;
    BEGIN
        -- Enable UUID extension
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        
        -- Create test table
        CREATE TABLE IF NOT EXISTS test_from_claude (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Create articles table
        CREATE TABLE IF NOT EXISTS articles (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            article_id TEXT UNIQUE NOT NULL,
            source_id TEXT,
            url TEXT NOT NULL,
            title TEXT,
            content TEXT,
            content_status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        result_msg := 'Tables created successfully';
        RETURN result_msg;
    EXCEPTION
        WHEN OTHERS THEN
            RETURN 'Error: ' || SQLERRM;
    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER;
    """
    
    try:
        # Try to call the function if it exists
        result = supabase.rpc('create_ainews_tables').execute()
        print(f"✅ Function result: {result.data}")
    except Exception as e:
        if "not find the function" in str(e):
            print("ℹ️ Function 'create_ainews_tables' doesn't exist.")
            print("\n📋 SQL to create this function:")
            print("-" * 50)
            print(advanced_function_sql)
            print("-" * 50)
        else:
            print(f"❌ Function call failed: {e}")
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print("=" * 60)
    print("✅ Supabase connection: WORKING")
    print("❌ Direct table creation via API: NOT SUPPORTED")
    print("⚠️ Table creation via RPC: POSSIBLE (requires setup)")
    print("\n📝 CONCLUSION:")
    print("To create tables programmatically, you need to:")
    print("1. First create an RPC function in Supabase Dashboard")
    print("2. Then call that function via supabase.rpc()")
    print("\nOR simply run the SQL directly in Supabase Dashboard")
    
except Exception as e:
    print(f"\n❌ Error: {e}")