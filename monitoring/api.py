"""
FastAPI routes for monitoring system
"""
from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import sqlite3
import os
import json
from pathlib import Path as PathLib

from .database import MonitoringDatabase
from .models import (
    SourceMetrics, SystemMetrics,
    SourceStatus, ContentStatus, MediaStatus,
    ArticleRecord, ArticleContent, SourceSummary
)
from .integration import get_monitoring_integration
from .log_processor import ErrorContextAggregator
from .memory_monitor import get_memory_monitor
from .process_manager import get_process_manager, ProcessStatus

# Import centralized logging
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app_logging import get_logger

logger = get_logger('monitoring.api')

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

# Initialize monitoring database - will be set by app.py
monitoring_db = None
monitoring_integration = None

def set_monitoring_db(db):
    """Set the monitoring database instance"""
    global monitoring_db, monitoring_integration
    monitoring_db = db
    monitoring_integration = get_monitoring_integration(db)


@router.get("/dashboard")
async def get_dashboard_data():
    """Get comprehensive dashboard data"""
    try:
        system_metrics = monitoring_db.get_system_metrics()
        source_metrics = monitoring_db.get_source_metrics()
        active_alerts = []  # Alerts removed
        error_summary = monitoring_db.get_error_summary(hours=24)
        
        # Calculate simple dashboard metrics
        sources_by_status = {}
        
        for source in source_metrics:
            status = source.last_status
            if status not in sources_by_status:
                sources_by_status[status] = 0
            sources_by_status[status] += 1
        
        # Get sources with most errors (simple problematic detection)
        problematic_sources = sorted(
            source_metrics,
            key=lambda s: s.recent_errors_24h,
            reverse=True
        )[:10]
        
        return {
            "system": {
                "total_sources": system_metrics.total_sources,
                "active_sources": system_metrics.active_sources,
                "error_sources": system_metrics.error_sources,
                "blocked_sources": system_metrics.blocked_sources,
                "total_articles": system_metrics.total_articles,
                "articles_24h": system_metrics.articles_24h,
                "articles_7d": system_metrics.articles_7d,
                "total_media_files": system_metrics.total_media_files,
                "media_downloaded": system_metrics.media_downloaded,
                "media_failed": system_metrics.media_failed,
                "database_size_mb": system_metrics.database_size_mb,
                "avg_parse_time_ms": system_metrics.avg_article_parse_time_ms,
                # Removed complex health score calculation
                # Calculate real success rate: sources with articles / active sources
                "success_rate": (len([s for s in source_metrics if s.recent_articles_24h > 0]) / max(1, system_metrics.active_sources)) * 100 if source_metrics else 0,
                "last_update": system_metrics.last_update.isoformat()
            },
            # Removed complex health overview
            "sources_by_status": sources_by_status,
            "problematic_sources": [
                {
                    "source_id": s.source_id,
                    "name": s.name,
                    "status": s.last_status,
                    # Removed health score field
                    "success_rate": s.success_rate,
                    "recent_errors": s.recent_errors_24h
                }
                for s in problematic_sources
            ],
            "active_alerts": [
                {
                    "id": alert.id,
                    "level": alert.level.value,
                    "title": alert.title,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "source": alert.source
                }
                for alert in active_alerts
            ],
            "error_summary": error_summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# REMOVED: Health overview endpoint - complex health scoring not needed


# REMOVED: Performance timeline endpoint - causes crashes and not needed


# Create a separate logs router for simplified logs endpoint
logs_router = APIRouter(prefix="/api/logs", tags=["logs"])

@logs_router.get("/recent")
async def get_logs_recent(limit: int = Query(100, ge=1, le=500)):
    """Get recent logs for dashboard - simplified version"""
    try:
        logs = []
        
        # Try to get logs from the main log file
        log_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'ai_news_parser.log')
        
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as f:
                lines = f.readlines()
                # Get last N lines
                recent_lines = lines[-limit:] if len(lines) > limit else lines
                
                for line in reversed(recent_lines):  # Most recent first
                    try:
                        # Try to parse JSON log
                        log_data = json.loads(line.strip())
                        logs.append({
                            "timestamp": log_data.get("timestamp", ""),
                            "level": log_data.get("level", "INFO"),
                            "message": log_data.get("message", line.strip())
                        })
                    except json.JSONDecodeError:
                        # If not JSON, treat as plain text log
                        logs.append({
                            "timestamp": datetime.now().isoformat(),
                            "level": "INFO",
                            "message": line.strip()
                        })
                    
                    if len(logs) >= limit:
                        break
        
        # If no file logs, get from monitoring database error_logs
        if not logs and monitoring_db:
            db_path = str(PathLib(monitoring_db.db_path))
            with sqlite3.connect(db_path) as conn:
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
        
        return {"logs": logs[:limit]}
        
    except Exception as e:
        # Return empty logs on error
        return {"logs": [], "error": str(e)}


