# API Reference - AI News Parser Clean

## Обзор

Мониторинг система предоставляет REST API и WebSocket endpoints для управления и наблюдения за AI News Parser.

Базовый URL: `http://localhost:8001`

## Статус: ВОССТАНОВЛЕННАЯ ВЕРСИЯ
- Основана на clean-системе от 7 августа 2025
- Убраны защитные системы (SessionManager, Supervisor)
- Простая архитектура без сложных таблиц сессий

## REST API Endpoints

### Системная информация

#### GET /api/system/info
Получить информацию о системе.

**Ответ:**
```json
{
  "version": "3.0.0",
  "environment": "production",
  "database": "Supabase PostgreSQL",
  "database_url": "https://mtguynupyltlqiwhmilc.supabase.co",
  "media_path": "/Users/skynet/Desktop/AI DEV/ainews-clean/data/media",
  "sources_count": 30,
  "active_sources": 30,
  "total_tables": 11
}
```

#### GET /api/system/status
Получить текущий статус системы.

**Ответ:**
```json
{
  "status": "running",
  "uptime_hours": 24.5,
  "last_crawl": "2025-08-03T14:30:00Z",
  "active_processes": 0,
  "queue_size": 0
}
```

### Управление источниками

#### GET /api/sources
Получить список всех источников.

**Параметры запроса:**
- `active_only` (boolean): Только активные источники

**Ответ:**
```json
[
  {
    "id": 1,
    "name": "TechCrunch AI",
    "url": "https://techcrunch.com",
    "rss_url": "https://techcrunch.com/category/artificial-intelligence/rss",
    "category": "news",
    "is_active": true,
    "last_parsed": "2025-08-03T14:00:00Z",
    "health_score": 85.5,
    "article_count": 156
  }
]
```

#### GET /api/sources/{source_id}
Получить детальную информацию об источнике.

**Ответ:**
```json
{
  "id": 1,
  "name": "TechCrunch AI",
  "metrics": {
    "total_articles": 156,
    "success_rate": 92.5,
    "avg_parse_time_ms": 234,
    "last_error": null,
    "recent_errors_24h": 0
  }
}
```

#### POST /api/sources/{source_id}/toggle
Включить/выключить источник.

**Тело запроса:**
```json
{
  "is_active": true
}
```

### Управление статьями

#### GET /api/articles
Получить список статей с пагинацией.

**Параметры запроса:**
- `page` (int): Номер страницы (default: 1)
- `limit` (int): Количество на странице (default: 20)
- `status` (string): Фильтр по статусу (pending/completed/failed)
- `source_id` (int): Фильтр по источнику
- `date_from` (string): Начальная дата (ISO format)
- `date_to` (string): Конечная дата (ISO format)

**Ответ:**
```json
{
  "articles": [
    {
      "article_id": "a1b2c3d4",
      "title": "OpenAI представила GPT-5",
      "url": "https://example.com/article",
      "source_name": "TechCrunch AI",
      "published_date": "2025-08-03T10:00:00Z",
      "content_status": "completed",
      "media_count": 3,
      "language": "en"
    }
  ],
  "total": 1250,
  "page": 1,
  "pages": 63
}
```

#### GET /api/articles/{article_id}
Получить полную информацию о статье.

**Ответ:**
```json
{
  "article_id": "a1b2c3d4",
  "title": "OpenAI представила GPT-5",
  "content": "...",
  "summary": "...",
  "tags": ["AI", "OpenAI", "GPT-5"],
  "categories": ["LLM", "Technology"],
  "media_files": [
    {
      "media_id": "m1",
      "url": "https://example.com/image.jpg",
      "file_path": "/media/2025/08/image.jpg",
      "width": 1200,
      "height": 800
    }
  ]
}
```

### Статистика и метрики

#### GET /api/stats/overview
Общая статистика системы.

**Ответ:**
```json
{
  "total_articles": 5423,
  "articles_today": 45,
  "articles_week": 312,
  "total_media_files": 1872,
  "orphaned_media_files": 255,
  "total_sources": 26,
  "active_sources": 24,
  "failed_sources": 2,
  "disk_usage_mb": 4567.8
}
```

#### GET /api/stats/sources
Статистика по источникам.

**Ответ:**
```json
[
  {
    "source_id": 1,
    "source_name": "TechCrunch AI",
    "article_count": 156,
    "success_rate": 92.5,
    "avg_articles_per_day": 4.5,
    "last_successful_parse": "2025-08-03T14:00:00Z"
  }
]
```

### Управление пайплайном

#### POST /api/pipeline/start
Запустить single-pipeline (обработка одной статьи).

**ВАЖНО**: Используйте ТОЛЬКО через dashboard. Прямые вызовы не рекомендуются.

**Ответ:**
```json
{
  "status": "started",
  "message": "Single pipeline started",
  "estimated_time_minutes": 5
}
```

#### POST /api/rss/discover
Запустить RSS discovery (фаза 1).

**Ответ:**
```json
{
  "status": "started", 
  "message": "RSS discovery started",
  "sources_count": 30
}
```

#### GET /api/pipeline/status
Получить статус пайплайна.

