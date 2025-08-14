# CLAUDE.md - AI News Parser Single Pipeline + External Prompts System

## 🔴 ВАЖНО: Общаться только на русском языке!

## ⚠️ КРИТИЧЕСКИ ВАЖНО: Запуск Pipeline
- **Pipeline запускается ТОЛЬКО из дашборда** через кнопку "Start Pipeline"
- **НИКОГДА не запускать напрямую** через терминал - защитные системы не будут работать
- **Debug трассировка ВСЕГДА включена** - логи в `/tmp/ainews_trace.txt`
- **При зависании**: запустить `./debug_hang.sh` для диагностики причины

## 🚀 Project: AI News Parser Single Pipeline
- **Purpose**: Streamlined AI news collection with external prompts system for easy customization
- **Stack**: Python, Supabase, Firecrawl Scrape API, DeepSeek AI, OpenAI API, FastAPI monitoring
- **Location**: Desktop/AI DEV/ainews-clean/
- **Version**: 3.0 - Full Supabase Migration + Duplicate Protection
- **Status**: Production ready with cloud database
- **Last Update**: August 14, 2025 - Full Supabase migration, SQLite removed

## 📋 System Overview
Single pipeline implementation with external prompts:
- **1 run = 1 article** - Core principle
- **29 news sources** - RSS feeds + Google Alerts
- **Simple FIFO queue** - No priorities
- **5 phases** - RSS → Parse → Media → Translate → Publish
- **External prompts** - Easy editing without code changes
- **Fixed tags & images** - Real URLs and proper tag generation

## 🎯 Main Commands

```bash
cd "Desktop/AI DEV/ainews-clean"
source venv/bin/activate

# Phase 1: Find new articles
python core/main.py --rss-discover

# Phases 2-5: Process ONE article through all phases  
python core/main.py --single-pipeline

# Continuous mode: Process ALL pending articles
python core/main.py --continuous-pipeline

# Change Tracking Module
python core/main.py --change-tracking --scan --limit 5     # Scan 5 sources for changes
python core/main.py --change-tracking --stats              # Tracking statistics
python core/main.py --change-tracking --export             # Export changes to main pipeline

# Information
python core/main.py --stats
python core/main.py --list-sources
```

## 🏗️ Project Structure
```
ainews-clean/
├── core/
│   ├── main.py            # Entry point (simplified)
│   ├── single_pipeline.py # Main pipeline logic
│   ├── database.py        # DB operations
│   └── config.py          # Configuration
├── services/              # Phase services
│   ├── content_parser.py  # Firecrawl Scrape + DeepSeek AI
│   ├── wordpress_publisher.py # Translation + Publishing
│   ├── prompts_loader.py  # External prompts loader
│   └── ...
├── prompts/               # 🆕 EXTERNAL PROMPTS SYSTEM
│   ├── content_cleaner.txt    # DeepSeek content cleaning
│   ├── article_translator.txt # Article translation (HTML)
│   ├── tag_generator.txt      # Tag generation from 74 tags
│   └── image_metadata.txt     # Image metadata translation
├── change_tracking/       # Change tracking module
├── monitoring/            # Web dashboard
├── app_logging/          # Logging system
├── agents/               # Agent contexts
└── data/                 # Databases
```

## 🆕 External Prompts System

### Overview
All LLM prompts extracted to separate files in `prompts/` folder for easy editing without code changes.

### Prompt Files
1. **`content_cleaner.txt`** - DeepSeek AI content cleaning
   - Extracts clean article content from raw markdown
   - Preserves real image URLs (no fake examples)
   - Adds [IMAGE_N] placeholders in logical places

2. **`article_translator.txt`** - Article translation
   - Translates to Russian with HTML formatting  
   - Adds expert commentary in `<blockquote>`
   - Selects categories from allowed list

3. **`tag_generator.txt`** - Tag generation
   - Selects 2-5 relevant tags from 74 curated tags
   - Creates new tags for important AI models/companies only
   - Prioritizes specific terms over generic ones

4. **`image_metadata.txt`** - Image metadata translation
   - Translates image alt-text to Russian
   - Creates SEO-friendly slugs

### Usage
```python
from services.prompts_loader import load_prompt

# Load prompt with variables
prompt = load_prompt('content_cleaner', 
    url=article_url, 
    content=raw_content
)
```

