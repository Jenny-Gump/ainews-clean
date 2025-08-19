# Система логирования AI News Parser

## Обзор

В AI News Parser используется **двухуровневая система логирования**, разработанная для разных целей и аудиторий. Важно понимать различие между этими уровнями и правильно их использовать.

## Двухуровневая архитектура

### 1. Консольное логирование (logger.*)
- **Цель**: Реалтайм информация о ходе выполнения процессов
- **Аудитория**: Пользователь, администратор, мониторинг dashboard
- **Методы**: `logger.info()`, `logger.error()`, `logger.warning()`, `logger.debug()`
- **Вывод**: Консоль (stdout/stderr), мониторинг в реальном времени
- **Формат**: Человекочитаемые сообщения с эмодзи и форматированием
- **Примеры использования**:
  ```python
  logger.info("🚀 Начинаем обработку статьи")
  logger.error("❌ Ошибка парсинга контента")
  logger.warning("⚠️ RSS feed медленно отвечает")
  ```
- **Детальная документация**: [app_logging/README.md](../app_logging/README.md#basic-logging)

### 2. Централизованное логирование (log_*)
- **Цель**: Постоянное хранение событий для последующего анализа и отладки
- **Аудитория**: Системные аналитики, разработчики, автоматизированные системы
- **Методы**: `log_error()`, `log_operation()`
- **Вывод**: 
  - `logs/errors.jsonl` - все ошибки системы
  - `logs/operations.jsonl` - метрики и операции
- **Формат**: Структурированный JSON с полным контекстом
- **Примеры использования**:
  ```python
  log_error('api_timeout', 'Firecrawl timeout after 60s',
           article_id='abc123', url='https://...', 
           module='content_parser')
           
  log_operation('phase_complete', 
                phase='content_parsing',
                duration_seconds=3.5,
                success=True)
  ```
- **Детальная документация**: [app_logging/README.md](../app_logging/README.md#operation-logging)

## Правила использования

### ЗОЛОТОЕ ПРАВИЛО
**Для ВСЕХ критических ошибок используйте ОБА типа логирования:**

```python
# ПРАВИЛЬНО - используем оба типа
error_msg = f"Failed to parse content for article {article_id}"
logger.error(f"❌ {error_msg}")  # Для пользователя в консоли
log_error('content_parsing_failed', error_msg,  # Для анализа в JSONL
         article_id=article_id, 
         url=article_url,
         module='content_parser')

# НЕПРАВИЛЬНО - только консоль
logger.error(f"❌ Failed to parse content")  # Ошибка потеряется!
```

### Когда использовать каждый тип

| Событие | logger.* | log_error() | log_operation() |
|---------|----------|-------------|-----------------|
| Старт процесса | ✅ | ❌ | ✅ |
| Прогресс выполнения | ✅ | ❌ | ❌ |
| Некритическое предупреждение | ✅ | ❌ | ❌ |
| Критическая ошибка | ✅ | ✅ | ❌ |
| API вызов с затратами | ❌ | ❌ | ✅ |
| Завершение фазы | ✅ | ❌ | ✅ |
| Метрики производительности | ❌ | ❌ | ✅ |

## Текущее покрытие по модулям

### ✅ Полное покрытие (используют оба типа правильно)

| Модуль | logger.* | log_error | log_operation | Статус |
|--------|----------|-----------|---------------|---------|
| **RSS Discovery** | | | | |
| services/rss_discovery.py | ✅ | ✅ (5 мест) | ✅ | ✅ Образцовый |
| **Change Tracking** (ИСПРАВЛЕНО 18.08.2025) | | | | |
| change_tracking/monitor.py | ✅ | ✅ (8 мест) | ✅ | ✅ Образцовый |
| change_tracking/database.py | ✅ | ✅ (6 мест) | ✅ | ✅ Образцовый |
| change_tracking/url_extractor.py | ✅ | ✅ (2 места) | ✅ | ✅ Образцовый |

| **Core Pipeline** (ИСПРАВЛЕНО 18.08.2025) | | | | |
| core/single_pipeline.py | ✅ | ✅ (6 мест) | ✅ | ✅ Образцовый |
| core/main.py | ✅ | ✅ (4 места) | ✅ | ✅ Образцовый |
| **Services** (ИСПРАВЛЕНО 18.08.2025) | | | | |
| services/content_parser.py | ✅ | ✅ (4 места) | ✅ | ✅ Образцовый |
| services/media_processor.py | ✅ | ✅ (2 места) | ✅ | ✅ Образцовый |
| services/firecrawl_client.py | ✅ | ✅ (3 места) | ✅ | ✅ Образцовый |

### ⚠️ Частичное покрытие (некритичные модули)

| Модуль | logger.* | log_error | log_operation | Статус |
|--------|----------|-----------|---------------|---------|
| **Monitoring** | | | | |
| monitoring/memory_monitor.py | ✅ | ❌ | ❌ | ⚠️ save_memory_metrics |
| monitoring/collectors.py | ✅ | ❌ | ❌ | ⚠️ Некритично |

## Анализ логов

### Просмотр ошибок
```bash
# Последние 10 ошибок
tail -10 logs/errors.jsonl | jq '.'

# Ошибки по модулям
cat logs/errors.jsonl | jq 'select(.module=="content_parser")'

# Ошибки за последний час
cat logs/errors.jsonl | jq 'select(.timestamp > (now - 3600 | todate))'
```

### Анализ операций
```bash
# Статистика по API затратам
cat logs/operations.jsonl | jq 'select(.cost_usd) | .cost_usd' | awk '{sum+=$1} END {print sum}'

# Медленные операции (>10 секунд)
cat logs/operations.jsonl | jq 'select(.duration_seconds > 10)'
```

## Файловая структура

```
logs/
├── errors.jsonl         # Все ошибки системы (log_error)
├── operations.jsonl     # Операции и метрики (log_operation)
└── monitoring_background.log  # Логи мониторинга (отдельная система)
```

## Ротация и очистка

- **Автоматическая ротация**: При достижении 10MB файл переименовывается с timestamp
- **Хранение**: Последние 5 ротированных файлов
- **Очистка**: Файлы старше 7 дней удаляются автоматически

## Связанная документация

1. **[app_logging/README.md](../app_logging/README.md)** - Детали реализации и API
2. **[docs/change_tracking/error-handling.md](change_tracking/error-handling.md)** - Обработка ошибок в Change Tracking
3. **[monitoring/README.md](../monitoring/README.md)** - Система мониторинга

## FAQ

### Почему две системы логирования?
- **logger.*** - для человека (читаемость, реалтайм)
- **log_*** - для машины (структурированность, анализ)

### Что делать если ошибка не критическая?
Используйте только `logger.warning()` без `log_error()`

### Куда смотреть если система зависла?
1. Консольный вывод - текущее состояние
2. `logs/errors.jsonl` - последние ошибки
3. `logs/operations.jsonl` - последние операции

### Как добавить новый тип ошибки?
```python
# В месте возникновения ошибки
logger.error(f"❌ Новый тип ошибки: {details}")
log_error('new_error_type', f"Описание: {details}",
         module='module_name',
         additional_context=value)
```

## 🎯 Результаты улучшения (18.08.2025)

### Добавленные `log_error()` места:

#### core/single_pipeline.py (6 мест):
1. **Строка 290**: `content_parsing_critical_error` - критические ошибки парсинга контента
2. **Строка 461**: `wordpress_preparation_failed` - ошибки подготовки WordPress
3. **Строка 744**: `pipeline_critical_error` - критические ошибки пайплайна
4. **Строка 268**: `content_parsing_failed` - уже был (базовые ошибки парсинга)
5. **Строка 209**: `pipeline_critical_error` - уже был (критические ошибки обработки)
6. **Строка 576**: `wordpress_publishing_failed` - уже был (ошибки публикации)

#### core/main.py (4 места):
1. **Строка 354**: `article_lookup_failed` - ошибки поиска статьи по ID
2. **Строка 509**: `cleanup_articles_failed` - ошибки очистки старых статей
3. **Строка 989**: `system_critical_error` - критические ошибки системы
4. **Строка 305**: `pipeline_fatal_error` - уже был (критические ошибки пайплайна)

#### services/content_parser.py (4 места):
1. **Строка 140**: `content_save_failed` - ошибки сохранения контента в БД
2. **Строка 155**: `article_mark_failed_error` - ошибки пометки статьи как failed
3. **Строка 441**: `article_parsing_failed` - общие ошибки парсинга статьи
4. **Строка 493**: `pending_articles_fetch_failed` - ошибки получения pending статей

#### services/media_processor.py (2 места):
1. **Строка 413**: `pending_media_fetch_failed` - ошибки получения pending медиа
2. **Строка 518**: `media_download_critical_error` - критические ошибки скачивания

#### services/firecrawl_client.py (3 места):
1. **Строка 157**: `redirect_resolve_failed` - ошибки resolve redirect (некритично)
2. **Строка 220**: `job_status_check_failed` - ошибки проверки статуса job
3. **Строка 342**: `firecrawl_error` - уже был (общие ошибки API)

### Итого: +13 новых критических мест покрыто log_error()

**Теперь ВСЕ ошибки извлечения данных логируются в `errors.jsonl`!**

## 🎯 Улучшения Change Tracking (18.08.2025)

### Добавленные места логирования ошибок:

#### change_tracking/monitor.py (6 новых мест):
1. **Строка 608**: `source_no_urls_extracted` - источник вернул 0 URLs из extract_article_urls
2. **Строка 322**: `changed_source_no_urls` - изменившийся источник не дал новых URLs
3. **Строка 341**: `unchanged_source_no_urls` - неизменный источник всё еще 0 URLs
4. **Строка 173**: `tracking_scan_failed` - общий сбой сканирования (уже был)
5. **Строка 343**: `tracking_timeout` - таймаут сканирования (уже был)
6. **log_operation с success=False** - когда urls_found==0

#### change_tracking/url_extractor.py (2 новых места):
1. **Строка 488**: `url_pattern_mismatch` - паттерны не совпадают для домена
2. **Строка 340**: `url_extraction_zero_results` - итоговый результат 0 URLs

### Ключевые улучшения:
- ✅ **Двойное логирование** везде где 0 URLs (console + JSONL)
- ✅ **success=False** в operations.jsonl когда нет результатов
- ✅ **Умное логирование** паттернов - только раз за домен за сессию
- ✅ **Детальная информация** - source_id, domain, patterns в логах

---
**Последнее обновление**: 18.08.2025
**Версия**: 2.0 - Полное покрытие критических ошибок