**Ответ:**
```json
{
  "is_running": false,
  "last_run": "2025-08-11T10:30:00Z",
  "queue_pending": 5,
  "queue_failed": 1,
  "processing_status": "idle"
}
```

### Change Tracking API

#### POST /api/tracking/scan
Запустить сканирование изменений источников.

**Тело запроса:**
```json
{
  "limit": 5,
  "batch_size": 3
}
```

**Ответ:**
```json
{
  "status": "started",
  "sources_to_scan": 5,
  "estimated_time_minutes": 10
}
```

#### GET /api/tracking/stats
Получить статистику change tracking.

**Ответ:**
```json
{
  "total_tracked": 1205,
  "new_today": 15,
  "changed_today": 8,
  "unchanged_today": 45,
  "sources_scanned": 45
}
```

### Логи и ошибки

#### GET /api/logs
Получить последние логи.

**Параметры запроса:**
- `limit` (int): Количество записей (default: 100)
- `level` (string): Уровень логов (DEBUG/INFO/WARNING/ERROR)
- `source` (string): Фильтр по источнику

**Ответ:**
```json
[
  {
    "timestamp": "2025-08-03T14:30:45Z",
    "level": "INFO",
    "message": "RSS Discovery completed",
    "source": "rss_discovery",
    "context": {
      "articles_found": 45
    }
  }
]
```

#### GET /api/errors
Получить последние ошибки.

**ПРОБЛЕМА**: Возвращает пустой массив, так как error_logs не заполняется.

## WebSocket API

### WS /ws/logs
Реального времени поток логов.

**Подключение:**
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/logs');
```

**Формат сообщений:**
```json
{
  "timestamp": "2025-08-03T14:30:45Z",
  "level": "INFO",
  "message": "Processing article",
  "context": {
    "article_id": "a1b2c3d4",
    "source": "TechCrunch AI"
  }
}
```

### WS /ws/metrics
Реального времени метрики системы.

**Подключение:**
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/metrics');
```

**Формат сообщений:**
```json
{
  "timestamp": "2025-08-03T14:30:45Z",
  "metrics": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "active_parsers": 3,
    "queue_size": 12,
    "articles_per_minute": 2.5
  }
}
```

## Аутентификация

**ПРОБЛЕМА**: API не имеет аутентификации - любой может получить доступ.

## Лимиты и ограничения

- Максимальный размер страницы: 100 записей
- Таймаут запросов: 30 секунд
- WebSocket переподключение: каждые 30 секунд ping/pong

## Коды ошибок

- `400` - Неверные параметры запроса
- `404` - Ресурс не найден
- `409` - Конфликт (например, парсинг уже запущен)
- `500` - Внутренняя ошибка сервера

## Примеры использования

### Получить статистику системы
```bash
curl http://localhost:8001/api/stats/overview
```

### Запустить single pipeline
```bash
curl -X POST http://localhost:8001/api/pipeline/start
```

### Запустить RSS discovery
```bash
curl -X POST http://localhost:8001/api/rss/discover
```

### Сканировать изменения источников
```bash
curl -X POST http://localhost:8001/api/tracking/scan \
  -H "Content-Type: application/json" \
  -d '{"limit": 5}'
```

### Подключиться к логам через WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/logs');

ws.onmessage = (event) => {
  const log = JSON.parse(event.data);
  console.log(`[${log.level}] ${log.message}`);
};
```

## Supabase Database API

### Direct Database Access
Система использует Supabase PostgreSQL через REST API и Python клиент.

**База данных:** `https://mtguynupyltlqiwhmilc.supabase.co`

**Таблицы (11 total):**
- `articles` - основные статьи
- `wordpress_articles` - переведённые статьи  
- `media_files` - медиафайлы
- `sources` - источники новостей
- `tracked_articles` - отслеживание изменений
- `tracked_urls` - найденные URL
- `pipeline_operations` - операции пайплайна
- `global_config` - конфигурация
- `system_metrics` - системные метрики
- `performance_metrics` - метрики производительности
- `memory_metrics` - метрики памяти

### Python Client Usage
```python
from services.supabase_client import get_supabase_client

client = get_supabase_client()

# Получить pending статьи
result = client.table('articles').select('*').eq('content_status', 'pending').execute()

# Обновить статус
client.table('articles').update({'content_status': 'parsed'}).eq('article_id', 'xyz').execute()
```

### MCP Server Access (для Claude)
```bash
# Выполнить SQL запрос
claude mcp supabase execute_sql --query "SELECT COUNT(*) FROM articles"

# Получить схему таблицы
claude mcp supabase list_tables
```

## Особенности текущей версии

### ✅ Что работает:
- Базовые endpoints статистики
- WebSocket для real-time логов
- Dashboard UI для управления
- Single pipeline через кнопку

### ⚠️ Ограничения:
- Нет аутентификации (только локальный доступ)
- Нет защитных систем (SessionManager убран)
- Простая архитектура без сложной диагностики
- Запуск пайплайна ТОЛЬКО через dashboard

### 🔧 Рекомендации:
- Используйте dashboard для всех операций
- Мониторьте логи через WebSocket
- Для production добавьте аутентификацию