# API & Commands - Change Tracking

**Модули**: `core/main.py`, `change_tracking/monitor.py`  
**Назначение**: Команды CLI и API для управления Change Tracking системой

## 📋 Обзор

Change Tracking предоставляет набор CLI команд через основной файл `main.py` для сканирования источников, просмотра статистики и экспорта данных. Все команды используют флаг `--change-tracking` для активации модуля.

## 🖥️ CLI Команды

### Базовая структура команды
```bash
cd "/Users/skynet/Desktop/AI DEV/ainews-clean"
python core/main.py --change-tracking [COMMAND] [OPTIONS]
```

### 1. Сканирование источников

#### Сканирование с лимитом
```bash
# Сканировать первые 5 источников
python core/main.py --change-tracking --scan --limit 5

# Сканировать с батч-размером 3
python core/main.py --change-tracking --scan --limit 10 --batch-size 3
```

#### Полное сканирование
```bash
# Сканировать все 47 источников (займет ~15 минут)
python core/main.py --change-tracking --scan

# Принудительное полное сканирование
python core/main.py --change-tracking --complete-scan
```

#### Сканирование только новых источников
```bash
# Сканировать только источники которые еще не проверялись
python core/main.py --change-tracking --scan --only-unscanned
```

### 2. Статистика и мониторинг

#### Общая статистика
```bash
# Статистика отслеживания
python core/main.py --change-tracking --tracking-stats
```

**Пример вывода:**
```
📊 СТАТИСТИКА ОТСЛЕЖИВАНИЯ ИЗМЕНЕНИЙ
============================================================
📋 Всего отслеживается: 52 страниц

📈 ПО СТАТУСАМ:
  🔄 CHANGED     :    7 страниц
  🆕 NEW         :    2 страниц
  ⚪ UNCHANGED   :   43 страниц

🌐 ТОП ИСТОЧНИКИ:
   1. perplexity                  2 страниц
   2. databricks_tracking         2 страниц
   3. together                    2 страниц

🔥 ПОСЛЕДНИЕ ИЗМЕНЕНИЯ:
  1. 🆕 https://www.perplexity.ai/hub
     ⏰ 2025-08-11T20:10:57+00:00
  2. 🔄 https://www.soundhound.com/voice-ai-blog/  
     ⏰ 2025-08-11T19:58:17+00:00
```

#### Показать новые URL
```bash
# Показать найденные новые URL
python core/main.py --change-tracking --show-new-urls

# Показать последние 20 URL
python core/main.py --change-tracking --show-new-urls --limit 20
```

### 3. Экспорт данных

#### Экспорт изменений (планируется)
```bash
# Экспорт изменений в основную систему
python core/main.py --change-tracking --export-changes

# Экспорт статей в articles таблицу
python core/main.py --change-tracking --export-articles
```

#### Извлечение URL
```bash
# Показать извлеченные URL без сохранения
python core/main.py --change-tracking --extract-urls --limit 3
```

### 4. Дополнительные команды

#### Информационные команды
```bash
# Список всех источников
python core/main.py --list-sources

# Общая статистика системы
python core/main.py --stats

# Показать справку
python core/main.py --help
```

## 🔧 Параметры команд

### Основные параметры

| Параметр | Тип | Описание | Пример |
|----------|-----|----------|---------|
| `--scan` | flag | Запустить сканирование | `--scan` |
| `--limit` | int | Лимит источников | `--limit 5` |
| `--batch-size` | int | Размер батча | `--batch-size 3` |
| `--complete-scan` | flag | Полное сканирование | `--complete-scan` |
| `--tracking-stats` | flag | Показать статистику | `--tracking-stats` |
| `--show-new-urls` | flag | Показать новые URL | `--show-new-urls` |
| `--extract-urls` | flag | Извлечь URL | `--extract-urls` |
| `--export-changes` | flag | Экспорт изменений | `--export-changes` |
| `--export-articles` | flag | Экспорт статей | `--export-articles` |

### Комбинирование параметров
```bash
# Сканирование с лимитом и статистикой
python core/main.py --change-tracking --scan --limit 3 --batch-size 1

# Сканирование и немедленный экспорт
python core/main.py --change-tracking --scan --export-articles

# Статистика с показом URL
python core/main.py --change-tracking --tracking-stats --show-new-urls --limit 10
```

## 🐍 Python API

### Основной класс ChangeMonitor
**Местоположение**: `change_tracking/monitor.py`

```python
from change_tracking.monitor import ChangeMonitor

# Инициализация
monitor = ChangeMonitor()

# Основные методы
result = await monitor.scan_webpage(url)
results = await monitor.scan_multiple_pages(urls) 
batch_result = await monitor.scan_sources_batch(batch_size=5, limit=10)
```

### Методы API

#### `scan_webpage(url, max_retries=3)`
**Назначение**: Сканировать одну веб-страницу
```python
result = await monitor.scan_webpage('https://www.anthropic.com/news')

# Возвращает:
{
    'url': 'https://www.anthropic.com/news',
    'status': 'success',
    'change_detected': False,
    'change_status': 'unchanged',
    'article_id': 'abc123',
    'extracted_urls': [...]
}
```

