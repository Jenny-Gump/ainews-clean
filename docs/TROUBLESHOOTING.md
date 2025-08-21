# Troubleshooting Guide - AI News Parser

## Распространённые проблемы и решения

### 🔴 Pipeline зависает / не обрабатывает статьи

**Симптомы:**
- Pipeline запущен, но статьи не обрабатываются
- Статус "in_progress" не меняется длительное время

**Решения:**
1. Проверить статус через мониторинг:
```bash
cd monitoring && ./start_monitoring.sh
# Открыть http://localhost:8001
```

2. Проверить наличие pending статей:
```bash
python core/main.py --stats
```

3. Перезапустить pipeline из дашборда (НЕ из терминала!)

### 🟡 Ошибки парсинга контента

**Симптомы:**
- Статьи застревают в статусе "failed"
- Ошибка "Content too short" или "Paywall detected"

**Решения:**
1. Проверить доступность URL:
```bash
curl -I <article_url>
```

2. Проверить лимиты Firecrawl API (6 минут таймаут)

3. Для тестирования использовать example.com:
```sql
-- Добавить тестовую статью в Supabase
INSERT INTO articles (article_id, source_id, url, title, content_status)
VALUES ('test_001', 'test_source', 'http://example.com/test', 'Test Article', 'pending');
```

### 🟢 Проблемы с медиафайлами

**Симптомы:**
- Изображения не загружаются
- WordPress не показывает картинки

**Решения:**
1. Проверить размеры изображений (минимум 250x250px)
2. Проверить статус медиа:
```bash
python core/main.py --stats
# Смотреть media_status в выводе
```

3. Медиа ошибки НЕ критичны - статьи публикуются без изображений

### 🔵 Ошибки API

**Симптомы:**
- 401 Unauthorized
- 429 Rate Limit
- Connection timeout

**Решения:**

#### DeepSeek API:
- Проверить ключ в .env: `DEEPSEEK_API_KEY`
- Fallback на GPT-4o автоматический

#### OpenAI API:
- Проверить ключ: `OPENAI_API_KEY`
- Используется для медиа и fallback

#### Firecrawl API:
- Проверить ключ: `FIRECRAWL_API_KEY`
- Лимит 500 запросов/месяц на бесплатном плане

#### WordPress:
- Проверить App Password: `WORDPRESS_APP_PASSWORD`
- URL должен быть с /wp-json/wp/v2

### 🟣 База данных Supabase

**Симптомы:**
- "Connection refused" 
- "UNIQUE constraint violated"

**Решения:**
1. Проверить подключение:
```python
from services.supabase_client import get_supabase_client
client = get_supabase_client()
# Должен вернуть объект без ошибок
```

2. При дублях URL - система автоматически обрабатывает через is_deleted флаг

3. Проверить переменные окружения:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`

### ⚫ Мониторинг не запускается

**Симптомы:**
- Dashboard не открывается на localhost:8001
- WebSocket disconnected

**Решения:**
1. Проверить порт:
```bash
lsof -i :8001
# Если занят, убить процесс или изменить порт
```

2. Перезапустить:
```bash
cd monitoring
./stop_monitoring.sh
./start_monitoring.sh
```

3. Проверить логи:
```bash
tail -f monitoring/logs/errors.jsonl
```

### 🟤 RSS Discovery не находит статьи

**Симптомы:**
- Phase 1 выполняется, но новых статей нет

**Решения:**
1. Проверить источники:
```bash
python core/main.py --list-sources
```

2. Проверить активность источников в БД:
```sql
SELECT source_id, name, last_checked, error_count 
FROM sources 
WHERE active = true 
ORDER BY error_count DESC;
```

3. Сбросить error_count для проблемного источника:
```sql
UPDATE sources SET error_count = 0 WHERE source_id = 'source_name';
```

### ⚪ Change Tracking модуль

**Симптомы:**
- Tracked URLs не экспортируются в основной pipeline
- Процесс зависает при сканировании источников

**Решения:**
1. Проверить статистику:
```bash
python core/main.py --change-tracking --tracking-stats
```

2. Экспортировать вручную:
```bash
python core/main.py --change-tracking --export-changes
```

3. Модуль изолирован - не влияет на основной pipeline

### 🔴 Change Tracking зависает на Supabase запросах

**Симптомы:**
- Процесс change_tracking зависает на определенном источнике
- В логах видно "Supabase query: get_existing_urls_for_source" без завершения
- Процесс не реагирует на SIGTERM

**Причина:**
ThreadPoolExecutor не может корректно прервать блокирующие HTTP запросы к Supabase

**Решения:**
1. Убить зависший процесс:
```bash
ps aux | grep "change_tracking"
kill -9 <PID>
```

2. Проверить проблемный источник в БД:
```sql
SELECT COUNT(*) FROM tracked_urls 
WHERE source_page_url = 'https://проблемный-источник.com/blog';
```

3. **Исправление реализовано (август 2025):**
- Удален ThreadPoolExecutor из `_execute_with_timeout`
- Добавлен retry механизм (3 попытки с задержками 1, 2, 4 секунды)
- Используется встроенный timeout в httpx клиенте Supabase

## Полезные команды

### Диагностика системы:
```bash
# Общая статистика
python core/main.py --stats

# Список источников
python core/main.py --list-sources

# Проверка БД через MCP
claude mcp supabase execute_sql --query "SELECT COUNT(*) FROM articles WHERE content_status = 'pending'"
```

### Тестирование:
```bash
# Добавить тестовую статью
python scripts/add_test_article.py

# Запустить один цикл pipeline
python core/main.py --single-pipeline
```

### Очистка:
```bash
# Удалить failed статьи старше 7 дней
DELETE FROM articles 
WHERE content_status = 'failed' 
AND created_at < NOW() - INTERVAL '7 days';
```

## Контакты поддержки

- GitHub Issues: https://github.com/anthropics/claude-code/issues
- Документация: `/docs/README.md`
- Конфигурация: `.env` файл