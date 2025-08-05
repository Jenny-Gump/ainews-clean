"""
Automation engine for AI News Parser monitoring
Handles automatic recovery, optimization, and maintenance tasks
"""
import asyncio
import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from app_logging import get_logger

from .database import MonitoringDatabase
from .models import SourceMetrics


class AutomationEngine:
    """Handles automated recovery and optimization tasks"""
    
    def __init__(self, db: MonitoringDatabase, alert_manager=None):
        self.logger = get_logger("monitoring.automation")
        self.db = db
        self.scheduler = AsyncIOScheduler()
        
        # Track automation state
        self.disabled_sources: Set[str] = set()
        self.recovery_attempts: Dict[str, int] = {}
        self.last_optimization = datetime.now()
        
        # Configuration
        self.config = {
            'auto_disable': {
                'enabled': True,
                'consecutive_failures': 10,
                'error_rate_threshold': 90,
                'cooldown_hours': 24
            },
            'auto_recovery': {
                'enabled': True,
                'retry_interval_minutes': 60,
                'max_retries': 3,
                'recovery_check_hours': 6
            },
            'log_cleanup': {
                'enabled': True,
                'retention_days': 30,
                'max_log_size_mb': 1000,
                'archive_old_logs': True
            },
            'optimization': {
                'enabled': True,
                'database_vacuum_days': 7,
                'index_rebuild_days': 30,
                'stats_cleanup_days': 90
            }
        }
        
        self._setup_scheduled_tasks()
        self.logger.info("Automation engine initialized")
    
    def _setup_scheduled_tasks(self):
        """Set up scheduled automation tasks"""
        # Recovery check every 6 hours
        self.scheduler.add_job(
            self.check_source_recovery,
            IntervalTrigger(hours=6),
            id='source_recovery_check',
            name='Check disabled sources for recovery'
        )
        
        # Log cleanup daily at 3 AM
        self.scheduler.add_job(
            self.cleanup_logs,
            CronTrigger(hour=3, minute=0),
            id='log_cleanup',
            name='Clean up old logs'
        )
        
        # Database optimization weekly on Sunday at 2 AM
        self.scheduler.add_job(
            self.optimize_database,
            CronTrigger(day_of_week=6, hour=2, minute=0),
            id='database_optimization',
            name='Optimize database'
        )
        
        # Performance optimization check every 4 hours
        self.scheduler.add_job(
            self.check_performance_optimization,
            IntervalTrigger(hours=4),
            id='performance_optimization',
            name='Check and apply performance optimizations'
        )
        
        self.logger.info("Scheduled tasks configured")
    
    async def start(self):
        """Start the automation engine"""
        self.scheduler.start()
        self.logger.info("Automation engine started")
    
    async def stop(self):
        """Stop the automation engine"""
        self.scheduler.shutdown()
        self.logger.info("Automation engine stopped")
    
    # Alert handling removed - no longer using alert system
    
    # Alert-based methods removed - no longer using alert system
    
    
    
    
    
    async def _disable_source(self, source_id: str, temporary: bool = False):
        """Disable a source"""
        try:
            with sqlite3.connect(self.db.ainews_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE sources 
                    SET last_status = 'blocked',
                        last_error = 'Auto-disabled by monitoring system',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE source_id = ?
                """, (source_id,))
                conn.commit()
                
                self.logger.info(f"Source {source_id} disabled {'temporarily' if temporary else 'permanently'}")
        except Exception as e:
            self.logger.error(f"Failed to disable source {source_id}: {e}")
    
    async def _enable_source(self, source_id: str):
        """Re-enable a source"""
        try:
            with sqlite3.connect(self.db.ainews_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE sources 
                    SET last_status = 'active',
                        last_error = NULL,
                        consecutive_failures = 0,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE source_id = ?
                """, (source_id,))
                conn.commit()
                
                self.disabled_sources.discard(source_id)
                self.logger.info(f"Source {source_id} re-enabled")
                
                # Alerting system removed
        except Exception as e:
            self.logger.error(f"Failed to enable source {source_id}: {e}")
    
    async def check_source_recovery(self):
        """Check if disabled sources can be recovered"""
        if not self.config['auto_recovery']['enabled']:
            return
        
        self.logger.info("Checking disabled sources for recovery")
        
        for source_id in list(self.disabled_sources):
            attempts = self.recovery_attempts.get(source_id, 0)
            max_retries = self.config['auto_recovery']['max_retries']
            
            if attempts >= max_retries:
                self.logger.info(f"Source {source_id} exceeded max recovery attempts ({max_retries})")
                continue
            
            # Try to test the source
            if await self._test_source(source_id):
                self.logger.info(f"Source {source_id} appears healthy, re-enabling")
                await self._enable_source(source_id)
                self.recovery_attempts.pop(source_id, None)
            else:
                self.recovery_attempts[source_id] = attempts + 1
                self.logger.info(f"Source {source_id} still unhealthy, attempt {attempts + 1}/{max_retries}")
    
    async def _test_source(self, source_id: str) -> bool:
        """Test if a source is healthy"""
        # Simple implementation - could be enhanced with actual source testing
        try:
            with sqlite3.connect(self.db.ainews_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT url, type FROM sources WHERE source_id = ?
                """, (source_id,))
                result = cursor.fetchone()
                
                if not result:
                    return False
                
                # In a real implementation, would test the URL
                # For now, just return True to simulate recovery
                return True
        except Exception as e:
            self.logger.error(f"Failed to test source {source_id}: {e}")
            return False
    
    async def cleanup_logs(self):
        """Clean up old log files"""
        if not self.config['log_cleanup']['enabled']:
            return
        
        self.logger.info("Starting log cleanup")
        
        retention_days = self.config['log_cleanup']['retention_days']
        max_size_mb = self.config['log_cleanup']['max_log_size_mb']
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        log_dir = Path("logs")
        if not log_dir.exists():
            return
        
        total_size = 0
        removed_count = 0
        archived_count = 0
        
        for log_file in log_dir.rglob("*.log*"):
            try:
                stat = log_file.stat()
                file_age = datetime.fromtimestamp(stat.st_mtime)
                file_size_mb = stat.st_size / (1024 * 1024)
                
                # Remove old files
                if file_age < cutoff_date:
                    if self.config['log_cleanup']['archive_old_logs']:
                        # Archive to compressed format
                        archive_path = log_file.with_suffix('.log.gz')
                        import gzip
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(archive_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        archived_count += 1
                    
                    log_file.unlink()
                    removed_count += 1
                    self.logger.debug(f"Removed old log file: {log_file}")
                else:
                    total_size += file_size_mb
                
                # Check individual file size
                if file_size_mb > max_size_mb:
                    # Rotate large files
                    rotate_path = log_file.with_suffix(f'.{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
                    log_file.rename(rotate_path)
                    self.logger.info(f"Rotated large log file: {log_file} -> {rotate_path}")
            
            except Exception as e:
                self.logger.error(f"Error processing log file {log_file}: {e}")
        
        self.logger.info(f"Log cleanup completed: removed {removed_count} files, "
                        f"archived {archived_count} files, total size: {total_size:.1f}MB")
    
    async def optimize_database(self):
        """Optimize database performance"""
        if not self.config['optimization']['enabled']:
            return
        
        self.logger.info("Starting database optimization")
        
        # Vacuum main database
        await self._vacuum_database()
        
        # Rebuild indexes if needed
        days_since_rebuild = (datetime.now() - self.last_optimization).days
        if days_since_rebuild >= self.config['optimization']['index_rebuild_days']:
            await self._rebuild_indexes()
            self.last_optimization = datetime.now()
        
        # Clean up old statistics
        await self._cleanup_old_stats()
        
        self.logger.info("Database optimization completed")
    
    async def _vacuum_database(self):
        """Vacuum the database to reclaim space"""
        try:
            for db_path in [self.db.db_path, self.db.ainews_db_path]:
                if Path(db_path).exists():
                    with sqlite3.connect(db_path) as conn:
                        conn.execute("VACUUM")
                        self.logger.info(f"Vacuumed database: {db_path}")
        except Exception as e:
            self.logger.error(f"Failed to vacuum database: {e}")
    
    async def _rebuild_indexes(self):
        """Rebuild database indexes"""
        try:
            with sqlite3.connect(self.db.ainews_db_path) as conn:
                cursor = conn.cursor()
                
                # Get all indexes
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
                """)
                indexes = cursor.fetchall()
                
                for (index_name,) in indexes:
                    try:
                        cursor.execute(f"REINDEX {index_name}")
                        self.logger.debug(f"Rebuilt index: {index_name}")
                    except Exception as e:
                        self.logger.error(f"Failed to rebuild index {index_name}: {e}")
                
                conn.commit()
                self.logger.info(f"Rebuilt {len(indexes)} indexes")
        except Exception as e:
            self.logger.error(f"Failed to rebuild indexes: {e}")
    
    async def _cleanup_old_stats(self):
        """Clean up old statistics data"""
        try:
            retention_days = self.config['optimization']['stats_cleanup_days']
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Clean up old performance metrics
                cursor.execute("""
                    DELETE FROM performance_metrics 
                    WHERE timestamp < ?
                """, (cutoff_date,))
                
                perf_deleted = cursor.rowcount
                
                # Clean up old source metrics
                cursor.execute("""
                    DELETE FROM source_metrics 
                    WHERE timestamp < ?
                """, (cutoff_date,))
                
                source_deleted = cursor.rowcount
                
                # Alerting system removed - no cleanup needed
                
                conn.commit()
                
                self.logger.info(f"Cleaned up old stats: {perf_deleted} performance metrics, "
                               f"{source_deleted} source metrics")
        except Exception as e:
            self.logger.error(f"Failed to cleanup old stats: {e}")
    
    async def _archive_old_data(self):
        """Archive old article data"""
        try:
            archive_dir = Path("data/archive")
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Archive articles older than 90 days
            cutoff_date = datetime.now() - timedelta(days=90)
            archive_path = archive_dir / f"articles_archive_{cutoff_date.strftime('%Y%m')}.db"
            
            with sqlite3.connect(self.db.ainews_db_path) as source_conn:
                with sqlite3.connect(str(archive_path)) as archive_conn:
                    # Copy old articles to archive
                    source_conn.backup(archive_conn, pages=100)
                    
                    # Delete from main database
                    cursor = source_conn.cursor()
                    cursor.execute("""
                        DELETE FROM articles 
                        WHERE created_at < ?
                    """, (cutoff_date,))
                    
                    archived_count = cursor.rowcount
                    source_conn.commit()
                    
                    self.logger.info(f"Archived {archived_count} old articles to {archive_path}")
        except Exception as e:
            self.logger.error(f"Failed to archive old data: {e}")
    
    async def _clear_caches(self):
        """Clear application caches"""
        try:
            cache_dir = Path("data/article_cache")
            if cache_dir.exists():
                for cache_file in cache_dir.glob("*.json"):
                    try:
                        # Only remove files older than 7 days
                        if (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).days > 7:
                            cache_file.unlink()
                    except Exception as e:
                        self.logger.error(f"Failed to remove cache file {cache_file}: {e}")
                
                self.logger.info("Cleared old cache files")
        except Exception as e:
            self.logger.error(f"Failed to clear caches: {e}")
    
    async def check_performance_optimization(self):
        """Check and apply performance optimizations"""
        self.logger.info("Checking for performance optimization opportunities")
        
        # Get current system metrics
        metrics = self.db.get_system_metrics()
        
        # Check if too many sources are failing
        if metrics.error_sources > 50:
            self.logger.warning(f"{metrics.error_sources} sources in error state, checking for patterns")
            
            # Analyze error patterns
            error_summary = self.db.get_error_summary(hours=24)
            
            # Group errors by type
            error_types = {}
            for error in error_summary['source_errors']:
                error_type = error.get('last_error', 'unknown')
                if error_type not in error_types:
                    error_types[error_type] = []
                error_types[error_type].append(error)
            
            # Log patterns
            for error_type, errors in error_types.items():
                if len(errors) > 5:
                    self.logger.info(f"Common error pattern: {error_type} affecting {len(errors)} sources")
        
        # Check parse rate
        recent_metrics = self.db.get_source_metrics()
        slow_sources = [m for m in recent_metrics if m.avg_parse_time_ms > 30000]  # 30 seconds
        
        if len(slow_sources) > 10:
            self.logger.warning(f"{len(slow_sources)} sources have slow parse times")
            
            # Could implement automatic timeout adjustments here
        
        self.logger.info("Performance optimization check completed")
    
    def get_automation_status(self) -> Dict[str, Any]:
        """Get current automation status"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return {
            'enabled': True,
            'disabled_sources': list(self.disabled_sources),
            'recovery_attempts': dict(self.recovery_attempts),
            'scheduled_jobs': jobs,
            'last_optimization': self.last_optimization.isoformat(),
            'config': self.config
        }