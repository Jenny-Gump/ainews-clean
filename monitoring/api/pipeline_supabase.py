#!/usr/bin/env python3
"""
Pipeline API endpoints for monitoring - Supabase version
Заменяет SQLite на Supabase для всех операций
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import psutil
import json
import os
import subprocess
import asyncio
import stat
from pathlib import Path

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])

# Global reference to monitoring database
monitoring_db = None

def set_monitoring_db(db):
    """Set the global monitoring database reference"""
    global monitoring_db
    monitoring_db = db

# Models
class PipelineOperation(BaseModel):
    phase: str
    operation: str
    status: str
    details: Optional[str] = None

@router.get("/status")
async def get_pipeline_status():
    """Get current single pipeline status"""
    try:
        if not monitoring_db:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Get latest operation from Supabase
        operations = monitoring_db.get_pipeline_operations(limit=1)
        latest_operation = operations[0] if operations else None
        
        # Get recent stats (simulated for now)
        phase_stats = {
            'rss_discovery': {'operations': 0, 'success': 0, 'errors': 0},
            'parsing': {'operations': 0, 'success': 0, 'errors': 0},
            'media': {'operations': 0, 'success': 0, 'errors': 0},
            'translation': {'operations': 0, 'success': 0, 'errors': 0},
            'publishing': {'operations': 0, 'success': 0, 'errors': 0}
        }
        
        # Determine if pipeline is running based on recent operations
        is_running = False
        if latest_operation:
            op_time = datetime.fromisoformat(latest_operation.get('timestamp', ''))
            if datetime.now() - op_time < timedelta(minutes=5):
                is_running = latest_operation.get('status') == 'in_progress'
        
        return {
            "status": "running" if is_running else "idle",
            "current_phase": latest_operation.get('phase') if latest_operation else None,
            "last_operation": latest_operation,
            "phase_stats": phase_stats,
            "is_running": is_running
        }
        
    except Exception as e:
        print(f"Error getting pipeline status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/operations")
async def get_pipeline_operations(
    phase: Optional[str] = None,
    limit: int = 100
):
    """Get recent pipeline operations"""
    try:
        if not monitoring_db:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Get operations from Supabase
        operations = monitoring_db.get_pipeline_operations(limit=limit)
        
        # Filter by phase if specified
        if phase:
            operations = [op for op in operations if op.get('phase') == phase]
        
        return {
            "operations": operations,
            "count": len(operations),
            "phase_filter": phase
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/errors")
async def get_pipeline_errors(
    hours: int = 24,
    limit: int = 100
):
    """Get recent pipeline errors"""
    try:
        if not monitoring_db:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # Get all operations and filter errors
        operations = monitoring_db.get_pipeline_operations(limit=limit*2)
        
        # Filter errors from last N hours
        time_threshold = datetime.now() - timedelta(hours=hours)
        errors = []
        error_summary = {}
        
        for op in operations:
            if op.get('status') == 'error':
                try:
                    op_time = datetime.fromisoformat(op.get('timestamp', ''))
                    if op_time >= time_threshold:
                        errors.append(op)
                        phase = op.get('phase', 'unknown')
                        error_summary[phase] = error_summary.get(phase, 0) + 1
                except:
                    pass
        
        return {
            "errors": errors[:limit],
            "count": len(errors),
            "error_summary": error_summary,
            "time_range_hours": hours
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/operation")
async def log_pipeline_operation(operation: PipelineOperation):
    """Log a pipeline operation (compatibility endpoint)"""
    try:
        if not monitoring_db:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        # For now, just log the operation
        print(f"Pipeline operation: {operation.phase} - {operation.operation} - {operation.status}")
        
        return {
            "success": True,
            "operation_id": 0,  # Dummy ID
            "message": "Operation logged (Supabase mode)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop-rss")
async def stop_rss_discovery():
    """Stop the RSS discovery process and all related Python processes"""
    try:
        import time  # Import time for sleep
        stopped = []
        
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
            
            stopped.append("rss_and_tracking_processes")
            
        except subprocess.TimeoutExpired:
            # If pkill times out, try more aggressive approach
            try:
                subprocess.run(["killall", "-9", "python3"], timeout=2, capture_output=True)
            except:
                pass  # Don't fail if killall doesn't work
        
        # Wait a moment and verify processes are actually stopped
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
                # Log operation to monitoring system
                details = f"Stopped processes: {', '.join(stopped)}"
                if remaining_processes:
                    details += f". Force-killed remaining PIDs: {', '.join(remaining_processes)}"
                print(f"RSS + Change Tracking stopped - {details}")
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

@router.get("/logs")
async def get_pipeline_logs(limit: int = 50):
    """Get recent pipeline logs from JSONL files"""
    try:
        # Correct path to logs directory
        base_path = Path(__file__).parent.parent.parent  # Go up to ainews-clean
        logs_dir = base_path / "logs"
        
        # Find the most recent operations log
        log_files = list(logs_dir.glob("operations*.jsonl"))
        if not log_files:
            return {"logs": [], "message": "No log files found"}
        
        # Sort by modification time
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        latest_log = log_files[0]
        
        # Read last N lines
        logs = []
        with open(latest_log, 'r') as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                try:
                    log_entry = json.loads(line)
                    # Приоритет человекочитаемому полю message
                    if 'message' in log_entry and log_entry['message'] != 'no-message':
                        # Заменяем operation на message для отображения
                        log_entry['operation'] = log_entry['message']
                    logs.append(log_entry)
                except:
                    pass
        
        # Reverse to show newest first
        logs.reverse()
        
        return {
            "logs": logs,
            "count": len(logs),
            "source": str(latest_log.name)
        }
        
    except Exception as e:
        return {"logs": [], "error": str(e)}

@router.get("/health")
async def get_pipeline_health():
    """Get pipeline health status"""
    try:
        # Check if pipeline processes are running
        running_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info.get('cmdline', []))
                if 'main.py' in cmdline and ('--single-pipeline' in cmdline or '--continuous' in cmdline):
                    running_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'command': cmdline[:100]
                    })
            except:
                pass
        
        return {
            "healthy": True,
            "database_connected": monitoring_db is not None,
            "running_processes": running_processes,
            "process_count": len(running_processes)
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "database_connected": monitoring_db is not None,
            "running_processes": [],
            "process_count": 0
        }

# Background task runners
async def run_continuous_pipeline():
    """Run continuous pipeline in background"""
    try:
        cmd = ["python3", "core/main.py", "--continuous-pipeline"]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd="/Users/skynet/Desktop/AI DEV/ainews-clean"
        )
        
        # Log operation
        if monitoring_db:
            print("Continuous pipeline started")
        
        # Wait for completion
        stdout, stderr = await process.communicate()
        
        return {
            "success": process.returncode == 0,
            "stdout": stdout.decode() if stdout else "",
            "stderr": stderr.decode() if stderr else ""
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/start/continuous")
async def start_continuous_pipeline(background_tasks: BackgroundTasks):
    """Start continuous pipeline processing"""
    try:
        # Check if already running
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info.get('cmdline', []))
                if 'main.py' in cmdline and '--continuous-pipeline' in cmdline:
                    return {
                        "success": False,
                        "message": "Continuous pipeline is already running",
                        "pid": proc.info['pid']
                    }
            except:
                pass
        
        # Start in background
        background_tasks.add_task(run_continuous_pipeline)
        
        return {
            "success": True,
            "message": "Continuous pipeline started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-single")
async def start_single_pipeline(background_tasks: BackgroundTasks):
    """Start single pipeline (actually starts continuous mode per dashboard design)"""
    try:
        # Check if already running
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info.get('cmdline', []))
                if 'main.py' in cmdline and '--continuous-pipeline' in cmdline:
                    return {
                        "success": False,
                        "message": "Pipeline is already running",
                        "pid": proc.info['pid']
                    }
            except:
                pass
        
        # Start continuous pipeline in background
        background_tasks.add_task(run_continuous_pipeline)
        
        return {
            "success": True,
            "message": "Pipeline started (continuous mode)",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-rss")
async def start_rss_and_tracking():
    """Start the full RSS discovery + Change Tracking cycle"""
    try:
        import stat
        from pathlib import Path
        
        # Check if already running
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info.get('cmdline', []))
                if 'run_rss_and_tracking.sh' in cmdline or ('main.py' in cmdline and '--rss-discover' in cmdline):
                    return {
                        "success": False,
                        "message": "RSS + Change Tracking is already running",
                        "pid": proc.info['pid']
                    }
            except:
                pass
        
        # Get the correct paths
        base_path = Path(__file__).parent.parent.parent  # Go up to ainews-clean
        script_path = base_path / "scripts" / "run_rss_and_tracking.sh"
        
        if not script_path.exists():
            raise HTTPException(status_code=500, detail=f"Integration script not found at {script_path}")
        
        # Make script executable
        script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)
        
        # Start the RSS + Change Tracking process
        process = subprocess.Popen(
            ["bash", str(script_path)],
            cwd=str(base_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Log the operation
        if monitoring_db:
            try:
                print("RSS + Change Tracking started")
            except:
                pass
        
        return {
            "success": True,
            "message": "RSS + Change Tracking started",
            "pid": process.pid,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start RSS + Change Tracking: {str(e)}")

@router.post("/stop")
async def stop_pipeline():
    """Stop all pipeline processes"""
    try:
        stopped = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info.get('cmdline', []))
                if 'main.py' in cmdline and ('--single-pipeline' in cmdline or '--continuous' in cmdline):
                    proc.terminate()
                    stopped.append(str(proc.info['pid']))
            except:
                pass
        
        # Log if processes were stopped
        if monitoring_db and stopped:
            print(f"Stopped pipeline processes: {', '.join(stopped)}")
        
        return {
            "success": True,
            "stopped_pids": stopped,
            "message": f"Stopped {len(stopped)} processes"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs-detailed")
async def get_pipeline_logs_detailed(limit: int = 50, offset: int = 0):
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
                        
                        # Skip technical operations
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

@router.post("/broadcast")
async def broadcast_operation(data: dict):
    """Receive operation updates from logger and broadcast via WebSocket"""
    try:
        # Import WebSocket manager from app.py
        from monitoring.app import manager
        
        if 'operation' in data:
            operation = data['operation']
            
            # Skip technical operations
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