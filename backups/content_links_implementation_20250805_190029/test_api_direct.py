#!/usr/bin/env python3
"""
Test the API endpoints directly
"""
import requests
import json

# Test GET endpoint
print("🧪 Testing API Endpoints Directly...")

print("\n1. Testing GET /api/extract/last-parsed:")
try:
    response = requests.get("http://localhost:8001/api/extract/last-parsed")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   Error: {e}")

print("\n2. Testing PUT /api/extract/last-parsed:")
try:
    data = {"last_parsed": "2025-08-04T13:35:00Z"}
    response = requests.put(
        "http://localhost:8001/api/extract/last-parsed",
        headers={"Content-Type": "application/json"},
        data=json.dumps(data)
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   Error: {e}")

print("\n3. Testing GET again to see if updated:")
try:
    response = requests.get("http://localhost:8001/api/extract/last-parsed")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   Error: {e}")

print("\n4. Checking database directly:")
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.database import Database

db = Database()
db_value = db.get_global_last_parsed()
print(f"   Database value: {db_value}")