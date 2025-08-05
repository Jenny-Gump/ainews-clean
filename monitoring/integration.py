"""
Integration hooks for monitoring system with the main parsing pipeline
"""
import time
import json
import sqlite3
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from app_logging import get_logger

from .collectors import SourceHealthCollector
from .database import MonitoringDatabase

logger = get_logger(__name__)


class MonitoringIntegration:
    """Provides integration hooks for the parsing pipeline"""
    
    def __init__(self, monitoring_db=None):
        if monitoring_db is None:
            # Use absolute path resolver to work from any directory
            monitoring_db_path = self._resolve_monitoring_db_path()
            self.monitoring_db = MonitoringDatabase(monitoring_db_path)
        else:
            self.monitoring_db = monitoring_db
        self.source_health_collector = SourceHealthCollector(self.monitoring_db)
        self._parse_start_times = {}
        self._source_metrics = {}
    
    def _resolve_monitoring_db_path(self) -> str:
        """Resolve monitoring database path from any system location"""
        current_dir = Path(__file__).parent
        # Go up until we find 'ainews-clean' directory
        while current_dir.name != 'ainews-clean' and current_dir.parent != current_dir:
            current_dir = current_dir.parent
        
        if current_dir.name != 'ainews-clean':
            # Fallback to relative path if we can't find ainews-clean directory
            logger.warning("Could not find ainews-clean root directory, using relative path")
            return "data/monitoring.db"
        
        monitoring_db_path = str(current_dir / "data" / "monitoring.db")
        logger.info(f"Resolved monitoring DB path: {monitoring_db_path}")
        return monitoring_db_path
        
    def on_source_parse_start(self, source_id: str, source_name: str) -> Dict[str, Any]:
        """Called when starting to parse a source"""
        start_time = time.time()
        self._parse_start_times[source_id] = start_time
        
        context = {
            'source_id': source_id,
            'source_name': source_name,
            'start_time': start_time,
            'timestamp': datetime.now().isoformat()  # Convert to ISO string for JSON serialization
        }
        
        logger.info(f"Monitoring: Starting parse for {source_name}", extra=context)
        return context
    
    def on_source_parse_complete(self, source_id: str, result: Dict[str, Any]) -> None:
        """Called when source parsing is complete"""
        start_time = self._parse_start_times.get(source_id, time.time())
        parse_time_ms = (time.time() - start_time) * 1000
        
        # Prepare metrics for collection
        parsing_result = {
            'success': result.get('article_count', 0) > 0 or result.get('success', False),
            'article_count': result.get('article_count', 0),
            'parse_time_ms': parse_time_ms,
            'error_type': result.get('error_type'),
            'error_message': result.get('error_message'),
            'response_time_ms': result.get('response_time_ms', parse_time_ms),
            'content_quality': self._calculate_content_quality(result),
            'media_success_rate': result.get('media_success_rate', 100)
        }
        
        # Collect metrics
        self.source_health_collector.collect_source_metrics(source_id, parsing_result)
        
        # Log completion
        logger.info(
            f"Monitoring: Completed parse for {source_id}",
            extra={
                'source_id': source_id,
                'articles': parsing_result['article_count'],
                'parse_time_ms': parse_time_ms,
                'success': parsing_result['success']
            }
        )
        
        # Clean up
        if source_id in self._parse_start_times:
            del self._parse_start_times[source_id]
    
    def on_rss_feed_checked(self, source_id: str, feed_stats: Dict[str, Any]) -> None:
        """Called when RSS feed is checked"""
        # Log RSS feed check
        logger.info(
            f"RSS feed checked for {source_id}",
            extra={
                'source_id': source_id,
                'articles_found': feed_stats.get('total_articles', 0),
                'new_articles': feed_stats.get('new_articles', 0),
                'fetch_time_ms': feed_stats.get('fetch_time_ms', 0)
            }
        )
    
    def on_scrape_batch_complete(self, source_id: str, batch_stats: Dict[str, Any]) -> None:
        """Called when a batch of articles is scraped"""
        # Log scraping batch completion
        logger.info(
            f"Scrape batch completed for {source_id}",
            extra={
                'source_id': source_id,
                'batch_size': batch_stats.get('batch_size', 0),
                'success_count': batch_stats.get('success_count', 0),
                'failed_count': batch_stats.get('failed_count', 0)
            }
        )
    
    def on_article_parsed(self, source_id: str, article_data: Dict[str, Any]) -> None:
        """Called when an individual article is parsed"""
        # Track article-level metrics
        if source_id not in self._source_metrics:
            self._source_metrics[source_id] = {
                'articles': [],
                'total_content_length': 0,
                'has_full_content_count': 0
            }
        
        content_length = len(article_data.get('content', ''))
        has_full_content = content_length > 100
        
        self._source_metrics[source_id]['articles'].append({
            'article_id': article_data.get('article_id'),
            'content_length': content_length,
            'has_full_content': has_full_content,
            'has_media': bool(article_data.get('media_files'))
        })
        
        self._source_metrics[source_id]['total_content_length'] += content_length
        if has_full_content:
            self._source_metrics[source_id]['has_full_content_count'] += 1
    
    def on_media_download(self, article_id: str, media_url: str, success: bool, 
                         download_time_ms: float) -> None:
        """Called when media is downloaded"""
        # Log media download metrics
        logger.debug(
            f"Monitoring: Media download {'succeeded' if success else 'failed'}",
            extra={
                'article_id': article_id,
                'media_url': media_url,
                'success': success,
                'download_time_ms': download_time_ms
            }
        )
    
    def on_error(self, source_id: str, error_type: str, error_message: str, 
                 context: Dict[str, Any]) -> None:
        """Called when an error occurs during parsing"""
        # Store error in monitoring database
        try:
            with sqlite3.connect(self.monitoring_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO error_logs (
                        source_id, error_type, error_message, 
                        context, timestamp
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    source_id,
                    error_type,
                    error_message,
                    json.dumps(context),
                    datetime.now()
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log error to monitoring DB: {e}")
        
        # Log error
        logger.error(
            f"Monitoring: Error in {source_id}",
            extra={
                'source_id': source_id,
                'error_type': error_type,
                'error_message': error_message,
                'context': context
            }
        )
    
    def _calculate_content_quality(self, result: Dict[str, Any]) -> float:
        """Calculate content quality score (0-100)"""
        if not result.get('article_count'):
            return 0
        
        source_id = result.get('source_id')
        if not source_id or source_id not in self._source_metrics:
            return 50  # Default middle score
        
        metrics = self._source_metrics[source_id]
        article_count = len(metrics['articles'])
        
        if article_count == 0:
            return 50
        
        # Calculate average content length
        avg_content_length = metrics['total_content_length'] / article_count
        
        # Calculate full content rate
        full_content_rate = metrics['has_full_content_count'] / article_count * 100
        
        # Calculate quality score
        # - 50% based on content length (optimal is 1000+ chars)
        # - 50% based on full content rate
        length_score = min(100, (avg_content_length / 1000) * 50)
        quality_score = (length_score + full_content_rate) / 2
        
        return quality_score
    
    def get_source_health_report(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get current health report for a source"""
        try:
            # Get detailed metrics
            metrics = self.monitoring_db.get_source_metrics_detailed()
            source_metrics = next((m for m in metrics if m['source_id'] == source_id), None)
            
            if not source_metrics:
                return None
            
            # Calculate health score
            health_score = self.source_health_collector.calculate_health_score(source_metrics)
            
            # Generate report
            report = {
                'source_id': source_id,
                'timestamp': datetime.now(),
                'health_score': health_score,
                'metrics': source_metrics,
                'status': self._get_health_status(health_score),
                'recommendations': self._get_recommendations(source_metrics, health_score)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate health report for {source_id}: {e}")
            return None
    
    def _get_health_status(self, health_score: float) -> str:
        """Get health status based on score"""
        if health_score >= 80:
            return "healthy"
        elif health_score >= 60:
            return "warning"
        elif health_score >= 40:
            return "degraded"
        else:
            return "critical"
    
    def _get_recommendations(self, metrics: Dict[str, Any], health_score: float) -> List[str]:
        """Generate recommendations based on metrics"""
        recommendations = []
        
        if health_score < 50:
            recommendations.append("Critical: Source needs immediate attention")
        
        if metrics.get('last_status') == 'blocked':
            recommendations.append("Source is blocked - check robots.txt or rate limiting")
        
        if metrics.get('recent_errors_24h', 0) > 10:
            recommendations.append("High error rate - review error logs for patterns")
        
        if metrics.get('avg_parse_time_ms', 0) > 5000:
            recommendations.append("Slow parsing - consider optimizing selectors or using cache")
        
        if metrics.get('performance_trend') == 'degrading':
            recommendations.append("Performance is degrading - monitor closely")
        
        return recommendations


# Global instance for easy access
_monitoring_integration = None

def get_monitoring_integration(monitoring_db=None) -> MonitoringIntegration:
    """Get or create the global monitoring integration instance"""
    global _monitoring_integration
    if _monitoring_integration is None:
        _monitoring_integration = MonitoringIntegration(monitoring_db)
    return _monitoring_integration