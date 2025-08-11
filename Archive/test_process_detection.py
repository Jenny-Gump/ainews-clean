#!/usr/bin/env python3
"""Debug process detection"""

import psutil

print("Checking for single-pipeline process...")
print("-" * 50)

for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmdline = proc.info.get('cmdline', [])
        cmdline_str = ' '.join(cmdline) if cmdline else ''
        
        # Check if this looks like our process
        if 'python' in cmdline_str.lower() and 'main.py' in cmdline_str:
            print(f"Found Python process:")
            print(f"  PID: {proc.info['pid']}")
            print(f"  Cmdline: {cmdline_str}")
            print(f"  Has --single-pipeline: {'--single-pipeline' in cmdline_str}")
            print()
            
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass

print("\nChecking with exact matching logic from API:")
print("-" * 50)

def check_pipeline():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline', [])
            cmdline_str = ' '.join(cmdline) if cmdline else ''
            
            # API's logic
            if cmdline_str and ('main.py' in cmdline_str or 'core/main.py' in cmdline_str) and '--single-pipeline' in cmdline_str:
                return True, cmdline_str
        except:
            pass
    return False, None

found, cmdline = check_pipeline()
print(f"API logic result: {'FOUND' if found else 'NOT FOUND'}")
if cmdline:
    print(f"Cmdline: {cmdline}")