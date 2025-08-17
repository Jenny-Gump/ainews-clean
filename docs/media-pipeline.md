# Media Pipeline - Полное руководство по работе с изображениями

**Последнее обновление:** 17 августа 2025 - Исправлены заголовки изображений

## Обзор

Система обработки медиа в AI News Parser работает на всех этапах пайплайна - от извлечения изображений из источников до публикации в WordPress с локальными URL. В августе 2025 были решены критические проблемы с использованием внешних URL вместо локальных и с отображением заголовков изображений.

## Архитектура Media Pipeline

```
RSS Article → Parse → Extract Media → Download → Process → Translate → Upload to WP → Update Content
```

## Этапы работы с изображениями

### Phase 1: RSS Discovery (Обнаружение)
**Файл:** `services/rss_fetcher.py`

На этом этапе изображения НЕ обрабатываются. Система только:
- Получает RSS feed
- Сохраняет URL статьи
- Устанавливает `media_status = 'pending'`

### Phase 2: Content Parsing (Парсинг контента)
**Файл:** `services/content_parser.py`

Использует Firecrawl Scrape API + DeepSeek AI для:
1. **Извлечение markdown** из веб-страницы
2. **Поиск изображений** в markdown:
   ```python
   # DeepSeek извлекает реальные URL изображений
   # Пример: ![Alt text](https://example.com/image.jpg)
   ```
3. **Добавление плейсхолдеров** `[IMAGE_N]` в логичных местах текста
4. **Сохранение URL в БД**:
   ```sql
   INSERT INTO media_files (article_id, url, alt_text, image_order)
   ```

**Промпт DeepSeek** (`prompts/content_cleaner.txt`):
- Извлекает РЕАЛЬНЫЕ URL изображений
- НЕ создает фейковые example.jpg
- Добавляет плейсхолдеры в подходящих местах

### Phase 3: Media Processing (Обработка медиа)
**Файл:** `services/media_processor.py`

#### 3.1 Загрузка изображений
```python
def download_media_files(article_id):
    # Получаем URL из БД
    media_files = get_media_for_download(article_id)
    
    for media in media_files:
        # Скачиваем файл
        response = requests.get(media['url'])
        
        # Сохраняем локально
        file_path = f"data/media/{article_id}/{filename}"
        save_file(file_path, response.content)
```

#### 3.2 Валидация изображений
- **Минимальный размер:** 250x250px
- **Форматы:** JPEG, PNG, WebP
- **Максимальный размер:** 10MB
- **Проверка через PIL (Pillow)**

#### 3.3 Обработка
- Конвертация WebP → JPEG
- Оптимизация размера
- Генерация уникальных имен файлов

**Статусы в БД:**
- `pending` → `downloading` → `processing` → `completed` или `failed`

### Phase 4: WordPress Translation (Перевод)
**Файл:** `services/wordpress_publisher.py`

#### 4.0 Промпт для метаданных изображений (ОБНОВЛЕН 17.08.2025)
**Файл:** `prompts/image_metadata.txt`

Промпт теперь генерирует 3 поля:
1. **title** - короткий заголовок изображения на русском (до 60 символов)
2. **alt_text_ru** - SEO-оптимизированный alt текст на русском (до 125 символов)
3. **slug** - человекочитаемый slug для файла (латиница)

#### 4.1 Генерация image_caption (НОВОЕ с 15.08.2025)
```python
# LLM генерирует единую подпись для всех изображений
# В промпте article_translator.txt указано:
"image_caption": "Подпись к изображению на русском языке в формате - Источник: www.доменноеимя источника"

# Пример результата:
{
    "title": "Заголовок на русском",
    "content": "Переведенный контент с [IMAGE_N] плейсхолдерами",
    "image_caption": "Источник: www.techcrunch.com",  # ← НОВОЕ ПОЛЕ
    // другие поля...
}
```

#### 4.2 Перевод метаданных (DeepSeek Chat) - ОБНОВЛЕНО 17.08.2025
```python
def _translate_media_metadata(metadata):
    # Переводим alt-text и генерируем title через DeepSeek
    prompt = load_prompt('image_metadata', 
        alt_text=metadata['alt_text'],
        article_title=metadata['article_title'])
    
    # DeepSeek Chat переводит (ОБНОВЛЕНО с 17.08.2025)
    response = self.deepseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    
    translated = {
        'title': "Короткий заголовок на русском",  # ← НОВОЕ с 17.08.2025
        'alt_text_ru': "Изображение показывает...",
        'slug': 'izobrazhenie-pokazyvaet'
    }
```

#### 4.3 Генерация контента
- Контент сохраняется С плейсхолдерами `[IMAGE_N]`
- Плейсхолдеры НЕ заменяются на этом этапе (после fix от 08.08.2025)
- Поле `image_caption` сохраняется в таблице `wordpress_articles`

### Phase 5: WordPress Publishing (Публикация)
**Файл:** `services/wordpress_publisher.py` + `core/single_pipeline.py`

