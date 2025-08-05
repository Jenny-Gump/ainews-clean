# API Reference - AI News Parser

## Обзор

Система предоставляет два типа API:
1. **REST API** - HTTP endpoints для управления и мониторинга
2. **WebSocket API** - Реального времени обновления логов и метрик

Базовый URL: `http://localhost:8001`

## REST API Endpoints

### Системная информация

#### GET /api/system/info
Получить информацию о системе.

**Ответ:**
```json
{
  "version": "2.0.0",
  "environment": "production",
  "database_path": "/Users/skynet/Desktop/AI DEV/ainews-clean/data/ainews.db",
  "monitoring_db_path": "/Users/skynet/Desktop/AI DEV/ainews-clean/data/monitoring.db",
  "media_path": "/Users/skynet/Desktop/AI DEV/ainews-clean/data/media",
  "sources_count": 26,
  "active_sources": 26
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

### Управление парсингом

#### POST /api/crawl/start
Запустить процесс парсинга.

**Тело запроса:**
```json
{
  "phase": "all",  // all|rss|parse|media
  "source_ids": [1, 2, 3]  // опционально, для конкретных источников
}
```

**Ответ:**
```json
{
  "task_id": "task_123",
  "status": "started",
  "phase": "all",
  "estimated_time_minutes": 15
}
```

#### GET /api/crawl/status
Получить статус текущего парсинга.

**Ответ:**
```json
{
  "is_running": true,
  "current_phase": "parse",
  "progress": {
    "total": 100,
    "completed": 45,
    "failed": 2
  },
  "started_at": "2025-08-03T14:00:00Z",
  "estimated_completion": "2025-08-03T14:15:00Z"
}
```

### Экстракт API

#### GET /api/extract/config
Получить текущую конфигурацию Extract API.

**Ответ:**
```json
{
  "global_last_parsed": "2025-08-01T00:00:00Z",
  "batch_size": 10,
  "timeout_seconds": 30,
  "rate_limit": {
    "requests_per_minute": 60,
    "concurrent_requests": 5
  }
}
```

#### PUT /api/extract/config
Обновить конфигурацию Extract API.

**Тело запроса:**
```json
{
  "global_last_parsed": "2025-08-02T00:00:00Z"
}
```

**ПРОБЛЕМА**: Этот endpoint сохранял данные в дублированную БД вместо основной.

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

### Получить статистику за сегодня
```bash
curl http://localhost:8001/api/stats/overview
```

### Запустить полный цикл парсинга
```bash
curl -X POST http://localhost:8001/api/crawl/start \
  -H "Content-Type: application/json" \
  -d '{"phase": "all"}'
```

### Подключиться к логам через WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/logs');

ws.onmessage = (event) => {
  const log = JSON.parse(event.data);
  console.log(`[${log.level}] ${log.message}`);
};
```

## Найденные проблемы

1. **Отсутствует аутентификация** - API полностью открыт
2. **PUT /api/extract/config** - сохранял в неправильную БД
3. **GET /api/errors** - всегда пустой, логирование не работает
4. **Нет версионирования API** - сложно поддерживать обратную совместимость
5. **Отсутствуют rate limits** - можно перегрузить систему