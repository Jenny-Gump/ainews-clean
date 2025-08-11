# Troubleshooting - AI News Parser Clean

**Обновлено**: 11 августа 2025 - восстановленная версия

## 🚨 Частые проблемы и решения

### 1. Pipeline не запускается / зависает

#### Проблема: Pipeline висит без результата
```bash
# Симптомы:
- Кнопка "Start Pipeline" не работает
- Логи не обновляются
- Процесс не завершается
```

#### ✅ Решения:
```bash
# 1. Проверить статус
python core/main.py --stats

# 2. Запустить ТОЛЬКО из dashboard
# НЕ запускать из терминала напрямую!
# Открыть http://localhost:8001 и использовать кнопку

# 3. Проверить pending статьи
python core/main.py --list-sources

# 4. Добавить тестовую статью
python -c "
import sqlite3
conn = sqlite3.connect('data/ainews.db')
conn.execute('''INSERT INTO articles (
    article_id, source_id, url, title, content_status
) VALUES (
    'test_001', 'test_source', 
    'http://example.com/test', 'Test Article', 'pending'
)''')
conn.commit()
conn.close()
print('Test article added')
"
```

### 2. Нет pending статей

#### Проблема: RSS discovery не находит статьи
```bash
# Симптомы:
python core/main.py --stats
# Показывает: pending: 0
```

#### ✅ Решения:
```bash
# 1. Запустить RSS discovery
python core/main.py --rss-discover

# 2. Проверить источники
python core/main.py --list-sources

# 3. Если источники неактивны - добавить тестовый
python -c "
import sqlite3
conn = sqlite3.connect('data/ainews.db')
conn.execute('''INSERT OR REPLACE INTO sources (
    source_id, name, rss_url, is_active
) VALUES (
    'test_rss', 'Test RSS', 
    'https://feeds.feedburner.com/oreilly/radar', 1
)''')
conn.commit()
conn.close()
print('Test source added')
"

# 4. Повторить RSS discovery
python core/main.py --rss-discover
```

### 3. Firecrawl API ошибки

#### Проблема: Timeout или 403 ошибки от Firecrawl
```bash
# Симптомы:
ERROR: Firecrawl request failed: Request timeout
ERROR: Firecrawl request failed: 403 Forbidden
```

#### ✅ Решения:
```bash
# 1. Проверить API ключ
echo $FIRECRAWL_API_KEY
# Должен быть установлен в .env файле

# 2. Использовать тестовый URL
python -c "
import sqlite3
conn = sqlite3.connect('data/ainews.db')
conn.execute('''UPDATE articles 
SET url = 'http://example.com/test-article' 
WHERE content_status = 'pending' LIMIT 1''')
conn.commit()
conn.close()
print('URL updated to test URL')
"

# 3. Увеличить timeout в config.py
# FIRECRAWL_TIMEOUT = 360  # 6 минут
```

### 4. DeepSeek/OpenAI API проблемы

#### Проблема: LLM API недоступны или лимиты исчерпаны
```bash
# Симптомы:
ERROR: DeepSeek API failed
ERROR: OpenAI API rate limit exceeded
```

#### ✅ Решения:
```bash
# 1. Проверить API ключи
echo $DEEPSEEK_API_KEY
echo $OPENAI_API_KEY

# 2. Проверить баланс в личных кабинетах
# DeepSeek: https://platform.deepseek.com/
# OpenAI: https://platform.openai.com/

# 3. Временно отключить LLM обработку
# Пропустить статьи с failed статусом:
python -c "
import sqlite3
conn = sqlite3.connect('data/ainews.db')
conn.execute('UPDATE articles SET content_status = \"failed\" WHERE content_status = \"pending\"')
conn.commit()
print('Pending articles marked as failed')
"
```

### 5. WordPress публикация не работает

#### Проблема: Статьи не публикуются на WordPress
```bash
# Симптомы:
- Статьи переведены, но не опубликованы
- Ошибки авторизации WordPress
```

#### ✅ Решения:
```bash
# 1. Проверить WordPress доступность
curl -I https://ailynx.ru/wp-json/wp/v2/posts

# 2. Проверить авторизацию
curl -u "admin:tE85 PFT4 Ghq9 nl26 nQlt gBnG" \
  "https://ailynx.ru/wp-json/wp/v2/posts?per_page=1"

# 3. Проверить переведенные статьи
python -c "
import sqlite3
conn = sqlite3.connect('data/ainews.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM wordpress_articles WHERE translation_status = \"translated\"')
count = cursor.fetchone()[0]
print(f'Translated articles ready: {count}')
"
```

### 6. База данных заблокирована

#### Проблема: SQLite database is locked
```bash
# Симптомы:
sqlite3.OperationalError: database is locked
```

#### ✅ Решения:
```bash
# 1. Найти процессы, использующие БД
lsof data/ainews.db
# Завершить зависшие процессы

# 2. Проверить целостность БД
python -c "
import sqlite3
try:
    conn = sqlite3.connect('data/ainews.db')
    conn.execute('PRAGMA integrity_check')
    result = conn.fetchone()
    print(f'DB integrity: {result[0]}')
    conn.close()
except Exception as e:
    print(f'DB error: {e}')
"

# 3. В крайнем случае - перезапустить мониторинг
pkill -f "monitoring"
cd monitoring && ./start_monitoring.sh
```

### 7. Change Tracking проблемы

#### Проблема: Change tracking не работает
```bash
# Симптомы:
- Команды --change-tracking не выполняются
- Нет новых tracked_articles
```

