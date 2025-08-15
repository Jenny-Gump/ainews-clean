# MCP Servers Documentation

## Обзор

AI News Parser использует несколько MCP (Model Context Protocol) серверов для различных операций. MCP серверы доступны только для Claude, система использует прямые API вызовы.

## Подключенные MCP серверы

### 1. **supabase** - Основная база данных
- **Назначение**: Доступ к основной БД системы
- **Project**: mtguynupyltlqiwhmilc
- **URL**: https://mtguynupyltlqiwhmilc.supabase.co
- **Использование**:
```bash
# Выполнить SQL запрос
claude mcp supabase execute_sql --query "SELECT COUNT(*) FROM articles"

# Список таблиц
claude mcp supabase list_tables

# Применить миграцию
claude mcp supabase apply_migration --name "add_index" --query "CREATE INDEX ..."
```

### 2. **ainews-sqlite** (Legacy, read-only)
- **Назначение**: Доступ к старой SQLite БД для миграции
- **Path**: /Users/skynet/Desktop/AI DEV/ainews-clean/data/ainews.db
- **Статус**: DISABLED - используется только для чтения старых данных
- **Использование**:
```bash
# Проверить старые данные
claude mcp ainews-sqlite query --sql "SELECT * FROM articles LIMIT 5"
```

### 3. **ainews-monitoring-db** 
- **Назначение**: База данных мониторинга
- **Path**: monitoring/data/monitoring.db
- **Использование**:
```bash
# Метрики системы
claude mcp ainews-monitoring-db query --sql "SELECT * FROM system_metrics ORDER BY timestamp DESC LIMIT 10"
```

### 4. **playwright** - Браузерная автоматизация
- **Назначение**: Тестирование веб-интерфейса, скриншоты
- **Использование**:
```bash
# Открыть страницу
claude mcp playwright browser_navigate --url "http://localhost:8001"

# Сделать скриншот
claude mcp playwright browser_take_screenshot --filename "dashboard.png"

# Кликнуть кнопку
claude mcp playwright browser_click --element "Start Pipeline" --ref "button#start"
```

### 5. **shadcn-ui** - UI компоненты
- **Назначение**: Получение кода UI компонентов для dashboard
- **Использование**:
```bash
# Список компонентов
claude mcp shadcn-ui list_components

# Получить компонент
claude mcp shadcn-ui get_component --componentName "button"
```

### 6. **context7** - Документация
- **Назначение**: Поиск документации библиотек
- **Использование**:
```bash
# Найти библиотеку
claude mcp context7 resolve-library-id --libraryName "supabase"

# Получить документацию
claude mcp context7 get-library-docs --context7CompatibleLibraryID "/supabase/supabase"
```

### 7. **gdrive** - Google Drive
- **Назначение**: Работа с Google Sheets для отчётов
- **Использование**:
```bash
# Поиск файлов
claude mcp gdrive gdrive_search --query "AI News Report"

# Чтение spreadsheet
claude mcp gdrive gsheets_read --spreadsheetId "abc123"
```

## Разница между MCP и прямым API

### MCP серверы (только для Claude):
- Используют протокол MCP
- Доступны через `claude mcp` команды
- Автоматическая авторизация
- Удобны для интерактивной работы

### Прямые API (для системы):
- Python клиенты: `supabase_client.py`
- REST API вызовы
- Требуют API ключи в .env
- Используются в production коде

## Конфигурация MCP

MCP серверы настроены локально для проекта:
```bash
# Список подключенных серверов
claude mcp list

# Добавить новый сервер
claude mcp add <name> "<command>" <args>

# Удалить сервер
claude mcp remove <name>
```

## Примеры использования

### Проверка статистики:
```bash
# Количество pending статей
claude mcp supabase execute_sql --query "SELECT COUNT(*) FROM articles WHERE content_status = 'pending'"

# Последние ошибки
claude mcp supabase execute_sql --query "SELECT article_id, content_error FROM articles WHERE content_status = 'failed' ORDER BY created_at DESC LIMIT 5"
```

### Мониторинг производительности:
```bash
# Метрики памяти
claude mcp ainews-monitoring-db query --sql "SELECT * FROM memory_metrics ORDER BY timestamp DESC LIMIT 10"

# Операции pipeline
claude mcp supabase execute_sql --query "SELECT * FROM pipeline_operations ORDER BY timestamp DESC LIMIT 20"
```

### Тестирование UI:
```bash
# Открыть dashboard
claude mcp playwright browser_navigate --url "http://localhost:8001"

# Проверить статус
claude mcp playwright browser_snapshot

# Нажать кнопку запуска
claude mcp playwright browser_click --element "Start Pipeline" --ref "button"
```

## Безопасность

- MCP серверы работают локально
- Нет внешнего доступа
- Credentials хранятся в системе Claude
- Production система не зависит от MCP