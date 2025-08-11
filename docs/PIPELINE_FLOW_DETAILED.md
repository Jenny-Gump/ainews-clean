# Pipeline Flow - Детальное описание

## Оглавление
1. [Общая архитектура](#общая-архитектура)
2. [Запуск и инициализация](#запуск-и-инициализация)
3. [Phase 1: RSS Discovery](#phase-1-rss-discovery)
4. [Phase 2: Content Parsing](#phase-2-content-parsing)
5. [Phase 3: Media Processing](#phase-3-media-processing)
6. [Phase 4: Translation & Preparation](#phase-4-translation--preparation)
7. [Phase 5: WordPress Publishing](#phase-5-wordpress-publishing)
8. [Защитные механизмы](#защитные-механизмы)
9. [Обработка ошибок](#обработка-ошибок)
10. [Мониторинг и логирование](#мониторинг-и-логирование)

---

## Общая архитектура

### Стек технологий
- **Python 3.11+** - основной язык
- **SQLite** - база данных (ainews.db + monitoring.db)
- **Firecrawl Scrape API** - парсинг контента (таймаут 5 минут)
- **DeepSeek Chat API** - очистка контента и перевод
- **OpenAI GPT-3.5** - генерация тегов
- **Playwright** - скачивание медиа файлов
- **WordPress REST API** - публикация
- **FastAPI + WebSocket** - мониторинг dashboard

### Принципы работы
- **FIFO очередь** - статьи обрабатываются в порядке добавления
- **Одна статья за раз** - никакой параллельной обработки
- **Fail-fast** - при ошибке переход к следующей статье
- **Non-blocking media** - ошибки медиа не блокируют публикацию

---

## Запуск и инициализация

### Способ 1: Dashboard UI
```
Dashboard (http://localhost:8001)
  ↓ Кнопка "Start Pipeline"
  ↓ POST /api/pipeline/start-single
  ↓ subprocess.Popen(["python3", "core/supervisor.py"])
  ↓ Supervisor запускает core/main.py --continuous-pipeline
```

### Способ 2: Командная строка
```bash
cd /Users/skynet/Desktop/AI DEV/ainews-clean
python3 core/supervisor.py  # Рекомендуется - с защитой
# или
python3 core/main.py --continuous-pipeline  # Без защиты
```

### Инициализация pipeline

1. **SessionManager создание сессии**
   ```python
   session_uuid = str(uuid.uuid4())
   INSERT INTO pipeline_sessions (session_uuid, status='active')
   ```

2. **Запуск независимого heartbeat процесса**
   ```python
   subprocess.Popen([sys.executable, "heartbeat_worker.py"])
   # Обновляет last_heartbeat каждые 10 секунд
   # Пишет в /tmp/ainews_heartbeat_*.txt
   ```

3. **Основной цикл**
   ```python
   while True:
       article = get_next_article()  # Получить из очереди
       if not article:
           break  # Нет статей - завершаем
       process_single_article(article)
   ```

---

## Phase 1: RSS Discovery

**Запуск**: Отдельно через кнопку "Start RSS" или `--rss-discover`

### Шаги:
1. **Загрузка источников**
   ```sql
   SELECT * FROM sources WHERE is_active = 1
   ```

2. **Для каждого источника** (30 штук):
   - Скачать RSS feed
   - Парсинг feedparser
   - Извлечение статей

3. **Сохранение в БД**:
   ```sql
   INSERT INTO articles (article_id, url, title, content_status='pending')
   -- Дедупликация по URL
   ```

4. **Статистика**:
   - Обычно находит 50-200 новых статей
   - Время выполнения: 1-3 минуты

---

## Phase 2: Content Parsing

**Таймаут фазы**: 10 минут (PARSING_TIMEOUT = 600)

### Шаг 2.1: Захват статьи
```python
article = session_manager.get_next_available_article()
# Ищет: content_status = 'pending' AND processing_session_id IS NULL
session_manager.claim_article(article_id)  # Атомарный UPDATE
```

### Шаг 2.2: Firecrawl Scrape API
```python
async with session.post(
    "https://api.firecrawl.dev/v1/scrape",
    json={
        "url": article_url,
        "formats": ["markdown"],
        "waitFor": 2000,  # Ждать 2 сек загрузки JS
        "timeout": 60000   # Общий таймаут 60 сек
    },
    timeout=aiohttp.ClientTimeout(total=300)  # 5 минут HTTP таймаут
)
```

**Особенности**:
- **0 ретраев** - если не получилось, статья failed
- **Таймаут 5 минут** на HTTP запрос
- **Возвращает** markdown контент + метаданные

### Шаг 2.3: DeepSeek очистка контента

**Попытки**: До 3 раз (автоматический retry внутри функции)

```python
for attempt in range(3):
    response = deepseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": load_prompt('content_cleaner')},
            {"role": "user", "content": f"URL: {url}\n\n{raw_markdown[:10000]}"}
        ],
        max_tokens=4000,
        temperature=0.1,
        timeout=60
    )
```

**Промпт** (`prompts/content_cleaner.txt`):
- Извлечь основной контент статьи
- Убрать навигацию, рекламу, футеры
- Сохранить реальные URL картинок
- Добавить [IMAGE_N] плейсхолдеры

### Шаг 2.4: Валидация контента

```python
word_count = len(content.split())
if word_count < 300:
    # Статья слишком короткая (возможно paywall)
    UPDATE articles SET content_status = 'failed'
    return {'success': False, 'error': 'Content too short'}
```

### Шаг 2.5: Сохранение медиа

```python
for idx, image in enumerate(images):
    INSERT INTO media_files (
        article_id, url, alt_text, 
        media_type='image', status='pending'
    )
```

### Результат Phase 2:
- **Успех**: `content_status = 'parsed'`, переход к Phase 3
- **Ошибка**: `content_status = 'failed'`, переход к следующей статье

---

## Phase 3: Media Processing

**Таймаут фазы**: 5 минут (MEDIA_TIMEOUT = 300)
**ВАЖНО**: Ошибки НЕ блокируют публикацию!

### Шаг 3.1: Получение списка медиа
```sql
SELECT * FROM media_files 
WHERE article_id = ? AND status = 'pending'
```

### Шаг 3.2: Playwright скачивание (для каждого файла)

```python
async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page()
    
    # Загрузка изображения
    response = await page.goto(image_url, wait_until='networkidle')
    
    # Скачивание
    content = await response.body()
    
    # Сохранение
    file_path = f"data/media/{article_id}/{filename}"
    Path(file_path).write_bytes(content)
```

### Шаг 3.3: Валидация изображения

```python
from PIL import Image
img = Image.open(file_path)
width, height = img.size

if width < 250 or height < 250:
    # Слишком маленькое изображение
    UPDATE media_files SET status = 'failed'
    continue
```

### Шаг 3.4: Обновление статуса

```python
UPDATE media_files SET 
    status = 'downloaded',
    local_path = ?,
    downloaded_at = CURRENT_TIMESTAMP
```

### Особенности:
- **Пауза 3 секунды** между загрузками
- **При любой ошибке**: `media_status = 'ready'` (не блокирует)
- **Очистка плейсхолдеров**: Убираются [IMAGE_N] для failed картинок

---

## Phase 4: Translation & Preparation

**Таймаут фазы**: 10 минут (TRANSLATION_TIMEOUT = 600)

### Шаг 4.1: Проверка дубликата
```python
if _is_already_processed(article_id):
    return {'success': True, 'already_processed': True}
```

### Шаг 4.2: DeepSeek перевод

```python
response = deepseek_client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": load_prompt('article_translator')},
        {"role": "user", "content": article_content}
    ],
    max_tokens=6000,
    temperature=0.3,
    timeout=120
)
```

**Промпт** (`prompts/article_translator.txt`):
- Перевести на русский язык
- Сохранить HTML форматирование
- Добавить экспертный комментарий в `<blockquote>`
- Выбрать категорию из списка

**Fallback на GPT-4o** при ошибке DeepSeek:
```python
except Exception as e:
    # Переключаемся на OpenAI
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        ...
    )
```

### Шаг 4.3: Пауза перед генерацией тегов
```python
await asyncio.sleep(5)  # Избегаем rate limit
```

### Шаг 4.4: Генерация тегов (GPT-3.5)

```python
response = openai_client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": load_prompt('tag_generator')},
        {"role": "user", "content": translated_content}
    ],
    max_tokens=500,
    temperature=0.2
)
```

**Промпт** (`prompts/tag_generator.txt`):
- Выбрать 2-5 тегов из списка 74 существующих
- Создать новые только для важных AI моделей/компаний
- Приоритет специфичным тегам

### Шаг 4.5: Сохранение в wordpress_articles

```sql
INSERT INTO wordpress_articles (
    article_id, title_ru, content_ru,
    excerpt_ru, categories, tags,
    yoast_title, yoast_description
)
```

---

## Phase 5: WordPress Publishing

**Таймаут**: Использует общий таймаут статьи

### Шаг 5.1: Проверка публикации
```python
if _is_wordpress_published(article_id):
    return {'success': True, 'already_published': True}
```

### Шаг 5.2: Загрузка медиа в WordPress

```python
for media_file in media_files:
    with open(media_file.local_path, 'rb') as f:
        response = requests.post(
            "https://ailynx.ru/wp-json/wp/v2/media",
            auth=('admin', APP_PASSWORD),
            files={'file': f},
            data={'alt_text': media_file.alt_text_ru}
        )
    media_file.wordpress_id = response.json()['id']
```

### Шаг 5.3: Создание поста

```python
post_data = {
    "title": title_ru,
    "content": content_ru_with_media,  # С заменой [IMAGE_N] на WP медиа
    "excerpt": excerpt_ru,
    "status": "publish",
    "categories": category_ids,
    "tags": tag_ids,
    "featured_media": featured_media_id,
    "meta": {
        "source_url": original_url,
        "_yoast_wpseo_title": yoast_title,
        "_yoast_wpseo_metadesc": yoast_description
    }
}

response = requests.post(
    "https://ailynx.ru/wp-json/wp/v2/posts",
    auth=('admin', APP_PASSWORD),
    json=post_data
)
```

### Шаг 5.4: Пауза после публикации
```python
await asyncio.sleep(5)  # Даем WordPress обработать
```

### Шаг 5.5: Обновление статуса
```sql
UPDATE articles SET 
    content_status = 'published',
    wordpress_id = ?,
    published_at = CURRENT_TIMESTAMP
```

---

## Защитные механизмы

### Уровень 1: Supervisor (внешний процесс)
- **Файл**: `core/supervisor.py`
- **Мониторит**: `/tmp/ainews_heartbeat.txt`
- **Убивает** если нет обновления 60 секунд
- **Максимум** 1 час работы (3600 секунд)
- **Адаптивные таймауты** для разных фаз

### Уровень 2: Pipeline таймауты
- **Общий**: 15 минут на одну статью
- **Парсинг**: 10 минут
- **Медиа**: 5 минут  
- **Перевод**: 10 минут
- **Механизм**: `asyncio.wait_for(task, timeout=TIMEOUT)`

### Уровень 3: Heartbeat процесс
- **Файл**: `core/heartbeat_worker.py`
- **Независимый** subprocess (не блокируется GIL)
- **Обновляет** каждые 10 секунд:
  - БД: `UPDATE pipeline_sessions SET last_heartbeat`
  - Файл: `/tmp/ainews_heartbeat_*.txt`

### Уровень 4: База данных таймауты
```python
conn = sqlite3.connect(db_path, timeout=5.0)
conn.execute("PRAGMA busy_timeout = 5000")
```

### Уровень 5: Watchdog сервис
- **Файл**: `core/watchdog.py` 
- **Проверяет** каждые 30 секунд
- **Освобождает** статьи застрявшие >5 минут
- **Очищает** сессии без heartbeat >10 минут

### Circuit Breaker
- **Файл**: `core/circuit_breaker.py`
- **Firecrawl**: 5 failures → 120s timeout
- **DeepSeek**: 3 failures → 60s timeout
- **OpenAI**: 3 failures → 90s timeout
- **WordPress**: 2 failures → 180s timeout

---

## Обработка ошибок

### Критические ошибки (прерывают обработку статьи)
1. **Firecrawl недоступен** → статья failed
2. **Контент <300 слов** → статья failed (paywall)
3. **DeepSeek и GPT-4o недоступны** → статья failed
4. **WordPress API ошибка** → статья failed

### Некритические ошибки (продолжают обработку)
1. **Медиа не скачалось** → публикуем без картинок
2. **Теги не сгенерировались** → публикуем без тегов
3. **Yoast мета не создалась** → публикуем без SEO

### Восстановление после сбоев
1. **Зависший процесс** → Supervisor убьет через 60 сек
2. **Заблокированная статья** → Watchdog освободит через 5 мин
3. **Зомби сессия** → Очистится через 10 мин
4. **Перегрузка API** → Circuit breaker подождет

---

## Мониторинг и логирование

### Dashboard (http://localhost:8001)
- **Pipeline Activity Monitor** - real-time операции
- **Кнопка Start/Stop Pipeline** - управление
- **Статистика** - обработано/ошибки/скорость

### Файлы логов
```
logs/
├── operations.jsonl     # Все операции pipeline
├── errors.jsonl         # Ошибки с контекстом
├── system.log          # Общий системный лог
└── monitoring/
    └── system.log      # Лог мониторинга
```

### База данных логов
```sql
-- ainews.db
pipeline_operations  -- Операции с таймингами
pipeline_sessions   -- Сессии с heartbeat

-- monitoring.db  
watchdog_actions    -- Действия watchdog
system_metrics      -- Метрики системы
```

### Пример записи в operations.jsonl
```json
{
  "timestamp": "2025-08-10T15:30:45",
  "phase": "content_parsing",
  "operation": "Парсинг контента: OpenAI Unveils GPT-5",
  "article_id": "abc123",
  "success": true,
  "duration_seconds": 12.3,
  "content_length": 3456,
  "word_count": 523
}
```

---

## Типичные проблемы и решения

### Проблема: Pipeline завис
**Решение**: Подождите 60 секунд - Supervisor автоматически перезапустит

### Проблема: Статья заблокирована
**Решение**: Подождите 5 минут - Watchdog освободит

### Проблема: Нет новых статей
**Решение**: Запустите RSS Discovery через кнопку "Start RSS"

### Проблема: Медиа не загружается
**Решение**: Не критично - статьи публикуются без картинок

### Проблема: API rate limit
**Решение**: Circuit breaker автоматически подождет

---

## Производительность

### Типичные показатели:
- **RSS Discovery**: 50-200 статей за 2-3 минуты
- **Обработка статьи**: 30-90 секунд
- **Скорость pipeline**: 40-120 статей/час
- **Успешность**: 85-95% (зависит от источников)

### Узкие места:
1. **Firecrawl API** - до 60 сек на сложные сайты
2. **DeepSeek перевод** - до 30 сек на большие статьи
3. **WordPress upload** - до 20 сек на статью с медиа
4. **Паузы между API** - 5 сек (защита от rate limit)

---

## Команды для отладки

```bash
# Проверка зависших процессов
ps aux | grep -E "(main.py|supervisor|heartbeat)"

# Проверка heartbeat файлов
ls -la /tmp/ainews_heartbeat*

# Просмотр последних операций
tail -f logs/operations.jsonl | jq '.'

# Проверка заблокированных статей
sqlite3 data/ainews.db "SELECT article_id, processing_session_id, 
  datetime(processing_started_at, 'localtime') 
  FROM articles WHERE processing_session_id IS NOT NULL"

# Принудительная очистка блокировок
sqlite3 data/ainews.db "UPDATE articles 
  SET processing_session_id = NULL 
  WHERE processing_session_id IS NOT NULL"

# Запуск Watchdog вручную
python3 core/watchdog.py

# Тест одной статьи
python3 core/main.py --single-pipeline
```

---

*Документ обновлен: 2025-08-10 | Версия: 1.0 | Fix #8 Integration*