# Change Tracking System Documentation

**Версия**: 4.1  
**Статус**: Production Ready (100% источников работают) **+ УПРАВЛЕНИЕ ПАМЯТЬЮ**  
**Последнее обновление**: 19 августа 2025 - **ИСПРАВЛЕНИЕ УТЕЧЕК ПАМЯТИ**

## 📋 Обзор

Change Tracking System — это модульная система для отслеживания изменений на веб-страницах новостных источников. Система извлекает URL статей из markdown-контента, полученного через Firecrawl changeTracking API, и сохраняет их в **облачной Supabase базе данных** для последующей обработки и интеграции с основным пайплайном.

## 🚀 **НОВОЕ В ВЕРСИИ 4.1**: Управление памятью

**✅ Исправлены утечки памяти (v4.1):**
- **gc.collect()** - периодическая очистка памяти каждые 10 источников
- **Минимальные данные** - results['details'] хранит только url/status/urls_found
- **Без markdown в БД** - только хэш для проверки изменений
- **Очистка переменных** - удаление markdown_content и scraped_data после использования
- **Обрезка результатов** - хранение только последних 10 записей в details

**✅ Последовательная обработка источников (v4.0):**
- **Батчи** → **Последовательный цикл** (один источник за раз)
- **Сложная логика** → **Простой for loop с try/finally**
- **Потеря логов** → **Гарантированное логирование каждого шага**
- **Без прогресса** → **Прогресс [1/50] для каждого источника**
- **Задержки sleep()** → **Убраны все искусственные задержки**

### 🎯 Основные возможности
- **47 активных источников** (100% success rate)
- **1050+ URL статей** в Supabase облачной БД
- **Автоматическое обнаружение** новых статей и изменений
- **Интеллектуальная обработка** различных форматов markdown
- **☁️ Supabase Cloud Database** для масштабируемости и надежности
- **Последовательная обработка** для полного контроля
- **🔄 Real-time интеграция** с основным пайплайном
- **📊 Cloud monitoring** через Supabase Dashboard

### 🏗️ Архитектура

```
change_tracking/
├── monitor.py           # Основной мониторинг (ChangeMonitor)
├── url_extractor.py     # Извлечение URL (URLExtractor) 
├── database.py          # ☁️ Supabase Database (ChangeTrackingDB)
├── firecrawl_client.py  # Firecrawl API клиент
└── README.md            # Техническая документация

🌐 Supabase Integration:
├── services/supabase_client.py  # Supabase wrapper client
├── core/db_config.py            # Database configuration
└── .env                         # Supabase credentials
   ├── SUPABASE_URL=https://mtguynupyltlqiwhmilc.supabase.co
   ├── SUPABASE_ANON_KEY=...
   └── SUPABASE_SERVICE_KEY=...
```

## 📚 Детальная документация

### 🔧 Технические компоненты
- **[URL Patterns System](change_tracking/url-patterns.md)** — Система паттернов для фильтрации URL
- **[Source Mapping](change_tracking/source-mapping.md)** — Маппинг источников и их конфигурация
- **[Escape Processing](change_tracking/escape-processing.md)** — Обработка escape-последовательностей в markdown
- **[Database Schema](change_tracking/database-schema.md)** — Структура базы данных
- **[API & Commands](change_tracking/api-commands.md)** — Команды и API интерфейс

