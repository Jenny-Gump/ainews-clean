"""
Database operations for monitoring system
"""
import sqlite3
import time
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import json
from pathlib import Path
import traceback

try:
    from app_logging import get_logger
except ImportError:
    # Fallback logging if app_logging is not available
    import logging
    def get_logger(name):
        return logging.getLogger(name)
from .models import (
    SourceMetrics, SystemMetrics, PerformanceMetrics,
    SourceHealthReport
)


class MonitoringDatabase:
    """Database handler for monitoring data with connection pooling and performance optimizations"""
    
    def __init__(self, db_path: str):
        self.logger = get_logger('monitoring.database')
        self.db_path = db_path
        # Resolve absolute path to main database
        self.ainews_db_path = self._resolve_ainews_db_path()
        
        # FIXED: Add query caching to prevent repeated complex queries
        self._query_cache = {}
        self._cache_timeouts = {}
        self._default_cache_timeout = 30  # 30 seconds default cache
        self._max_cache_entries = 100  # Limit cache size
        
        # Performance optimization: Connection pooling
        self._connection_pool = []
        self._max_pool_size = 10
        self._pool_lock = None
        
        # Performance monitoring
        self._query_stats = {}
        self._slow_query_threshold = 1.0  # Log queries taking longer than 1 second
        
        # Log database paths for debugging
        self.logger.info(f"Monitoring DB path: {self.db_path}")
        self.logger.info(f"Main DB path: {self.ainews_db_path}")
        self.logger.info(f"Main DB exists: {Path(self.ainews_db_path).exists()}")
        # Remove articles.db reference - we only use ainews.db now
        # self.articles_db_path = str(Path(db_path).parent / "articles.db")
        try:
            # Initialize threading lock for connection pool
            import threading
            self._pool_lock = threading.Lock()
            
            self._init_database()
            self._optimize_database()
            self.logger.info(f"Monitoring database initialized at {db_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize monitoring database: {e}", exc_info=True)
            raise
    
    def _resolve_ainews_db_path(self) -> str:
        """Resolve ainews database path from any system location"""
        current_dir = Path(__file__).parent
        # Go up to find the project root (ainews-clean)
        while current_dir.name != 'ainews-clean' and current_dir.parent != current_dir:
            current_dir = current_dir.parent
        
        if current_dir.name != 'ainews-clean':
            # Fallback to relative path if we can't find ainews-clean directory
            self.logger.warning("Could not find ainews-clean root directory, using relative path")
            return str(Path(__file__).parent.parent / "data" / "ainews.db")
        
        ainews_db_path = str(current_dir / "data" / "ainews.db")
        self.logger.info(f"Resolved ainews DB path: {ainews_db_path}")
        return ainews_db_path
    
    def _init_database(self):
        """Initialize monitoring database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Performance metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cpu_usage_percent REAL,
                    memory_usage_mb REAL,
                    disk_usage_percent REAL,
                    active_connections INTEGER,
                    queue_size INTEGER,
                    parse_rate_per_minute REAL,
                    error_rate_percent REAL
                )
            """)
            
            
            # Source health reports table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS source_health_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_healthy INTEGER,
                    health_score REAL,
                    issues TEXT,
                    recommendations TEXT,
                    metrics_24h TEXT,
                    metrics_7d TEXT,
                    performance_trend TEXT
                    -- FOREIGN KEY (source_id) REFERENCES sources(source_id) -- Cross-database FK not supported
                )
            """)
            
            # Source metrics table - detailed metrics for each source
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS source_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    articles_parsed INTEGER DEFAULT 0,
                    articles_failed INTEGER DEFAULT 0,
                    avg_parse_time_ms REAL,
                    last_success_at DATETIME,
                    last_error_at DATETIME,
                    error_count_24h INTEGER DEFAULT 0,
                    success_rate_24h REAL,
                    health_score REAL
                )
            """)
            
            # Article stats table - article statistics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS article_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_articles INTEGER,
                    new_articles_24h INTEGER,
                    avg_content_length INTEGER,
                    has_full_content INTEGER,
                    parse_method TEXT,
                    api_cost REAL
                )
            """)
            
            # Error logs table - detailed error history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    error_type TEXT,
                    error_message TEXT,
                    stack_trace TEXT,
                    context TEXT,
                    correlation_id TEXT,
                    resolved INTEGER DEFAULT 0
                )
            """)
            
            # RSS feed metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rss_feed_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    source_id TEXT,
                    feed_url TEXT,
                    status TEXT,
                    articles_count INTEGER,
                    fetch_time_ms REAL,
                    error_message TEXT,
                    last_updated DATETIME
                )
            """)
            
            # Memory monitoring tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_memory_mb REAL NOT NULL,
                    used_memory_mb REAL NOT NULL,
                    available_memory_mb REAL NOT NULL,
                    processes_count INTEGER DEFAULT 0,
                    ainews_processes_count INTEGER DEFAULT 0,
                    ainews_memory_mb REAL DEFAULT 0,
                    top_consumer_memory_mb REAL DEFAULT 0
                )
            """)
            
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emergency_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_memory_mb REAL NOT NULL,
                    used_memory_mb REAL NOT NULL,
                    processes TEXT,  -- JSON array of process details
                    ainews_processes TEXT  -- JSON array of AI News processes
                )
            """)
            
            # Create indexes for existing tables
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_perf_timestamp ON performance_metrics(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_health_source ON source_health_reports(source_id)")
            
            # Create indexes for new tables
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_metrics_source ON source_metrics(source_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_metrics_timestamp ON source_metrics(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_article_stats_source ON article_stats(source_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_article_stats_timestamp ON article_stats(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_logs_source ON error_logs(source_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp ON error_logs(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_logs_type ON error_logs(error_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_logs_resolved ON error_logs(resolved)")
            
            # Create indexes for memory monitoring tables
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_metrics_timestamp ON memory_metrics(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_emergency_snapshots_timestamp ON emergency_snapshots(timestamp)")
            
            # Extract API monitoring tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS extract_api_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    url TEXT NOT NULL,
                    cost_usd REAL NOT NULL,
                    response_time_ms REAL NOT NULL,
                    success INTEGER NOT NULL,
                    content_length INTEGER DEFAULT 0,
                    error_message TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS extract_api_errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    url TEXT,
                    response_code INTEGER,
                    retry_count INTEGER DEFAULT 0
                )
            """)
            
            # Create indexes for Extract API tables
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_extract_api_metrics_timestamp ON extract_api_metrics(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_extract_api_metrics_success ON extract_api_metrics(success)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_extract_api_errors_timestamp ON extract_api_errors(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_extract_api_errors_type ON extract_api_errors(error_type)")
            
            # System metrics table for CPU/memory/process tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_percent REAL,
                    process_count INTEGER,
                    ainews_process_count INTEGER,
                    network_connections INTEGER,
                    open_files INTEGER
                )
            """)
            
            # Parsing progress table for real-time status
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parsing_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    parser_pid INTEGER,
                    status TEXT,
                    current_source TEXT,
                    total_sources INTEGER,
                    processed_sources INTEGER,
                    total_articles INTEGER,
                    progress_percent REAL,
                    estimated_completion DATETIME,
                    last_update DATETIME
                )
            """)
            
            # Create indexes for new tables
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_parsing_progress_timestamp ON parsing_progress(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_parsing_progress_pid ON parsing_progress(parser_pid)")
            
            conn.commit()
    
    def _optimize_database(self):
        """Apply database optimizations for better performance"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # SQLite performance optimizations
                cursor.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging for better concurrency
                cursor.execute("PRAGMA synchronous = NORMAL")  # Balance between safety and speed
                cursor.execute("PRAGMA cache_size = -64000")  # 64MB cache
                cursor.execute("PRAGMA temp_store = MEMORY")  # Store temp tables in memory
                cursor.execute("PRAGMA mmap_size = 268435456")  # 256MB memory map
                
                # Foreign key enforcement
                cursor.execute("PRAGMA foreign_keys = ON")
                
                # Auto-vacuum for space management
                cursor.execute("PRAGMA auto_vacuum = INCREMENTAL")
                
                conn.commit()
                self.logger.info("Database performance optimizations applied")
                
        except Exception as e:
            self.logger.warning(f"Failed to apply database optimizations: {e}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection from the pool or create new one"""
        if not self._pool_lock:
            # Fallback if threading not available
            return sqlite3.connect(self.db_path)
        
        with self._pool_lock:
            if self._connection_pool:
                return self._connection_pool.pop()
            else:
                conn = sqlite3.connect(self.db_path)
                # Apply optimizations to new connections
                conn.execute("PRAGMA journal_mode = WAL")
                conn.execute("PRAGMA synchronous = NORMAL")
                return conn
    
    def _return_connection(self, conn: sqlite3.Connection):
        """Return a connection to the pool"""
        if not self._pool_lock:
            conn.close()
            return
        
        with self._pool_lock:
            if len(self._connection_pool) < self._max_pool_size:
                self._connection_pool.append(conn)
            else:
                conn.close()
    
    def _execute_with_timing(self, query: str, params=None, db_path: str = None):
        """Execute query with performance timing"""
        start_time = time.time()
        
        try:
            db_to_use = db_path or self.db_path
            
            if db_to_use == self.db_path:
                # Use connection pool for monitoring database
                conn = self._get_connection()
                try:
                    if params:
                        cursor = conn.execute(query, params)
                    else:
                        cursor = conn.execute(query)
                    results = cursor.fetchall()
                    conn.commit()
                    return results
                finally:
                    self._return_connection(conn)
            else:
                # Direct connection for other databases
                with sqlite3.connect(db_to_use) as conn:
                    if params:
                        cursor = conn.execute(query, params)
                    else:
                        cursor = conn.execute(query)
                    results = cursor.fetchall()
                    return results
            
        finally:
            elapsed = time.time() - start_time
            
            # Track query performance
            query_key = query.split()[0].upper()  # SELECT, INSERT, UPDATE, etc.
            if query_key not in self._query_stats:
                self._query_stats[query_key] = {'count': 0, 'total_time': 0, 'max_time': 0}
            
            stats = self._query_stats[query_key]
            stats['count'] += 1
            stats['total_time'] += elapsed
            stats['max_time'] = max(stats['max_time'], elapsed)
            
            # Log slow queries
            if elapsed > self._slow_query_threshold:
                self.logger.warning(f"Slow query ({elapsed:.2f}s): {query[:100]}...")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics"""
        stats = {
            'query_stats': dict(self._query_stats),
            'cache_stats': {
                'cache_entries': len(self._query_cache),
                'max_cache_entries': self._max_cache_entries,
                'cache_timeout': self._default_cache_timeout
            },
            'connection_pool': {
                'pool_size': len(self._connection_pool),
                'max_pool_size': self._max_pool_size
            }
        }
        
        # Calculate averages
        for query_type, query_stats in stats['query_stats'].items():
            if query_stats['count'] > 0:
                query_stats['avg_time'] = query_stats['total_time'] / query_stats['count']
        
        return stats
    
    def _get_cached_result(self, cache_key: str, timeout_seconds: int = None):
        """Get cached result if still valid"""
        if timeout_seconds is None:
            timeout_seconds = self._default_cache_timeout
        
        if cache_key in self._query_cache:
            cache_time = self._cache_timeouts.get(cache_key, 0)
            if time.time() - cache_time < timeout_seconds:
                return self._query_cache[cache_key]
        
        return None
    
    def _cache_result(self, cache_key: str, result: Any):
        """Cache query result with cleanup"""
        # Clean up old cache entries if too many
        if len(self._query_cache) >= self._max_cache_entries:
            self._cleanup_old_cache()
        
        self._query_cache[cache_key] = result
        self._cache_timeouts[cache_key] = time.time()
    
    def _cleanup_old_cache(self):
        """Clean up old cache entries"""
        try:
            current_time = time.time()
            expired_keys = [
                key for key, cache_time in self._cache_timeouts.items()
                if current_time - cache_time > self._default_cache_timeout
            ]
            
            for key in expired_keys:
                if key in self._query_cache:
                    del self._query_cache[key]
                if key in self._cache_timeouts:
                    del self._cache_timeouts[key]
            
            # If still too many, remove oldest 20%
            if len(self._query_cache) >= self._max_cache_entries:
                sorted_cache = sorted(
                    self._cache_timeouts.items(),
                    key=lambda x: x[1]
                )
                
                num_to_remove = len(self._query_cache) // 5
                for key, _ in sorted_cache[:num_to_remove]:
                    if key in self._query_cache:
                        del self._query_cache[key]
                    if key in self._cache_timeouts:
                        del self._cache_timeouts[key]
                        
            self.logger.debug(f"Cache cleanup: {len(expired_keys)} expired, {len(self._query_cache)} remaining")
                        
        except Exception as e:
            self.logger.error(f"Error during cache cleanup: {e}")
    
    def clear_cache(self):
        """Clear all cached query results - called by memory monitor"""
        try:
            cache_size_before = len(self._query_cache)
            self._query_cache.clear()
            self._cache_timeouts.clear()
            self.logger.info(f"Database cache cleared: {cache_size_before} cached queries")
        except Exception as e:
            self.logger.error(f"Error clearing database cache: {e}")
    
    def get_source_metrics(self, source_id: Optional[str] = None) -> List[SourceMetrics]:
        """Get metrics for sources"""
        with sqlite3.connect(self.ainews_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    s.source_id,
                    s.name,
                    s.url,
                    s.type,
                    s.has_rss,
                    s.last_status,
                    s.last_error,
                    s.success_rate,
                    s.last_parsed,
                    s.total_articles,
                    COUNT(DISTINCT a24.article_id) as recent_articles_24h,
                    COUNT(DISTINCT CASE WHEN a24.content_status = 'failed' THEN a24.article_id END) as recent_errors_24h,
                    AVG(CASE 
                        WHEN a24.parsed_at IS NOT NULL AND a24.created_at IS NOT NULL 
                        AND (julianday(a24.parsed_at) - julianday(a24.created_at)) * 86400000 BETWEEN 0 AND 300000
                        THEN (julianday(a24.parsed_at) - julianday(a24.created_at)) * 86400000 
                        ELSE NULL 
                    END) as avg_parse_time_ms
                FROM sources s
                -- Добавляем join с таблицей базы данных articles для подсчета статуса
                LEFT JOIN articles a24 ON s.source_id = a24.source_id 
                    AND a24.created_at >= datetime('now', '-24 hours')
            """
            
            if source_id:
                query += " WHERE s.source_id = ?"
                cursor.execute(query + " GROUP BY s.source_id", (source_id,))
            else:
                cursor.execute(query + " GROUP BY s.source_id")
            
            metrics = []
            for row in cursor.fetchall():
                # Simplified health calculation (removed complex scoring)
                health_score = 100 if row["last_status"] == "active" else 50
                
                metrics.append(SourceMetrics(
                    source_id=row['source_id'],
                    name=row['name'],
                    url=row['url'],
                    type=row['type'],
                    has_rss=bool(row['has_rss']),
                    last_status=row['last_status'],
                    last_error=row['last_error'],
                    success_rate=row['success_rate'] or 0.0,
                    last_parsed=datetime.fromisoformat(row['last_parsed']) if row['last_parsed'] else None,
                    total_articles=row['total_articles'] or 0,
                    recent_articles_24h=row['recent_articles_24h'] or 0,
                    recent_errors_24h=row['recent_errors_24h'] or 0,
                    avg_parse_time_ms=row['avg_parse_time_ms'] or 0.0,
                    health_score=health_score
                ))
            
            return metrics
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get overall system metrics"""
        # FIXED: Add caching to prevent frequent DB calls (dashboard calls this every few seconds)
        cache_key = "system_metrics"
        cached_result = self._get_cached_result(cache_key, timeout_seconds=10)  # Cache for 10 seconds
        if cached_result is not None:
            return cached_result
            
        with sqlite3.connect(self.ainews_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get source statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_sources,
                    COUNT(CASE WHEN last_status = 'active' THEN 1 END) as active_sources,
                    COUNT(CASE WHEN last_status = 'error' THEN 1 END) as error_sources,
                    COUNT(CASE WHEN last_status = 'blocked' THEN 1 END) as blocked_sources
                FROM sources
            """)
            source_stats = cursor.fetchone()
            
        # Get active sources count from main monitoring DB 
        main_monitoring_db = os.path.join(os.path.dirname(self.db_path), '..', 'data', 'monitoring.db')
        with sqlite3.connect(main_monitoring_db) as mon_conn:
            mon_cursor = mon_conn.cursor()
            mon_cursor.execute("""
                SELECT COUNT(DISTINCT source_id) 
                FROM source_metrics 
                WHERE timestamp >= datetime('now', '-24 hours')
            """)
            active_count = mon_cursor.fetchone()[0]
            self.logger.debug(f"Active sources from monitoring DB: {active_count}, DB path: {main_monitoring_db}")
        
        # Get article statistics from ainews.db
        with sqlite3.connect(self.ainews_db_path) as art_conn:
            art_cursor = art_conn.cursor()
            
            # Convert tuple to list to modify
            source_stats_list = list(source_stats)
            source_stats_list[1] = active_count  # Update active_sources count
            
            art_cursor.execute("""
                SELECT 
                    COUNT(*) as total_articles,
                    COUNT(CASE WHEN created_at >= datetime('now', '-24 hours') THEN 1 END) as articles_24h,
                    COUNT(CASE WHEN created_at >= datetime('now', '-7 days') THEN 1 END) as articles_7d
                FROM articles
            """)
            article_stats = art_cursor.fetchone()
            
            # Get media statistics
            art_cursor.execute("""
                SELECT 
                    COUNT(*) as total_media_files,
                    COUNT(CASE WHEN status = 'downloaded' THEN 1 END) as media_downloaded,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as media_failed
                FROM media_files
            """)
            media_stats = art_cursor.fetchone()
            
            # Get performance statistics - use actual parse times from monitoring DB instead of time difference
            perf_stats = (0.0,)  # Default value
            try:
                # Get average parse time from monitoring database
                with sqlite3.connect(self.db_path) as monitoring_conn:
                    monitoring_cursor = monitoring_conn.cursor()
                    monitoring_cursor.execute("""
                        SELECT AVG(avg_parse_time_ms) as avg_parse_time_ms
                        FROM source_metrics 
                        WHERE avg_parse_time_ms IS NOT NULL 
                        AND avg_parse_time_ms > 0 
                        AND avg_parse_time_ms <= 300000
                        AND timestamp >= datetime('now', '-24 hours')
                    """)
                    monitoring_result = monitoring_cursor.fetchone()
                    if monitoring_result and monitoring_result[0]:
                        perf_stats = (monitoring_result[0],)
            except Exception as e:
                self.logger.warning(f"Could not get monitoring parse times: {e}")
                # Fallback to a reasonable default rather than the incorrect time difference
                perf_stats = (5000.0,)  # 5 seconds default
            
            # Get database size
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()
            
            result = SystemMetrics(
                total_sources=source_stats_list[0],  # total_sources
                active_sources=source_stats_list[1],  # active_sources (updated)
                error_sources=source_stats_list[2],   # error_sources
                blocked_sources=source_stats_list[3], # blocked_sources
                total_articles=article_stats[0],      # total_articles
                articles_24h=article_stats[1],        # articles_24h
                articles_7d=article_stats[2],         # articles_7d
                total_media_files=media_stats[0],     # total_media_files
                media_downloaded=media_stats[1],      # media_downloaded
                media_failed=media_stats[2],          # media_failed
                avg_article_parse_time_ms=perf_stats[0] or 0.0 if perf_stats else 0.0,
                avg_media_download_time_ms=0.0,  # Media timing tracking disabled
                database_size_mb=db_size[0] / 1024 / 1024 if db_size else 0.0,  # Convert to MB
                last_update=datetime.now()
            )
            
            # Cache the result
            self._cache_result(cache_key, result)
            return result
    
    def get_source_activity_timeline(self, source_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get source activity timeline"""
        with sqlite3.connect(self.ainews_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as articles_count,
                    COUNT(CASE WHEN content_status = 'completed' THEN 1 END) as successful,
                    COUNT(CASE WHEN content_status = 'failed' THEN 1 END) as failed,
                    AVG(CASE 
                        WHEN parsed_at IS NOT NULL AND created_at IS NOT NULL 
                        AND (julianday(parsed_at) - julianday(created_at)) * 86400000 BETWEEN 0 AND 300000
                        THEN (julianday(parsed_at) - julianday(created_at)) * 86400000 
                        ELSE NULL 
                    END) as avg_parse_time_ms
                FROM articles
                WHERE source_id = ?
                    AND created_at >= datetime('now', ? || ' days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """, (source_id, -days))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period"""
        with sqlite3.connect(self.ainews_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get source errors
            cursor.execute("""
                SELECT 
                    last_status,
                    last_error,
                    COUNT(*) as count
                FROM sources
                WHERE last_status IN ('error', 'blocked', 'not_found')
                    AND last_parsed >= datetime('now', ? || ' hours')
                GROUP BY last_status, last_error
                ORDER BY count DESC
            """, (-hours,))
            source_errors = [dict(row) for row in cursor.fetchall()]
            
            # Get article parsing errors
            cursor.execute("""
                SELECT 
                    content_error,
                    COUNT(*) as count,
                    COUNT(DISTINCT source_id) as affected_sources
                FROM articles
                WHERE content_status = 'failed'
                    AND created_at >= datetime('now', ? || ' hours')
                    AND content_error IS NOT NULL
                GROUP BY content_error
                ORDER BY count DESC
                LIMIT 10
            """, (-hours,))
            article_errors = [dict(row) for row in cursor.fetchall()]
            
            # Get media download errors
            cursor.execute("""
                SELECT 
                    error,
                    COUNT(*) as count,
                    COUNT(DISTINCT source_id) as affected_sources
                FROM media_files
                WHERE status = 'failed'
                    AND created_at >= datetime('now', ? || ' hours')
                    AND error IS NOT NULL
                GROUP BY error
                ORDER BY count DESC
                LIMIT 10
            """, (-hours,))
            media_errors = [dict(row) for row in cursor.fetchall()]
            
            return {
                'source_errors': source_errors,
                'article_errors': article_errors,
                'media_errors': media_errors,
                'summary': {
                    'total_source_errors': sum(e['count'] for e in source_errors),
                    'total_article_errors': sum(e['count'] for e in article_errors),
                    'total_media_errors': sum(e['count'] for e in media_errors)
                }
            }
    
    def save_performance_metrics(self, metrics: PerformanceMetrics):
        """Save performance metrics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO performance_metrics (
                    timestamp, cpu_usage_percent, memory_usage_mb,
                    disk_usage_percent, active_connections, queue_size,
                    parse_rate_per_minute, error_rate_percent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.timestamp,
                metrics.cpu_usage_percent,
                metrics.memory_usage_mb,
                metrics.disk_usage_percent,
                metrics.active_connections,
                metrics.queue_size,
                metrics.parse_rate_per_minute,
                metrics.error_rate_percent
            ))
            conn.commit()
    
    
    def get_source_articles(self, source_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent articles for a source"""
        with sqlite3.connect(self.ainews_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    article_id,
                    title,
                    description,
                    content,
                    url,
                    published_date,
                    content_status,
                    created_at
                FROM articles
                WHERE source_id = ?
                ORDER BY published_date DESC
                LIMIT ?
            """, (source_id, limit))
            
            articles = []
            for row in cursor.fetchall():
                # Determine what content to show based on availability
                content = row[3]  # Full content from DB
                description = row[2]  # RSS description
                
                # Show content priority: full content > description > fallback message
                if content and len(content.strip()) > 50:
                    display_content = content
                    content_source = "Полный текст статьи"
                elif description and len(description.strip()) > 0:
                    display_content = description
                    content_source = "Описание из RSS (полный текст не загружен)"
                else:
                    display_content = "Контент недоступен - только заголовок из RSS-ленты"
                    content_source = "Только заголовок"
                
                articles.append({
                    'article_id': row[0],
                    'title': row[1],
                    'description': description,
                    'full_content': display_content,
                    'content_source': content_source,
                    'content_status': row[6],
                    'url': row[4],
                    'published_date': row[5],
                    'created_at': row[7],
                    'author': ''  # Not tracked in current schema
                })
            
            return articles
    
    def get_source_metrics_detailed(self) -> List[Dict[str, Any]]:
        """CACHED: Get detailed metrics for all sources including performance trends"""
        # FIXED: Check cache first (this query is called every 5 seconds!)
        cache_key = "source_metrics_detailed"
        cached_result = self._get_cached_result(cache_key, timeout_seconds=30)
        if cached_result is not None:
            return cached_result
        
        with sqlite3.connect(self.ainews_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get basic source metrics with enhanced data
            query = """
                SELECT 
                    s.source_id,
                    s.name,
                    s.url,
                    s.type,
                    s.has_rss,
                    s.last_status,
                    s.last_error,
                    s.success_rate,
                    s.last_parsed,
                    s.total_articles,
                    s.consecutive_failures,
                    -- 24 hour metrics
                    COUNT(DISTINCT a24.article_id) as recent_articles_24h,
                    COUNT(DISTINCT CASE WHEN a24.content_status = 'failed' THEN a24.article_id END) as recent_errors_24h,
                    COUNT(DISTINCT a24.article_id) as total_attempts_24h,
                    AVG(CASE 
                        WHEN a24.parsed_at IS NOT NULL AND a24.created_at IS NOT NULL 
                        AND (julianday(a24.parsed_at) - julianday(a24.created_at)) * 86400000 BETWEEN 0 AND 300000
                        THEN (julianday(a24.parsed_at) - julianday(a24.created_at)) * 86400000 
                        ELSE NULL 
                    END) as avg_parse_time_ms,
                    -- Content quality metrics
                    AVG(LENGTH(a24.content)) as avg_content_length,
                    AVG(CASE WHEN a24.content IS NOT NULL AND LENGTH(a24.content) > 100 THEN 1.0 ELSE 0.0 END) * 100 as full_content_rate,
                    -- Media metrics
                    COUNT(DISTINCT m.media_id) as total_media,
                    COUNT(DISTINCT CASE WHEN m.status = 'downloaded' THEN m.media_id END) as media_downloaded,
                    (COUNT(DISTINCT CASE WHEN m.status = 'downloaded' THEN m.media_id END) * 100.0 / 
                     NULLIF(COUNT(DISTINCT m.media_id), 0)) as media_success_rate
                FROM sources s
                LEFT JOIN articles a24 ON s.source_id = a24.source_id 
                    AND a24.created_at >= datetime('now', '-24 hours')
                LEFT JOIN media_files m ON a24.article_id = m.article_id
                GROUP BY s.source_id
            """
            
            cursor.execute(query)
            
            results = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                
                # Calculate performance trend
                row_dict['performance_trend'] = self._calculate_performance_trend(row_dict['source_id'])
                
                # Parse datetime if needed
                if row_dict['last_parsed'] and isinstance(row_dict['last_parsed'], str):
                    row_dict['last_parsed'] = datetime.fromisoformat(row_dict['last_parsed'].replace('Z', '+00:00'))
                
                results.append(row_dict)
            
            # FIXED: Cache the expensive query result
            self._cache_result(cache_key, results)
            return results
    
    def _calculate_performance_trend(self, source_id: str) -> str:
        """Calculate if performance is improving, stable, or degrading"""
        with sqlite3.connect(self.ainews_db_path) as conn:
            cursor = conn.cursor()
            
            # Get historical success rates
            cursor.execute("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(CASE WHEN content_status = 'completed' THEN 1 END) * 100.0 / COUNT(*) as success_rate
                FROM articles
                WHERE source_id = ? AND created_at >= datetime('now', '-7 days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """, (source_id,))
            
            rates = [row[1] for row in cursor.fetchall()]
            
            if len(rates) < 3:
                return "stable"
            
            # Simple trend analysis
            recent_avg = sum(rates[:3]) / 3
            older_avg = sum(rates[3:]) / len(rates[3:]) if len(rates) > 3 else recent_avg
            
            if recent_avg > older_avg + 10:
                return "improving"
            elif recent_avg < older_avg - 10:
                return "degrading"
            else:
                return "stable"
    
    def update_source_metrics(self, source_id: str, **kwargs):
        """Update source metrics in monitoring database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert new metrics record
            cursor.execute("""
                INSERT INTO source_metrics (
                    source_id, articles_parsed, articles_failed, 
                    avg_parse_time_ms, last_success_at, success_rate_24h
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                source_id,
                kwargs.get('articles_parsed', 0),
                kwargs.get('articles_failed', 0),
                kwargs.get('avg_parse_time_ms', 0),
                datetime.now() if kwargs.get('articles_parsed', 0) > 0 else None,
                kwargs.get('success_rate', 0)
            ))
            
            conn.commit()
    
    # REMOVED: Complex health score update method - now using simple calculation
    
    # REMOVED: Complex health score calculation - using simple status-based calculation instead
    
    def get_sources_by_error_count(self, hours: int = 24, limit: int = 10) -> List[SourceMetrics]:
        """Get sources sorted by error count for the specified time period"""
        # Simply return the top error sources from existing source metrics
        all_sources = self.get_source_metrics()
        
        # Sort by recent errors count (descending) and filter out sources with 0 errors
        sources_with_errors = [s for s in all_sources if s.recent_errors_24h > 0]
        sources_with_errors.sort(key=lambda s: s.recent_errors_24h, reverse=True)
        
        return sources_with_errors[:limit]
    
    # Methods for new tables
    
    def save_source_metrics(self, metrics: Dict[str, Any]):
        """Save source metrics to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO source_metrics (
                    source_id, articles_parsed, articles_failed,
                    avg_parse_time_ms, last_success_at, last_error_at,
                    error_count_24h, success_rate_24h, health_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics['source_id'],
                metrics.get('articles_parsed', 0),
                metrics.get('articles_failed', 0),
                metrics.get('avg_parse_time_ms'),
                metrics.get('last_success_at'),
                metrics.get('last_error_at'),
                metrics.get('error_count_24h', 0),
                metrics.get('success_rate_24h'),
                metrics.get('health_score')
            ))
            conn.commit()
    
    # REMOVED: save_article_stats method - api_cost tracking not needed
    
    def log_error(self, error_info: Dict[str, Any]):
        """Log an error to the error_logs table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO error_logs (
                    source_id, error_type, error_message,
                    stack_trace, context, correlation_id
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                error_info.get('source_id'),
                error_info.get('error_type', 'unknown'),
                error_info.get('error_message', ''),
                error_info.get('stack_trace', traceback.format_exc()),
                json.dumps(error_info.get('context', {})),
                error_info.get('correlation_id')
            ))
            conn.commit()
    
    def get_recent_error_logs(self, source_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent error logs, optionally filtered by source"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM error_logs
                WHERE 1=1
            """
            params = []
            
            if source_id:
                query += " AND source_id = ?"
                params.append(source_id)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_source_metrics_history(self, source_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical metrics for a source"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM source_metrics
                WHERE source_id = ?
                    AND timestamp >= datetime('now', ? || ' hours')
                ORDER BY timestamp DESC
            """, (source_id, -hours))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # REMOVED: get_article_stats_summary method - api_cost tracking not needed
    
    # Memory monitoring methods
    def save_memory_metrics(self, metrics_data: Dict[str, Any]):
        """Save memory metrics to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO memory_metrics (
                        timestamp, total_memory_mb, used_memory_mb, available_memory_mb,
                        processes_count, ainews_processes_count, ainews_memory_mb,
                        top_consumer_memory_mb
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics_data['timestamp'],
                    metrics_data['total_memory_mb'],
                    metrics_data['used_memory_mb'],
                    metrics_data['available_memory_mb'],
                    metrics_data['processes_count'],
                    metrics_data['ainews_processes_count'],
                    metrics_data['ainews_memory_mb'],
                    metrics_data['top_consumer_memory_mb']
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error saving memory metrics: {e}")
    
    
    def save_emergency_snapshot(self, snapshot_data: Dict[str, Any]):
        """Save emergency memory snapshot"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO emergency_snapshots (
                        timestamp, total_memory_mb, used_memory_mb,
                        processes, ainews_processes
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    snapshot_data['timestamp'],
                    snapshot_data['total_memory_mb'],
                    snapshot_data['used_memory_mb'],
                    json.dumps(snapshot_data['processes']),
                    json.dumps(snapshot_data['ainews_processes'])
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error saving emergency snapshot: {e}")
    
    def get_memory_metrics_history(self, hours: int = 2) -> List[Dict[str, Any]]:
        """Get memory metrics history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM memory_metrics
                    WHERE timestamp >= datetime('now', ? || ' hours')
                    ORDER BY timestamp DESC
                    LIMIT 1000
                """, (-hours,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting memory metrics history: {e}")
            return []
    
    
    def get_latest_memory_info(self) -> Optional[Dict[str, Any]]:
        """Get latest memory information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM memory_metrics
                    ORDER BY timestamp DESC
                    LIMIT 1
                """)
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"Error getting latest memory info: {e}")
            return None
    
    def execute_query(self, query: str, params=None):
        """Execute a query and return results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if params:
                    cursor = conn.execute(query, params)
                else:
                    cursor = conn.execute(query)
                
                results = cursor.fetchall()
                return results
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            raise
    
    def cleanup_old_memory_data(self, days: int = 7):
        """Clean up old memory monitoring data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clean up old memory metrics (keep only last 7 days)
                cursor.execute("""
                    DELETE FROM memory_metrics
                    WHERE timestamp < datetime('now', ? || ' days')
                """, (-days,))
                
                
                # Clean up emergency snapshots older than 30 days
                cursor.execute("""
                    DELETE FROM emergency_snapshots
                    WHERE timestamp < datetime('now', '-30 days')
                """)
                
                conn.commit()
                deleted_metrics = cursor.rowcount
                self.logger.info(f"Cleaned up {deleted_metrics} old memory records")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old memory data: {e}")
    
    def cleanup_old_data(self, retention_days: Optional[Dict[str, int]] = None):
        """Clean up old data from all monitoring tables
        
        Args:
            retention_days: Dict with table-specific retention policies.
                           Defaults: system_metrics=7, parsing_progress=1, 
                           performance_metrics=30, source_metrics=30, etc.
        """
        if retention_days is None:
            retention_days = {
                'system_metrics': 7,
                'parsing_progress': 1,  # Only keep 24 hours
                'performance_metrics': 30,
                'source_metrics': 30,
                'article_stats': 30,
                'error_logs': 30,
                'rss_feed_metrics': 7,
                'memory_metrics': 7,
                'emergency_snapshots': 30
            }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                total_deleted = 0
                
                for table, days in retention_days.items():
                    try:
                        # Special handling for tables with 'resolved' column
                        if table in ['error_logs']:
                            cursor.execute(f"""
                                DELETE FROM {table}
                                WHERE timestamp < datetime('now', ? || ' days')
                                AND (resolved = 1 OR resolved IS NULL)
                            """, (-days,))
                        else:
                            cursor.execute(f"""
                                DELETE FROM {table}
                                WHERE timestamp < datetime('now', ? || ' days')
                            """, (-days,))
                        
                        deleted = cursor.rowcount
                        total_deleted += deleted
                        if deleted > 0:
                            self.logger.info(f"Cleaned up {deleted} records from {table}")
                    
                    except sqlite3.OperationalError as e:
                        # Table might not exist
                        self.logger.debug(f"Skipping cleanup for {table}: {e}")
                        continue
                
                # VACUUM to reclaim space after deletions
                if total_deleted > 1000:
                    cursor.execute("VACUUM")
                    self.logger.info("Database vacuumed after cleanup")
                
                conn.commit()
                self.logger.info(f"Total cleanup: {total_deleted} records deleted")
                
        except Exception as e:
            self.logger.error(f"Error during data cleanup: {e}", exc_info=True)
    
    def create_backup(self, backup_dir: str = None) -> Optional[str]:
        """Create a backup of the monitoring database
        
        Args:
            backup_dir: Directory to save backup. Defaults to ./backups/
            
        Returns:
            Path to backup file if successful, None otherwise
        """
        try:
            if backup_dir is None:
                backup_dir = os.path.join(os.path.dirname(self.db_path), 'backups')
            
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f'monitoring_{timestamp}.db')
            
            # Use SQLite backup API
            with sqlite3.connect(self.db_path) as source:
                with sqlite3.connect(backup_path) as dest:
                    source.backup(dest)
            
            # Verify backup
            with sqlite3.connect(backup_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                
            file_size = os.path.getsize(backup_path) / 1024 / 1024  # MB
            self.logger.info(f"Backup created: {backup_path} ({file_size:.2f} MB, {table_count} tables)")
            
            # Clean up old backups (keep last 7)
            self._cleanup_old_backups(backup_dir, keep_count=7)
            
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}", exc_info=True)
            return None
    
    def _cleanup_old_backups(self, backup_dir: str, keep_count: int = 7):
        """Keep only the most recent backups"""
        try:
            backup_files = sorted([
                f for f in os.listdir(backup_dir) 
                if f.startswith('monitoring_') and f.endswith('.db')
            ])
            
            if len(backup_files) > keep_count:
                for old_backup in backup_files[:-keep_count]:
                    old_path = os.path.join(backup_dir, old_backup)
                    os.remove(old_path)
                    self.logger.debug(f"Removed old backup: {old_backup}")
                    
        except Exception as e:
            self.logger.warning(f"Error cleaning old backups: {e}")
    
    def save_system_metrics(self, metrics: Dict[str, Any]):
        """Save system-wide metrics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO system_metrics (
                        timestamp, cpu_percent, memory_percent, disk_percent,
                        process_count, ainews_process_count, network_connections, open_files
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.get('timestamp', datetime.now()),
                    metrics.get('cpu_percent'),
                    metrics.get('memory_percent'),
                    metrics.get('disk_percent'),
                    metrics.get('process_count'),
                    metrics.get('ainews_process_count'),
                    metrics.get('network_connections'),
                    metrics.get('open_files')
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error saving system metrics: {e}")
    
    def save_parsing_progress(self, progress: Dict[str, Any]):
        """Save parsing progress"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO parsing_progress (
                        timestamp, parser_pid, status, current_source,
                        total_sources, processed_sources, total_articles,
                        progress_percent, estimated_completion, last_update
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    progress.get('timestamp', datetime.now()),
                    progress.get('parser_pid'),
                    progress.get('status'),
                    progress.get('current_source'),
                    progress.get('total_sources'),
                    progress.get('processed_sources'),
                    progress.get('total_articles'),
                    progress.get('progress_percent'),
                    progress.get('estimated_completion'),
                    progress.get('last_update', datetime.now())
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error saving parsing progress: {e}")
    
    def get_latest_parsing_progress(self) -> Optional[Dict[str, Any]]:
        """Get the latest parsing progress"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM parsing_progress
                    ORDER BY timestamp DESC
                    LIMIT 1
                """)
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"Error getting parsing progress: {e}")
            return None
    
    def get_system_resources(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get system resource history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM system_metrics
                    WHERE timestamp >= datetime('now', ? || ' hours')
                    ORDER BY timestamp DESC
                """, (-hours,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting system resources: {e}")
            return []
    
    def get_memory_metrics_history(self, hours: float = 1) -> List[Dict[str, Any]]:
        """Get memory metrics history for analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        timestamp,
                        used_memory_mb,
                        available_memory_mb,
                        total_memory_mb,
                        alert_level
                    FROM memory_metrics
                    WHERE timestamp >= datetime('now', ? || ' hours')
                    ORDER BY timestamp DESC
                """, (-hours,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting memory metrics history: {e}")
            return []
    
    # Extract API monitoring methods
    def save_extract_api_metrics(self, metrics_data: Dict[str, Any]):
        """Save Extract API metrics to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO extract_api_metrics (
                        timestamp, url, cost_usd, response_time_ms,
                        success, content_length, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics_data['timestamp'],
                    metrics_data['url'],
                    metrics_data['cost_usd'],
                    metrics_data['response_time_ms'],
                    1 if metrics_data['success'] else 0,
                    metrics_data.get('content_length', 0),
                    metrics_data.get('error_message')
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error saving Extract API metrics: {e}")
    
    def log_extract_api_error(self, error_data: Dict[str, Any]):
        """Log Extract API error to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO extract_api_errors (
                        timestamp, error_type, error_message, url,
                        response_code, retry_count
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    error_data['timestamp'],
                    error_data['error_type'],
                    error_data['error_message'],
                    error_data.get('url'),
                    error_data.get('response_code'),
                    error_data.get('retry_count', 0)
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error logging Extract API error: {e}")
    
    def get_extract_api_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get Extract API usage summary"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get metrics summary
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_requests,
                        SUM(cost_usd) as total_cost,
                        AVG(cost_usd) as avg_cost_per_request,
                        AVG(response_time_ms) as avg_response_time,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests,
                        AVG(content_length) as avg_content_length
                    FROM extract_api_metrics
                    WHERE timestamp >= datetime('now', ? || ' hours')
                """, (-hours,))
                
                metrics = cursor.fetchone()
                
                # Get error summary
                cursor.execute("""
                    SELECT 
                        error_type,
                        COUNT(*) as count
                    FROM extract_api_errors
                    WHERE timestamp >= datetime('now', ? || ' hours')
                    GROUP BY error_type
                    ORDER BY count DESC
                """, (-hours,))
                
                errors = [dict(row) for row in cursor.fetchall()]
                
                if metrics and metrics['total_requests']:
                    success_rate = (metrics['successful_requests'] / metrics['total_requests']) * 100
                else:
                    success_rate = 0.0
                
                return {
                    'total_requests': metrics['total_requests'] or 0,
                    'total_cost_usd': round(metrics['total_cost'] or 0, 4),
                    'avg_cost_per_request': round(metrics['avg_cost_per_request'] or 0, 4),
                    'avg_response_time_ms': round(metrics['avg_response_time'] or 0, 1),
                    'success_rate_percent': round(success_rate, 1),
                    'avg_content_length': round(metrics['avg_content_length'] or 0, 0),
                    'error_breakdown': errors,
                    'total_errors': sum(e['count'] for e in errors)
                }
                
        except Exception as e:
            self.logger.error(f"Error getting Extract API summary: {e}")
            return {
                'total_requests': 0,
                'total_cost_usd': 0.0,
                'avg_cost_per_request': 0.0,
                'avg_response_time_ms': 0.0,
                'success_rate_percent': 0.0,
                'avg_content_length': 0,
                'error_breakdown': [],
                'total_errors': 0
            }
    
    def get_extract_api_cost_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get Extract API cost history for charting"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        datetime(timestamp, 'localtime') as hour,
                        SUM(cost_usd) as hourly_cost,
                        COUNT(*) as hourly_requests,
                        AVG(response_time_ms) as avg_response_time
                    FROM extract_api_metrics
                    WHERE timestamp >= datetime('now', ? || ' hours')
                    GROUP BY datetime(timestamp, 'localtime', 'start of hour')
                    ORDER BY hour DESC
                """, (-hours,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Error getting Extract API cost history: {e}")
            return []