# AI News Parser - Processing Flow Documentation

**Версия**: 2.0  
**Последнее обновление**: 11 августа 2025  
**Назначение**: Детальное описание всех процессов парсинга по шагам

## 📋 Обзор

Этот документ детально описывает каждый этап обработки новостей в системе AI News Parser Clean, включая основную систему (Single Pipeline) и модуль Change Tracking. Каждый процесс разложен по шагам с указанием того, как данные фильтруются и попадают в итоговые таблицы.

## 🔄 Основная система (Single Pipeline)

### Phase 1: RSS Discovery
**Файл**: `services/rss.py`  
**Команда**: `python core/main.py --rss-discover`

#### Шаг 1.1: Загрузка RSS источников
```python
# sources.json → RSS URLs
sources = [
    {"source_id": "openai", "rss_url": "https://openai.com/news/rss"},
    {"source_id": "anthropic", "rss_url": "https://www.anthropic.com/news.rss"}
]
```

#### Шаг 1.2: Парсинг RSS feeds
```python
for source in sources:
    feed = feedparser.parse(source['rss_url'])
    for entry in feed.entries:
        article = {
            'url': entry.link,
            'title': entry.title, 
            'published_date': entry.published,
            'source_id': source['source_id']
        }
```

#### Шаг 1.3: Фильтрация дубликатов
```sql
-- Проверка существования URL в БД
SELECT COUNT(*) FROM articles WHERE url = ?
-- Если > 0, пропустить статью
```

#### Шаг 1.4: Сохранение в БД
```sql
INSERT INTO articles (
    article_id, source_id, url, title, published_date,
    content_status, media_status, discovered_via
) VALUES (
    ?, ?, ?, ?, ?, 'pending', 'pending', 'rss'
);
```

**Результат Phase 1**: Статьи со статусом `pending` в таблице `articles`

---

### Phase 2: Content Parsing  
**Файл**: `services/content_parser.py`  
**Команда**: `python core/main.py --single-pipeline`

#### Шаг 2.1: Выборка статьи для парсинга
```sql
SELECT * FROM articles 
WHERE content_status = 'pending' 
ORDER BY created_at ASC 
LIMIT 1;
```

#### Шаг 2.2: Firecrawl Scrape API запрос
```python
# Запрос к Firecrawl Scrape API
response = firecrawl.scrape_url(article_url)
raw_markdown = response['markdown']
raw_html = response['html']
```

#### Шаг 2.3: DeepSeek AI обработка контента
```python
# Загрузка промпта из prompts/content_cleaner.txt
prompt = load_prompt('content_cleaner', url=article_url, content=raw_markdown)

# Отправка в DeepSeek API
response = deepseek_api.complete(prompt)
cleaned_content = response['content']

# Извлечение данных из JSON ответа
{
    "title": "Clean Article Title",
    "content": "Article content with [IMAGE_1] placeholders",
    "images": [
        {"url": "https://cdn.example.com/image1.jpg", "alt": "Image description"}
    ],
    "summary": "Brief summary"
}
```

#### Шаг 2.4: Валидация контента
```python
def validate_content(content: str) -> bool:
    # Минимум 300 слов для предотвращения paywall
    word_count = len(content.split())
    if word_count < 300:
        return False
        
    # Проверка на фантазийный контент
    if "I don't have access" in content:
        return False
        
    return True
```

#### Шаг 2.5: Сохранение результата
```sql
-- При успехе
UPDATE articles SET
    title = ?,
    content = ?,
    summary = ?,
    content_status = 'parsed',
    updated_at = CURRENT_TIMESTAMP
WHERE article_id = ?;

-- При ошибке
UPDATE articles SET
    content_status = 'failed',
    error_message = ?
WHERE article_id = ?;
```

**Результат Phase 2**: Статья со статусом `parsed` и готовым контентом

---

### Phase 3: Media Processing
**Файл**: `services/media_processing.py`

#### Шаг 3.1: Извлечение URL изображений
```python
# Из DeepSeek ответа
images = parsed_response['images']
valid_images = []

for img in images:
    if self.validate_image_url(img['url']):
        valid_images.append(img)
```

