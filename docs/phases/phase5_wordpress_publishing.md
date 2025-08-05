# Phase 5: WordPress Publishing

> 📚 **Навигация**: [← Phase 4](phase4_wordpress_preparation.md) | [← Все фазы](../README.md#-пятифазный-пайплайн-обработки)

## Обзор
Пятая фаза - публикация подготовленных статей в WordPress с медиафайлами.

## Основные компоненты
- **WordPressPublisher** (`services/wordpress_publisher.py`)
- **WordPress REST API** - для создания постов и загрузки медиа
- **DeepSeek Chat API** - для перевода метаданных изображений

## Процесс работы

### 1. Выборка статей для публикации
```sql
SELECT * FROM wordpress_articles 
WHERE translation_status = 'translated' 
  AND published_to_wp = 0
LIMIT ?
```

### 2. Создание поста в WordPress
```python
post_data = {
    'title': article['title'],
    'content': article['content'],
    'excerpt': article['excerpt'],
    'status': 'draft',  # Всегда черновик для review
    'categories': category_ids,
    'tags': tag_ids,
    'meta': {
        '_yoast_wpseo_title': article['_yoast_wpseo_title'],
        '_yoast_wpseo_metadesc': article['_yoast_wpseo_metadesc'],
        '_yoast_wpseo_focuskw': article['focus_keyword']
    }
}
```

### 3. Загрузка медиафайлов
1. **Перевод метаданных изображений**:
   ```python
   # Через DeepSeek Chat API
   alt_text_ru = "Изображение для " + article_title
   caption_ru = translated_caption if caption else None
   ```

2. **Загрузка в WordPress**:
   ```python
   files = {'file': (filename, file_content, mime_type)}
   response = requests.post(
       f"{api_url}/media",
       files=files,
       headers={'Authorization': f'Basic {auth}'},
       data={
           'post': wp_post_id,
           'alt_text': alt_text_ru,
           'caption': caption_ru
       }
   )
   ```

### 4. Обработка изображений в статье (обновлено!)
**Правила размещения**:
- **1 изображение**: только featured image
- **2+ изображения**: первое - featured, остальные равномерно в контенте

```python
# Новый алгоритм распределения
if len(images) == 1:
    # Только featured image
    set_featured_media(wp_post_id, images[0])
else:
    # Первое - featured
    set_featured_media(wp_post_id, images[0])
    
    # Остальные - равномерно по параграфам
    images_to_insert = images[1:]
    positions = calculate_positions(paragraph_count, len(images_to_insert))
    insert_images_at_positions(content, images_to_insert, positions)
```

### 5. Обновление статуса
```sql
UPDATE wordpress_articles SET
    published_to_wp = 1,
    wp_post_id = ?
WHERE article_id = ?
```

## Валидация медиафайлов (NEW!)
- **Размер файла**: 3 КБ - 2 МБ
- **Размеры изображения**: минимум 300×300 пикселей
- Изображения не прошедшие валидацию автоматически удаляются

## WordPress конфигурация
```env
WORDPRESS_API_URL=https://ailynx.ru/wp-json/wp/v2
WORDPRESS_USERNAME=admin
WORDPRESS_APP_PASSWORD=tE85 PFT4 Ghq9 nl26 nQlt gBnG
```

## Команда запуска
```bash
python core/main.py --wordpress-publish --limit 5
```

## Особенности
- **Статус draft**: все посты создаются как черновики
- **Батчевая загрузка**: медиафайлы загружаются после создания поста
- **Graceful degradation**: пост публикуется даже если часть медиа не загрузилась
- **Дедупликация**: проверка существующих постов по заголовку

## Метрики
- Опубликовано постов
- Загружено медиафайлов
- Ошибки публикации
- Время публикации