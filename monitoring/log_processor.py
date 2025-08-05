"""
Log processor for real-time extraction of metrics from JSON logs
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
import threading
import queue
from collections import defaultdict
import re

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from app_logging import get_logger
from .database import MonitoringDatabase


class LogFileHandler(FileSystemEventHandler):
    """Handles file system events for log files"""
    
    def __init__(self, processor: 'LogDataExtractor'):
        self.processor = processor
        self.logger = get_logger('monitoring.log_processor')
    
    def on_modified(self, event):
        """Handle file modification events"""
        if isinstance(event, FileModifiedEvent) and not event.is_directory:
            if event.src_path.endswith('.log'):
                log_name = Path(event.src_path).name
                self.processor.process_log_file(log_name, tail_only=True)


class LogDataExtractor:
    """Extracts monitoring metrics from JSON-formatted logs in real-time"""
    
    def __init__(self, monitoring_db: MonitoringDatabase, logs_dir: str = "logs", error_collector: Optional['ErrorContextCollector'] = None):
        self.logger = get_logger('monitoring.log_processor')
        self.monitoring_db = monitoring_db
        self.logs_dir = Path(logs_dir)
        self._running = False
        self._observer = None
        self._processor_thread = None
        self._queue = queue.Queue()
        self.error_collector = error_collector
        
        # Track file positions for efficient tailing
        self._file_positions = {}
        self._position_file = self.logs_dir / ".log_positions.json"
        self._load_positions()
        
        # FIXED: Metrics cache with limits to prevent memory leaks
        self._metrics_cache = defaultdict(lambda: self._create_limited_list())
        self._max_cache_entries_per_type = 100  # Reduced from 1000 to prevent memory growth
        self._last_flush_time = time.time()
        self._flush_interval = 60  # Flush every 60 seconds
        
        # Define log extractors
        self._extractors = {
            'api.log': self._extract_api_metrics,
            'errors.log': self._extract_error_metrics,
            'metrics.log': self._extract_performance_metrics,
            'parsing.log': self._extract_parsing_metrics,
            'ai_news_parser.log': self._extract_general_metrics,
            'api_costs.log': self._extract_api_cost_metrics
        }
        
        # FIXED: Error context aggregator with limits
        self._error_contexts = defaultdict(lambda: self._create_limited_list())
        self._max_error_contexts_per_type = 50  # Reduced from 500 to prevent memory growth
        self._correlation_patterns = re.compile(r'(crawl_id|article_id|source_id|request_id)["\':\s]+["\']*([a-zA-Z0-9\-_]+)')
        
        # File positions cleanup
        self._max_file_positions = 1000  # Limit tracked file positions
    
    def _create_limited_list(self) -> List[Any]:
        """Create a list that automatically limits its size"""
        return []
    
    def _add_to_cache_with_limit(self, cache_key: str, item: Any, max_items: int):
        """Add item to cache with size limit"""
        cache_list = self._metrics_cache[cache_key]
        
        # Remove oldest items if at limit
        if len(cache_list) >= max_items:
            # Remove oldest 20% of items
            items_to_remove = max(1, len(cache_list) // 5)
            cache_list[:] = cache_list[items_to_remove:]
        
        cache_list.append(item)
    
    def _add_to_error_context_with_limit(self, context_key: str, item: Any):
        """Add error context with size limit"""
        context_list = self._error_contexts[context_key]
        
        # Remove oldest items if at limit
        if len(context_list) >= self._max_error_contexts_per_type:
            # Remove oldest 20% of items
            items_to_remove = max(1, len(context_list) // 5)
            context_list[:] = context_list[items_to_remove:]
        
        context_list.append(item)
    
    def _cleanup_file_positions(self):
        """Clean up old file positions to prevent memory leaks"""
        if len(self._file_positions) > self._max_file_positions:
            # Sort by access time and remove oldest
            sorted_positions = sorted(
                self._file_positions.items(),
                key=lambda x: x[1].get('last_accessed', 0)
            )
            
            # Remove oldest 20%
            items_to_remove = len(self._file_positions) // 5
            for key, _ in sorted_positions[:items_to_remove]:
                del self._file_positions[key]
            
            self.logger.info(f"Cleaned up {items_to_remove} old file positions")
    
    def _cleanup_old_data(self):
        """Periodic cleanup of old data to prevent memory growth"""
        try:
            # Clean up metrics cache - keep only recent entries
            for cache_key in list(self._metrics_cache.keys()):
                cache_list = self._metrics_cache[cache_key]
                if len(cache_list) > self._max_cache_entries_per_type // 2:
                    # Keep only the most recent half
                    self._metrics_cache[cache_key] = cache_list[-(self._max_cache_entries_per_type // 2):]
            
            # Clean up error contexts - keep only recent entries
            for context_key in list(self._error_contexts.keys()):
                context_list = self._error_contexts[context_key]
                if len(context_list) > self._max_error_contexts_per_type // 2:
                    # Keep only the most recent half
                    self._error_contexts[context_key] = context_list[-(self._max_error_contexts_per_type // 2):]
            
            # Clean up file positions
            self._cleanup_file_positions()
            
            # Force garbage collection
            import gc
            gc.collect()
            
            self.logger.debug("Completed periodic cleanup of old data")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def start(self):
        """Start the log processor"""
        self._running = True
        
        # Start file watcher
        self._observer = Observer()
        event_handler = LogFileHandler(self)
        self._observer.schedule(event_handler, str(self.logs_dir), recursive=False)
        self._observer.start()
        
        # Start processor thread
        self._processor_thread = threading.Thread(target=self._process_queue)
        self._processor_thread.daemon = True
        self._processor_thread.start()
        
        # Process existing logs for backlog
        self._process_backlog()
        
        self.logger.info("Log processor started")
    
    def stop(self):
        """Stop the log processor"""
        self._running = False
        
        if self._observer:
            self._observer.stop()
            self._observer.join()
        
        if self._processor_thread:
            self._processor_thread.join()
        
        # Final flush
        self._flush_metrics()
        self._save_positions()
        
        self.logger.info("Log processor stopped")
    
    def _load_positions(self):
        """Load saved file positions"""
        if self._position_file.exists():
            try:
                with open(self._position_file, 'r') as f:
                    self._file_positions = json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load positions: {e}")
                self._file_positions = {}
    
    def _save_positions(self):
        """Save file positions"""
        try:
            with open(self._position_file, 'w') as f:
                json.dump(self._file_positions, f)
        except Exception as e:
            self.logger.error(f"Failed to save positions: {e}")
    
    def _process_recent_log_entries(self, log_name: str, since_timestamp: float):
        """Process only recent log entries since given timestamp"""
        log_path = self.logs_dir / log_name
        if not log_path.exists():
            return
        
        try:
            processed_count = 0
            with open(log_path, 'r', encoding='utf-8') as f:
                # Start from end and work backwards to find entries within time window
                # For efficiency, we'll read the whole file but only process recent entries
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            # Check timestamp
                            timestamp_str = entry.get('timestamp', '')
                            if timestamp_str:
                                # Parse ISO format timestamp
                                entry_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                entry_timestamp = entry_time.timestamp()
                                
                                # Only process if within time window
                                if entry_timestamp >= since_timestamp:
                                    self._queue.put((log_name, line))
                                    processed_count += 1
                        except (json.JSONDecodeError, ValueError):
                            # Skip invalid entries
                            pass
                
                # Update file position to end
                self._file_positions[log_name] = f.tell()
                
            if processed_count > 0:
                self.logger.info(f"Processed {processed_count} recent entries from {log_name}")
                    
        except Exception as e:
            self.logger.error(f"Error processing recent entries from {log_name}: {e}")
    
    def _process_backlog(self):
        """Process only recent log entries (last 3 hours) from all log files"""
        self.logger.info("Processing backlog - reading only last 3 hours of logs")
        three_hours_ago = time.time() - (3 * 60 * 60)
        
        for log_file in self.logs_dir.glob("*.log"):
            if log_file.name in self._extractors:
                # For backlog, we'll use a special method to read only recent entries
                self._process_recent_log_entries(log_file.name, three_hours_ago)
    
    def process_log_file(self, log_name: str, tail_only: bool = True):
        """Process a specific log file"""
        log_path = self.logs_dir / log_name
        if not log_path.exists():
            return
        
        try:
            # Get last position
            last_position = self._file_positions.get(log_name, 0) if tail_only else 0
            
            with open(log_path, 'r', encoding='utf-8') as f:
                # Seek to last position
                f.seek(last_position)
                
                # Read new lines
                for line in f:
                    line = line.strip()
                    if line:
                        self._queue.put((log_name, line))
                
                # Update position
                self._file_positions[log_name] = f.tell()
        
        except Exception as e:
            self.logger.error(f"Error processing {log_name}: {e}")
    
    def _process_queue(self):
        """Process queued log entries"""
        while self._running:
            try:
                # Get items with timeout
                items = []
                deadline = time.time() + 1.0
                
                while time.time() < deadline:
                    try:
                        item = self._queue.get(timeout=0.1)
                        items.append(item)
                        if len(items) >= 100:  # Batch size limit
                            break
                    except queue.Empty:
                        break
                
                # Process batch
                if items:
                    for log_name, line in items:
                        self._process_log_entry(log_name, line)
                
                # Periodic flush and cleanup
                if time.time() - self._last_flush_time > self._flush_interval:
                    self._flush_metrics()
                    self._save_positions()
                    self._cleanup_old_data()  # Add periodic cleanup
                    self._last_flush_time = time.time()
            
            except Exception as e:
                self.logger.error(f"Error in queue processor: {e}")
    
    def _process_log_entry(self, log_name: str, line: str):
        """Process a single log entry"""
        try:
            # Track line in error collector if available
            if self.error_collector:
                self.error_collector.add_log_line(log_name, line)
            
            # Parse JSON
            entry = json.loads(line)
            
            # Get appropriate extractor
            extractor = self._extractors.get(log_name)
            if extractor:
                metrics = extractor(entry)
                if metrics:
                    self._cache_metrics(log_name, metrics)
            
            # Always check for errors
            if entry.get('level') == 'ERROR':
                self._aggregate_error_context(entry)
                # Also capture enhanced error context
                if self.error_collector:
                    self.error_collector.capture_error_context(log_name, entry)
        
        except json.JSONDecodeError:
            # Skip non-JSON lines
            pass
        except Exception as e:
            self.logger.error(f"Error processing log entry: {e}")
    
    def _extract_api_metrics(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract metrics from API logs"""
        extra = entry.get('extra', {})
        
        # Look for API response metrics
        if 'response_time_ms' in extra or 'status_code' in extra:
            return {
                'timestamp': entry.get('timestamp'),
                'endpoint': extra.get('endpoint', 'unknown'),
                'method': extra.get('method', 'GET'),
                'status_code': extra.get('status_code'),
                'response_time_ms': extra.get('response_time_ms'),
                'api_cost': extra.get('cost', 0),
                'rate_limit_remaining': extra.get('rate_limit_remaining'),
                'source_id': extra.get('source_id')
            }
        
        return None
    
    def _extract_error_metrics(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract metrics from error logs"""
        return {
            'timestamp': entry.get('timestamp'),
            'error_type': entry.get('extra', {}).get('error_type', 'unknown'),
            'source_id': entry.get('extra', {}).get('source_id'),
            'module': entry.get('module'),
            'message': entry.get('message'),
            'stack_trace': entry.get('extra', {}).get('stack_trace')
        }
    
    def _extract_performance_metrics(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract metrics from performance logs"""
        extra = entry.get('extra', {})
        
        if 'cpu_percent' in extra or 'memory_mb' in extra:
            return {
                'timestamp': entry.get('timestamp'),
                'cpu_percent': extra.get('cpu_percent'),
                'memory_mb': extra.get('memory_mb'),
                'disk_percent': extra.get('disk_percent'),
                'active_threads': extra.get('active_threads'),
                'queue_size': extra.get('queue_size')
            }
        
        return None
    
    def _extract_parsing_metrics(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract metrics from parsing logs"""
        extra = entry.get('extra', {})
        
        # Look for parsing completion events
        if 'parse_time_ms' in extra or 'articles_parsed' in extra:
            return {
                'timestamp': entry.get('timestamp'),
                'source_id': extra.get('source_id'),
                'articles_parsed': extra.get('articles_parsed', 0),
                'parse_time_ms': extra.get('parse_time_ms'),
                'success': extra.get('success', False),
                'parse_method': extra.get('parse_method'),
                'content_length': extra.get('content_length')
            }
        
        return None
    
    def _extract_general_metrics(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract metrics from general application logs"""
        extra = entry.get('extra', {})
        
        # Look for monitoring events
        if entry.get('logger') == 'monitoring.integration':
            if 'Completed parse' in entry.get('message', ''):
                return {
                    'timestamp': entry.get('timestamp'),
                    'source_id': extra.get('extra', {}).get('source_id'),
                    'articles': extra.get('extra', {}).get('articles', 0),
                    'parse_time_ms': extra.get('extra', {}).get('parse_time_ms'),
                    'success': extra.get('extra', {}).get('success', False)
                }
        
        # Look for crawl service events
        elif entry.get('logger') == 'ai_news_parser.crawl_service':
            if 'Crawl completed' in entry.get('message', ''):
                return {
                    'timestamp': entry.get('timestamp'),
                    'source_id': extra.get('source_id'),
                    'crawl_id': extra.get('crawl_id'),
                    'total_items': extra.get('total_items', 0),
                    'duration': extra.get('duration'),
                    'attempts': extra.get('attempts', 1)
                }
        
        return None
    
    def _extract_api_cost_metrics(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract API cost metrics"""
        extra = entry.get('extra', {})
        
        if 'cost' in extra or 'tokens_used' in extra:
            return {
                'timestamp': entry.get('timestamp'),
                'service': extra.get('service', 'unknown'),
                'endpoint': extra.get('endpoint'),
                'cost': extra.get('cost', 0),
                'tokens_used': extra.get('tokens_used', 0),
                'source_id': extra.get('source_id')
            }
        
        return None
    
    def _cache_metrics(self, log_name: str, metrics: Dict[str, Any]):
        """Cache metrics for batch processing with size limit"""
        self._add_to_cache_with_limit(log_name, metrics, self._max_cache_entries_per_type)
    
    def _flush_metrics(self):
        """Flush cached metrics to database"""
        try:
            for log_name, metrics_list in self._metrics_cache.items():
                if not metrics_list:
                    continue
                
                # Process based on log type
                if log_name == 'api.log':
                    self._store_api_metrics(metrics_list)
                elif log_name == 'errors.log':
                    self._store_error_metrics(metrics_list)
                elif log_name == 'parsing.log':
                    self._store_parsing_metrics(metrics_list)
                elif log_name == 'api_costs.log':
                    self._store_cost_metrics(metrics_list)
                elif log_name == 'ai_news_parser.log':
                    self._store_general_metrics(metrics_list)
            
            # Clear cache
            self._metrics_cache.clear()
            
        except Exception as e:
            self.logger.error(f"Error flushing metrics: {e}")
    
    def _store_api_metrics(self, metrics_list: List[Dict[str, Any]]):
        """Store API metrics in database"""
        # Group by source
        by_source = defaultdict(list)
        for m in metrics_list:
            if m.get('source_id'):
                by_source[m['source_id']].append(m)
        
        # Calculate aggregates per source
        for source_id, metrics in by_source.items():
            total_requests = len(metrics)
            total_cost = sum(m.get('cost', 0) for m in metrics)
            avg_response_time = sum(m.get('response_time_ms', 0) for m in metrics) / total_requests
            error_count = sum(1 for m in metrics if m.get('status_code', 200) >= 400)
            
            self.monitoring_db.update_source_metrics(
                source_id=source_id,
                api_requests=total_requests,
                api_errors=error_count,
                avg_response_time_ms=avg_response_time,
                api_cost=total_cost
            )
    
    def _store_error_metrics(self, metrics_list: List[Dict[str, Any]]):
        """Store error metrics in database"""
        for error in metrics_list:
            self.monitoring_db.log_error({
                'source_id': error.get('source_id'),
                'error_type': error.get('error_type'),
                'error_message': error.get('message'),
                'stack_trace': error.get('stack_trace'),
                'context': {
                    'module': error.get('module'),
                    'timestamp': error.get('timestamp')
                }
            })
    
    def _store_parsing_metrics(self, metrics_list: List[Dict[str, Any]]):
        """Store parsing metrics in database"""
        # Group by source
        by_source = defaultdict(list)
        for m in metrics_list:
            if m.get('source_id'):
                by_source[m['source_id']].append(m)
        
        # Update source metrics
        for source_id, metrics in by_source.items():
            successful = [m for m in metrics if m.get('success')]
            failed = [m for m in metrics if not m.get('success')]
            
            total_articles = sum(m.get('articles_parsed', 0) for m in successful)
            avg_parse_time = sum(m.get('parse_time_ms', 0) for m in metrics) / len(metrics) if metrics else 0
            
            self.monitoring_db.update_source_metrics(
                source_id=source_id,
                articles_parsed=total_articles,
                articles_failed=len(failed),
                avg_parse_time_ms=avg_parse_time,
                success_rate=(len(successful) / len(metrics) * 100) if metrics else 0
            )
    
    def _store_cost_metrics(self, metrics_list: List[Dict[str, Any]]):
        """Store API cost metrics"""
        # Group by source
        by_source = defaultdict(float)
        for m in metrics_list:
            if m.get('source_id'):
                by_source[m['source_id']] += m.get('cost', 0)
        
        # Update article stats with costs
        for source_id, total_cost in by_source.items():
            self.monitoring_db.save_article_stats({
                'source_id': source_id,
                'api_cost': total_cost
            })
    
    def _store_general_metrics(self, metrics_list: List[Dict[str, Any]]):
        """Store general metrics from main log"""
        # Process monitoring integration events
        for m in metrics_list:
            if m.get('source_id') and 'parse_time_ms' in m:
                self.monitoring_db.update_source_metrics(
                    source_id=m['source_id'],
                    articles_parsed=m.get('articles', 0),
                    avg_parse_time_ms=m.get('parse_time_ms', 0),
                    success_rate=100 if m.get('success') else 0
                )
    
    def _aggregate_error_context(self, error_entry: Dict[str, Any]):
        """Aggregate error context for debugging"""
        # Extract correlation IDs
        message = error_entry.get('message', '')
        extra = error_entry.get('extra', {})
        
        correlations = {}
        # Find correlation IDs in message and extra
        for match in self._correlation_patterns.finditer(message):
            correlations[match.group(1)] = match.group(2)
        
        for key, value in extra.items():
            if key in ['crawl_id', 'article_id', 'source_id', 'request_id']:
                correlations[key] = value
        
        # Store error with context
        error_info = {
            'timestamp': error_entry.get('timestamp'),
            'source_id': correlations.get('source_id'),
            'error_type': error_entry.get('logger', 'unknown'),
            'error_message': message,
            'stack_trace': extra.get('stack_trace', ''),
            'context': {
                'module': error_entry.get('module'),
                'function': error_entry.get('function'),
                'line': error_entry.get('line'),
                'correlations': correlations,
                'extra': extra
            },
            'correlation_id': correlations.get('crawl_id') or correlations.get('request_id')
        }
        
        self.monitoring_db.log_error(error_info)
    
    def consume_log_metrics(self) -> Dict[str, Any]:
        """Public method for collectors to consume extracted metrics"""
        # Force flush and return summary
        self._flush_metrics()
        
        # Return summary of processed metrics
        return {
            'processed_entries': sum(len(v) for v in self._metrics_cache.values()),
            'last_flush': datetime.fromtimestamp(self._last_flush_time).isoformat(),
            'active_logs': list(self._metrics_cache.keys())
        }
    
    def force_cleanup(self):
        """Force cleanup method for memory monitor to call"""
        self.logger.info("Forcing cleanup due to memory pressure")
        self._cleanup_old_data()
        self._flush_metrics()
        
        # Also clear error collector buffers if available
        if self.error_collector:
            self.error_collector.clear_old_errors(days=0.125)  # Clear anything older than 3 hours


class ErrorContextCollector:
    """
    Enhanced error context collector for comprehensive debugging
    
    Features:
    - Full stack traces capture
    - Surrounding log lines (5 before/after)
    - Error grouping by type and source
    - Exportable error bundles
    - Enhanced error storage in database
    """
    
    def __init__(self, monitoring_db: MonitoringDatabase, logs_dir: str = "logs"):
        self.monitoring_db = monitoring_db
        self.logger = get_logger('monitoring.error_collector')
        self.logs_dir = Path(logs_dir)
        
        # Error context storage
        self._error_buffer = defaultdict(list)  # log_file -> list of lines
        self._max_buffer_lines = 100  # Reduced from 1000 to prevent memory growth
        self._context_lines = 5  # Lines before/after error
        
        # Error grouping
        self._error_groups = defaultdict(list)  # (error_type, source_id) -> list of errors
        self._max_errors_per_group = 20  # Reduced from 100 to prevent memory growth
        
        # Export capabilities
        self._export_dir = Path("error_exports")
        self._export_dir.mkdir(exist_ok=True)
    
    def add_log_line(self, log_file: str, line: str):
        """Add a log line to the buffer for context tracking"""
        buffer = self._error_buffer[log_file]
        buffer.append({
            'timestamp': datetime.now(),
            'line': line
        })
        
        # Maintain buffer size limit
        if len(buffer) > self._max_buffer_lines:
            buffer.pop(0)
    
    def capture_error_context(self, log_file: str, error_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Capture full error context including surrounding lines"""
        buffer = self._error_buffer.get(log_file, [])
        error_time = error_entry.get('timestamp', datetime.now())
        
        # Find error position in buffer
        error_idx = -1
        for i, entry in enumerate(buffer):
            if abs((entry['timestamp'] - error_time).total_seconds()) < 1:
                error_idx = i
                break
        
        # Collect surrounding lines
        context_before = []
        context_after = []
        
        if error_idx >= 0:
            # Get lines before
            start_idx = max(0, error_idx - self._context_lines)
            context_before = [entry['line'] for entry in buffer[start_idx:error_idx]]
            
            # Get lines after
            end_idx = min(len(buffer), error_idx + self._context_lines + 1)
            context_after = [entry['line'] for entry in buffer[error_idx + 1:end_idx]]
        
        # Extract detailed error info
        error_info = {
            'timestamp': error_time,
            'log_file': log_file,
            'error_type': self._classify_error(error_entry),
            'error_message': error_entry.get('message', ''),
            'stack_trace': error_entry.get('extra', {}).get('stack_trace', ''),
            'module': error_entry.get('module', ''),
            'function': error_entry.get('function', ''),
            'line_number': error_entry.get('line', 0),
            'source_id': error_entry.get('extra', {}).get('source_id'),
            'context_before': context_before,
            'context_after': context_after,
            'extra_data': error_entry.get('extra', {})
        }
        
        # Group error
        self._group_error(error_info)
        
        # Store enhanced error in database
        self._store_enhanced_error(error_info)
        
        return error_info
    
    def _classify_error(self, error_entry: Dict[str, Any]) -> str:
        """Classify error type based on content"""
        message = error_entry.get('message', '').lower()
        extra = error_entry.get('extra', {})
        
        # Common error patterns
        if 'timeout' in message:
            return 'timeout_error'
        elif 'connection' in message or 'network' in message:
            return 'network_error'
        elif 'rate limit' in message:
            return 'rate_limit_error'
        elif 'parse' in message or 'parsing' in message:
            return 'parsing_error'
        elif 'memory' in message:
            return 'memory_error'
        elif 'permission' in message or 'access denied' in message:
            return 'permission_error'
        elif 'validation' in message:
            return 'validation_error'
        elif extra.get('error_type'):
            return extra['error_type']
        else:
            return 'unknown_error'
    
    def _group_error(self, error_info: Dict[str, Any]):
        """Group error by type and source"""
        group_key = (error_info['error_type'], error_info.get('source_id', 'no_source'))
        error_group = self._error_groups[group_key]
        
        # Add to group with limit
        error_group.append({
            'timestamp': error_info['timestamp'],
            'message': error_info['error_message'],
            'stack_trace': error_info['stack_trace']
        })
        
        if len(error_group) > self._max_errors_per_group:
            error_group.pop(0)
    
    def _store_enhanced_error(self, error_info: Dict[str, Any]):
        """Store enhanced error with full context in database"""
        try:
            # Prepare context data
            context_data = {
                'module': error_info['module'],
                'function': error_info['function'],
                'line_number': error_info['line_number'],
                'context_before': error_info['context_before'],
                'context_after': error_info['context_after'],
                'extra_data': error_info['extra_data']
            }
            
            # Store in database
            self.monitoring_db.log_error({
                'source_id': error_info.get('source_id'),
                'error_type': error_info['error_type'],
                'error_message': error_info['error_message'],
                'stack_trace': error_info['stack_trace'],
                'context': context_data,
                'timestamp': error_info['timestamp']
            })
            
        except Exception as e:
            self.logger.error(f"Failed to store enhanced error: {e}")
    
    def get_error_groups(self) -> Dict[str, Any]:
        """Get all error groups with statistics"""
        groups = []
        
        for (error_type, source_id), errors in self._error_groups.items():
            if errors:
                groups.append({
                    'error_type': error_type,
                    'source_id': source_id,
                    'count': len(errors),
                    'first_seen': min(e['timestamp'] for e in errors),
                    'last_seen': max(e['timestamp'] for e in errors),
                    'sample_messages': [e['message'] for e in errors[:3]]
                })
        
        # Sort by count descending
        groups.sort(key=lambda g: g['count'], reverse=True)
        
        return {
            'total_groups': len(groups),
            'total_errors': sum(g['count'] for g in groups),
            'groups': groups
        }
    
    def export_error_bundle(self, error_type: str = None, source_id: str = None) -> str:
        """Export error bundle with all context for debugging"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"error_bundle_{timestamp}"
        
        if error_type:
            filename += f"_{error_type}"
        if source_id:
            filename += f"_{source_id}"
        
        filename += ".json"
        filepath = self._export_dir / filename
        
        # Collect errors to export
        errors_to_export = []
        
        for (e_type, s_id), errors in self._error_groups.items():
            if error_type and e_type != error_type:
                continue
            if source_id and s_id != source_id:
                continue
            
            for error in errors:
                errors_to_export.append({
                    'error_type': e_type,
                    'source_id': s_id,
                    'error': error
                })
        
        # Get recent errors from database
        db_errors = self.monitoring_db.get_recent_error_logs(limit=1000)
        
        # Filter if needed
        if error_type or source_id:
            db_errors = [
                e for e in db_errors
                if (not error_type or e.get('error_type') == error_type) and
                   (not source_id or e.get('source_id') == source_id)
            ]
        
        # Create bundle
        bundle = {
            'export_timestamp': timestamp,
            'filters': {
                'error_type': error_type,
                'source_id': source_id
            },
            'summary': self.get_error_groups(),
            'buffered_errors': errors_to_export,
            'database_errors': db_errors,
            'system_info': {
                'timestamp': datetime.now().isoformat(),
                'logs_dir': str(self.logs_dir),
                'export_dir': str(self._export_dir)
            }
        }
        
        # Write bundle
        with open(filepath, 'w') as f:
            json.dump(bundle, f, indent=2, default=str)
        
        self.logger.info(f"Exported error bundle to {filepath}")
        return str(filepath)
    
    def clear_old_errors(self, days: float = 7):
        """Clear old errors from memory"""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        # Clear from groups
        for group_key in list(self._error_groups.keys()):
            errors = self._error_groups[group_key]
            self._error_groups[group_key] = [
                e for e in errors
                if e['timestamp'] > cutoff_time
            ]
            
            # Remove empty groups
            if not self._error_groups[group_key]:
                del self._error_groups[group_key]
        
        self.logger.info(f"Cleared errors older than {days} days")


class ErrorContextAggregator:
    """Aggregates error context for 1-click debugging"""
    
    def __init__(self, monitoring_db: MonitoringDatabase):
        self.monitoring_db = monitoring_db
        self.logger = get_logger('monitoring.error_aggregator')
    
    def get_error_context(self, error_id: str) -> Dict[str, Any]:
        """Get full context for an error including related logs"""
        # Get error from database
        errors = self.monitoring_db.get_recent_error_logs(limit=1000)
        error = next((e for e in errors if str(e.get('id')) == error_id), None)
        
        if not error:
            return {'error': 'Error not found'}
        
        context = error.get('context', {})
        correlations = context.get('correlations', {})
        
        # Get related logs by correlation IDs
        related_logs = []
        
        # TODO: Implement correlation-based log retrieval
        # This would require parsing logs with correlation IDs
        
        return {
            'error': error,
            'related_logs': related_logs,
            'source_info': self._get_source_info(error.get('source_id')),
            'timeline': self._build_error_timeline(error, related_logs)
        }
    
    def _get_source_info(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get source information"""
        if not source_id:
            return None
        
        metrics = self.monitoring_db.get_source_metrics(source_id)
        if metrics:
            source = metrics[0]
            return {
                'source_id': source.source_id,
                'name': source.name,
                'url': source.url,
                'health_score': source.health_score,
                'last_status': source.last_status
            }
        
        return None
    
    def _build_error_timeline(self, error: Dict[str, Any], related_logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build timeline of events leading to error"""
        timeline = []
        
        # Add error event
        timeline.append({
            'timestamp': error.get('timestamp'),
            'type': 'error',
            'message': error.get('error_message'),
            'details': error
        })
        
        # Add related events
        for log in related_logs:
            timeline.append({
                'timestamp': log.get('timestamp'),
                'type': log.get('level', 'info').lower(),
                'message': log.get('message'),
                'details': log
            })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x['timestamp'])
        
        return timeline
    
    def force_cleanup(self):
        """Force cleanup of all caches - called by memory monitor"""
        try:
            # Clear metrics cache
            cache_sizes_before = {k: len(v) for k, v in self._metrics_cache.items()}
            self._metrics_cache.clear()
            
            # Clear error contexts
            error_sizes_before = {k: len(v) for k, v in self._error_contexts.items()}
            self._error_contexts.clear()
            
            # Cleanup file positions
            positions_before = len(self._file_positions)
            self._cleanup_file_positions()
            
            # Force flush any remaining metrics
            self._flush_metrics()
            
            self.logger.info(f"LogDataExtractor force cleanup completed:")
            self.logger.info(f"  - Metrics cache cleared: {sum(cache_sizes_before.values())} entries")
            self.logger.info(f"  - Error contexts cleared: {sum(error_sizes_before.values())} entries")
            self.logger.info(f"  - File positions: {positions_before} -> {len(self._file_positions)}")
            
        except Exception as e:
            self.logger.error(f"Error during force cleanup: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get current cache statistics"""
        return {
            'metrics_cache': {
                log_type: len(entries) for log_type, entries in self._metrics_cache.items()
            },
            'error_contexts': {
                context_type: len(entries) for context_type, entries in self._error_contexts.items()
            },
            'file_positions_count': len(self._file_positions),
            'limits': {
                'max_cache_entries_per_type': self._max_cache_entries_per_type,
                'max_error_contexts_per_type': self._max_error_contexts_per_type,
                'max_file_positions': self._max_file_positions
            }
        }