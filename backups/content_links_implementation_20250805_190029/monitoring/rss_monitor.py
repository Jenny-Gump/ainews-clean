"""
RSS Feed Monitoring Module
Monitors RSS feeds health, performance, and integration with scraping pipeline
"""
import asyncio
import aiohttp
import feedparser
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import json
import logging
from dataclasses import dataclass

from .database import MonitoringDatabase


@dataclass
class RSSFeedStatus:
    """RSS Feed status information"""
    source_id: str
    feed_url: str
    status: str  # 'healthy', 'error', 'timeout', 'unknown'
    articles_count: int
    fetch_time_ms: float
    last_updated: Optional[datetime]
    error_message: Optional[str] = None


class RSSMonitor:
    """Monitors RSS feeds health and performance"""
    
    def __init__(self, monitoring_db: MonitoringDatabase):
        self.monitoring_db = monitoring_db
        self.logger = logging.getLogger('monitoring.rss')
        self._running = False
        self._check_interval = 300  # 5 minutes
        self._timeout = 30  # 30 seconds timeout
        self._rss_feeds = {}
        self._load_rss_feeds()
    
    def _execute_query(self, query: str, params=None):
        """Execute query using monitoring database"""
        # Temporary workaround for execute_query issue
        import sqlite3
        try:
            with sqlite3.connect(self.monitoring_db.db_path) as conn:
                if params:
                    cursor = conn.execute(query, params)
                else:
                    cursor = conn.execute(query)
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            raise
        
    def _load_rss_feeds(self):
        """Load RSS feeds from sources_extract.json"""
        try:
            import os
            sources_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'services', 'sources_extract.json')
            with open(sources_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Extract RSS URLs for each source
            for source in data['sources']:
                if 'rss_url' in source and source['rss_url']:
                    self._rss_feeds[source['id']] = {
                        'url': source['rss_url'],
                        'name': source['name']
                    }
                    
            self.logger.info(f"Loaded {len(self._rss_feeds)} RSS feeds for monitoring")
            
        except Exception as e:
            self.logger.error(f"Error loading RSS feeds: {e}")
            self._rss_feeds = {}
    
    async def check_rss_feed(self, source_id: str, feed_url: str) -> RSSFeedStatus:
        """Check individual RSS feed health"""
        start_time = time.time()
        
        try:
            # Parse RSS feed with timeout
            loop = asyncio.get_event_loop()
            feed = await asyncio.wait_for(
                loop.run_in_executor(None, feedparser.parse, feed_url),
                timeout=self._timeout
            )
            
            fetch_time_ms = (time.time() - start_time) * 1000
            
            # Check for parsing errors
            if feed.bozo and feed.bozo_exception:
                return RSSFeedStatus(
                    source_id=source_id,
                    feed_url=feed_url,
                    status='error',
                    articles_count=0,
                    fetch_time_ms=fetch_time_ms,
                    last_updated=None,
                    error_message=str(feed.bozo_exception)
                )
            
            # Count articles and get last update time
            articles_count = len(feed.entries)
            last_updated = None
            
            if feed.entries:
                # Get most recent article date
                for entry in feed.entries:
                    entry_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        entry_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        entry_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                    
                    if entry_date and (not last_updated or entry_date > last_updated):
                        last_updated = entry_date
            
            # Determine status
            status = 'healthy'
            if articles_count == 0:
                status = 'error'
            elif last_updated and (datetime.now(timezone.utc) - last_updated).days > 7:
                status = 'stale'
            
            return RSSFeedStatus(
                source_id=source_id,
                feed_url=feed_url,
                status=status,
                articles_count=articles_count,
                fetch_time_ms=fetch_time_ms,
                last_updated=last_updated
            )
            
        except asyncio.TimeoutError:
            fetch_time_ms = (time.time() - start_time) * 1000
            return RSSFeedStatus(
                source_id=source_id,
                feed_url=feed_url,
                status='timeout',
                articles_count=0,
                fetch_time_ms=fetch_time_ms,
                last_updated=None,
                error_message=f"Timeout after {self._timeout}s"
            )
            
        except Exception as e:
            fetch_time_ms = (time.time() - start_time) * 1000
            return RSSFeedStatus(
                source_id=source_id,
                feed_url=feed_url,
                status='error',
                articles_count=0,
                fetch_time_ms=fetch_time_ms,
                last_updated=None,
                error_message=str(e)
            )
    
    async def check_all_feeds(self) -> List[RSSFeedStatus]:
        """Check all RSS feeds concurrently"""
        if not self._rss_feeds:
            return []
        
        tasks = []
        for source_id, feed_info in self._rss_feeds.items():
            task = self.check_rss_feed(source_id, feed_info['url'])
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid results
        feed_statuses = []
        for result in results:
            if isinstance(result, RSSFeedStatus):
                feed_statuses.append(result)
            elif isinstance(result, Exception):
                self.logger.error(f"RSS check exception: {result}")
        
        return feed_statuses
    
    def save_rss_metrics(self, feed_status: RSSFeedStatus):
        """Save RSS metrics to monitoring database"""
        try:
            # Save to rss_feed_metrics table
            self._execute_query(
                """INSERT INTO rss_feed_metrics 
                   (source_id, feed_url, feed_status, articles_in_feed, 
                    fetch_time_ms, last_updated, parse_errors)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    feed_status.source_id,
                    feed_status.feed_url,
                    feed_status.status,
                    feed_status.articles_count,
                    feed_status.fetch_time_ms,
                    feed_status.last_updated,
                    1 if feed_status.status == 'error' else 0
                )
            )
            
            # Update source_metrics table with RSS info
            self._execute_query(
                """UPDATE source_metrics 
                   SET rss_status = ?, rss_last_check = ?, rss_articles_found = ?, 
                       rss_fetch_time_ms = ?
                   WHERE source_id = ?""",
                (
                    feed_status.status,
                    datetime.now(),
                    feed_status.articles_count,
                    feed_status.fetch_time_ms,
                    feed_status.source_id
                )
            )
            
        except Exception as e:
            self.logger.error(f"Error saving RSS metrics for {feed_status.source_id}: {e}")
    
    def get_rss_summary(self) -> Dict[str, Any]:
        """Get RSS system summary"""
        try:
            # Get recent RSS metrics
            query = """
                SELECT 
                    feed_status,
                    COUNT(*) as count,
                    AVG(fetch_time_ms) as avg_fetch_time,
                    AVG(articles_in_feed) as avg_articles
                FROM rss_feed_metrics 
                WHERE timestamp > datetime('now', '-1 hour')
                GROUP BY feed_status
            """
            
            results = self._execute_query(query)
            
            summary = {
                'total_feeds': len(self._rss_feeds),
                'status_breakdown': {},
                'avg_fetch_time_ms': 0,
                'avg_articles_per_feed': 0,
                'last_check': None
            }
            
            total_feeds_checked = 0
            total_fetch_time = 0
            total_articles = 0
            
            for row in results:
                status, count, avg_fetch, avg_articles = row
                summary['status_breakdown'][status] = count
                total_feeds_checked += count
                total_fetch_time += avg_fetch * count
                total_articles += avg_articles * count
            
            if total_feeds_checked > 0:
                summary['avg_fetch_time_ms'] = total_fetch_time / total_feeds_checked
                summary['avg_articles_per_feed'] = total_articles / total_feeds_checked
            
            # Get last check time
            last_check_query = "SELECT MAX(timestamp) FROM rss_feed_metrics"
            last_check_result = self._execute_query(last_check_query)
            if last_check_result and last_check_result[0][0]:
                summary['last_check'] = last_check_result[0][0]
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting RSS summary: {e}")
            return {
                'total_feeds': len(self._rss_feeds),
                'status_breakdown': {},
                'avg_fetch_time_ms': 0,
                'avg_articles_per_feed': 0,
                'last_check': None,
                'error': str(e)
            }
    
    def get_feed_details(self) -> List[Dict[str, Any]]:
        """Get detailed status for each feed"""
        try:
            query = """
                WITH latest_rss AS (
                    SELECT source_id, MAX(timestamp) as max_timestamp
                    FROM rss_feed_metrics
                    GROUP BY source_id
                )
                SELECT 
                    r.source_id,
                    r.feed_url,
                    r.feed_status,
                    r.articles_in_feed,
                    r.fetch_time_ms,
                    r.last_updated,
                    r.timestamp as last_check,
                    NULL as source_name
                FROM rss_feed_metrics r
                INNER JOIN latest_rss lr ON r.source_id = lr.source_id AND r.timestamp = lr.max_timestamp
                ORDER BY r.source_id
            """
            
            results = self._execute_query(query)
            
            feeds = []
            for row in results:
                feeds.append({
                    'source_id': row[0],
                    'feed_url': row[1],
                    'status': row[2],
                    'articles_count': row[3],
                    'fetch_time_ms': row[4],
                    'last_updated': row[5],
                    'last_check': row[6],
                    'source_name': row[7] or row[0]
                })
            
            return feeds
            
        except Exception as e:
            self.logger.error(f"Error getting feed details: {e}")
            return []
    
    async def start_monitoring(self):
        """Start RSS monitoring loop"""
        self._running = True
        self.logger.info("Starting RSS monitoring")
        
        # Run initial check immediately on startup
        try:
            self.logger.info("Running initial RSS check...")
            feed_statuses = await self.check_all_feeds()
            
            # Save metrics for each feed
            for status in feed_statuses:
                self.save_rss_metrics(status)
            
            self.logger.info(f"Initial RSS check completed: {len(feed_statuses)} feeds checked")
            
            # Log summary
            summary = self.get_rss_summary()
            self.logger.info(f"Initial RSS summary: {summary['status_breakdown']}")
            
        except Exception as e:
            self.logger.error(f"Error in initial RSS check: {e}")
        
        while self._running:
            try:
                # Check all RSS feeds
                feed_statuses = await self.check_all_feeds()
                
                # Save metrics for each feed
                for status in feed_statuses:
                    self.save_rss_metrics(status)
                
                self.logger.info(f"RSS check completed: {len(feed_statuses)} feeds checked")
                
                # Log summary
                summary = self.get_rss_summary()
                self.logger.info(f"RSS summary: {summary['status_breakdown']}")
                
            except Exception as e:
                self.logger.error(f"Error in RSS monitoring loop: {e}")
            
            # Wait for next check
            await asyncio.sleep(self._check_interval)
    
    def stop_monitoring(self):
        """Stop RSS monitoring"""
        self._running = False
        self.logger.info("RSS monitoring stopped")


class RSSIntegration:
    """Integration between RSS monitoring and scraping metrics"""
    
    def __init__(self, monitoring_db: MonitoringDatabase):
        self.monitoring_db = monitoring_db
        self.logger = logging.getLogger('monitoring.rss_integration')
    
    def record_scraping_metrics(self, source_id: str, scrape_stats: Dict[str, Any]):
        """Record scraping metrics for RSS source"""
        try:
            scrape_attempts = scrape_stats.get('rss_articles', 0)
            scrape_successes = scrape_stats.get('saved', 0)
            success_rate = (scrape_successes / scrape_attempts * 100) if scrape_attempts > 0 else 0
            
            # Update source_metrics table
            self._execute_query(
                """UPDATE source_metrics 
                   SET scrape_success_rate = ?, last_success_at = ?
                   WHERE source_id = ?""",
                (success_rate, datetime.now(), source_id)
            )
            
            # Update rss_feed_metrics with scraping info
            self._execute_query(
                """UPDATE rss_feed_metrics 
                   SET scrape_attempts = ?, scrape_successes = ?
                   WHERE source_id = ? AND timestamp = (
                       SELECT MAX(timestamp) FROM rss_feed_metrics 
                       WHERE source_id = ?
                   )""",
                (scrape_attempts, scrape_successes, source_id, source_id)
            )
            
        except Exception as e:
            self.logger.error(f"Error recording scraping metrics for {source_id}: {e}")
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get RSS to scraping integration status"""
        try:
            query = """
                WITH latest_rss AS (
                    SELECT source_id, MAX(timestamp) as max_timestamp
                    FROM rss_feed_metrics
                    GROUP BY source_id
                )
                SELECT 
                    r.source_id,
                    r.feed_status,
                    r.articles_in_feed,
                    r.new_articles_found,
                    r.scrape_attempts,
                    r.scrape_successes,
                    s.scrape_success_rate
                FROM rss_feed_metrics r
                INNER JOIN latest_rss lr ON r.source_id = lr.source_id AND r.timestamp = lr.max_timestamp
                LEFT JOIN source_metrics s ON r.source_id = s.source_id
                ORDER BY r.source_id
            """
            
            results = self._execute_query(query)
            
            integration_data = []
            for row in results:
                source_id, feed_status, articles_in_feed, new_articles, scrape_attempts, scrape_successes, success_rate = row
                
                integration_data.append({
                    'source_id': source_id,
                    'feed_status': feed_status,
                    'articles_in_feed': articles_in_feed,
                    'new_articles_found': new_articles,
                    'scrape_attempts': scrape_attempts,
                    'scrape_successes': scrape_successes,
                    'scrape_success_rate': success_rate or 0,
                    'pipeline_efficiency': (scrape_successes / articles_in_feed * 100) if articles_in_feed > 0 else 0
                })
            
            return {
                'sources': integration_data,
                'summary': {
                    'total_sources': len(integration_data),
                    'healthy_feeds': len([s for s in integration_data if s['feed_status'] == 'healthy']),
                    'avg_pipeline_efficiency': sum(s['pipeline_efficiency'] for s in integration_data) / len(integration_data) if integration_data else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting integration status: {e}")
            return {'sources': [], 'summary': {}}