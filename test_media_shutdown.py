#!/usr/bin/env python3
"""
Test media processing with graceful shutdown
"""
import subprocess
import time
import signal
import sys

def test_media_shutdown():
    """Test media processing and interrupt it to check graceful shutdown"""
    print("Starting media processing test...")
    
    # Start the media processing
    cmd = ["python", "core/main.py", "--media-only"]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # Let it run for 15 seconds
    start_time = time.time()
    timeout = 15
    
    try:
        while time.time() - start_time < timeout:
            line = process.stdout.readline()
            if line:
                print(line.strip())
            
            if process.poll() is not None:
                break
                
        # Send interrupt signal
        print("\n>>> Sending interrupt signal...")
        process.send_signal(signal.SIGINT)
        
        # Wait for graceful shutdown and collect remaining output
        remaining_output = []
        try:
            for line in process.stdout:
                remaining_output.append(line.strip())
                print(line.strip())
        except:
            pass
            
        # Wait for process to finish
        process.wait(timeout=10)
        
        # Check if we got the summary statistics
        found_summary = any("ИТОГИ СКАЧИВАНИЯ МЕДИА" in line for line in remaining_output)
        
        if found_summary:
            print("\n✅ SUCCESS: Found summary statistics after interrupt!")
        else:
            print("\n❌ FAILED: No summary statistics found after interrupt")
            
    except subprocess.TimeoutExpired:
        print("\n❌ Process didn't terminate gracefully")
        process.kill()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        process.kill()
    finally:
        if process.poll() is None:
            process.kill()

if __name__ == "__main__":
    # Change to project directory
    import os
    os.chdir("/Users/skynet/Desktop/AI DEV/ainews-clean")
    
    # Activate venv
    activate_this = 'venv/bin/activate_this.py'
    if os.path.exists(activate_this):
        exec(open(activate_this).read(), {'__file__': activate_this})
    
    test_media_shutdown()