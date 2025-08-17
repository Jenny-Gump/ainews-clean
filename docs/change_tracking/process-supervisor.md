# Process Supervisor Documentation

**Версия**: 1.0  
**Статус**: Production Ready  
**Создан**: 17 августа 2025  
**Цель**: Изоляция источников и предотвращение зависаний

## 📋 Обзор

Process Supervisor — это новый компонент системы AI News Parser, созданный для решения проблемы постоянных зависаний при обработке RSS и Change Tracking источников. Каждый источник запускается в изолированном процессе с жёстким таймаутом.

## 🎯 Проблема, которую решает

### До Process Supervisor:
- Система могла зависнуть навсегда на одном источнике
- Многослойные таймауты конфликтовали между собой
- Retry логика усугубляла проблему (до 3 попыток с exponential backoff)
- Процессы требовали ручного kill -9

### После Process Supervisor:
- ✅ Гарантия: никогда не зависнет >60 секунд
- ✅ Каждый источник в изолированном процессе
- ✅ Ошибка = skip и продолжить
- ✅ Полная статистика: successful/skipped/killed

## 🏗️ Архитектура

```
┌─────────────────────────────────────┐
│      Process Supervisor              │
│  (timeout_per_source = 60s)          │
└──────────┬──────────────────────────┘
           │
           ├─── subprocess.run(timeout=60)
           │
    ┌──────▼──────┐     ┌──────────────┐
    │  RSS Source │     │ Change Track │
    │   Process   │     │   Process    │
    │  (isolated) │     │  (isolated)  │
    └─────────────┘     └──────────────┘
           │                    │
     ✅ Success            ⏱️ Timeout → SIGKILL
     ❌ Error → Skip       ✅ Success
```

## 🔧 Использование

### Базовое использование

```python
from core.process_supervisor import ProcessSupervisor

# Создаём супервайзер с таймаутом 60 секунд
supervisor = ProcessSupervisor(timeout_per_source=60)

# Обработка RSS источников
result = supervisor.run_rss_source('techcrunch')
# Returns: {'status': 'success'|'killed'|'error', 'articles': N}

# Обработка Change Tracking
result = supervisor.run_change_tracking_source('https://openai.com/blog')
# Returns: {'status': 'new'|'changed'|'unchanged'|'killed'|'error'}

# Обработка всех RSS источников
results = supervisor.run_all_rss_sources()
# Returns: {'stats': {...}, 'results': [...]}
```

### CLI интерфейс

```bash
# RSS Discovery с супервайзером
python core/process_supervisor.py --mode rss --timeout 60

# Change Tracking конкретного URL
python core/process_supervisor.py --mode change-tracking --url https://example.com --timeout 30

# Обработка конкретных RSS источников
python core/process_supervisor.py --mode rss --sources techcrunch mit_news --timeout 45
```

## 📊 Статистика

Process Supervisor собирает следующую статистику:

- **processed**: Общее количество обработанных источников
- **successful**: Успешно обработанные источники
- **skipped**: Пропущенные из-за ошибок
- **killed**: Убитые по таймауту (SIGKILL)
- **errors**: Неожиданные ошибки

### Пример статистики
```python
{
    'processed': 30,
    'successful': 27,
    'skipped': 1,
    'killed': 2,  # Это те, что зависли и были убиты
    'errors': 0
}
```

## ⚙️ Конфигурация

### Таймауты по умолчанию
- **RSS Discovery**: 60 секунд на источник
- **Change Tracking**: 60 секунд на страницу
- **Можно настроить**: от 10 до 300 секунд

### Рекомендуемые настройки
```python
# Для быстрых RSS источников
supervisor = ProcessSupervisor(timeout_per_source=30)

# Для медленных Change Tracking страниц
supervisor = ProcessSupervisor(timeout_per_source=90)

# Production настройки (баланс)
supervisor = ProcessSupervisor(timeout_per_source=60)
```

## 🔍 Диагностика

### Логирование
```
✅ techcrunch processed in 2.1s - 5 articles
⏱️ slow_source KILLED after 60s timeout
❌ broken_source failed: Connection error
⚠️ skipped_source - skipped: Invalid RSS
```

### Проблемные источники
Если источник постоянно попадает в категорию "killed":
1. Проверить доступность источника вручную
2. Увеличить таймаут для этого источника
3. Рассмотреть удаление источника из списка

## 🚀 Преимущества

1. **Гарантия от зависаний** - жёсткий таймаут с SIGKILL
2. **Изоляция процессов** - один источник не влияет на другие
3. **Простота** - никаких сложных retry и recovery
4. **Прозрачность** - ясная статистика и логи
5. **Масштабируемость** - легко параллелизовать

## 📈 Результаты внедрения

**До внедрения:**
- Зависания до бесконечности
- Ручное вмешательство каждый день
- Непредсказуемое время обработки

**После внедрения:**
- 0 зависаний >60 секунд
- Полностью автономная работа
- Предсказуемое время: макс 60 сек × количество источников

## 🔗 Связанные компоненты

- **RSS Discovery** (`services/rss_discovery.py`) - упрощён для работы с супервайзером
- **Change Tracking** (`change_tracking/monitor.py`) - убраны retry для совместимости
- **Firecrawl Client** (`services/firecrawl_client.py`) - уменьшены таймауты

## 📝 Философия MVP

Process Supervisor следует принципу MVP (Minimum Viable Product):
- **Минимум кода** - один файл, простая логика
- **Максимум эффекта** - полное решение проблемы зависаний
- **Никакой магии** - subprocess + timeout + SIGKILL
- **Fail fast** - ошибка = skip, не пытаемся исправить

---

**📧 Поддержка:** См. [bug-fixes.md](bug-fixes.md) для истории исправлений