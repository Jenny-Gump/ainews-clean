"""
Test creating a simple table in Supabase via RPC
"""

import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Connect to Supabase
url = os.getenv('SUPABASE_URL')
service_key = os.getenv('SUPABASE_SERVICE_KEY')

print(f"🔗 Connecting to Supabase...")
supabase = create_client(url, service_key)

# Simple test table SQL
create_test_table_sql = """
CREATE TABLE IF NOT EXISTS claude_test_table (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
"""

try:
    print("📝 Creating test table via RPC...")
    
    # Call RPC function to create table
    result = supabase.rpc('execute_sql', {'query': create_test_table_sql}).execute()
    print(f"✅ RPC Result: {result.data}")
    
    # Wait a moment for cache to update
    import time
    time.sleep(2)
    
    # Try to insert test data
    print("\n🧪 Testing the new table...")
    test_data = {
        'message': f'Hello from Claude at {datetime.now().isoformat()}'
    }
    
    insert_result = supabase.table('claude_test_table').insert(test_data).execute()
    print(f"✅ Data inserted: {insert_result.data}")
    
    # Read it back
    read_result = supabase.table('claude_test_table').select('*').execute()
    print(f"\n📖 Table contents:")
    for row in read_result.data:
        print(f"  - ID: {row['id']}, Message: {row['message']}")
    
    print("\n✅ SUCCESS! I can create tables in Supabase!")
    
except Exception as e:
    print(f"❌ Error: {e}")