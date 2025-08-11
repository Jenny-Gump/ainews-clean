#!/bin/bash

# Start Extract API Monitoring System

echo "🚀 Starting Extract API Monitoring System..."

# Check if virtual environment exists
if [ ! -d "../venv" ]; then
    echo "❌ Virtual environment not found. Please create it first:"
    echo "   python -m venv venv && source venv/bin/activate"
    echo "   pip install -r monitoring/requirements.txt"
    exit 1
fi

# Activate virtual environment
source ../venv/bin/activate

# Move to project root for proper module resolution
cd ..

# Install requirements if needed
pip install -q -r monitoring/requirements.txt

# Create logs directory if needed
mkdir -p logs/monitoring

# Function for log rotation
rotate_logs() {
    local log_file="logs/monitoring/system.log"
    local max_size=$((50 * 1024 * 1024))  # 50MB
    
    if [ -f "$log_file" ] && [ $(stat -f%z "$log_file" 2>/dev/null || echo 0) -gt $max_size ]; then
        # Rotate logs: keep last 5 files
        for i in {4..1}; do
            if [ -f "${log_file}.${i}" ]; then
                mv "${log_file}.${i}" "${log_file}.$((i+1))"
            fi
        done
        if [ -f "$log_file" ]; then
            mv "$log_file" "${log_file}.1"
        fi
        echo "🔄 Log rotated (exceeded 50MB)"
    fi
}

# Rotate logs before starting
rotate_logs

# Start monitoring server with log rotation
echo "📊 Starting monitoring server on http://localhost:8001"

# Set process title and start monitoring 
exec -a "ainews-monitoring-dashboard" python -m monitoring.app 2>&1 | tee -a logs/monitoring/system.log