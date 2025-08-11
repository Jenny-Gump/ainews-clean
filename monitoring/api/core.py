"""
Core utilities and shared functionality for monitoring API
"""
import sqlite3
import os
import json
from datetime import datetime, timedelta
from pathlib import Path as PathLib
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from fastapi import HTTPException, APIRouter

# Add parent directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app_logging import get_logger

logger = get_logger('monitoring.api.core')

# Global database instances - will be set by app.py
monitoring_db = None
monitoring_integration = None

def set_monitoring_db(db):
    """Set the monitoring database instance"""
    global monitoring_db, monitoring_integration
    monitoring_db = db
    from ..integration import get_monitoring_integration
    monitoring_integration = get_monitoring_integration(db)

def get_monitoring_db():
    """Get the monitoring database instance"""
    if monitoring_db is None:
        raise HTTPException(status_code=500, detail="Monitoring database not initialized")
    return monitoring_db

def get_monitoring_integration():
    """Get the monitoring integration instance"""
    if monitoring_integration is None:
        raise HTTPException(status_code=500, detail="Monitoring integration not initialized")
    return monitoring_integration

# Pydantic models for API responses
class SystemOverview(BaseModel):
    """System overview for dashboard"""
    total_sources: int
    active_sources: int
    error_sources: int
    blocked_sources: int
    total_articles: int
    articles_24h: int
    articles_7d: int
    total_media_files: int
    media_downloaded: int
    media_failed: int
    database_size_mb: float
    avg_parse_time_ms: float
    success_rate: float
    last_update: str

class SourceDetail(BaseModel):
    """Source detail model"""
    source_id: str
    name: str
    status: str
    success_rate: float
    recent_errors: int

class ProcessControlResponse(BaseModel):
    """Response for process control operations"""
    success: bool
    message: str
    status: Optional[str] = None
    timestamp: str

class BulkUpdateRequest(BaseModel):
    """Request model for bulk updates"""
    source_id: str
    last_parsed: str

class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    database_connected: bool
    monitoring_active: bool
    total_sources: int
    active_sources: int