## 📊 Database

### Main tables
- **articles** - Articles with status flow
- **media_files** - Media attachments with real URLs
- **wordpress_articles** - Translated content with tags
- **sources** - News sources
- **tracked_articles** - Change tracking (isolated module)

### Article status flow
```
pending → parsed → published
         ↓
       failed
```

## 🗄️ Supabase Integration (Основная БД)

### Connection Status  
- **URL**: `https://mtguynupyltlqiwhmilc.supabase.co`
- **Status**: ✅ PRODUCTION - основная база данных системы
- **Доступ**: Full access через MCP server + Python client
- **SQLite**: ❌ ПОЛНОСТЬЮ УДАЛЕН - миграция завершена

### Database Protection
- **UNIQUE Constraint**: ✅ `articles_url_unique` - защита от дублей на URL
- **Indexes**: ✅ `idx_articles_url` - быстрый поиск по URL
- **Duplicate Detection**: ✅ Методы проверяют `is_deleted` статус
- **Error Handling**: ✅ Graceful обработка constraint violations

### Available Components
- **Client Module**: `services/supabase_client.py` - основной клиент с защитой от дублей
- **Factory**: `core/database_factory.py` - автоматическое подключение к Supabase
- **Config**: `core/db_config.py` - конфигурация подключения
- **MCP Server**: ✅ Подключен через `claude mcp add supabase`

### Current Statistics
- **782 статьи** - все с уникальными URL
- **0 дублей** - система полностью защищена
- **Sources**: Очищены от дублирующихся feed_url

## 🧪 Testing

**IMPORTANT**: Always use `http://example.com/` for testing:

```sql
-- Add test article to Supabase
INSERT INTO articles (
    article_id, source_id, url, title, 
    content_status, media_status
) VALUES (
    'test_001', 'test_source', 
    'http://example.com/test-article',
    'Test Article', 'pending', 'pending'
);
```

## 🤝 Agent System

### Available Agents
1. **database-optimization-specialist** - DB operations
2. **monitoring-performance-specialist** - System monitoring
3. **frontend-dashboard-specialist** - Dashboard UI
4. **source-manager** - RSS sources
5. **news-crawler-specialist** - News collection

### Agent workflow
1. Read context: `agents/[name]-context.md`
2. Use Task tool with exact agent name
3. Update context after completion

## 🔧 WordPress Integration

- **Site**: https://ailynx.ru
- **Admin**: See .env file
- **Categories**: 19 (under "Новости")
- **Tags**: 74+ (AI models, companies, people) - auto-creates new ones
- **Images**: Real URLs with proper alt-text in Russian
- **SEO**: Yoast integration with no field restrictions

## 📈 Monitoring

```bash
cd monitoring && ./start_monitoring.sh
# Open http://localhost:8001
```

## 🚨 СИСТЕМА ВОССТАНОВЛЕНА (11 августа 2025)

**ВАЖНО**: Система восстановлена с бэкапа от 7 августа БЕЗ защитных механизмов:
- ❌ **НЕТ SessionManager, Supervisor, Watchdog, Debug Tracer**
- ❌ **НЕТ Heartbeat мониторинга процессов**
- ❌ **НЕТ защиты от зависаний SQLite**
- ✅ **Запуск ТОЛЬКО из дашборда** - кнопка "Start Pipeline"
- ✅ **Простая архитектура** как было 7 августа
- ✅ **БД очищена** от таблиц сессий

## 🔴 Critical Rules

1. **Pipeline запускается ТОЛЬКО из дашборда** - НИКОГДА не из терминала
2. **ONE article per run** - Never batch process
3. **FIFO queue only** - No priorities 
4. **Test with example.com** - Never real sites during development
5. **Edit prompts not code** - All prompts in `prompts/` folder

## 📝 Key Files (RESTORED)

- `core/main.py` - Restored entry point (без защитных систем)
- `core/single_pipeline.py` - Restored pipeline (без SessionManager)
- `services/content_parser.py` - Restored content parser
- `services/wordpress_publisher.py` - Restored publisher
- `monitoring/api/pipeline.py` - Упрощенный API (без session tables)

## 🛠️ Environment Variables

