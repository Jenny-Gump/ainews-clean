"""
Metric collectors for the monitoring system
"""
import psutil
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import threading
import queue

from .models import PerformanceMetrics, SourceMetrics
from .database import MonitoringDatabase
# from .log_processor import LogDataExtractor  # REMOVED - module not found


class MetricsCollector:
    """Base class for metric collectors"""
    
    def __init__(self, monitoring_db: MonitoringDatabase):
        self.monitoring_db = monitoring_db
        self._running = False
        self._thread = None
    
    def start(self):
        """Start the collector"""
        self._running = True
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._thread.start()
    
    def stop(self):
        """Stop the collector"""
        self._running = False
        if self._thread:
            self._thread.join()
    
    def _run(self):
        """Main collector loop - to be implemented by subclasses"""
        raise NotImplementedError


class SystemResourceCollector(MetricsCollector):
    """Collects system resource metrics (CPU, memory, processes)"""
    
    def __init__(self, monitoring_db: MonitoringDatabase, interval_seconds: int = 30):
        super().__init__(monitoring_db)
        self.interval_seconds = interval_seconds
        self._metrics_history = []  # For rolling averages
        self._max_history_size = 120  # 1 hour of data at 30s intervals
        
    def _run(self):
        """Collect system resource metrics every 30 seconds"""
        while self._running:
            try:
                # Collect CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Collect memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                memory_used_gb = memory.used / 1024 / 1024 / 1024
                
                # Count processes
                total_processes = len(psutil.pids())
                
                # Count AI News processes
                ainews_processes = 0
                ainews_memory_mb = 0.0
                try:
                    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cmdline']):
                        try:
                            proc_info = proc.info
                            if proc_info['cmdline']:
                                cmdline_str = ' '.join(proc_info['cmdline']).lower()
                                ai_news_keywords = ['ainews', 'ai-news', 'main.py', 'app.py', 'rss_scrape_parser', 'monitoring']
                                if any(keyword in cmdline_str for keyword in ai_news_keywords):
                                    ainews_processes += 1
                                    ainews_memory_mb += proc_info['memory_info'].rss / 1024 / 1024
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                except Exception as e:
                    print(f"Error counting AI News processes: {e}")
                
                # Get disk usage
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
                
                # Get network connections
                network_connections = len(psutil.net_connections())
                
                # Get open files (approximate)
                open_files = 0
                try:
                    for proc in psutil.process_iter(['open_files']):
                        try:
                            if proc.info['open_files']:
                                open_files += len(proc.info['open_files'])
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                except:
                    open_files = -1  # Unable to determine
                
                # Store metrics in database
                metrics = {
                    'timestamp': datetime.now(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'disk_percent': disk_percent,
                    'process_count': total_processes,
                    'ainews_process_count': ainews_processes,
                    'network_connections': network_connections,
                    'open_files': open_files
                }
                
                # Save to database
                self._save_system_metrics(metrics)
                
                # Update history for rolling averages
                self._update_metrics_history(metrics)
                
                
            except Exception as e:
                # Silently ignore the error to reduce log noise
                # Most likely cause: temporary process disappears during iteration
                pass
            
            time.sleep(self.interval_seconds)
    
    def _save_system_metrics(self, metrics: Dict[str, Any]):
        """Save system metrics to database"""
        try:
            with sqlite3.connect(self.monitoring_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO system_metrics 
                    (timestamp, cpu_percent, memory_percent, disk_percent, 
                     process_count, ainews_process_count, network_connections, open_files)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics['timestamp'],
                    metrics['cpu_percent'],
                    metrics['memory_percent'],
                    metrics['disk_percent'],
                    metrics['process_count'],
                    metrics['ainews_process_count'],
                    metrics['network_connections'],
                    metrics['open_files']
                ))
                conn.commit()
        except Exception as e:
            print(f"Error saving system metrics: {e}")
    
    def _update_metrics_history(self, metrics: Dict[str, Any]):
        """Update metrics history for rolling averages"""
        self._metrics_history.append(metrics)
        if len(self._metrics_history) > self._max_history_size:
            self._metrics_history.pop(0)
    
    def _check_resource_alerts(self, metrics: Dict[str, Any], ainews_memory_mb: float):
        """Check for resource threshold violations"""
        alerts = []
        
        # CPU alert (>80%)
        if metrics['cpu_percent'] > 80:
            alerts.append({
                'level': 'warning' if metrics['cpu_percent'] < 90 else 'critical',
                'type': 'high_cpu',
                'title': f"High CPU Usage: {metrics['cpu_percent']:.1f}%",
                'message': f"CPU usage is at {metrics['cpu_percent']:.1f}%",
                'details': {'cpu_percent': metrics['cpu_percent']}
            })
        
        # Memory alert (>7GB for AI News)
        if ainews_memory_mb > 7168:  # 7GB in MB
            alerts.append({
                'level': 'warning' if ainews_memory_mb < 8192 else 'critical',
                'type': 'high_memory',
                'title': f"High Memory Usage: {ainews_memory_mb/1024:.1f}GB",
                'message': f"AI News processes using {ainews_memory_mb/1024:.1f}GB of memory",
                'details': {'memory_mb': ainews_memory_mb}
            })
        
    
    def get_rolling_averages(self, minutes: int = 5) -> Dict[str, float]:
        """Calculate rolling averages for the specified time period"""
        if not self._metrics_history:
            return {}
        
        # Get metrics from the last N minutes
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [m for m in self._metrics_history if m['timestamp'] >= cutoff_time]
        
        if not recent_metrics:
            return {}
        
        # Calculate averages
        return {
            'avg_cpu_percent': sum(m['cpu_percent'] for m in recent_metrics) / len(recent_metrics),
            'avg_memory_percent': sum(m['memory_percent'] for m in recent_metrics) / len(recent_metrics),
            'avg_process_count': sum(m['process_count'] for m in recent_metrics) / len(recent_metrics),
            'avg_ainews_processes': sum(m['ainews_process_count'] for m in recent_metrics) / len(recent_metrics)
        }


