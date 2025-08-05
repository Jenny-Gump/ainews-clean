# Database Module - Extract API System

## Overview
This is a simplified database module optimized for the Extract API system. It has been migrated from the old system with significant simplifications.

## Key Changes from Old System

### Removed Features
- RSS+Scrape API related code
- Two-phase architecture methods
- Circuit breaker logging
- Monitoring database integration
- Complex batch operations
- Deprecated methods

### Simplified Features
- Single-phase Extract API focus
- Cleaner method signatures
- Reduced complexity in logging
- Streamlined error handling

### New Features
- Extract API specific fields (summary, tags, categories, etc.)
- Related links table for Extract API data
- Simplified media handling
- Better type hints

## Database Schema

### Tables
1. **sources** - News sources configuration
2. **articles** - Main article data with Extract API fields
3. **media_files** - Media attachments with metadata
4. **related_links** - Related articles from Extract API

### Key Methods

#### Source Management
- `get_sources()` - Get list of active sources
- `update_source_status()` - Update source status
- `get_source_stats()` - Get source statistics

#### Article Management
- `article_exists()` - Check if article exists
- `insert_article()` - Insert new article
- `get_pending_articles()` - Get articles for parsing
- `update_article_content()` - Update with Extract API data
- `update_article_status()` - Update article status
- `increment_article_retry_count()` - Handle retries

#### Media Management
- `insert_media()` - Add media record
- `get_pending_media()` - Get media for download
- `update_media_status()` - Update media status

#### Statistics
- `get_stats()` - Overall database statistics
- `get_parsing_statistics()` - Parsing-specific stats

## Usage Example

```python
from core.database import Database

# Initialize
db = Database()

# Insert article
article_id = db.insert_article({
    'url': 'https://example.com/article',
    'title': 'AI News Article',
    'source_id': 'techcrunch',
    'description': 'Article description'
})

# Update with Extract API content
db.update_article_content(article_id, {
    'content': 'Full article content...',
    'summary': 'Brief summary',
    'tags': ['AI', 'technology'],
    'categories': ['Tech'],
    'language': 'en',
    'word_count': 1500,
    'reading_time_minutes': 5
})
```

## Migration Notes
- The `logging` directory was renamed to `app_logging` to avoid Python module conflicts
- Foreign key constraints are enforced - ensure sources exist before inserting articles
- All timestamps use SQLite's CURRENT_TIMESTAMP for consistency
- JSON fields (tags, categories) are stored as text and converted automatically