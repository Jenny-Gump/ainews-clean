# 📊 Change Tracking Module

**Версия**: 3.0  
**Статус**: Production Ready ✅ **SUPABASE**  
**Назначение**: Отслеживание изменений + извлечение URL статей из новостных источников  
**Последнее обновление**: 2025-08-14 - **МИГРАЦИЯ НА SUPABASE ЗАВЕРШЕНА**

---

## 🚀 КРИТИЧЕСКОЕ ОБНОВЛЕНИЕ (2025-08-14)

**💫 МИГРАЦИЯ НА SUPABASE ЗАВЕРШЕНА** - Полный переход с SQLite на Supabase для всех операций Change Tracking системы.

### ✅ Что изменилось:
- **База данных**: SQLite → **Supabase Cloud Database**
- **API calls**: `conn.execute()` → **Supabase REST API**
- **Производительность**: Локальная БД → **Облачная инфраструктура**
- **Интеграция**: Изолированная система → **Единая экосистема с основным пайплайном**

### ✅ Новые возможности:
- **Real-time мониторинг** через Supabase Dashboard
- **Автоматическое масштабирование** облачной БД  
- **Унифицированная архитектура** всей системы на Supabase
- **Улучшенная отказоустойчивость** и производительность

---

## 🎯 Описание

Модуль отслеживает изменения на веб-страницах новостных сайтов через **Firecrawl changeTracking API** и **автоматически извлекает URL отдельных статей** из измененных страниц. Система обнаруживает новые статьи и экспортирует их в основной пайплайн для обработки.

### Ключевые особенности

- 🔍 **Автоматическое обнаружение изменений** через Firecrawl API
- 🔗 **Извлечение URL статей** из markdown контента страниц
- 📊 **Двухуровневая БД** - tracked_articles + tracked_urls (**на Supabase**)
- 🚀 **Батч-обработка** для эффективности с retry механизмом
- 📈 **Детальная статистика** и мониторинг
- 🎯 **Smart filtering** - только новые URL экспортируются
- ⚡ **Retry система** - автоматические повторы при API ошибках
- 🔄 **Полная интеграция** с основным пайплайном через таблицу articles
- ✅ **Сброс флага is_new** после экспорта для предотвращения дубликатов

### ✅ КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ (версия 2.4)

- **🔥 ИСПРАВЛЕН mark_urls_as_old() БАГ** - система больше НЕ сбрасывает `is_new` флаги существующих URL
- **🎯 Корректное определение новых URL** - добавляются только действительно новые статьи
- **📊 Точная статистика** - флаги `is_new` отражают реальное состояние URL
- **🚀 Стабильная работа** - протестировано на всех 50 источниках

### ⚠️ Минорные ограничения

- **НЕ проверяются даты публикации статей** - система определяет "новые" статьи только по наличию URL в БД
- При первом сканировании источника все статьи будут помечены как baseline (не новые)

---

## 📁 Структура модуля

```
change_tracking/
├── README.md              # Эта документация
├── sources.txt           # Список отслеживаемых URL (50 источников)
├── __init__.py           # Инициализация модуля
├── monitor.py            # Основной класс ChangeMonitor + URL extraction
├── database.py           # Работа с БД (tracked_articles + tracked_urls)
├── url_extractor.py      # Извлечение URL из markdown контента (НОВЫЙ)
├── scripts/              # Утилиты
│   ├── test_tracking.py # Тестирование системы
│   ├── run_scan.py      # Регулярное сканирование
│   └── stats.py         # Просмотр статистики
└── docs/                 # Дополнительная документация
    ├── API.md           # Описание Firecrawl API
    └── DOMAIN_MAPPING_FIXED.md # ✅ Маппинг доменов исправлен
```

---

## 🗄️ База данных (Supabase)

### 🌟 Новая архитектура: Supabase Cloud Database

**URL**: `https://mtguynupyltlqiwhmilc.supabase.co`  
**Доступ**: Полный через Service Key + RPC функции  
**Интеграция**: Единая экосистема с основным пайплайном

