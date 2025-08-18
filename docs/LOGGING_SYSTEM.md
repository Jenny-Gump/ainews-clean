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
| **Change Tracking** | | | | |
| change_tracking/monitor.py | ✅ | ✅ (2 места) | ✅ | ✅ Образцовый |
| change_tracking/database.py | ✅ | ✅ (6 мест) | ✅ | ✅ Образцовый |
| change_tracking/url_extractor.py | ✅ | ❌ | ✅ | ⚠️ Достаточно |

### ❌ Неполное покрытие (требуют доработки)

| Модуль | logger.* | log_error | log_operation | Проблема |
|--------|----------|-----------|---------------|----------|
| **Core Pipeline** | | | | |
| core/single_pipeline.py | ✅ | ❌ | ✅ | ❌ 3 критических места |
| core/main.py | ✅ | ❌ | ❌ | ❌ Ошибки запуска |
| **Monitoring** | | | | |
| monitoring/memory_monitor.py | ✅ | ❌ | ❌ | ❌ save_memory_metrics |
| monitoring/collectors.py | ✅ | ❌ | ❌ | ⚠️ Некритично |
| **Services** | | | | |
| services/content_parser.py | ✅ | ❌ | ✅ | ⚠️ Желательно |
| services/media_processor.py | ✅ | ❌ | ✅ | ⚠️ Желательно |

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

---
**Последнее обновление**: 18.08.2025
**Версия**: 1.0