#### ✅ Решения:
```bash
# 1. Проверить таблицу tracked_articles
python -c "
import sqlite3
conn = sqlite3.connect('data/ainews.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM tracked_articles')
count = cursor.fetchone()[0]
print(f'Tracked articles: {count}')
"

# 2. Тест с одним источником
python core/main.py --change-tracking --scan --limit 1

# 3. Проверить Firecrawl API для changeTracking
# Может требовать больше кредитов
```

### 8. Monitoring dashboard не запускается

#### Проблема: Dashboard недоступен на localhost:8001
```bash
# Симптомы:
- Порт 8001 недоступен
- Ошибки при запуске ./start_monitoring.sh
```

#### ✅ Решения:
```bash
# 1. Проверить порт
lsof -i :8001
# Если занят - завершить процесс

# 2. Запустить мониторинг
cd monitoring
./start_monitoring.sh

# 3. Проверить логи
tail -f monitoring.log

# 4. Альтернативный запуск
cd monitoring
python main.py
```

### 9. External prompts не загружаются

#### Проблема: Ошибки при загрузке prompts из папки prompts/
```bash
# Симптомы:
FileNotFoundError: prompts/content_cleaner.txt
```

#### ✅ Решения:
```bash
# 1. Проверить наличие файлов промптов
ls -la prompts/
# Должны быть: content_cleaner.txt, article_translator.txt, etc.

# 2. Проверить права доступа
chmod 644 prompts/*.txt

# 3. Временно использовать резервные промпты в коде
# Если файлы отсутствуют, система должна использовать default промпты
```

## 🛠️ Команды диагностики

### Проверка состояния системы
```bash
# Основная статистика
python core/main.py --stats

# Статус источников
python core/main.py --list-sources

# Проверка БД
python -c "
import sqlite3
conn = sqlite3.connect('data/ainews.db')
tables = conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall()
print('Tables:', [t[0] for t in tables])
"

# Проверка pending статей
python -c "
import sqlite3
conn = sqlite3.connect('data/ainews.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM articles WHERE content_status = \"pending\"')
pending = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM articles WHERE content_status = \"failed\"')  
failed = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM articles WHERE content_status = \"parsed\"')
parsed = cursor.fetchone()[0]
print(f'Pending: {pending}, Failed: {failed}, Parsed: {parsed}')
"
```

### Сброс системы для тестирования
```bash
# Очистка failed статей (превратить в pending)
python -c "
import sqlite3
conn = sqlite3.connect('data/ainews.db')
conn.execute('UPDATE articles SET content_status = \"pending\" WHERE content_status = \"failed\"')
affected = conn.total_changes
conn.commit()
print(f'Reset {affected} articles to pending')
"

# Добавление тестового контента
python -c "
import sqlite3
conn = sqlite3.connect('data/ainews.db')
conn.execute('''INSERT OR REPLACE INTO articles (
    article_id, source_id, url, title, content, 
    content_status, media_status
) VALUES (
    'test_debug', 'test_source', 
    'http://example.com/debug', 'Debug Test Article',
    'This is test content for debugging purposes.', 
    'parsed', 'completed'
)''')
conn.commit()
print('Debug article added')
"
```

## 🆘 Экстренное восстановление

### Если система полностью не работает:

```bash
# 1. Проверить основные файлы
ls -la core/main.py
ls -la data/ainews.db
ls -la venv/bin/activate

# 2. Переустановить зависимости
source venv/bin/activate
pip install -r requirements.txt

# 3. Проверить переменные окружения
cat .env | head -5

# 4. Создать минимальную тестовую статью
python -c "
import sqlite3
import os
os.makedirs('data', exist_ok=True)
conn = sqlite3.connect('data/ainews.db')
conn.execute('''CREATE TABLE IF NOT EXISTS articles (
    article_id TEXT PRIMARY KEY,
    source_id TEXT,
    url TEXT,
    title TEXT,
    content TEXT,
    content_status TEXT DEFAULT 'pending',
    media_status TEXT DEFAULT 'pending'
)''')
conn.execute('''INSERT OR REPLACE INTO articles VALUES (
    'emergency_test', 'test_source', 'http://example.com/test',
    'Emergency Test', 'Test content', 'pending', 'pending'
)''')
conn.commit()
print('Emergency test article created')
"

# 5. Запустить простой тест
python core/main.py --stats
```

## 📞 Получение помощи

### Сбор информации для поддержки:
```bash
# Создать диагностический отчет
cat > debug_report.txt << EOF
=== AI News Parser Clean Debug Report ===
Date: $(date)
Python: $(python --version)
Working Directory: $(pwd)

=== System Status ===
$(python core/main.py --stats 2>&1)

=== Database Tables ===
$(python -c "
import sqlite3
conn = sqlite3.connect('data/ainews.db')
tables = conn.execute('SELECT name FROM sqlite_master WHERE type=\'table\'').fetchall()
for table in tables:
    count = conn.execute(f'SELECT COUNT(*) FROM {table[0]}').fetchone()[0]
    print(f'{table[0]}: {count} records')
" 2>&1)

=== Recent Errors ===
$(tail -20 app_logging/*.log 2>/dev/null || echo "No log files found")

=== Environment ===
FIRECRAWL_API_KEY: $(echo $FIRECRAWL_API_KEY | cut -c1-10)...
DEEPSEEK_API_KEY: $(echo $DEEPSEEK_API_KEY | cut -c1-10)...
OPENAI_API_KEY: $(echo $OPENAI_API_KEY | cut -c1-10)...
EOF

echo "Debug report saved to debug_report.txt"
```

При возникновении проблем:
1. Создайте диагностический отчет командой выше
2. Опишите что делали перед ошибкой
3. Приложите точный текст ошибки
4. Укажите используемую ОС и версию Python