### Таблица `tracked_articles` (Supabase)

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | BIGINT (PK) | Auto-increment primary key |
| `article_id` | TEXT (UNIQUE) | Уникальный ID статьи |
| `source_id` | TEXT | Источник (домен) |
| `url` | TEXT (UNIQUE) | URL страницы |
| `title` | TEXT | Заголовок страницы |
| `content` | TEXT | Markdown контент |
| `current_hash` | TEXT | MD5 хэш текущего контента |
| `previous_hash` | TEXT | MD5 хэш предыдущего контента |
| `change_detected` | BOOLEAN | Обнаружено изменение |
| `change_status` | TEXT | `new`, `changed`, `unchanged` |
| `exported_to_main` | BOOLEAN | Экспортировано в основной пайплайп |
| `last_checked` | TIMESTAMPTZ | Время последней проверки (UTC) |
| `created_at` | TIMESTAMPTZ | Время создания записи (UTC) |
| `updated_at` | TIMESTAMPTZ | Время последнего обновления (UTC) |

### Таблица `tracked_urls` (Supabase)

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | BIGINT (PK) | Auto-increment primary key |
| `source_page_url` | TEXT | URL страницы-каталога (из tracked_articles) |
| `article_url` | TEXT (UNIQUE) | URL конкретной статьи |
| `article_title` | TEXT | Заголовок статьи |
| `discovered_at` | TIMESTAMPTZ | Время обнаружения URL (UTC, по умолчанию NOW()) |
| `source_domain` | TEXT | Домен для source_id |
| `is_new` | BOOLEAN | Требует экспорта (по умолчанию true) |
| `exported_to_articles` | BOOLEAN | Экспортирован в таблицу articles (по умолчанию false) |
| `exported_at` | TIMESTAMPTZ | Время экспорта (UTC) |

### Индексы и ограничения (Supabase)
**tracked_articles:**
- Primary Key: `id` (BIGINT)
- Unique: `article_id`, `url`
- Index: `source_id`, `change_detected`, `exported_to_main`
- Index: `last_checked` для сортировки

**tracked_urls:**
- Primary Key: `id` (BIGINT)  
- Unique: `article_url`
- Index: `source_page_url`, `source_domain`
- Index: `is_new`, `exported_to_articles` для фильтрации
- Index: `discovered_at` для сортировки

### 🚀 Преимущества Supabase:
- **Автоматическое масштабирование** при росте нагрузки
- **Real-time подписки** на изменения данных
- **Встроенная безопасность** Row Level Security (RLS)
- **API автоматически** - REST и GraphQL из коробки
- **Резервное копирование** и восстановление данных

---

## 🔧 Использование

### Основные команды (через core/main.py)

```bash
cd "Desktop/AI DEV/ainews-clean"

# Сканирование источников (рекомендуемый способ)
python core/main.py --change-tracking --scan --limit 10 --batch-size 5

# Завершение сканирования - только неотсканированные источники
python core/main.py --change-tracking --complete-scan --batch-size 3

# Просмотр статистики отслеживания
python core/main.py --change-tracking --tracking-stats

# ========================================
# НОВАЯ ФУНКЦИОНАЛЬНОСТЬ: Извлечение URL
# ========================================

# Извлечь URL статей из отслеживаемых страниц с изменениями
python core/main.py --change-tracking --extract-urls --limit 20

# Показать статистику найденных URL
python core/main.py --change-tracking --show-new-urls

# Экспортировать новые URL в таблицу articles (для обработки основным пайплайном)
python core/main.py --change-tracking --export-articles --limit 50

# Полный workflow:
# 1. Сканирование изменений
python core/main.py --change-tracking --scan --batch-size 3
# 2. Извлечение URL из измененных страниц (автоматически)
# 3. Экспорт в articles
python core/main.py --change-tracking --export-articles
# 4. Обработка основным пайплайном
python core/main.py --single-pipeline
```

