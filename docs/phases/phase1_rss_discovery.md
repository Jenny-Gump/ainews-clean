# Phase 1: RSS Discovery

> 📚 **Навигация**: [← Все фазы](../README.md#-пятифазный-пайплайн-обработки) | [→ Phase 2](phase2_content_parsing.md)

## Обзор
Первая фаза пайплайна AI News Parser - обнаружение новых статей через RSS ленты и Google Alerts.

## Основные компоненты
- **ExtractRSSDiscovery** (`services/rss_discovery.py`) - основной класс для RSS дискавери
- **Источники** (`data/sources_extract.json`) - 26 источников (25 RSS + 1 Google Alerts)

## Процесс работы

### 1. Загрузка источников
```python
sources = ExtractRSSDiscovery().load_sources()
# Загружает из data/sources_extract.json
```

### 2. Парсинг RSS лент
- Использует `feedparser` для чтения RSS/Atom лент
- Поддерживает различные форматы дат
- Обрабатывает Google Alerts специально

### 3. Фильтрация статей
- По дате: только статьи за последние N дней (по умолчанию 7)
- По дубликатам: проверка по URL в базе данных
- По релевантности: базовая проверка на AI тематику

### 4. Сохранение в БД
```sql
INSERT INTO articles (
    article_id, source_id, url, title, description,
    published_at, content_status
) VALUES (?, ?, ?, ?, ?, ?, 'pending')
```

## База данных
- **Таблица**: `articles`
- **Статус**: `content_status = 'pending'` для новых статей
- **Уникальность**: по `url`

## Команда запуска
```bash
python core/main.py --rss-discover
```

## Метрики
- Количество найденных статей
- Количество новых статей
- Количество дубликатов
- Время выполнения

## Особенности
- Неагрессивный режим: последовательная обработка источников
- Обработка ошибок: пропуск недоступных источников
- Логирование: подробные логи через `app_logging`

## Интеграция с мониторингом
- Progress tracking через `ParsingProgressTracker`
- Обновление статуса в реальном времени
- WebSocket уведомления для дашборда