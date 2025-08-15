# Documentation Index - AI News Parser Clean

**Обновлено**: 11 августа 2025 - оптимизированная документация

## 📚 Обзор документации

Данная папка содержит всю техническую документацию проекта AI News Parser Clean. Документация оптимизирована и сокращена с ~20 файлов до 10 актуальных документов.

## 🗂️ Структура документации

### 🏗️ Архитектура и обзор системы
- **[architecture.md](architecture.md)** - Полный обзор архитектуры системы
- **[PIPELINE_FLOW_DETAILED.md](PIPELINE_FLOW_DETAILED.md)** - Детальное описание работы пайплайна

### 💾 База данных
- **[DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)** - Полная схема всех таблиц БД

### 🔧 Настройка и конфигурация  
- **[SOURCES.md](SOURCES.md)** - Список всех источников новостей (29 RSS + 47 tracking)
- **[llm-models.md](llm-models.md)** - Документация по LLM моделям и промптам

### 📊 Специализированные модули
- **[media-pipeline.md](media-pipeline.md)** - Подробное руководство по обработке медиа
- **[tracking-system.md](tracking-system.md)** - Change Tracking Module для мониторинга изменений
- **[last-parsed-system.md](last-parsed-system.md)** - Система глобальных меток времени

### 🌐 API и интеграции
- **[API/API_REFERENCE.md](API/API_REFERENCE.md)** - REST API endpoints для мониторинга
- **[API/yoast_seo_integration.md](API/yoast_seo_integration.md)** - Интеграция с Yoast SEO через WordPress API
- **[MCP_SERVERS.md](MCP_SERVERS.md)** - MCP серверы для Claude (Supabase, Playwright, etc.)

### 🛠️ Диагностика и решение проблем
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Руководство по решению частых проблем

## 🎯 Быстрый старт

### Для разработчиков:
1. **Начать с**: [architecture.md](architecture.md) - понять общую структуру
2. **Изучить пайплайн**: [PIPELINE_FLOW_DETAILED.md](PIPELINE_FLOW_DETAILED.md)
3. **Настроить источники**: [SOURCES.md](SOURCES.md)
4. **При проблемах**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### Для администраторов:
1. **API мониторинга**: [API/API_REFERENCE.md](API/API_REFERENCE.md)
2. **WordPress интеграция**: [API/yoast_seo_integration.md](API/yoast_seo_integration.md)
3. **Схема БД**: [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)

### Для специалистов:
- **Медиа-обработка**: [media-pipeline.md](media-pipeline.md)
- **Change tracking**: [tracking-system.md](tracking-system.md)
- **LLM настройки**: [llm-models.md](llm-models.md)

## ⚡ Основные команды

```bash
cd "Desktop/AI DEV/ainews-clean"
source venv/bin/activate

# Базовые операции
python core/main.py --rss-discover      # RSS discovery
python core/main.py --single-pipeline   # Обработать 1 статью
python core/main.py --stats             # Статистика

# Change tracking
python core/main.py --change-tracking --scan --limit 5

# Мониторинг
cd monitoring && ./start_monitoring.sh  # Dashboard на http://localhost:8001
```

## 🔗 Связанные ресурсы

### Внешние документы:
- **Основной README**: `/Users/skynet/Desktop/AI DEV/ainews-clean/README.md`
- **CLAUDE.md**: `/Users/skynet/Desktop/AI DEV/ainews-clean/CLAUDE.md`
- **Monitoring README**: `/Users/skynet/Desktop/AI DEV/ainews-clean/monitoring/README.md`

### Конфигурационные файлы:
- **External Prompts**: `/Users/skynet/Desktop/AI DEV/ainews-clean/prompts/`
- **Agent Contexts**: `/Users/skynet/Desktop/AI DEV/ainews-clean/agents/`

## 📈 История изменений

### 11 августа 2025 - Оптимизация документации:
- ✅ Удалена папка `Архив/` (старая фазовая архитектура)
- ✅ Удалены дублирующие файлы: FIRECRAWL.md, yoast_examples.md
- ✅ Объединены tracking документы в один tracking-system.md
- ✅ Обновлен API_REFERENCE.md для восстановленной версии
- ✅ Создан актуальный TROUBLESHOOTING.md
- ✅ Сокращено с ~20 до 10 ключевых документов

### Архивированные документы:
Следующие документы были удалены как устаревшие:
- `Архив/PIPELINE_OVERVIEW.md` → заменен на PIPELINE_FLOW_DETAILED.md
- `Архив/phases/` → система перешла на single-pipeline
- `TRACKING_INTEGRATION.md` + `WEB_TRACKING_READY.md` → объединены в tracking-system.md
- `API/FIRECRAWL.md` + `FIRECRAWL_CLIENT_README.md` → информация интегрирована
- `API/wordpress_integration.md` → информация перенесена в другие документы

## 💡 Рекомендации по использованию

1. **Всегда начинать с architecture.md** для понимания системы
2. **Использовать TROUBLESHOOTING.md** при любых проблемах
3. **Документы актуальны** для восстановленной версии от 11 августа 2025
4. **При изменениях системы** - обновлять соответствующие документы
5. **Для глубокого понимания** - читать документы в порядке complexity: architecture → pipeline → database → specialists

## 🎯 Статус документации

**Статус**: ✅ Оптимизировано и актуально  
**Покрытие**: 100% ключевых компонентов системы  
**Дубликаты**: Устранены  
**Устаревшие файлы**: Удалены  
**Качество**: Высокое, соответствует коду

---

*Документация поддерживается в актуальном состоянии и отражает текущую архитектуру восстановленной системы AI News Parser Clean.*