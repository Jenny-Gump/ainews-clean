# Error Handling in AI News Parser System

## Overview
Comprehensive error tracking and handling system for RSS Discovery and Change Tracking modules with automatic cleanup and detailed logging.

## Error Logging Infrastructure

### Централизованное логирование в файлы
- **Основные файлы**: 
  - `logs/errors.jsonl` - все ошибки системы
  - `logs/operations.jsonl` - операции и метрики
- **Формат**: JSONL (JSON Lines) для легкого парсинга
- **Ротация**: Автоматическая при превышении 50MB
- **Очистка**: Автоматическое удаление через 7 дней

### Двухуровневая система логирования
1. **logger.error()** - для консоли и реального времени
2. **log_error()** - для централизованного хранения в JSONL

**Важно**: Для критических ошибок используются ОБА метода!

## Error Types

### RSS Discovery Errors

| Error Type | Description | Common Causes |
|------------|-------------|---------------|
| `rss_http_error` | HTTP status != 200 | Feed offline, 404, 403 |
| `rss_timeout` | Parsing timeout (10s) | Slow server, large feed |
| `rss_parse_warning` | Parser warnings | Malformed XML, encoding issues |
| `rss_general_error` | Any other error | Network issues, DNS failures |

### Change Tracking Errors

| Error Type | Description | Common Causes |
|------------|-------------|---------------|
| `tracking_scan_failed` | Failed after all retries | Site offline, blocking |
| `tracking_timeout` | Timeout (45s) | Slow site, large page |
| `tracking_fk_error` | Foreign key violation | Source not in DB |
| `tracking_db_error` | Database errors | Connection issues |
| `tracking_url_normalize_error` | URL normalization failed | Invalid URL format |

## Timeout Configuration

### Current Settings (as of August 2025)

#### Firecrawl Client
```python
# services/firecrawl_client.py:89-92
timeout=aiohttp.ClientTimeout(
    total=60,           # Total request timeout
    sock_connect=10,    # Connection timeout
    sock_read=30        # Socket read timeout
)
```

#### Change Tracking
```python
# change_tracking/monitor.py:229
timeout=45  # Asyncio timeout for scraping
```

#### RSS Discovery
```python
# services/rss_discovery.py:191
timeout=10  # RSS parsing timeout
```

## Retry Logic

### Change Tracking Retries
- **Max attempts**: 2 (configurable)
- **Retry delay**: Exponential backoff (2s, 4s, 8s...)
- **Implementation**: `change_tracking/monitor.py:163-166`

```python
wait_time = 2 ** (attempt + 1)  # 2s, 4s, 8s...
await asyncio.sleep(wait_time)
```

## Error Analysis

### Viewing Errors

#### Просмотр логов из файлов
```bash
# Последние RSS ошибки
grep "rss_" logs/errors.jsonl | tail -20

# Последние tracking ошибки  
grep "tracking_" logs/errors.jsonl | tail -20

# Все ошибки за последний час
tail -100 logs/errors.jsonl | jq '.timestamp' | sort

# Подсчет ошибок по типам
cat logs/errors.jsonl | jq '.error_type' | sort | uniq -c | sort -rn

# Ошибки по модулям
cat logs/errors.jsonl | jq '.module' | sort | uniq -c | sort -rn

# Топ источников с ошибками
cat logs/errors.jsonl | jq '.source_id' | sort | uniq -c | sort -rn | head -10
```

## Auto-cleanup

### Script Location
`scripts/clean_old_logs.sh`

### Что делает скрипт:
1. Удаляет файлы логов старше 7 дней
2. Ротирует большие файлы логов (>50MB)
3. Показывает статистику после очистки

### Manual Run
```bash
cd "/Users/skynet/Desktop/AI DEV/ainews-clean"
./scripts/clean_old_logs.sh
```

### Cron Setup (Daily at 3 AM)
```bash
crontab -e
# Add this line:
0 3 * * * /Users/skynet/Desktop/AI\ DEV/ainews-clean/scripts/clean_old_logs.sh
```

## Troubleshooting Common Issues

### 1. Empty Exception Messages
**Problem**: RSS errors showing empty exception field
**Solution**: Using `repr(e)` instead of `str(e)` for better error details
**File**: `services/rss_discovery.py:323`

### 2. Timeout Errors
**Problem**: 23% of Change Tracking sources timing out
**Solutions**:
- Increased sock_read from 10s to 30s
- Increased total timeout from 40s to 60s
- Increased Change Tracking timeout from 30s to 45s

### 3. Failed Sources
**Common problematic sources**:
- Anthropic News - Often slow response
- Google Cloud AI Blog - Large pages
- ABB Robotics - Geographic restrictions
- Stability AI - Rate limiting

### 4. Проблемы с логированием
**Симптомы**: Ошибки не появляются в errors.jsonl
**Проверить**:
- Импортирован ли log_error в модуле
- Вызывается ли log_error после logger.error
- Права доступа к папке logs/

## Monitoring Dashboard Integration

The monitoring dashboard (`http://localhost:8001`) displays:
- Real-time error counts
- Error trends over time
- Sources with most errors
- Success/failure rates

### Key Metrics
- **Error Rate**: Errors per hour
- **Success Rate**: Successful scans percentage
- **Top Failing Sources**: Sources with most errors
- **Error Types Distribution**: Breakdown by error type

## Best Practices

1. **Monitor error patterns** - Check for systematic issues
2. **Adjust timeouts** - Based on source requirements
3. **Review logs weekly** - Identify trending issues
4. **Update blocked domains** - Add consistently failing sources
5. **Test fixes locally** - Before deploying to production

## Related Documentation

- [Change Tracking Flow](./FLOW.md) - Overall system flow
- [Database Schema](../DATABASE_SCHEMA.md) - Complete DB structure
- [Troubleshooting Guide](../TROUBLESHOOTING.md) - General troubleshooting
- [Monitoring README](../../monitoring/README.md) - Dashboard details