class SystemMetricsCollector(MetricsCollector):
    """Collects system performance metrics"""
    
    def __init__(self, monitoring_db: MonitoringDatabase, interval_seconds: int = 60):
        super().__init__(monitoring_db)
        self.interval_seconds = interval_seconds
        self._parse_queue_size = 0
        self._active_connections = 0
        # FIXED: Add size limits to prevent memory leaks
        self._recent_parses = queue.Queue(maxsize=10000)  # Limit to 10K entries
        self._recent_errors = queue.Queue(maxsize=5000)   # Limit to 5K entries
        self._metrics_cache = {}
        self._cache_cleanup_counter = 0
    
    def update_parse_metrics(self, success: bool):
        """Update parsing metrics with overflow protection"""
        now = time.time()
        
        # FIXED: Handle queue overflow gracefully
        try:
            self._recent_parses.put_nowait((now, success))
        except queue.Full:
            # Remove oldest entries when queue is full
            try:
                # Remove 10% of entries to make room
                entries_to_remove = max(1, self._recent_parses.qsize() // 10)
                for _ in range(entries_to_remove):
                    if not self._recent_parses.empty():
                        self._recent_parses.get_nowait()
                    else:
                        break
                # Now try to add the new entry
                self._recent_parses.put_nowait((now, success))
            except (queue.Empty, queue.Full):
                # If still problems, just skip this entry
                pass
        
        # Track errors separately
        if not success:
            try:
                self._recent_errors.put_nowait((now, True))
            except queue.Full:
                # Remove oldest error entries
                try:
                    for _ in range(max(1, self._recent_errors.qsize() // 10)):
                        if not self._recent_errors.empty():
                            self._recent_errors.get_nowait()
                        else:
                            break
                    self._recent_errors.put_nowait((now, True))
                except (queue.Empty, queue.Full):
                    pass
        
        # Periodic cleanup of old entries (every 10 calls)
        self._cache_cleanup_counter += 1
        if self._cache_cleanup_counter >= 10:
            self._cleanup_old_entries(now)
            self._cache_cleanup_counter = 0
    
    def _cleanup_old_entries(self, current_time: float):
        """Clean up entries older than 1 minute"""
        cutoff = current_time - 60
        
        # Clean recent parses
        temp_parses = []
        while not self._recent_parses.empty():
            try:
                timestamp, success = self._recent_parses.get_nowait()
                if timestamp >= cutoff:
                    temp_parses.append((timestamp, success))
            except queue.Empty:
                break
        
        # Put back valid entries
        for entry in temp_parses:
            try:
                self._recent_parses.put_nowait(entry)
            except queue.Full:
                break
        
        # Clean recent errors
        temp_errors = []
        while not self._recent_errors.empty():
            try:
                timestamp, error = self._recent_errors.get_nowait()
                if timestamp >= cutoff:
                    temp_errors.append((timestamp, error))
            except queue.Empty:
                break
        
        # Put back valid entries
        for entry in temp_errors:
            try:
                self._recent_errors.put_nowait(entry)
            except queue.Full:
                break
    
    def set_queue_size(self, size: int):
        """Update parse queue size"""
        self._parse_queue_size = size
    
    def set_active_connections(self, count: int):
        """Update active connections count"""
        self._active_connections = count
    
    def _run(self):
        """Collect system metrics periodically"""
        while self._running:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Calculate AI News project memory usage
                ainews_memory_mb = 0.0
                try:
                    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cmdline']):
                        try:
                            proc_info = proc.info
                            if proc_info['cmdline']:
                                cmdline_str = ' '.join(proc_info['cmdline']).lower()
                                ai_news_keywords = ['ainews', 'ai-news', 'main.py', 'app.py', 'unified_crawl_parser', 'monitoring']
                                if any(keyword in cmdline_str for keyword in ai_news_keywords):
                                    ainews_memory_mb += proc_info['memory_info'].rss / 1024 / 1024
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                except Exception as e:
                    print(f"Error calculating AI News memory: {e}")
                    # Fallback to a small default value if we can't calculate
                    ainews_memory_mb = 200.0  # 200MB default
                
                # Calculate parse rate and error rate
                parse_count = 0
                error_count = 0
                
                # Count recent parses
                for _, success in list(self._recent_parses.queue):
                    parse_count += 1
                    if not success:
                        error_count += 1
                
                parse_rate = parse_count  # per minute
                error_rate = (error_count / parse_count * 100) if parse_count > 0 else 0
                
                # Create metrics object
                metrics = PerformanceMetrics(
                    timestamp=datetime.now(),
                    cpu_usage_percent=cpu_percent,
                    memory_usage_mb=ainews_memory_mb,  # Use AI News memory instead of system memory
                    disk_usage_percent=disk.percent,
                    active_connections=self._active_connections,
                    queue_size=self._parse_queue_size,
                    parse_rate_per_minute=parse_rate,
                    error_rate_percent=error_rate
                )
                
                # Save to database
                self.monitoring_db.save_performance_metrics(metrics)
                
                
            except Exception as e:
                # Silently ignore temporary errors to reduce log noise
                pass
            
            # Sleep for the interval
            time.sleep(self.interval_seconds)
    
    def _clear_caches(self):
        """Clear internal caches to free memory"""
        try:
            # Clear metrics cache
            if hasattr(self, '_metrics_cache'):
                self._metrics_cache.clear()
            
            # Clear queues if they're too large
            if self._recent_parses.qsize() > 1000:
                while self._recent_parses.qsize() > 500:
                    try:
                        self._recent_parses.get_nowait()
                    except queue.Empty:
                        break
            
            if self._recent_errors.qsize() > 500:
                while self._recent_errors.qsize() > 250:
                    try:
                        self._recent_errors.get_nowait()
                    except queue.Empty:
                        break
                        
            print(f"SystemMetricsCollector cache cleared. Parse queue: {self._recent_parses.qsize()}, Error queue: {self._recent_errors.qsize()}")
        except Exception as e:
            print(f"Error clearing SystemMetricsCollector caches: {e}")


class SourceHealthCollector(MetricsCollector):
    """Simplified source metrics collector - complex health scoring removed"""
    
    def __init__(self, monitoring_db: MonitoringDatabase, check_interval_seconds: int = 300, log_processor: Optional[Any] = None):
        super().__init__(monitoring_db)
        self.check_interval_seconds = check_interval_seconds
        # FIXED: Add limits to prevent unlimited cache growth
        self._metrics_cache = {}
        self._max_cache_entries = 1000  # Limit cache size
        self._last_collection_time = {}
        self._cache_cleanup_counter = 0
        self.log_processor = log_processor
    
    def collect_source_metrics(self, source_id: str, parsing_result: Dict[str, Any]):
        """Collect metrics during parsing for real-time updates"""
        timestamp = datetime.now()
        
        # Extract metrics from parsing result
        metrics = {
            'timestamp': timestamp,
            'source_id': source_id,
            'success': parsing_result.get('success', False),
            'articles_found': parsing_result.get('article_count', 0),
            'parse_time_ms': parsing_result.get('parse_time_ms', 0),
            'error_type': parsing_result.get('error_type', None),
            'error_message': parsing_result.get('error_message', None),
            'response_time_ms': parsing_result.get('response_time_ms', 0),
            'content_quality': parsing_result.get('content_quality', 0),
            'media_success_rate': parsing_result.get('media_success_rate', 100),
        }
        
        # Cache metrics for batch processing with size control
        if source_id not in self._metrics_cache:
            self._metrics_cache[source_id] = []
        
        # FIXED: Prevent unlimited cache growth
        if len(self._metrics_cache[source_id]) >= 100:  # Max 100 entries per source
            # Remove oldest 20% of entries
            entries_to_remove = len(self._metrics_cache[source_id]) // 5
            self._metrics_cache[source_id] = self._metrics_cache[source_id][entries_to_remove:]
        
        self._metrics_cache[source_id].append(metrics)
        
        # Periodic cleanup of the entire cache
        self._cache_cleanup_counter += 1
        if self._cache_cleanup_counter >= 50:  # Every 50 calls
            self._cleanup_cache()
            self._cache_cleanup_counter = 0
        
        # Process cached metrics every 60 seconds
        if source_id not in self._last_collection_time or \
           (timestamp - self._last_collection_time.get(source_id, datetime.min)).seconds > 60:
            self._process_cached_metrics(source_id)
            self._last_collection_time[source_id] = timestamp
    
    def _process_cached_metrics(self, source_id: str):
        """Process cached metrics and update database"""
        if source_id not in self._metrics_cache or not self._metrics_cache[source_id]:
            return
        
        metrics_list = self._metrics_cache[source_id]
        
        # Calculate aggregated metrics
        total_attempts = len(metrics_list)
        successful_attempts = sum(1 for m in metrics_list if m['success'])
        total_articles = sum(m['articles_found'] for m in metrics_list)
        avg_parse_time = sum(m['parse_time_ms'] for m in metrics_list) / total_attempts if total_attempts > 0 else 0
        avg_response_time = sum(m['response_time_ms'] for m in metrics_list) / total_attempts if total_attempts > 0 else 0
        
        # Store in monitoring database
        try:
            self.monitoring_db.update_source_metrics(
                source_id=source_id,
                articles_parsed=total_articles,
                articles_failed=total_attempts - successful_attempts,
                avg_parse_time_ms=avg_parse_time,
                avg_response_time_ms=avg_response_time,
                success_rate=successful_attempts / total_attempts * 100 if total_attempts > 0 else 0
            )
        except Exception as e:
            print(f"Error updating source metrics for {source_id}: {e}")
        
        # Clear cache
        self._metrics_cache[source_id] = []
    
    def _cleanup_cache(self):
        """Clean up the entire metrics cache to prevent memory leaks"""
        try:
            # Remove empty cache entries
            empty_keys = [key for key, value in self._metrics_cache.items() if not value]
            for key in empty_keys:
                del self._metrics_cache[key]
            
            # If cache is still too large, remove oldest entries
            if len(self._metrics_cache) > self._max_cache_entries:
                # Sort by last collection time and remove oldest
                sorted_keys = sorted(
                    self._metrics_cache.keys(),
                    key=lambda k: self._last_collection_time.get(k, datetime.min)
                )
                
                keys_to_remove = sorted_keys[:len(self._metrics_cache) - self._max_cache_entries]
                for key in keys_to_remove:
                    del self._metrics_cache[key]
                    if key in self._last_collection_time:
                        del self._last_collection_time[key]
            
            print(f"SourceHealthCollector cache cleanup: {len(self._metrics_cache)} sources cached")
        except Exception as e:
            print(f"Error during cache cleanup: {e}")
    
    def _clear_caches(self):
        """Clear internal caches to free memory - called by memory monitor"""
        try:
            # Clear metrics cache
            cache_size_before = len(self._metrics_cache)
            self._metrics_cache.clear()
            
            # Clear collection times
            self._last_collection_time.clear()
            
            print(f"SourceHealthCollector caches cleared. Removed {cache_size_before} cached sources.")
        except Exception as e:
            print(f"Error clearing SourceHealthCollector caches: {e}")
    
    def consume_log_metrics(self):
        """Consume metrics from log processor - DISABLED: log_processor removed"""
        if not self.log_processor:
            return
        
        # DISABLED: log_processor module removed
        # Original functionality commented out
        # try:
        #     log_summary = self.log_processor.consume_log_metrics()
        #     if log_summary.get('processed_entries', 0) > 0:
        #         print(f"Consumed {log_summary['processed_entries']} log entries")
        return  # Method disabled
    
    # REMOVED: Complex 7-component health scoring - using simple status-based calculation
    def calculate_simple_status(self, source_metrics: Dict[str, Any]) -> str:
        """Simple status calculation based on last_status only"""
        last_status = source_metrics.get('last_status', 'unknown')
        recent_errors = source_metrics.get('recent_errors_24h', 0)
        
        if last_status == 'active' and recent_errors < 5:
            return 'healthy'
        elif recent_errors >= 5:
            return 'warning'
        else:
            return 'error'
    
    def _run(self):
        """Check source health periodically"""
        while self._running:
            try:
                # Consume metrics from log processor
                self.consume_log_metrics()
                
                # Process any remaining cached metrics
                for source_id in list(self._metrics_cache.keys()):
                    self._process_cached_metrics(source_id)
                
                # Get all source metrics with enhanced data
                try:
                    sources = self.monitoring_db.get_source_metrics_detailed()
                except Exception as e:
                    print(f"Error checking source health: {e}")
                    self.logger.error(f"Failed to get source metrics: {e}")
                    time.sleep(30)  # Wait before retrying
                    continue
                
                for source in sources:
                    # Simple status calculation (removed complex health scoring)
                    simple_status = self.calculate_simple_status(source)
                    health_score = 100 if simple_status == 'healthy' else (50 if simple_status == 'warning' else 0)
                    
                    # Skip database health score update (method removed)
                    
                
            except Exception as e:
                print(f"Error checking source health: {e}")
                import traceback
                traceback.print_exc()
            
            time.sleep(self.check_interval_seconds)