```env
FIRECRAWL_API_KEY=...
DEEPSEEK_API_KEY=...
OPENAI_API_KEY=...
WORDPRESS_API_URL=https://ailynx.ru/wp-json/wp/v2
WORDPRESS_USERNAME=...
WORDPRESS_APP_PASSWORD=...
SUPABASE_URL=https://mtguynupyltlqiwhmilc.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_KEY=...
SUPABASE_PROJECT_REF=mtguynupyltlqiwhmilc
```

## 🔍 Диагностика зависаний

### При зависании pipeline:
```bash
# 1. Запустить скрипт диагностики
./debug_hang.sh

# 2. Посмотреть последнюю операцию
cat /tmp/ainews_last_operation.txt

# 3. Анализ всех незавершенных операций
python3 core/debug_tracer.py analyze

# 4. Проверить heartbeat
ls -la /tmp/ainews_heartbeat_main.txt
```

### Файлы диагностики:
- `/tmp/ainews_trace.txt` - Полный trace всех операций
- `/tmp/ainews_last_operation.txt` - Последняя операция перед зависанием
- `/tmp/ainews_heartbeat_main.txt` - Heartbeat файл (обновляется каждые 10 сек)
- `/tmp/ainews_faulthandler.log` - Stack trace при зависании

## 🆕 Recent Updates (August 8, 2025)

### ✅ КРИТИЧЕСКИЙ БАГ ИСПРАВЛЕН - Медиа обработка
- ✅ **Проблема устранена**: Статьи больше НЕ застревают в статусе `parsed` 
- ✅ **Причина была**: Медиа failure блокировал WordPress phases
- ✅ **Исправление**: Медиа ошибки теперь НЕ критичны для пайплайна
- ✅ **Умная очистка**: `[IMAGE_N]` плейсхолдеры убираются для failed картинок
- ✅ **Надежность**: Статьи публикуются даже если все картинки failed

## 🆕 Previous Updates (August 7, 2025)

### ✅ Major Fixes Applied
1. **External Prompts System**
   - All LLM prompts moved to `prompts/` folder
   - Easy editing without code changes
   - Dynamic prompt loading with variables

2. **Fixed Tag Generation**
   - Corrected `log_operation()` error that blocked tag creation
   - Tags now properly generated and added to WordPress
   - Auto-creates missing tags (e.g., GPT-5)

3. **Fixed Image System**  
   - DeepSeek now extracts real image URLs from markdown
   - No more fake "example.jpg" placeholder URLs
   - Proper image alt-text translation to Russian

4. **Content Validation (НОВОЕ)**
   - ✅ Добавлена проверка минимум 300 слов для предотвращения публикации paywall-статей
   - ✅ Автоматическое помечение коротких статей как `failed`
   - ✅ Защита от публикации пустых/фантазийных статей

5. **Полная очистка legacy кода (НОВОЕ)**
   - ✅ Удалены backup файлы и папки (~17MB освобождено)
   - ✅ Исправлены сломанные импорты `log_processor` в мониторинге
   - ✅ Обновлены устаревшие TODO комментарии (6 файлов)
   - ✅ Удалены пустые таблицы `extract_api_*` из БД мониторинга
   - ✅ Очищены неиспользуемые поля Extract API из таблицы `articles`
   - ✅ Оптимизированы базы данных через VACUUM

6. **Architecture Improvements**
   - Firecrawl Scrape API instead of Extract (preserves links)
   - DeepSeek AI for intelligent content cleaning
   - Real-time tag generation with fallback to GPT-3.5

### 🧪 Testing Results
- ✅ Tags: `['OpenAI', 'GPT-5', 'DeepSeek', 'Moonshot AI']`
- ✅ Images: Real URLs from `cdn.i-scmp.com` and `img.i-scmp.com`  
- ✅ Alt-text: Proper Russian translation
- ✅ WordPress: Published as ID 227 with all metadata
- ✅ Content Validation: 929 слов > 300 минимум, статья прошла проверку
- ✅ System: 100% работоспособна после полной очистки legacy кода

## 📌 Migration Notes

### What was added
- External prompts system in `prompts/`
- `prompts_loader.py` module
- Fixed tag generation logic
- Improved image URL handling
- Better error handling for LLM operations