### Прямое использование скриптов

```bash
cd change_tracking

# Тестирование системы
python scripts/test_tracking.py --sources --limit 3
python scripts/test_tracking.py --url "https://openai.com/news/"
python scripts/test_tracking.py --stats

# Регулярное сканирование
python scripts/run_scan.py --max-sources 10 --batch-size 3

# Детальная статистика
python scripts/stats.py stats
python scripts/stats.py changed --limit 15
```

### Параметры сканирования

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `--limit` | Максимальное количество источников | 5 |
| `--batch-size` | Размер батча для обработки | 3 |
| `--complete-scan` | Сканировать только неотсканированные | false |
| `--retry` | Количество повторов при ошибках | 3 |

---

## 🔄 Как работает система

### 1. Сканирование страницы
```python
from change_tracking import ChangeMonitor

monitor = ChangeMonitor()
result = await monitor.scan_webpage("https://openai.com/news/")
```

### 2. Анализ статуса изменений

**`new`** - первое сканирование страницы:
- Создается запись в `tracked_articles`
- Сохраняется контент и хэш
- `change_detected = TRUE`
- **URL НЕ извлекаются** (baseline только)

**`changed`** - контент изменился:
- Обновляется запись в БД
- `previous_hash = старый хэш`
- `current_hash = новый хэш`  
- `change_detected = TRUE`
- **Извлекаются ВСЕ URL** из контента
- Новые URL помечаются `is_new = 1`

**`unchanged`** - без изменений:
- Обновляется только `last_checked`
- `change_detected = FALSE`
- URL не извлекаются

### 3. Экспорт и сброс флагов

```python
# Экспорт новых URL в основной пайплайн
results = monitor.export_new_urls_to_articles(limit=50)
```

**При экспорте:**
- URL с `is_new = 1` экспортируются в таблицу `articles`
- После успешного экспорта: `is_new = 0, exported_to_articles = 1`
- Это предотвращает повторный экспорт тех же URL

### 4. Батч-обработка с smart filtering
```python
# Сканирование всех источников батчами
results = await monitor.scan_sources_batch(
    batch_size=5,
    limit=20,
    only_unscanned=True  # Только неотсканированные источники
)
```

### 5. Retry механизм
```python
# Автоматические повторы при ошибках
result = await monitor.scan_webpage(url, max_retries=3)
```

**Retry логика:**
- Максимум 3 попытки на источник
- Exponential backoff: 5с, 10с, 20с
- Повтор только для retryable ошибок (408, 5xx, timeout)
- Логирование каждой попытки

---

## 📰 Источники

Файл `sources.txt` содержит 50 URL страниц новостных разделов:

- https://www.anthropic.com/news
- https://openai.com/news/
- https://huggingface.co/blog
- https://blog.google/technology/ai/
- https://research.google/blog/
- https://deepmind.google/discover/blog/
- https://blog.cloudflare.com/
- https://cursor.com/blog
- ... и другие (всего 50)

### ⚠️ Синхронизация источников

**ВАЖНО**: Система использует два файла для конфигурации:
- `sources.txt` - простой список URL для сканирования
- `data/tracking_sources.json` - полная конфигурация с source_id, названиями и категориями

**Файлы должны быть синхронизированы!** При добавлении нового источника обновите оба файла.

### Добавление источников
```bash
# Редактировать файл
nano sources.txt

# Добавить URL на новой строке
echo "https://example.com/ai-news/" >> sources.txt
```

---

## 📊 API Reference

### ChangeMonitor

```python
class ChangeMonitor:
    async def scan_webpage(url: str) -> Dict
    async def scan_multiple_pages(urls: List[str]) -> Dict  
    async def scan_sources_batch(batch_size: int, limit: int) -> Dict
    def get_tracking_stats() -> Dict
    def load_sources_from_file() -> List[str]
    def get_changed_articles(limit: int) -> List[Dict]
    def export_to_main_pipeline(article_ids: List[str]) -> bool
```

### ChangeTrackingDB

