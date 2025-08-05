# Phase 4: WordPress Preparation

> 📚 **Навигация**: [← Phase 3](phase3_media_processing.md) | [← Все фазы](../README.md#-пятифазный-пайплайн-обработки) | [→ Phase 5](phase5_wordpress_publishing.md)

## Обзор
Четвертая фаза - подготовка статей для публикации в WordPress: перевод на русский язык и SEO-оптимизация.

⚠️ **ВАЖНО**: Эта фаза запускается **только** для статей с `media_status = 'ready'`, что гарантирует завершение обработки медиафайлов в Phase 3.

## Основные компоненты
- **WordPressPublisher** (`services/wordpress_publisher.py`) - основной класс
- **DeepSeek Chat API** - для перевода и переписывания

## Процесс работы

### 1. Выборка статей для обработки (с проверкой зависимостей)
```sql
SELECT a.article_id, a.title, a.content, a.summary, a.tags, 
       a.categories, a.language, a.url, a.source_id, a.published_date
FROM articles a
LEFT JOIN wordpress_articles w ON a.article_id = w.article_id
WHERE a.content_status = 'parsed' 
  AND a.media_status = 'ready'    -- КЛЮЧЕВОЕ УСЛОВИЕ!
  AND a.content IS NOT NULL
  AND w.id IS NULL
ORDER BY a.published_date DESC
LIMIT ?
```

**Условие `media_status = 'ready'` гарантирует:**
- Статьи без медиафайлов обрабатываются сразу
- Статьи с медиафайлами ждут завершения Phase 3
- Исключает проблемы с незавершенной обработкой медиа

### 2. Перевод и переписывание через DeepSeek
```python
prompt = f"""
Переведи и перепиши эту статью об ИИ на русский язык.

Требования:
1. Сохрани все технические термины и названия компаний/продуктов
2. Адаптируй под русскоязычную аудиторию
3. Сохрани фактическую точность
4. Сделай текст живым и интересным
5. Добавь краткий комментарий редактора в конце

Формат ответа JSON:
{{
    "title": "Заголовок на русском",
    "content": "Полный текст статьи с HTML разметкой",
    "excerpt": "Краткое описание 1-2 предложения",
    "focus_keyword": "ключевое слово для SEO",
    "categories": ["категория1", "категория2"],
    "tags": ["тег1", "тег2", "тег3"]
}}
"""
```

### 3. SEO оптимизация (Yoast формат)
```python
# Генерация SEO заголовка (max 60 символов)
seo_title = self._generate_seo_title(title, focus_keyword)

# Генерация meta описания (max 160 символов)  
meta_description = self._generate_meta_description(excerpt, focus_keyword)
```

### 4. Сохранение в wordpress_articles
```sql
INSERT INTO wordpress_articles (
    article_id, title, content, excerpt, slug,
    categories, tags, focus_keyword,
    _yoast_wpseo_title, _yoast_wpseo_metadesc,
    featured_image_index, translation_status,
    source_language, target_language, llm_model
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'translated', 'en', 'ru', 'deepseek-chat')
```

## Категории WordPress
- Новости (главная)
  - LLM и языковые модели
  - Компьютерное зрение  
  - Обработка речи
  - Робототехника и автоматизация
  - И другие...

## Команда запуска
```bash
python core/main.py --wordpress-prepare --limit 10
```

## Обработка медиафайлов
- Определение featured image (первое изображение)
- Подготовка данных для последующей загрузки
- Сохранение индекса featured image

## Особенности
- **Батчевая обработка**: до 10 статей за раз
- **Обработка ошибок**: пропуск проблемных статей
- **Валидация**: проверка корректности перевода
- **Логирование**: подробные логи процесса

## Метрики
- Обработано статей
- Успешно переведено
- Ошибки перевода
- Среднее время обработки