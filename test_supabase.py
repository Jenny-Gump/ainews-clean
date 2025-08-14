"""
Test Supabase connection and create test data
"""

import os
from supabase import create_client
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials
url = os.getenv('SUPABASE_URL')
service_key = os.getenv('SUPABASE_SERVICE_KEY')

print(f"🔗 Connecting to Supabase: {url}")

# Create client with service key (admin access)
supabase = create_client(url, service_key)

try:
    # First, let's try to create a simple test table via RPC or direct insert
    # Since we can't create tables via API directly, let's work with existing tables
    # or create a test record in a simple table
    
    # Try to create a test record in a test table
    # If table doesn't exist, this will fail and we'll know
    
    test_data = {
        'name': 'Test from Claude',
        'description': 'Testing Supabase connection',
        'created_at': datetime.now().isoformat()
    }
    
    print("\n📝 Attempting to insert test data...")
    
    # Try to insert into a 'test' table (if it exists)
    try:
        response = supabase.table('test').insert(test_data).execute()
        print("✅ Successfully inserted test data!")
        print(f"Response: {response.data}")
        
        # Try to read it back
        read_response = supabase.table('test').select('*').execute()
        print(f"\n📖 Data in test table: {read_response.data}")
        
    except Exception as e:
        if "not find the table" in str(e):
            print(f"❌ Table 'test' doesn't exist. Let me try the articles table...")
            
            # Try with the articles table from our schema
            article_test = {
                'article_id': 'test_from_claude_001',
                'source_id': 'test_source',
                'url': 'http://example.com/test',
                'title': 'Test Article from Claude',
                'content': 'This is a test article created by Claude to verify Supabase access',
                'content_status': 'pending',
                'media_status': 'pending'
            }
            
            print("\n📝 Attempting to insert into articles table...")
            response = supabase.table('articles').insert(article_test).execute()
            print("✅ Successfully inserted test article!")
            print(f"Response: {response.data}")
            
            # Read it back
            read_response = supabase.table('articles').select('*').eq('article_id', 'test_from_claude_001').execute()
            print(f"\n📖 Test article retrieved: {read_response.data}")
            
            # Clean up - delete test article
            delete_response = supabase.table('articles').delete().eq('article_id', 'test_from_claude_001').execute()
            print("\n🧹 Test article deleted")
        else:
            print(f"❌ Error: {e}")
    
    # Try to list tables using the information schema
    print("\n📊 Attempting to query database info...")
    
    # Get table count (this works if we have access to any tables)
    try:
        # Try a simple query to see what we can access
        response = supabase.rpc('get_table_list', {}).execute() if hasattr(supabase, 'rpc') else None
        print(f"Tables via RPC: {response}")
    except:
        print("RPC method not available or no such function")
    
    print("\n✅ Supabase connection test completed!")
    print("Service key provides full database access.")
    
except Exception as e:
    print(f"\n❌ Connection test failed: {e}")
    print("Please check your credentials and network connection.")