#### Шаг 3.2: Проверка изображений
```python
def validate_image_url(self, url: str) -> bool:
    try:
        response = requests.head(url)
        # Проверка размера (мин. 250x250px)
        if 'content-length' in response.headers:
            size = int(response.headers['content-length'])
            return size > 10000  # ~10KB минимум
        return True
    except:
        return False
```

#### Шаг 3.3: Дедупликация изображений
```python
# Удаление дубликатов по URL
seen_urls = set()
unique_images = []
for img in valid_images:
    if img['url'] not in seen_urls:
        seen_urls.add(img['url'])
        unique_images.append(img)
```

#### Шаг 3.4: Сохранение медиа данных
```sql
INSERT INTO media_files (
    media_id, article_id, media_url, alt_text, 
    media_type, file_size, created_at
) VALUES (?, ?, ?, ?, 'image', ?, CURRENT_TIMESTAMP);

-- Обновление статуса статьи
UPDATE articles SET media_status = 'completed' WHERE article_id = ?;
```

**Результат Phase 3**: Статья с прикрепленными изображениями

---

### Phase 4: Translation & Publishing
**Файл**: `services/wordpress_publisher.py`

#### Шаг 4.1: Генерация тегов
```python
# Загрузка промпта из prompts/tag_generator.txt
prompt = load_prompt('tag_generator', 
    title=article_title,
    content=article_content,
    tags_list=curated_tags_74
)

# DeepSeek API для генерации тегов
response = deepseek_api.complete(prompt)
tags = response['tags']  # ['OpenAI', 'GPT-5', 'Machine Learning']
```

#### Шаг 4.2: Перевод статьи
```python
# Загрузка промпта из prompts/article_translator.txt  
prompt = load_prompt('article_translator',
    title=article_title,
    content=article_content,
    summary=article_summary
)

# DeepSeek API для перевода
response = deepseek_api.complete(prompt)
translated_data = {
    "title_ru": "Заголовок на русском",
    "content_ru": "<p>HTML контент с комментариями</p>",
    "category": "Новые модели",
    "excerpt_ru": "Краткое описание"
}
```

#### Шаг 4.3: Перевод метаданных изображений
```python
# Для каждого изображения
for image in media_files:
    prompt = load_prompt('image_metadata',
        alt_text=image['alt_text'],
        article_context=article_title
    )
    
    response = deepseek_api.complete(prompt)
    image['alt_text_ru'] = response['alt_text_ru']
    image['slug'] = response['slug']
```

#### Шаг 4.4: Публикация в WordPress
```python
# Создание поста
wp_post = {
    'title': translated_data['title_ru'],
    'content': translated_data['content_ru'],
    'status': 'publish',
    'categories': [category_id],
    'tags': tag_ids,
    'excerpt': translated_data['excerpt_ru'],
    'featured_media': featured_image_id
}

response = wp_api.posts.create(wp_post)
wp_post_id = response['id']
```

#### Шаг 4.5: Сохранение результата
```sql
INSERT INTO wordpress_articles (
    wordpress_id, article_id, title_ru, content_ru,
    category_ru, tags_ru, published_at
) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP);

UPDATE articles SET
    status = 'published',
    wordpress_id = ?
WHERE article_id = ?;
```

**Результат Phase 4**: Статья опубликована на https://ailynx.ru/

---

## 🔍 Change Tracking Flow

### CT Phase 1: Source Scanning
**Файл**: `change_tracking/monitor.py`  
**Команда**: `python core/main.py --change-tracking --scan --limit 5`

#### Шаг CT1.1: Загрузка источников
```python
# data/tracking_sources.json → URL list
sources = [
    {"source_id": "anthropic", "url": "https://www.anthropic.com/news"},
    {"source_id": "openai_tracking", "url": "https://openai.com/news/"}
]
```

#### Шаг CT1.2: Firecrawl changeTracking запрос
```python
for source in sources:
    response = firecrawl.scrape_url(source['url'])
    markdown_content = response['markdown']
    
    # Сохранение в БД
    result = {
        'url': source['url'],
        'content': markdown_content,
        'change_detected': False,
        'change_status': 'unchanged'
    }
```

