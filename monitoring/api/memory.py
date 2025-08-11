"""
Memory monitoring and system resources API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import os

# Import core utilities
from .core import (
    get_monitoring_db, get_monitoring_db_connection, get_system_resources,
    cleanup_memory, format_timestamp, handle_db_error, logger
)

router = APIRouter(prefix="/api", tags=["memory"])

@router.get("/memory")
async def get_memory_info():
    """Get current memory usage information"""
    try:
        from ..memory_monitor import get_memory_monitor
        memory_monitor = get_memory_monitor()
        
        if not memory_monitor:
            return {
                "status": "not_available",
                "message": "Memory monitor not initialized",
                "timestamp": format_timestamp(datetime.now())
            }
        
        # Get current memory stats
        memory_stats = memory_monitor.get_current_memory_info()
        
        return {
            "status": "available",
            "memory": memory_stats,
            "timestamp": format_timestamp(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Error getting memory info: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": format_timestamp(datetime.now())
        }

@router.get("/memory/current")
async def get_memory_current():
    """Get current memory usage (alias for /memory for frontend compatibility)"""
    return await get_memory_info()

@router.get("/memory/statistics")
async def get_memory_statistics():
    """Get detailed memory statistics"""
    try:
        system_resources = get_system_resources()
        
        # Get additional memory info if available
        additional_info = {}
        try:
            from ..memory_monitor import get_memory_monitor
            memory_monitor = get_memory_monitor()
            if memory_monitor:
                additional_info = memory_monitor.get_statistics()
        except Exception as e:
            logger.warning(f"Could not get detailed memory stats: {str(e)}")
        
        return {
            "system_resources": system_resources,
            "additional_info": additional_info,
            "timestamp": format_timestamp(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Error getting memory statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get memory statistics: {str(e)}")

@router.get("/memory/processes")
async def get_memory_processes():
    """Get memory usage by processes"""
    try:
        import psutil
        
        processes = []
        
        # Get all processes
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'memory_info', 'cpu_percent', 'cmdline']):
            try:
                proc_info = proc.info
                
                # Filter for relevant processes (Python, Node.js, AI News related)
                cmdline = proc_info.get('cmdline', [])
                cmd_str = ' '.join(cmdline).lower() if cmdline else ''
                
                # Check if process is relevant to AI News system
                is_relevant = False
                
                if proc_info['name']:
                    name_lower = proc_info['name'].lower()
                    # Include Python, Node.js, uvicorn, monitoring processes
                    if any(keyword in name_lower for keyword in ['python', 'uvicorn', 'monitoring', 'node']):
                        is_relevant = True
                
                # Also include processes running from AI News directory or MCP servers
                if not is_relevant and cmdline:
                    if any(keyword in cmd_str for keyword in ['ainews', 'mcp-sqlite-server', 'main.py', 'single_pipeline']):
                        is_relevant = True
                
                if is_relevant:
                    
                    memory_info = proc_info.get('memory_info', {})
                    cmdline = proc_info.get('cmdline', [])
                    
                    # Determine process type based on name and command line
                    process_type = 'unknown'
                    human_name = proc_info['name']
                    name_lower = proc_info['name'].lower()
                    
                    # Python processes
                    if 'python' in name_lower:
                        process_type = 'python'
                        # Check if it's a specific type of Python process
                        if cmdline:
                            if 'uvicorn app:app' in cmd_str:
                                process_type = 'monitoring'
                                human_name = 'Monitoring Dashboard (Uvicorn)'
                            elif 'monitoring' in cmd_str or 'app.py' in cmd_str:
                                process_type = 'monitoring'
                                human_name = 'Monitoring Dashboard'
                            elif 'main.py' in cmd_str and 'single-pipeline' in cmd_str:
                                process_type = 'parser'
                                human_name = 'Single Pipeline Parser'
                            elif 'main.py' in cmd_str and 'rss-discover' in cmd_str:
                                process_type = 'parser'
                                human_name = 'RSS Discovery Parser'
                            elif 'main.py' in cmd_str or 'parser' in cmd_str:
                                process_type = 'parser'
                                human_name = 'AI News Parser'
                            elif 'single_pipeline' in cmd_str:
                                process_type = 'parser'
                                human_name = 'Single Pipeline'
                            elif 'crawl' in cmd_str:
                                process_type = 'crawler'
                                human_name = 'News Crawler'
                            elif 'rss-discover' in cmd_str:
                                process_type = 'parser'
                                human_name = 'RSS Discovery'
                            elif 'json.tool' in cmd_str:
                                human_name = 'JSON Tool (Temporary)'
                            else:
                                human_name = 'Python Process'
                    
                    # Node.js processes
                    elif 'node' in name_lower:
                        process_type = 'node'
                        if 'mcp-sqlite-server' in cmd_str:
                            process_type = 'mcp-server'
                            if 'ainews.db' in cmd_str:
                                human_name = 'MCP Server (Main DB)'
                            elif 'monitoring.db' in cmd_str:
                                human_name = 'MCP Server (Monitoring DB)'
                            else:
                                human_name = 'MCP SQLite Server'
                        elif 'claude' in cmd_str:
                            human_name = 'Claude IDE Process'
                        elif 'mcp-server-playwright' in cmd_str:
                            human_name = 'Playwright MCP Server'
                        elif 'context7-mcp-server' in cmd_str:
                            human_name = 'Context7 MCP Server'
                        elif 'shadcn-ui-mcp-server' in cmd_str:
                            human_name = 'ShadCN UI MCP Server'
                        elif 'npm' in cmd_str and 'playwright' in cmd_str:
                            human_name = 'NPM Playwright Process'
                        elif 'npm' in cmd_str:
                            human_name = 'NPM Process'
                        else:
                            human_name = 'Node.js Process'
                    
                    # Uvicorn processes
                    elif 'uvicorn' in name_lower:
                        process_type = 'monitoring'
                        human_name = 'Uvicorn Server'
                    
                    processes.append({
                        "pid": proc_info['pid'],
                        "name": proc_info['name'],
                        "human_name": human_name,
                        "process_type": process_type,
                        "memory_percent": round(proc_info.get('memory_percent', 0) or 0, 2),
                        "memory_mb": round(memory_info.rss / (1024 * 1024), 2) if hasattr(memory_info, 'rss') and memory_info.rss else 0,
                        "virtual_memory_mb": round(memory_info.vms / (1024 * 1024), 2) if hasattr(memory_info, 'vms') and memory_info.vms else 0,
                        "cpu_percent": round(proc_info.get('cpu_percent', 0) or 0, 1),
                        "cmdline": ' '.join(cmdline) if cmdline else proc_info['name']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Sort by memory usage
        processes.sort(key=lambda x: x['memory_percent'], reverse=True)
        
        return {
            "processes": processes[:20],  # Top 20 processes
            "total_processes": len(processes),
            "timestamp": format_timestamp(datetime.now())
        }
        
    except ImportError:
        return {
            "error": "psutil not available",
            "processes": [],
            "timestamp": format_timestamp(datetime.now())
        }
    except Exception as e:
        logger.error(f"Error getting process memory info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get process memory info: {str(e)}")

@router.post("/memory/cleanup")
async def perform_memory_cleanup():
    """Perform memory cleanup operations"""
    try:
        # Perform cleanup
        result = cleanup_memory()
        
        # Try to get updated memory stats after cleanup
        try:
            updated_stats = get_system_resources()
            result["memory_after_cleanup"] = updated_stats.get("memory", {})
        except Exception as e:
            logger.warning(f"Could not get updated memory stats: {str(e)}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error during memory cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Memory cleanup failed: {str(e)}")

@router.get("/memory/history")
async def get_memory_history(
    hours: int = Query(24, ge=1, le=168, description="Hours of history to retrieve")
):
    """Get memory usage history"""
    try:
        with get_monitoring_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if we have memory metrics table
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='system_resources'
            """)
            
            if not cursor.fetchone():
                return {
                    "history": [],
                    "message": "No memory history available - system_resources table not found",
                    "hours": hours,
                    "timestamp": format_timestamp(datetime.now())
                }
            
            # Get memory history
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute("""
                SELECT timestamp, memory_percent, memory_used_gb, memory_total_gb
                FROM system_resources
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            """, (cutoff_time.isoformat(),))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    "timestamp": row[0],
                    "memory_percent": row[1],
                    "memory_used_gb": row[2],
                    "memory_total_gb": row[3]
                })
            
            # Calculate stats
            if history:
                memory_percents = [h['memory_percent'] for h in history if h['memory_percent']]
                avg_memory = sum(memory_percents) / len(memory_percents) if memory_percents else 0
                max_memory = max(memory_percents) if memory_percents else 0
                min_memory = min(memory_percents) if memory_percents else 0
            else:
                avg_memory = max_memory = min_memory = 0
            
            return {
                "history": history,
                "statistics": {
                    "avg_memory_percent": round(avg_memory, 2),
                    "max_memory_percent": round(max_memory, 2),
                    "min_memory_percent": round(min_memory, 2),
                    "data_points": len(history)
                },
                "hours": hours,
                "timestamp": format_timestamp(datetime.now())
            }
            
    except Exception as e:
        logger.error(f"Error getting memory history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get memory history: {str(e)}")