#### 5.1 Создание поста (НОВЫЙ подход после fix)
```python
# 1. Подготовка данных БЕЗ замены плейсхолдеров
wp_post_data = _prepare_wordpress_post(article)
# content содержит [IMAGE_N]

# 2. Создание поста в WordPress
wp_post_id = _create_wordpress_post(wp_post_data)

# 3. Пометка как опубликован
_mark_as_published(article_id, wp_post_id)
```

#### 5.2 Загрузка медиа в WordPress
```python
def _process_media_for_article(article_id, wp_post_id):
    for media in media_files:
        # Загружаем файл в WordPress
        wp_media_id = _upload_single_media(
            file_path=media['file_path'],
            post_id=wp_post_id,
            metadata={'alt_text_ru': '...', 'slug': '...'}
        )
        
        # Получаем WordPress URL
        wp_source_url = _get_wordpress_media_url(wp_media_id)
        # Пример: https://ailynx.ru/wp-content/uploads/2025/08/image.jpg
        
        # Сохраняем в БД
        UPDATE media_files 
        SET wp_media_id = ?, wp_source_url = ?
        WHERE id = ?
```

#### 5.3 Обновление контента (КРИТИЧЕСКОЕ изменение)
```python
# НОВОЕ: После загрузки медиа обновляем контент
updated_content = _replace_image_placeholders(
    article['content'], 
    article_id
)

# Заменяем плейсхолдеры на WordPress URL
def _replace_image_placeholders(content, article_id):
    # Получаем изображения с wp_source_url и caption
    SELECT 
        COALESCE(wp_source_url, url) as display_url,
        alt_text_ru,
        caption  # ← Добавлено 15.08.2025
    FROM media_files WHERE article_id = ?
    
    # Заменяем [IMAGE_1] на HTML с figcaption (обновлено 15.08.2025)
    <figure class="wp-block-image size-large">
        <img src="{wp_source_url}" alt="{alt_text_ru}"/>
        <figcaption>{caption}</figcaption>
    </figure>

# Обновляем пост в WordPress
_update_post_content(wp_post_id, updated_content)
```

## База данных

**База данных:** Supabase PostgreSQL  
**URL:** `https://mtguynupyltlqiwhmilc.supabase.co`  
**Таблица:** `media_files` (386+ записей)

### Таблица `media_files` (Supabase)
```sql
CREATE TABLE media_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id TEXT,
    url TEXT NOT NULL,           -- Внешний URL источника
    local_path TEXT,             -- Локальный путь к файлу
    alt_text TEXT,               -- Оригинальный alt
    alt_text_ru TEXT,            -- Переведенный alt
    caption TEXT,                -- Подпись к изображению (единая для всех в статье)
    width INTEGER,               -- Ширина изображения
    height INTEGER,              -- Высота изображения
    file_size INTEGER,           -- Размер файла в байтах
    mime_type TEXT,              -- MIME тип (image/jpeg, image/png)
    image_order INTEGER,         -- Порядок в статье
    status TEXT DEFAULT 'pending', -- pending/completed/failed
    wp_media_id INTEGER,         -- ID в WordPress Media Library
    wp_source_url TEXT,          -- WordPress URL (КРИТИЧНО!)
    wp_upload_status TEXT DEFAULT 'pending', -- pending/uploaded/failed
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Таблица `wordpress_articles` (Supabase)
```sql
CREATE TABLE wordpress_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id TEXT NOT NULL UNIQUE,
    title TEXT,
    content TEXT,
    excerpt TEXT,
    slug TEXT,
    categories TEXT,
    tags TEXT,
    _yoast_wpseo_title TEXT,
    _yoast_wpseo_metadesc TEXT,
    focus_keyword TEXT,
    image_caption TEXT,          -- Единая подпись для всех изображений статьи (добавлено 15.08.2025)
    wp_post_id INTEGER,
    -- другие поля...
);
```

### Ключевая логика: COALESCE
```sql
SELECT COALESCE(wp_source_url, url) as display_url
```
- Если `wp_source_url` есть → используем локальный URL
- Если нет → fallback на внешний URL

## Критические исправления (август 2025)

### Проблема #1: Внешние URL вместо локальных
**Симптом**: Статьи публиковались с внешними URL изображений, хотя медиа успешно загружалось в WordPress.

**Причина**:
1. `_prepare_wordpress_post()` заменял плейсхолдеры ДО загрузки медиа
2. В момент замены `wp_source_url = NULL`
3. COALESCE возвращал внешний URL
4. Медиа загружалось ПОСЛЕ создания поста

**Решение**:
1. Создаем пост с плейсхолдерами `[IMAGE_N]`
2. Загружаем медиа → получаем `wp_source_url`
3. Заменяем плейсхолдеры на локальные URL
4. Обновляем контент через WordPress REST API

### Проблема #2: OpenAI API ключ блокировал медиа
**Симптом**: Медиа файлы не загружались в WordPress, система зависала на переводе метаданных.

**Причина**: 
- OpenAI API ключ был неправильным/просроченным
- `_translate_media_metadata()` падал с 401 ошибкой
- Без переведенных метаданных загрузка в WordPress не происходила

**Решение (11 августа 2025)**:
- Заменили OpenAI на DeepSeek Chat для перевода метаданных
- Система стала полностью независимой от OpenAI
- Медиа пайплайн работает стабильно

### Проблема #3: Отображение подписей к изображениям (15 августа 2025)
**Симптом**: Изображения публиковались без подписей с указанием источника.

**Причина**:
- Не было поля для хранения единой подписи к изображениям
- HTML разметка не включала `<figcaption>` теги

**Решение**:
1. Добавлено поле `image_caption` в таблицу `wordpress_articles`
2. LLM генерирует единую подпись в формате "Источник: www.example.com"
3. Обновлен метод `_process_media_for_article` для использования единой подписи
4. Обновлен метод `_replace_image_placeholders` для добавления `<figcaption>` в HTML

### Проблема #4: Хеши вместо заголовков изображений (17 августа 2025)
**Симптом**: Заголовки изображений в WordPress отображались как хеши (например "984c9902ab1a") вместо осмысленных названий на русском.

**Причина**:
1. Промпт `image_metadata.txt` не генерировал поле `title`
2. При загрузке в WordPress не передавался параметр `title`
3. WordPress использовал имя файла (хеш) как заголовок

**Решение**:
1. Обновлен промпт `image_metadata.txt` - добавлена генерация `title`
2. Метод `_translate_media_metadata` теперь возвращает `title`
3. Метод `_upload_media_to_wordpress` принимает и передает `title` в WordPress API
4. При загрузке изображений title устанавливается корректно

### Изменения в коде

#### wordpress_publisher.py
```python
# Убрали из _prepare_wordpress_post:
- content = self._replace_image_placeholders(article['content'], article.get('article_id'))
+ content = article['content']  # Оставляем плейсхолдеры

