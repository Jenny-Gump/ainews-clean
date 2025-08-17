# Change Tracking System - Детальный Flow

**Версия:** 3.3 (17 августа 2025)  
**Статус:** Production Ready + Timeout Protection via Process Supervisor  
**Основа:** Анализ кода из change_tracking/monitor.py, database.py и process_supervisor.py  
**Обновления:** MVP решение зависаний через Process Supervisor, упрощены таймауты

---

## 📊 Архитектура - 2 таблицы

### `tracked_articles` - Отслеживаемые страницы источников
- **Назначение:** Хранит страницы-каталоги источников (например, mistral.ai/news)
- **UNIQUE:** url (одна страница = одна запись)
- **Ключевые поля:** `change_status`, `change_detected`, `exported_to_main`

### `tracked_urls` - Извлеченные URL статей  
- **Назначение:** Хранит URL отдельных статей найденных на страницах
- **UNIQUE:** `(source_page_url, article_url)` - один URL может быть с разных страниц
- **Ключевые поля:** `is_new`, `exported_to_articles`

---

## 🔄 ДЕТАЛЬНЫЙ FLOW - Пошаговый процесс

### ФАЗА 1: Сканирование источников (`--scan`)

#### Шаг 1.1: Firecrawl API вызов
- **Код:** `monitor.py:188-198`
- **API:** `client.scrape_url(url, formats=['markdown', 'changeTracking'])`
- **Результат:** `markdown_content` + `change_status` (`new`/`changed`/`unchanged`)

#### Шаг 1.2: Обработка статуса страницы
- **Код:** `monitor.py:209-284`
- **Логика:**
  - `new` или нет в БД → создает запись в `tracked_articles`
  - `changed` → обновляет `tracked_articles` с новым хешем
  - `unchanged` → помечает как без изменений

#### Шаг 1.3: **КРИТИЧНО!** Извлечение URL происходит ВСЕГДА
- **Код:** `monitor.py:287-309`
- **Для `changed`:** извлекает URL (строка 287-297)
- **Для `unchanged`:** **ТОЖЕ извлекает URL** (строка 298-309)
- **Причина:** *"могли добавиться новые статьи"* даже при unchanged

### ФАЗА 2: Извлечение и анализ URL

#### Шаг 2.1: Парсинг markdown контента
- **Код:** `monitor.py:550-555` → `url_extractor.extract_urls_from_content()`
- **Процесс:** Ищет все ссылки в markdown, фильтрует по паттернам
- **Результат:** Список `extracted_urls` со всей страницы

#### Шаг 2.2: Получение существующих URL
- **Код:** `monitor.py:562` → `db.get_existing_urls_for_source(source_page_url)`
- **SQL:** `SELECT article_url FROM tracked_urls WHERE source_page_url = ?`
- **Результат:** Set существующих URL для данного источника

#### Шаг 2.3: Поиск новых URL
- **Код:** `monitor.py:565` → `url_extractor.find_new_urls(extracted_urls, existing_urls)`
- **Логика:** `current_urls - existing_urls` (разность множеств)
- **Результат:** Только URL которых нет в `tracked_urls`

### ФАЗА 3: Сохранение новых URL

#### Шаг 3.1: Запись в tracked_urls
- **Код:** `database.py:287-291`
- **SQL:** 
  ```sql
  INSERT INTO tracked_urls (
      source_page_url, article_url, article_title, 
      source_domain, is_new, exported_to_articles
  ) VALUES (?, ?, ?, ?, 1, 0)
  ```
- **Флаги:** `is_new=1, exported_to_articles=0`

#### Шаг 3.2: Обработка дублей
- **Код:** `database.py:298-302`
- **Constraint:** `UNIQUE(source_page_url, article_url)`
- **При дубле:** `IntegrityError` → игнорируется, счетчик не увеличивается

### ФАЗА 4: Экспорт в articles (`--export-articles`) [ОПТИМИЗИРОВАНО v3.1]

#### Шаг 4.1: Выборка готовых к экспорту (Supabase)
- **Код:** `database.py:447-460`
- **Supabase Query:** 
  ```python
  response = self.supabase.client.table('tracked_urls')\
      .select('*')\
      .eq('is_new', True)\
      .eq('exported_to_articles', False)\
      .order('discovered_at', desc=True)\
      .limit(limit)\
      .execute()
  ```
- **Лимит:** Настраиваемый (по умолчанию 100)

#### Шаг 4.2: Батчевая обработка [NEW v3.1]
- **Код:** `database.py:485-495`
- **Оптимизации:**
  ```python
  BATCH_SIZE = 50  # Обрабатываем батчами
  for batch_start in range(0, total_urls, BATCH_SIZE):
      batch = new_urls[batch_start:batch_end]
      logger.info(f"Processing batch {batch_num}/{total_batches}")
  ```
