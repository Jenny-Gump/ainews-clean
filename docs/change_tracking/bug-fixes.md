# Change Tracking Bug Fixes

**Дата создания:** 15 августа 2025  
**Последнее обновление:** 17 августа 2025 (v3.2)  
**Статус:** Активные исправления + Timeout fixes  
**Цель:** Документирование критических багов и их решений

---

## 🐛 Bug #1: store_tracked_urls() не передает source_page_url

### Описание проблемы
**Дата обнаружения:** 15 августа 2025  
**Серьезность:** КРИТИЧЕСКАЯ  
**Статус:** ✅ ИСПРАВЛЕНО

### Симптомы
- Change Tracking система находила 0 новых статей из 50 источников
- Логи показывали: `Found 0 new URLs out of X total` 
- В БД: `is_new=true` было 0 записей из 1054 URL
- KeyError при попытке сохранения новых URL

### Техническая причина
Функция `store_tracked_urls()` в `change_tracking/database.py:262` не добавляла `source_page_url` к данным URL перед передачей в `add_tracked_urls()`.

**Проблемный код:**
```python
def store_tracked_urls(self, source_page_url: str, urls_data: List[Dict[str, str]]) -> int:
    if not urls_data:
        return 0
    return self.add_tracked_urls(urls_data)  # ❌ Не передает source_page_url
```

**Ошибка в add_tracked_urls():**
```python
existing = self.supabase.client.table('tracked_urls')\
    .select('id')\
    .eq('source_page_url', url_data['source_page_url'])\  # ❌ KeyError!
    .eq('article_url', url_data['article_url'])\
    .limit(1)\
    .execute()
```

### Решение
**Файл:** `change_tracking/database.py`  
**Строки:** 244-269  
**Исправление:** Добавление обогащения данных URL полем `source_page_url`

**Исправленный код:**
```python
def store_tracked_urls(
    self, 
    source_page_url: str, 
    urls_data: List[Dict[str, str]]
) -> int:
    if not urls_data:
        return 0
    
    # ИСПРАВЛЕНИЕ БАГА: Добавляем source_page_url к каждому URL перед сохранением
    enriched_urls = []
    for url_data in urls_data:
        enriched_data = url_data.copy()
        enriched_data['source_page_url'] = source_page_url
        enriched_urls.append(enriched_data)
        
    return self.add_tracked_urls(enriched_urls)
```

### Результат исправления
- ✅ Новые URL корректно сохраняются с `is_new=true`
- ✅ Change Tracking находит новые статьи из источников
- ✅ Нет больше KeyError при сохранении URL
- ✅ Система показывает реальное количество найденных статей

### Тестирование
```bash
# Команда для тестирования
python core/main.py --change-tracking --scan --limit 1

# Проверка результата в БД
SELECT COUNT(*) FROM tracked_urls WHERE is_new = true;
```

### Бэкап
Файл сохранен в: `backups/change_tracking_fix_20250815_204651/database.py`

---

## 🔄 Планируемые исправления

### Потенциальные улучшения
1. **Валидация данных:** Добавить проверку наличия обязательных полей
2. **Логирование:** Улучшить логи для отладки сохранения URL
3. **Тесты:** Создать unit-тесты для функций базы данных
4. **Мониторинг:** Алерты при is_new=0 в течение длительного времени

---

## 📊 Статистика исправлений

| Дата | Bug ID | Серьезность | Статус | Время на исправление |
|------|--------|-------------|--------|-------------------|
| 15.08.2025 | #1 | КРИТИЧЕСКАЯ | ✅ Исправлено | 30 минут |
| 15.08.2025 | #2 | КРИТИЧЕСКАЯ | ✅ Исправлено | 45 минут |
| 15.08.2025 | #3 | КРИТИЧЕСКАЯ | ✅ Исправлено | 2 часа |
| 15.08.2025 | #4 | ВЫСОКАЯ | ✅ Исправлено | 1 час |
| 17.08.2025 | #5 | КРИТИЧЕСКАЯ | ✅ Исправлено | 15 минут |

---

## 🐛 Bug #2: Foreign Key Constraint Violation при создании tracked_articles

### Описание проблемы
**Дата обнаружения:** 15 августа 2025  
**Серьезность:** КРИТИЧЕСКАЯ  
**Статус:** ✅ ИСПРАВЛЕНО

### Симптомы
- Change Tracking зависал на 4+ минуты при сканировании источников
- Ошибка Supabase: `foreign key constraint "tracked_articles_source_id_fkey" violated`
- Конкретная ошибка: `Key (source_id)=(huggingface_co) is not present in table "sources"`
- Процесс не завершался, требовал принудительного завершения

