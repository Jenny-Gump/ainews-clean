#!/usr/bin/env python3
"""
Test script to verify the dashboard button fix.
This script will:
1. Start the single pipeline via API
2. Check the process status repeatedly
3. Verify the grace period is working
"""

import requests
import time
import subprocess
import psutil

BASE_URL = "http://localhost:8001"

def check_process_running():
    """Check if single pipeline process is running"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            cmdline_str = ' '.join(cmdline) if cmdline else ''
            if ('main.py' in cmdline_str or 'core/main.py' in cmdline_str) and '--single-pipeline' in cmdline_str:
                return True
        except:
            pass
    return False

def test_button_fix():
    print("🧪 Testing dashboard button fix...")
    print("-" * 50)
    
    # Step 1: Check initial status
    print("1. Checking initial status...")
    response = requests.get(f"{BASE_URL}/api/extract/status")
    status = response.json()
    print(f"   Initial status: {status}")
    
    # Step 2: Start single pipeline
    print("\n2. Starting single pipeline via API...")
    response = requests.post(f"{BASE_URL}/api/pipeline/start-single")
    if response.ok:
        print("   ✅ Pipeline start request sent")
    else:
        print(f"   ❌ Failed to start: {response.text}")
        return
    
    # Step 3: Check status repeatedly during grace period
    print("\n3. Checking status during 15-second grace period...")
    start_time = time.time()
    checks = []
    
    while time.time() - start_time < 16:
        elapsed = time.time() - start_time
        response = requests.get(f"{BASE_URL}/api/extract/status")
        status = response.json()
        process_running = check_process_running()
        
        checks.append({
            'time': round(elapsed, 1),
            'api_status': status['single_pipeline'],
            'process_found': process_running
        })
        
        print(f"   [{elapsed:5.1f}s] API: {status['single_pipeline']:10s} | Process: {'Found' if process_running else 'Not found'}")
        time.sleep(2)
    
    # Step 4: Analyze results
    print("\n4. Analysis:")
    print("-" * 50)
    
    # Check if process was eventually detected
    process_detected_at = None
    for check in checks:
        if check['process_found']:
            process_detected_at = check['time']
            break
    
    if process_detected_at:
        print(f"   ✅ Process detected after {process_detected_at} seconds")
    else:
        print("   ⚠️  Process was not detected during test")
    
    # Check if API status changed during grace period
    status_changes = []
    for i in range(1, len(checks)):
        if checks[i]['api_status'] != checks[i-1]['api_status']:
            status_changes.append(f"{checks[i-1]['api_status']} → {checks[i]['api_status']} at {checks[i]['time']}s")
    
    if status_changes:
        print(f"   ⚠️  Status changed during grace period:")
        for change in status_changes:
            print(f"      - {change}")
    else:
        print("   ✅ Status remained stable during grace period")
    
    # Step 5: Stop the pipeline
    print("\n5. Stopping pipeline...")
    response = requests.post(f"{BASE_URL}/api/pipeline/stop")
    if response.ok:
        print("   ✅ Pipeline stopped")
    else:
        print(f"   ❌ Failed to stop: {response.text}")
    
    print("\n" + "=" * 50)
    print("Test complete!")

if __name__ == "__main__":
    test_button_fix()