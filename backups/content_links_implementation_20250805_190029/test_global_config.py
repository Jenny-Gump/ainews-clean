#!/usr/bin/env python3
"""
Test script for global_config implementation
"""
import sys
import os

# Add core directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import Database
from datetime import datetime, timezone

def test_global_config():
    """Test global config functionality"""
    print("Testing Global Config System...")
    
    # Initialize database (this will create global_config table)
    db = Database()
    
    # Test getting default global last_parsed
    print(f"Default global_last_parsed: {db.get_global_last_parsed()}")
    
    # Test setting a new value
    current_time = datetime.now(timezone.utc)
    timestamp_str = current_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    print(f"Setting global_last_parsed to: {timestamp_str}")
    db.set_global_last_parsed(timestamp_str)
    
    # Test getting the updated value
    retrieved = db.get_global_last_parsed()
    print(f"Retrieved global_last_parsed: {retrieved}")
    
    # Verify they match
    if retrieved == timestamp_str:
        print("✅ Global config system working correctly!")
    else:
        print("❌ Global config system not working properly")
        print(f"Expected: {timestamp_str}")
        print(f"Got: {retrieved}")
    
    # Test other config values
    print("\nTesting other config values...")
    db.set_global_config('test_key', 'test_value', 'Test configuration')
    retrieved_test = db.get_global_config('test_key')
    print(f"Test config: {retrieved_test}")
    
    if retrieved_test == 'test_value':
        print("✅ Generic config system working correctly!")
    else:
        print("❌ Generic config system not working")

if __name__ == "__main__":
    test_global_config()