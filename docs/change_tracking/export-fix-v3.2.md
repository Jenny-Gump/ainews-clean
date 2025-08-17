# Export Fix v3.2 - Исправление критического бага экспорта

**Дата**: 16 августа 2025  
**Версия**: 3.3  
**Статус**: ✅ ПОЛНОСТЬЮ ИСПРАВЛЕНО

## 🔴 Проблема

### Симптомы:
1. При запуске экспорта (`--export-articles`) в логах показывалось 25 URL для экспорта
2. Реально экспортировался только 1 URL (первый в списке)
3. Процесс зависал после первого URL
4. При повторном запуске те же 25 URL снова появлялись для экспорта
5. URL не помечались как `exported_to_articles=true`

### Анализ проблемы:

#### Неправильный порядок логирования:
```python
# БЫЛО (monitor.py):
# Сначала логировались ВСЕ 25 URL
for idx, url_data in enumerate(new_urls, 1):
    log_operation('change_tracking_export_url', ...)
    time.sleep(0.5)

# Потом вызывался реальный экспорт
exported_count = self.db.export_urls_to_articles(new_urls)
```

#### Зависание в export_urls_to_articles:
- Процесс зависал после обработки первого URL
- Проблема была в signal.SIGALRM который не совместим с httpx/asyncio
- Батчевая обработка усложняла диагностику

## ✅ Решение

### 1. Исправлен порядок логирования (monitor.py):
```python
# СТАЛО:
# Логируем только начало
log_operation('change_tracking_export_start', 
              message=f'📤 Starting export of {len(new_urls)} URLs')

# Вызываем экспорт (логирование внутри)
exported_count = self.db.export_urls_to_articles(new_urls)
```

### 2. Переписана функция export_urls_to_articles (database.py):

#### Ключевые изменения:
- **Удален signal.SIGALRM** - не работает с asyncio/httpx
- **Индивидуальная обработка** - каждый URL в отдельном try-except
- **Логирование в процессе** - каждый URL логируется при обработке
- **Немедленная пометка** - URL помечается как exported сразу после вставки
- **Детальная статистика** - exported, skipped, failed counts

#### Новая структура:
```python
def export_urls_to_articles(self, new_urls):
    for idx, url_data in enumerate(new_urls, 1):
        try:
            # Логируем прогресс
            log_operation('change_tracking_export_url', 
                         message=f'📤 Exporting [{idx}/{total}]: {domain}')
            
            # Проверяем дубликаты
            if article_exists(url):
                mark_as_exported(url_id)
                skipped_count += 1
                continue
                
            # Вставляем в articles
            result = insert_article(data)
            
            if result:
                # Сразу помечаем как exported
                mark_as_exported(url_id)
                exported_count += 1
                
        except Exception as e:
            # Ошибка одного URL не прерывает остальные
            failed_count += 1
            continue
```

### 3. Добавлена функция _mark_url_as_exported:
```python
def _mark_url_as_exported(self, url_id: int) -> bool:
    """Помечает URL как экспортированный в tracked_urls"""
    self.supabase.client.table('tracked_urls')\
        .update({
            'exported_to_articles': True,
            'exported_at': datetime.now(timezone.utc).isoformat(),
            'is_new': False
        })\
        .eq('id', url_id)\
        .execute()
```

## 📊 Результаты тестирования (v3.3)

### Исправления v3.3:
1. **Синхронизация флагов**: Очищены 3 URL которые были в articles но не помечены как exported
2. **Таймаут защита**: Добавлен таймаут 3 сек в article_exists() 
3. **Батч-проверка**: Все URL проверяются одним запросом перед экспортом
4. **Оптимизация**: Убрана двойная проверка каждого URL

### Финальный тест: Экспорт всех 12 URL
```bash
# Очистка застрявших URL
UPDATE tracked_urls SET exported_to_articles=true WHERE article_url IN (SELECT url FROM articles)

# Экспорт первых 3 URL
python3 core/main.py --change-tracking --export-articles --limit 3
✅ Экспортировано: 3/3 успешно, без зависаний

# Экспорт оставшихся 9 URL  
python3 core/main.py --change-tracking --export-articles --limit 10
✅ Экспортировано: 9/9 успешно, без зависаний
```

### Проверка в Supabase:
- ✅ 12 новых URL добавлены в таблицу `articles`
- ✅ Все 12 URL помечены как `exported_to_articles=true`
- ✅ 0 URL осталось с флагом `is_new=true`
- ✅ Нет зависаний даже на длинных AWS URL

## 🎯 Ключевые улучшения

1. **Надежность**: Ошибка одного URL не прерывает весь процесс
2. **Прозрачность**: Каждый шаг логируется с временем выполнения
3. **Корректность**: URL помечаются сразу после успешного экспорта
4. **Производительность**: Удалены проблемные таймауты signal.SIGALRM
5. **Диагностика**: Полная статистика: exported, skipped, failed

## 📝 Затронутые файлы

1. `change_tracking/monitor.py`:
   - Функция `export_new_urls_to_articles` - изменен порядок логирования

2. `change_tracking/database.py`:
   - Функция `export_urls_to_articles` - полностью переписана
   - Добавлена функция `_mark_url_as_exported`

3. `services/supabase_client.py`:
   - Добавлен `on_conflict='source_id'` в upsert операции

## ⚠️ Важные замечания

1. **signal.SIGALRM не работает с asyncio/httpx** - не используйте для таймаутов
2. **Логирование должно происходить во время операции**, а не заранее
3. **Каждый URL должен обрабатываться независимо** для надежности
4. **Пометка exported должна быть немедленной** после успешной вставки

---

**Версия документа**: 1.0  
**Автор**: Claude (AI Assistant)  
**Дата создания**: 16.08.2025