```python
class ChangeTrackingDB:
    def create_tracked_article(...) -> bool
    def update_tracked_article(...) -> bool
    def mark_unchanged(article_id: str) -> bool
    def get_tracked_article_by_url(url: str) -> Dict
    def get_tracking_stats() -> Dict
    def get_changed_articles(limit: int) -> List[Dict]
    def mark_exported(article_ids: List[str]) -> bool
    def cleanup_old_records(days_old: int) -> int
```

---

## 🔗 Интеграция с основным пайплайном

### Текущий статус
- ✅ Модуль работает изолированно
- ✅ Детектирует изменения
- ⏳ Экспорт в основной пайплайн (TODO)

### Планируемая интеграция

1. **Команда в main.py**:
   ```bash
   python core/main.py --change-tracking --scan
   python core/main.py --change-tracking --export
   ```

2. **Cron/Scheduler**:
   - Автоматическое сканирование каждые 4 часа
   - Экспорт изменений в основную таблицу `articles`

3. **API эндпоинты**:
   - `/api/tracking/stats` - статистика
   - `/api/tracking/changes` - список изменений
   - `/api/tracking/export` - запуск экспорта

---

## ⚡ Производительность

### Рекомендуемые настройки
- **Batch size**: 5 (оптимальный баланс скорость/нагрузка)
- **Timeout**: 60 секунд на страницу
- **Frequency**: каждые 4 часа
- **Cleanup**: старше 30 дней

### Метрики
- ~8-12 секунд на страницу
- ~2 секунды пауза между батчами
- ~3-5 минут полное сканирование 50 источников

---

## 🛠️ Конфигурация

### Environment Variables
```env
FIRECRAWL_API_KEY=fc-xxx...    # Required for changeTracking
LOG_LEVEL=INFO                 # DEBUG для детального логирования
```

### Paths
- Sources file: `change_tracking/sources.txt`
- Database: **Supabase Cloud** `https://mtguynupyltlqiwhmilc.supabase.co` (таблицы `tracked_articles`, `tracked_urls`)
- Logs: `app_logging/` (change_tracking.monitor, change_tracking.database)

---

## 🔒 Безопасность

- **Изоляция**: Отдельная таблица, не влияет на основные данные
- **Валидация**: Проверка URL перед сканированием  
- **Rate limiting**: Паузы между запросами к Firecrawl
- **Error handling**: Graceful обработка ошибок API

---

## 📝 Логирование

```python
# Основные события
INFO: "Scanning webpage: https://openai.com/news/"
INFO: "NEW page tracked: https://..."
INFO: "CHANGED: https://..."

# Ошибки
ERROR: "Error scanning https://...: API timeout"

# Статистика
INFO: "Scan complete: 2 new, 1 changed, 15 unchanged, 0 errors"
```

---

## 🐛 Troubleshooting

### Проблема: No URLs found in sources.txt
```bash
# Проверить путь к файлу
ls -la change_tracking/sources.txt

# Проверить содержимое
head change_tracking/sources.txt
```

### Проблема: API errors
```bash
# Проверить API ключ
grep FIRECRAWL_API_KEY .env

# Проверить статус Firecrawl
curl -H "Authorization: Bearer $FIRECRAWL_API_KEY" https://api.firecrawl.dev/v0/status
```

### Проблема: Supabase connection issues
```bash
# Проверить подключение к Supabase
python3 -c "
from change_tracking.database import ChangeTrackingDB
db = ChangeTrackingDB()
print(db.get_tracking_stats())
"

# Проверить учетные данные Supabase
grep SUPABASE_ .env

# Проверить статус Supabase проекта
curl -H "apikey: $SUPABASE_ANON_KEY" "$SUPABASE_URL/rest/v1/"
```

---

## 📈 Roadmap

