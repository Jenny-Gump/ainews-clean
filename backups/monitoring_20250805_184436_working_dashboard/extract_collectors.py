"""
Extract API specific monitoring collectors
Tracks metrics specific to Firecrawl Extract API system
"""
import time
import json
from typing import Dict, Any, Optional
from datetime import datetime
from app_logging import get_logger


class ExtractAPIMonitoringCollector:
    """
    Monitors Extract API specific metrics:
    - API costs and usage
    - Content quality from Extract API
    - Processing times for Extract operations
    - Error patterns specific to Extract API
    """
    
    def __init__(self, monitoring_db=None):
        self.logger = get_logger('monitoring.extract_api')
        self.monitoring_db = monitoring_db
        self._extract_metrics = {
            'total_requests': 0,
            'total_cost_usd': 0.0,
            'average_response_time': 0.0,
            'success_rate': 0.0,
            'content_quality_score': 0.0
        }
    
    def track_extract_request(self, url: str, cost_usd: float, response_time_ms: float, 
                            success: bool, content_length: int = 0, error_message: str = None):
        """Track an Extract API request"""
        
        # Update internal metrics
        self._extract_metrics['total_requests'] += 1
        self._extract_metrics['total_cost_usd'] += cost_usd
        
        # Log the request
        self.logger.info(
            "Extract API request tracked",
            url=url,
            cost_usd=cost_usd,
            response_time_ms=response_time_ms,
            success=success,
            content_length=content_length,
            error_message=error_message,
            total_requests=self._extract_metrics['total_requests'],
            total_cost=self._extract_metrics['total_cost_usd']
        )
        
        # Store in monitoring database if available
        if self.monitoring_db:
            try:
                self.monitoring_db.save_extract_api_metrics({
                    'timestamp': datetime.now(),
                    'url': url,
                    'cost_usd': cost_usd,
                    'response_time_ms': response_time_ms,
                    'success': success,
                    'content_length': content_length,
                    'error_message': error_message
                })
            except Exception as e:
                self.logger.warning(f"Failed to save Extract API metrics to DB: {e}")
    
    def track_content_quality(self, article_id: str, content_length: int, 
                            images_count: int, has_summary: bool, 
                            has_tags: bool, has_related_links: bool):
        """Track content quality metrics from Extract API"""
        
        # Calculate quality score (0-100)
        quality_score = self._calculate_content_quality_score(
            content_length, images_count, has_summary, has_tags, has_related_links
        )
        
        self.logger.info(
            "Extract API content quality tracked",
            article_id=article_id,
            content_length=content_length,
            images_count=images_count,
            has_summary=has_summary,
            has_tags=has_tags,
            has_related_links=has_related_links,
            quality_score=quality_score
        )
        
        # Update average quality score
        current_avg = self._extract_metrics.get('content_quality_score', 0.0)
        total_requests = self._extract_metrics['total_requests']
        if total_requests > 0:
            self._extract_metrics['content_quality_score'] = (
                (current_avg * (total_requests - 1) + quality_score) / total_requests
            )
    
    def track_api_error(self, error_type: str, error_message: str, url: str, 
                       response_code: int = None, retry_count: int = 0):
        """Track Extract API specific errors"""
        
        self.logger.error(
            "Extract API error tracked",
            error_type=error_type,
            error_message=error_message,
            url=url,
            response_code=response_code,
            retry_count=retry_count
        )
        
        # Store error in monitoring database
        if self.monitoring_db:
            try:
                self.monitoring_db.log_extract_api_error({
                    'timestamp': datetime.now(),
                    'error_type': error_type,
                    'error_message': error_message,
                    'url': url,
                    'response_code': response_code,
                    'retry_count': retry_count
                })
            except Exception as e:
                self.logger.warning(f"Failed to log Extract API error to DB: {e}")
    
    def track_timeout_event(self, url: str, timeout_seconds: int, operation_type: str):
        """Track timeout events specific to Extract API"""
        
        self.logger.warning(
            "Extract API timeout tracked",
            url=url,
            timeout_seconds=timeout_seconds,
            operation_type=operation_type  # 'extract_request', 'job_wait', etc.
        )
    
    def track_cost_usage(self, daily_cost_limit: float = 50.0):
        """Track and alert on Extract API cost usage"""
        
        current_cost = self._extract_metrics['total_cost_usd']
        cost_percentage = (current_cost / daily_cost_limit) * 100
        
        self.logger.info(
            "Extract API cost usage",
            current_cost_usd=current_cost,
            daily_limit_usd=daily_cost_limit,
            cost_percentage=cost_percentage
        )
        
        # Alert if approaching limit
        if cost_percentage > 80:
            self.logger.warning(
                "Extract API cost approaching daily limit",
                current_cost_usd=current_cost,
                daily_limit_usd=daily_cost_limit,
                cost_percentage=cost_percentage
            )
        
        if cost_percentage > 95:
            self.logger.error(
                "Extract API cost near daily limit - consider stopping",
                current_cost_usd=current_cost,
                daily_limit_usd=daily_cost_limit,
                cost_percentage=cost_percentage
            )
    
    def _calculate_content_quality_score(self, content_length: int, images_count: int,
                                       has_summary: bool, has_tags: bool, 
                                       has_related_links: bool) -> float:
        """Calculate content quality score (0-100)"""
        
        score = 0.0
        
        # Content length score (40 points max)
        if content_length > 2000:
            score += 40
        elif content_length > 1000:
            score += 30
        elif content_length > 500:
            score += 20
        elif content_length > 100:
            score += 10
        
        # Images score (20 points max)
        if images_count > 3:
            score += 20
        elif images_count > 1:
            score += 15
        elif images_count > 0:
            score += 10
        
        # Metadata scores (40 points total)
        if has_summary:
            score += 15
        if has_tags:
            score += 15
        if has_related_links:
            score += 10
        
        return min(100.0, score)
    
    def get_extract_api_summary(self) -> Dict[str, Any]:
        """Get summary of Extract API metrics"""
        
        return {
            'total_requests': self._extract_metrics['total_requests'],
            'total_cost_usd': round(self._extract_metrics['total_cost_usd'], 4),
            'average_cost_per_request': (
                round(self._extract_metrics['total_cost_usd'] / max(1, self._extract_metrics['total_requests']), 4)
            ),
            'content_quality_score': round(self._extract_metrics['content_quality_score'], 1),
            'timestamp': datetime.now().isoformat()
        }
    
    def reset_daily_metrics(self):
        """Reset daily metrics (call at midnight)"""
        
        self.logger.info(
            "Resetting Extract API daily metrics",
            final_total_requests=self._extract_metrics['total_requests'],
            final_total_cost=self._extract_metrics['total_cost_usd']
        )
        
        self._extract_metrics = {
            'total_requests': 0,
            'total_cost_usd': 0.0,
            'average_response_time': 0.0,
            'success_rate': 0.0,
            'content_quality_score': 0.0
        }


# Global instance for easy access
_extract_api_collector = None

def get_extract_api_collector(monitoring_db=None) -> ExtractAPIMonitoringCollector:
    """Get or create the global Extract API monitoring collector"""
    global _extract_api_collector
    if _extract_api_collector is None:
        _extract_api_collector = ExtractAPIMonitoringCollector(monitoring_db)
    return _extract_api_collector