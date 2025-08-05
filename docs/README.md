# Документация AI News Parser

📚 **Центральный хаб документации проекта**

## 🔄 Пятифазный пайплайн обработки

Система работает через 5 последовательных фаз:

### [📡 Phase 1: RSS Discovery](phases/phase1_rss_discovery.md)
Сканирование RSS лент и обнаружение новых статей
- 26 источников новостей об ИИ
- Фильтрация по дате и дубликатам
- Сохранение в БД со статусом `pending`

### [🔍 Phase 2: Content Parsing](phases/phase2_content_parsing.md)
Извлечение полного контента через Firecrawl Extract API
- Markdown формат контента
- Метаданные и медиафайлы
- Обновление статуса на `completed`

### [📸 Phase 3: Media Processing](phases/phase3_media_processing.md)
Скачивание и валидация медиафайлов
- Валидация размеров (≥300×300px)
- Проверка размера файла (3KB-2MB)
- Дедупликация по хешу

### [🌐 Phase 4: WordPress Preparation](phases/phase4_wordpress_preparation.md)
Подготовка контента для WordPress
- Перевод на русский (DeepSeek Chat)
- SEO-оптимизация (Yoast)
- Категоризация и тегирование

### [📝 Phase 5: WordPress Publishing](phases/phase5_wordpress_publishing.md)
Публикация в WordPress
- Создание черновиков постов
- Загрузка медиа с метаданными
- Умное размещение изображений

## 📋 Техническая документация

### Архитектура
- **[Обзор архитектуры](architecture.md)** - Дизайн системы и компоненты
- **[База данных](DATABASE_SCHEMA.md)** - Структура таблиц и связи
- **[Обзор пайплайна](PIPELINE_OVERVIEW.md)** - Детальный workflow

### API интеграции
- **[API Reference](API/API_REFERENCE.md)** - Обзор всех API
- **[Firecrawl Client](API/FIRECRAWL_CLIENT_README.md)** - Extract API клиент
- **[WordPress Integration](API/wordpress_integration.md)** - REST API WordPress
- **[Yoast SEO](API/yoast_seo_integration.md)** - SEO метаданные

### Настройка и эксплуатация
- **[WordPress Setup](wordpress_setup.md)** - Установка и настройка WP
- **[Troubleshooting](TROUBLESHOOTING.md)** - Решение проблем

## 🚀 Быстрые команды

```bash
# Полный цикл обработки
python core/main.py --rss-full          # Фазы 1-3
python core/main.py --wordpress-prepare # Фаза 4
python core/main.py --wordpress-publish # Фаза 5

# Отдельные фазы
python core/main.py --rss-discover      # Только RSS
python core/main.py --parse-pending     # Только парсинг
python core/main.py --media-only        # Только медиа
```

## 📁 Структура документации

```
docs/
├── README.md              # Этот файл
├── phases/               # Документация по фазам
│   ├── phase1_rss_discovery.md
│   ├── phase2_content_parsing.md
│   ├── phase3_media_processing.md
│   ├── phase4_wordpress_preparation.md
│   └── phase5_wordpress_publishing.md
├── API/                  # API документация
│   ├── API_REFERENCE.md
│   ├── FIRECRAWL_CLIENT_README.md
│   ├── wordpress_integration.md
│   └── yoast_seo_integration.md
├── architecture.md       # Архитектура системы
├── DATABASE_SCHEMA.md    # Схема БД
├── PIPELINE_OVERVIEW.md  # Обзор пайплайна
├── wordpress_setup.md    # Настройка WordPress
└── TROUBLESHOOTING.md   # Решение проблем
```

## 🔗 Связанная документация

- **[Основной README](../README.md)** - Обзор проекта
- **[Мониторинг](../monitoring/README.md)** - Веб-дашборд
- **[Логирование](../app_logging/README.md)** - Система логов
- **[CLAUDE.md](../CLAUDE.md)** - Для AI-ассистентов

---

💡 **Совет**: Начните с [обзора пайплайна](PIPELINE_OVERVIEW.md) для понимания общей картины, затем изучайте отдельные фазы по необходимости.