#### Шаг CT1.3: Обнаружение изменений  
```python
# Вычисление хеша контента
current_hash = hashlib.md5(markdown_content.encode()).hexdigest()

# Сравнение с предыдущим хешем
if current_hash != previous_hash:
    result['change_detected'] = True
    result['change_status'] = 'changed'
```

#### Шаг CT1.4: Сохранение состояния
```sql
INSERT OR REPLACE INTO tracked_articles (
    article_id, source_id, url, content,
    current_hash, previous_hash, change_status,
    last_checked
) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP);
```

**Результат CT Phase 1**: Отслеживаемые страницы в `tracked_articles`

---

### CT Phase 2: URL Extraction  
**Файл**: `change_tracking/url_extractor.py`

#### Шаг CT2.1: Определение типа обработки
```python
# Проверка на escape-sequences
if any(domain in source_url for domain in escape_sources):
    urls = self._extract_escape_links(content, source_url, source_id)
else:
    urls = self._extract_all_links(content)
```

#### Шаг CT2.2: Извлечение ссылок (стандартный режим)
```python
# Поиск markdown ссылок
patterns = [
    r'\[([^\]]*)\]\((https?://[^)]+)\)',  # [text](url)
    r'\[([^\]]*)\]:\s*(https?://\S+)',    # [text]: url  
    r'<(https?://[^>]+)>'                 # <url>
]

for pattern in patterns:
    matches = re.finditer(pattern, content)
    for match in matches:
        title, url = match.groups()
        links.append((title, url))
```

#### Шаг CT2.3: Обработка escape-sequences
```python
# Для источников с \\\\\\\ в markdown
escape_pattern = r'([^]]*?(?:\\\\\\\\[^]]*?)*?)\]\((https?://[^)]+)\)'
matches = re.finditer(escape_pattern, content)

for match in matches:
    text_block = match.group(1)  # "Title\\\\\\\\Author\\\\\\\\Date" 
    url = match.group(2)
    
    # Извлечение заголовка из блока
    lines = text_block.split('\\\\\\\\')
    title = max(lines, key=len)  # Выбрать самую длинную строку
```

#### Шаг CT2.4: Фильтрация URL
```python
def _is_article_url(self, url: str, source_url: str) -> bool:
    # 1. Exclude patterns проверка
    for pattern in self.exclude_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return False
    
    # 2. Domain patterns проверка  
    if source_domain in self.domain_patterns:
        allowed_patterns = self.domain_patterns[source_domain]
        for pattern in allowed_patterns:
            if re.search(pattern, url_path):
                return True
        return False
    
    # 3. Общие новостные паттерны
    news_patterns = [r'/news/', r'/blog/', r'/2024/', r'/2025/']
    return any(re.search(p, url) for p in news_patterns)
```

#### Шаг CT2.5: Очистка заголовков
```python
def _clean_title(self, title: str) -> str:
    # Удаление escape-sequences
    cleaned = title.replace('\\\\\\\\', ' ')
    
    # Удаление markdown форматирования
    cleaned = re.sub(r'\*+', '', cleaned)  # **bold**
    cleaned = re.sub(r'`+', '', cleaned)   # `code`
    
    # Исключение навигационных элементов
    invalid_titles = ['read more', 'learn more', 'click here', ...]
    if cleaned.lower() in invalid_titles:
        return None
        
    return cleaned.strip()
```

#### Шаг CT2.6: Дедупликация и сохранение
```python
# Удаление дубликатов по URL
seen_urls = set()
unique_urls = []
for item in found_urls:
    if item['article_url'] not in seen_urls:
        seen_urls.add(item['article_url'])
        unique_urls.append(item)

# Результат: список извлеченных URL
extracted_urls = [
    {
        'article_url': 'https://anthropic.com/news/article1',
        'article_title': 'Clean Article Title',
        'source_domain': 'anthropic'
    }
]
```

**Результат CT Phase 2**: Список извлеченных URL статей

---

### CT Phase 3: Change Detection & Storage
**Файл**: `change_tracking/database.py` (изолированная БД для tracking)

#### Шаг CT3.1: Сравнение с существующими URL
```python
# Получение существующих URL из БД
existing_urls = set()
query = "SELECT DISTINCT url FROM tracked_articles WHERE source_id = ?"
existing_urls.update([row[0] for row in cursor.fetchall()])

