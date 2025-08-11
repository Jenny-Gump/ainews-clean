# RSS Discovery endpoints for dashboard control
from fastapi import HTTPException, Request
from fastapi import APIRouter
import logging
import subprocess
import sys
import os
import psutil
import sqlite3
import time

logger = logging.getLogger(__name__)
router = APIRouter()

# Global monitoring_db reference
monitoring_db = None

def set_monitoring_db(db):
    """Set the monitoring database instance"""
    global monitoring_db
    monitoring_db = db


def check_process_with_retry(cmdline_pattern, max_retries=3, delay=0.5):
    """
    Check if a process is running with retry logic.
    This helps detect processes that are just starting up.
    """
    for attempt in range(max_retries):
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                cmdline_str = ' '.join(cmdline) if cmdline else ''
                
                # Check if process matches the pattern
                if cmdline_str and cmdline_pattern(cmdline_str):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Wait before next retry (except on last attempt)
        if attempt < max_retries - 1:
            time.sleep(delay)
    
    return False

@router.post("/api/extract/rss/start")
async def start_rss_discovery():
    """Start RSS discovery process"""
    try:
        # Get the project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logger.info(f"Project root: {project_root}")
        
        # Use shell command for better background execution
        cmd = f"cd '{project_root}' && source venv/bin/activate && python core/main.py --rss-discover > /dev/null 2>&1 &"
        logger.info(f"Running command: {cmd}")
        
        # Execute via shell
        result = os.system(cmd)
        
        if result != 0:
            raise HTTPException(status_code=500, detail="Failed to start RSS discovery")
        
        # Give it a moment to start
        import time
        time.sleep(0.5)
        
        logger.info(f"RSS Discovery started")
        
        return {
            "status": "started",
            "message": "RSS discovery started",
            "command": cmd
        }
    except Exception as e:
        logger.error(f"Error starting RSS discovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/extract/rss/stop")
async def stop_rss_discovery():
    """Stop RSS discovery process"""
    try:
        # Find and kill any RSS discovery processes
        killed_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'main.py' in ' '.join(cmdline) and '--rss-discover' in ' '.join(cmdline):
                    os.kill(proc.info['pid'], 9)
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        if killed_count > 0:
            return {
                "status": "stopped",
                "message": f"Stopped {killed_count} RSS discovery process(es)"
            }
        else:
            return {
                "status": "not_running",
                "message": "No RSS discovery process found"
            }
    except Exception as e:
        logger.error(f"Error stopping RSS discovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/extract/status")
async def get_extract_status():
    """Get current extraction status including Change Tracking"""
    try:
        # Define pattern matchers for each process type
        def is_rss_process(cmdline_str):
            return (('main.py' in cmdline_str or 'core/main.py' in cmdline_str) and '--rss-discover' in cmdline_str) or \
                   ('run_rss_and_tracking.sh' in cmdline_str)
        
        def is_pipeline_process(cmdline_str):
            return ('main.py' in cmdline_str or 'core/main.py' in cmdline_str) and \
                   ('--single-pipeline' in cmdline_str or '--continuous-pipeline' in cmdline_str)
        
        def is_change_tracking(cmdline_str):
            return ('main.py' in cmdline_str or 'core/main.py' in cmdline_str) and '--change-tracking' in cmdline_str
        
        # Check if RSS discovery or RSS+Tracking script is running
        rss_running = check_process_with_retry(is_rss_process, max_retries=2, delay=0.3)
        
        # Check if single pipeline is running (with more retries for slower startup)
        single_pipeline_running = check_process_with_retry(is_pipeline_process, max_retries=3, delay=0.5)
        
        # Check if Change Tracking is running
        change_tracking_running = check_process_with_retry(is_change_tracking, max_retries=2, delay=0.3)
        
        return {
            "rss_discovery": "running" if rss_running else "stopped",
            "single_pipeline": "running" if single_pipeline_running else "stopped",
            "change_tracking": "running" if change_tracking_running else "stopped"
        }
    except Exception as e:
        logger.error(f"Error getting extract status: {e}")
        return {
            "rss_discovery": "unknown",
            "single_pipeline": "unknown",
            "change_tracking": "unknown",
            "error": str(e)
        }


@router.get("/api/extract/articles/stats")
async def get_articles_stats():
    """Get article statistics"""
    try:
        if not monitoring_db:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Get article counts by status from main database
        conn = sqlite3.connect(monitoring_db.ainews_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                content_status, 
                COUNT(*) as count
            FROM articles
            GROUP BY content_status
        """)
        
        status_counts = {}
        for row in cursor.fetchall():
            status_counts[row[0]] = row[1]
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM articles")
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total": total,
            "by_status": status_counts,
            "pending": status_counts.get('pending', 0),
            "parsed": status_counts.get('parsed', 0),
            "published": status_counts.get('published', 0),
            "failed": status_counts.get('failed', 0)
        }
    except Exception as e:
        logger.error(f"Error getting article stats: {e}")
        return {
            "total": 0,
            "by_status": {},
            "pending": 0,
            "parsed": 0,
            "published": 0,
            "failed": 0,
            "error": str(e)
        }


@router.get("/api/extract/last-parsed")
async def get_last_parsed():
    """Get global last parsed timestamp from global_config"""
    try:
        if not monitoring_db:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Get global_last_parsed from global_config table
        conn = sqlite3.connect(monitoring_db.ainews_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT value 
            FROM global_config 
            WHERE key = 'global_last_parsed'
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            # Convert to ISO format with timezone for consistency
            timestamp = result[0]
            if not timestamp.endswith('Z') and '+' not in timestamp:
                timestamp = timestamp + 'Z'
            
            return {
                "last_parsed": timestamp,
                "has_parsed": True,
                "source": "global_config"
            }
        else:
            return {
                "last_parsed": None,
                "has_parsed": False,
                "source": "global_config"
            }
    except Exception as e:
        logger.error(f"Error getting last parsed: {e}")
        return {
            "last_parsed": None,
            "has_parsed": False,
            "error": str(e)
        }


@router.put("/api/extract/last-parsed")
async def update_last_parsed(request: Request):
    """Update global last parsed timestamp"""
    try:
        data = await request.json()
        last_parsed = data.get("last_parsed") or data.get("timestamp")
        
        if not last_parsed:
            raise HTTPException(status_code=400, detail="last_parsed timestamp is required")
        
        # Validate timestamp format
        try:
            from datetime import datetime
            datetime.fromisoformat(last_parsed.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid timestamp format")
        
        # Update global last parsed timestamp in the database
        if not monitoring_db:
            raise HTTPException(status_code=500, detail="Database not available")
        
        conn = sqlite3.connect(monitoring_db.ainews_db_path)
        cursor = conn.cursor()
        
        # Update or insert global config
        cursor.execute("""
            INSERT OR REPLACE INTO global_config (key, value, description, updated_at) 
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, ('global_last_parsed', last_parsed, 'Global last parsed timestamp for all sources'))
        
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "message": "Global last parsed timestamp updated successfully",
            "timestamp": last_parsed
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update last parsed: {e}")
        raise HTTPException(status_code=500, detail=str(e))