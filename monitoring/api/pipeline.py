"""
Pipeline monitoring API for single pipeline integration

This module provides simplified real-time monitoring for the single pipeline system:
- Status tracking for each phase (RSS, parsing, translation, publishing)  
- Recent operations display (last 50 operations)
- Simple error tracking (critical errors only)
- Session tracking for complete pipeline runs
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import os
import sqlite3
import subprocess
import asyncio
from pathlib import Path

from .core import get_monitoring_db

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

# Global monitoring database reference
monitoring_db = None

def set_monitoring_db(db):
    """Set the monitoring database instance"""
    global monitoring_db
    monitoring_db = db


@router.get("/status")
async def get_pipeline_status():
    """Get current single pipeline status"""
    try:
        if not monitoring_db:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Get latest pipeline session
        conn = sqlite3.connect(monitoring_db.ainews_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Sessions table removed - no current session tracking
        current_session = None
        
        # Get latest operation
        cursor.execute("""
            SELECT * FROM pipeline_operations 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        
        latest_operation = cursor.fetchone()
        
        # Get recent stats (last hour)
        one_hour_ago = datetime.now() - timedelta(hours=1)
        cursor.execute("""
            SELECT 
                phase,
                COUNT(*) as operations_count,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count
            FROM pipeline_operations 
            WHERE timestamp > ?
            GROUP BY phase
        """, (one_hour_ago.isoformat(),))
        
        phase_stats = {}
        for row in cursor.fetchall():
            phase_stats[row['phase']] = {
                'operations': row['operations_count'],
                'success': row['success_count'],
                'errors': row['error_count']
            }
        
        conn.close()
        
        # Determine if pipeline is running based on recent operations (last 5 minutes)
        recent_time = datetime.now() - timedelta(minutes=5)
        is_running = False
        if latest_operation and latest_operation['timestamp']:
            try:
                op_time = datetime.fromisoformat(latest_operation['timestamp'].replace('Z', '+00:00'))
                is_running = op_time > recent_time
            except:
                is_running = False
        
        # Build status response
        status = {
            "current_session": None,  # Session table removed
            "latest_operation": dict(latest_operation) if latest_operation else None,
            "phase_stats": phase_stats,
            "is_running": is_running,
            "timestamp": datetime.now().isoformat()
        }
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting pipeline status: {str(e)}")


