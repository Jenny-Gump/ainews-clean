"""
Monitoring API module - refactored from monolithic api.py into modular structure

This module aggregates all API routers:
- control: System control and dashboard endpoints
- articles: Article management and search
- memory: Memory monitoring and system resources
- logs: Log management and viewing
- rss: RSS feed monitoring
- profiling: Memory profiling and analysis
"""
from fastapi import APIRouter
import os

# Import core utilities and database setup
from .core import set_monitoring_db

# Import all routers
from .control import router as control_router
from .articles import router as articles_router
from .memory import router as memory_router
from .pipeline import router as pipeline_router

# Create additional routers for functionality not yet moved
from fastapi import HTTPException, Query, Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json

# Import core utilities for additional routers
from .core import (
    get_monitoring_db, get_monitoring_db_connection, get_recent_logs_from_file,
    get_recent_logs_from_db, format_timestamp, handle_db_error, logger
)

# Logs router
logs_router = APIRouter(prefix="/api/logs", tags=["logs"])

@logs_router.get("/recent")
async def get_logs_recent(limit: int = Query(100, ge=1, le=500)):
    """Get recent logs for dashboard - simplified version"""
    try:
        logs = []
        
        # Try to get logs from the main log file
        log_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs', 'ai_news_parser.log')
        
        if os.path.exists(log_file_path):
            logs = get_recent_logs_from_file(log_file_path, limit)
        
        # If no file logs, get from monitoring database error_logs
        if not logs:
            logs = get_recent_logs_from_db(limit)
        
        return {"logs": logs[:limit]}
        
    except Exception as e:
        # Return empty logs on error
        return {"logs": [], "error": str(e)}

# RSS router
rss_router = APIRouter(prefix="/api/rss", tags=["rss"])

