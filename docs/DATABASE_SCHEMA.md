# Схема баз данных AI News Parser

## Обзор

Система AI News Parser Clean использует две SQLite базы данных:

1. **Основная база** (`/Users/skynet/Desktop/AI DEV/ainews-clean/data/ainews.db`) - хранение статей и медиафайлов
2. **База мониторинга** (`/Users/skynet/Desktop/AI DEV/ainews-clean/data/monitoring.db`) - метрики и мониторинг системы

## Схема основной базы данных

### Таблица sources
Хранит настроенные источники RSS лент.

```sql
CREATE TABLE sources (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,              -- Отображаемое имя
    url TEXT NOT NULL,               -- URL основного сайта  
    rss_url TEXT NOT NULL,           -- URL RSS ленты
    category TEXT,                   -- Категория источника
    is_active BOOLEAN DEFAULT 1,     -- Флаг активности
    extract_rules TEXT,              -- JSON правила для Firecrawl
    extract_wait_for TEXT           -- CSS селектор для ожидания
);
```

### Таблица articles
Основное хранилище статей с контентом и метаданными.

```sql
CREATE TABLE articles (
    article_id TEXT PRIMARY KEY,      -- Уникальный SHA256 хеш от URL
    source_id INTEGER,                -- FK к sources.id
    url TEXT UNIQUE NOT NULL,         -- URL статьи
    title TEXT NOT NULL,              -- Заголовок статьи
    content TEXT,                     -- Полный текст статьи
    published_date DATETIME,          -- Дата публикации
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    content_status TEXT DEFAULT 'pending', -- pending/completed/failed
    
    -- Поля Extract API
    extract_success BOOLEAN,          -- Флаг успешного извлечения
    extract_markdown TEXT,            -- Markdown версия
    summary TEXT,                     -- AI-сгенерированное резюме
    tags TEXT,                        -- Извлеченные теги (JSON)
    categories TEXT,                  -- Извлеченные категории (JSON)
    media_count INTEGER DEFAULT 0,    -- Количество медиафайлов
    language TEXT,                    -- Определенный язык
    
    FOREIGN KEY (source_id) REFERENCES sources(id)
);
```

### Таблица media_files  
Хранит скачанные медиафайлы с метаданными.

```sql
CREATE TABLE media_files (
    media_id TEXT PRIMARY KEY,        -- Уникальный хеш
    article_id TEXT NOT NULL,         -- FK к articles
    url TEXT NOT NULL,                -- Оригинальный URL медиа
    file_path TEXT,                   -- Локальный путь хранения
    alt_text TEXT,                    -- Alt текст изображения
    caption TEXT,                     -- Подпись изображения
    mime_type TEXT,                   -- MIME тип
    file_size INTEGER,                -- Размер в байтах
    width INTEGER,                    -- Ширина изображения
    height INTEGER,                   -- Высота изображения
    download_time_ms REAL,            -- Время загрузки
    status TEXT DEFAULT 'pending',    -- pending/completed/failed
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (article_id) REFERENCES articles(article_id)
);
```


### Таблица wordpress_articles
Хранит переведенный контент готовый для WordPress.

```sql
CREATE TABLE wordpress_articles (
    id INTEGER PRIMARY KEY,
    article_id TEXT NOT NULL UNIQUE,  -- FK к articles (уникальный)
    title TEXT NOT NULL,              -- Заголовок на русском
    content TEXT NOT NULL,            -- HTML контент на русском
    excerpt TEXT,                     -- Краткое описание (150-200 символов)
    slug TEXT NOT NULL,               -- URL slug (транслитерация)
    categories TEXT,                  -- JSON массив категорий
    tags TEXT,                        -- JSON массив тегов
    _yoast_wpseo_title TEXT,         -- SEO заголовок (до 60 символов)
    _yoast_wpseo_metadesc TEXT,      -- SEO описание (до 160 символов)
    focus_keyword TEXT,               -- Главное ключевое слово
    featured_image_index INTEGER DEFAULT 0,     -- Не используется (изображения убраны)
    images_data TEXT DEFAULT '{}',    -- Не используется (изображения убраны)
    translation_status TEXT DEFAULT 'pending',  -- pending/translated/failed
    translation_error TEXT,           -- Текст ошибки при неудаче
    translated_at DATETIME,           -- Время перевода
    published_to_wp BOOLEAN DEFAULT 0,-- Флаг публикации в WordPress
    wp_post_id INTEGER,               -- ID поста в WordPress
    source_language TEXT,             -- Исходный язык (обычно 'en')
    target_language TEXT DEFAULT 'ru',-- Целевой язык
    llm_model TEXT,                   -- Модель DeepSeek (deepseek-reasoner или deepseek-chat)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (article_id) REFERENCES articles(article_id)
);
```

### Таблица global_config
Системные настройки.

