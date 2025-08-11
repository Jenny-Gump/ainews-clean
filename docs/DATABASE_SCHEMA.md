# Схема баз данных AI News Parser

**Обновлено**: 9 августа 2025 - Добавлены поля для хранения сырых LLM ответов

## Обзор

Система AI News Parser Clean использует две SQLite базы данных:

1. **Основная база** (`/Users/skynet/Desktop/AI DEV/ainews-clean/data/ainews.db`) - хранение статей и медиафайлов
2. **База мониторинга** (`/Users/skynet/Desktop/AI DEV/ainews-clean/data/monitoring.db`) - метрики и мониторинг системы

## Схема основной базы данных

### Таблица sources
Хранит настроенные источники RSS лент.

```sql
CREATE TABLE sources (
    source_id TEXT PRIMARY KEY,           -- Уникальный идентификатор источника
    name TEXT NOT NULL,                   -- Отображаемое имя
    url TEXT NOT NULL,                    -- URL основного сайта  
    type TEXT,                           -- Тип источника (rss/crawl)
    has_rss INTEGER DEFAULT 0,            -- Флаг наличия RSS
    last_status TEXT,                     -- Последний статус
    last_error TEXT,                      -- Последняя ошибка
    success_rate REAL DEFAULT 0.0,        -- Процент успешности
    last_parsed DATETIME,                 -- Время последнего парсинга
    total_articles INTEGER DEFAULT 0,     -- Всего статей
    selectors TEXT,                       -- CSS селекторы (JSON)
    category TEXT,                        -- Категория источника
    validation_status TEXT,               -- Статус валидации
    circuit_breaker_failures INTEGER DEFAULT 0,     -- Счетчик сбоев
    circuit_breaker_reset_time TIMESTAMP,           -- Время сброса circuit breaker
    last_article_discovery DATETIME,     -- Последнее обнаружение статьи
    consecutive_failures INTEGER DEFAULT 0,         -- Последовательные сбои
    rss_url TEXT,                         -- URL RSS ленты
    last_rss_check DATETIME,              -- Последняя проверка RSS
    rss_fetch_frequency INTEGER DEFAULT 3600        -- Частота проверки RSS в секундах
);
```

### Таблица articles
Основное хранилище статей с контентом и метаданными.

```sql
CREATE TABLE articles (
    article_id TEXT PRIMARY KEY,          -- Уникальный SHA256 хеш от URL
    source_id TEXT NOT NULL,              -- FK к sources.source_id
    url TEXT NOT NULL UNIQUE,             -- URL статьи
    title TEXT,                           -- Заголовок статьи
    content TEXT,                         -- Полный текст статьи (очищенный DeepSeek)
    published_date DATETIME,              -- Дата публикации
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    content_status TEXT DEFAULT 'pending', -- pending/parsed/failed/published
    content_error TEXT,                   -- Сообщение об ошибке парсинга
    parsed_at DATETIME,                   -- Время успешного парсинга
    media_count INTEGER DEFAULT 0,        -- Количество медиафайлов
    media_status TEXT DEFAULT 'pending',  -- pending/ready/processing
    processing_session_id TEXT DEFAULT NULL,     -- UUID сессии обработки
    processing_started_at DATETIME DEFAULT NULL, -- Время начала обработки
    processing_worker_id TEXT DEFAULT NULL,      -- ID воркера
    processing_completed_at DATETIME DEFAULT NULL, -- Время завершения обработки
    description TEXT,                     -- Краткое описание из RSS (summary)
    discovered_via TEXT DEFAULT 'rss',    -- Источник обнаружения (rss/web_monitoring/change_tracking)
    llm_content_raw TEXT,                 -- Сырой ответ от DeepSeek при очистке контента (✅ НОВОЕ)
    llm_translation_raw TEXT,             -- Сырой ответ от DeepSeek/GPT-4o при переводе (✅ НОВОЕ)
    llm_tags_raw TEXT,                    -- Сырой ответ от DeepSeek/GPT-3.5 при генерации тегов (✅ НОВОЕ)
    
    FOREIGN KEY (source_id) REFERENCES sources(source_id)
);
```

### Таблица media_files  
Хранит скачанные медиафайлы с метаданными.

