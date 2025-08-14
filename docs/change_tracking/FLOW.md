# Change Tracking System - Детальный Flow

**Версия:** 2.0 (август 2025)  
**Статус:** Production Ready  
**Основа:** Анализ кода из change_tracking/monitor.py и database.py

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

### ФАЗА 4: Экспорт в articles (`--export-articles`)

#### Шаг 4.1: Выборка готовых к экспорту
- **Код:** `database.py:130-137`
- **SQL:** 
  ```sql
  SELECT * FROM tracked_urls 
  WHERE is_new = 1 AND exported_to_articles = 0
  ORDER BY discovered_at DESC
  LIMIT 100
  ```
- **Лимит:** 100 URL за раз

#### Шаг 4.2: Вставка в articles
- **Код:** `database.py:175-180`
- **SQL:**
  ```sql
  INSERT INTO articles (
      article_id, source_id, url, title,
      content_status, media_status, discovered_via
  ) VALUES (?, ?, ?, ?, 'pending', 'pending', 'change_tracking')
  ```

#### Шаг 4.3: Обновление флагов
- **Код:** `database.py:183-192`
- **SQL:**
  ```sql
  UPDATE tracked_urls 
  SET exported_to_articles = 1, 
      exported_at = ?,
      is_new = 0
  WHERE id = ?
  ```
- **Результат:** URL помечен как обработанный

#### Шаг 4.4: Обработка дублей в articles
- **Код:** `database.py:196-210`
- **При `IntegrityError`:** флаги все равно сбрасываются
- **Проблема:** articles НЕ имеет UNIQUE constraint на url

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

## ⚠️ Ключевые особенности и проблемы

### Особенности:
1. **URL извлекаются ВСЕГДА** - даже для unchanged страниц
2. **Сравнение с базой** - только новые URL помечаются is_new=1
3. **UNIQUE constraint** работает на уровне tracked_urls
4. **Лимит 100** URL за экспорт

### Проблемы:
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