"""
Extract System API endpoints for monitoring dashboard
"""
import asyncio
import subprocess
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_logging import get_logger, handle_websocket_error, handle_database_error, handle_api_error, handle_process_error
# Import Database from core directory
from core.database import Database

logger = get_logger('monitoring.extract_api')

# Create router
router = APIRouter(prefix="/api/extract", tags=["extract"])

# Process management
extract_processes = {
    'rss': None,
    'parse': None, 
    'media': None
}

# WebSocket connections for log streaming
log_connections = set()

class ExtractProcessManager:
    """Manages Extract system processes"""
    
    def __init__(self):
        self.processes = extract_processes
        self.main_dir = Path(__file__).parent.parent  # ainews-clean directory
        # Use virtual environment Python if available
        venv_python = self.main_dir / "venv" / "bin" / "python"
        self.python_cmd = str(venv_python) if venv_python.exists() else sys.executable
        
    async def start_rss(self) -> Dict[str, Any]:
        """Start RSS Discovery phase"""
        if self.processes['rss'] and self.processes['rss'].poll() is None:
            return {"status": "already_running", "pid": self.processes['rss'].pid}
            
        try:
            cmd = [self.python_cmd, str(self.main_dir / "core" / "main.py"), "--rss-discover"]
            self.processes['rss'] = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(self.main_dir)
            )
            
            # Start log streaming
            asyncio.create_task(self._stream_process_logs('rss', self.processes['rss']))
            
            logger.info(f"Started RSS Discovery process with PID: {self.processes['rss'].pid}")
            return {"status": "started", "pid": self.processes['rss'].pid}
            
        except Exception as e:
            handle_process_error(e, 'rss-discover', {'phase': 'rss', 'action': 'start'})
            raise HTTPException(status_code=500, detail=str(e))
    
    async def stop_rss(self) -> Dict[str, Any]:
        """Stop RSS Discovery phase"""
        if not self.processes['rss'] or self.processes['rss'].poll() is not None:
            return {"status": "not_running"}
            
        try:
            self.processes['rss'].terminate()
            self.processes['rss'].wait(timeout=5)
            logger.info("Stopped RSS Discovery process")
            return {"status": "stopped"}
        except subprocess.TimeoutExpired:
            self.processes['rss'].kill()
            logger.warning("Force killed RSS Discovery process")
            return {"status": "killed"}
        finally:
            self.processes['rss'] = None
    
    async def start_parse(self) -> Dict[str, Any]:
        """Start Extract API parsing phase"""
        if self.processes['parse'] and self.processes['parse'].poll() is None:
            return {"status": "already_running", "pid": self.processes['parse'].pid}
            
        try:
            cmd = [self.python_cmd, str(self.main_dir / "core" / "main.py"), "--parse-pending"]
            self.processes['parse'] = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(self.main_dir)
            )
            
            # Start log streaming
            asyncio.create_task(self._stream_process_logs('parse', self.processes['parse']))
            
            logger.info(f"Started Extract API parsing with PID: {self.processes['parse'].pid}")
            # Debug logging
            logger.debug(f"Parse process stored in self.processes: {self.processes['parse']}")
            logger.debug(f"Parse process PID: {self.processes['parse'].pid}")
            return {"status": "started", "pid": self.processes['parse'].pid}
            
        except Exception as e:
            handle_process_error(e, 'parse-pending', {'phase': 'parse', 'action': 'start'})
            raise HTTPException(status_code=500, detail=str(e))
    
    async def stop_parse(self) -> Dict[str, Any]:
        """Stop Extract API parsing phase"""
        if not self.processes['parse']:
            logger.warning("Parse process not found in processes dict")
            return {"status": "not_running"}
            
        if self.processes['parse'].poll() is not None:
            logger.warning(f"Parse process already finished with return code: {self.processes['parse'].poll()}")
            return {"status": "not_running"}
            
        try:
            pid = self.processes['parse'].pid
            logger.info(f"Attempting to stop Parse process with PID: {pid}")
            self.processes['parse'].terminate()
            self.processes['parse'].wait(timeout=5)
            logger.info(f"Successfully stopped Parse process (PID: {pid})")
            return {"status": "stopped"}
        except subprocess.TimeoutExpired:
            logger.warning(f"Parse process did not stop gracefully, force killing PID: {self.processes['parse'].pid}")
            self.processes['parse'].kill()
            self.processes['parse'].wait()  # Wait for kill to complete
            logger.warning("Force killed parsing process")
            return {"status": "killed"}
        finally:
            self.processes['parse'] = None
    
    async def start_media(self) -> Dict[str, Any]:
        """Start media download phase"""
        if self.processes['media'] and self.processes['media'].poll() is None:
            return {"status": "already_running", "pid": self.processes['media'].pid}
            
        try:
            cmd = [self.python_cmd, str(self.main_dir / "core" / "main.py"), "--media-only"]
            self.processes['media'] = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(self.main_dir)
            )
            
            # Start log streaming
            asyncio.create_task(self._stream_process_logs('media', self.processes['media']))
            
            logger.info(f"Started media download with PID: {self.processes['media'].pid}")
            return {"status": "started", "pid": self.processes['media'].pid}
            
        except Exception as e:
            handle_process_error(e, 'media-only', {'phase': 'media', 'action': 'start'})
            raise HTTPException(status_code=500, detail=str(e))
    
    async def stop_media(self) -> Dict[str, Any]:
        """Stop media download phase"""
        if not self.processes['media'] or self.processes['media'].poll() is not None:
            return {"status": "not_running"}
            
        try:
            self.processes['media'].terminate()
            self.processes['media'].wait(timeout=5)
            logger.info("Stopped media download")
            return {"status": "stopped"}
        except subprocess.TimeoutExpired:
            self.processes['media'].kill()
            logger.warning("Force killed media download process")
            return {"status": "killed"}
        finally:
            self.processes['media'] = None
    
    async def _stream_process_logs(self, phase: str, process):
        """Stream process output to WebSocket connections"""
        try:
            # All phases use stdout streaming now
            await self._stream_stdout_logs(phase, process)
                
        except Exception as e:
            handle_process_error(e, f'{phase}-log-streaming', {'phase': phase, 'action': 'stream_logs'})
    
    async def _stream_stdout_logs(self, phase: str, process):
        """Stream logs from process stdout (all phases)"""
        while process.poll() is None:
            line = process.stdout.readline()
            if line:
                # Parse log line if it's JSON
                log_data = {
                    "phase": phase,
                    "timestamp": datetime.now().isoformat(),
                    "message": line.strip()
                }
                
                try:
                    # Try to parse as JSON log
                    json_log = json.loads(line.strip())
                    log_data["level"] = json_log.get("level", "info")
                    log_data["message"] = json_log.get("message", line.strip())
                except json.JSONDecodeError:
                    # Plain text log - this is expected behavior
                    log_data["level"] = "info"
                
                await self._send_log_to_websockets(log_data)
                
            await asyncio.sleep(0.1)
    
    
    async def _send_log_to_websockets(self, log_data):
        """Send log data to all WebSocket connections"""
        disconnected = set()
        for websocket in log_connections:
            try:
                await websocket.send_json(log_data)
            except Exception as e:
                handle_websocket_error(e, websocket, {'action': 'send_log_data', 'phase': log_data.get('phase')})
                disconnected.add(websocket)
        
        # Remove disconnected clients
        log_connections.difference_update(disconnected)