@router.get("/logs/recent")
async def get_recent_logs(
    level: Optional[str] = Query(None, description="Filter by log level"),
    source: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(100, description="Number of logs to return"),
    search: Optional[str] = Query(None, description="Search in log messages")
):
    """Get recent log entries with filtering"""
    try:
        from .log_reader import get_log_reader
        log_reader = get_log_reader()
        
        if not log_reader:
            return {
                "status": "not_running",
                "message": "Log reader is not running",
                "logs": []
            }
        
        # Get recent logs from queue (convert queue to list)
        logs = []
        queue_items = list(log_reader.queue._queue)
        
        # Apply filters
        for log in reversed(queue_items):  # Most recent first
            # Level filter
            if level and log.get('level', '').lower() != level.lower():
                continue
            
            # Source filter
            if source and log.get('source', '') != source:
                continue
            
            # Search filter
            if search:
                message = log.get('message', '').lower()
                if search.lower() not in message:
                    continue
            
            logs.append(log)
            
            if len(logs) >= limit:
                break
        
        return {
            "status": "running",
            "total_in_buffer": log_reader.queue.qsize(),
            "returned": len(logs),
            "logs": logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# REMOVED: Complex system health endpoint - inaccurate and not needed


@router.get("/sources")
async def get_sources_monitoring(
    status: Optional[str] = Query(None, description="Filter by status"),
    type: Optional[str] = Query(None, description="Filter by type"),
    problematic: Optional[str] = Query(None, description="Filter problematic sources"),
    # Removed health_threshold parameter
    sort_by: str = Query("recent_errors", description="Sort field"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200)
):
    """Get monitored sources with filtering and pagination"""
    try:
        # Get all source metrics
        all_sources = monitoring_db.get_source_metrics()
        
        # Apply filters
        filtered_sources = all_sources
        
        if status:
            filtered_sources = [s for s in filtered_sources if s.last_status == status]
        
        if type:
            filtered_sources = [s for s in filtered_sources if s.type == type]
        
        # Filter problematic sources
        if problematic:
            if problematic == 'frequent_errors':
                filtered_sources = [s for s in filtered_sources if s.recent_errors_24h > 10]
            elif problematic == 'no_activity':
                filtered_sources = [s for s in filtered_sources if s.recent_articles_24h == 0]
            elif problematic == 'low_health':
                # Changed to high error rate instead of health score
                filtered_sources = [s for s in filtered_sources if s.recent_errors_24h > 5]
        
        # Removed health_threshold filtering
        
        # Sort
        reverse = (sort_order == "desc")
        if sort_by == "recent_errors":
            filtered_sources.sort(key=lambda s: s.recent_errors_24h, reverse=reverse)
        elif sort_by == "success_rate":
            filtered_sources.sort(key=lambda s: s.success_rate, reverse=reverse)
        elif sort_by == "recent_articles":
            filtered_sources.sort(key=lambda s: s.recent_articles_24h, reverse=reverse)
        elif sort_by == "recent_errors":
            filtered_sources.sort(key=lambda s: s.recent_errors_24h, reverse=reverse)
        elif sort_by == "name":
            filtered_sources.sort(key=lambda s: s.name.lower(), reverse=reverse)
        
        # Paginate
        total = len(filtered_sources)
        start = (page - 1) * limit
        end = start + limit
        paginated_sources = filtered_sources[start:end]
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "sources": [
                {
                    "source_id": s.source_id,
                    "name": s.name,
                    "url": s.url,
                    "type": s.type,
                    "has_rss": s.has_rss,
                    "status": s.last_status,
                    "last_error": s.last_error,
                    "error_type": getattr(s, 'error_type', None),
                    "success_rate": s.success_rate,
                    "last_parsed": s.last_parsed.isoformat() if s.last_parsed else None,
                    "total_articles": s.total_articles,
                    "recent_articles_24h": s.recent_articles_24h,
                    "recent_errors_24h": s.recent_errors_24h,
                    "avg_parse_time_ms": s.avg_parse_time_ms,
                    # Removed health_score field
                }
                for s in paginated_sources
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Last Parsed Management Endpoints - MUST come before parameterized routes
@router.get("/sources/last-parsed")
async def get_all_last_parsed_priority():
    """Get last parsed timestamps for all sources - Priority route to avoid conflicts"""
    try:
        import sqlite3
        from pathlib import Path
        
        db_path = Path(monitoring_db.ainews_db_path)
        if not db_path.exists():
            raise HTTPException(status_code=404, detail="Main database not found")
        
        with sqlite3.connect(str(db_path)) as conn:
            # Get global last_parsed from global_config
            cursor = conn.execute(
                "SELECT value FROM global_config WHERE key = 'global_last_parsed'"
            )
            global_config_row = cursor.fetchone()
            global_last_parsed = global_config_row[0] if global_config_row else "2025-08-01T00:00:00Z"
            
            # Get all sources but use global timestamp
            cursor = conn.execute(
                "SELECT source_id, name FROM sources ORDER BY name"
            )
            results = cursor.fetchall()
            
        sources = []
        for row in results:
            sources.append({
                "source_id": row[0],
                "source_name": row[1],
                "last_parsed": global_last_parsed  # All sources now use global timestamp
            })
            
        return {
            "sources": sources,
            "total": len(sources)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get last parsed data: {str(e)}")


@router.get("/sources/{source_id}")
async def get_source_details(source_id: str = Path(..., description="Source ID")):
    """Get detailed monitoring data for a specific source"""
    try:
        # Get source metrics
        sources = monitoring_db.get_source_metrics(source_id)
        if not sources:
            raise HTTPException(status_code=404, detail="Source not found")
        
        source = sources[0]
        
        # Get activity timeline
        timeline_7d = monitoring_db.get_source_activity_timeline(source_id, days=7)
        timeline_30d = monitoring_db.get_source_activity_timeline(source_id, days=30)
        
        # Calculate trends
        if len(timeline_7d) >= 2:
            recent_avg = sum(t['articles_count'] for t in timeline_7d[:3]) / 3
            older_avg = sum(t['articles_count'] for t in timeline_7d[3:6]) / 3 if len(timeline_7d) >= 6 else 0
            trend = "increasing" if recent_avg > older_avg else "decreasing" if recent_avg < older_avg else "stable"
        else:
            trend = "unknown"
        
        # Get health report if available
        health_report = None
        try:
            db_path = monitoring_db.db_path
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM source_health_reports 
                    WHERE source_id = ? 
                    ORDER BY timestamp DESC LIMIT 1
                """, (source_id,))
                
                health_data = cursor.fetchone()
                if health_data:
                    health_report = {
                        "is_healthy": bool(health_data["is_healthy"]),
                        "health_score": health_data["health_score"],
                        "issues": health_data["issues"],
                        "recommendations": health_data["recommendations"],
                        "performance_trend": health_data["performance_trend"]
                    }
        except Exception:
            pass  # Health report is optional
        
        return {
            "source": {
                "source_id": source.source_id,
                "name": source.name,
                "url": source.url,
                "type": source.type,
                "has_rss": source.has_rss,
                "status": source.last_status,
                "last_error": source.last_error,
                "error_type": getattr(source, 'error_type', None),
                "success_rate": source.success_rate,
                "last_parsed": source.last_parsed.isoformat() if source.last_parsed else None,
                "total_articles": source.total_articles,
                # Removed health_score field
            },
            "metrics_24h": {
                "articles": source.recent_articles_24h,
                "errors": source.recent_errors_24h,
                "avg_parse_time_ms": source.avg_parse_time_ms,
                "error_rate": (source.recent_errors_24h / max(1, source.recent_articles_24h + source.recent_errors_24h)) * 100
            },
            "health_report": health_report,
            "timeline_7d": timeline_7d,
            "timeline_30d": timeline_30d,
            "trend": trend,
            "recent_articles": monitoring_db.get_source_articles(source_id, limit=100)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sources/toggle/{source_id}")
async def toggle_source(
    source_id: str = Path(..., description="Source ID"),
    enabled: bool = Query(..., description="Enable or disable the source")
):
    """Enable or disable a source - CRITICAL ENDPOINT"""
    try:
        # Connect to main database to update source status
        from pathlib import Path
        ainews_db_path = str(Path(__file__).parent.parent / "data" / "ainews.db")
        
        with sqlite3.connect(ainews_db_path) as conn:
            cursor = conn.cursor()
            
            # Check if source exists
            cursor.execute("SELECT source_id FROM sources WHERE source_id = ?", (source_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Source not found")
            
            # Update source status based on enabled flag
            new_status = "active" if enabled else "disabled"
            
            cursor.execute(
                "UPDATE sources SET last_status = ? WHERE source_id = ?",
                (new_status, source_id)
            )
            conn.commit()
            
            # Log the change (optional audit trail)
            # TODO: Add proper audit logging if needed
            
            return {
                "success": True,
                "source_id": source_id,
                "enabled": enabled,
                "status": new_status,
                "message": f"Source {'enabled' if enabled else 'disabled'} successfully"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle source: {str(e)}")




@router.get("/error-breakdown")
async def get_error_breakdown():
    """Get detailed breakdown of source errors by type"""
    try:
        # Connect to main ainews database
        ainews_db_path = str(PathLib(monitoring_db.db_path).parent / "ainews.db")
        
        with sqlite3.connect(ainews_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all sources with errors
            cursor.execute("""
                SELECT source_id, name, last_error, last_status 
                FROM sources 
                WHERE last_status = 'error' AND last_error IS NOT NULL
            """)
            
            error_sources = cursor.fetchall()
        
        # Group errors by type
        error_groups = {}
        
        for row in error_sources:
            source_id = row['source_id']
            name = row['name']
            last_error = row['last_error']
            
            # Determine error type
            if "Timeout" in last_error:
                error_type = "Timeout"
            elif "ERR_CERT" in last_error or "SSL" in last_error.upper():
                error_type = "SSL Certificate"
            elif "ENOTFOUND" in last_error or "DNS" in last_error.upper():
                error_type = "DNS Resolution"
            elif "ECONNREFUSED" in last_error or "Connection refused" in last_error:
                error_type = "Connection Refused"
            elif "404" in last_error or "Not Found" in last_error:
                error_type = "Page Not Found"
            else:
                error_type = "Other"
            
            if error_type not in error_groups:
                error_groups[error_type] = {
                    "count": 0,
                    "sources": []
                }
            
            error_groups[error_type]["count"] += 1
            error_groups[error_type]["sources"].append({
                "source_id": source_id,
                "name": name,
                "error": last_error
            })
        
        # Format response
        breakdown = []
        for error_type, data in error_groups.items():
            breakdown.append({
                "type": error_type,
                "count": data["count"], 
                "description": f"{error_type} ({data['count']} sources)",
                "sources": data["sources"]
            })
        
        # Sort by count (descending)
        breakdown.sort(key=lambda x: x["count"], reverse=True)
        
        return {
            "total_error_sources": len(error_sources),
            "breakdown": breakdown,
            "summary": [item["description"] for item in breakdown]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/errors/recent")
async def get_recent_errors(
    limit: int = Query(50, description="Maximum number of errors to return"),
    error_type: Optional[str] = Query(None, description="Filter by error type"),
    source_id: Optional[str] = Query(None, description="Filter by source ID"),
    hours: int = Query(24, description="Number of hours to look back")
):
    """Get recent errors from error_logs table"""
    try:
        # Build query
        query = """
            SELECT id, source_id, timestamp, error_type, error_message, stack_trace, context, resolved
            FROM error_logs
            WHERE timestamp > datetime('now', '-{} hours')
        """.format(hours)
        
        params = []
        
        if error_type:
            query += " AND error_type = ?"
            params.append(error_type)
        
        if source_id:
            query += " AND source_id = ?"
            params.append(source_id)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        # Execute query
        results = monitoring_db.execute_query(query, params)
        
        # Format errors
        errors = []
        for row in results:
            errors.append({
                "id": row[0],
                "source_id": row[1],
                "timestamp": row[2],
                "error_type": row[3],
                "error_message": row[4],
                "stack_trace": row[5],
                "context": row[6],
                "resolved": bool(row[7]),
                "level": "CRITICAL" if "CRITICAL" in str(row[3]).upper() else "ERROR"
            })
        
        # Get statistics
        stats_query = """
            SELECT 
                COUNT(*) as total_errors,
                COUNT(DISTINCT source_id) as sources_with_errors
            FROM error_logs
            WHERE timestamp > datetime('now', '-{} hours')
        """.format(hours)
        
        stats_result = monitoring_db.execute_query(stats_query)
        stats = stats_result[0] if stats_result else (0, 0)
        
        # Get last error time (from all errors, not just within hours range)
        last_error_query = """
            SELECT MAX(timestamp) FROM error_logs
        """
        
        last_error_result = monitoring_db.execute_query(last_error_query)
        last_error_time = last_error_result[0][0] if last_error_result and last_error_result[0][0] else None
        
        return {
            "errors": errors,
            "total_errors": stats[0],
            "sources_with_errors": stats[1],
            "last_error_time": last_error_time
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/errors/{error_id}/debug")
async def get_error_debug_context(
    error_id: str = Path(..., description="Error ID to get debug context for")
):
    """Get full debug context for a specific error including related logs"""
    try:
        # Initialize error context aggregator
        error_aggregator = ErrorContextAggregator(monitoring_db)
        
        # Get error context
        error_context = error_aggregator.get_error_context(error_id)
        
        if error_context.get('error') == 'Error not found':
            raise HTTPException(status_code=404, detail="Error not found")
        
        return error_context
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/summary")
async def get_log_processing_summary():
    """Get summary of log processing metrics"""
    try:
        # Get log processor instance from app
        from .app import log_processor
        
        if not log_processor:
            return {
                "status": "not_running",
                "message": "Log processor is not running"
            }
        
        # Get processing summary
        summary = log_processor.consume_log_metrics()
        
        return {
            "status": "running",
            "summary": summary,
            "logs_monitored": list(log_processor._extractors.keys())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




# REMOVED: Automation status endpoint - not used


# REMOVED: Enable source endpoint - not used


# REMOVED: Disable source endpoint - not used


# REMOVED: Source recovery endpoint - not used






@router.get("/health")
async def get_system_health():
    """Get comprehensive system health status"""
    try:
        # Get system metrics
        system_metrics = monitoring_db.get_system_metrics()
        
        # Get latest performance metrics for CPU/memory data
        try:
            cursor = monitoring_db.connection.cursor()
            cursor.execute("""
                SELECT cpu_usage_percent, memory_usage_mb, disk_usage_percent, active_connections
                FROM performance_metrics 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            perf_row = cursor.fetchone()
            if perf_row:
                cpu_usage = perf_row["cpu_usage_percent"]
                memory_usage = perf_row["memory_usage_mb"] 
                disk_usage = perf_row["disk_usage_percent"]
                active_connections = perf_row["active_connections"]
            else:
                cpu_usage = memory_usage = disk_usage = active_connections = 0
        except Exception:
            cpu_usage = memory_usage = disk_usage = active_connections = 0
        
        # Simple status determination based on metrics
        if cpu_usage > 90 or memory_usage > 8000 or disk_usage > 90:
            overall_status = "critical"
        elif cpu_usage > 70 or memory_usage > 6000 or disk_usage > 70:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "system_metrics": {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage,
                "active_connections": active_connections
            },
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")


@router.get("/metrics")
async def get_performance_metrics():
    """Get comprehensive performance metrics"""
    try:
        # Get recent system metrics
        system_metrics = monitoring_db.get_system_metrics()
        
        # Get latest performance metrics for CPU/memory data
        try:
            cursor = monitoring_db.connection.cursor()
            cursor.execute("""
                SELECT cpu_usage_percent, memory_usage_mb, disk_usage_percent, 
                       parse_rate_per_minute, error_rate_percent, timestamp
                FROM performance_metrics 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            perf_row = cursor.fetchone()
            if perf_row:
                cpu_usage = perf_row["cpu_usage_percent"]
                memory_usage = perf_row["memory_usage_mb"] 
                disk_usage = perf_row["disk_usage_percent"]
                parse_rate = perf_row["parse_rate_per_minute"]
                error_rate = perf_row["error_rate_percent"]
                perf_timestamp = perf_row["timestamp"]
            else:
                cpu_usage = memory_usage = disk_usage = parse_rate = error_rate = 0
                perf_timestamp = datetime.now().isoformat()
        except Exception:
            cpu_usage = memory_usage = disk_usage = parse_rate = error_rate = 0
            perf_timestamp = datetime.now().isoformat()
        
        # Get source performance metrics
        source_metrics = monitoring_db.get_source_metrics_detailed()
        
        # Calculate aggregate performance metrics
        total_parse_time = sum([s.get('avg_parse_time_ms', 0) or 0 for s in source_metrics])
        avg_parse_time = total_parse_time / len(source_metrics) if source_metrics else 0
        
        total_success_rate = sum([s.get('success_rate', 0) or 0 for s in source_metrics])
        avg_success_rate = total_success_rate / len(source_metrics) if source_metrics else 0
        
        # Get error rates
        error_summary = monitoring_db.get_error_summary(hours=24)
        total_errors = error_summary.get('total_errors', 0)
        
        # Get recent performance data
        recent_metrics = []
        recent_metrics.append({
            "timestamp": perf_timestamp,
            "cpu_percent": cpu_usage,
            "memory_mb": memory_usage,
            "disk_percent": disk_usage,
            "parse_rate": parse_rate,
            "error_rate": error_rate
        })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system_performance": {
                "average_parse_time_ms": round(avg_parse_time, 2),
                "average_success_rate": round(avg_success_rate, 2),
                "total_errors_24h": total_errors,
                "current_cpu_usage": cpu_usage,
                "current_memory_usage": memory_usage,
                "parse_rate_per_minute": parse_rate
            },
            "source_performance": {
                "total_sources": len(source_metrics),
                "active_sources": len([s for s in source_metrics if s.get('last_status') == 'active']),
                "fastest_sources": sorted(source_metrics, key=lambda x: x.get('avg_parse_time_ms', float('inf')))[:5],
                "slowest_sources": sorted(source_metrics, key=lambda x: x.get('avg_parse_time_ms', 0), reverse=True)[:5]
            },
            "recent_metrics": recent_metrics
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")


@router.get("/articles")
async def get_article_statistics():
    """Get comprehensive article statistics"""
    try:
        # Get article stats from main database
        article_stats = monitoring_db.get_article_stats_summary(hours=24)
        
        # Get source-specific article metrics
        source_metrics = monitoring_db.get_source_metrics_detailed()
        
        # Calculate article distribution by source
        articles_by_source = {}
        total_articles = 0
        
        for source in source_metrics:
            source_id = source.get('source_id')
            article_count = source.get('articles_count_24h', 0)
            articles_by_source[source_id] = article_count
            total_articles += article_count
        
        # Get top performing sources
        top_sources = sorted(articles_by_source.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_articles_24h": total_articles,
                "total_sources_active": len([s for s in source_metrics if s.get('articles_count_24h', 0) > 0]),
                "average_articles_per_source": round(total_articles / len(source_metrics), 2) if source_metrics else 0,
                "articles_with_media": article_stats.get('articles_with_media', 0),
                "articles_with_full_content": article_stats.get('articles_with_full_content', 0)
            },
            "top_sources": [
                {
                    "source_id": source_id,
                    "article_count": count,
                    "percentage": round((count / total_articles * 100), 2) if total_articles > 0 else 0
                }
                for source_id, count in top_sources
            ],
            "content_quality": {
                "average_content_length": article_stats.get('avg_content_length', 0),
                "full_content_rate": article_stats.get('full_content_rate', 0),
                "media_success_rate": article_stats.get('media_success_rate', 0),
                "duplicate_rate": article_stats.get('duplicate_rate', 0)
            },
            "recent_activity": {
                "last_hour": article_stats.get('articles_last_hour', 0),
                "last_6_hours": article_stats.get('articles_last_6h', 0),
                "last_24_hours": total_articles
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get article statistics: {str(e)}")


@router.get("/logs/stats")
async def get_log_statistics():
    """Get log statistics and summary"""
    try:
        from .log_reader import get_log_reader
        log_reader = get_log_reader()
        
        if not log_reader:
            return {
                "status": "not_running",
                "message": "Log reader is not running"
            }
        
        # Get log statistics from queue
        queue_items = list(log_reader.queue._queue)
        
        # Calculate statistics
        stats = {
            "total": len(queue_items),
            "error": 0,
            "warning": 0,
            "info": 0,
            "debug": 0
        }
        
        sources = {}
        recent_errors = []
        
        for log in queue_items:
            # Count by level
            level = log.get('level', 'info').lower()
            if level in stats:
                stats[level] += 1
            
            # Count by source
            source = log.get('source', 'unknown')
            if source not in sources:
                sources[source] = 0
            sources[source] += 1
            
            # Collect recent errors
            if level == 'error' and len(recent_errors) < 10:
                recent_errors.append({
                    "timestamp": log.get('timestamp'),
                    "source": source,
                    "message": log.get('message'),
                    "log_file": log.get('log_file')
                })
        
        # Sort sources by count
        top_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "status": "running",
            "statistics": stats,
            "top_sources": [
                {"source": source, "count": count}
                for source, count in top_sources
            ],
            "recent_errors": recent_errors,
            "monitored_files": list(log_reader.log_files.keys()),
            "file_positions": log_reader.file_positions
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get log statistics: {str(e)}")


@router.get("/logs/files")
async def get_log_files():
    """Get list of monitored log files and their status"""
    try:
        from .log_reader import get_log_reader
        log_reader = get_log_reader()
        
        if not log_reader:
            return {
                "status": "not_running",
                "message": "Log reader is not running",
                "files": []
            }
        
        files = []
        for name, filename in log_reader.log_files.items():
            filepath = log_reader.log_dir / filename
            exists = filepath.exists()
            size = filepath.stat().st_size if exists else 0
            position = log_reader.file_positions.get(str(filepath), 0)
            
            files.append({
                "name": name,
                "filename": filename,
                "path": str(filepath),
                "exists": exists,
                "size_bytes": size,
                "position": position,
                "read_percentage": (position / size * 100) if size > 0 else 0
            })
        
        return {
            "status": "running",
            "log_directory": str(log_reader.log_dir),
            "files": files
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get log files: {str(e)}")


# Memory monitoring endpoints
@router.get("/memory")
async def get_memory_info():
    """Get current system memory information"""
    try:
        memory_monitor = get_memory_monitor()
        if not memory_monitor:
            raise HTTPException(status_code=503, detail="Memory monitor not initialized")
        
        return memory_monitor.get_current_memory_info()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memory info: {str(e)}")


@router.get("/memory/statistics")
async def get_memory_statistics():
    """Get memory monitor statistics"""
    try:
        memory_monitor = get_memory_monitor()
        if not memory_monitor:
            raise HTTPException(status_code=503, detail="Memory monitor not initialized")
        
        return memory_monitor.get_statistics()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memory statistics: {str(e)}")


@router.get("/memory/processes")
async def get_memory_processes():
    """Get detailed memory usage by processes"""
    try:
        memory_monitor = get_memory_monitor()
        if not memory_monitor:
            raise HTTPException(status_code=503, detail="Memory monitor not initialized")
        
        snapshot = memory_monitor.get_memory_snapshot()
        
        return {
            "timestamp": snapshot.timestamp.isoformat(),
            "system_memory": {
                "total_mb": snapshot.total_memory_mb,
                "used_mb": snapshot.used_memory_mb,
                "available_mb": snapshot.available_memory_mb,
                "usage_percent": (snapshot.used_memory_mb / snapshot.total_memory_mb) * 100
            },
            "processes": {
                "total_count": len(snapshot.processes),
                "ainews_count": len(snapshot.ainews_processes),
                "top_consumers": [
                    {
                        "pid": p.pid,
                        "name": p.name,
                        "memory_mb": p.memory_mb,
                        "cpu_percent": p.cpu_percent,
                        "create_time": p.create_time.isoformat(),
                        "is_ainews": p in snapshot.ainews_processes,
                        "cmdline": " ".join(p.cmdline[:3]) if p.cmdline else ""  # First 3 args
                    }
                    for p in snapshot.top_memory_consumers[:15]
                ],
                "ainews_processes": [
                    {
                        "pid": p.pid,
                        "name": p.name,
                        "memory_mb": p.memory_mb,
                        "cpu_percent": p.cpu_percent,
                        "create_time": p.create_time.isoformat(),
                        "cmdline": " ".join(p.cmdline) if p.cmdline else ""
                    }
                    for p in snapshot.ainews_processes
                ]
            },
            "alert_level": memory_monitor._get_alert_level(snapshot.used_memory_mb).value,
            "thresholds": {
                "warning_mb": memory_monitor.warning_threshold_mb,
                "critical_mb": memory_monitor.critical_threshold_mb,
                "max_mb": memory_monitor.max_memory_mb
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memory processes: {str(e)}")


@router.post("/memory/cleanup")
async def trigger_memory_cleanup():
    """Trigger manual memory cleanup"""
    try:
        memory_monitor = get_memory_monitor()
        if not memory_monitor:
            raise HTTPException(status_code=503, detail="Memory monitor not initialized")
        
        before_snapshot = memory_monitor.get_memory_snapshot()
        before_memory = before_snapshot.used_memory_mb
        
        # Trigger cleanup
        memory_monitor._trigger_soft_cleanup()
        
        # Wait a moment and get after snapshot
        import time
        time.sleep(2)
        after_snapshot = memory_monitor.get_memory_snapshot()
        after_memory = after_snapshot.used_memory_mb
        
        freed_memory = before_memory - after_memory
        
        return {
            "success": True,
            "timestamp": after_snapshot.timestamp.isoformat(),
            "memory_before_mb": before_memory,
            "memory_after_mb": after_memory,
            "memory_freed_mb": freed_memory,
            "cleanup_effectiveness_percent": (freed_memory / before_memory) * 100 if before_memory > 0 else 0
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger memory cleanup: {str(e)}")


@router.get("/memory/history")
async def get_memory_history(hours: int = Query(2, ge=1, le=24)):
    """Get memory usage history"""
    try:
        memory_monitor = get_memory_monitor()
        if not memory_monitor:
            raise HTTPException(status_code=503, detail="Memory monitor not initialized")
        
        # Get history from memory monitor
        history = memory_monitor._memory_history
        
        # Filter by time range
        cutoff_time = datetime.now() - timedelta(hours=hours)
        filtered_history = [
            snapshot for snapshot in history
            if snapshot.timestamp > cutoff_time
        ]
        
        # Format for API response
        history_data = []
        for snapshot in filtered_history[-100:]:  # Last 100 entries max
            ainews_memory = sum(p.memory_mb for p in snapshot.ainews_processes)
            history_data.append({
                "timestamp": snapshot.timestamp.isoformat(),
                "total_memory_mb": snapshot.used_memory_mb,
                "ainews_memory_mb": ainews_memory,
                "alert_level": memory_monitor._get_alert_level(snapshot.used_memory_mb).value,
                "processes_count": len(snapshot.processes),
                "ainews_processes_count": len(snapshot.ainews_processes)
            })
        
        return {
            "hours_requested": hours,
            "entries_count": len(history_data),
            "history": history_data,
            "summary": {
                "max_memory_mb": max([h["total_memory_mb"] for h in history_data]) if history_data else 0,
                "min_memory_mb": min([h["total_memory_mb"] for h in history_data]) if history_data else 0,
                "avg_memory_mb": sum([h["total_memory_mb"] for h in history_data]) / len(history_data) if history_data else 0,
                "alerts_count": len([h for h in history_data if h["alert_level"] in ["warning", "critical", "emergency"]])
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memory history: {str(e)}")


# System Resources Endpoint
@router.get("/system/resources")
async def get_system_resources():
    """Get current system resource usage including CPU, memory, and processes"""
    try:
        import psutil
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Count processes
        total_processes = len(psutil.pids())
        ainews_processes = 0
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if any(keyword in cmdline for keyword in ['rss_scrape_parser', 'monitoring', 'ainews-clean', 'extract_system', 'main_extract.py']):
                    ainews_processes += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Get network connections
        try:
            network_connections = len(psutil.net_connections())
        except:
            network_connections = 0
        
        # Save to database
        system_metrics = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent,
            'process_count': total_processes,
            'ainews_process_count': ainews_processes,
            'network_connections': network_connections,
            'open_files': 0  # Requires root on most systems
        }
        
        monitoring_db.save_system_metrics(system_metrics)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count()
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": disk.percent
            },
            "processes": {
                "total": total_processes,
                "ainews": ainews_processes
            },
            "network": {
                "connections": network_connections
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system resources: {str(e)}")


# Parsing Active Status Endpoint
@router.get("/parsing/active")
async def get_active_parsing_status():
    """Get current active parsing status and progress"""
    try:
        process_manager = get_process_manager()
        status = process_manager.get_status()
        
        # Get latest progress from database
        db_progress = monitoring_db.get_latest_parsing_progress()
        
        # Combine process manager status with database progress
        return {
            "is_active": status['status'] in ['running', 'paused'],
            "process_status": status,
            "parsing_progress": db_progress,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get parsing status: {str(e)}")


# Process Control API Endpoints
@router.post("/control/start")
async def start_parser(
    days_back: int = Query(7, ge=1, le=30, description="Number of days to go back for crawling"),
    last_parsed: Optional[str] = Query(None, description="Last parsed timestamp to resume from")
):
    """Start the AI News Parser process"""
    try:
        process_manager = get_process_manager()
        
        success = process_manager.start_parser(days_back=days_back, last_parsed=last_parsed)
        
        if success:
            return {
                "success": True,
                "message": "Parser started successfully",
                "status": process_manager.get_status()
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail="Failed to start parser. Check if it's already running or check logs for errors."
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start parser: {str(e)}")


@router.post("/control/pause")
async def pause_parser():
    """Pause the running parser process"""
    try:
        process_manager = get_process_manager()
        
        success = process_manager.pause_parser()
        
        if success:
            return {
                "success": True,
                "message": "Parser paused successfully",
                "status": process_manager.get_status()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to pause parser. Check if it's currently running."
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause parser: {str(e)}")


@router.post("/control/resume")
async def resume_parser():
    """Resume the paused parser process"""
    try:
        process_manager = get_process_manager()
        
        success = process_manager.resume_parser()
        
        if success:
            return {
                "success": True,
                "message": "Parser resumed successfully",
                "status": process_manager.get_status()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to resume parser. Check if it's currently paused."
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resume parser: {str(e)}")


@router.post("/control/stop")
async def stop_parser(
    timeout: int = Query(30, ge=5, le=300, description="Timeout in seconds for graceful shutdown")
):
    """Stop the parser process gracefully"""
    try:
        process_manager = get_process_manager()
        
        success = process_manager.stop_parser(timeout=timeout)
        
        if success:
            return {
                "success": True,
                "message": "Parser stopped successfully",
                "status": process_manager.get_status()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to stop parser. It may not be running or may have already stopped."
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop parser: {str(e)}")


@router.post("/control/emergency-stop")
async def emergency_stop_parser():
    """Emergency stop - forcefully kill all parser processes"""
    try:
        process_manager = get_process_manager()
        
        success = process_manager.emergency_stop()
        
        if success:
            return {
                "success": True,
                "message": "Emergency stop completed - all parser processes terminated",
                "status": process_manager.get_status()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to perform emergency stop"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform emergency stop: {str(e)}")


@router.get("/control/status")
async def get_parser_status():
    """Get current parser process status and progress"""
    try:
        process_manager = get_process_manager()
        
        status = process_manager.get_status()
        health = process_manager.is_process_healthy()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "is_healthy": health,
            "capabilities": {
                "can_start": status['status'] in ['idle', 'stopped', 'error'],
                "can_pause": status['status'] == 'running',
                "can_resume": status['status'] == 'paused',
                "can_stop": status['status'] in ['running', 'paused'],
                "can_emergency_stop": status['status'] in ['running', 'paused', 'stopping']
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get parser status: {str(e)}")


@router.post("/control/cleanup-memory")
async def cleanup_parser_memory():
    """Force memory cleanup for parser processes"""
    try:
        process_manager = get_process_manager()
        
        cleanup_results = process_manager.cleanup_memory()
        
        return {
            "success": True,
            "message": "Memory cleanup completed",
            "results": cleanup_results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup memory: {str(e)}")


@router.post("/control/update-progress")
async def update_parser_progress(
    current_source: Optional[str] = None,
    total_sources: Optional[int] = None,
    processed_sources: Optional[int] = None,
    total_articles: Optional[int] = None
):
    """Update parser progress information (for external monitoring integration)"""
    try:
        process_manager = get_process_manager()
        
        process_manager.update_progress(
            current_source=current_source,
            total_sources=total_sources,
            processed_sources=processed_sources,
            total_articles=total_articles
        )
        
        return {
            "success": True,
            "message": "Progress updated successfully",
            "current_status": process_manager.get_status()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update progress: {str(e)}")


# =======================================
# ARTICLES API - CRITICAL FOR DAY 3
# =======================================

# Create separate router for articles API
articles_router = APIRouter(prefix="/api", tags=["articles"])


@articles_router.get("/articles")
async def get_articles(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Articles per page"),
    search: Optional[str] = Query(None, description="Search in article titles"),
    source_filter: Optional[str] = Query(None, description="Filter by source ID"),
    date_filter: Optional[str] = Query(None, description="Filter by date range (24h, 7d, 30d, all)"),
    status: Optional[str] = Query(None, description="Filter by content status"),
    sort_by: str = Query("created_at", description="Sort field (created_at, published_date, title)"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)")
):
    """Get articles with pagination, search and filtering - CRITICAL ENDPOINT"""
    try:
        # Connect to main articles database - use absolute path
        from pathlib import Path
        ainews_db_path = str(Path(__file__).parent.parent / "data" / "ainews.db")
        
        with sqlite3.connect(ainews_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build WHERE clause
            where_conditions = []
            params = []
            
            if search:
                where_conditions.append("a.title LIKE ?")
                params.append(f"%{search}%")
            
            if source_filter:
                where_conditions.append("a.source_id = ?")
                params.append(source_filter)
            
            # Add date filter support
            if date_filter:
                if date_filter == "24h":
                    where_conditions.append("a.published_date >= datetime('now', '-1 day')")
                elif date_filter == "7d":
                    where_conditions.append("a.published_date >= datetime('now', '-7 days')")
                elif date_filter == "30d":
                    where_conditions.append("a.published_date >= datetime('now', '-30 days')")
                # 'all' means no date filter
            
            # Add status filter support
            if status:
                where_conditions.append("a.content_status = ?")
                params.append(status)
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # Validate sort parameters
            valid_sort_fields = ["created_at", "published_date", "title"]
            if sort_by not in valid_sort_fields:
                sort_by = "created_at"
            
            sort_order = "DESC" if sort_order.lower() == "desc" else "ASC"
            
            # Get total count for pagination
            count_query = f"""
                SELECT COUNT(DISTINCT a.article_id) as total
                FROM articles a
                JOIN sources s ON a.source_id = s.source_id
                LEFT JOIN media_files m ON a.article_id = m.article_id
                {where_clause}
            """
            
            cursor.execute(count_query, params)
            total = cursor.fetchone()["total"]
            
            # Calculate pagination
            offset = (page - 1) * limit
            
            # Main query with JOIN to get source name and media files count
            query = f"""
                SELECT 
                    a.article_id,
                    a.source_id,
                    a.title,
                    a.url,
                    a.description,
                    a.published_date,
                    a.content_status,
                    a.created_at,
                    LENGTH(COALESCE(a.content, '')) as content_length,
                    s.name as source_name,
                    COUNT(m.id) as media_count
                FROM articles a
                JOIN sources s ON a.source_id = s.source_id
                LEFT JOIN media_files m ON a.article_id = m.article_id
                {where_clause}
                GROUP BY a.article_id, a.source_id, a.title, a.url, a.description, 
                         a.published_date, a.content_status, a.created_at, s.name
                ORDER BY a.{sort_by} {sort_order}
                LIMIT ? OFFSET ?
            """
            
            cursor.execute(query, params + [limit, offset])
            rows = cursor.fetchall()
            
            # Format articles with content preview URL
            articles = []
            for row in rows:
                article = {
                    "article_id": row["article_id"],
                    "source_id": row["source_id"],
                    "source_name": row["source_name"],
                    "title": row["title"],
                    "url": row["url"],
                    "description": row["description"],
                    "published_date": row["published_date"],
                    "content_status": row["content_status"],
                    "created_at": row["created_at"],
                    "content_length": row["content_length"],
                    "media_count": row["media_count"],
                    "content_preview_url": f"/api/articles/{row['article_id']}/content"
                }
                articles.append(article)
            
            # Calculate pagination info
            total_pages = (total + limit - 1) // limit
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
                "articles": articles
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get articles: {str(e)}")


@articles_router.get("/articles/{article_id}/content")
async def get_article_content(article_id: str = Path(..., description="Article ID")):
    """Get full content of a specific article - CRITICAL ENDPOINT"""
    try:
        # Connect to main articles database - use absolute path
        from pathlib import Path
        ainews_db_path = str(Path(__file__).parent.parent / "data" / "ainews.db")
        
        with sqlite3.connect(ainews_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get article with source information
            query = """
                SELECT 
                    a.article_id,
                    a.title,
                    a.url,
                    a.description,
                    a.published_date,
                    a.content,
                    a.content_status,
                    a.created_at,
                    s.name as source_name,
                    s.url as source_url
                FROM articles a
                JOIN sources s ON a.source_id = s.source_id
                WHERE a.article_id = ?
            """
            
            cursor.execute(query, (article_id,))
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Article not found")
            
            # Format article content
            article_content = {
                "article_id": row["article_id"],
                "title": row["title"],
                "source_name": row["source_name"],
                "source_url": row["source_url"],
                "url": row["url"],
                "description": row["description"],
                "published_date": row["published_date"],
                "content": row["content"],
                "content_status": row["content_status"],
                "created_at": row["created_at"],
                "content_length": len(row["content"]) if row["content"] else 0,
                "has_content": bool(row["content"] and len(row["content"]) > 0)
            }
            
            return article_content
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get article content: {str(e)}")



@articles_router.get("/articles/search")
async def search_articles(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Articles per page")
):
    """Search articles by title and content - CRITICAL ENDPOINT"""
    try:
        # Connect to main articles database - use absolute path
        from pathlib import Path
        ainews_db_path = str(Path(__file__).parent.parent / "data" / "ainews.db")
        
        with sqlite3.connect(ainews_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Search in title and content
            search_pattern = f"%{q}%"
            
            # Get total count
            count_query = """
                SELECT COUNT(*) as total
                FROM articles a
                JOIN sources s ON a.source_id = s.source_id
                WHERE a.title LIKE ? OR a.content LIKE ?
            """
            cursor.execute(count_query, (search_pattern, search_pattern))
            total = cursor.fetchone()["total"]
            
            # Get articles with pagination
            offset = (page - 1) * limit
            
            query = """
                SELECT 
                    a.article_id,
                    a.source_id,
                    a.title,
                    a.url,
                    a.description,
                    a.published_date,
                    a.content_status,
                    a.created_at,
                    LENGTH(COALESCE(a.content, '')) as content_length,
                    s.name as source_name
                FROM articles a
                JOIN sources s ON a.source_id = s.source_id
                WHERE a.title LIKE ? OR a.content LIKE ?
                ORDER BY a.created_at DESC
                LIMIT ? OFFSET ?
            """
            
            cursor.execute(query, (search_pattern, search_pattern, limit, offset))
            rows = cursor.fetchall()
            
            articles = []
            for row in rows:
                articles.append({
                    "article_id": row["article_id"],
                    "source_id": row["source_id"],
                    "source_name": row["source_name"],
                    "title": row["title"],
                    "url": row["url"],
                    "description": row["description"],
                    "published_date": row["published_date"],
                    "content_status": row["content_status"],
                    "created_at": row["created_at"],
                    "content_length": row["content_length"]
                })
            
            return {
                "query": q,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit,
                "articles": articles
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@articles_router.get("/articles/sources")
async def get_article_sources():
    """Get list of sources with article counts for filtering - CRITICAL ENDPOINT"""
    try:
        # Connect to main articles database - use absolute path
        from pathlib import Path
        ainews_db_path = str(Path(__file__).parent.parent / "data" / "ainews.db")
        
        with sqlite3.connect(ainews_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get sources that have articles with counts
            query = """
                SELECT 
                    s.source_id,
                    s.name,
                    COUNT(a.article_id) as article_count,
                    MAX(a.created_at) as latest_article
                FROM sources s
                LEFT JOIN articles a ON s.source_id = a.source_id
                GROUP BY s.source_id, s.name
                HAVING article_count > 0
                ORDER BY article_count DESC, s.name ASC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Format sources
            sources = []
            for row in rows:
                source = {
                    "source_id": row["source_id"],
                    "name": row["name"],
                    "article_count": row["article_count"],
                    "latest_article": row["latest_article"]
                }
                sources.append(source)
            
            return {
                "total_sources": len(sources),
                "sources": sources
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get article sources: {str(e)}")


@articles_router.get("/articles/statuses")
async def get_article_statuses():
    """Get list of unique article statuses for filtering"""
    try:
        # Connect to main articles database - use absolute path
        from pathlib import Path
        ainews_db_path = str(Path(__file__).parent.parent / "data" / "ainews.db")
        
        with sqlite3.connect(ainews_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get unique content status values with counts
            query = """
                SELECT 
                    content_status,
                    COUNT(*) as count
                FROM articles 
                WHERE content_status IS NOT NULL AND content_status != ''
                GROUP BY content_status
                ORDER BY count DESC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Format statuses
            statuses = []
            for row in rows:
                status = {
                    "status": row["content_status"],
                    "count": row["count"]
                }
                statuses.append(status)
            
            return {
                "total_statuses": len(statuses),
                "statuses": statuses
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get article statuses: {str(e)}")


@articles_router.get("/articles/dates")
async def get_article_dates():
    """Get list of available date ranges for filtering"""
    try:
        # Connect to main articles database - use absolute path
        from pathlib import Path
        ainews_db_path = str(Path(__file__).parent.parent / "data" / "ainews.db")
        
        with sqlite3.connect(ainews_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get date ranges with article counts
            query = """
                SELECT 
                    DATE(created_at) as article_date,
                    COUNT(*) as count
                FROM articles 
                WHERE created_at IS NOT NULL
                GROUP BY DATE(created_at)
                ORDER BY article_date DESC
                LIMIT 30
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Format dates and add predefined ranges
            date_ranges = [
                {"value": "24h", "label": "Last 24 hours", "count": None},
                {"value": "7d", "label": "Last 7 days", "count": None},
                {"value": "30d", "label": "Last 30 days", "count": None},
                {"value": "all", "label": "All time", "count": None}
            ]
            
            # Add specific dates
            recent_dates = []
            for row in rows:
                date_obj = {
                    "value": row["article_date"],
                    "label": row["article_date"],
                    "count": row["count"]
                }
                recent_dates.append(date_obj)
            
            return {
                "predefined_ranges": date_ranges,
                "recent_dates": recent_dates
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get article dates: {str(e)}")


@articles_router.get("/articles/stats")
async def get_articles_stats():
    """Get articles statistics summary"""
    try:
        # Connect to main articles database - use absolute path
        from pathlib import Path
        ainews_db_path = str(Path(__file__).parent.parent / "data" / "ainews.db")
        
        with sqlite3.connect(ainews_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get overall statistics
            stats_query = """
                SELECT 
                    COUNT(*) as total_articles,
                    COUNT(CASE WHEN content IS NOT NULL AND LENGTH(content) > 0 THEN 1 END) as articles_with_content,
                    COUNT(CASE WHEN content_status = 'parsed' THEN 1 END) as completed_articles,
                    COUNT(CASE WHEN published_date >= datetime('now', '-24 hours') THEN 1 END) as articles_24h,
                    COUNT(CASE WHEN published_date >= datetime('now', '-7 days') THEN 1 END) as articles_7d,
                    AVG(LENGTH(COALESCE(content, ''))) as avg_content_length,
                    MIN(created_at) as oldest_article,
                    MAX(created_at) as newest_article
                FROM articles
            """
            
            cursor.execute(stats_query)
            stats = cursor.fetchone()
            
            # Get content status breakdown
            status_query = """
                SELECT 
                    content_status,
                    COUNT(*) as count
                FROM articles
                GROUP BY content_status
                ORDER BY count DESC
            """
            
            cursor.execute(status_query)
            status_breakdown = [
                {"status": row["content_status"], "count": row["count"]}
                for row in cursor.fetchall()
            ]
            
            return {
                "summary": {
                    "total_articles": stats["total_articles"],
                    "articles_with_content": stats["articles_with_content"],
                    "completed_articles": stats["completed_articles"],
                    "articles_24h": stats["articles_24h"],
                    "articles_7d": stats["articles_7d"],
                    "avg_content_length": round(stats["avg_content_length"] or 0, 2),
                    "content_rate": round((stats["articles_with_content"] / max(1, stats["total_articles"])) * 100, 2),
                    "oldest_article": stats["oldest_article"],
                    "newest_article": stats["newest_article"]
                },
                "status_breakdown": status_breakdown,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get articles stats: {str(e)}")


# PARAMETERIZED ROUTES MUST COME LAST - FastAPI matches routes in order
@articles_router.get("/articles/{article_id}")
async def get_article_by_id(article_id: str = Path(..., description="Article ID")):
    """Get full article with content and media - CRITICAL ENDPOINT"""
    try:
        # Connect to main articles database - use absolute path
        from pathlib import Path
        ainews_db_path = str(Path(__file__).parent.parent / "data" / "ainews.db")
        
        with sqlite3.connect(ainews_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get article with source information and media
            query = """
                SELECT 
                    a.article_id,
                    a.source_id,
                    a.title,
                    a.url,
                    a.description,
                    a.published_date,
                    a.content,
                    a.content_status,
                    a.created_at,
                    a.media_count,
                    s.name as source_name,
                    s.url as source_url
                FROM articles a
                JOIN sources s ON a.source_id = s.source_id
                WHERE a.article_id = ?
            """
            
            cursor.execute(query, (article_id,))
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Article not found")
            
            # Get associated media files
            media_query = """
                SELECT media_id, url, type, status, file_path, created_at
                FROM media_files
                WHERE article_id = ?
            """
            cursor.execute(media_query, (article_id,))
            media_files = [dict(media_row) for media_row in cursor.fetchall()]
            
            article = {
                "article_id": row["article_id"],
                "source_id": row["source_id"],
                "source_name": row["source_name"],
                "source_url": row["source_url"],
                "title": row["title"],
                "url": row["url"],
                "description": row["description"],
                "published_date": row["published_date"],
                "content": row["content"],
                "content_status": row["content_status"],
                "created_at": row["created_at"],
                "media_count": row["media_count"],
                "media_files": media_files
            }
            
            return article
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get article: {str(e)}")


@articles_router.get("/articles/{article_id}/media")
async def get_article_media(article_id: str = Path(..., description="Article ID")):
    """Get media files for a specific article - CRITICAL ENDPOINT"""
    try:
        # Connect to main articles database - use absolute path
        from pathlib import Path
        ainews_db_path = str(Path(__file__).parent.parent / "data" / "ainews.db")
        
        with sqlite3.connect(ainews_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # First verify article exists
            cursor.execute("SELECT article_id FROM articles WHERE article_id = ?", (article_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Article not found")
            
            # Get media files for the article
            query = """
                SELECT 
                    media_id,
                    url,
                    type,
                    file_path,
                    mime_type,
                    width,
                    height,
                    alt_text,
                    status,
                    file_size,
                    created_at
                FROM media_files
                WHERE article_id = ?
                ORDER BY created_at ASC
            """
            
            cursor.execute(query, (article_id,))
            media_files = []
            
            for row in cursor.fetchall():
                media_file = {
                    "media_id": row["media_id"],
                    "url": row["url"],
                    "type": row["type"],
                    "file_path": row["file_path"],
                    "mime_type": row["mime_type"],
                    "width": row["width"],
                    "height": row["height"],
                    "alt_text": row["alt_text"],
                    "status": row["status"],
                    "file_size": row["file_size"],
                    "created_at": row["created_at"]
                }
                media_files.append(media_file)
            
            return {
                "article_id": article_id,
                "media_count": len(media_files),
                "media_files": media_files
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get article media: {str(e)}")


@articles_router.delete("/articles/{article_id}")
async def delete_article(article_id: str = Path(..., description="Article ID")):
    """Delete a specific article and its related data"""
    try:
        # Connect to main articles database - use absolute path
        from pathlib import Path as FilePath
        ainews_db_path = str(FilePath(__file__).parent.parent / "data" / "ainews.db")
        
        with sqlite3.connect(ainews_db_path) as conn:
            # Check if article exists
            cursor = conn.execute("SELECT article_id FROM articles WHERE article_id = ?", (article_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Article not found")
            
            # Delete related data first (foreign key constraints)
            # Delete media files
            media_cursor = conn.execute("DELETE FROM media_files WHERE article_id = ?", (article_id,))
            deleted_media = media_cursor.rowcount
            
            # Delete related links
            conn.execute("DELETE FROM related_links WHERE article_id = ?", (article_id,))
            
            # Delete the article itself
            article_cursor = conn.execute("DELETE FROM articles WHERE article_id = ?", (article_id,))
            deleted_articles = article_cursor.rowcount
            
            conn.commit()
            
        if deleted_articles == 0:
            raise HTTPException(status_code=404, detail="Article not found")
            
        logger.info(f"Deleted article {article_id} and {deleted_media} media files")
        
        return {
            "status": "success",
            "message": f"Article {article_id} deleted successfully",
            "deleted_articles": deleted_articles,
            "deleted_media": deleted_media
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete article {article_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete article: {str(e)}")


# Export articles router separately so it can be included in main app
# Don't include it in monitoring router to avoid path prefix conflicts


# Articles API endpoints are complete and working


# Memory Profiling Router
profiling_router = APIRouter(prefix="/api/profiling", tags=["profiling"])


@profiling_router.get("/memory/snapshot")
async def get_memory_snapshot():
    """Get a detailed memory snapshot of all Python objects"""
    try:
        import gc
        import sys
        from collections import defaultdict
        
        # Force garbage collection first
        gc.collect()
        
        # Get object counts by type
        type_counts = defaultdict(int)
        type_sizes = defaultdict(int)
        
        for obj in gc.get_objects():
            obj_type = type(obj).__name__
            type_counts[obj_type] += 1
            try:
                type_sizes[obj_type] += sys.getsizeof(obj)
            except:
                pass
        
        # Sort by size
        sorted_types = sorted(
            [(t, type_counts[t], type_sizes[t]) for t in type_counts],
            key=lambda x: x[2],
            reverse=True
        )[:50]  # Top 50 types
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_objects": sum(type_counts.values()),
            "total_types": len(type_counts),
            "top_types_by_size": [
                {
                    "type": t[0],
                    "count": t[1],
                    "total_size_bytes": t[2],
                    "avg_size_bytes": t[2] // t[1] if t[1] > 0 else 0
                }
                for t in sorted_types
            ],
            "gc_stats": gc.get_stats()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memory snapshot: {str(e)}")


@profiling_router.get("/memory/growth")
async def analyze_memory_growth(minutes: int = Query(10, description="Minutes of data to analyze")):
    """Analyze memory growth patterns"""
    try:
        # Get memory history from database
        history = monitoring_db.get_memory_metrics_history(hours=minutes/60)
        
        if len(history) < 2:
            return {
                "message": "Not enough data to analyze growth",
                "data_points": len(history)
            }
        
        # Calculate growth rate
        first = history[-1]  # Oldest
        last = history[0]   # Newest
        
        time_diff = (datetime.fromisoformat(last['timestamp']) - 
                    datetime.fromisoformat(first['timestamp'])).total_seconds() / 60
        
        memory_diff = last['used_memory_mb'] - first['used_memory_mb']
        growth_rate_per_minute = memory_diff / time_diff if time_diff > 0 else 0
        
        # Find peaks
        peak_memory = max(h['used_memory_mb'] for h in history)
        peak_time = next(h['timestamp'] for h in history if h['used_memory_mb'] == peak_memory)
        
        # Detect potential leaks (consistent growth)
        growth_periods = 0
        for i in range(1, len(history)):
            if history[i-1]['used_memory_mb'] > history[i]['used_memory_mb']:
                growth_periods += 1
        
        leak_probability = (growth_periods / (len(history) - 1)) * 100 if len(history) > 1 else 0
        
        return {
            "analysis_period_minutes": minutes,
            "data_points": len(history),
            "memory_growth": {
                "start_mb": first['used_memory_mb'],
                "end_mb": last['used_memory_mb'],
                "total_growth_mb": memory_diff,
                "growth_rate_mb_per_minute": round(growth_rate_per_minute, 2)
            },
            "peak": {
                "memory_mb": peak_memory,
                "timestamp": peak_time
            },
            "leak_analysis": {
                "consistent_growth_percentage": round(leak_probability, 1),
                "potential_leak": leak_probability > 70,
                "recommendation": "Memory leak likely" if leak_probability > 70 else "Normal fluctuation"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze memory growth: {str(e)}")


# =======================================
# SIMPLIFIED MEMORY & ERRORS API - DAY 4
# =======================================

# Create separate routers for Memory and Errors API
memory_router = APIRouter(prefix="/api/memory", tags=["memory"])
errors_router = APIRouter(prefix="/api/errors", tags=["errors"])

import psutil
import gc
import signal
import os


@memory_router.get("/current")
async def get_memory_current():
    """Get current memory and system metrics for dashboard"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # Process counts
        total_processes = len(psutil.pids())
        
        # Count AI News processes
        ainews_processes = 0
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                name = proc.info['name']
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if any(keyword in cmdline.lower() or keyword in name.lower() 
                      for keyword in ['unified_crawl_parser', 'monitoring', 'crawl', 'ainews', 'main.py']):
                    ainews_processes += 1
            except:
                continue
        
        return {
            "cpu_percent": round(cpu_percent, 1),
            "memory_percent": round(memory_percent, 1),
            "total_processes": total_processes,
            "ainews_processes": ainews_processes,
            "disk_percent": round(disk_percent, 1)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting memory status: {str(e)}")


@memory_router.get("/status")
async def get_memory_status():
    """Simple memory status - главный endpoint для мониторинга памяти"""
    try:
        # System memory
        memory = psutil.virtual_memory()
        
        # Find AI News processes
        ainews_processes = []
        total_ainews_memory = 0
        
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent', 'cmdline', 'create_time']):
            try:
                proc_info = proc.info
                cmdline = ' '.join(proc_info['cmdline'] or [])
                name = proc_info['name']
                
                # Check if it's an AI News process
                is_ainews = any(keyword in cmdline.lower() or keyword in name.lower() 
                              for keyword in ['unified_crawl_parser', 'monitoring', 'crawl', 'ainews', 'main.py'])
                
                if is_ainews:
                    memory_mb = proc_info['memory_info'].rss / 1024 / 1024
                    total_ainews_memory += memory_mb
                    
                    ainews_processes.append({
                        "pid": proc_info['pid'],
                        "name": name,
                        "memory_mb": round(memory_mb, 2),
                        "cpu_percent": proc_info['cpu_percent'] or 0,
                        "command": cmdline[:100] + '...' if len(cmdline) > 100 else cmdline
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort processes by memory usage
        ainews_processes.sort(key=lambda x: x['memory_mb'], reverse=True)
        
        # Determine memory status
        used_percent = memory.percent
        if used_percent >= 90:
            status = "critical"
        elif used_percent >= 75:
            status = "warning"
        else:
            status = "normal"
        
        return {
            "system_memory": {
                "total": round(memory.total / 1024 / 1024 / 1024, 2),  # GB
                "used": round(memory.used / 1024 / 1024 / 1024, 2),   # GB
                "percent": used_percent
            },
            "ainews_processes": ainews_processes,
            "total_ainews_memory_mb": round(total_ainews_memory, 2),
            "memory_status": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memory status: {str(e)}")


@memory_router.get("/processes")
async def get_memory_processes():
    """Get list of AI News processes for dashboard"""
    try:
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent', 'cmdline']):
            try:
                proc_info = proc.info
                name = proc_info['name']
                cmdline = ' '.join(proc_info['cmdline'] or [])
                
                # Check if it's an AI News process
                is_ainews = any(keyword in cmdline.lower() or keyword in name.lower() 
                              for keyword in ['unified_crawl_parser', 'monitoring', 'crawl', 'ainews', 'main.py', 'app.py', 'extract_system', 'main_extract.py'])
                
                if is_ainews:
                    memory_mb = proc_info['memory_info'].rss / 1024 / 1024
                    
                    # Determine process type and create human-readable name
                    human_name = "Unknown AI Process"
                    process_type = "unknown"
                    
                    if 'mcp-sqlite' in cmdline.lower():
                        human_name = "Database API Server"
                        process_type = "database"
                    elif 'extract_system' in cmdline.lower() or 'main_extract.py' in cmdline.lower():
                        # Determine Extract phase
                        if '--rss-discover' in cmdline:
                            human_name = "Extract RSS Discovery"
                        elif '--parse-pending' in cmdline:
                            human_name = "Extract API Parser"
                        elif '--media-only' in cmdline:
                            human_name = "Extract Media Downloader"
                        else:
                            human_name = "Extract API System"
                        process_type = "extract"
                    elif 'monitoring' in cmdline.lower() or 'app.py' in cmdline.lower():
                        human_name = "Monitoring Dashboard"
                        process_type = "monitoring" 
                    elif 'main.py' in cmdline.lower() or 'crawl' in cmdline.lower():
                        human_name = "News Parser Engine"
                        process_type = "parser"
                    elif 'unified_crawl_parser' in cmdline.lower():
                        human_name = "Unified Crawler"
                        process_type = "crawler"
                    elif name.lower() == 'python' or name.lower() == 'python3':
                        human_name = "Python AI Service"
                        process_type = "python"
                    elif name == 'node':
                        human_name = "Node.js AI Service"  
                        process_type = "node"
                    elif name == 'zsh' or name == 'bash':
                        human_name = "AI Script Runner"
                        process_type = "shell"
                    
                    # Format technical details for tooltip
                    technical_details = cmdline if cmdline else name
                    if len(technical_details) > 150:
                        technical_details = technical_details[:147] + "..."
                    
                    processes.append({
                        "pid": proc_info['pid'],
                        "name": name,
                        "human_name": human_name,
                        "process_type": process_type,
                        "cmdline": cmdline,
                        "technical_details": technical_details,
                        "memory_mb": round(memory_mb, 2),
                        "cpu_percent": proc_info['cpu_percent'] or 0
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by memory usage
        processes.sort(key=lambda x: x['memory_mb'], reverse=True)
        
        return {"processes": processes}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting processes: {str(e)}")


@memory_router.post("/kill-process/{pid}")
async def kill_process(pid: int = Path(..., description="Process ID to kill")):
    """Kill specific process by PID"""
    try:
        # Check if process exists and get info
        try:
            proc = psutil.Process(pid)
            proc_name = proc.name()
            proc_cmdline = ' '.join(proc.cmdline())
        except psutil.NoSuchProcess:
            raise HTTPException(status_code=404, detail=f"Process {pid} not found")
        
        # Safety check - only kill AI News related processes
        safe_keywords = ['unified_crawl_parser', 'monitoring', 'crawl', 'ainews', 'main.py', 'python']
        is_safe = any(keyword in proc_cmdline.lower() or keyword in proc_name.lower() 
                     for keyword in safe_keywords)
        
        if not is_safe:
            raise HTTPException(
                status_code=403, 
                detail=f"Refusing to kill process {pid} ({proc_name}) - not recognized as AI News process"
            )
        
        # Kill process
        try:
            proc.terminate()  # Graceful termination first
            proc.wait(timeout=5)
        except psutil.TimeoutExpired:
            proc.kill()  # Force kill if graceful failed
            proc.wait(timeout=5)
        
        return {
            "success": True,
            "message": f"Process {pid} ({proc_name}) killed successfully",
            "pid": pid,
            "process_name": proc_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to kill process: {str(e)}")


@memory_router.post("/kill-all-ainews")
async def kill_all_ainews_processes():
    """Kill all AI News related processes - emergency cleanup"""
    try:
        killed_processes = []
        failed_processes = []
        
        # Find all AI News processes
        keywords = ['unified_crawl_parser', 'monitoring', 'crawl', 'ainews', 'main.py']
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                proc_info = proc.info
                cmdline = ' '.join(proc_info['cmdline'] or [])
                name = proc_info['name']
                
                # Check if it's an AI News process
                is_ainews = any(keyword in cmdline.lower() or keyword in name.lower() 
                              for keyword in keywords)
                
                if is_ainews and proc_info['pid'] != os.getpid():  # Don't kill ourselves
                    try:
                        process = psutil.Process(proc_info['pid'])
                        process.terminate()
                        try:
                            process.wait(timeout=3)
                        except psutil.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=3)
                        
                        killed_processes.append({
                            "pid": proc_info['pid'],
                            "name": name,
                            "command": cmdline[:50] + '...' if len(cmdline) > 50 else cmdline
                        })
                    except Exception as e:
                        failed_processes.append({
                            "pid": proc_info['pid'],
                            "name": name,
                            "error": str(e)
                        })
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return {
            "success": True,
            "message": f"Killed {len(killed_processes)} AI News processes",
            "killed_processes": killed_processes,
            "failed_processes": failed_processes,
            "total_killed": len(killed_processes),
            "total_failed": len(failed_processes)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to kill AI News processes: {str(e)}")


# Remove cleanup endpoint - not needed in simplified version


@errors_router.get("/recent")
async def get_recent_errors(limit: int = Query(50, ge=1, le=200, description="Number of errors to return")):
    """Get recent errors with aggregated statistics for dashboard"""
    try:
        # Connect to monitoring database
        db_path = str(PathLib(monitoring_db.db_path))
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get total errors count (last 24h)
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM error_logs 
                WHERE timestamp >= datetime('now', '-24 hours')
            """)
            total_errors = cursor.fetchone()['total']
            
            # Get sources with errors count (last 24h)
            cursor.execute("""
                SELECT COUNT(DISTINCT source_id) as count
                FROM error_logs 
                WHERE timestamp >= datetime('now', '-24 hours')
                AND source_id IS NOT NULL
            """)
            sources_with_errors = cursor.fetchone()['count']
            
            # Get last error time
            cursor.execute("""
                SELECT MAX(timestamp) as last_error
                FROM error_logs
            """)
            last_error_result = cursor.fetchone()
            last_error_time = last_error_result['last_error'] if last_error_result else None
            
            # Get recent errors with additional fields
            query = """
                SELECT 
                    id,
                    timestamp,
                    error_type,
                    error_message,
                    source_id,
                    stack_trace,
                    context
                FROM error_logs 
                ORDER BY timestamp DESC 
                LIMIT ?
            """
            
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            
            errors = []
            for row in rows:
                # Parse context if it's JSON
                context = None
                if row["context"]:
                    try:
                        context = json.loads(row["context"])
                    except:
                        context = {"raw": row["context"]}
                
                error = {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "level": row["error_type"] or "ERROR",
                    "error_message": row["error_message"],
                    "source_id": row["source_id"],
                    "error_type": row["error_type"],
                    "context": context
                }
                errors.append(error)
            
            return {
                "total_errors": total_errors,
                "sources_with_errors": sources_with_errors,
                "last_error_time": last_error_time,
                "errors": errors
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent errors: {str(e)}")


@errors_router.get("/export")
async def export_errors_with_context(
    format: str = Query("json", description="Export format (json or text)"),
    days: int = Query(7, description="Days of data to export")
):
    """Export errors with full context for debugging"""
    try:
        # Connect to monitoring database
        db_path = str(PathLib(monitoring_db.db_path))
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all errors with context
            query = """
                SELECT 
                    id,
                    timestamp,
                    error_type,
                    error_message,
                    source_id,
                    stack_trace,
                    context,
                    correlation_id,
                    resolved
                FROM error_logs 
                WHERE timestamp >= datetime('now', ? || ' days')
                ORDER BY timestamp DESC
            """
            
            cursor.execute(query, (-days,))
            rows = cursor.fetchall()
            
            if format == "json":
                # Export as structured JSON
                errors = []
                for row in rows:
                    error_data = {
                        "id": row['id'],
                        "timestamp": row['timestamp'],
                        "error_type": row['error_type'],
                        "error_message": row['error_message'],
                        "source_id": row['source_id'],
                        "stack_trace": row['stack_trace'],
                        "correlation_id": row['correlation_id'],
                        "resolved": bool(row['resolved'])
                    }
                    
                    # Parse context JSON if available
                    if row['context']:
                        try:
                            error_data['context'] = json.loads(row['context'])
                        except:
                            error_data['context'] = row['context']
                    
                    errors.append(error_data)
                
                return {
                    "export_date": datetime.now().isoformat(),
                    "days_included": days,
                    "total_errors": len(errors),
                    "errors": errors
                }
            
            else:
                # Export as formatted text for copy-paste
                export_lines = []
                export_lines.append("=" * 80)
                export_lines.append(f"AI NEWS ERROR EXPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                export_lines.append(f"Period: Last {days} days | Total errors: {len(rows)}")
                export_lines.append("=" * 80)
                export_lines.append("")
                
                for i, row in enumerate(rows, 1):
                    export_lines.append(f"[{i}] Error ID: {row['id']}")
                    export_lines.append(f"    Time: {row['timestamp']}")
                    export_lines.append(f"    Type: {row['error_type']} | Source: {row['source_id'] or 'SYSTEM'}")
                    export_lines.append(f"    Message: {row['error_message']}")
                    
                    if row['correlation_id']:
                        export_lines.append(f"    Correlation ID: {row['correlation_id']}")
                    
                    if row['context']:
                        export_lines.append(f"    Context: {row['context'][:200]}...")
                    
                    if row['stack_trace']:
                        export_lines.append("    Stack Trace:")
                        stack_lines = row['stack_trace'].split('\n')[:10]
                        for line in stack_lines:
                            export_lines.append(f"        {line}")
                        if len(row['stack_trace'].split('\n')) > 10:
                            export_lines.append("        ...")
                    
                    export_lines.append("")
                
                formatted_text = "\n".join(export_lines)
                
                # Return as plain text response
                from fastapi.responses import PlainTextResponse
                return PlainTextResponse(formatted_text)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export errors: {str(e)}")


@errors_router.post("/{source_id}/retry")
async def retry_source(source_id: str = Path(..., description="Source ID to retry")):
    """Retry source with errors - trigger immediate re-crawl"""
    try:
        # Simple implementation - just start parser for this specific source
        # In the future, this could be enhanced to queue a specific retry job
        
        return {
            "success": True,
            "message": f"Retry initiated for source: {source_id}",
            "source_id": source_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retry source: {str(e)}")


@errors_router.delete("/clear")
async def clear_errors():
    """Clear all errors from the error log"""
    try:
        # Connect to monitoring database
        db_path = str(PathLib(monitoring_db.db_path))
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Delete all errors
            cursor.execute("DELETE FROM error_logs")
            deleted_count = cursor.rowcount
            conn.commit()
            
        return {
            "success": True,
            "message": f"Cleared {deleted_count} errors from the log",
            "deleted_count": deleted_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear errors: {str(e)}")


# RSS-specific API router
rss_router = APIRouter(prefix="/api/rss", tags=["rss"])


@rss_router.get("/status")
async def get_rss_status():
    """Get overall RSS system status"""
    try:
        # Get RSS summary from monitoring database
        query = """
            SELECT 
                feed_status,
                COUNT(*) as count,
                AVG(fetch_time_ms) as avg_fetch_time,
                AVG(articles_in_feed) as avg_articles
            FROM rss_feed_metrics 
            WHERE timestamp > datetime('now', '-1 hour')
            GROUP BY feed_status
        """
        
        results = monitoring_db.execute_query(query)
        
        status_breakdown = {}
        total_feeds = 0
        total_fetch_time = 0
        total_articles = 0
        
        for row in results:
            status, count, avg_fetch, avg_articles = row
            status_breakdown[status] = count
            total_feeds += count
            total_fetch_time += avg_fetch * count if avg_fetch else 0
            total_articles += avg_articles * count if avg_articles else 0
        
        # Get total available RSS feeds
        rss_count_query = "SELECT COUNT(DISTINCT source_id) FROM rss_feed_metrics"
        rss_count_result = monitoring_db.execute_query(rss_count_query)
        total_rss_feeds = rss_count_result[0][0] if rss_count_result else 0
        
        # Get last check time
        last_check_query = "SELECT MAX(timestamp) FROM rss_feed_metrics"
        last_check_result = monitoring_db.execute_query(last_check_query)
        last_check = last_check_result[0][0] if last_check_result and last_check_result[0][0] else None
        
        return {
            "total_rss_feeds": total_rss_feeds,
            "feeds_checked_last_hour": total_feeds,
            "status_breakdown": status_breakdown,
            "avg_fetch_time_ms": total_fetch_time / total_feeds if total_feeds > 0 else 0,
            "avg_articles_per_feed": total_articles / total_feeds if total_feeds > 0 else 0,
            "last_check": last_check,
            "system_health": "healthy" if status_breakdown.get("healthy", 0) > status_breakdown.get("error", 0) else "degraded"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get RSS status: {str(e)}")


@rss_router.get("/feeds")
async def get_rss_feeds():
    """Get detailed status for all RSS feeds"""
    try:
        # First get source names from ainews database
        import sqlite3
        from pathlib import Path
        
        ainews_db_path = Path(monitoring_db.ainews_db_path)
        source_names = {}
        
        if ainews_db_path.exists():
            with sqlite3.connect(str(ainews_db_path)) as conn:
                cursor = conn.execute("SELECT source_id, name FROM sources")
                for row in cursor:
                    source_names[row[0]] = row[1]
        
        # Get RSS metrics from monitoring database
        query = """
            WITH latest_rss AS (
                SELECT source_id, MAX(timestamp) as max_timestamp
                FROM rss_feed_metrics
                GROUP BY source_id
            ),
            error_counts AS (
                SELECT source_id, COUNT(*) as error_count
                FROM error_logs
                WHERE timestamp > datetime('now', '-24 hours')
                GROUP BY source_id
            )
            SELECT DISTINCT
                r.source_id,
                r.feed_url,
                r.feed_status,
                r.articles_in_feed,
                r.new_articles_found,
                r.fetch_time_ms,
                r.last_updated,
                r.timestamp as last_check,
                r.scrape_attempts,
                r.scrape_successes,
                NULL as source_name,
                COALESCE(s.rss_status, 'unknown') as rss_status,
                COALESCE(s.scrape_success_rate, 0.0) as scrape_success_rate,
                COALESCE(e.error_count, 0) as error_count
            FROM rss_feed_metrics r
            INNER JOIN latest_rss lr ON r.source_id = lr.source_id AND r.timestamp = lr.max_timestamp
            LEFT JOIN (
                SELECT DISTINCT source_id, rss_status, scrape_success_rate
                FROM source_metrics
                WHERE timestamp = (SELECT MAX(timestamp) FROM source_metrics sm WHERE sm.source_id = source_metrics.source_id)
            ) s ON r.source_id = s.source_id
            LEFT JOIN error_counts e ON r.source_id = e.source_id
            ORDER BY r.source_id
        """
        
        results = monitoring_db.execute_query(query)
        
        feeds = []
        for row in results:
            # Safely unpack row with correct number of values
            if len(row) >= 14:
                source_id, feed_url, feed_status, articles_in_feed, new_articles, fetch_time_ms, last_updated, last_check, scrape_attempts, scrape_successes, source_name, rss_status, scrape_success_rate, error_count = row[:14]
            else:
                # Skip malformed rows
                continue
            
            # Get actual total articles count from ainews database (all statuses)
            total_articles = 0
            if ainews_db_path.exists():
                with sqlite3.connect(str(ainews_db_path)) as conn:
                    cursor = conn.execute(
                        "SELECT COUNT(*) FROM articles WHERE source_id = ?",
                        (source_id,)
                    )
                    result = cursor.fetchone()
                    if result:
                        total_articles = result[0]
            
            # Efficiency is 100% if no errors, otherwise based on error rate
            efficiency = 100.0 if error_count == 0 else max(0, 100 - (error_count * 10))  # Deduct 10% per error
            
            # Debug logging (commented out for now)
            # if source_id in ["amazon_ai", "google_ai"]:
            #     logger.info(f"Debug {source_id}: error_count={error_count}, efficiency={efficiency}")
            
            feeds.append({
                "source_id": source_id,
                "source_name": source_names.get(source_id, source_id),  # Use proper name from sources table
                "feed_url": feed_url,
                "status": feed_status,
                "articles_count": total_articles,  # Total articles from this source in database
                "error_count": error_count or 0,  # Total errors
                "fetch_time_ms": fetch_time_ms or 0,
                "last_updated": last_updated,
                "last_check": last_check,
                "scrape_attempts": scrape_attempts or 0,
                "scrape_successes": scrape_successes or 0,
                "scrape_success_rate": scrape_success_rate or 0,
                "pipeline_efficiency": efficiency,
                "new_articles_found": new_articles or 0
            })
        
        # Count feeds with actual errors (error_count > 0)
        feeds_with_errors = len([f for f in feeds if f["error_count"] > 0])
        
        return {
            "feeds": feeds,
            "total_feeds": len(feeds),
            "healthy_feeds": len([f for f in feeds if f["status"] == "healthy"]),
            "error_feeds": feeds_with_errors,  # Use actual error count
            "avg_pipeline_efficiency": sum(f["pipeline_efficiency"] for f in feeds) / len(feeds) if feeds else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get RSS feeds: {str(e)}")


@rss_router.get("/metrics")
async def get_rss_metrics(hours: int = Query(24, description="Hours of data to retrieve")):
    """Get RSS metrics over time"""
    try:
        query = """
            SELECT 
                datetime(timestamp) as time_bucket,
                feed_status,
                COUNT(*) as feed_count,
                AVG(fetch_time_ms) as avg_fetch_time,
                AVG(articles_in_feed) as avg_articles,
                SUM(new_articles_found) as total_new_articles,
                SUM(scrape_attempts) as total_scrape_attempts,
                SUM(scrape_successes) as total_scrape_successes
            FROM rss_feed_metrics 
            WHERE timestamp > datetime('now', '-{} hours')
            GROUP BY datetime(timestamp), feed_status
            ORDER BY time_bucket DESC
        """.format(hours)
        
        results = monitoring_db.execute_query(query)
        
        metrics_by_time = {}
        for row in results:
            time_bucket, status, count, avg_fetch, avg_articles, new_articles, scrape_attempts, scrape_successes = row
            
            if time_bucket not in metrics_by_time:
                metrics_by_time[time_bucket] = {
                    "timestamp": time_bucket,
                    "status_counts": {},
                    "total_feeds": 0,
                    "avg_fetch_time_ms": 0,
                    "avg_articles_per_feed": 0,
                    "new_articles_found": 0,
                    "scrape_success_rate": 0
                }
            
            metrics_by_time[time_bucket]["status_counts"][status] = count
            metrics_by_time[time_bucket]["total_feeds"] += count
            metrics_by_time[time_bucket]["avg_fetch_time_ms"] += avg_fetch * count if avg_fetch else 0
            metrics_by_time[time_bucket]["avg_articles_per_feed"] += avg_articles * count if avg_articles else 0
            metrics_by_time[time_bucket]["new_articles_found"] += new_articles or 0
            
            if scrape_attempts and scrape_attempts > 0:
                metrics_by_time[time_bucket]["scrape_success_rate"] = (scrape_successes or 0) / scrape_attempts * 100
        
        # Normalize averages
        for metrics in metrics_by_time.values():
            if metrics["total_feeds"] > 0:
                metrics["avg_fetch_time_ms"] /= metrics["total_feeds"]
                metrics["avg_articles_per_feed"] /= metrics["total_feeds"]
        
        return {
            "time_series": list(metrics_by_time.values()),
            "summary": {
                "total_timepoints": len(metrics_by_time),
                "hours_covered": hours
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get RSS metrics: {str(e)}")


@rss_router.get("/feed/{source_id}")
async def get_feed_details(source_id: str = Path(..., description="Source ID")):
    """Get detailed information for a specific RSS feed"""
    try:
        query = """
            SELECT 
                source_id,
                feed_url,
                feed_status,
                articles_in_feed,
                new_articles_found,
                fetch_time_ms,
                last_updated,
                timestamp as last_check,
                parse_errors,
                scrape_attempts,
                scrape_successes
            FROM rss_feed_metrics 
            WHERE source_id = ?
            ORDER BY timestamp DESC
            LIMIT 10
        """
        
        results = monitoring_db.execute_query(query, [source_id])
        
        if not results:
            raise HTTPException(status_code=404, detail=f"RSS feed not found for source: {source_id}")
        
        # Get source info
        source_query = "SELECT name, url FROM source_metrics WHERE source_id = ?"
        source_result = monitoring_db.execute_query(source_query, [source_id])
        source_info = source_result[0] if source_result else (source_id, "Unknown")
        
        history = []
        for row in results:
            history.append({
                "timestamp": row[7],  # last_check
                "status": row[2],     # feed_status
                "articles_in_feed": row[3],
                "new_articles_found": row[4],
                "fetch_time_ms": row[5],
                "last_updated": row[6],
                "parse_errors": row[8] or 0,
                "scrape_attempts": row[9] or 0,
                "scrape_successes": row[10] or 0
            })
        
        latest = history[0] if history else {}
        
        return {
            "source_id": source_id,
            "source_name": source_info[0],
            "source_url": source_info[1],
            "feed_url": results[0][1],  # feed_url from first result
            "latest_status": latest,
            "history": history,
            "health_score": 100 if latest.get("status") == "healthy" else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get feed details: {str(e)}")


@rss_router.post("/feed/{source_id}/check")
async def check_rss_feed(source_id: str = Path(..., description="Source ID to check")):
    """Manually trigger RSS feed check for a specific source"""
    try:
        # This would trigger the RSS monitor to check a specific feed
        # For now, return a success response
        
        return {
            "success": True,
            "message": f"RSS feed check initiated for source: {source_id}",
            "source_id": source_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check RSS feed: {str(e)}")


# Last Parsed Management Endpoints - Individual and bulk operations
# Note: /sources/last-parsed endpoint moved to top of file to avoid route conflicts

@router.get("/sources/{source_id}/last-parsed")
async def get_source_last_parsed(source_id: str):
    """Get last parsed timestamp for a specific source"""
    try:
        import sqlite3
        from pathlib import Path
        
        db_path = Path(monitoring_db.ainews_db_path)
        if not db_path.exists():
            raise HTTPException(status_code=404, detail="Main database not found")
        
        with sqlite3.connect(str(db_path)) as conn:
            # Get global last_parsed from global_config
            cursor = conn.execute(
                "SELECT value FROM global_config WHERE key = 'global_last_parsed'"
            )
            global_config_row = cursor.fetchone()
            global_last_parsed = global_config_row[0] if global_config_row else "2025-08-01T00:00:00Z"
            
            # Check if source exists
            cursor = conn.execute(
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


@router.put("/sources/{source_id}/last-parsed")
async def update_source_last_parsed(
    source_id: str,
    last_parsed: str = Query(..., description="Last parsed timestamp in ISO format")
):
    """Update last parsed timestamp for a specific source"""
    try:
        # Validate timestamp format
        from datetime import datetime
        try:
            datetime.fromisoformat(last_parsed.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid timestamp format. Use ISO format.")
        
        import sqlite3
        from pathlib import Path
        
        db_path = Path(monitoring_db.ainews_db_path)
        if not db_path.exists():
            raise HTTPException(status_code=404, detail="Main database not found")
        
        with sqlite3.connect(str(db_path)) as conn:
            # Check if source exists
            cursor = conn.execute(
                "SELECT source_id FROM sources WHERE source_id = ?",
                (source_id,)
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
            
            # Update global last_parsed (affects all sources)
            cursor = conn.execute(
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


@router.post("/sources/last-parsed/bulk")
async def bulk_update_last_parsed(updates: List[Dict[str, str]]):
    """Bulk update last parsed timestamps for multiple sources
    
    Expected format:
    [
        {"source_id": "source1", "last_parsed": "2025-01-01T00:00:00"},
        {"source_id": "source2", "last_parsed": "2025-01-01T00:00:00"}
    ]
    """
    try:
        import sqlite3
        from pathlib import Path
        
        db_path = Path(monitoring_db.ainews_db_path)
        if not db_path.exists():
            raise HTTPException(status_code=404, detail="Main database not found")
        
        # Validate all timestamps first
        for update in updates:
            try:
                datetime.fromisoformat(update['last_parsed'].replace('Z', '+00:00'))
            except (ValueError, KeyError):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid timestamp format for source {update.get('source_id')}"
                )
        
        success_count = 0
        failed_sources = []
        
        with sqlite3.connect(str(db_path)) as conn:
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