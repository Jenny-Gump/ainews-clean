"""
Data models for the monitoring system
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class SourceStatus(Enum):
    """Source status enumeration"""
    ACTIVE = "active"
    ERROR = "error"
    BLOCKED = "blocked"
    NOT_FOUND = "not_found"
    EMPTY = "empty"
    UNCHECKED = "unchecked"
    RATE_LIMITED = "rate_limited"


class ContentStatus(Enum):
    """Content parsing status enumeration"""
    PENDING = "pending"
    PARSING = "parsing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RATE_LIMITED = "rate_limited"


class MediaStatus(Enum):
    """Media download status enumeration"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    FAILED = "failed"
    SKIPPED = "skipped"



@dataclass
class SourceMetrics:
    """Metrics for a single source"""
    source_id: str
    name: str
    url: str
    type: str
    has_rss: bool
    last_status: str
    last_error: Optional[str]
    success_rate: float
    last_parsed: Optional[datetime]
    total_articles: int
    recent_articles_24h: int = 0
    recent_errors_24h: int = 0
    avg_parse_time_ms: float = 0.0
    health_score: float = 0.0  # 0-100 calculated health score


@dataclass
class SystemMetrics:
    """Overall system metrics"""
    total_sources: int
    active_sources: int
    error_sources: int
    blocked_sources: int
    total_articles: int
    articles_24h: int
    articles_7d: int
    total_media_files: int
    media_downloaded: int
    media_failed: int
    avg_article_parse_time_ms: float
    avg_media_download_time_ms: float
    database_size_mb: float
    last_update: datetime


@dataclass
class PerformanceMetrics:
    """Performance tracking metrics"""
    timestamp: datetime
    cpu_usage_percent: float
    memory_usage_mb: float
    disk_usage_percent: float
    active_connections: int
    queue_size: int
    parse_rate_per_minute: float
    error_rate_percent: float



@dataclass
class SourceHealthReport:
    """Detailed health report for a source"""
    source_id: str
    timestamp: datetime
    is_healthy: bool
    health_score: float  # 0-100
    issues: List[str]
    recommendations: List[str]
    metrics_24h: Dict[str, Any]
    metrics_7d: Dict[str, Any]
    performance_trend: str  # "improving", "stable", "degrading"


@dataclass
class ArticleRecord:
    """Article data model"""
    article_id: str
    source_id: str
    title: str
    url: str
    description: Optional[str]
    published_date: Optional[datetime]
    content_status: str
    created_at: datetime
    content_length: int
    source_name: str
    content_preview_url: str


@dataclass
class ArticleContent:
    """Full article content model"""
    article_id: str
    title: str
    source_name: str
    source_url: str
    url: str
    published_date: Optional[datetime]
    content: Optional[str]
    description: Optional[str]
    content_status: str
    created_at: datetime


@dataclass
class SourceSummary:
    """Source summary for filtering"""
    source_id: str
    name: str
    article_count: int