# Initialize manager
process_manager = ExtractProcessManager()

# API Endpoints
@router.post("/rss/start")
async def start_rss():
    """Start RSS Discovery phase"""
    return await process_manager.start_rss()

@router.post("/rss/stop")
async def stop_rss():
    """Stop RSS Discovery phase"""
    return await process_manager.stop_rss()

@router.post("/parse/start")
async def start_parse():
    """Start Extract API parsing phase"""
    return await process_manager.start_parse()

@router.post("/parse/stop")
async def stop_parse():
    """Stop Extract API parsing phase"""
    return await process_manager.stop_parse()

@router.post("/media/start")
async def start_media():
    """Start media download phase"""
    return await process_manager.start_media()

@router.post("/media/stop")
async def stop_media():
    """Stop media download phase"""
    return await process_manager.stop_media()

@router.get("/status")
async def get_status():
    """Get status of all Extract processes"""
    status = {}
    for phase, process in extract_processes.items():
        if process and process.poll() is None:
            status[phase] = {
                "running": True,
                "pid": process.pid
            }
        else:
            status[phase] = {
                "running": False,
                "pid": None
            }
    return status

@router.get("/last-parsed")
async def get_last_parsed():
    """Get global last_parsed timestamp from global_config table"""
    try:
        # Use Database class to get global config with absolute path
        from core.database import Database
        import os
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'ainews.db')
        db = Database(db_path)
        
        last_parsed = db.get_global_last_parsed()
        logger.info(f"Found global last_parsed from config: {last_parsed}")
        
        return {"last_parsed": last_parsed}
        
    except Exception as e:
        handle_database_error(e, 'get_global_last_parsed', {'endpoint': '/last-parsed', 'method': 'GET'})
        # Return default instead of raising exception
        return {"last_parsed": "2025-08-01T00:00:00Z"}