### What was fixed
- `log_operation()` parameter conflict
- DeepSeek prompt for real image URLs
- Tag generation pipeline
- Image placeholder system

## 🚨 Common Issues

### No pending articles
```bash
# Check status
python core/main.py --stats

# Add test article with example.com
# See Testing section above
```

### Tags not appearing
- ✅ **FIXED** - Was caused by `log_operation()` error
- Now tags properly generated and added to WordPress
- Check logs for "Generated tags: [...]" confirmation

### Broken images
- ✅ **FIXED** - DeepSeek now extracts real URLs
- Updated `content_cleaner.txt` prompt with strict instructions
- No more fake "example.jpg" URLs

### API errors
- Check .env file
- Verify API keys
- Ensure pauses are in place
- DeepSeek has fallback to GPT-4o for translation
- Tag generation has fallback to GPT-3.5

## 🌐 WordPress REST API Доступ

### Основные эндпоинты
```bash
# Получить статью
curl "https://ailynx.ru/wp-json/wp/v2/posts/230"

# Получить содержимое статьи
curl "https://ailynx.ru/wp-json/wp/v2/posts/230" | jq '.content.rendered'

# Получить все статьи
curl "https://ailynx.ru/wp-json/wp/v2/posts"

# С авторизацией для создания/редактирования
curl -u "admin:tE85 PFT4 Ghq9 nl26 nQlt gBnG" "https://ailynx.ru/wp-json/wp/v2/posts"
```

### Проверка статей через REST API
```bash
# Последние статьи
curl "https://ailynx.ru/wp-json/wp/v2/posts?per_page=5&orderby=date&order=desc"

# Конкретная статья с метаданными
curl "https://ailynx.ru/wp-json/wp/v2/posts/230?context=edit" 

# Получить теги и категории
curl "https://ailynx.ru/wp-json/wp/v2/tags"
curl "https://ailynx.ru/wp-json/wp/v2/categories"
```

## 🔍 Change Tracking System

**Назначение**: Отслеживание изменений на веб-страницах AI источников с извлечением URL статей

### Ключевые возможности
- 📊 **47 источников** с 100% работоспособностью
- 🔍 **985+ извлеченных URL** с автоматической фильтрацией
- 📈 **Изолированная БД** - таблица `tracked_articles` (не влияет на основную систему)
- 🚀 **Batch обработка** с поддержкой escape-sequences
- 📋 **Детальная статистика** по источникам и изменениям
- ⚡ **Специальные фильтры** - URL patterns и escape processing для каждого источника

### Команды модуля
```bash
# Сканирование источников
python core/main.py --change-tracking --scan --limit 5
python core/main.py --change-tracking --scan --batch-size 3

# Статистика и мониторинг  
python core/main.py --change-tracking --tracking-stats
python core/main.py --change-tracking --show-new-urls --limit 20

# Экспорт данных (планируется)
python core/main.py --change-tracking --export-changes
```

### Статусы изменений
- **🆕 new** - Новая страница (первое сканирование)
- **🔄 changed** - Обнаружены изменения в контенте с новыми URL
- **⚪ unchanged** - Без изменений

### Архитектура системы
- **URL Extraction**: Продвинутая система извлечения ссылок с поддержкой escape-sequences (`\\\\\\\\`)
- **Source Mapping**: Маппинг 47 источников из `data/tracking_sources.json`
- **Domain Patterns**: Индивидуальные паттерны фильтрации для каждого источника
- **Database Schema**: Изолированная таблица `tracked_articles` с полной трассировкой изменений

### Документация Change Tracking
- **[docs/tracking-system.md](docs/tracking-system.md)** - Центральная документация системы
- **[docs/FLOW.md](docs/FLOW.md)** - Детальный процесс работы (CT Phase 1-3)
- **[docs/change_tracking/](docs/change_tracking/)** - Детальная документация компонентов:
  - `url-patterns.md` - Система фильтрации URL
  - `source-mapping.md` - Конфигурация источников
  - `escape-processing.md` - Обработка escape-sequences
  - `database-schema.md` - Структура базы данных
  - `api-commands.md` - CLI команды и API

---

**Updated**: August 14, 2025 | **Version**: 3.0 | **Full Supabase Migration + Duplicate Protection**