```sql
CREATE TABLE media_files (
    id INTEGER PRIMARY KEY,
    article_id TEXT NOT NULL,         -- FK к articles
    url TEXT NOT NULL,                -- Оригинальный URL медиа
    type TEXT,                        -- Тип медиа (image/video)
    file_path TEXT,                   -- Локальный путь хранения
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    media_id TEXT,                    -- Уникальный хеш медиа
    source_id TEXT,                   -- FK к sources
    file_size INTEGER,                -- Размер в байтах
    mime_type TEXT,                   -- MIME тип
    width INTEGER,                    -- Ширина изображения
    height INTEGER,                   -- Высота изображения
    alt_text TEXT,                    -- Alt текст изображения
    status TEXT DEFAULT 'pending',    -- pending/completed/failed
    error TEXT,                       -- Текст ошибки при загрузке
    source TEXT,                      -- Источник медиа
    caption TEXT,                     -- Подпись изображения
    wp_media_id INTEGER,              -- ID медиа в WordPress
    wp_upload_status TEXT DEFAULT 'pending', -- Статус загрузки в WP
    wp_uploaded_at DATETIME,          -- Время загрузки в WP
    alt_text_ru TEXT,                 -- Alt текст на русском
    caption_ru TEXT,                  -- Подпись на русском
    image_order INTEGER,              -- Порядок изображения в статье
    processing_session_id TEXT DEFAULT NULL,  -- UUID сессии обработки
    wp_source_url TEXT,               -- URL медиа в WordPress (✅ НОВОЕ)
    
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
    featured_image_index INTEGER,    -- Индекс главного изображения
    images_data TEXT,                 -- JSON данные изображений
    translation_status TEXT DEFAULT 'pending',  -- pending/translated/failed
    translation_error TEXT,           -- Текст ошибки при неудаче
    translated_at DATETIME,           -- Время перевода
    published_to_wp BOOLEAN DEFAULT 0,-- Флаг публикации в WordPress
    wp_post_id INTEGER,               -- ID поста в WordPress
    source_language TEXT,             -- Исходный язык (обычно 'en')
    target_language TEXT DEFAULT 'ru',-- Целевой язык
    llm_model TEXT,                   -- Модель DeepSeek (deepseek-reasoner или deepseek-chat)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,              -- Время последнего обновления
    processing_session_id TEXT DEFAULT NULL,  -- UUID сессии обработки
    
    FOREIGN KEY (article_id) REFERENCES articles(article_id)
);
```

### Таблица global_config
Системные настройки.