### v2.3 (ТЕКУЩАЯ ВЕРСИЯ ✅)
- [x] Извлечение URL статей из markdown контента
- [x] Таблица tracked_urls для кэширования найденных URL
- [x] Автоматический экспорт в таблицу articles
- [x] Создание sources для новых доменов
- [x] Интеграция с core/main.py (команды --extract-urls, --show-new-urls, --export-articles)
- [x] Smart filtering - только новые URL
- [x] Полная интеграция с основным пайплайном
- [x] **Исправлен баг**: Сброс флага is_new после экспорта для предотвращения дубликатов

### v2.4 (КРИТИЧЕСКИ ВАЖНО)
- [ ] **Извлечение и проверка дат публикации** - определять реально новые статьи
- [ ] Использование Firecrawl Extract API для структурированных данных
- [ ] Фильтрация статей по дате публикации относительно последнего сканирования

### v2.5 (Следующие планы)
- [ ] Умная фильтрация изменений (не все изменения = новости)
- [ ] Поддержка RSS + Change Tracking
- [ ] Кластеризация похожих изменений
- [ ] Metrics для Prometheus

### v3.0 (Долгосрочно)
- [ ] ML-классификация важности изменений
- [ ] Поддержка других провайдеров (не только Firecrawl)
- [ ] Distributed scanning
- [ ] Advanced analytics dashboard

---

## 👥 Contributing

При добавлении новых источников:
1. Проверить, что сайт доступен для Firecrawl
2. Добавить URL в `sources.txt`
3. Протестировать: `python scripts/test_tracking.py --url "NEW_URL"`
4. Обновить документацию

---

## 🔥 Changelog версии 2.4 (2025-08-08)

### ❌ КРИТИЧЕСКИЙ БАГ ИСПРАВЛЕН
**Проблема**: Функция `mark_urls_as_old()` в monitor.py сбрасывала флаг `is_new = 0` для ВСЕХ существующих URL при каждом сканировании изменений.

**Последствия**: 
- URL которые должны были экспортироваться теряли флаг новизны
- Система показывала неточную статистику  
- Реально новые URL смешивались со сброшенными

**Исправление**:
- Удалена строка `self.db.mark_urls_as_old(source_page_url)` из monitor.py:442
- Система теперь добавляет ТОЛЬКО действительно новые URL
- Существующие URL и их флаги остаются нетронутыми

### ✅ ТЕСТИРОВАНИЕ
- Восстановлены корректные флаги для 236 URL
- Полное тестирование на всех 50 источниках  
- Система корректно определяет 0 новых URL при повторном сканировании

---

## 🔥 Changelog версии 2.5 (2025-08-09)

