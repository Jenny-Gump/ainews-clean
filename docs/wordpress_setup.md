# Настройка публикации на WordPress

## Шаг 1: Получите данные для доступа к WordPress API

1. **WordPress API URL**: 
   - Обычно это: `https://your-site.com/wp-json/wp/v2`
   - Замените `your-site.com` на ваш домен

2. **Application Password**:
   - Войдите в WordPress админку
   - Перейдите в Users → Your Profile
   - Прокрутите до секции "Application Passwords"
   - Введите имя приложения (например, "AI News Parser")
   - Нажмите "Add New Application Password"
   - Сохраните сгенерированный пароль (показывается только один раз!)

3. **Username**: 
   - Ваш логин в WordPress

## Шаг 2: Настройте .env файл

Откройте файл `.env` и добавьте:

```env
# WordPress API Configuration
WORDPRESS_API_URL=https://your-site.com/wp-json/wp/v2
WORDPRESS_USERNAME=your_username
WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

Замените:
- `your-site.com` на ваш домен
- `your_username` на ваш логин
- `xxxx xxxx...` на сгенерированный Application Password

## Шаг 3: Создайте категории в WordPress

Войдите в WordPress админку и создайте следующие категории:
- LLM
- Машинное обучение
- Техника
- Digital
- Люди
- Финансы
- Наука
- Обучение
- Другие индустрии

**Важно**: Названия должны точно совпадать!

## Шаг 4: Использование

### Подготовка статей (перевод и адаптация):
```bash
cd "Desktop/AI DEV/ainews-clean"
python core/main.py --wordpress-prepare --limit 5
```

### Публикация на WordPress:
```bash
python core/main.py --wordpress-publish --limit 5
```

### Проверка статуса:
```bash
python core/main.py --stats
```

## Рабочий процесс

1. **Сбор новостей** (автоматически):
   ```bash
   python core/main.py --rss-full
   ```

2. **Подготовка для WordPress** (перевод через DeepSeek):
   ```bash
   python core/main.py --wordpress-prepare --limit 10
   ```

3. **Публикация на сайт**:
   ```bash
   python core/main.py --wordpress-publish --limit 5
   ```

## Настройки публикации

В файле `services/wordpress_publisher.py` можно изменить:
- `status`: 'publish' (сразу публиковать) или 'draft' (сохранить как черновик)
- Модель перевода в `.env`: `WORDPRESS_LLM_MODEL=deepseek-reasoner`

## Проверка результатов

1. В базе данных:
   ```sql
   -- Проверить переведенные статьи
   SELECT * FROM wordpress_articles WHERE translation_status = 'translated';
   
   -- Проверить опубликованные
   SELECT * FROM wordpress_articles WHERE published_to_wp = 1;
   ```

2. В WordPress:
   - Posts → All Posts
   - Проверьте новые посты

## Возможные проблемы

1. **401 Unauthorized**: Проверьте Application Password и username
2. **404 Not Found**: Проверьте URL API (должен заканчиваться на /wp/v2)
3. **Категории не назначаются**: Создайте категории в WordPress с точными названиями
4. **Timeout при переводе**: Уменьшите --limit или используйте более быструю модель

## Дополнительные настройки

### Изменить статус публикации на черновики:
В файле `services/wordpress_publisher.py` строка 479:
```python
'status': 'draft',  # вместо 'publish'
```

### Изменить модель перевода:
В `.env`:
```env
WORDPRESS_LLM_MODEL=deepseek-chat  # быстрее, но менее качественно
```