```sql
CREATE TABLE global_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,                 -- Описание параметра
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Ключевые значения**:
- `global_last_parsed`: Глобальная метка времени для синхронизации RSS

### Дополнительные таблицы основной базы

#### Таблица related_links
Хранит связанные ссылки из статей.

```sql
CREATE TABLE related_links (
    id INTEGER PRIMARY KEY,
    article_id TEXT NOT NULL,
    title TEXT NOT NULL,              -- Заголовок ссылки
    url TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (article_id) REFERENCES articles(article_id)
);
```

#### Таблица tracked_articles
Отслеживание изменений в статьях (Change Tracking).

```sql
CREATE TABLE tracked_articles (
    article_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    published_date DATETIME,
    content TEXT,
    last_checked DATETIME DEFAULT CURRENT_TIMESTAMP,
    previous_hash TEXT,
    current_hash TEXT,
    change_detected BOOLEAN DEFAULT FALSE,
    change_status TEXT,               -- new/unchanged/changed/removed
    exported_to_main BOOLEAN DEFAULT FALSE,
    exported_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### Таблица tracked_urls
Отслеживание обнаруженных URL на страницах источников.

```sql
CREATE TABLE tracked_urls (
    id INTEGER PRIMARY KEY,
    source_page_url TEXT NOT NULL,   -- URL страницы источника
    article_url TEXT NOT NULL,       -- URL обнаруженной статьи
    article_title TEXT,               -- Заголовок статьи
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    source_domain TEXT NOT NULL,     -- Домен источника
    is_new BOOLEAN DEFAULT 1,        -- Флаг новой статьи
    exported_to_articles BOOLEAN DEFAULT 0,  -- Экспортирована в основную таблицу
    exported_at DATETIME              -- Время экспорта
);
```

#### Таблица session_locks
Блокировки для предотвращения параллельной обработки одной статьи.

```sql
CREATE TABLE session_locks (
    article_id TEXT PRIMARY KEY,         -- ID статьи (уникальная блокировка)
    session_uuid TEXT NOT NULL,          -- UUID сессии
    worker_id TEXT NOT NULL,             -- ID воркера
    locked_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- Время блокировки
    heartbeat DATETIME DEFAULT CURRENT_TIMESTAMP, -- Последний heartbeat
    released_at DATETIME DEFAULT NULL,   -- Время освобождения блокировки
    status TEXT DEFAULT 'locked'         -- Статус блокировки (locked/released)
);
```

#### Таблица pipeline_sessions
Сессии выполнения пайплайна.

```sql
CREATE TABLE pipeline_sessions (
    id INTEGER PRIMARY KEY,
    started_at DATETIME NOT NULL,
    completed_at DATETIME,
    total_articles INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0
);
```

#### Таблица pipeline_operations
Операции в рамках сессий пайплайна.

```sql
CREATE TABLE pipeline_operations (
    id INTEGER PRIMARY KEY,
    session_id INTEGER,               -- FK к pipeline_sessions
    phase TEXT NOT NULL,              -- Фаза пайплайна
    operation TEXT NOT NULL,          -- Название операции
    status TEXT NOT NULL,             -- Статус выполнения
    details JSON,                     -- Детали операции
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES pipeline_sessions(id)
);
```

## Схема базы мониторинга

### Таблица performance_metrics
Метрики производительности системы.

```sql
CREATE TABLE performance_metrics (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    cpu_usage_percent REAL,           -- Использование CPU в процентах
    memory_usage_mb REAL,              -- Использование памяти в MB
    disk_usage_percent REAL,           -- Использование диска в процентах
    active_connections INTEGER,        -- Активные соединения
    queue_size INTEGER,                -- Размер очереди
    parse_rate_per_minute REAL,        -- Скорость парсинга в минуту
    error_rate_percent REAL            -- Процент ошибок
);
```

### Таблица source_health_reports
Отчеты о здоровье источников.

```sql
CREATE TABLE source_health_reports (
    id INTEGER PRIMARY KEY,
    source_id TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_healthy INTEGER,               -- Флаг здоровья
    health_score REAL,                -- Оценка здоровья
    issues TEXT,                      -- JSON с проблемами
    recommendations TEXT,              -- JSON с рекомендациями
    metrics_24h TEXT,                 -- Метрики за 24 часа
    metrics_7d TEXT,                  -- Метрики за 7 дней
    performance_trend TEXT            -- Тренд производительности
);
```

### Таблица source_metrics
Метрики источников.

```sql
CREATE TABLE source_metrics (
    id INTEGER PRIMARY KEY,
    source_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    success_rate REAL,                -- Процент успешности
    avg_parse_time_ms REAL,           -- Среднее время парсинга
    total_articles INTEGER,           -- Всего статей
    new_articles_24h INTEGER,         -- Новые статьи за 24 часа
    error_count INTEGER,              -- Количество ошибок
    last_error TEXT                   -- Последняя ошибка
);
```

### Таблица article_stats
Статистика по статьям.

```sql
CREATE TABLE article_stats (
    id INTEGER PRIMARY KEY,
    source_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_articles INTEGER,           -- Всего статей от источника
    new_articles_24h INTEGER,         -- Новые статьи за 24 часа
    avg_content_length INTEGER,       -- Средняя длина контента
    has_full_content INTEGER,         -- Количество с полным контентом
    parse_method TEXT,                -- Метод парсинга
    api_cost REAL                     -- Стоимость API
);
```

### Таблица error_logs
Детальное отслеживание ошибок.

```sql
CREATE TABLE error_logs (
    id INTEGER PRIMARY KEY,
    source_id TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    error_type TEXT,
    error_message TEXT,
    stack_trace TEXT,                 -- Стек вызовов
    context TEXT,                     -- JSON контекст
    correlation_id TEXT,              -- ID корреляции
    resolved INTEGER DEFAULT 0        -- Флаг решения
);
```

### Таблица memory_metrics
Метрики использования памяти.

```sql
CREATE TABLE memory_metrics (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_memory_mb REAL NOT NULL,    -- Всего памяти MB
    used_memory_mb REAL NOT NULL,     -- Использовано памяти MB
    available_memory_mb REAL NOT NULL,-- Доступно памяти MB
    processes_count INTEGER DEFAULT 0,         -- Количество процессов
    ainews_processes_count INTEGER DEFAULT 0,  -- Процессы AI News
    ainews_memory_mb REAL DEFAULT 0,           -- Память AI News MB
    top_consumer_memory_mb REAL DEFAULT 0      -- Макс потребление MB
);
```


### Таблица system_metrics
Общие системные метрики.

```sql
CREATE TABLE system_metrics (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    cpu_percent REAL,                 -- Использование CPU %
    memory_percent REAL,              -- Использование памяти %
    disk_percent REAL,                -- Использование диска %
    process_count INTEGER,            -- Количество процессов
    ainews_process_count INTEGER,     -- Процессы AI News
    network_connections INTEGER,      -- Сетевые соединения
    open_files INTEGER                -- Открытые файлы
);
```

### Таблица parsing_progress
Прогресс парсинга.

```sql
CREATE TABLE parsing_progress (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    parser_pid INTEGER,               -- PID процесса парсера
    status TEXT,                      -- Статус парсинга
    current_source TEXT,              -- Текущий источник
    total_sources INTEGER,            -- Всего источников
    processed_sources INTEGER,        -- Обработано источников
    total_articles INTEGER,           -- Всего статей
    progress_percent REAL,            -- Процент прогресса
    estimated_completion DATETIME,    -- Ожидаемое завершение
    last_update DATETIME              -- Последнее обновление
);
```

### Таблица extract_api_metrics
Метрики Firecrawl Extract API.

```sql
CREATE TABLE extract_api_metrics (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    url TEXT NOT NULL,                -- URL запроса
    cost_usd REAL NOT NULL,           -- Стоимость в USD
    response_time_ms REAL NOT NULL,   -- Время ответа в мс
    success INTEGER NOT NULL,         -- Успешность запроса
    content_length INTEGER DEFAULT 0, -- Длина контента
    error_message TEXT                -- Сообщение об ошибке
);
```

### Таблица extract_api_errors
Ошибки Firecrawl Extract API.

```sql
CREATE TABLE extract_api_errors (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    error_type TEXT NOT NULL,         -- Тип ошибки
    error_message TEXT NOT NULL,      -- Сообщение об ошибке
    url TEXT,                         -- URL запроса
    response_code INTEGER,            -- HTTP код ответа
    retry_count INTEGER DEFAULT 0     -- Количество повторов
);
```

### Таблица alerts
Системные алерты.

```sql
CREATE TABLE alerts (
    id TEXT PRIMARY KEY,              -- Уникальный ID алерта
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    level TEXT,                       -- Уровень алерта
    source TEXT,                      -- Источник алерта
    title TEXT,                       -- Заголовок алерта
    message TEXT,                     -- Сообщение
    details TEXT,                     -- Подробности
    resolved INTEGER DEFAULT 0,       -- Флаг решения
    resolved_at DATETIME              -- Время решения
);
```

### Таблица memory_alerts
Алерты по памяти (не используется).

```sql
CREATE TABLE memory_alerts (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    memory_usage_mb REAL,
    threshold_mb REAL,
    alert_level TEXT,                 -- warning/critical
    action_taken TEXT
);
```

### Таблица emergency_snapshots
Снимки системы при критических ситуациях (не используется).

```sql
CREATE TABLE emergency_snapshots (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    trigger TEXT,                     -- Что вызвало снимок
    system_state TEXT,                -- JSON состояния системы
    memory_usage_mb REAL,
    active_tasks TEXT                 -- JSON активных задач
);
```

### Таблица rss_feed_metrics
Метрики RSS лент (не используется).

```sql
CREATE TABLE rss_feed_metrics (
    id INTEGER PRIMARY KEY,
    source_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    fetch_time_ms REAL,
    items_found INTEGER,
    new_items INTEGER,
    errors TEXT                       -- JSON с ошибками
);
```

## Связи между данными

### Основная база данных
```
sources (1) -----> (N) articles
                        |
                        ├──> related_links (N)
                        ├──> tracked_articles (1)
                        ├──> media_files (N)
                        └──> wordpress_articles (1)

tracked_urls (N) - Независимая таблица для отслеживания URL

pipeline_sessions (1) -----> (N) pipeline_operations

global_config - Системные настройки
```

### База мониторинга
```
Метрики и мониторинг:
- performance_metrics     # Общие метрики производительности
- source_health_reports   # Отчеты о здоровье источников
- source_metrics          # Метрики источников
- article_stats           # Статистика по статьям
- error_logs              # Логи ошибок
- memory_metrics          # Метрики памяти
- system_metrics          # Системные метрики
- parsing_progress        # Прогресс парсинга
- extract_api_metrics     # Метрики Firecrawl API
- extract_api_errors      # Ошибки Firecrawl API
- alerts                  # Системные алерты

Не используются:
- emergency_snapshots
- rss_feed_metrics
- memory_alerts
```

**Важно**: 
- wordpress_articles создается только для articles со статусом 'completed'
- tracked_articles используется для Change Tracking через Firecrawl
- related_links хранит извлеченные ссылки из статей

## Ключевые индексы

### Основная база
- `articles.url` (UNIQUE)
- `articles.article_id` (PRIMARY)
- `articles.source_id` (FOREIGN KEY)
- `articles.content_status`
- `articles.llm_content_raw` (PARTIAL INDEX WHERE NOT NULL) ✅ НОВЫЙ
- `articles.llm_translation_raw` (PARTIAL INDEX WHERE NOT NULL) ✅ НОВЫЙ
- `articles.llm_tags_raw` (PARTIAL INDEX WHERE NOT NULL) ✅ НОВЫЙ
- `media_files.article_id` (FOREIGN KEY)
- `media_files.media_id` (PRIMARY)
- `media_files.wp_source_url` (INDEX WHERE NOT NULL)
- `wordpress_articles.article_id` (UNIQUE)
- `wordpress_articles.translation_status`
- `session_locks.article_id` (PRIMARY)

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

## Остающиеся рекомендации

1. Периодически очищать orphaned медиафайлы
2. Включить проверку внешних ключей в SQLite
3. Добавить составные индексы для частых запросов

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
LEFT JOIN articles a ON s.source_id = a.source_id
WHERE a.content_status = 'parsed'
GROUP BY s.source_id;
```

### Последние ошибки парсинга
```sql
SELECT source_id, error_type, error_message, timestamp
FROM error_logs
WHERE resolved = 0
ORDER BY timestamp DESC
LIMIT 10;
```

### Статистика переводов
```sql
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN translation_status = 'translated' THEN 1 ELSE 0 END) as translated,
    SUM(CASE WHEN published_to_wp = 1 THEN 1 ELSE 0 END) as published