@router.put("/last-parsed")
async def update_last_parsed(data: Dict[str, Any]):
    """Update global last_parsed timestamp in global_config"""
    try:
        last_parsed = data.get('last_parsed')
        if not last_parsed:
            raise ValueError("last_parsed is required")
            
        # Use Database class to set global config with absolute path
        from core.database import Database
        import os
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'ainews.db')
        db = Database(db_path)
        
        # Clean and validate timestamp format
        import re
        
        # Remove any duplicate seconds (:XX:00Z -> :XXZ)
        last_parsed = re.sub(r':(\d{2}):00Z$', r':\1Z', last_parsed)
        
        # Ensure proper format
        if 'T' in last_parsed and not last_parsed.endswith('Z'):
            last_parsed = last_parsed + 'Z'
            
        # Validate datetime format
        from datetime import datetime
        try:
            datetime.fromisoformat(last_parsed.replace('Z', '+00:00'))
        except ValueError as ve:
            raise ValueError(f"Invalid timestamp format: {last_parsed}. Error: {ve}")
            
        db.set_global_last_parsed(last_parsed)
        
        logger.info(f"Updated global last_parsed to: {last_parsed}")
        return {"status": "success", "timestamp": last_parsed}
        
    except Exception as e:
        handle_database_error(e, 'set_global_last_parsed', {'endpoint': '/last-parsed', 'method': 'PUT', 'timestamp': data.get('last_parsed')})
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/articles/by-status/{status}")
async def delete_articles_by_status(status: str):
    """Delete articles and their media by content_status"""
    try:
        # Validate status
        if status not in ['pending', 'parsed', 'failed']:
            raise HTTPException(status_code=400, detail="Invalid status. Must be: pending, parsed, or failed")
        
        # Use the main database path directly
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'ainews.db')
        
        with sqlite3.connect(db_path) as conn:
            # First get list of article_ids to delete
            cursor = conn.execute("""
                SELECT article_id 
                FROM articles 
                WHERE content_status = ?
            """, (status,))
            article_ids = [row[0] for row in cursor.fetchall()]
            
            if not article_ids:
                return {"status": "success", "deleted_articles": 0, "deleted_media": 0}
            
            # Delete media files first
            media_cursor = conn.execute("""
                DELETE FROM media_files 
                WHERE article_id IN ({})
            """.format(','.join(['?' for _ in article_ids])), article_ids)
            deleted_media = media_cursor.rowcount
            
            # Delete related links
            conn.execute("""
                DELETE FROM related_links 
                WHERE article_id IN ({})
            """.format(','.join(['?' for _ in article_ids])), article_ids)
            
            # Delete articles
            article_cursor = conn.execute("""
                DELETE FROM articles 
                WHERE content_status = ?
            """, (status,))
            deleted_articles = article_cursor.rowcount
            
            conn.commit()
            
        logger.info(f"Deleted {deleted_articles} articles and {deleted_media} media files with status '{status}'")
        
        return {
            "status": "success",
            "deleted_articles": deleted_articles,
            "deleted_media": deleted_media
        }
        
    except HTTPException:
        raise
    except Exception as e:
        handle_database_error(e, 'delete_articles_by_status', {'endpoint': f'/articles/by-status/{status}', 'method': 'DELETE', 'status': status})
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/articles/stats")
async def get_articles_stats():
    """Get statistics about articles by status"""
    try:
        # Use the main database path directly
        import sqlite3
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'ainews.db')
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    content_status,
                    COUNT(*) as count,
                    MIN(created_at) as oldest,
                    MAX(created_at) as newest
                FROM articles
                GROUP BY content_status
            """)
            
            stats = {}
            for row in cursor.fetchall():
                status, count, oldest, newest = row
                stats[status or 'pending'] = {
                    'count': count,
                    'oldest': oldest,
                    'newest': newest
                }
        
        return stats
        
    except Exception as e:
        handle_database_error(e, 'get_articles_stats', {'endpoint': '/articles/stats', 'method': 'GET'})
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for log streaming
@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for real-time log streaming - connects to main log streaming system"""
    await websocket.accept()
    
    # Add to both local connections and main system log subscribers
    log_connections.add(websocket)
    
    # Import the main connection manager
    try:
        from monitoring.app import manager
        manager.log_subscribers.add(websocket)
        manager.active_connections.add(websocket)
        logger.info("WebSocket connected to unified log streaming system")
    except ImportError:
        logger.warning("Could not connect to main log streaming system")
    
    try:
        # Send initial confirmation
        await websocket.send_json({
            "type": "connection_established",
            "message": "Connected to Extract API log stream"
        })
        
        # Keep connection alive
        while True:
            # Wait for any message (ping/pong)
            try:
                message = await websocket.receive_text()
                data = json.loads(message)
                if data.get('type') == 'ping':
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
            
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        handle_websocket_error(e, websocket, {'endpoint': '/ws/logs', 'action': 'maintain_connection'})
    finally:
        # Clean up from both systems
        log_connections.discard(websocket)
        try:
            from monitoring.app import manager
            manager.log_subscribers.discard(websocket)
            manager.active_connections.discard(websocket)
        except ImportError:
            pass