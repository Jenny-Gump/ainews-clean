# WordPress Integration Documentation

## Поля WordPress для AI News Parser

### Основные поля поста

#### Обязательные поля
- **title** (string) - HTML заголовок поста
- **content** (string) - HTML контент поста  
- **status** (string) - Статус поста: "publish", "draft", "pending", "private"

#### Дополнительные поля
- **excerpt** (string) - Краткое описание поста
- **slug** (string) - URL-совместимый идентификатор (алфавитно-цифровой + дефисы)
- **categories** (array) - Массив ID категорий или строка через запятую "32, 30, 33"
- **tags** (array) - Массив ID тегов или строка через запятую "121, 95, 117"

### Yoast SEO Meta Fields

Yoast SEO добавляет собственные мета-поля для оптимизации:

#### Основные Yoast поля
- **_yoast_wpseo_title** - SEO заголовок (до 60 символов)
- **_yoast_wpseo_metadesc** - SEO описание (до 160 символов)  
- **_yoast_wpseo_focuskw** - Фокусное ключевое слово
- **_yoast_wpseo_canonical** - Canonical URL
- **_yoast_wpseo_opengraph-title** - Open Graph заголовок
- **_yoast_wpseo_opengraph-description** - Open Graph описание

### Категории для AI News Parser

Используем фиксированный список категорий:

```json
[
  "LLM",
  "Машинное обучение", 
  "Техника",
  "Digital",
  "Люди",
  "Финансы", 
  "Наука",
  "Обучение",
  "Другие индустрии"
]
```

### Теги - структура по группам

#### Группа 1: Нейросети и LLM
- GPT-4, GPT-3.5, Claude, LLaMA, PaLM, Gemini
- Transformer, BERT, T5, ChatGPT
- Stable Diffusion, DALL-E, Midjourney

#### Группа 2: Компании
- OpenAI, Google, Microsoft, Meta, Apple
- Anthropic, Cohere, Hugging Face, Stability AI
- NVIDIA, AMD, Intel

#### Группа 3: Люди  
- Sam Altman, Elon Musk, Demis Hassabis
- Yann LeCun, Geoffrey Hinton, Andrej Karpathy
- Jensen Huang, Satya Nadella

### WordPress REST API Endpoints

#### Создание поста
```
POST /wp-json/wp/v2/posts
```

#### Пример данных для создания поста
```json
{
  "title": "Заголовок статьи",
  "content": "<p>HTML контент статьи</p>",
  "excerpt": "Краткое описание",
  "slug": "url-statyi",
  "status": "publish",
  "categories": "32, 30, 33",
  "tags": "121, 95, 117",
  "meta": {
    "_yoast_wpseo_title": "SEO заголовок",
    "_yoast_wpseo_metadesc": "SEO описание",
    "_yoast_wpseo_focuskw": "ключевое слово"
  }
}
```

### Обработка изображений

**ВАЖНО**: В текущей реализации Phase 4 изображения НЕ используются. Весь контент обрабатывается как чистый текст без медиафайлов.

### Требования к контенту

#### SEO оптимизация
- **Заголовок**: 50-60 символов
- **Мета-описание**: 150-160 символов
- **Фокусное ключевое слово**: 1-3 слова
- **Alt-текст изображений**: описательный, до 125 символов

#### Структура контента
- Использовать заголовки H2, H3 для структуры
- Параграфы не более 150 слов
- Списки для перечислений
- Выделение важных моментов **жирным** или *курсивом*

### Примеры готовых постов

#### Минимальный пост
```json
{
  "title": "Новости ИИ: GPT-5 анонсирован",
  "content": "<p>OpenAI анонсировала GPT-5...</p>",  
  "status": "publish",
  "categories": ["LLM"],
  "tags": ["GPT-5", "OpenAI", "Sam Altman"]
}
```

#### Полный пост с SEO
```json
{
  "title": "DeepMind представила Gemini Ultra",
  "content": "<h2>Основные возможности</h2><p>Gemini Ultra превосходит GPT-4...</p>",
  "excerpt": "DeepMind анонсировала Gemini Ultra - новую мультимодальную модель ИИ",
  "slug": "deepmind-gemini-ultra-announcement", 
  "status": "publish",
  "categories": ["LLM", "Техника"],
  "tags": ["Gemini", "DeepMind", "Google", "Demis Hassabis"],
  "meta": {
    "_yoast_wpseo_title": "DeepMind Gemini Ultra: новая эра мультимодального ИИ",
    "_yoast_wpseo_metadesc": "DeepMind представила Gemini Ultra - мультимодальную модель ИИ, превосходящую GPT-4. Подробности и возможности новой системы.",
    "_yoast_wpseo_focuskw": "Gemini Ultra DeepMind"
  }
}
```

## Интеграция с AI News Parser

### Phase 4: WordPress Publishing Flow

1. **Загрузка статей** - получение completed статей из БД (без медиафайлов)
2. **LLM обработка** - перевод и адаптация через DeepSeek API
   - Таймаут: 3 минуты на статью
   - При ошибке: сохранение со статусом 'failed'
3. **Валидация** - проверка формата ответа и категорий
4. **Сохранение** - запись в таблицу wordpress_articles
   - Успех: translation_status = 'translated'
   - Ошибка: translation_status = 'failed' + translation_error
5. **Публикация** (будущая фаза) - отправка в WordPress через API

### Обработка ошибок

- **Таймаут API** (3 минуты) - статья помечается как failed
- **Невалидный JSON** - статья помечается как failed с ошибкой
- **Процесс продолжается** - ошибка одной статьи не останавливает обработку остальных

### Команды для управления

```bash
# Обработка статей для WordPress
python3 core/main.py --wordpress-prepare --limit 10

# Проверка результатов
python3 core/main.py --stats

# Рекомендуемые настройки
# - Используйте deepseek-reasoner для качественных переводов
# - Обрабатывайте небольшими батчами (5-10 статей)
# - Таймаут 3 минуты достаточен для большинства статей
```

### Структура таблицы wordpress_articles

```sql
CREATE TABLE wordpress_articles (
    id INTEGER PRIMARY KEY,
    article_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    content TEXT NOT NULL, 
    excerpt TEXT,
    slug TEXT NOT NULL,
    categories TEXT,  -- JSON массив
    tags TEXT,        -- JSON массив
    _yoast_wpseo_title TEXT,
    _yoast_wpseo_metadesc TEXT,
    focus_keyword TEXT,
    featured_image_index INTEGER DEFAULT 0,  -- Не используется
    images_data TEXT DEFAULT '{}',           -- Не используется
    translation_status TEXT DEFAULT 'pending', -- pending/translated/failed
    translation_error TEXT,                    -- Текст ошибки при failed
    translated_at DATETIME,
    published_to_wp BOOLEAN DEFAULT 0,
    wp_post_id INTEGER,
    source_language TEXT,
    target_language TEXT DEFAULT 'ru',
    llm_model TEXT,                           -- deepseek-reasoner или deepseek-chat
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```