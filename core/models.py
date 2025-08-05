"""
Pydantic models for AI News Parser system.
Matches database schema and Extract API fields.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, validator


class SourceCategory(str, Enum):
    """Source categories"""
    COMPANY = "company"
    RESEARCH = "research"
    NEWS = "news"
    BLOG = "blog"
    NEWSLETTER = "newsletter"
    OTHER = "other"


class SourceStatus(str, Enum):
    """Source status options"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class MediaType(str, Enum):
    """Media file types"""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


class MediaStatus(str, Enum):
    """Media download status"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# Base models with common fields
class TimestampedModel(BaseModel):
    """Base model with timestamp fields"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Source models
class SourceBase(BaseModel):
    """Base source model"""
    name: str
    url: HttpUrl
    rss_url: HttpUrl
    category: SourceCategory = SourceCategory.OTHER
    description: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Source name cannot be empty')
        return v.strip()


class SourceCreate(SourceBase):
    """Model for creating a source"""
    is_active: bool = True


class SourceUpdate(BaseModel):
    """Model for updating a source"""
    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    rss_url: Optional[HttpUrl] = None
    category: Optional[SourceCategory] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    status: Optional[SourceStatus] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Source name cannot be empty')
        return v.strip() if v else v


class Source(SourceBase, TimestampedModel):
    """Complete source model"""
    id: int
    is_active: bool = True
    status: SourceStatus = SourceStatus.ACTIVE
    last_fetched: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None
    
    class Config:
        orm_mode = True


# Article models
class ArticleBase(BaseModel):
    """Base article model"""
    title: str
    url: HttpUrl
    source_id: int
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Article title cannot be empty')
        return v.strip()


class ArticleCreate(ArticleBase):
    """Model for creating an article"""
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    
    # Extract API specific fields
    extract_success: bool = False
    extract_markdown: Optional[str] = None
    extract_cleaned_html: Optional[str] = None
    extract_screenshot: Optional[str] = None
    extract_metadata: Optional[Dict[str, Any]] = None
    
    @validator('tags', 'categories', pre=True)
    def ensure_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v or []


class ArticleUpdate(BaseModel):
    """Model for updating an article"""
    title: Optional[str] = None
    author: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    
    # Extract API fields
    extract_success: Optional[bool] = None
    extract_markdown: Optional[str] = None
    extract_cleaned_html: Optional[str] = None
    extract_screenshot: Optional[str] = None
    extract_metadata: Optional[Dict[str, Any]] = None
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Article title cannot be empty')
        return v.strip() if v else v


class Article(ArticleBase, TimestampedModel):
    """Complete article model"""
    id: int
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    
    # Processing status
    is_processed: bool = False
    processing_error: Optional[str] = None
    
    # Extract API fields
    extract_success: bool = False
    extract_markdown: Optional[str] = None
    extract_cleaned_html: Optional[str] = None
    extract_screenshot: Optional[str] = None
    extract_metadata: Optional[Dict[str, Any]] = None
    
    # Relationships
    source: Optional[Source] = None
    media_files: List['MediaFile'] = Field(default_factory=list)
    related_links: List['RelatedLink'] = Field(default_factory=list)
    
    class Config:
        orm_mode = True


# Media file models
class MediaFileBase(BaseModel):
    """Base media file model"""
    article_id: int
    url: HttpUrl
    media_type: MediaType
    
    @validator('media_type', pre=True)
    def detect_media_type(cls, v, values):
        if v:
            return v
        
        # Auto-detect from URL if not provided
        url_str = str(values.get('url', '')).lower()
        if any(ext in url_str for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']):
            return MediaType.IMAGE
        elif any(ext in url_str for ext in ['.mp4', '.webm', '.mov', '.avi']):
            return MediaType.VIDEO
        elif any(ext in url_str for ext in ['.mp3', '.wav', '.ogg']):
            return MediaType.AUDIO
        elif any(ext in url_str for ext in ['.pdf', '.doc', '.docx']):
            return MediaType.DOCUMENT
        
        return MediaType.IMAGE  # Default


class MediaFileCreate(MediaFileBase):
    """Model for creating a media file"""
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    local_path: Optional[str] = None
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


class MediaFileUpdate(BaseModel):
    """Model for updating a media file"""
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    local_path: Optional[str] = None
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    status: Optional[MediaStatus] = None
    error_message: Optional[str] = None


class MediaFile(MediaFileBase, TimestampedModel):
    """Complete media file model"""
    id: int
    alt_text: Optional[str] = None
    caption: Optional[str] = None
    local_path: Optional[str] = None
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    status: MediaStatus = MediaStatus.PENDING
    download_attempts: int = 0
    error_message: Optional[str] = None
    
    class Config:
        orm_mode = True


# Related link models
class RelatedLinkBase(BaseModel):
    """Base related link model"""
    article_id: int
    url: HttpUrl
    title: str
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('Link title cannot be empty')
        return v.strip()


class RelatedLinkCreate(RelatedLinkBase):
    """Model for creating a related link"""
    description: Optional[str] = None
    link_type: Optional[str] = None


class RelatedLink(RelatedLinkBase, TimestampedModel):
    """Complete related link model"""
    id: int
    description: Optional[str] = None
    link_type: Optional[str] = None
    
    class Config:
        orm_mode = True


# Response models for API
class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int


class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    database: str
    articles_count: int
    sources_count: int
    active_sources_count: int


# Stats models
class SourceStats(BaseModel):
    """Source statistics"""
    source_id: int
    source_name: str
    total_articles: int
    articles_today: int
    articles_week: int
    last_article_date: Optional[datetime] = None
    error_rate: float
    avg_articles_per_day: float


class SystemStats(BaseModel):
    """System-wide statistics"""
    total_articles: int
    total_sources: int
    active_sources: int
    articles_today: int
    articles_week: int
    articles_month: int
    total_media_files: int
    downloaded_media: int
    failed_media: int
    database_size_mb: float
    last_update: datetime