### Техническая причина
**Системное несоответствие между компонентами:**
1. **tracking_sources.json** НЕ содержал URL для huggingface.co
2. **Fallback логика** в `monitor.py:80` генерировала `huggingface_co` из домена
3. **Supabase содержал** `source_id = "hugging_face"` но НЕТ `"huggingface_co"`
4. **Foreign Key constraint** блокировал INSERT и зависал процесс

**Проблемный код в monitor.py:**
```python
# Fallback генерировал неправильные source_id
domain = urlparse(url).netloc.replace('.', '_')  # huggingface.co → huggingface_co
```

### Решение
**Многокомпонентное исправление:**

#### 1. Добавлен источник в tracking_sources.json
```json
{
  "source_id": "hugging_face",
  "name": "Hugging Face Blog",
  "url": "https://huggingface.co/blog",
  "rss_url": "https://huggingface.co/blog/rss",
  "type": "web",
  "category": "ai_platforms"
}
```

#### 2. Исправлена fallback логика в monitor.py:79-95
```python
def _get_source_id(self, url: str) -> str:
    # ИСПРАВЛЕНИЕ FK BUG: Специальные маппинги для проблемных доменов
    domain_mappings = {
        'huggingface.co': 'hugging_face',
        'www.huggingface.co': 'hugging_face',
        'doosanrobotics.com': 'doosan_robotics',
        'www.doosanrobotics.com': 'doosan_robotics'
    }
    
    domain = urlparse(url).netloc.lower()
    if domain in domain_mappings:
        return domain_mappings[domain]
```

#### 3. Добавлена обработка FK ошибок в database.py:53-61
```python
except Exception as e:
    if 'foreign key constraint' in str(e).lower():
        self.logger.error(f"❌ Source '{article_data['source_id']}' not found in sources table - skipping article")
        return False  # Мягкий отказ вместо зависания
```

#### 4. Создан скрипт проверки scripts/check_source_mapping.py
Автоматическая проверка соответствия источников между tracking_sources.json и Supabase.

### Результат исправления
- ✅ Процесс не зависает на FK violations
- ✅ Добавлен source hugging_face в tracking_sources.json (47 источников)
- ✅ Правильный маппинг для проблемных доменов
- ✅ Обработка FK ошибок вместо зависания
- ✅ Система работает стабильно: 24 новых URL в БД

### Тестирование
```bash
# Тест исправления
python core/main.py --change-tracking --scan --limit 1
# Результат: ✅ 0 ошибок, процесс завершился успешно
```

---

## 🐛 Bug #3: Зависание процесса при экспорте URL

### Описание проблемы
**Дата обнаружения:** 15 августа 2025  
**Серьезность:** КРИТИЧЕСКАЯ  
**Статус:** ✅ ИСПРАВЛЕНО

### Симптомы
- Процесс зависал на экспорте URL в 19:45:14 на aws.amazon.com
- Логировались только первые 10 URL, но обрабатывались все
- Зависание происходило на 11+ URL который не логировался
- Процесс требовал принудительного завершения (kill -9)

### Техническая причина
1. **Неполное логирование:** В `monitor.py:683` логировались только первые 10 URL
2. **Отсутствие таймаутов:** Supabase операции могли зависать навсегда
3. **Последовательная обработка:** Большое количество URL обрабатывалось по одному

### Решение
**Файлы:** 
- `change_tracking/database.py` - добавлены таймауты и батчевая обработка
- `change_tracking/monitor.py:683-695` - полное логирование всех URL

**Исправления:**
1. **Таймауты операций:**
```python
def _with_timeout(self, func, timeout_seconds=30):
    # Защита от зависаний через signal.SIGALRM
```

2. **Батчевая обработка:**
```python
BATCH_SIZE = 50  # Обрабатываем батчами
for batch_start in range(0, total_urls, BATCH_SIZE):
    # Обработка батча с логированием прогресса
```

3. **Полное логирование:**
```python
for idx, url_data in enumerate(new_urls, 1):
    logger.info(f'📤 Exporting [{idx}/{len(new_urls)}]: {domain}')
```

### Результат
- ✅ Процесс не зависает благодаря таймаутам
- ✅ Все URL логируются с индексами [11/20]
- ✅ Батчевая обработка ускоряет экспорт
- ✅ Мониторинг медленных операций >5 сек

---

## 🐛 Bug #4: Duplicate Key Errors в Supabase