# Database utility functions
def get_ainews_db_connection():
    """Get connection to main ainews database"""
    try:
        # Try to use monitoring_db if available
        if monitoring_db and hasattr(monitoring_db, 'ainews_db_path'):
            db_path = PathLib(monitoring_db.ainews_db_path)
        else:
            # Fallback to direct path
            db_path = PathLib(__file__).parent.parent.parent / "data" / "ainews.db"
        
        if not db_path.exists():
            raise HTTPException(status_code=404, detail=f"Main database not found at {db_path}")
        return sqlite3.connect(str(db_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

def get_monitoring_db_connection():
    """Get connection to monitoring database"""
    try:
        # Try to use monitoring_db if available
        if monitoring_db and hasattr(monitoring_db, 'db_path'):
            db_path = str(PathLib(monitoring_db.db_path))
        else:
            # Fallback to direct path
            db_path = str(PathLib(__file__).parent.parent.parent / "data" / "monitoring.db")
        
        return sqlite3.connect(db_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Monitoring database connection failed: {str(e)}")

def validate_timestamp(timestamp_str: str) -> bool:
    """Validate ISO timestamp format"""
    try:
        datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False

def format_timestamp(dt: datetime) -> str:
    """Format datetime to ISO string"""
    return dt.isoformat()

def calculate_success_rate(successful: int, total: int) -> float:
    """Calculate success rate percentage"""
    if total == 0:
        return 0.0
    return (successful / total) * 100

# Common error handling
def handle_db_error(e: Exception, operation: str = "database operation"):
    """Handle database errors consistently"""
    logger.error(f"Database error during {operation}: {str(e)}")
    raise HTTPException(status_code=500, detail=f"Database error during {operation}")

def handle_validation_error(field: str, value: Any, expected: str):
    """Handle validation errors consistently"""
    raise HTTPException(
        status_code=400, 
        detail=f"Invalid {field}: {value}. Expected {expected}"
    )

# Log file utilities
def get_recent_logs_from_file(log_file_path: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get recent logs from file"""
    logs = []
    
    if not os.path.exists(log_file_path):
        return logs
    
    try:
        with open(log_file_path, 'r') as f:
            lines = f.readlines()
            recent_lines = lines[-limit:] if len(lines) > limit else lines
            
            for line in reversed(recent_lines):
                try:
                    log_data = json.loads(line.strip())
                    logs.append({
                        "timestamp": log_data.get("timestamp", ""),
                        "level": log_data.get("level", "INFO"),
                        "message": log_data.get("message", line.strip())
                    })
                except json.JSONDecodeError:
                    logs.append({
                        "timestamp": datetime.now().isoformat(),
                        "level": "INFO",
                        "message": line.strip()
                    })
                
                if len(logs) >= limit:
                    break
    except Exception as e:
        logger.error(f"Error reading log file {log_file_path}: {str(e)}")
    
    return logs

def get_recent_logs_from_db(limit: int = 100) -> List[Dict[str, Any]]:
    """Get recent logs from monitoring database"""
    logs = []
    
    try:
        with get_monitoring_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, error_type as level, error_message as message
                FROM error_logs
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            for row in cursor.fetchall():
                logs.append({
                    "timestamp": row[0],
                    "level": row[1] or "ERROR",
                    "message": row[2]
                })
    except Exception as e:
        logger.error(f"Error reading logs from database: {str(e)}")
    
    return logs

# Source management utilities
def get_source_by_id(source_id: str) -> Dict[str, Any]:
    """Get source details by ID"""
    try:
        with get_ainews_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT source_id, name, url, type, status FROM sources WHERE source_id = ?",
                (source_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
            
            return {
                "source_id": result[0],
                "name": result[1],
                "url": result[2],
                "type": result[3],
                "status": result[4]
            }
    except HTTPException:
        raise
    except Exception as e:
        handle_db_error(e, "getting source details")

def toggle_source_status(source_id: str) -> Dict[str, Any]:
    """Toggle source active/inactive status"""
    try:
        with get_ainews_db_connection() as conn:
            # Get current status
            cursor = conn.cursor()
            cursor.execute(
                "SELECT status FROM sources WHERE source_id = ?",
                (source_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
            
            current_status = result[0]
            new_status = 'inactive' if current_status == 'active' else 'active'
            
            # Update status
            cursor.execute(
                "UPDATE sources SET status = ? WHERE source_id = ?",
                (new_status, source_id)
            )
            conn.commit()
            
            return {
                "source_id": source_id,
                "old_status": current_status,
                "new_status": new_status,
                "success": True
            }
    except HTTPException:
        raise
    except Exception as e:
        handle_db_error(e, "toggling source status")

def get_global_last_parsed() -> str:
    """Get global last parsed timestamp"""
    try:
        with get_ainews_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM global_config WHERE key = 'global_last_parsed'"
            )
            result = cursor.fetchone()
            return result[0] if result else "2025-08-01T00:00:00Z"
    except Exception as e:
        logger.error(f"Error getting global last parsed: {str(e)}")
        return "2025-08-01T00:00:00Z"

def update_global_last_parsed(timestamp: str) -> bool:
    """Update global last parsed timestamp"""
    try:
        if not validate_timestamp(timestamp):
            return False
        
        with get_ainews_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO global_config (key, value, description, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                ('global_last_parsed', timestamp, 'Global last parsed timestamp for all sources')
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating global last parsed: {str(e)}")
        return False

# Article utilities
def get_articles_with_filters(
    search: Optional[str] = None,
    status: Optional[str] = None,
    source_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = 1,
    limit: int = 50
) -> Dict[str, Any]:
    """Get articles with various filters"""
    try:
        with get_ainews_db_connection() as conn:
            # Build query
            conditions = []
            params = []
            
            if search:
                conditions.append("(title LIKE ? OR content LIKE ?)")
                search_term = f"%{search}%"
                params.extend([search_term, search_term])
            
            if status:
                conditions.append("content_status = ?")
                params.append(status)
            
            if source_id:
                conditions.append("source_id = ?")
                params.append(source_id)
            
            if date_from:
                conditions.append("published_date >= ?")
                params.append(date_from)
            
            if date_to:
                conditions.append("published_date <= ?")
                params.append(date_to)
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            # Count total
            count_query = f"SELECT COUNT(*) FROM articles {where_clause}"
            cursor = conn.cursor()
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
            # Get paginated results
            offset = (page - 1) * limit
            query = f"""
                SELECT article_id, title, url, source_id, published_date, 
                       content_status, created_at, 
                       CASE WHEN media_count > 0 THEN 1 ELSE 0 END as has_media
                FROM articles 
                {where_clause}
                ORDER BY published_date DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            articles = []
            
            for row in cursor.fetchall():
                articles.append({
                    "article_id": row[0],
                    "title": row[1],
                    "url": row[2],
                    "source_id": row[3],
                    "published_at": row[4],  # published_date mapped to published_at
                    "status": row[5],  # content_status mapped to status
                    "created_at": row[6],
                    "has_media": bool(row[7])
                })
            
            return {
                "articles": articles,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit
            }
    
    except Exception as e:
        handle_db_error(e, "getting articles")

# System resource utilities
def get_system_resources() -> Dict[str, Any]:
    """Get current system resources"""
    try:
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_total_gb = memory.total / (1024**3)
        memory_used_gb = memory.used / (1024**3)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_total_gb = disk.total / (1024**3)
        disk_used_gb = disk.used / (1024**3)
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count
            },
            "memory": {
                "percent": memory_percent,
                "total_gb": round(memory_total_gb, 2),
                "used_gb": round(memory_used_gb, 2),
                "available_gb": round(memory.available / (1024**3), 2)
            },
            "disk": {
                "percent": disk_percent,
                "total_gb": round(disk_total_gb, 2),
                "used_gb": round(disk_used_gb, 2),
                "free_gb": round(disk.free / (1024**3), 2)
            },
            "timestamp": datetime.now().isoformat()
        }
    except ImportError:
        return {
            "error": "psutil not available",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system resources: {str(e)}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Process management utilities
def get_process_status() -> Dict[str, Any]:
    """Get current process status"""
    try:
        from ..process_manager import get_process_manager
        process_manager = get_process_manager()
        
        return {
            "status": process_manager.get_status().value,
            "is_running": process_manager.is_running(),
            "is_paused": process_manager.is_paused(),
            "can_start": process_manager.can_start(),
            "can_pause": process_manager.can_pause(),
            "can_resume": process_manager.can_resume(),
            "can_stop": process_manager.can_stop(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting process status: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Memory monitoring utilities
def cleanup_memory() -> Dict[str, Any]:
    """Perform memory cleanup"""
    try:
        from ..memory_monitor import get_memory_monitor
        memory_monitor = get_memory_monitor()
        
        if memory_monitor:
            cleanup_result = memory_monitor.cleanup_memory()
            return {
                "success": True,
                "message": "Memory cleanup completed",
                "freed_mb": cleanup_result.get("freed_mb", 0),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "Memory monitor not available",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error during memory cleanup: {str(e)}")
        return {
            "success": False,
            "message": f"Memory cleanup failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# RSS/Source discovery utilities
def get_rss_sources_summary() -> Dict[str, Any]:
    """Get RSS sources summary"""
    try:
        with get_ainews_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get sources by type
            cursor.execute("""
                SELECT type, status, COUNT(*) as count
                FROM sources 
                GROUP BY type, status
            """)
            
            sources_breakdown = {}
            total_sources = 0
            
            for row in cursor.fetchall():
                source_type = row[0] or 'unknown'
                status = row[1]
                count = row[2]
                total_sources += count
                
                if source_type not in sources_breakdown:
                    sources_breakdown[source_type] = {}
                sources_breakdown[source_type][status] = count
            
            return {
                "total_sources": total_sources,
                "sources_breakdown": sources_breakdown,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        handle_db_error(e, "getting RSS sources summary")


# Create router for database endpoints
db_router = APIRouter(prefix="/api/db", tags=["database"])

@db_router.post("/initialize")
async def initialize_database():
    """Initialize and test database connections"""
    try:
        results = {
            "ainews_db": False,
            "monitoring_db": False,
            "errors": []
        }
        
        # Test main database
        try:
            conn = get_ainews_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles")
            article_count = cursor.fetchone()[0]
            conn.close()
            results["ainews_db"] = True
            results["article_count"] = article_count
        except Exception as e:
            results["errors"].append(f"Main DB: {str(e)}")
        
        # Test monitoring database
        try:
            conn = get_monitoring_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM system_metrics")
            metrics_count = cursor.fetchone()[0]
            conn.close()
            results["monitoring_db"] = True
            results["metrics_count"] = metrics_count
        except Exception as e:
            results["errors"].append(f"Monitoring DB: {str(e)}")
        
        # Re-initialize monitoring_db if needed
        global monitoring_db
        if monitoring_db is None:
            try:
                from ..database import MonitoringDatabase
                monitoring_db = MonitoringDatabase()
                set_monitoring_db(monitoring_db)
                results["reinitialized"] = True
            except Exception as e:
                results["errors"].append(f"Re-init failed: {str(e)}")
        
        success = results["ainews_db"] and results["monitoring_db"]
        
        return {
            "success": success,
            "status": "connected" if success else "partial",
            "details": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database initialization failed: {str(e)}")

@db_router.get("/status")
async def get_database_status():
    """Get current database connection status"""
    try:
        results = {
            "ainews_db": False,
            "monitoring_db": False,
            "status": "unknown"
        }
        
        # Test main database
        try:
            conn = get_ainews_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles")
            article_count = cursor.fetchone()[0]
            conn.close()
            results["ainews_db"] = True
            results["article_count"] = article_count
        except Exception:
            pass
        
        # Test monitoring database  
        try:
            conn = get_monitoring_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM system_metrics")
            metrics_count = cursor.fetchone()[0]
            conn.close()
            results["monitoring_db"] = True
            results["metrics_count"] = metrics_count
        except Exception:
            pass
        
        # Determine overall status
        if results["ainews_db"] and results["monitoring_db"]:
            results["status"] = "connected"
        elif results["ainews_db"] or results["monitoring_db"]:
            results["status"] = "partial"
        else:
            results["status"] = "disconnected"
        
        return results
        
    except Exception as e:
        return {
            "status": "error",
            "ainews_db": False,
            "monitoring_db": False,
            "error": str(e)
        }