#### `scan_multiple_pages(urls)`
**Назначение**: Сканировать несколько страниц параллельно
```python
urls = ['https://openai.com/news/', 'https://anthropic.com/news']
results = await monitor.scan_multiple_pages(urls)

# Возвращает:
{
    'scanned': 2,
    'new': 1,
    'changed': 0,
    'unchanged': 1,
    'errors': 0,
    'results': [...]
}
```

#### `scan_sources_batch(batch_size, limit, only_unscanned=False)`
**Назначение**: Батч-сканирование источников
```python
result = await monitor.scan_sources_batch(
    batch_size=3, 
    limit=10,
    only_unscanned=True
)

# Возвращает статистику по всему батчу
```

### URLExtractor API
**Местоположение**: `change_tracking/url_extractor.py`

```python
from change_tracking.url_extractor import URLExtractor

extractor = URLExtractor()

# Извлечение URL из markdown
urls = extractor.extract_urls_from_content(
    markdown_content="[Link](https://example.com)",
    source_page_url="https://source.com/blog"
)

# Поиск новых URL  
new_urls = extractor.find_new_urls(
    current_urls=urls,
    existing_urls={'https://old.com'}
)

# Статистика
stats = extractor.get_stats(urls)
# {'total': 5, 'domains': 3, 'avg_title_length': 45}
```

### TrackingDatabase API
**Местоположение**: `change_tracking/database.py`

```python
from change_tracking.database import TrackingDatabase

db = TrackingDatabase()

# Сохранить результат
success = db.store_tracking_result(result_dict)

# Получить статистику
stats = db.get_sources_stats()
# {'anthropic': 1, 'openai': 2, ...}

# Последние изменения
changes = db.get_recent_changes(limit=10)

# Пометить как экспортированное
db.mark_as_exported('article_id_123')
```

## 📊 Структура ответов API

### Успешный ответ сканирования
```python
{
    'url': 'https://www.anthropic.com/news',
    'status': 'success',
    'change_detected': True,
    'change_status': 'changed',  # new/changed/unchanged
    'article_id': 'abc123def',
    'extracted_urls': [
        {
            'article_url': 'https://www.anthropic.com/news/article1',
            'article_title': 'Article Title',
            'source_domain': 'anthropic'
        }
    ],
    'scan_time': '2025-08-11T20:15:30+00:00',
    'processing_time_ms': 3250
}
```

### Ошибка сканирования
```python
{
    'url': 'https://broken.com',
    'status': 'error',
    'error': 'Connection timeout',
    'change_detected': False,
    'extracted_urls': 0,
    'scan_time': '2025-08-11T20:15:30+00:00'
}
```

### Батч результат
```python
{
    'batch_size': 5,
    'sources_scanned': 5,
    'total_time_seconds': 45.6,
    'results': {
        'new': 2,
        'changed': 1, 
        'unchanged': 2,
        'errors': 0
    },
    'extracted_urls_total': 89,
    'sources_with_changes': ['source1', 'source2']
}
```

## 🔍 Практические примеры

### Пример 1: Быстрая проверка 3 источников
```bash
cd "/Users/skynet/Desktop/AI DEV/ainews-clean"

# Сканировать 3 источника с батч-размером 1 (по одному)
python core/main.py --change-tracking --scan --limit 3 --batch-size 1

# Посмотреть результаты
python core/main.py --change-tracking --tracking-stats
```

### Пример 2: Мониторинг в production
```bash
# Полное сканирование всех источников (production режим)
python core/main.py --change-tracking --scan

# Экспорт найденных изменений
python core/main.py --change-tracking --export-changes

# Проверка статистики
python core/main.py --change-tracking --tracking-stats --show-new-urls
```

### Пример 3: Отладка конкретного источника
```python
# Python скрипт для отладки
import asyncio
from change_tracking.monitor import ChangeMonitor

async def debug_source():
    monitor = ChangeMonitor()
    result = await monitor.scan_webpage('https://www.anthropic.com/news')
    
    print(f"Status: {result['status']}")
    print(f"URLs extracted: {len(result['extracted_urls'])}")
    
    for url_data in result['extracted_urls'][:5]:
        print(f"- {url_data['article_title']} → {url_data['article_url']}")

# Запуск
asyncio.run(debug_source())
```

## ⚠️ Ограничения и рекомендации

### Производительность
- **Batch size**: Рекомендуется 3-5 для баланса скорости/стабильности
- **Timeout**: Каждый источник может занять до 10 секунд
- **Rate limiting**: Firecrawl API имеет лимиты запросов

### Мониторинг
```bash
# Рекомендуемая частота сканирования
# Быстрая проверка: каждые 2 часа
python core/main.py --change-tracking --scan --limit 5

# Полная проверка: раз в день  
python core/main.py --change-tracking --scan --complete-scan
```

### Логирование
- **Уровень**: INFO для статистики, DEBUG для детальной информации
- **Файлы**: Используется система app_logging
- **Модули**: `change_tracking.*` для фильтрации логов

### Обработка ошибок
```python
try:
    result = await monitor.scan_webpage(url)
    if result['status'] == 'error':
        print(f"Ошибка: {result['error']}")
except Exception as e:
    print(f"Исключение: {e}")
```

---

**🔗 См. также:**
- [Database Schema](database-schema.md) — Структура данных
- [URL Patterns](url-patterns.md) — Система фильтрации  
- [Processing Flow](../FLOW.md#api-workflow) — Процесс работы API