### Описание проблемы
**Дата обнаружения:** 15 августа 2025  
**Серьезность:** ВЫСОКАЯ  
**Статус:** ✅ ИСПРАВЛЕНО

### Симптомы
- Ошибка: `duplicate key value violates unique constraint "sources_source_id_key"`
- Происходила при попытке создать существующий source
- Вызывала задержки и ошибки в логах

### Техническая причина
Метод `upsert_source()` в `services/supabase_client.py:220` не указывал `on_conflict` параметр, что приводило к INSERT вместо UPDATE ON CONFLICT.

### Решение
**Файл:** `services/supabase_client.py:220-222`

**Исправленный код:**
```python
response = self.client.table('sources').upsert(
    source_data,
    on_conflict='source_id'  # Указываем конфликтную колонку
).execute()
```

### Результат
- ✅ Корректная обработка существующих источников
- ✅ Нет duplicate key errors
- ✅ Правильный UPSERT вместо INSERT

### Тестирование
```bash
# Тест экспорта с новыми исправлениями
python3 -c "
from change_tracking.monitor import ChangeMonitor
monitor = ChangeMonitor()
new_urls = monitor.db.get_new_urls(limit=5)
exported = monitor.db.export_urls_to_articles(new_urls[:5])
print(f'Successfully exported {exported} URLs')
"
# Результат: ✅ Successfully exported 2 URLs (без ошибок)
```

### Бэкап
Файлы сохранены в: `backups/foreign_key_fix_20250815_211541/`

---

## 🐛 Bug #5: Конфликт таймаутов приводит к зависанию системы

### Описание проблемы
**Дата обнаружения:** 17 августа 2025  
**Серьезность:** КРИТИЧЕСКАЯ  
**Статус:** ✅ ИСПРАВЛЕНО

### Симптомы
- Система change tracking зависала на случайных источниках
- После таймаута не переходила к следующему источнику
- Требовалось принудительное завершение процесса
- Зависания происходили случайным образом на разных источниках

### Техническая причина
**Конфликт таймаутов между asyncio и aiohttp:**
1. **asyncio.wait_for** в `monitor.py:202-208` установлен на 45 секунд
2. **aiohttp.ClientTimeout** в `firecrawl_client.py:89-92` установлен на 60 секунд
3. Когда aiohttp ждёт 60 секунд, asyncio не может прервать операцию после 45 секунд
4. Результат: система зависает, ожидая завершения aiohttp таймаута

**Проблемный код в firecrawl_client.py:**
```python
timeout=aiohttp.ClientTimeout(
    total=60,           # 60 секунд общий таймаут > 45 сек asyncio
    sock_connect=10,    # 10 секунд на подключение
    sock_read=30        # 30 секунд на чтение данных
)
```

### Решение
**Файлы:** 
- `services/firecrawl_client.py:89-92` - исправление таймаутов
- `change_tracking/monitor.py:330-342` - принудительное закрытие сессии

**Исправления:**

#### 1. Синхронизация таймаутов в firecrawl_client.py:
```python
timeout=aiohttp.ClientTimeout(
    total=40,           # Reduced to 40s (less than asyncio timeout 45s)
    sock_connect=5,     # 5 seconds to establish connection (faster detection)
    sock_read=10        # 10 seconds to read data (faster timeout on stuck connections)
)
```

#### 2. Принудительное закрытие сессии в monitor.py:
```python
except asyncio.TimeoutError as e:
    self.logger.error(f"Timeout scanning {url} after 45s")
    # Принудительно закрыть сессию чтобы не зависало
    if hasattr(self, 'firecrawl') and self.firecrawl:
        try:
            await self.firecrawl.close()
            self.logger.info(f"Force closed Firecrawl session after timeout for {url}")
        except Exception as close_error:
            self.logger.warning(f"Error closing Firecrawl session: {close_error}")
```

### Результат исправления
- ✅ Таймаут aiohttp (40s) теперь меньше asyncio таймаута (45s)
- ✅ При таймауте система корректно переходит к следующему источнику
- ✅ Сессия принудительно закрывается при зависании
- ✅ Система больше не требует принудительного завершения

### Тестирование
```bash
# Тест с новыми таймаутами
python core/main.py --change-tracking --scan --limit 5

# Результат: система корректно обрабатывает таймауты и продолжает работу
```

### Бэкап
Файлы сохранены в: `backups/fix_timeout_20250817_112113/`

---

**📝 Следующее обновление:** При обнаружении новых багов  
**🔗 См. также:** [FLOW.md](FLOW.md), [database-schema.md](database-schema.md)