@rss_router.get("/status")
async def get_rss_status():
    """Get overall RSS system status"""
    try:
        from .core import get_ainews_db_connection
        
        with get_ainews_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get source counts
            cursor.execute("SELECT COUNT(*) FROM sources WHERE type = 'rss'")
            rss_sources = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sources WHERE type = 'rss' AND status = 'active'")
            active_rss = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM articles 
                WHERE source_id IN (SELECT source_id FROM sources WHERE type = 'rss')
                AND DATE(created_at) = DATE('now')
            """)
            articles_today = cursor.fetchone()[0]
        
        return {
            "total_rss_sources": rss_sources,
            "active_rss_sources": active_rss,
            "articles_today": articles_today,
            "status": "operational" if active_rss > 0 else "no_active_sources",
            "timestamp": format_timestamp(datetime.now())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get RSS status: {str(e)}")

@rss_router.get("/feeds")
async def get_rss_feeds():
    """Get detailed status for all RSS feeds"""
    try:
        monitoring_db = get_monitoring_db()
        source_metrics = monitoring_db.get_source_metrics()
        
        # Filter RSS sources
        rss_feeds = [s for s in source_metrics if s.type == 'rss']
        
        feeds_data = []
        for feed in rss_feeds:
            feeds_data.append({
                "source_id": feed.source_id,
                "name": feed.name,
                "url": feed.url,
                "status": feed.status,
                "last_status": feed.last_status,
                "success_rate": feed.success_rate,
                "recent_articles_24h": feed.recent_articles_24h,
                "recent_errors_24h": feed.recent_errors_24h,
                "total_articles": feed.total_articles,
                "last_successful_parse": feed.last_successful_parse.isoformat() if feed.last_successful_parse else None,
                "last_error": feed.last_error.isoformat() if feed.last_error else None
            })
        
        return {
            "feeds": feeds_data,
            "total": len(feeds_data),
            "timestamp": format_timestamp(datetime.now())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get RSS feeds: {str(e)}")

# Profiling router
profiling_router = APIRouter(prefix="/api/profiling", tags=["profiling"])

@profiling_router.get("/memory/snapshot")
async def get_memory_snapshot():
    """Get a detailed memory snapshot of all Python objects"""
    try:
        import gc
        import sys
        from collections import defaultdict
        
        # Force garbage collection
        gc.collect()
        
        # Get object counts by type
        object_counts = defaultdict(int)
        total_objects = 0
        
        for obj in gc.get_objects():
            obj_type = type(obj).__name__
            object_counts[obj_type] += 1
            total_objects += 1
        
        # Sort by count
        sorted_counts = sorted(object_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Get memory info
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            memory_data = {
                "rss_mb": round(memory_info.rss / (1024 * 1024), 2),
                "vms_mb": round(memory_info.vms / (1024 * 1024), 2)
            }
        except ImportError:
            memory_data = {"error": "psutil not available"}
        
        return {
            "total_objects": total_objects,
            "objects_by_type": dict(sorted_counts[:20]),  # Top 20 types
            "memory_info": memory_data,
            "gc_stats": {
                "collections": gc.get_count(),
                "garbage_count": len(gc.garbage)
            },
            "timestamp": format_timestamp(datetime.now())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memory snapshot: {str(e)}")

# Additional endpoints that need to be preserved
@control_router.get("/logs/recent")
async def get_recent_logs(
    level: Optional[str] = Query(None, description="Filter by log level"),
    source: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(100, description="Number of logs to return"),
    search: Optional[str] = Query(None, description="Search in log messages")
):
    """Get recent log entries with filtering"""
    try:
        # Simplified version - just return from database
        logs = get_recent_logs_from_db(limit)
        
        # Apply simple filters
        if level:
            logs = [log for log in logs if log.get('level', '').lower() == level.lower()]
        
        if search:
            logs = [log for log in logs if search.lower() in log.get('message', '').lower()]
        
        return {
            "status": "running",
            "total_in_buffer": len(logs),
            "returned": len(logs[:limit]),
            "logs": logs[:limit]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Last parsed management endpoints - moved from control
@control_router.get("/sources/{source_id}/last-parsed")
async def get_source_last_parsed(source_id: str):
    """Get last parsed timestamp for a specific source"""
    try:
        from .core import get_ainews_db_connection, get_global_last_parsed
        
        global_last_parsed = get_global_last_parsed()
        
        with get_ainews_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT source_id, name FROM sources WHERE source_id = ?",
                (source_id,)
            )
            result = cursor.fetchone()
            
        if result:
            return {
                "source_id": result[0],
                "source_name": result[1],
                "last_parsed": global_last_parsed  # Use global timestamp
            }
        else:
            raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get last parsed: {str(e)}")

@control_router.put("/sources/{source_id}/last-parsed")
async def update_source_last_parsed(
    source_id: str,
    last_parsed: str = Query(..., description="Last parsed timestamp in ISO format")
):
    """Update last parsed timestamp for a specific source"""
    try:
        from .core import validate_timestamp, get_ainews_db_connection
        
        # Validate timestamp format
        if not validate_timestamp(last_parsed):
            raise HTTPException(status_code=400, detail="Invalid timestamp format. Use ISO format.")
        
        with get_ainews_db_connection() as conn:
            # Check if source exists
            cursor = conn.cursor()
            cursor.execute(
                "SELECT source_id FROM sources WHERE source_id = ?",
                (source_id,)
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
            
            # Update global last_parsed (affects all sources)
            cursor.execute(
                "INSERT OR REPLACE INTO global_config (key, value, description, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                ('global_last_parsed', last_parsed, 'Global last parsed timestamp for all sources')
            )
            conn.commit()
            
        return {
            "success": True,
            "source_id": source_id,
            "last_parsed": last_parsed,
            "message": f"Global last parsed timestamp updated (affects all sources)"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update last parsed: {str(e)}")

@control_router.post("/sources/last-parsed/bulk")
async def bulk_update_last_parsed(updates: List[Dict[str, str]]):
    """Bulk update last parsed timestamps for multiple sources"""
    try:
        from .core import get_ainews_db_connection, validate_timestamp
        
        # Validate all timestamps first
        for update in updates:
            if not validate_timestamp(update.get('last_parsed', '')):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid timestamp format for source {update.get('source_id')}"
                )
        
        success_count = 0
        failed_sources = []
        
        with get_ainews_db_connection() as conn:
            for update in updates:
                cursor = conn.execute(
                    "UPDATE sources SET last_parsed = ? WHERE source_id = ?",
                    (update['last_parsed'], update['source_id'])
                )
                if cursor.rowcount > 0:
                    success_count += 1
                else:
                    failed_sources.append(update['source_id'])
            
            conn.commit()
        
        return {
            "success": True,
            "total_requested": len(updates),
            "success_count": success_count,
            "failed_sources": failed_sources,
            "message": f"Updated {success_count} sources"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk update last parsed: {str(e)}")

# Create main router that includes all sub-routers
router = APIRouter()

# Include all routers
router.include_router(control_router)
router.include_router(articles_router)  
router.include_router(memory_router)
router.include_router(pipeline_router)  # Single pipeline monitoring
router.include_router(logs_router)
router.include_router(rss_router)
router.include_router(profiling_router)

# Export individual routers for backward compatibility
__all__ = [
    'router',           # Main aggregated router
    'control_router',   # System control (was main monitoring_router)
    'articles_router',  # Articles management
    'memory_router',    # Memory and system resources
    'pipeline_router',  # Single pipeline monitoring
    'logs_router',      # Logs viewing
    'rss_router',       # RSS monitoring  
    'profiling_router', # Memory profiling
    'set_monitoring_db' # Database setup function
]

# Expose the database setup function
__all__.append('set_monitoring_db')