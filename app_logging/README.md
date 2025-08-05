# Centralized Logging System

## Overview

AI News Parser Clean uses a centralized, enhanced logging system that provides structured, context-aware logging across all modules. The system has been optimized after cleanup to use a single unified logging module.

## Features

- **Enhanced Logger Wrapper**: Extended logger with parameter support
- **Context Management**: Structured context managers for operations and articles
- **Configuration-Based Setup**: JSON configuration with environment overrides
- **Execution Time Tracking**: Built-in decorators for performance monitoring
- **Error Context Logging**: Structured error reporting with context
- **Memory Efficient**: Single module design without duplication

## System Architecture

### Single Module Design
- **Primary Module**: `app_logging/logger.py` (248 lines, used in 25+ files)
- **Replaced**: `core/logger.py` (removed as unused duplicate)
- **Status**: Fully consolidated logging system

### File Structure
```
app_logging/
├── __init__.py          # Module exports
├── logger.py            # Main logging implementation
├── config.json          # Logging configuration
└── README.md           # This documentation
```

## Configuration

The system loads configuration from `app_logging/config.json`:

```json
{
  "level": "INFO"
}
```

Key features:
- **Auto-configuration**: `configure_logging()` sets up global logging
- **Environment Override**: LOG_LEVEL environment variable supported
- **Single Setup**: Global configuration prevents duplicate handlers

## Usage Examples

### Basic Enhanced Logging

```python
from app_logging import get_logger

logger = get_logger(__name__)

# Enhanced logger supports extra parameters
logger.info("Article processed", article_id=123, processing_time=1.5)
logger.error("Parse failed", url="example.com", error_type="timeout")
```

### Context Managers

```python
from app_logging import LogContext

# Operation context
with LogContext.operation("rss_discovery", source_id=5):
    logger.info("Starting RSS scan")  # Includes source_id automatically

# Article context  
with LogContext.article("art_123", article_url="example.com"):
    logger.info("Processing content")  # Includes article info
```

### Performance Tracking

```python
from app_logging import log_execution_time

@log_execution_time
def expensive_operation():
    # Function execution time logged automatically
    process_data()
```

### Error Logging with Context

```python
from app_logging import log_error

try:
    result = parse_content(url)
except Exception as e:
    log_error(logger, e, {"url": url, "attempt": retry_count})
```

## Enhanced Logger Features

The `EnhancedLogger` class extends standard logging with:

- **Parameter Support**: Extra kwargs in all log methods
- **Safe Parameter Handling**: Automatic extraction of logging-specific parameters
- **Backwards Compatibility**: Drop-in replacement for standard loggers
- **Context Integration**: Works seamlessly with context managers

## Current Usage Statistics

After cleanup analysis:
- **Active Files**: 25 Python files using the logging system
- **Primary Users**: 
  - `core/` modules (main.py, database.py)
  - `services/` modules (all content processing)
  - `monitoring/` modules (system monitoring)
  - `scripts/` modules (WordPress and utilities)

## Log Locations

### System Logs
```
logs/
├── .log_positions.json      # Log reader positions (monitoring)
├── error_exports/           # Error export directory
├── logrotate.conf          # Log rotation configuration
└── monitoring/
    └── system.log          # Main monitoring system log
```

### Log Rotation
- **Monitoring logs**: 50MB limit with 5 file rotation
- **Automatic cleanup**: Managed by `start_monitoring.sh`
- **Real-time streaming**: Integrated with dashboard

## Integration Points

### Monitoring System
- **Real-time log streaming**: Via WebSocket to dashboard
- **Log processing**: `LogDataExtractor` reads and processes logs
- **Error tracking**: Automatic error context collection
- **Performance metrics**: Execution time aggregation

### Dashboard Integration
- **Log viewer**: Real-time log display at http://localhost:8001
- **Filtering**: By log level and module
- **Search**: Full-text log search capabilities
- **Export**: Error logs can be exported for analysis

## Performance Optimizations

After cleanup:
- **Single module loading**: No duplicate imports
- **Efficient context handling**: Minimal overhead context managers
- **Memory management**: Automatic cleanup in long-running processes
- **I/O optimization**: Buffered log writing

## Best Practices

### 1. Use Enhanced Features
```python
# Good: Use parameter support
logger.info("Article parsed", article_id=123, word_count=500)

# Avoid: String formatting
logger.info(f"Article {article_id} parsed with {word_count} words")
```

### 2. Leverage Context Managers
```python
# Good: Structured context
with LogContext.operation("content_parsing", source="techcrunch"):
    for article in articles:
        with LogContext.article(article.id, article.url):
            parse_article(article)
```

### 3. Error Context
```python
# Good: Rich error context
try:
    result = firecrawl_client.extract(url)
except Exception as e:
    log_error(logger, e, {
        "url": url,
        "attempt": retry_count,
        "source_id": source.id
    })
```

## Migration Notes

### From Old System
- **Removed**: `core/logger.py` (unused duplicate)
- **Consolidated**: All logging through `app_logging`
- **Enhanced**: Parameter support added throughout
- **Optimized**: Single configuration system

### Backwards Compatibility
- All existing `get_logger()` calls work unchanged
- Context managers enhanced but maintain compatibility
- Configuration system extended but preserves existing settings

## Troubleshooting

### Common Issues

1. **No logs in monitoring**:
   - Check `logs/monitoring/system.log` exists
   - Verify monitoring process is running: `ps aux | grep monitoring`
   - Check log permissions in `logs/` directory

2. **Performance impact**:
   - Reduce log level in `app_logging/config.json`
   - Check for excessive context manager nesting
   - Monitor log file sizes

3. **Memory usage**:
   - Enhanced logger has minimal overhead
   - Context managers auto-cleanup
   - Long-running processes should restart periodically

### System Health
```bash
# Check logging system status
ls -la logs/
tail -f logs/monitoring/system.log
ps aux | grep -E "(monitoring|python.*main.py)"
```

## Future Enhancements

Planned improvements:
- **Structured JSON output**: For better parsing
- **Remote logging**: Integration with log aggregation services  
- **Advanced filtering**: Enhanced dashboard filtering options
- **Metrics export**: Prometheus/OpenTelemetry integration