@router.get("/operations")
async def get_recent_operations(limit: int = 50, phase: Optional[str] = None):
    """Get recent pipeline operations"""
    try:
        if not monitoring_db:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        conn = sqlite3.connect(monitoring_db.ainews_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query with optional phase filter
        query = "SELECT * FROM pipeline_operations"
        params = []
        
        if phase:
            query += " WHERE phase = ?"
            params.append(phase)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        operations = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "operations": operations,
            "count": len(operations),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting operations: {str(e)}")


@router.get("/errors")
async def get_pipeline_errors(hours: int = 24, limit: int = 20):
    """Get recent pipeline errors"""
    try:
        if not monitoring_db:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        conn = sqlite3.connect(monitoring_db.ainews_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get errors from specified time range
        time_threshold = datetime.now() - timedelta(hours=hours)
        cursor.execute("""
            SELECT * FROM pipeline_operations 
            WHERE status = 'error' 
            AND timestamp > ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (time_threshold.isoformat(), limit))
        
        errors = [dict(row) for row in cursor.fetchall()]
        
        # Get error summary by phase
        cursor.execute("""
            SELECT 
                phase,
                COUNT(*) as error_count
            FROM pipeline_operations 
            WHERE status = 'error' 
            AND timestamp > ?
            GROUP BY phase
        """, (time_threshold.isoformat(),))
        
        error_summary = {}
        for row in cursor.fetchall():
            error_summary[row['phase']] = row['error_count']
        
        conn.close()
        
        return {
            "errors": errors,
            "error_summary": error_summary,
            "total_errors": len(errors),
            "time_range_hours": hours,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting errors: {str(e)}")


@router.post("/session/start")
async def start_pipeline_session():
    """Start a new pipeline session - simplified after removing session tables"""
    try:
        # Session table removed - return simple confirmation
        return {
            "session_id": int(datetime.now().timestamp()),
            "status": "started", 
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting session: {str(e)}")


@router.post("/session/complete")
async def complete_pipeline_session(total_articles: int = 0):
    """Complete current pipeline session - simplified after removing session tables"""
    try:
        # Session table removed - return simple confirmation
        return {
            "status": "completed",
            "total_articles": total_articles,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing session: {str(e)}")


@router.post("/operation")
async def log_pipeline_operation(
    phase: str,
    operation: str,
    status: str,
    details: Optional[Dict[str, Any]] = None
):
    """Log a pipeline operation"""
    try:
        if not monitoring_db:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Validate parameters
        valid_phases = ['rss_discovery', 'parsing', 'media_processing', 'translation', 'publishing']
        valid_statuses = ['success', 'error', 'in_progress']
        
        if phase not in valid_phases:
            raise HTTPException(status_code=400, detail=f"Invalid phase. Must be one of: {valid_phases}")
        
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        conn = sqlite3.connect(monitoring_db.ainews_db_path)
        cursor = conn.cursor()
        
        # Session table removed - use NULL session ID
        session_id = None
        
        # Insert operation
        cursor.execute("""
            INSERT INTO pipeline_operations (phase, operation, status, details, timestamp, session_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            phase,
            operation,
            status,
            json.dumps(details) if details else None,
            datetime.now().isoformat(),
            session_id
        ))
        
        operation_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return {
            "operation_id": operation_id,
            "session_id": session_id,
            "status": "logged",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging operation: {str(e)}")


@router.get("/sessions")
async def get_pipeline_sessions(limit: int = 10):
    """Get recent pipeline sessions - simplified after removing session tables"""
    try:
        # Session table removed - return empty sessions list
        return {
            "sessions": [],
            "count": 0,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sessions: {str(e)}")


@router.get("/health")
async def pipeline_health_check():
    """Simple health check for pipeline monitoring"""
    try:
        if not monitoring_db:
            return {"status": "error", "detail": "Database not initialized"}
        
        # Test database connection
        conn = sqlite3.connect(monitoring_db.ainews_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e),
            "timestamp": datetime.now().isoformat()
        }


# Global process tracking
active_processes = {
    "single_pipeline": None,
    "rss_discovery": None
}


@router.post("/start-single")
async def start_single_pipeline():
    """Start the single pipeline process"""
    global active_processes
    
    try:
        # Check if already running
        if active_processes.get("single_pipeline") and active_processes["single_pipeline"].poll() is None:
            return {"success": False, "message": "Single pipeline is already running"}
        
        # Get the correct path to main.py
        base_path = Path(__file__).parent.parent.parent  # Go up to ainews-clean
        main_path = base_path / "core" / "main.py"
        
        if not main_path.exists():
            raise HTTPException(status_code=500, detail=f"main.py not found at {main_path}")
        
        # Start the continuous pipeline process directly
        process = subprocess.Popen(
            ["python3", str(main_path), "--continuous-pipeline"],
            cwd=str(base_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        active_processes["single_pipeline"] = process
        
        # Log the operation
        if monitoring_db:
            try:
                conn = sqlite3.connect(monitoring_db.ainews_db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO pipeline_operations (phase, operation, status, timestamp)
                    VALUES (?, ?, ?, ?)
                """, ("system", "Continuous pipeline started", "in_progress", datetime.now().isoformat()))
                conn.commit()
                conn.close()
            except:
                pass  # Don't fail if logging fails
        
        return {
            "success": True,
            "message": "Continuous pipeline started (обрабатывает ВСЕ статьи)",
            "pid": process.pid,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start single pipeline: {str(e)}")


@router.post("/start-rss")
async def start_rss_and_tracking():
    """Start the full RSS discovery + Change Tracking cycle"""
    global active_processes
    
    try:
        # Check if already running
        if active_processes.get("rss_discovery") and active_processes["rss_discovery"].poll() is None:
            return {"success": False, "message": "RSS + Change Tracking is already running"}
        
        # Get the correct paths
        base_path = Path(__file__).parent.parent.parent  # Go up to ainews-clean
        script_path = base_path / "scripts" / "run_rss_and_tracking.sh"
        
        if not script_path.exists():
            raise HTTPException(status_code=500, detail=f"Integration script not found at {script_path}")
        
        # Make script executable
        import stat
        script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)
        
        # Start the full RSS + Change Tracking process
        process = subprocess.Popen(
            ["bash", str(script_path)],
            cwd=str(base_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        active_processes["rss_discovery"] = process
        
        # Log the operation
        if monitoring_db:
            try:
                conn = sqlite3.connect(monitoring_db.ainews_db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO pipeline_operations (phase, operation, status, timestamp)
                    VALUES (?, ?, ?, ?)
                """, ("full_cycle", "RSS + Change Tracking started", "in_progress", datetime.now().isoformat()))
                conn.commit()
                conn.close()
            except:
                pass  # Don't fail if logging fails
        
        return {
            "success": True,
            "message": "RSS + Change Tracking started",
            "pid": process.pid,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start RSS + Change Tracking: {str(e)}")


@router.post("/stop-rss")
async def stop_rss_discovery():
    """Stop the RSS discovery process and all related Python processes"""
    global active_processes
    
    try:
        stopped = []
        
        # Stop RSS discovery process (main script)
        if active_processes.get("rss_discovery") and active_processes["rss_discovery"].poll() is None:
            active_processes["rss_discovery"].terminate()
            try:
                active_processes["rss_discovery"].wait(timeout=5)
            except subprocess.TimeoutExpired:
                active_processes["rss_discovery"].kill()
            stopped.append("rss_discovery")
            active_processes["rss_discovery"] = None
        
        # Additional cleanup: Kill all related Python processes
        try:
            # Kill any hanging change-tracking processes
            subprocess.run([
                "pkill", "-f", "main.py.*change-tracking"
            ], timeout=3, capture_output=True)
            
            # Kill any hanging RSS discovery processes
            subprocess.run([
                "pkill", "-f", "main.py.*rss-discover"
            ], timeout=3, capture_output=True)
            
            # Kill any hanging run_rss_and_tracking.sh processes
            subprocess.run([
                "pkill", "-f", "run_rss_and_tracking.sh"
            ], timeout=3, capture_output=True)
            
            stopped.append("related_processes")
            
        except subprocess.TimeoutExpired:
            # If pkill times out, try more aggressive approach
            try:
                subprocess.run(["killall", "-9", "python3"], timeout=2, capture_output=True)
            except:
                pass  # Don't fail if killall doesn't work
        
        # Wait a moment and verify processes are actually stopped
        import time
        time.sleep(1)
        
        # Check if any related processes are still running
        remaining_processes = []
        try:
            result = subprocess.run([
                "pgrep", "-f", "main.py.*(change-tracking|rss-discover)"
            ], capture_output=True, text=True, timeout=3)
            if result.stdout.strip():
                remaining_processes = result.stdout.strip().split('\n')
                # Force kill remaining processes
                for pid in remaining_processes:
                    if pid.strip():
                        try:
                            subprocess.run(["kill", "-9", pid.strip()], timeout=2)
                        except:
                            pass
        except:
            pass
        
        # Log the operation with details about cleanup
        if monitoring_db:
            try:
                conn = sqlite3.connect(monitoring_db.ainews_db_path)
                cursor = conn.cursor()
                details = f"Stopped processes: {', '.join(stopped)}"
                if remaining_processes:
                    details += f". Force-killed remaining PIDs: {', '.join(remaining_processes)}"
                cursor.execute("""
                    INSERT INTO pipeline_operations (phase, operation, status, details, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, ("rss_discovery", "RSS + Change Tracking stopped", "completed", details, datetime.now().isoformat()))
                conn.commit()
                conn.close()
            except:
                pass  # Don't fail if logging fails
        
        return {
            "success": True,
            "message": f"RSS + Change Tracking stopped. Cleaned up: {', '.join(stopped) if stopped else 'no active processes'}",
            "stopped": stopped,
            "cleanup_performed": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop RSS discovery: {str(e)}")


@router.post("/stop")
async def stop_pipeline():
    """Stop all pipeline processes"""
    global active_processes
    
    stopped = []
    
    try:
        # Stop single pipeline
        if active_processes.get("single_pipeline") and active_processes["single_pipeline"].poll() is None:
            active_processes["single_pipeline"].terminate()
            try:
                active_processes["single_pipeline"].wait(timeout=5)
            except subprocess.TimeoutExpired:
                active_processes["single_pipeline"].kill()
            stopped.append("single_pipeline")
            active_processes["single_pipeline"] = None
        else:
            # Fallback: Find and kill pipeline process by pattern if not tracked
            try:
                # Use pkill to find and terminate pipeline processes
                result = subprocess.run(
                    ["pkill", "-f", "main\\.py.*(continuous-pipeline|single-pipeline)"],
                    capture_output=True,
                    timeout=3
                )
                if result.returncode == 0:
                    stopped.append("pipeline_fallback")
                    # logger.info("Pipeline stopped using fallback mechanism")
            except subprocess.TimeoutExpired:
                # If pkill times out, try more aggressive approach
                subprocess.run(
                    ["pkill", "-9", "-f", "main\\.py.*(continuous-pipeline|single-pipeline)"],
                    capture_output=True,
                    timeout=2
                )
                stopped.append("pipeline_force_killed")
            except Exception as e:
                # logger.warning(f"Fallback pipeline termination failed: {e}")
                pass
        
        # Stop RSS discovery
        if active_processes.get("rss_discovery") and active_processes["rss_discovery"].poll() is None:
            active_processes["rss_discovery"].terminate()
            try:
                active_processes["rss_discovery"].wait(timeout=5)
            except subprocess.TimeoutExpired:
                active_processes["rss_discovery"].kill()
            stopped.append("rss_discovery")
            active_processes["rss_discovery"] = None
        
        # Log the operation
        if monitoring_db and stopped:
            try:
                conn = sqlite3.connect(monitoring_db.ainews_db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO pipeline_operations (phase, operation, status, timestamp)
                    VALUES (?, ?, ?, ?)
                """, ("system", f"Stopped: {', '.join(stopped)}", "success", datetime.now().isoformat()))
                conn.commit()
                conn.close()
            except:
                pass  # Don't fail if logging fails
        
        return {
            "success": True,
            "message": f"Stopped {len(stopped)} process(es)",
            "stopped": stopped,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop pipeline: {str(e)}")


@router.post("/broadcast")
async def broadcast_operation(data: dict):
    """Receive operation updates from logger and broadcast via WebSocket"""
    try:
        # Import WebSocket manager from app.py
        from monitoring.app import manager
        
        if 'operation' in data:
            operation = data['operation']
            
            # Skip technical operations that should not appear in dashboard
            operation_text = operation.get("operation", "")
            if any(tech_op in operation_text for tech_op in ["media_download", "media_batch_download", "phase_failure", "phase_skipped"]):
                return {"success": True, "skipped": True}
            
            # Map to pipeline operation format for WebSocket
            phase = "unknown"
            if "phase" in operation:
                phase = operation["phase"]
            elif "operation" in operation:
                if "rss" in operation["operation"].lower():
                    phase = "rss_discovery"
                elif "pars" in operation["operation"].lower():
                    phase = "parsing"
                elif "translat" in operation["operation"].lower():
                    phase = "translation"
                elif "publish" in operation["operation"].lower():
                    phase = "publishing"
                elif "media" in operation["operation"].lower():
                    phase = "media_processing"
            
            # Format for WebSocket broadcast
            ws_data = {
                "type": "pipeline_log",
                "timestamp": operation.get("timestamp", datetime.now().isoformat()),
                "phase": phase,
                "operation": operation.get("operation", "unknown"),
                "status": "success" if operation.get("success", True) else "error",
                "details": operation
            }
            
            # Broadcast to all connected WebSocket clients
            await manager.broadcast(ws_data)
        
        return {"success": True}
    except Exception as e:
        # Don't fail - just log and continue
        return {"success": False, "error": str(e)}


@router.get("/logs")
async def get_pipeline_logs(limit: int = 50, offset: int = 0):
    """Get pipeline logs from operations.jsonl and errors.jsonl files"""
    try:
        logs = []
        
        # Get path to logs directory
        base_path = Path(__file__).parent.parent.parent  # Go up to ainews-clean
        logs_dir = base_path / "logs"
        
        # Read operations.jsonl
        operations_file = logs_dir / "operations.jsonl"
        if operations_file.exists():
            with open(operations_file, 'r') as f:
                lines = f.readlines()
                for line in reversed(lines[-100:]):  # Get last 100 operations
                    try:
                        op = json.loads(line.strip())
                        
                        # Skip technical operations that should not appear in dashboard
                        operation_text = op.get("operation", "")
                        if any(tech_op in operation_text for tech_op in ["media_download", "media_batch_download", "phase_failure", "phase_skipped"]):
                            continue
                        
                        # Map to pipeline operation format
                        phase = "unknown"
                        if "phase" in op:
                            phase = op["phase"]
                        elif "operation" in op:
                            if "rss" in op["operation"].lower():
                                phase = "rss_discovery"
                            elif "pars" in op["operation"].lower():
                                phase = "parsing"
                            elif "translat" in op["operation"].lower():
                                phase = "translation"
                            elif "publish" in op["operation"].lower():
                                phase = "publishing"
                            elif "media" in op["operation"].lower():
                                phase = "media_processing"
                        
                        logs.append({
                            "timestamp": op.get("timestamp", datetime.now().isoformat()),
                            "phase": phase,
                            "operation": op.get("operation", "Unknown operation"),
                            "status": "success" if op.get("success", True) else "error",
                            "details": op
                        })
                    except json.JSONDecodeError:
                        continue
        
        # Read errors.jsonl
        errors_file = logs_dir / "errors.jsonl"
        if errors_file.exists():
            with open(errors_file, 'r') as f:
                lines = f.readlines()
                for line in reversed(lines[-50:]):  # Get last 50 errors
                    try:
                        error = json.loads(line.strip())
                        logs.append({
                            "timestamp": error.get("timestamp", datetime.now().isoformat()),
                            "phase": "error",
                            "operation": f"Error: {error.get('error_type', 'Unknown')}",
                            "status": "error",
                            "details": error
                        })
                    except json.JSONDecodeError:
                        continue
        
        # Sort by timestamp
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Apply pagination
        paginated_logs = logs[offset:offset + limit]
        
        return {
            "operations": paginated_logs,
            "total": len(logs),
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting logs: {str(e)}")