### 📊 Рабочие процессы
- **[Processing Flow](../FLOW.md#change-tracking-flow)** — Подробный процесс парсинга и обработки
- **[Детальный Flow](change_tracking/FLOW.md)** — Пошаговый анализ кода и архитектуры системы

## 🚀 Быстрый старт

### Основные команды
```bash
cd "/Users/skynet/Desktop/AI DEV/ainews-clean"

# Сканировать источники последовательно (рекомендуется)
python core/main.py --change-tracking --scan --sequential --limit 5

# Старый батчевый режим (deprecated)
python core/main.py --change-tracking --scan --batch-size 5 --limit 5

# Просмотр статистики (Supabase)  
python core/main.py --change-tracking --tracking-stats

# Экспорт изменений в основную систему (✅ РАБОТАЕТ)
python core/main.py --change-tracking --export-articles

# Полный цикл RSS + Change Tracking (интеграция)
bash scripts/run_rss_and_tracking.sh
```

### Мониторинг (Supabase)
```bash
# Статистика отслеживания (из Supabase)
python core/main.py --change-tracking --tracking-stats

# Последние изменения (из Supabase)
python core/main.py --change-tracking --show-new-urls

# Проверка подключения к Supabase
python3 -c "
from change_tracking.database import ChangeTrackingDB
db = ChangeTrackingDB()
print('✅ Supabase connection successful')
stats = db.get_tracking_stats()
print(f'📊 Tracked articles: {stats[\"total_tracked\"]}')
print(f'🔄 Recent changes: {len(stats[\"recent_changes\"])}')
"
```

## 📈 Статистика системы

**По состоянию на 14 августа 2025 (Supabase Migration):**

### 🚀 Состояние после миграции на Supabase:
- **✅ 50 tracked articles** в Supabase Cloud Database  
- **✅ 10 recent changes** с активными обновлениями
- **✅ 0 errors** в процессе миграции
- **✅ 100% совместимость** с существующими данными
- **⚡ Улучшенная производительность** благодаря облачной инфраструктуре

### ✅ Рабочие источники (47/47 = 100%)

| Категория | Источники | URL |
|-----------|-----------|-----|
| **Top-5** | kuka (111), fanuc (109), nscale (60), perplexity (57), crusoe (48) | 385 |
| **AI Companies** | anthropic, openai, mistral, cohere, ai21, stability, elevenlabs | 168 |  
| **Tech Giants** | google (research, cloud, deepmind), microsoft, aws | 89 |
| **Platforms** | huggingface, databricks, scale, together | 124 |
| **Robotics** | waymo, abb, fanuc, kinova, kuka, doosan, manus | 278 |
| **Healthcare** | tempus, pathai, openevidence | 67 |
| **Other** | writer, uizard, soundhound, audioscenic, suno | 87 |

### 📊 Ключевые метрики
- **Общий рост**: 275% (было 280 URL → стало 1050+ URL)
- **Источники**: +74% (было 27 → стало 47)
- **Успех rate**: 100% источников работают
- **Среднее время сканирования**: ~3 сек/источник
- **Хранение**: ☁️ **Supabase Cloud Database** (tracked_articles + tracked_urls)

## 🔄 Режимы обработки (v4.0)

### Последовательная обработка (рекомендуется)
```python
# Новый метод - полный контроль и логирование
async def scan_sources_sequential():
    for i, url in enumerate(sources, 1):
        log_operation(f'[{i}/{total}] 🔍 Scanning: {domain}')
        try:
            result = await scan_webpage(url)
            log_operation(f'[{i}/{total}] ✅ Completed: {domain}')
        except TimeoutError:
            log_operation(f'[{i}/{total}] ⏱️ Timeout: {domain}')
        except Exception:
            log_operation(f'[{i}/{total}] ❌ Error: {domain}')
        finally:
            # ВСЕГДА логируем завершение
```

### Батчевая обработка (legacy)
- Всё еще доступна через `--batch-size`
- Усложняет отладку из-за группировки источников
- Будет удалена в версии 5.0

## 🛠️ Конфигурация

### Источники
Конфигурация источников находится в:
- **`data/tracking_sources.json`** — JSON конфигурация всех 47 источников
- **Структура**: `{source_id, name, url, rss_url, type, category}`

### URL Паттерны  
Система использует 3 типа конфигураций:
1. **domain_patterns** — Разрешенные пути для каждого домена
2. **escape_sources** — Источники с escape-последовательностями (`\\\\\\\\`)
3. **exclude_patterns** — Исключающие паттерны (медиа, навигация)

## 🔍 Диагностика

### Проверка источника
```python
# Диагностика конкретного источника
from change_tracking.monitor import ChangeMonitor
monitor = ChangeMonitor()
result = await monitor.scan_webpage('https://example.com/blog')
```

### Логирование
- **Модуль**: `change_tracking.*`
- **Уровень**: INFO для статистики, WARNING для проблем
- **Файлы**: Используется система app_logging

## 🔗 Интеграция

### С основной системой (через Supabase)
- **✅ Экспорт**: URL автоматически экспортируются в основную Supabase таблицу `articles`
- **✅ RSS Integration**: Полная интеграция через `scripts/run_rss_and_tracking.sh`
- **✅ Monitoring**: Интеграция с мониторинг дашбордом через единую Supabase БД
- **✅ Unified ecosystem**: Change Tracking теперь часть единой архитектуры

### С Firecrawl API
- **changeTracking API**: Автоматическое обнаружение изменений
- **markdown формат**: Получение structured контента
- **Rate limiting**: Соблюдение лимитов API

## 🎯 Результаты внедрения

**Достижения (15.08.2025):**
- ✅ **Все 47 источников работают** (достигнут 100% success rate)
- ✅ **1050+ URL в базе** (рост в 3.75 раза)  
- ✅ **Критические баги исправлены** (Store URLs и FK constraints)
- ✅ **Система production-ready** и стабильна

**Методы исправления:**
- **escape_sources** — 75% источников (21 из 28)
- **domain_patterns** — 20% источников  
- **URL fixes** — 5% источников (perplexity)

---

## 🔧 Оптимизации производительности (v3.3)

### MVP решение проблемы зависаний (17.08.2025) 🚀
- **ПРОБЛЕМА**: Постоянные зависания на RSS Discovery и Change Tracking из-за многослойных конфликтующих таймаутов
- **РЕШЕНИЕ**: Process Supervisor + упрощение таймаутов + fail-fast стратегия
- **РЕЗУЛЬТАТ**: Система НИКОГДА не зависает >60 сек, обработка за 2-30 сек на источник

**Ключевые изменения:**
- ✅ **Process Supervisor** - изоляция каждого источника в отдельном процессе
- ✅ **RSS Discovery** - таймаут для feedparser.parse(), уменьшение HTTP таймаутов  
- ✅ **Change Tracking** - убраны retry (max_retries=1), убрана задержка sleep(8)
- ✅ **Философия** - fail fast, skip forward, никаких сложных retry

### Исправление критического бага экспорта (16.08.2025)
- **ПРОБЛЕМА**: Логирование всех URL происходило ДО реального экспорта, процесс зависал после первого URL
- **РЕШЕНИЕ**: Логирование перенесено внутрь цикла экспорта, каждый URL логируется при обработке
- **РЕЗУЛЬТАТ**: Все URL корректно экспортируются и помечаются как обработанные

### Улучшения обработки ошибок
- **Индивидуальная обработка**: Каждый URL обрабатывается отдельно с try-except
- **Продолжение при ошибках**: Ошибка одного URL не прерывает обработку остальных
- **Детальная диагностика**: Логирование времени каждой операции и статистики
- **Мгновенная пометка**: URL помечается как exported сразу после успешного экспорта

### Исправления критических багов
- **Duplicate key errors**: Добавлен `on_conflict='source_id'` в upsert операции
- **Зависание при экспорте**: Удален проблемный signal.SIGALRM, добавлена правильная обработка
- **Двойной экспорт**: URL теперь корректно помечаются как `exported_to_articles=true`

## 📄 История изменений

**v4.1 (19.08.2025) - MEMORY MANAGEMENT** 💾
- **✅ ИСПРАВЛЕНЫ УТЕЧКИ ПАМЯТИ** - проблема зависания hai.stanford.edu решена
- **✅ ПЕРИОДИЧЕСКАЯ ОЧИСТКА** - gc.collect() каждые 10 источников
- **✅ МИНИМАЛЬНЫЕ ДАННЫЕ** - только необходимая информация в results
- **✅ БЕЗ КОНТЕНТА В БД** - экономия памяти на больших markdown
- **✅ ОЧИСТКА ПЕРЕМЕННЫХ** - освобождение памяти после обработки
- **✅ СТАБИЛЬНАЯ РАБОТА** - обработка 47+ источников без зависаний

**v4.0 (19.08.2025) - SEQUENTIAL PROCESSING** 🎯
- **✅ ПОСЛЕДОВАТЕЛЬНАЯ ОБРАБОТКА** - новый метод scan_sources_sequential()
- **✅ ПОЛНОЕ ЛОГИРОВАНИЕ** - каждый источник с прогрессом [1/50], [2/50]
- **✅ ГАРАНТИЯ ЛОГОВ** - try/finally блоки для каждого источника
- **✅ УБРАНЫ ЗАДЕРЖКИ** - никаких sleep(), быстрая обработка
- **✅ ОПЦИЯ --sequential** - выбор режима обработки в main.py
- **✅ ПРОСТОТА ОТЛАДКИ** - последовательное выполнение, легко найти проблему

**v3.3 (17.08.2025) - TIMEOUT FIX MVP** 🚀
- **✅ РЕШЕНА ПРОБЛЕМА ЗАВИСАНИЙ** - Process Supervisor с жёстким таймаутом 60 сек
- **✅ УПРОЩЕНЫ ТАЙМАУТЫ** - Убраны вложенные таймауты и конфликты
- **✅ RSS DISCOVERY ОПТИМИЗИРОВАН** - Таймаут для feedparser, уменьшены HTTP таймауты
- **✅ CHANGE TRACKING УПРОЩЕН** - max_retries=1, убрана задержка, таймаут 30s
- **✅ FAIL-FAST СТРАТЕГИЯ** - Ошибка = skip, никаких сложных retry
- **✅ ТЕСТЫ ПРОЙДЕНЫ** - 0 зависаний, обработка за 2-30 сек на источник

**v3.2 (16.08.2025) - EXPORT FIX** 🔧
- **✅ ИСПРАВЛЕН КРИТИЧЕСКИЙ БАГ ЭКСПОРТА** - Логирование перенесено внутрь цикла обработки
- **✅ УСТРАНЕНО ЗАВИСАНИЕ** - Удален проблемный signal.SIGALRM который не работает с asyncio
- **✅ КОРРЕКТНАЯ ПОМЕТКА URL** - Каждый URL помечается как exported сразу после обработки
- **✅ УЛУЧШЕНА ОБРАБОТКА ОШИБОК** - Ошибка одного URL не прерывает весь процесс
- **✅ ДЕТАЛЬНАЯ ДИАГНОСТИКА** - Логирование времени операций и полная статистика

**v3.1 (15.08.2025) - PERFORMANCE & STABILITY** 🚀
- **✅ ИСПРАВЛЕНЫ ЗАВИСАНИЯ** - Добавлены таймауты для всех Supabase операций
- **✅ DUPLICATE KEY FIXED** - Корректная обработка конфликтов через on_conflict
- **✅ БАТЧЕВАЯ ОБРАБОТКА** - URL обрабатываются батчами по 50 для оптимизации
- **✅ ПОЛНОЕ ЛОГИРОВАНИЕ** - Все URL логируются с индексами и прогрессом
- **✅ МОНИТОРИНГ ПРОИЗВОДИТЕЛЬНОСТИ** - Замер времени и предупреждения о медленных операциях

**v3.0 (14.08.2025) - SUPABASE MIGRATION COMPLETE** 🚀
- **✅ ПОЛНАЯ МИГРАЦИЯ НА SUPABASE** - SQLite → Supabase Cloud Database
- **✅ Unified ecosystem** - интеграция с основным пайплайном через единую БД
- **✅ API Layer rewrite** - все `conn.execute()` заменены на `supabase.client.table()` операции
- **✅ Cloud scalability** - автоматическое масштабирование и отказоустойчивость
- **✅ Real-time capabilities** - возможность подписки на изменения данных
- **✅ Production testing** - 50 tracked articles мигрировано без ошибок
- **✅ Export integration** - полная интеграция экспорта с основной системой
- **✅ Monitoring integration** - RSS + Change Tracking в одном скрипте

**v2.0 (11.08.2025)**
- Достигнут 100% success rate (47/47 источников)
- Добавлено 1020 URL статей
- Исправлена система escape-sequences обработки
- Оптимизированы domain_patterns для всех источников

**v1.0 (07.08.2025)**  
- Первоначальная версия системы
- 27 работающих источников из 49 (55%)
- 280 URL в базе
- Базовая архитектура и API

---

**📧 Техническая поддержка:** См. [API & Commands](change_tracking/api-commands.md) для детальных инструкций