# Поиск новых URL
new_urls = []
for url_data in extracted_urls:
    if url_data['article_url'] not in existing_urls:
        new_urls.append(url_data)
```

#### Шаг CT3.2: Обновление статистики в tracked_articles
```sql
-- Обновление основной записи с результатами сканирования
UPDATE tracked_articles SET
    content = ?, -- markdown + extracted URLs как JSON
    last_checked = CURRENT_TIMESTAMP,
    change_status = ?,
    change_detected = ?,
    updated_at = CURRENT_TIMESTAMP
WHERE article_id = ?;
```

#### Шаг CT3.3: Логирование изменений
```python
if new_urls:
    self.logger.info(f"Found {len(new_urls)} new URLs from {source_url}")
    for url_data in new_urls[:3]:  # Показать первые 3
        self.logger.info(f"  - {url_data['article_title']} → {url_data['article_url']}")
```

**Результат CT Phase 3**: Обновленная база данных с новыми URL

---

## 📊 Статистика и метрики

### Основная система (Single Pipeline)
```
Входной поток: RSS feeds (30 источников)
├── Phase 1: 15-20 новых статей/день
├── Phase 2: 95% успех парсинга (валидация 300+ слов)
├── Phase 3: 80% статей имеют изображения
└── Phase 4: 100% публикация в WordPress

Время обработки:
├── Phase 1: ~30 сек (все RSS)
├── Phase 2: ~45 сек (1 статья)  
├── Phase 3: ~15 сек (медиа)
└── Phase 4: ~60 сек (перевод + публикация)
```

### Change Tracking система
```
Входной поток: Web scraping (47 источников)
├── CT Phase 1: ~3 сек/источник сканирование
├── CT Phase 2: 985+ URL извлечено (100% успех)  
└── CT Phase 3: Изолированное хранение

Метрики качества:
├── URL extraction rate: 100% источников работают
├── False positives: <5% (навигационные ссылки)
└── Processing time: ~15 мин для всех 47 источников
```

## 🔗 Интеграция между системами

### Экспорт из Change Tracking в основную систему
```sql  
-- Потенциальный экспорт (в разработке)
INSERT INTO articles (
    article_id, source_id, url, title,
    content_status, discovered_via, created_at
)
SELECT 
    generate_uuid() as article_id,
    source_id,
    extracted_url as url,
    extracted_title as title,
    'pending' as content_status,
    'change_tracking' as discovered_via,
    CURRENT_TIMESTAMP
FROM tracked_articles_extracted_urls
WHERE exported_to_main = 0;
```

### Дедупликация между системами
```sql
-- Проверка дубликатов перед экспортом
SELECT COUNT(*) FROM articles 
WHERE url IN (
    SELECT extracted_url FROM tracked_articles_urls 
    WHERE exported_to_main = 0
);
```

## ⚠️ Критические точки и фильтры

### 1. Валидация контента (Phase 2)
```python
# КРИТИЧЕСКИЙ ФИЛЬТР: Предотвращение paywall статей
if word_count < 300:
    # Статья помечается как failed
    # НЕ публикуется в WordPress
    return "failed"
```

### 2. URL фильтрация (CT Phase 2)  
```python
# КРИТИЧЕСКИЕ ФИЛЬТРЫ:
exclude_patterns = [
    r'/contact', r'/about',     # Служебные страницы
    r'\.jpg$', r'\.png$',       # Медиа файлы
    r'facebook\.com',           # Социальные сети
    r'/_next/',                 # Технические ресурсы
]
```

### 3. Title cleaning (CT Phase 2)
```python
# Исключение навигационных элементов
invalid_titles = [
    'read more', 'learn more', 'click here',
    'arrow right', 'close banner', 'menu'
]
```

### 4. Изображения validation (Phase 3)
```python
# Минимальные требования к изображениям
min_file_size = 10000  # 10KB
min_dimensions = "250x250"  # Было 300x300
```

---

**🔗 Дополнительная документация:**
- [Change Tracking System](change_tracking/) — Детальная документация CT модуля  
- [Architecture](architecture.md) — Общая архитектура системы
- [API Reference](API/API_REFERENCE.md) — Справочник API