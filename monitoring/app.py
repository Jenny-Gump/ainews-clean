"""
Main monitoring application
"""
import os
import sys
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn
import asyncio
import json
import time
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime

# Custom JSON encoder for datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, 'value'):  # For enum values
            return obj.value
        return super().default(obj)

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import refactored modular API
from monitoring.api import (
    router as monitoring_router,
    articles_router, 
    memory_router,
    pipeline_router, 
    rss_router, 
    profiling_router, 
    logs_router,
    set_monitoring_db
)
from monitoring.api_rss_endpoints import router as extract_router
# NOTE: extract_api.py was removed during MVP simplification - not needed for core functionality
# from monitoring.extract_api import router as extract_router
from monitoring.database import MonitoringDatabase
from monitoring.collectors import SystemMetricsCollector, SourceHealthCollector, SystemResourceCollector
# log_processor removed - Real-time Logs and Errors functionality deleted
from monitoring.parsing_tracker import ParsingProgressTracker
from monitoring.automation import AutomationEngine
from monitoring.memory_monitor import initialize_memory_monitor, get_memory_monitor
# log_reader removed - Real-time Logs functionality deleted
from monitoring.process_manager import get_process_manager, ProcessStatus
from monitoring.rss_monitor import RSSMonitor, RSSIntegration


# Global collectors and processors
system_collector = None
health_collector = None
system_resource_collector = None
# Removed: log_processor, error_context_collector, log_reader, log_stream_task
# These were part of Real-time Logs and Errors functionality
parsing_progress_tracker = None
automation_engine = None
broadcast_task = None
memory_monitor = None
process_manager = None
rss_monitor = None
rss_integration = None
rss_monitor_task = None