@router.get("/system/resources")
async def get_system_resource_metrics():
    """Get comprehensive system resource metrics"""
    try:
        resources = get_system_resources()
        
        # Get additional system information
        try:
            import platform
            import datetime as dt
            
            system_info = {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "hostname": platform.node(),
                "uptime_hours": None  # Could add uptime if needed
            }
        except Exception as e:
            logger.warning(f"Could not get system info: {str(e)}")
            system_info = {}
        
        # Get disk usage for different paths if available
        disk_info = {}
        try:
            import psutil
            
            # Check main database disk usage
            monitoring_db = get_monitoring_db()
            if hasattr(monitoring_db, 'ainews_db_path'):
                db_disk = psutil.disk_usage(os.path.dirname(monitoring_db.ainews_db_path))
                disk_info["database_partition"] = {
                    "total_gb": round(db_disk.total / (1024**3), 2),
                    "used_gb": round(db_disk.used / (1024**3), 2),
                    "free_gb": round(db_disk.free / (1024**3), 2),
                    "percent": round((db_disk.used / db_disk.total) * 100, 2)
                }
        except Exception as e:
            logger.warning(f"Could not get detailed disk info: {str(e)}")
        
        # Get load average if on Unix
        load_avg = None
        try:
            if hasattr(os, 'getloadavg'):
                load_avg = {
                    "1_min": round(os.getloadavg()[0], 2),
                    "5_min": round(os.getloadavg()[1], 2),
                    "15_min": round(os.getloadavg()[2], 2)
                }
        except Exception:
            pass
        
        return {
            "resources": resources,
            "system_info": system_info,
            "disk_details": disk_info,
            "load_average": load_avg,
            "timestamp": format_timestamp(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Error getting system resources: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get system resources: {str(e)}")

@router.get("/logs/stats")
async def get_logs_statistics():
    """Get log file statistics and disk usage"""
    try:
        log_stats = {}
        
        # Main log file
        main_log_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'logs', 
            'ai_news_parser.log'
        )
        
        if os.path.exists(main_log_path):
            stat = os.stat(main_log_path)
            log_stats["main_log"] = {
                "path": main_log_path,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": format_timestamp(datetime.fromtimestamp(stat.st_mtime))
            }
        
        # Monitoring log file
        monitoring_log_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'monitoring.log'
        )
        
        if os.path.exists(monitoring_log_path):
            stat = os.stat(monitoring_log_path)
            log_stats["monitoring_log"] = {
                "path": monitoring_log_path,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": format_timestamp(datetime.fromtimestamp(stat.st_mtime))
            }
        
        # Check logs directory for other log files
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        other_logs = []
        
        if os.path.exists(logs_dir):
            for item in os.listdir(logs_dir):
                item_path = os.path.join(logs_dir, item)
                if os.path.isfile(item_path) and item.endswith('.log'):
                    stat = os.stat(item_path)
                    other_logs.append({
                        "filename": item,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "modified": format_timestamp(datetime.fromtimestamp(stat.st_mtime))
                    })
        
        # Calculate total log size
        total_size = sum([
            log_stats.get("main_log", {}).get("size_mb", 0),
            log_stats.get("monitoring_log", {}).get("size_mb", 0)
        ] + [log.get("size_mb", 0) for log in other_logs])
        
        return {
            "log_files": log_stats,
            "other_logs": other_logs,
            "total_size_mb": round(total_size, 2),
            "timestamp": format_timestamp(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Error getting log statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get log statistics: {str(e)}")

@router.get("/logs/files")
async def get_log_files():
    """Get list of available log files with metadata"""
    try:
        log_files = []
        
        # Check main logs directory
        main_logs_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'logs'
        )
        
        if os.path.exists(main_logs_dir):
            for item in os.listdir(main_logs_dir):
                item_path = os.path.join(main_logs_dir, item)
                if os.path.isfile(item_path) and (item.endswith('.log') or item.endswith('.txt')):
                    stat = os.stat(item_path)
                    log_files.append({
                        "filename": item,
                        "path": item_path,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "size_bytes": stat.st_size,
                        "modified": format_timestamp(datetime.fromtimestamp(stat.st_mtime)),
                        "readable": os.access(item_path, os.R_OK),
                        "location": "main_logs"
                    })
        
        # Check monitoring logs directory
        monitoring_logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        
        if os.path.exists(monitoring_logs_dir):
            for item in os.listdir(monitoring_logs_dir):
                item_path = os.path.join(monitoring_logs_dir, item)
                if os.path.isfile(item_path) and item.endswith('.log'):
                    stat = os.stat(item_path)
                    log_files.append({
                        "filename": item,
                        "path": item_path,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "size_bytes": stat.st_size,
                        "modified": format_timestamp(datetime.fromtimestamp(stat.st_mtime)),
                        "readable": os.access(item_path, os.R_OK),
                        "location": "monitoring_logs"
                    })
        
        # Sort by modification time (newest first)
        log_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return {
            "log_files": log_files,
            "total_files": len(log_files),
            "total_size_mb": round(sum(f['size_mb'] for f in log_files), 2),
            "timestamp": format_timestamp(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Error getting log files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get log files: {str(e)}")

@router.delete("/logs/{filename}")
async def delete_log_file(filename: str):
    """Delete a specific log file"""
    try:
        # Security check - only allow deletion of .log files
        if not filename.endswith('.log'):
            raise HTTPException(status_code=400, detail="Can only delete .log files")
        
        # Check if file exists in monitoring logs directory
        monitoring_logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        file_path = os.path.join(monitoring_logs_dir, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Log file {filename} not found")
        
        # Get file size before deletion
        file_size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)
        
        # Delete the file
        os.remove(file_path)
        
        return {
            "success": True,
            "message": f"Log file {filename} deleted successfully",
            "filename": filename,
            "size_freed_mb": file_size_mb,
            "timestamp": format_timestamp(datetime.now())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting log file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete log file: {str(e)}")

@router.post("/logs/cleanup")
async def cleanup_old_logs(
    days_older_than: int = Query(7, ge=1, le=365, description="Delete logs older than N days")
):
    """Clean up old log files"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days_older_than)
        deleted_files = []
        total_size_freed = 0
        
        # Check monitoring logs directory
        monitoring_logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        
        if os.path.exists(monitoring_logs_dir):
            for item in os.listdir(monitoring_logs_dir):
                if item.endswith('.log'):
                    item_path = os.path.join(monitoring_logs_dir, item)
                    
                    if os.path.isfile(item_path):
                        stat = os.stat(item_path)
                        file_modified = datetime.fromtimestamp(stat.st_mtime)
                        
                        if file_modified < cutoff_date:
                            file_size_mb = round(stat.st_size / (1024 * 1024), 2)
                            os.remove(item_path)
                            
                            deleted_files.append({
                                "filename": item,
                                "size_mb": file_size_mb,
                                "modified": format_timestamp(file_modified)
                            })
                            total_size_freed += file_size_mb
        
        return {
            "success": True,
            "message": f"Cleaned up {len(deleted_files)} old log files",
            "days_older_than": days_older_than,
            "deleted_files": deleted_files,
            "total_size_freed_mb": round(total_size_freed, 2),
            "timestamp": format_timestamp(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup logs: {str(e)}")