```sql
CREATE TABLE global_config (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Ключевые значения**:
- `global_last_parsed`: Глобальная метка времени для синхронизации RSS

## Схема базы мониторинга

### Таблица source_metrics
Отслеживает здоровье и производительность источников.

```sql
CREATE TABLE source_metrics (
    id INTEGER PRIMARY KEY,
    source_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_articles INTEGER DEFAULT 0,
    success_rate REAL DEFAULT 0,
    avg_parse_time_ms REAL DEFAULT 0,
    content_quality_score REAL DEFAULT 0,
    last_status TEXT,
    health_score REAL DEFAULT 0,
    recent_errors_24h INTEGER DEFAULT 0,
    performance_trend TEXT,
    blocked_days INTEGER DEFAULT 0,
    last_healthy DATETIME,
    crawl_frequency_hours REAL,
    media_success_rate REAL DEFAULT 100
);
```

### Таблица system_metrics
Общая производительность системы.

```sql
CREATE TABLE system_metrics (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    cpu_usage REAL,
    memory_usage REAL,
    disk_usage REAL,
    active_parsers INTEGER DEFAULT 0,
    queue_size INTEGER DEFAULT 0,
    articles_per_hour REAL DEFAULT 0,
    api_calls_per_hour REAL DEFAULT 0,
    avg_article_parse_time_ms REAL DEFAULT 0,
    total_errors INTEGER DEFAULT 0,
    uptime_hours REAL DEFAULT 0
);
```

### Таблица parse_history
Записи индивидуальных сессий парсинга.

```sql
CREATE TABLE parse_history (
    id INTEGER PRIMARY KEY,
    source_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN,
    article_count INTEGER DEFAULT 0,
    parse_time_ms REAL,
    error_type TEXT,
    error_message TEXT,
    response_time_ms REAL,
    content_quality REAL,
    media_success_rate REAL DEFAULT 100
);
```

### Таблица error_logs
Детальное отслеживание ошибок.

```sql
CREATE TABLE error_logs (
    id INTEGER PRIMARY KEY,
    source_id TEXT,
    error_type TEXT,
    error_message TEXT,
    context TEXT,                     -- JSON контекст
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**ПРОБЛЕМА**: Таблица существует но содержит 0 записей - логирование ошибок не реализовано.

### Таблица api_metrics
Отслеживание использования Firecrawl API.

```sql
CREATE TABLE api_metrics (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    endpoint TEXT,
    method TEXT,
    status_code INTEGER,
    response_time_ms REAL,
    request_size INTEGER,
    response_size INTEGER,
    error_message TEXT,
    api_key_usage TEXT
);
```

## Связи между данными

```
sources (1) -----> (N) articles
   |                      |
   |                      v
   |                 media_files (N)
   |                      |
   |                      v
   v                wordpress_articles (1)
source_metrics (N)
parse_history (N)
error_logs (N)
```

**Важно**: wordpress_articles создается только для articles со статусом 'completed'. Изображения из media_files НЕ используются в Phase 4.

## Ключевые индексы

### Основная база
- `articles.url` (UNIQUE)
- `articles.article_id` (PRIMARY)
- `articles.source_id` (FOREIGN KEY)
- `articles.content_status`
- `media_files.article_id` (FOREIGN KEY)
- `media_files.media_id` (PRIMARY)
- `wordpress_articles.article_id` (UNIQUE)
- `wordpress_articles.translation_status`

### База мониторинга
- `source_metrics.source_id`
- `source_metrics.timestamp`
- `parse_history.source_id`
- `error_logs.source_id`

## Проблемы целостности данных

1. **Orphaned медиафайлы**: При удалении статей медиафайлы остаются в БД
2. **Нет проверки внешних ключей**: Стандартные настройки SQLite
3. **Предотвращение дубликатов**: Только уникальность URL
4. **Обработка транзакций**: Некоторые операции не атомарны

## Рекомендуемые исправления

1. Периодически очищать orphaned медиафайлы
2. Включить проверку внешних ключей в SQLite
3. Добавить составные индексы для частых запросов
4. Реализовать правильные границы транзакций
5. Добавить ограничения валидации данных

## Примеры критических запросов

### Получение глобального last_parsed
```sql
SELECT value FROM global_config WHERE key = 'global_last_parsed';
```

### Поиск orphaned медиафайлов
```sql
SELECT COUNT(*) FROM media_files m 
LEFT JOIN articles a ON m.article_id = a.article_id 
WHERE a.article_id IS NULL;
```

### Статистика по источникам
```sql
SELECT s.name, COUNT(a.article_id) as article_count,
       AVG(LENGTH(a.content)) as avg_content_length
FROM sources s
LEFT JOIN articles a ON s.id = a.source_id
WHERE a.content_status = 'completed'
GROUP BY s.id;
```