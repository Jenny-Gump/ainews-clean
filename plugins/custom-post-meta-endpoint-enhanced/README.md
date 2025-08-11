# Custom Post Meta Endpoint Enhanced

## 🚀 Описание
Расширенная версия плагина WordPress REST API для создания постов и управления Yoast SEO мета-данными категорий и тегов.

## ✨ Новые возможности в версии 2.0.0
- ✅ **Обновление мета-описаний категорий** через REST API
- ✅ **Обновление мета-описаний тегов** через REST API  
- ✅ **Полная совместимость с Yoast SEO**
- ✅ **Без ограничений на длину SEO полей**
- ✅ **Расширенная документация в админ-панели**

## 📋 API Эндпоинты

### 1. Создание постов
```
POST /wp-json/custom-post-meta/v1/posts
```

### 2. Обновление категорий  
```
PUT /wp-json/custom-post-meta/v1/categories/{id}
```

### 3. Обновление тегов
```
PUT /wp-json/custom-post-meta/v1/tags/{id}  
```

## 🔧 Установка
1. Загрузите папку плагина в `/wp-content/plugins/`
2. Активируйте плагин в админ-панели WordPress
3. Настройте API ключ в **Настройки → Post Meta API**

## 🛡️ Безопасность
- Требуется API ключ в заголовке `X-API-Key`
- Валидация всех входящих данных
- Sanitization полей перед сохранением
- Проверка существования категорий/тегов

## 📖 Примеры использования

### Обновить категорию "Разработка":
```bash
curl -X PUT "https://yoursite.com/wp-json/custom-post-meta/v1/categories/131" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "seo_title": "AI в разработке | AI LYNX",
    "seo_description": "Новости разработки с AI: кодинг-ассистенты, GitHub Copilot, инструменты программирования с ИИ",
    "focus_keyword": "AI разработка"
  }'
```

### Обновить тег "OpenAI":
```bash  
curl -X PUT "https://yoursite.com/wp-json/custom-post-meta/v1/tags/83" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "seo_title": "OpenAI новости | AI LYNX", 
    "seo_description": "Последние новости OpenAI: GPT модели, ChatGPT обновления, исследования в области ИИ",
    "focus_keyword": "OpenAI"
  }'
```

## 📊 Поддерживаемые поля

### Для категорий и тегов:
- `seo_title` - SEO заголовок (без ограничений по длине)
- `seo_description` - SEO описание (без ограничений по длине) 
- `focus_keyword` - Ключевое слово для Yoast SEO
- `description` - Обычное описание категории/тега

### Для постов:
- Все поля из оригинального плагина
- Полная поддержка Yoast SEO полей
- Категории и теги

## 🔄 Миграция
Плагин полностью совместим с существующим `custom-post-meta-endpoint-simple`. 
Просто замените файлы - все API ключи и настройки сохранятся.

## 🆕 Changelog

### Version 2.0.0 (2025-08-10)
- ➕ Добавлены эндпоинты для категорий и тегов
- ➕ Поддержка Yoast SEO мета-полей для taxonomies
- ➕ Расширенная документация в админ-панели
- ➕ Примеры CURL запросов
- 🔧 Улучшена валидация и безопасность

### Version 1.0.0
- ✅ Базовая функциональность создания постов
- ✅ Поддержка Yoast SEO для постов

## 👨‍💻 Автор
Модифицированная версия для проекта AI News Parser Clean

## 📄 Лицензия
GPL v2 or later