# AI News Parser Clean

🤖 **Автоматизированная система сбора и публикации новостей об искусственном интеллекте**

## 🎯 О проекте

AI News Parser - это полностью автоматизированная система, которая:
- 📡 Собирает новости из 26 источников об ИИ
- 🔍 Извлекает полный контент через Firecrawl Extract API
- 🌐 Переводит на русский язык через DeepSeek Chat
- 📝 Публикует в WordPress с SEO-оптимизацией
- 🖼️ Загружает изображения с переводом только alt-текста
- 📊 Мониторит процессы в реальном времени

**Сайт**: [ailynx.ru](https://ailynx.ru) - Новости ИИ на русском языке

## 🚀 Быстрый старт

```bash
# Клонирование и настройка
cd "/Users/skynet/Desktop/AI DEV/ainews-clean"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Настройка окружения
cp .env.example .env
# Добавьте API ключи в .env

# Запуск полного цикла
python core/main.py --rss-full            # Фазы 1-3
python core/main.py --wordpress-prepare   # Фаза 4
python core/main.py --wordpress-publish   # Фаза 5
```

## 📚 Документация

### 🔄 Пайплайн обработки
- **[Обзор пайплайна](docs/README.md)** - Детальное описание всех 5 фаз
- **[Архитектура системы](docs/architecture.md)** - Технический дизайн
- **[База данных](docs/DATABASE_SCHEMA.md)** - Структура таблиц

### 🛠️ Компоненты системы
- **[Логирование](app_logging/README.md)** - Централизованная система логов
- **[Мониторинг](monitoring/README.md)** - Веб-дашборд и метрики
- **[API документация](docs/API/)** - Интеграции с внешними API

### 🔧 Настройка и использование
- **[WordPress Setup](docs/wordpress_setup.md)** - Настройка WordPress
- **[Решение проблем](docs/TROUBLESHOOTING.md)** - Частые проблемы

### 👥 Для разработчиков
- **[CLAUDE.md](CLAUDE.md)** - Инструкции для AI-ассистентов
- **[Агенты](agents/)** - Специализированные AI агенты

## 🏗️ Архитектура

```
ainews-clean/
├── core/           # Основная логика приложения
├── services/       # Сервисы для каждой фазы
├── monitoring/     # Веб-дашборд [подробнее](monitoring/README.md)
├── app_logging/    # Система логирования [подробнее](app_logging/README.md)
├── data/          # Базы данных и медиафайлы
├── docs/          # Документация [подробнее](docs/README.md)
├── agents/        # AI агенты для разработки
└── scripts/       # Утилиты и скрипты
```

## 💡 Ключевые особенности

- **🔄 5-фазный пайплайн**: RSS → Парсинг → Медиа → Подготовка → Публикация
- **📄 Извлечение контента**: Firecrawl Extract API для полного контента
- **🌍 Автоперевод**: Адаптация контента для русскоязычной аудитории
- **📈 SEO-ready**: Полная поддержка Yoast SEO
- **🖼️ Умная валидация**: Фильтрация изображений (≥300×300px, 3KB-2MB)
- **🏷️ Метаданные изображений**: Только alt-текст и title (без caption/description)
- **📊 Мониторинг**: Реальное время через WebSocket
- **🛡️ Отказоустойчивость**: Graceful degradation на каждом этапе

## 🔧 Конфигурация

### Необходимые API ключи (.env)
```env
FIRECRAWL_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here
WORDPRESS_API_URL=https://ailynx.ru/wp-json/wp/v2
WORDPRESS_USERNAME=admin
WORDPRESS_APP_PASSWORD=your_app_password
```

### Команды управления
```bash
# Информация о системе
python core/main.py --list-sources  # Список источников
python core/main.py --stats         # Статистика

# Мониторинг
cd monitoring && ./start_monitoring.sh
# Открыть http://localhost:8001
```

## 📊 Статус системы

- **Источники**: 26 (25 RSS + Google Alerts)
- **База данных**: SQLite с оптимизацией
- **API**: Firecrawl Extract, DeepSeek Chat
- **Мониторинг**: FastAPI + WebSocket
- **Логирование**: Структурированные JSON логи

## 🤝 Вклад в проект

Проект использует систему AI агентов для разработки. См. [agents/AGENT_WORKFLOW.md](agents/AGENT_WORKFLOW.md) для деталей.

## 📝 Лицензия

Проект разработан для ailynx.ru

---

**Версия**: 1.2.0 | **Последнее обновление**: Август 2025