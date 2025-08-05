# Phase 3: Media Processing

> 📚 **Навигация**: [← Phase 2](phase2_content_parsing.md) | [← Все фазы](../README.md#-пятифазный-пайплайн-обработки) | [→ Phase 4](phase4_wordpress_preparation.md)

## Обзор
Третья фаза - скачивание и валидация медиафайлов (изображений и видео) из спарсенных статей.

## Основные компоненты
- **ExtractMediaDownloaderPlaywright** (`services/media_processor.py`) - скачивание через wget с браузерными заголовками (класс назван для совместимости, но использует wget, не Playwright API)

## Процесс работы

### 1. Выборка медиафайлов
```sql
SELECT * FROM media_files 
WHERE status = 'pending' 
AND file_path IS NULL
```

### 2. Скачивание файлов
- Использует `wget` с браузерными User-Agent заголовками
- Неагрессивный режим: 1 файл одновременно  
- Случайные задержки между файлами (2-5 сек)
- Timeout: 30 секунд на файл
- Без автоматических повторов (обрабатывается один раз)

### 3. Валидация (обновлено!)
```python
# Размер файла
MIN_FILE_SIZE = 3 * 1024       # 3 КБ минимум
MAX_FILE_SIZE = 2 * 1024 * 1024 # 2 МБ максимум

# Размеры изображения (NEW!)
MIN_IMAGE_WIDTH = 300   # минимум 300px
MIN_IMAGE_HEIGHT = 300  # минимум 300px
```

### 4. Процесс валидации
1. **Проверка размера файла**: 3 КБ - 2 МБ
2. **Для изображений**: проверка размеров через PIL
   ```python
   with Image.open(file_path) as img:
       width, height = img.size
       if width < 300 or height < 300:
           # Удаляем файл
           os.remove(file_path)
           raise Exception("Изображение слишком маленькое")
   ```

### 5. Сохранение в БД
```sql
UPDATE media_files SET
    file_path = ?,
    file_size = ?,
    type = ?,
    width = ?,      -- NEW!
    height = ?,     -- NEW!
    status = 'completed'
WHERE media_id = ?
```

## Структура папок
```
data/media/
├── {article_id[:8]}/
│   ├── {hash1}.jpg
│   ├── {hash2}.png
│   └── ...
```

## Команда запуска
```bash
python core/main.py --media-only
```

## Особенности
- **Дедупликация**: по URL хешу  
- **Расширения**: автоопределение из URL
- **Типы**: image (jpg, png, webp) и video (mp4, webm)
- **Безопасность**: обход защит через браузерные заголовки
- **Надежность**: один файл обрабатывается только один раз
- **Статусы**: 'pending' → 'completed' или 'failed' с детальными причинами

## Метрики
- Скачано файлов
- Отфильтровано по размеру
- Отфильтровано по dimensions
- Ошибки скачивания
- Общий размер медиа