# Добавили новый метод:
def _update_post_content(self, wp_post_id: int, new_content: str) -> bool:
    response = requests.post(
        f"{self.config.wordpress_api_url}/posts/{wp_post_id}",
        json={'content': new_content},
        auth=auth
    )

# Изменили порядок в publish_to_wordpress:
1. Создать пост
2. Загрузить медиа
3. Заменить плейсхолдеры
4. Обновить контент

# Обновлен _replace_image_placeholders (15.08.2025):
if img_data['caption']:
    html = f'''<figure class="wp-block-image size-large">
<img src="{img_data['display_url']}" alt="{img_data['alt_text']}" class="{wp_class}"/>
<figcaption>{img_data['caption']}</figcaption>
</figure>'''
```

## Паузы и тайминги

- **После публикации поста:** 5 секунд перед загрузкой медиа
- **Между медиафайлами:** 3 секунды
- **Timeout для загрузки:** 30 секунд
- **Timeout для Firecrawl:** 6 минут

## Fallback стратегии

1. **Если медиа не скачалось:**
   - Статус = `failed`
   - Используется внешний URL

2. **Если не прошла валидация:**
   - Изображение < 250x250px → пропускается
   - Неподдерживаемый формат → пропускается

3. **Если WordPress upload failed:**
   - `wp_source_url` остается NULL
   - COALESCE использует внешний URL

4. **Если обновление контента failed:**
   - Пост остается с плейсхолдерами
   - Логируется warning

## Мониторинг

### Проверка через REST API
```bash
# Последняя статья
curl "https://ailynx.ru/wp-json/wp/v2/posts?per_page=1"

# Проверка изображений
curl "https://ailynx.ru/wp-json/wp/v2/posts/274" | \
  jq -r '.content.rendered' | \
  grep -o '<img[^>]*src="[^"]*"'
```

### Проверка в БД
```sql
-- Статистика медиа
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN wp_source_url IS NOT NULL THEN 1 ELSE 0 END) as local,
    SUM(CASE WHEN wp_source_url IS NULL THEN 1 ELSE 0 END) as external
FROM media_files;

-- Проблемные статьи
SELECT article_id, COUNT(*) as failed_count
FROM media_files 
WHERE status = 'failed'
GROUP BY article_id;
```

## Лучшие практики

1. **Всегда проверяйте wp_source_url** перед заменой плейсхолдеров
2. **Используйте COALESCE** для fallback на внешние URL
3. **Логируйте все этапы** обработки медиа
4. **Не блокируйте пайплайн** при ошибках медиа
5. **Сохраняйте оригинальные URL** как backup

## Troubleshooting

### Изображения не загружаются
1. Проверьте `status` в `media_files`
2. Проверьте логи: `grep "media" logs/monitoring/system.log`
3. Проверьте права на папку `data/media/`

### Используются внешние URL
1. Проверьте `wp_source_url` в БД
2. Убедитесь, что обновление контента прошло
3. Проверьте логи: `grep "update.*content" logs/`

### Плейсхолдеры в опубликованных статьях
1. Проверьте, что `_update_post_content()` вызывается
2. Проверьте response от WordPress API
3. Проверьте наличие изображений в БД

## Ссылки

- [Основная документация](../README.md)
- [Архитектура системы](architecture.md)
- [LLM модели и промпты](llm-models.md)
- [WordPress REST API](https://developer.wordpress.org/rest-api/reference/media/)