- **Мониторинг:** Время каждой операции замеряется

#### Шаг 4.3: Проверка дубликатов с таймаутом [NEW v3.1]
- **Код:** `database.py:502-507`
- **Защита от зависаний:**
  ```python
  if self._with_timeout(self.supabase.article_exists, 10)(article_url):
      # URL уже существует, помечаем как экспортированный
  ```

#### Шаг 4.4: Создание source с on_conflict [FIXED v3.1]
- **Код:** `services/supabase_client.py:220-222`
- **Исправление duplicate key:**
  ```python
  response = self.client.table('sources').upsert(
      source_data,
      on_conflict='source_id'  # Правильный UPSERT
  ).execute()
  ```

#### Шаг 4.5: Вставка в articles с мониторингом
- **Код:** `database.py:524-545`
- **Supabase Insert:**
  ```python
  result = self._with_timeout(self.supabase.insert_article, 10)(article_data)
  if operation_duration > 5:
      logger.warning(f"Slow export: {operation_duration:.2f}s")
  ```

#### Шаг 4.6: Обновление флагов и полное логирование [IMPROVED v3.1]
- **Код:** `monitor.py:683-695`
- **Улучшения:**
  - Логируются ВСЕ URL с индексами: `[11/20]`
  - Замер времени каждой операции
  - Батчевые результаты: `Batch 1/3 completed: 45 URLs exported`

---

## 🔄 Диаграмма состояний флагов

```
[Новый URL найден]
       ↓
is_new=1, exported_to_articles=0
       ↓
[--export-articles]
       ↓
is_new=0, exported_to_articles=1
       ↓
[URL обработан навсегда]
```

---

## 📈 Статистика текущего состояния

```sql
-- Проверка состояния флагов
SELECT is_new, exported_to_articles, COUNT(*) as count 
FROM tracked_urls 
GROUP BY is_new, exported_to_articles;
```

**Результат (после исправления 12.08.2025):**
- `is_new=0, exported_to_articles=0`: 107 URL (baseline)
- `is_new=0, exported_to_articles=1`: 925 URL (обработанные)
- `is_new=1, exported_to_articles=0`: 0 URL (готовые к экспорту)

---

## 🛡️ Process Supervisor - Защита от зависаний (v3.3)

### Новый компонент системы:
**Файл:** `core/process_supervisor.py`  
**Цель:** Изоляция источников и гарантия от зависаний

### Как работает:
1. **Каждый источник в отдельном процессе** - полная изоляция
2. **Жёсткий таймаут 60 секунд** - subprocess.run(timeout=60)
3. **SIGKILL при превышении** - принудительное завершение
4. **Статистика** - successful/skipped/killed/errors

### Использование:
```python
from core.process_supervisor import ProcessSupervisor

supervisor = ProcessSupervisor(timeout_per_source=60)

# Change Tracking с защитой от зависаний
result = supervisor.run_change_tracking_source('https://example.com')
# Гарантия: завершится за 60 секунд или будет убит
```

### Результаты:
- **До:** Зависания до бесконечности
- **После:** Максимум 60 секунд на источник
- **Статистика:** 0 killed в тестах = всё работает быстро

---

## ⚠️ Ключевые особенности и проблемы

### Особенности:
1. **URL извлекаются ВСЕГДА** - даже для unchanged страниц
2. **Сравнение с базой** - только новые URL помечаются is_new=1
3. **UNIQUE constraint** работает на уровне tracked_urls
4. **Лимит 100** URL за экспорт
5. **Process Supervisor** - защита от зависаний (NEW в v3.3)

### Решённые проблемы (v3.3):
1. ✅ **Зависания** - Process Supervisor с таймаутом 60 сек
2. ✅ **Retry усугубляет** - убраны retry (max_retries=1)
3. ✅ **Конфликт таймаутов** - упрощена иерархия таймаутов

### Оставшиеся проблемы:
1. **articles НЕ имеет UNIQUE на url** - возможны дубли RSS vs tracking
2. **Лимит 100** может потребовать несколько запусков для больших batches
3. **Межисточниковые дубли** не отслеживаются

---

## 📝 Примеры команд

```bash
# Сканирование источников
python core/main.py --change-tracking --scan --limit 5

# Экспорт готовых URL
python core/main.py --change-tracking --export-articles

# Статистика
python core/main.py --change-tracking --tracking-stats
```

---

**Документ создан:** 12 августа 2025  
**Основа:** Анализ кода change_tracking система v2.0