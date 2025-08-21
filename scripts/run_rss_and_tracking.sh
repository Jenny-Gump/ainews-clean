#!/bin/bash

# Последовательный запуск RSS Discovery и Change Tracking
# Этот скрипт запускается из мониторинга для полного цикла сбора новостей

BASE_DIR="/Users/skynet/Desktop/AI DEV/ainews-clean"
cd "$BASE_DIR"

# Process ID file for tracking
PID_FILE="$BASE_DIR/data/rss_tracking_process.pid"
echo $$ > "$PID_FILE"

# Cleanup function
cleanup() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Received termination signal, cleaning up..."
    
    # Kill any child processes
    if [ ! -z "$RSS_PID" ]; then
        kill $RSS_PID 2>/dev/null
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Terminated RSS discovery process"
    fi
    
    if [ ! -z "$TRACKING_PID" ]; then
        kill $TRACKING_PID 2>/dev/null
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Terminated change tracking process"
    fi
    
    if [ ! -z "$EXPORT_PID" ]; then
        kill $EXPORT_PID 2>/dev/null
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Terminated export process"
    fi
    
    # Remove PID file
    rm -f "$PID_FILE"
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] RSS + Change Tracking stopped by signal"
    
    # Use exec to ensure complete termination
    exec true
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT SIGHUP

# Initialize process variables
RSS_PID=""
TRACKING_PID=""
EXPORT_PID=""

# Set Python path for imports
export PYTHONPATH="$BASE_DIR:$PYTHONPATH"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting RSS + Change Tracking integration (PID: $$)"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting RSS Discovery..."

# 1. RSS Discovery
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting RSS Discovery..."
python3 core/main.py --rss-discover &
RSS_PID=$!
wait $RSS_PID
RSS_EXIT_CODE=$?
RSS_PID=""  # Clear PID after completion

if [ $RSS_EXIT_CODE -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] RSS Discovery completed successfully"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Waiting 2 seconds before Change Tracking..."
    sleep 2
    
    # 2. Change Tracking Scan
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Change Tracking scan..."
    
    # Note: Detailed per-source logging is now handled inside the Change Tracking module
    # The module will log each source with progress [1/50], [2/50], etc.
    
    # Используем последовательное сканирование для полного контроля и логирования
    python3 core/main.py --change-tracking --scan --sequential &
    TRACKING_PID=$!
    wait $TRACKING_PID
    SCAN_EXIT_CODE=$?
    TRACKING_PID=""  # Clear PID after completion
    
    # Log exit code for debugging
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Change Tracking scan exited with code: $SCAN_EXIT_CODE"
    
    if [ $SCAN_EXIT_CODE -eq 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Change Tracking scan completed successfully"
        
        # Log scan completion
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Change Tracking scan completed"
        
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Waiting 3 seconds before export..."
        sleep 3
        
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting export of new articles..."
        
        # Log export start
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📤 Exporting Change Tracking articles"
        
        # 3. Export found URLs from Change Tracking (правильная функция)
        python3 core/main.py --change-tracking --export-articles &
        EXPORT_PID=$!
        wait $EXPORT_PID
        EXPORT_EXIT_CODE=$?
        EXPORT_PID=""  # Clear PID after completion
        
        if [ $EXPORT_EXIT_CODE -eq 0 ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Change Tracking export completed successfully"
            
            # Log export completion
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Change Tracking export completed"
            
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Full news collection cycle completed!"
            
            # Clean up PID file
            rm -f "$PID_FILE"
            
            # Use exec to replace the shell process completely
            exec true
        else
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Change Tracking export failed with code $EXPORT_EXIT_CODE"
            exit $EXPORT_EXIT_CODE
        fi
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Change Tracking scan failed with code $SCAN_EXIT_CODE"
        exit $SCAN_EXIT_CODE
    fi
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: RSS Discovery failed with code $RSS_EXIT_CODE"
    exit $RSS_EXIT_CODE
fi