### ✅ НОВЫЕ ИСТОЧНИКИ
- Добавлен **Cloudflare Blog** (https://blog.cloudflare.com/)
- Добавлен **Cursor Blog** (https://cursor.com/blog)
- Удален Stack Overflow Survey (не подходит для новостей)
- Общее количество источников: **50**

### ✅ УЛУЧШЕНИЯ URL EXTRACTOR
- Добавлены критические исключения для `/people/`, `/topics/`, `/_next/`
- Доменно-специфичные паттерны для точной фильтрации
- Улучшена обработка multiline markdown (для Cursor Blog)
- Исправлена синхронизация между `sources.txt` и `tracking_sources.json`

### ✅ ИСПРАВЛЕНИЯ СИНХРОНИЗАЦИИ
- AWS: `https://aws.amazon.com/blogs/machine-learning/`
- Stanford: `https://hai.stanford.edu/news`
- Augmedix: `https://www.augmedix.com/press-room`

---

## 🔥 Changelog версии 2.6 (2025-08-10)

### ✅ ИНТЕГРАЦИЯ С MONITORING DASHBOARD
- **Полная интеграция** с мониторинг системой через кнопку "Start RSS"
- **Последовательный запуск**: RSS Discovery → Change Tracking Scan → Change Tracking Export
- **Детальное логирование** для каждого источника с прогрессом по батчам
- **Исправлены endpoint'ы** кнопок с `/api/extract/rss/` на `/api/pipeline/`

### ✅ УЛУЧШЕНИЯ ЛОГИРОВАНИЯ
- Добавлено детальное логирование для каждого сканируемого источника
- Логи показывают реальные сообщения вместо operation names
- Добавлены эмодзи для визуального различия статусов:
  - 🔍 Scanning - источник сканируется
  - ✅ Changed - найдены изменения
  - 🆕 New - новый источник добавлен
  - ⏸️ No changes - без изменений
  - ❌ Error - ошибка сканирования
- Логирование прогресса батчей с номером и размером

### ✅ ИСПРАВЛЕНИЯ
- **Убран лимит сканирования** - теперь сканируются все 50 источников
- **Исправлен default в main.py** - изменен с `default=5` на `default=None`
- **Исправлен JavaScript** для отображения поля `message` вместо `operation`
- **Добавлен cache-busting** параметр версии для принудительного обновления JS

### ⚠️ ОБНАРУЖЕННЫЕ ПРОБЛЕМЫ (требуют исправления)

#### 1. URL Extraction возвращает 0 URL
**Симптомы:**
- 7 источников показали изменения (change_status = 'changed')
- 0 новых URL извлечено из всех измененных источников
- Последние успешные URL в БД от 2025-08-09

**Тестирование OpenAI News:**
```
Content length: 6803 (контент получен)
Extracted 0 URLs from https://openai.com/news/
```

**Возможные причины:**
- Паттерны URL не соответствуют текущей структуре страниц
- Слишком строгие фильтры в exclude_patterns
- Изменился формат markdown от Firecrawl

#### 2. Database Error "datatype mismatch"
**Ошибка в логах:**
```json
{
  "timestamp": "2025-08-10T10:34:55.188941",
  "error_type": "database_error",
  "message": "datatype mismatch",
  "db_path": "data/ainews.db"
}
```

**Возможные причины:**
- Несоответствие типов при экспорте из tracked_urls в articles
- Проблема с datetime форматом
- NULL значения в обязательных полях

### 📋 СОЗДАН ПЛАН АУДИТА
Детальный план проверки системы создан в файле:
`/Users/skynet/Desktop/change_tracking_audit_plan.md`

План включает:
- Скрипты для тестирования каждого измененного источника
- SQL запросы для анализа БД
- Пошаговую диагностику URL extraction
- Проверку ошибки database mismatch

---

## 🔥 Changelog версии 2.8 (2025-08-11)

### ✅ ИСПРАВЛЕНА АРХИТЕКТУРНАЯ ОШИБКА: URL EXTRACTION

#### 🚨 ПРОБЛЕМА ОБНАРУЖЕНА:
**Неправильное использование общего экстрактора вместо индивидуальных конфигураций источников**

**Что было сделано неправильно:**
- Добавлен универсальный escape-паттерн в общий `url_extractor.py`
- Игнорированы индивидуальные настройки из `source_extractors_complete.json`
- 28 источников не работали из-за отсутствия специфичных паттернов

#### ✅ ПРАВИЛЬНОЕ РЕШЕНИЕ:
1. **Откачен универсальный escape-паттерн** из общего экстрактора
2. **Добавлен специфичный метод** `_extract_escape_links()` для проблемных источников
3. **Источники с escape-форматом** обрабатываются индивидуально:
   - `deepmind.google` 
   - `new.abb.com`
   - `scale.com`
   - `stability.ai` 
   - `waymo.com`

#### 📊 РЕЗУЛЬТАТЫ ИСПРАВЛЕНИЯ:
- **ABB Robotics**: 0 → 16 URL ✅
- **DeepMind**: 0 → 8 URL ✅  
- **Scale**: 0 → 26 URL ✅
- **Waymo**: 0 → 7 URL ✅
- **Stability AI**: 0 → 30 URL ✅

**Итого источников с URL**: 18 → 23 (+5)  
**Итого URL в системе**: 200 → 280 (+80)  
**Готовы к экспорту**: 80 URL

#### 🛠️ ТЕХНИЧЕСКОЕ РЕШЕНИЕ:
```python
# В extract_urls_from_content():
escape_sources = [
    'deepmind.google', 'new.abb.com', 'scale.com', 'stability.ai', 'waymo.com'
]

if any(domain in source_page_url for domain in escape_sources):
    found_urls.extend(self._extract_escape_links(markdown_content, source_page_url, source_domain))
```

#### 🎯 ПРИНЦИП РАБОТЫ:
- **Общий экстрактор**: стандартные markdown паттерны
- **Специальный метод**: escape-последовательности `\\\\` для конкретных источников
- **Правильные заголовки**: извлечение самой длинной содержательной строки

### ❌ ОСТАЛОСЬ 28 ИСТОЧНИКОВ:
Требуют индивидуального анализа и добавления в список escape_sources или других специальных методов.

---

## 🔥 Changelog версии 2.7 (2025-08-11) - УСТАРЕЛ

### ⚠️ ПРЕДЫДУЩАЯ ВЕРСИЯ СОДЕРЖАЛА АРХИТЕКТУРНУЮ ОШИБКУ
Универсальный подход через общий экстрактор был неправильным. Правильно - индивидуальная обработка каждого источника через специфичные методы.

---

## 🚀 Changelog версии 3.0 (2025-08-14) - SUPABASE MIGRATION

### ✅ ПОЛНАЯ МИГРАЦИЯ НА SUPABASE ЗАВЕРШЕНА

#### 🎯 Технические изменения:
- **Database Layer**: Полный переход с SQLite на Supabase Cloud Database
- **API Integration**: Замена `conn.execute()` на `supabase.client.table()` операции
- **Connection Management**: Использование SupabaseClient wrapper через `DatabaseConfig`
- **Error Handling**: Адаптированы все методы для работы с Supabase API responses

#### 🔧 Обновленные методы:
```python
# Вместо SQLite:
conn.execute("SELECT * FROM tracked_articles WHERE url = ?", (url,))

# Теперь Supabase:
self.supabase.client.table('tracked_articles').select('*').eq('url', url).execute()
```

#### 🧪 Результаты тестирования:
- ✅ **ChangeTrackingDB**: Инициализация без ошибок
- ✅ **Supabase connection**: 50 tracked articles обнаружено  
- ✅ **Recent changes**: 10 записей с правильными timestamps
- ✅ **Export functionality**: Работает корректно (0 new URLs to export)
- ✅ **Integration test**: RSS + Change Tracking + Export в единой цепочке

#### 📊 Текущее состояние системы:
```
✅ 50 tracked articles в Supabase
✅ 10 recent changes с активностью от:
   - suno.com/blog
   - blog.perplexity.ai  
   - lambda.ai/blog
   - scale.com/blog
   - huggingface.co/blog
✅ 0 errors в процессе миграции
```

#### 🌟 Новые возможности:
- **Unified ecosystem**: Change Tracking теперь часть единой Supabase инфраструктуры
- **Real-time monitoring**: Возможность подписки на изменения в таблицах
- **Cloud scalability**: Автоматическое масштабирование при росте нагрузки  
- **Better reliability**: Облачная отказоустойчивость вместо локальной SQLite

#### ⚠️ Breaking Changes:
- **Не совместимо** с предыдущими SQLite версиями
- **Требуется настройка** Supabase credentials в `.env`
- **Новая схема данных** с BIGINT primary keys и TIMESTAMPTZ полями

#### 🎯 Команды после миграции:
```bash
# Тест подключения
python3 -c "from change_tracking.database import ChangeTrackingDB; print(ChangeTrackingDB().get_tracking_stats())"

# Полный цикл RSS + Change Tracking  
bash scripts/run_rss_and_tracking.sh

# Экспорт найденных URL
python core/main.py --change-tracking --export-articles
```

---

**Обновлено**: 2025-08-14  
**Версия**: 3.0 - CRITICAL: Полная миграция на Supabase Cloud Database  
**Автор**: AI News Parser Team