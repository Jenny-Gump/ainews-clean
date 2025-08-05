# Руководство по устранению проблем

## Критические проблемы системы

### 1. Дублирование базы данных

**Проблема:** Система создала дублированную базу данных в директории мониторинга.

**Симптомы:**
- Изменения в дашборде не отражаются в основной системе
- PUT запросы к `/api/extract/config` не сохраняют данные
- Разные значения `last_parsed` в дашборде и основной БД

**Расположение баз:**
- Основная: `/Users/skynet/Desktop/AI DEV/ainews-clean/data/ainews.db` ✅
- Дубликат: `/Users/skynet/Desktop/AI DEV/ainews-clean/monitoring/data/ainews.db` ❌ (удалена)

**Решение:**
```bash
# 1. Удалить дублированную базу
rm /Users/skynet/Desktop/AI DEV/ainews-clean/monitoring/data/ainews.db

# 2. Обновить extract_api.py для использования абсолютного пути
# В файле monitoring/extract_api.py изменить:
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'ainews.db')
```

### 2. Синхронизация last_parsed между источниками

**Проблема:** Глобальная дата `last_parsed` не синхронизировалась между всеми источниками.

**Симптомы:**
- Разные источники парсят статьи за разные периоды
- Невозможно установить единую дату для всех RSS лент
- Дашборд показывает неправильную дату

**Решение реализовано:**
1. Создана таблица `global_config` для хранения глобальных настроек
2. Добавлены методы в `database.py`:
   - `get_global_last_parsed()`
   - `set_global_last_parsed()`
3. Обновлен `rss_discovery.py` для использования глобальной даты

**Как проверить текущую дату:**
```sql
SELECT value FROM global_config WHERE key = 'global_last_parsed';
```

### 3. Orphaned медиафайлы (255 файлов - 73%)

**Проблема:** При удалении статей медиафайлы остаются в БД без связи.

**Симптомы:**
- 255 медиафайлов не связаны со статьями
- Занимают место в БД и на диске
- Невозможно определить их принадлежность

**Запрос для поиска:**
```sql
SELECT COUNT(*) FROM media_files m 
LEFT JOIN articles a ON m.article_id = a.article_id 
WHERE a.article_id IS NULL;
```

**Решение:**
```sql
-- Удалить orphaned файлы
DELETE FROM media_files 
WHERE article_id NOT IN (SELECT article_id FROM articles);

-- Запустить VACUUM для очистки места
VACUUM;
```

**Предотвращение:** Добавить периодическую очистку orphaned записей в cron или скрипт обслуживания.

### 4. Пустые error_logs (0 записей)

**Проблема:** Система не логирует ошибки в базу мониторинга.

**Симптомы:**
- Таблица `error_logs` всегда пустая
- Ошибки теряются после перезапуска
- Невозможно анализировать проблемы

**Проверка:**
```sql
SELECT COUNT(*) FROM error_logs; -- Результат: 0
```

**Решение:** Реализовать вызов `monitoring_integration.on_error()` во всех местах обработки ошибок.

### 5. Отключенная система алертов

**Проблема:** Настроенные алерты не отправляются.

**Симптомы:**
- Критические ошибки не замечаются вовремя
- Нет уведомлений о падении источников
- Система может деградировать незаметно

**Решение:** Включить и настроить алерты в `monitoring/alerts.py`.

### 6. Дублирование времени в логах

**Проблема:** В логах отображается время несколько раз.

**Симптомы:**
```
[14:17:59] [14:17:59] [INFO] Message
```

**Причина:** Время добавляется в нескольких местах:
1. В форматтере Python логгера
2. В JavaScript при отображении
3. В сообщении от сервера

**Решение:** Использовать единый формат без времени в Python:
```python
formatter = logging.Formatter('[%(levelname)s] %(message)s')
```

## Частые проблемы

### RSS Discovery находит 0 статей

**Проверки:**
1. Проверить глобальную дату last_parsed:
   ```bash
   python core/main.py --stats
   ```

2. Проверить активность источников:
   ```sql
   SELECT name, is_active FROM sources;
   ```

3. Проверить доступность RSS:
   ```bash
   curl -I https://techcrunch.com/category/artificial-intelligence/rss
   ```

### Firecrawl API возвращает ошибки

**Проверки:**
1. Проверить API ключ в `.env`:
   ```
   FIRECRAWL_API_KEY=your_key_here
   ```

2. Проверить лимиты API:
   - 500 запросов в минуту
   - 10 параллельных запросов

3. Проверить статус коды в логах

### Медиафайлы не скачиваются

**Проверки:**
1. Проверить права доступа:
   ```bash
   ls -la data/media/
   ```

2. Проверить место на диске:
   ```bash
   df -h
   ```

3. Проверить URL медиафайлов в БД

### Dashboard не обновляется

**Проверки:**
1. WebSocket соединение:
   - Открыть консоль браузера
   - Проверить вкладку Network -> WS

2. Проверить процесс мониторинга:
   ```bash
   ps aux | grep "monitoring/app.py"
   ```

3. Перезапустить мониторинг:
   ```bash
   cd monitoring && ./stop_monitoring.sh && ./start_monitoring.sh
   ```

## Диагностические команды

### Проверка здоровья системы
```bash
# Общая статистика
python core/main.py --stats

# Список источников
python core/main.py --list-sources

# Проверка БД
sqlite3 data/ainews.db "SELECT COUNT(*) FROM articles;"
```

### Проверка мониторинга
```bash
# API статус
curl http://localhost:8001/api/system/status

# Метрики источников
curl http://localhost:8001/api/stats/sources
```

### Очистка системы
```bash
# Удалить старые логи
find app_logging/logs -name "*.log" -mtime +7 -delete

# Очистить orphaned медиа
sqlite3 data/ainews.db "DELETE FROM media_files WHERE article_id NOT IN (SELECT article_id FROM articles);"
```

## Восстановление после сбоев

### Полный сброс last_parsed
```sql
UPDATE global_config SET value = '2025-08-01T00:00:00Z' WHERE key = 'global_last_parsed';
```

### Переиндексация источников
```bash
python scripts/reindex_sources.py
```

### Восстановление из бэкапа
```bash
# Остановить все процессы
cd monitoring && ./stop_monitoring.sh

# Восстановить БД
cp backup/ainews.db data/ainews.db
cp backup/monitoring.db data/monitoring.db

# Запустить систему
./start_monitoring.sh
```

## Контакты для поддержки

При критических проблемах обращаться:
- Документация: `/Users/skynet/Desktop/AI DEV/ainews-clean/docs/`
- Логи: `/Users/skynet/Desktop/AI DEV/ainews-clean/app_logging/logs/`
- Конфигурация: `/Users/skynet/Desktop/AI DEV/ainews-clean/.env`