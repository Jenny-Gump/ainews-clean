# Phase 2: Content Parsing

> 📚 **Навигация**: [← Phase 1](phase1_rss_discovery.md) | [← Все фазы](../README.md#-пятифазный-пайплайн-обработки) | [→ Phase 3](phase3_media_processing.md)

## Обзор
Вторая фаза - извлечение полного контента статей используя Firecrawl Extract API.

## Основные компоненты
- **ContentParser** (`services/content_parser.py`) - парсер контента
- **FirecrawlClient** (`services/firecrawl_client.py`) - клиент для Extract API

## Процесс работы

### 1. Выборка pending статей
```python
# Получаем статьи со статусом 'pending'
pending_articles = db.execute("""
    SELECT article_id, source_id, url, title 
    FROM articles 
    WHERE content_status = 'pending'
    ORDER BY created_at ASC
""")
```

### 2. Парсинг через Extract API
```python
# Строго по 1 статье за раз
result = await parser.parse_single_article(
    article_id=article['article_id'],
    url=article['url'],
    source_id=article['source_id']
)
```

### 3. Extract API параметры
```json
{
    "url": "article_url",
    "formats": ["extract"],
    "includeTags": ["img", "video", "iframe"],
    "removeSelector": "nav, footer, .ads",
    "timeout": 120000
}
```

### 4. Обработка результата
- **Контент**: markdown формат от Extract API
- **Метаданные**: автор, дата публикации, теги
- **Медиа**: ссылки на изображения и видео
- **Related links**: связанные статьи

### 5. Сохранение в БД
- Обновление `articles` таблицы
- Создание записей в `media_files` (если найдены изображения)
- Установка статусов:
  - `content_status = 'parsed'`
  - `media_status = 'processing'` (если есть медиа) или `'ready'` (если нет медиа)

## База данных
```sql
-- Обновление статьи
UPDATE articles SET
    content = ?,
    content_status = 'parsed',
    parsed_at = ?,
    media_count = ?,
    media_status = ?    -- 'processing' или 'ready'
WHERE article_id = ?

-- Медиафайлы
INSERT INTO media_files (
    article_id, url, type, alt_text, caption
) VALUES (?, ?, ?, ?, ?)
```

## Команда запуска
```bash
python core/main.py --parse-pending
```

## Особенности
- **Rate limiting**: 1 статья за раз
- **Retry логика**: 3 попытки с экспоненциальной задержкой
- **Обработка ошибок**: graceful degradation
- **Логирование**: структурированные логи с контекстом

## Метрики
- Успешно спарсено
- Ошибки парсинга
- Среднее время парсинга
- API использование