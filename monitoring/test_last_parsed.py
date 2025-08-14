#!/usr/bin/env python3
"""
Test script for Last Parsed system with Supabase
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

print("Testing Last Parsed System with Supabase")
print("=" * 50)

# Test 1: Check environment variables
print("\n1. Environment Variables:")
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')
print(f"   SUPABASE_URL: {url}")
print(f"   Key exists: {bool(key)}")

if not key:
    print("   ERROR: No Supabase key found!")
    sys.exit(1)

# Test 2: Connect to Supabase
print("\n2. Supabase Connection:")
try:
    from supabase import create_client, Client
    supabase = create_client(url, key)
    print("   ✅ Connected to Supabase")
except Exception as e:
    print(f"   ❌ Connection failed: {e}")
    sys.exit(1)

# Test 3: Read current value
print("\n3. Read Current Value:")
try:
    result = supabase.table('global_config').select('value').eq('key', 'global_last_parsed').single().execute()
    current_value = result.data.get('value') if result.data else None
    print(f"   Current value: {current_value}")
except Exception as e:
    print(f"   ❌ Read failed: {e}")

# Test 4: Update value
print("\n4. Update Value:")
new_value = "2025-08-14T18:00:00Z"
try:
    from datetime import datetime
    update_result = supabase.table('global_config').upsert({
        'key': 'global_last_parsed',
        'value': new_value,
        'description': 'Global last parsed timestamp for all sources',
        'updated_at': datetime.now().isoformat()
    }, on_conflict='key').execute()
    print(f"   ✅ Updated to: {new_value}")
except Exception as e:
    print(f"   ❌ Update failed: {e}")

# Test 5: Verify update
print("\n5. Verify Update:")
try:
    verify_result = supabase.table('global_config').select('value').eq('key', 'global_last_parsed').single().execute()
    verified_value = verify_result.data.get('value') if verify_result.data else None
    if verified_value == new_value:
        print(f"   ✅ Value successfully updated to: {verified_value}")
    else:
        print(f"   ❌ Value mismatch! Expected: {new_value}, Got: {verified_value}")
except Exception as e:
    print(f"   ❌ Verification failed: {e}")

# Test 6: Test API endpoints
print("\n6. Test API Endpoints:")
import requests

base_url = "http://localhost:8001"

# Test GET endpoint
print("   Testing GET /api/extract/last-parsed:")
try:
    response = requests.get(f"{base_url}/api/extract/last-parsed")
    if response.status_code == 200:
        data = response.json()
        print(f"     ✅ Response: {data}")
    else:
        print(f"     ❌ Status code: {response.status_code}")
except Exception as e:
    print(f"     ❌ Request failed: {e}")

# Test PUT endpoint
print("   Testing PUT /api/extract/last-parsed:")
test_timestamp = "2025-08-14T19:00:00Z"
try:
    response = requests.put(
        f"{base_url}/api/extract/last-parsed",
        json={"last_parsed": test_timestamp}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"     ✅ Response: {data}")
        
        # Verify in database
        verify = supabase.table('global_config').select('value').eq('key', 'global_last_parsed').single().execute()
        db_value = verify.data.get('value') if verify.data else None
        if db_value == test_timestamp:
            print(f"     ✅ Database updated correctly: {db_value}")
        else:
            print(f"     ❌ Database not updated! Expected: {test_timestamp}, Got: {db_value}")
    else:
        print(f"     ❌ Status code: {response.status_code}")
except Exception as e:
    print(f"     ❌ Request failed: {e}")

print("\n" + "=" * 50)
print("Testing complete!")