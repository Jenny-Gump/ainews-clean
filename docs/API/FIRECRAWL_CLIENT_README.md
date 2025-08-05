# FirecrawlClient Service Module

## Overview

I've created a clean, reusable Firecrawl API client service module for the Extract API system. This replaces the scattered Firecrawl logic that was previously embedded across multiple files.

## Files Created/Modified

### New Files:
- `/services/firecrawl_client.py` - Main FirecrawlClient service
- `/test_firecrawl_client.py` - Test script to verify functionality
- `/FIRECRAWL_CLIENT_README.md` - This documentation

### Modified Files:
- `/services/content_parser.py` - Refactored to use FirecrawlClient
- `/services/__init__.py` - Updated exports
- `/core/main.py` - Updated imports to use new service structure

## FirecrawlClient Features

### Core Functionality
- **Clean API**: Simple, intuitive interface for Extract API operations
- **Async Support**: Full async/await support with context managers
- **Error Handling**: Custom `FirecrawlError` exception with detailed error info
- **Rate Limiting**: Built-in rate limiting to respect API limits
- **Retry Logic**: Configurable retry mechanism with exponential backoff
- **Redirect Resolution**: Automatic handling of redirect URLs (especially Google redirects)

### Key Methods
- `extract_content(url, schema, prompt)` - Extract content from a single URL
- `extract_with_retry(url, max_retries)` - Extract with automatic retries
- `get_statistics()` - Get usage statistics and performance metrics
- `reset_statistics()` - Reset usage statistics

### Usage Examples

#### Basic Usage
```python
from services.firecrawl_client import FirecrawlClient

async with FirecrawlClient() as client:
    result = await client.extract_content("https://example.com/article")
    print(f"Title: {result.get('title')}")
    print(f"Content: {result.get('content')[:200]}...")
```

#### With Retry
```python
async with FirecrawlClient() as client:
    result = await client.extract_with_retry(
        "https://example.com/article",
        max_retries=3
    )
```

#### Convenience Functions
```python
from services.firecrawl_client import extract_article_content, extract_multiple_articles

# Single article
result = await extract_article_content("https://example.com/article")

# Multiple articles (concurrent)
urls = ["https://example1.com", "https://example2.com"]
results = await extract_multiple_articles(urls, max_concurrent=3)
```

## ContentParser Integration

The `ContentParser` class has been refactored to use the new `FirecrawlClient`:

### Key Features
- **Clean Architecture**: Separates content extraction from database operations
- **Statistics Tracking**: Tracks both parsing and Firecrawl statistics
- **Batch Processing**: Process multiple articles with configurable batch sizes
- **Database Integration**: Automatically saves extracted content to database
- **Error Handling**: Graceful error handling with proper database updates

### Usage Examples

#### Single Article
```python
from services.content_parser import ContentParser

async with ContentParser() as parser:
    result = await parser.parse_article(article_id, url, source_id)
```

#### Batch Processing
```python
async with ContentParser() as parser:
    summary = await parser.process_pending_articles(
        batch_size=10,
        max_articles=100
    )
    print(f"Processed: {summary['total_processed']}")
    print(f"Success rate: {summary['success_rate']:.1f}%")
```

## Configuration

The client uses configuration from `core.config.ExtractConfig`:

- `FIRECRAWL_API_KEY` - API key from environment variables
- `EXTRACT_API_URL` - Firecrawl Extract API endpoint
- `REQUEST_TIMEOUT` - Request timeout (default: 120 seconds)
- `MAX_RETRIES` - Maximum retry attempts (default: 2)
- `EXTRACT_SCHEMA` - JSON schema for structured extraction
- `EXTRACT_PROMPT` - Prompt for extraction guidance

## Error Handling

### FirecrawlError Exception
Custom exception class that provides:
- Error message
- HTTP status code (if applicable)
- Response data for debugging

### Permanent vs Temporary Errors
The client distinguishes between:
- **Permanent errors**: 403, blocked, not supported - no retry
- **Temporary errors**: Timeouts, network issues - will retry

## Statistics and Monitoring

Both `FirecrawlClient` and `ContentParser` provide detailed statistics:

### FirecrawlClient Stats
- Total requests made
- Successful/failed extractions
- Success rate percentage
- Average processing time
- Estimated costs
- Requests per second

### ContentParser Stats
- Articles processed
- Database save success/failure rates
- Combined with Firecrawl statistics

## Rate Limiting

Built-in rate limiting features:
- Configurable delay between requests (default: 1 second)
- Automatic request spacing
- Respect for API limits

## Testing

Use the provided test script:

```bash
cd /Users/skynet/Desktop/AI DEV/ainews-clean
python test_firecrawl_client.py
```

The test script verifies:
- Basic client functionality
- Convenience functions
- Error handling and retries
- Statistics tracking

## Migration from Old System

### What Changed
1. **Centralized Logic**: All Firecrawl operations now in one service
2. **Clean Interface**: Simple, consistent API across all operations
3. **Better Error Handling**: Custom exceptions with detailed information
4. **Improved Statistics**: More comprehensive metrics and monitoring
5. **Modular Design**: Easy to test, maintain, and extend

### Benefits
- **Reusability**: Other modules can easily use Firecrawl functionality
- **Maintainability**: All Firecrawl logic in one place
- **Testability**: Easy to unit test and verify functionality
- **Consistency**: Standardized error handling and logging
- **Performance**: Built-in rate limiting and retry logic

## Next Steps

1. **Test the implementation** with your actual data
2. **Update other modules** that might use Firecrawl directly
3. **Add monitoring integration** if needed
4. **Consider adding caching** for frequently accessed URLs
5. **Implement batch extraction** for higher throughput if needed

The new FirecrawlClient provides a solid foundation for all Extract API operations in your system while maintaining clean separation of concerns and excellent error handling.