#!/bin/bash

# Stop Extract API Monitoring System

echo "🛑 Stopping Extract API Monitoring System..."

# Check if PID file exists
PID_FILE="monitoring.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    
    # Check if process is running
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Stopping monitoring process (PID: $PID)..."
        
        # Send SIGTERM first (graceful shutdown)
        kill -TERM "$PID"
        
        # Wait up to 10 seconds for graceful shutdown
        for i in {1..10}; do
            if ! ps -p "$PID" > /dev/null 2>&1; then
                echo "✅ Monitoring stopped gracefully"
                rm -f "$PID_FILE"
                exit 0
            fi
            sleep 1
        done
        
        # If still running, force kill
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "⚠️  Forcing shutdown..."
            kill -KILL "$PID"
            sleep 2
            
            if ! ps -p "$PID" > /dev/null 2>&1; then
                echo "✅ Monitoring stopped (forced)"
                rm -f "$PID_FILE"
            else
                echo "❌ Failed to stop monitoring process"
                exit 1
            fi
        fi
    else
        echo "⚠️  Process not running, removing stale PID file"
        rm -f "$PID_FILE"
    fi
else
    echo "⚠️  No PID file found, checking for running processes..."
    
    # Look for monitoring processes
    MONITORING_PIDS=$(ps aux | grep -E "python.*monitoring\.app|uvicorn.*monitoring" | grep -v grep | awk '{print $2}')
    
    if [ -n "$MONITORING_PIDS" ]; then
        echo "Found monitoring processes: $MONITORING_PIDS"
        for pid in $MONITORING_PIDS; do
            echo "Stopping PID $pid..."
            kill -TERM "$pid"
        done
        sleep 3
        
        # Check if any are still running
        STILL_RUNNING=$(ps aux | grep -E "python.*monitoring\.app|uvicorn.*monitoring" | grep -v grep | awk '{print $2}')
        if [ -n "$STILL_RUNNING" ]; then
            echo "⚠️  Force killing remaining processes..."
            for pid in $STILL_RUNNING; do
                kill -KILL "$pid"
            done
        fi
        echo "✅ Monitoring processes stopped"
    else
        echo "✅ No monitoring processes found"
    fi
fi

echo "🧹 Monitoring system stopped"