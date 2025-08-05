# AI News Parser Pipeline Overview

> 📚 **Навигация**: [← Документация](README.md) | [← Главная](../README.md)

## Обзор системы
AI News Parser - автоматизированная система сбора, обработки и публикации новостей об искусственном интеллекте на русском языке.

## 🔄 Пятифазный пайплайн с зависимостями

### [Phase 1: RSS Discovery](phases/phase1_rss_discovery.md)
- Сканирование 26 источников новостей (25 RSS + Google Alerts)
- Фильтрация по дате и релевантности
- Сохранение новых статей со статусом `content_status = 'pending'`
- **Команда**: `python core/main.py --rss-discover`

### [Phase 2: Content Parsing](phases/phase2_content_parsing.md)
- Извлечение контента через Firecrawl Extract API (строго по 1 статье)
- Сохранение полного контента, summary, тегов
- Обновление статуса на `content_status = 'parsed'`
- **Установка media_status**: `'processing'` (если есть медиа) или `'ready'` (если нет медиа)
- **Команда**: `python core/main.py --parse-pending`

### [Phase 3: Media Processing](phases/phase3_media_processing.md)
- Скачивание изображений через wget с браузерными заголовками
- Валидация размеров (≥300×300px, 3КБ-2МБ) 
- **Без retry логики** - каждый файл обрабатывается только один раз
- Статусы медиа: `'pending'` → `'completed'` или `'failed'`
- **Автоматическое обновление**: `media_status = 'ready'` когда все медиа обработано
- **Команда**: `python core/main.py --media-only`

### [Phase 4: WordPress Preparation](phases/phase4_wordpress_preparation.md)
- ⚠️ **Зависимость**: запускается только для статей с `media_status = 'ready'`
- Перевод на русский через DeepSeek Chat API
- SEO-оптимизация (Yoast совместимость)
- Категоризация и тегирование
- Сохранение в таблицу wordpress_articles
- **Команда**: `python core/main.py --wordpress-prepare --limit 10`

### [Phase 5: WordPress Publishing](phases/phase5_wordpress_publishing.md)
- Создание постов в WordPress (draft статус)
- Загрузка медиафайлов с переводом только alt_text
- Установка featured image (первое изображение)
- **Команда**: `python core/main.py --wordpress-publish --limit 5`

## 🚀 Полный цикл
```bash
# Фазы 1-3: RSS → Parsing → Media
python core/main.py --rss-full

# Фазы 4-5: WordPress подготовка и публикация
python core/main.py --wordpress-prepare --limit 10
python core/main.py --wordpress-publish --limit 5
```

## 📊 Мониторинг
```bash
cd monitoring && ./start_monitoring.sh
# Дашборд доступен на http://localhost:8001
```

## 🏗️ Архитектура
- **База данных**: SQLite с полем `media_status` для управления зависимостями
- **API**: Firecrawl Extract API (только), DeepSeek Chat для перевода
- **Медиа**: wget с браузерными заголовками (не Playwright API)
- **WordPress**: REST API интеграция с Yoast SEO
- **Контроль зависимостей**: автоматическое управление статусами между фазами

## 📁 Структура проекта
```
ainews-clean/
├── core/           # Основная логика
├── services/       # Сервисы для каждой фазы
├── monitoring/     # Веб-дашборд
├── data/          # БД и конфигурация
├── docs/          # Документация
│   └── phases/    # Документация по фазам
└── agents/        # AI агенты для разработки
```

## 🔧 Конфигурация
- [Основная документация](../README.md)
- [Архитектура системы](architecture.md)
- [База данных](DATABASE_SCHEMA.md)
- [WordPress настройка](wordpress_setup.md)
- [Решение проблем](TROUBLESHOOTING.md)

## 💡 Ключевые особенности
- **Строгие зависимости**: Phase 4 запускается только после завершения Phase 3
- **Неагрессивный режим**: последовательная обработка (1 файл одновременно)
- **Без retry логики**: каждый медиафайл обрабатывается только один раз
- **Автоматические статусы**: `media_status` обновляется автоматически
- **Умная валидация**: фильтрация некачественного контента (≥300×300px)
- **SEO-ready**: полная поддержка Yoast SEO
- **Медиа обработка**: только alt_text переводится
- **Отказоустойчивость**: graceful degradation на каждом этапе

## 📊 Статусы и зависимости

### Статусы content_status:
- `pending` → `parsed` → `published`

### Статусы media_status:
- `pending` - медиа еще не обрабатывалось
- `processing` - медиафайлы скачиваются
- `ready` - готово к Phase 4

### Статусы media_files:
- `pending` → `completed` или `failed`

### Правила зависимостей:
- **Phase 2 → Phase 3**: автоматически (если есть медиа)
- **Phase 3 → Phase 4**: только при `media_status = 'ready'`
- **Phase 4 → Phase 5**: только при наличии записи в wordpress_articles