class ConnectionManager:
    """OPTIMIZED WebSocket connection manager with memory efficiency"""
    
    def __init__(self):
        # FIXED: Use set for O(1) operations instead of list O(n)
        self.active_connections: set = set()
        
        # log_subscribers removed - Real-time Logs functionality deleted
        
        # FIXED: Cache serialized messages to avoid repeated JSON encoding
        self._message_cache = {}
        self._last_broadcast_data = None
        self._last_broadcast_time = 0
        self._cache_timeout = 2  # Cache messages for 2 seconds
        
        # Connection tracking
        self._connection_count = 0
        self._max_connections = 100  # Limit concurrent connections
    
    async def connect(self, websocket: WebSocket):
        # FIXED: Limit maximum connections
        if len(self.active_connections) >= self._max_connections:
            await websocket.close(code=1008, reason="Too many connections")
            return False
        
        await websocket.accept()
        self.active_connections.add(websocket)
        self._connection_count += 1
        return True
    
    def disconnect(self, websocket: WebSocket):
        # FIXED: O(1) removal with set.discard
        self.active_connections.discard(websocket)
    
    async def broadcast(self, data: dict):
        """OPTIMIZED broadcast with message caching and batch operations"""
        if not self.active_connections:
            return
        
        # FIXED: Cache JSON serialization to avoid repeated encoding
        current_time = time.time()
        data_hash = hash(str(sorted(data.items())))
        
        # Use cached message if data hasn't changed and cache is fresh
        if (self._last_broadcast_data == data_hash and 
            current_time - self._last_broadcast_time < self._cache_timeout and
            'cached_message' in self._message_cache):
            message = self._message_cache['cached_message']
        else:
            # Serialize once and cache
            message = json.dumps(data, cls=DateTimeEncoder)
            self._message_cache['cached_message'] = message
            self._last_broadcast_data = data_hash
            self._last_broadcast_time = current_time
        
        # FIXED: Batch disconnection handling
        disconnected = set()
        
        # Send to all connections concurrently
        tasks = []
        for connection in self.active_connections:
            tasks.append(self._send_to_connection(connection, message, disconnected))
        
        # Wait for all sends to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # FIXED: Batch remove disconnected clients (efficient with set)
        self.active_connections -= disconnected
    
    async def _send_to_connection(self, connection: WebSocket, message: str, disconnected: set):
        """Send message to a single connection"""
        try:
            await connection.send_text(message)
        except:
            disconnected.add(connection)
    
    def get_connection_count(self) -> int:
        """Get current number of active connections"""
        return len(self.active_connections)
    
    def cleanup_cache(self):
        """Clean up message cache - called by memory monitor"""
        try:
            cache_size_before = len(self._message_cache)
            self._message_cache.clear()
            print(f"ConnectionManager cache cleared: {cache_size_before} cached messages")
        except Exception as e:
            print(f"Error clearing ConnectionManager cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection manager statistics"""
        return {
            'active_connections': len(self.active_connections),
            'total_connections_created': self._connection_count,
            'cached_messages': len(self._message_cache),
            'last_broadcast_time': self._last_broadcast_time,
            'max_connections': self._max_connections,
            # 'log_subscribers': removed - Real-time Logs functionality deleted
        }
    
    # send_log_to_subscribers removed - Real-time Logs functionality deleted


# WebSocket connection manager
manager = ConnectionManager()


async def broadcast_system_metrics():
    """Background task to broadcast system metrics every 30 seconds"""
    while True:
        try:
            if manager.active_connections and system_collector and health_collector:
                # Only send essential metrics, not parsing progress
                # Parsing progress is sent separately via callbacks
                data = {
                    "type": "metrics_update",
                    "timestamp": int(asyncio.get_event_loop().time()),
                    "system_metrics": await get_current_system_metrics(),
                    "memory_info": await get_current_memory_info(),
                    "process_status": await get_current_process_status(),
                }
                
                # Minimal additional data - client will request specific data as needed
                
                await manager.broadcast(data)
            
            await asyncio.sleep(120)  # Dashboard updates every 2 minutes
            
        except Exception as e:
            print(f"Error in broadcast_system_metrics: {e}")
            await asyncio.sleep(120)


# stream_logs_to_subscribers removed - Real-time Logs functionality deleted


async def broadcast_process_update(update_data: Dict):
    """Broadcast process-specific updates to WebSocket clients"""
    try:
        if manager.active_connections:
            await manager.broadcast(update_data)
    except Exception as e:
        print(f"Error broadcasting process update: {e}")


async def get_current_system_metrics():
    """Get current system metrics from collector"""
    try:
        if system_collector and hasattr(system_collector, 'db'):
            # Get system metrics from database
            metrics = system_collector.db.get_system_metrics()
            # Convert to dict for JSON serialization
            if hasattr(metrics, '__dict__'):
                return metrics.__dict__
            return vars(metrics) if metrics else {}
    except Exception as e:
        print(f"Error getting system metrics: {e}")
    return {}


async def get_current_health_scores():
    """Get current health scores from collector"""
    try:
        if health_collector and hasattr(health_collector, 'db'):
            # Get source metrics with health scores from database
            source_metrics = health_collector.db.get_source_metrics_detailed()
            # Extract health scores 
            health_scores = {}
            for source in source_metrics:
                health_scores[source.get('source_id', 'unknown')] = {
                    'health_score': source.get('health_score', 0),
                    'status': source.get('status', 'unknown'),
                    'last_updated': source.get('last_updated', None)
                }
            return health_scores
    except Exception as e:
        print(f"Error getting health scores: {e}")
    return {}


async def get_current_rss_metrics():
    """Get current RSS metrics"""
    try:
        if rss_monitor:
            summary = rss_monitor.get_rss_summary()
            details = rss_monitor.get_feed_details()
            return {
                'summary': summary,
                'feeds': details
            }
    except Exception as e:
        print(f"Error getting RSS metrics: {e}")
    return {'summary': {}, 'feeds': []}




async def get_current_memory_info():
    """Get current memory information from memory monitor"""
    try:
        memory_monitor = get_memory_monitor()
        if memory_monitor:
            return memory_monitor.get_current_memory_info()
    except Exception as e:
        print(f"Error getting memory info: {e}")
    return {}


async def get_current_process_status():
    """Get current process status from process manager"""
    try:
        global process_manager
        if process_manager:
            status = process_manager.get_status()
            return {
                "parser_status": status['status'],
                "parser_pid": status['pid'],
                "parser_uptime": status['uptime_seconds'],
                "current_source": status['current_source'],
                "progress": status['progress'],
                "is_healthy": process_manager.is_process_healthy(),
                "memory_info": status['memory_info']
            }
    except Exception as e:
        print(f"Error getting process status: {e}")
    return {
        "parser_status": "unknown",
        "parser_pid": None,
        "parser_uptime": None,
        "current_source": None,
        "progress": {"total_sources": 0, "processed_sources": 0, "total_articles": 0, "progress_percent": 0},
        "is_healthy": False,
        "memory_info": None
    }


async def get_current_system_resources():
    """Get current system resource metrics"""
    try:
        global system_resource_collector
        if system_resource_collector:
            # Get rolling averages
            averages = system_resource_collector.get_rolling_averages(minutes=5)
            
            # Get latest metrics from database
            with sqlite3.connect(system_resource_collector.monitoring_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT cpu_percent, memory_percent, disk_percent, 
                           process_count, ainews_process_count, network_connections
                    FROM system_metrics
                    ORDER BY timestamp DESC
                    LIMIT 1
                """)
                row = cursor.fetchone()
                
                if row:
                    return {
                        "current": {
                            "cpu_percent": row[0],
                            "memory_percent": row[1],
                            "disk_percent": row[2],
                            "process_count": row[3],
                            "ainews_process_count": row[4],
                            "network_connections": row[5]
                        },
                        "averages_5min": averages
                    }
    except Exception as e:
        print(f"Error getting system resources: {e}")
    
    return {
        "current": {},
        "averages_5min": {}
    }


async def get_current_parsing_progress():
    """Get current parsing progress"""
    try:
        global parsing_progress_tracker
        if parsing_progress_tracker:
            state = parsing_progress_tracker.get_current_state()
            stats = parsing_progress_tracker.get_source_stats()
            return {
                "state": state,
                "source_stats": stats
            }
    except Exception as e:
        print(f"Error getting parsing progress: {e}")
    
    return {
        "state": {
            "status": "idle",
            "progress_percent": 0
        },
        "source_stats": {}
    }


# get_current_error_summary removed - Errors functionality deleted


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global system_collector, health_collector, system_resource_collector, parsing_progress_tracker, automation_engine, broadcast_task, memory_monitor, process_manager, rss_monitor, rss_integration, rss_monitor_task
    
    try:
        # Ensure data directory exists - use absolute path to project data directory
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        
        # Initialize database with proper path
        db_path = data_dir / "monitoring.db"
        monitoring_db = MonitoringDatabase(str(db_path))
        
        # Set monitoring database in API module
        from monitoring.api import set_monitoring_db
        set_monitoring_db(monitoring_db)
        
        # Set monitoring database in RSS endpoints module
        from monitoring.api_rss_endpoints import set_monitoring_db as set_rss_db
        set_rss_db(monitoring_db)
        
        # Set monitoring database in pipeline API module
        from monitoring.api.pipeline import set_monitoring_db as set_pipeline_db
        set_pipeline_db(monitoring_db)
        
        # Removed: error_context_collector and log_processor initialization
        # These were part of Real-time Logs and Errors functionality
        
        # Initialize parsing progress tracker
        parsing_progress_tracker = ParsingProgressTracker(monitoring_db)
        parsing_progress_tracker.start()
        
        # Initialize automation engine
        automation_engine = AutomationEngine(monitoring_db, None)
        await automation_engine.start()
        
        # Start collectors with log processor
        system_collector = SystemMetricsCollector(monitoring_db)
        health_collector = SourceHealthCollector(monitoring_db)
        system_resource_collector = SystemResourceCollector(monitoring_db, interval_seconds=30)
        
        system_collector.start()
        health_collector.start()
        system_resource_collector.start()
        
        # Initialize and start memory monitor with 10GB limit
        memory_monitor = initialize_memory_monitor(monitoring_db, max_memory_gb=10.0)
        
        # Register cleanup callbacks for memory monitor
        # (LogProcessor cleanup removed as it was part of deleted Real-time Logs functionality)
        memory_monitor.register_cleanup_callback(
            lambda: system_collector._clear_caches() if system_collector and hasattr(system_collector, '_clear_caches') else None,
            "SystemCollector cache cleanup"
        )
        memory_monitor.register_cleanup_callback(
            lambda: health_collector._clear_caches() if health_collector and hasattr(health_collector, '_clear_caches') else None,
            "HealthCollector cache cleanup"
        )
        memory_monitor.register_cleanup_callback(
            lambda: manager.cleanup_cache() if manager else None,
            "ConnectionManager cache cleanup"
        )
        memory_monitor.register_cleanup_callback(
            lambda: monitoring_db.clear_cache() if monitoring_db else None,
            "Database query cache cleanup"
        )
        
        # Register emergency callbacks
        memory_monitor.register_emergency_callback(
            lambda: print("EMERGENCY: Forcing garbage collection"),
            "Emergency GC"
        )
        
        # Start memory monitor
        memory_monitor.start()
        
        # Removed: log_reader initialization - Real-time Logs functionality deleted
        
        # Initialize RSS monitor and integration
        rss_monitor = RSSMonitor(monitoring_db)
        rss_integration = RSSIntegration(monitoring_db)
        
        # Start RSS monitoring task
        rss_monitor_task = asyncio.create_task(rss_monitor.start_monitoring())
        
        # Initialize process manager
        process_manager = get_process_manager()
        
        # Setup automatic restart with max 3 attempts
        process_manager.setup_automatic_restart(max_attempts=3, restart_delay=60)
        
        # Register process manager callbacks for WebSocket broadcasting
        def on_status_change(status: ProcessStatus, details: Dict):
            """Callback for process status changes"""
            asyncio.create_task(broadcast_process_update({
                "type": "process_status_change",
                "status": status.value,
                "details": details,
                "timestamp": datetime.now().isoformat()
            }))
            
            # Update parsing tracker based on status
            if status == ProcessStatus.RUNNING and details.get('pid'):
                parsing_progress_tracker.start_parsing(details['pid'], details.get('days_back', 7) * 26)  # Approx sources
            elif status == ProcessStatus.PAUSED:
                parsing_progress_tracker.pause_parsing()
            elif status == ProcessStatus.STOPPED:
                parsing_progress_tracker.complete_parsing()
            elif status == ProcessStatus.ERROR:
                parsing_progress_tracker.error_parsing(details.get('error', 'Unknown error'))
        
        def on_progress_update(progress_data: Dict):
            """Callback for process progress updates"""
            asyncio.create_task(broadcast_process_update({
                "type": "process_progress_update",
                "progress": progress_data,
                "timestamp": datetime.now().isoformat()
            }))
            
            # Update parsing tracker
            if progress_data.get('current_source'):
                parsing_progress_tracker.update_source(progress_data['current_source'])
            if progress_data.get('total_sources'):
                parsing_progress_tracker._current_state['total_sources'] = progress_data['total_sources']
            if progress_data.get('total_articles'):
                parsing_progress_tracker.add_articles(
                    progress_data.get('current_source', 'unknown'),
                    progress_data['total_articles'] - parsing_progress_tracker._current_state['total_articles']
                )
        
        process_manager.register_status_callback(on_status_change)
        process_manager.register_progress_callback(on_progress_update)
        
        # Register parsing tracker callbacks for WebSocket
        def on_parsing_update(state: Dict):
            """Callback for parsing progress updates"""
            # Base parsing progress event
            asyncio.create_task(broadcast_process_update({
                "type": "parsing_progress",
                "state": state,
                "timestamp": datetime.now().isoformat()
            }))
            
            # Phase-specific events
            current_phase = state.get('current_phase')
            if current_phase and current_phase != 'idle':
                # Send phase update event
                asyncio.create_task(broadcast_process_update({
                    "type": "parsing_phase_update",
                    "phase": current_phase,
                    "phase_data": state.get('current_phase_data', {}),
                    "all_phases": state.get('phases', {}),
                    "timestamp": datetime.now().isoformat()
                }))
                
                # Send source progress event if processing a source
                if state.get('current_source'):
                    asyncio.create_task(broadcast_process_update({
                        "type": "source_progress",
                        "source_id": state['current_source'],
                        "source_name": state.get('current_source_name'),
                        "phase": current_phase,
                        "articles": state.get('total_articles', 0),
                        "speed": state.get('articles_per_minute', 0),
                        "timestamp": datetime.now().isoformat()
                    }))
                
                # Send speed metrics for charts
                if 'phases' in state:
                    speed_data = {}
                    for phase_name, phase_data in state['phases'].items():
                        if 'speed_history' in phase_data:
                            speed_data[phase_name] = phase_data['speed_history']
                    
                    if speed_data:
                        asyncio.create_task(broadcast_process_update({
                            "type": "speed_metrics",
                            "speed_history": speed_data,
                            "current_speeds": {
                                phase: data.get('speed', 0) 
                                for phase, data in state['phases'].items()
                            },
                            "timestamp": datetime.now().isoformat()
                        }))
                
                # Send pipeline state event
                if 'pipeline_data' in state:
                    asyncio.create_task(broadcast_process_update({
                        "type": "pipeline_state",
                        "pipeline": state['pipeline_data'],
                        "overall_progress": state.get('phase_progress', {}).get('overall', 0),
                        "timestamp": datetime.now().isoformat()
                    }))
        
        parsing_progress_tracker.register_update_callback(on_parsing_update)
        
        # Start WebSocket broadcast task
        broadcast_task = asyncio.create_task(broadcast_system_metrics())
        
        # Removed: log_stream_task - Real-time Logs functionality deleted
        
        print(f"Monitoring system started with database at {db_path}")
        print(f"Automation engine initialized")
        print(f"Memory monitor started with 10GB limit")
        print(f"Process manager initialized with WebSocket integration")
        print(f"WebSocket broadcast task started")
        print(f"Log reader started for real-time log streaming")
        
    except Exception as e:
        print(f"Failed to initialize monitoring system: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    yield
    
    # Cleanup
    try:
        # Cancel broadcast task if it exists
        if broadcast_task and not broadcast_task.done():
            broadcast_task.cancel()
        
        # Removed: log_stream_task cancel - Real-time Logs functionality deleted
        
        # Cancel RSS monitor task if it exists
        if rss_monitor_task and not rss_monitor_task.done():
            rss_monitor_task.cancel()
            
        if system_collector:
            system_collector.stop()
        if health_collector:
            health_collector.stop()
        if system_resource_collector:
            system_resource_collector.stop()
        # Removed: log_processor.stop() - Real-time Logs functionality deleted
        if parsing_progress_tracker:
            parsing_progress_tracker.stop()
        if automation_engine:
            await automation_engine.stop()
        if memory_monitor:
            memory_monitor.stop()
        # Removed: log_reader.stop() - Real-time Logs functionality deleted
        if rss_monitor:
            rss_monitor.stop_monitoring()
        
        print("Monitoring system stopped")
    except Exception as e:
        print(f"Error during cleanup: {e}")


# Create FastAPI app
app = FastAPI(
    title="AI News Monitoring System",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Mount media files from data directory  
media_path = Path(__file__).parent.parent / "data" / "media"
if media_path.exists():
    app.mount("/media", StaticFiles(directory=str(media_path)), name="media")

# Include monitoring API routes
app.include_router(monitoring_router)
# Include extract API routes for RSS Discovery
app.include_router(extract_router)

# Include articles API routes directly (without prefix to avoid conflicts)
app.include_router(articles_router)

# Include new Memory API routes (Day 4)
app.include_router(memory_router)
# errors_router removed - Errors functionality deleted

# Include Pipeline API routes (Single pipeline integration)
app.include_router(pipeline_router)

# Include RSS API routes
app.include_router(rss_router)

# Include Profiling API routes
app.include_router(profiling_router)

# Include Logs API routes
app.include_router(logs_router)

# Include Database API routes
from monitoring.api.core import db_router
app.include_router(db_router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time monitoring updates"""
    await manager.connect(websocket)
    
    # Track subscriptions for this client
    client_subscriptions = set()
    
    # Send initial data
    try:
        initial_data = {
            "type": "initial",
            "timestamp": int(asyncio.get_event_loop().time()),
            "system_metrics": await get_current_system_metrics(),
            "health_scores": await get_current_health_scores(),
            "process_status": await get_current_process_status()
        }
        await websocket.send_text(json.dumps(initial_data, cls=DateTimeEncoder))
        
        # Keep connection alive
        while True:
            # Wait for messages from client
            try:
                message = await websocket.receive_text()
                data = json.loads(message)
                
                # subscribe_logs removed - Real-time Logs functionality deleted
                if data.get('type') == 'ping':
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                pass
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket connection error: {e}")
    finally:
        # log_subscribers cleanup removed - Real-time Logs functionality deleted
        manager.disconnect(websocket)


# /ws/logs WebSocket endpoint removed - Real-time Logs functionality deleted


@app.get("/")
async def root():
    """Serve the monitoring dashboard"""
    return FileResponse(str(static_path / "index.html"))


@app.get("/favicon.ico")
async def favicon():
    """Serve the favicon"""
    return FileResponse(str(static_path / "favicon.ico"))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "collectors": {
            "system": system_collector is not None and system_collector._running,
            "health": health_collector is not None and health_collector._running,
            # "log_processor": removed - Real-time Logs functionality deleted
        },
        "automation": {
            "enabled": automation_engine is not None,
            "disabled_sources": len(automation_engine.disabled_sources) if automation_engine else 0
        }
    }


@app.get("/api/logs/recent")
async def get_recent_logs(limit: int = 100, level: Optional[str] = None, component: Optional[str] = None):
    """Get recent logs from the database and log files"""
    try:
        logs = []
        
        # First, get logs from error_logs table
        db_path = os.path.join(os.path.dirname(__file__), "data/monitoring.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get error logs
        cursor.execute("""
            SELECT * FROM error_logs 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
        
        for row in cursor.fetchall():
            log_entry = {
                'id': row['id'],
                'timestamp': row['timestamp'],
                'level': 'ERROR',
                'logger': row['error_type'] or 'unknown',
                'message': row['error_message'],
                'source_id': row['source_id'],
                'context': json.loads(row['context']) if row['context'] else {}
            }
            logs.append(log_entry)
        
        conn.close()
        
        # Also read recent lines from main log file
        log_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'ai_news_parser.log')
        if os.path.exists(log_file_path):
            with open(log_file_path, 'r') as f:
                # Read last N lines
                lines = f.readlines()[-limit:]
                for line in lines:
                    try:
                        log_data = json.loads(line.strip())
                        logs.append(log_data)
                    except json.JSONDecodeError:
                        pass
        
        # Sort by timestamp
        logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Apply filters
        if level:
            logs = [log for log in logs if log.get('level', '').upper() == level.upper()]
        if component:
            logs = [log for log in logs if log.get('logger', '').endswith(component)]
        
        return {"logs": logs[:limit]}
        
    except Exception as e:
        print(f"Error getting recent logs: {e}")
        return {"logs": [], "error": str(e)}


@app.get("/health/quick")
async def quick_health_check():
    """Быстрая проверка здоровья системы без обращения к БД"""
    import psutil
    import os
    from datetime import datetime
    
    # Проверяем только базовые метрики без обращения к БД
    try:
        # CPU и память
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Проверяем статус коллекторов
        collectors_ok = (
            system_collector is not None and system_collector._running and
            health_collector is not None and health_collector._running
        )
        
        # Определяем общий статус
        if cpu_percent > 90 or memory.percent > 90 or not collectors_ok:
            status = "degraded"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "collectors_running": collectors_ok
            }
        }
    
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


def create_pid_file():
    """Create PID file to prevent multiple instances"""
    pid_file = "monitoring.pid"
    current_pid = os.getpid()
    
    # Check if PID file exists
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Check if process is still running
            try:
                os.kill(old_pid, 0)  # Signal 0 just checks if process exists
                print(f"❌ Monitoring already running with PID {old_pid}")
                print("Use ./stop_monitoring.sh to stop existing instance")
                sys.exit(1)
            except (OSError, ProcessLookupError):
                # Process doesn't exist, remove stale PID file
                print(f"⚠️  Removing stale PID file (process {old_pid} not found)")
                os.remove(pid_file)
        except (ValueError, IOError):
            # Invalid PID file, remove it
            os.remove(pid_file)
    
    # Create new PID file
    with open(pid_file, 'w') as f:
        f.write(str(current_pid))
    
    print(f"✅ Monitoring started with PID {current_pid}")
    
    # Register cleanup function
    import atexit
    atexit.register(cleanup_pid_file)


def cleanup_pid_file():
    """Remove PID file on exit"""
    pid_file = "monitoring.pid"
    if os.path.exists(pid_file):
        try:
            os.remove(pid_file)
            print("🧹 PID file cleaned up")
        except OSError:
            pass


if __name__ == "__main__":
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Create PID file and check for existing instances
    create_pid_file()
    
    try:
        # Run the monitoring server
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8001,  # Different port from main visualizer
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")
    finally:
        cleanup_pid_file()