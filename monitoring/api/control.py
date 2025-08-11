"""
System control and process management API endpoints
"""
from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, Dict, Any
from datetime import datetime
import os

# Import core utilities
from .core import (
    get_monitoring_db, get_monitoring_integration, get_process_status,
    ProcessControlResponse, HealthCheckResponse, format_timestamp,
    handle_db_error, get_rss_sources_summary, logger
)

# Import process manager
from ..process_manager import get_process_manager, ProcessStatus

router = APIRouter(prefix="/api/monitoring", tags=["control"])

@router.get("/dashboard")
async def get_dashboard_data():
    """Get comprehensive dashboard data"""
    try:
        monitoring_db = get_monitoring_db()
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
                # Calculate real success rate: sources with articles / active sources
                "success_rate": (len([s for s in source_metrics if s.recent_articles_24h > 0]) / max(1, system_metrics.active_sources)) * 100 if source_metrics else 0,
                "last_update": system_metrics.last_update.isoformat()
            },
            "sources_by_status": sources_by_status,
            "problematic_sources": [
                {
                    "source_id": s.source_id,
                    "name": s.name,
                    "status": s.last_status,
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

@router.get("/sources")
async def get_sources_monitoring(
    status: Optional[str] = Query(None, description="Filter by status"),
    type: Optional[str] = Query(None, description="Filter by type"),
    problematic: Optional[str] = Query(None, description="Filter problematic sources"),
    sort_by: str = Query("recent_errors", description="Sort field"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200)
):
    """Get monitored sources with filtering and pagination"""
    try:
        monitoring_db = get_monitoring_db()
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
        
        # Sort
        reverse = (sort_order == "desc")
        if sort_by == "recent_errors":
            filtered_sources.sort(key=lambda s: s.recent_errors_24h, reverse=reverse)
        elif sort_by == "success_rate":
            filtered_sources.sort(key=lambda s: s.success_rate, reverse=reverse)
        elif sort_by == "recent_articles":
            filtered_sources.sort(key=lambda s: s.recent_articles_24h, reverse=reverse)
        elif sort_by == "name":
            filtered_sources.sort(key=lambda s: s.name.lower(), reverse=reverse)
        
        # Paginate
        total = len(filtered_sources)
        start = (page - 1) * limit
        end = start + limit
        paginated_sources = filtered_sources[start:end]
        
        # Convert to dict format
        sources_data = []
        for source in paginated_sources:
            sources_data.append({
                "source_id": source.source_id,
                "name": source.name,
                "url": source.url,
                "type": source.type,
                "last_status": source.last_status,
                "success_rate": source.success_rate,
                "recent_articles_24h": source.recent_articles_24h,
                "recent_errors_24h": source.recent_errors_24h,
                "total_articles": source.total_articles,
                "total_successful_parses": source.total_successful_parses,
                "total_failed_parses": source.total_failed_parses,
                "avg_parse_time_ms": source.avg_parse_time_ms,
                "last_successful_parse": source.last_successful_parse.isoformat() if source.last_successful_parse else None,
                "last_error": source.last_error.isoformat() if source.last_error else None,
                "status": source.status
            })
        
        return {
            "sources": sources_data,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit if total > 0 else 0
            },
            "filters": {
                "status": status,
                "type": type,
                "problematic": problematic,
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sources/last-parsed")
async def get_sources_last_parsed():
    """Get last parsed timestamps for all sources"""
    try:
        from .core import get_ainews_db_connection, get_global_last_parsed
        
        # Get global timestamp (affects all sources)
        global_last_parsed = get_global_last_parsed()
        
        with get_ainews_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT source_id, name FROM sources ORDER BY name")
            sources = cursor.fetchall()
        
        # Return all sources with the same global timestamp
        sources_data = []
        for source in sources:
            sources_data.append({
                "source_id": source[0],
                "source_name": source[1],
                "last_parsed": global_last_parsed
            })
        
        return {
            "sources": sources_data,
            "global_last_parsed": global_last_parsed,
            "count": len(sources_data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sources/{source_id}")
async def get_source_details(source_id: str = Path(..., description="Source ID to get details for")):
    """Get detailed information about a specific source"""
    try:
        monitoring_db = get_monitoring_db()
        # Get source from monitoring database
        source_metrics = monitoring_db.get_source_metrics()
        source = next((s for s in source_metrics if s.source_id == source_id), None)
        
        if not source:
            raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
        
        # Get additional details from main database
        from .core import get_ainews_db_connection
        with get_ainews_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get basic source info
            cursor.execute(
                "SELECT name, url, type, status FROM sources WHERE source_id = ?",
                (source_id,)
            )
            source_info = cursor.fetchone()
            
            # Get recent articles (last 10)
            cursor.execute("""
                SELECT article_id, title, published_date, content_status
                FROM articles 
                WHERE source_id = ? 
                ORDER BY published_date DESC 
                LIMIT 10
            """, (source_id,))
            recent_articles = cursor.fetchall()
            
        return {
            "source_id": source.source_id,
            "name": source.name,
            "url": source.url,
            "type": source.type,
            "status": source.status,
            "last_status": source.last_status,
            "success_rate": source.success_rate,
            "recent_articles_24h": source.recent_articles_24h,
            "recent_errors_24h": source.recent_errors_24h,
            "total_articles": source.total_articles,
            "total_successful_parses": source.total_successful_parses,
            "total_failed_parses": source.total_failed_parses,
            "avg_parse_time_ms": source.avg_parse_time_ms,
            "last_successful_parse": source.last_successful_parse.isoformat() if source.last_successful_parse else None,
            "last_error": source.last_error.isoformat() if source.last_error else None,
            "recent_articles": [
                {
                    "article_id": article[0],
                    "title": article[1],
                    "published_at": article[2],  # published_date mapped to published_at
                    "status": article[3]  # content_status mapped to status
                }
                for article in recent_articles
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sources/toggle/{source_id}")
async def toggle_source(source_id: str = Path(..., description="Source ID to toggle")):
    """Toggle source between active and inactive status"""
    try:
        from .core import toggle_source_status
        result = toggle_source_status(source_id)
        
        return {
            "success": True,
            "message": f"Source {source_id} status changed from {result['old_status']} to {result['new_status']}",
            "source_id": source_id,
            "old_status": result['old_status'],
            "new_status": result['new_status'],
            "timestamp": format_timestamp(datetime.now())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle source: {str(e)}")

@router.get("/error-breakdown")
async def get_error_breakdown():
    """Get breakdown of errors by type and source"""
    try:
        monitoring_db = get_monitoring_db()
        
        # Get error summary for last 24 hours
        error_summary = monitoring_db.get_error_summary(hours=24)
        
        return {
            "time_period": "24 hours",
            "total_errors": sum(error_summary.values()),
            "errors_by_type": error_summary,
            "timestamp": format_timestamp(datetime.now())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/errors/recent")
async def get_recent_errors(
    level: Optional[str] = Query(None, description="Filter by error level"),
    source: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(100, ge=1, le=500, description="Number of errors to return")
):
    """Get recent errors from monitoring database"""
    try:
        from .core import get_monitoring_db_connection
        
        with get_monitoring_db_connection() as conn:
            conditions = []
            params = []
            
            if level:
                conditions.append("error_type = ?")
                params.append(level)
            
            if source:
                conditions.append("source = ?")
                params.append(source)
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            query = f"""
                SELECT timestamp, error_type, error_message, source, context
                FROM error_logs
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT ?
            """
            params.append(limit)
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            errors = []
            for row in cursor.fetchall():
                errors.append({
                    "timestamp": row[0],
                    "level": row[1],
                    "message": row[2],
                    "source": row[3],
                    "context": row[4]
                })
        
        return {
            "errors": errors,
            "count": len(errors),
            "filters": {
                "level": level,
                "source": source,
                "limit": limit
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/errors/{error_id}/debug")
async def get_error_debug_info(error_id: str):
    """Get debug information for a specific error"""
    # Simplified - just return basic info since complex error context was removed
    return {
        "error_id": error_id,
        "debug_info": "Error debug functionality simplified",
        "timestamp": format_timestamp(datetime.now())
    }

@router.get("/logs/summary")
async def get_logs_summary():
    """Get summary of log entries by level"""
    try:
        from .core import get_monitoring_db_connection
        
        with get_monitoring_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT error_type, COUNT(*) as count
                FROM error_logs
                WHERE timestamp >= datetime('now', '-24 hours')
                GROUP BY error_type
                ORDER BY count DESC
            """)
            
            summary = {}
            total = 0
            
            for row in cursor.fetchall():
                level = row[0] or "unknown"
                count = row[1]
                summary[level] = count
                total += count
        
        return {
            "summary": summary,
            "total": total,
            "period": "24 hours",
            "timestamp": format_timestamp(datetime.now())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """System health check endpoint"""
    try:
        monitoring_db = get_monitoring_db()
        system_metrics = monitoring_db.get_system_metrics()
        
        # Check database connectivity
        database_connected = True
        try:
            monitoring_db.get_system_metrics()
        except Exception:
            database_connected = False
        
        # Check if monitoring is active
        monitoring_active = system_metrics.total_sources > 0
        
        status = "healthy"
        if not database_connected:
            status = "unhealthy"
        elif not monitoring_active:
            status = "degraded"
        
        return HealthCheckResponse(
            status=status,
            timestamp=format_timestamp(datetime.now()),
            database_connected=database_connected,
            monitoring_active=monitoring_active,
            total_sources=system_metrics.total_sources,
            active_sources=system_metrics.active_sources
        )
        
    except Exception as e:
        return HealthCheckResponse(
            status="unhealthy",
            timestamp=format_timestamp(datetime.now()),
            database_connected=False,
            monitoring_active=False,
            total_sources=0,
            active_sources=0
        )

@router.get("/metrics")
async def get_system_metrics():
    """Get detailed system metrics"""
    try:
        monitoring_db = get_monitoring_db()
        system_metrics = monitoring_db.get_system_metrics()
        source_metrics = monitoring_db.get_source_metrics()
        
        # Calculate additional metrics
        active_sources = len([s for s in source_metrics if s.status == 'active'])
        error_sources = len([s for s in source_metrics if s.recent_errors_24h > 0])
        successful_sources = len([s for s in source_metrics if s.recent_articles_24h > 0])
        
        return {
            "system": {
                "total_sources": system_metrics.total_sources,
                "active_sources": active_sources,
                "error_sources": error_sources,
                "successful_sources": successful_sources,
                "total_articles": system_metrics.total_articles,
                "articles_24h": system_metrics.articles_24h,
                "articles_7d": system_metrics.articles_7d,
                "database_size_mb": system_metrics.database_size_mb,
                "avg_parse_time_ms": system_metrics.avg_article_parse_time_ms
            },
            "sources": {
                "by_status": {},
                "by_type": {},
                "performance": {
                    "avg_success_rate": sum(s.success_rate for s in source_metrics) / len(source_metrics) if source_metrics else 0,
                    "avg_errors_24h": sum(s.recent_errors_24h for s in source_metrics) / len(source_metrics) if source_metrics else 0
                }
            },
            "timestamp": system_metrics.last_update.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/parsing/active")
async def get_active_parsing():
    """Get information about currently active parsing operations"""
    try:
        from ..parsing_tracker import get_parsing_tracker
        tracker = get_parsing_tracker()
        
        if not tracker:
            return {
                "active": False,
                "message": "No active parsing operations"
            }
        
        # Get current progress
        progress = tracker.get_progress()
        
        return {
            "active": True,
            "progress": progress,
            "timestamp": format_timestamp(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Error getting active parsing info: {str(e)}")
        return {
            "active": False,
            "error": str(e),
            "timestamp": format_timestamp(datetime.now())
        }

# Process control endpoints
@router.post("/control/start")
async def start_parser(
    days_back: int = Query(7, ge=1, le=30, description="Number of days to go back for crawling"),
    last_parsed: Optional[str] = Query(None, description="Last parsed timestamp to resume from")
):
    """Start the AI News Parser process"""
    try:
        process_manager = get_process_manager()
        
        if not process_manager.can_start():
            current_status = process_manager.get_status()
            return ProcessControlResponse(
                success=False,
                message=f"Cannot start parser. Current status: {current_status.value}",
                status=current_status.value,
                timestamp=format_timestamp(datetime.now())
            )
        
        # Prepare start parameters
        start_params = {"days_back": days_back}
        if last_parsed:
            from .core import validate_timestamp
            if not validate_timestamp(last_parsed):
                raise HTTPException(status_code=400, detail="Invalid last_parsed timestamp format")
            start_params["last_parsed"] = last_parsed
        
        # Start the process
        result = process_manager.start(**start_params)
        
        return ProcessControlResponse(
            success=result.success,
            message=result.message,
            status=process_manager.get_status().value,
            timestamp=format_timestamp(datetime.now())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting parser: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start parser: {str(e)}")

@router.post("/control/pause")
async def pause_parser():
    """Pause the running parser process"""
    try:
        process_manager = get_process_manager()
        
        if not process_manager.can_pause():
            current_status = process_manager.get_status()
            return ProcessControlResponse(
                success=False,
                message=f"Cannot pause parser. Current status: {current_status.value}",
                status=current_status.value,
                timestamp=format_timestamp(datetime.now())
            )
        
        result = process_manager.pause()
        
        return ProcessControlResponse(
            success=result.success,
            message=result.message,
            status=process_manager.get_status().value,
            timestamp=format_timestamp(datetime.now())
        )
        
    except Exception as e:
        logger.error(f"Error pausing parser: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to pause parser: {str(e)}")

@router.post("/control/resume")
async def resume_parser():
    """Resume the paused parser process"""
    try:
        process_manager = get_process_manager()
        
        if not process_manager.can_resume():
            current_status = process_manager.get_status()
            return ProcessControlResponse(
                success=False,
                message=f"Cannot resume parser. Current status: {current_status.value}",
                status=current_status.value,
                timestamp=format_timestamp(datetime.now())
            )
        
        result = process_manager.resume()
        
        return ProcessControlResponse(
            success=result.success,
            message=result.message,
            status=process_manager.get_status().value,
            timestamp=format_timestamp(datetime.now())
        )
        
    except Exception as e:
        logger.error(f"Error resuming parser: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to resume parser: {str(e)}")

@router.post("/control/stop")
async def stop_parser(
    timeout: int = Query(30, ge=5, le=300, description="Timeout in seconds for graceful shutdown")
):
    """Stop the parser process gracefully"""
    try:
        process_manager = get_process_manager()
        
        if not process_manager.can_stop():
            current_status = process_manager.get_status()
            return ProcessControlResponse(
                success=False,
                message=f"Cannot stop parser. Current status: {current_status.value}",
                status=current_status.value,
                timestamp=format_timestamp(datetime.now())
            )
        
        result = process_manager.stop(timeout=timeout)
        
        return ProcessControlResponse(
            success=result.success,
            message=result.message,
            status=process_manager.get_status().value,
            timestamp=format_timestamp(datetime.now())
        )
        
    except Exception as e:
        logger.error(f"Error stopping parser: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop parser: {str(e)}")

@router.post("/control/emergency-stop")
async def emergency_stop_parser():
    """Emergency stop - forcefully kill all parser processes"""
    try:
        process_manager = get_process_manager()
        
        result = process_manager.emergency_stop()
        
        return ProcessControlResponse(
            success=result.success,
            message=result.message,
            status=process_manager.get_status().value,
            timestamp=format_timestamp(datetime.now())
        )
        
    except Exception as e:
        logger.error(f"Error during emergency stop: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to emergency stop: {str(e)}")

@router.get("/control/status")
async def get_parser_status():
    """Get current parser process status and progress"""
    try:
        process_manager = get_process_manager()
        status_info = get_process_status()
        
        # Get parsing progress if available
        parsing_progress = None
        try:
            from ..parsing_tracker import get_parsing_tracker
            tracker = get_parsing_tracker()
            if tracker:
                parsing_progress = tracker.get_progress()
        except Exception as e:
            logger.error(f"Error getting parsing progress: {str(e)}")
        
        return {
            "process": status_info,
            "parsing_progress": parsing_progress,
            "timestamp": format_timestamp(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Error getting parser status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get parser status: {str(e)}")

@router.post("/control/cleanup-memory")
async def cleanup_parser_memory():
    """Force memory cleanup for parser processes"""
    try:
        from .core import cleanup_memory
        result = cleanup_memory()
        
        return ProcessControlResponse(
            success=result["success"],
            message=result["message"],
            timestamp=result["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Error during memory cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup memory: {str(e)}")

@router.post("/control/update-progress")
async def update_parser_progress(
    current_source: Optional[str] = None,
    total_sources: Optional[int] = None,
    processed_sources: Optional[int] = None,
    total_articles: Optional[int] = None,
    processed_articles: Optional[int] = None,
    current_phase: Optional[str] = None
):
    """Update parser progress information"""
    try:
        from ..parsing_tracker import get_parsing_tracker
        tracker = get_parsing_tracker()
        
        if not tracker:
            return {
                "success": False,
                "message": "Parsing tracker not available"
            }
        
        # Update progress
        progress_data = {}
        if current_source:
            progress_data["current_source"] = current_source
        if total_sources:
            progress_data["total_sources"] = total_sources
        if processed_sources:
            progress_data["processed_sources"] = processed_sources
        if total_articles:
            progress_data["total_articles"] = total_articles
        if processed_articles:
            progress_data["processed_articles"] = processed_articles
        if current_phase:
            progress_data["current_phase"] = current_phase
        
        tracker.update_progress(**progress_data)
        
        return {
            "success": True,
            "message": "Progress updated successfully",
            "updated_fields": list(progress_data.keys()),
            "timestamp": format_timestamp(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Error updating progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update progress: {str(e)}")

# RSS Discovery endpoints
@router.get("/rss/sources")
async def get_rss_sources():
    """Get RSS sources summary"""
    try:
        return get_rss_sources_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))