FROM wordpress_articles;
```

### Анализ LLM ответов (НОВОЕ)
```sql
-- Найти статьи с ошибками парсинга JSON
SELECT article_id, title, content_error,
       LENGTH(llm_content_raw) as content_resp_len,
       LENGTH(llm_translation_raw) as trans_resp_len
FROM articles 
WHERE content_error LIKE '%JSON%' OR content_error LIKE '%escape%'
ORDER BY created_at DESC;

-- Статистика по LLM ответам
SELECT 
    COUNT(*) as total_articles,
    COUNT(llm_content_raw) as with_content_resp,
    COUNT(llm_translation_raw) as with_trans_resp,
    COUNT(llm_tags_raw) as with_tags_resp,
    AVG(LENGTH(llm_content_raw)) as avg_content_size
FROM articles;

-- Просмотр сырого ответа для отладки
SELECT article_id, title, 
       SUBSTR(llm_content_raw, 1, 500) as content_preview,
       content_error
FROM articles 
WHERE article_id = 'b801127038583f37';
```

## История изменений

### 9 августа 2025 - Добавлены поля для хранения сырых LLM ответов
- ✅ **Добавлены 3 новых поля в articles**: `llm_content_raw`, `llm_translation_raw`, `llm_tags_raw`
- ✅ **Цель**: Сохранение сырых ответов от LLM для отладки проблем с парсингом JSON
- ✅ **Частичные индексы**: Добавлены для быстрого поиска статей с LLM ответами
- ✅ **MVP подход**: Минимальные изменения кода, поля nullable для обратной совместимости
- ✅ **Миграция**: `migrations/004_add_llm_raw_responses.sql`

### 8 августа 2025 - Исправление RSS Discovery и добавление недостающих полей
- ✅ **Добавлены поля в articles**: `description` и `discovered_via` для RSS Discovery
- ✅ **Исправлена критическая ошибка**: RSS Discovery не мог сохранять статьи
- ✅ **66 pending статей**: Успешно добавлены после исправления

### 8 августа 2025 - Полная синхронизация с реальной структурой БД
- ✅ **Проверена реальная структура**: Все таблицы проверены через MCP SQLite
- ✅ **Добавлены новые поля**: `processing_session_id`, `wp_source_url` в media_files
- ✅ **Добавлена таблица session_locks**: Блокировки для параллельной обработки
- ✅ **Исправлен порядок полей**: Приведено в соответствие с реальной БД
- ✅ **Обновлены индексы**: Добавлен индекс для `wp_source_url`
- ✅ **Актуализированы связи**: Добавлены поля обработки сессий

### 7 августа 2025 - Legacy Code Cleanup
- Удалены неиспользуемые поля Extract API из таблицы `articles`
- Оптимизированы базы данных через VACUUM
- Добавлена валидация контента (минимум 300 слов)