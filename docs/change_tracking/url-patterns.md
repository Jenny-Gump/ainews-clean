# URL Patterns System - Change Tracking

**Файл**: `change_tracking/url_extractor.py:32-125`  
**Назначение**: Система паттернов для фильтрации и валидации URL статей

## 📋 Обзор

URL Patterns System — это ключевой компонент URLExtractor, который определяет какие URL считаются релевантными статьями, а какие должны быть исключены. Система использует регулярные выражения и доменно-специфичные правила для точной фильтрации.

## 🎯 Основные компоненты

### 1. Domain Patterns (`domain_patterns`)
**Местоположение**: `url_extractor.py:34-125`

Карта доменов и разрешенных путей для извлечения URL:

```python
self.domain_patterns = {
    # AI Companies
    'openai.com': [r'/blog/', r'/news/'],
    'anthropic.com': [r'/news/', r'/research/'],
    'mistral.ai': [r'/news/[^/]+'],
    'cohere.com': [r'/blog/[^/]+', r'/research/[^/]+'],
    
    # Tech Giants
    'blog.google': [r'/technology/ai/'],
    'research.google': [r'/blog/'],
    'deepmind.google': [r'/blog/', r'/discover/'],
    
    # Платформы
    'huggingface.co': [r'/blog/', r'/papers/'],
    'databricks.com': [r'/blog/'],
    'scale.com': [r'/blog/[^/]+'],
    
    # Специфичные пути
    'writer.com': [r'/engineering/[^/]+'],  # НЕ /blog/!
    'pathai.com': [r'/news/'],
    'perplexity.ai': [r'/hub/'],
}
```

### 2. Exclude Patterns (`exclude_patterns`)
**Местоположение**: `url_extractor.py:127-228`

Паттерны для исключения нерелевантных URL:

```python
self.exclude_patterns = [
    # Технические URL
    r'/_next/',      # Next.js ресурсы
    r'/people/',     # Страницы авторов
    r'/topics/',     # Категории
    
    # Файлы и медиа
    r'\\.jpg$', r'\\.png$', r'\\.gif$',
    r'\\.css$', r'\\.js$', r'\\.pdf$',
    
    # Социальные сети
    r'facebook\\.com', r'twitter\\.com', r'linkedin\\.com',
    
    # Служебные страницы
    r'/contact', r'/about', r'/careers', r'/pricing'
]
```

### 3. Escape Sources (`escape_sources`)  
**Местоположение**: `url_extractor.py:260-265`

Список доменов, чей markdown содержит escape-последовательности `\\\\\\\\`:

```python
escape_sources = [
    'deepmind.google', 'new.abb.com', 'scale.com', 'stability.ai', 
    'waymo.com', 'c3.ai', 'crusoe.ai', 'cursor.com',
    'databricks.com', 'research.google', 'instabase.com', 
    'kinovarobotics.com', 'kuka.com', 'manus.im',
    'openevidence.com', 'huggingface.co', 'pathai.com', 
    'www.perplexity.ai', 'soundhound.com', 'uizard.io', 'writer.com'
]
```

## 🔧 Алгоритм фильтрации

### Функция `_is_article_url()`
**Местоположение**: `url_extractor.py:416-475`

```python
def _is_article_url(self, url: str, source_page_url: str) -> bool:
    # 1. Исключить сам исходный URL
    if url == source_page_url:
        return False
        
    # 2. Проверить exclude_patterns
    for pattern in self.exclude_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return False
    
    # 3. Проверить домен
    if not (url_domain == source_domain or url_domain.endswith('.' + source_domain)):
        return False
        
    # 4. URL должен быть длиннее базовой страницы
    if len(url_path) <= len(source_path):
        return False
        
    # 5. НОВАЯ ЛОГИКА: Domain patterns
    if source_domain in self.domain_patterns:
        allowed_patterns = self.domain_patterns[source_domain]
        for pattern in allowed_patterns:
            if re.search(pattern, url_path, re.IGNORECASE):
                return True
        return False  # Если не совпал ни один паттерн
        
    # 6. Для неизвестных доменов - общие паттерны
    news_patterns = [r'/news/', r'/blog/', r'/2024/', r'/2025/']
    return any(re.search(p, url, re.IGNORECASE) for p in news_patterns)
```

## 🎯 Примеры работы

### Успешные совпадения
```
✅ https://openai.com/blog/gpt-4-turbo
   domain_patterns['openai.com'] = [r'/blog/'] → MATCH

✅ https://writer.com/engineering/ai-agents  
   domain_patterns['writer.com'] = [r'/engineering/'] → MATCH

✅ https://huggingface.co/blog/transformers-4-30
   domain_patterns['huggingface.co'] = [r'/blog/'] → MATCH
```

### Исключенные URL
```
❌ https://openai.com/about
   exclude_patterns = [r'/about'] → EXCLUDED

❌ https://blog.google/image.jpg
   exclude_patterns = [r'\\.jpg$'] → EXCLUDED

❌ https://scale.com/_next/static/css/main.css
   exclude_patterns = [r'/_next/'] → EXCLUDED
```

### Escape-последовательности
```
# Источники с \\\\\\\ в markdown:
🔧 deepmind.google → текст\\\\\\\\дата](url)
🔧 stability.ai   → заголовок\\\\\\\\автор](url)  
🔧 huggingface.co → title\\\\\\\\by author](url)
```

## 📊 Статистика паттернов

**По состоянию на 11.08.2025:**

| Тип паттерна | Источников | Примеры |
|-------------|-----------|---------|
| **domain_patterns** | 25 | openai, google, huggingface |
| **escape_sources** | 21 | deepmind, stability, crusoe |
| **exclude_patterns** | ∀ | Применяется ко всем источникам |
| **Без паттерна** | 1 | Используют общие news_patterns |

### Распределение по категориям

```python
# AI Companies (строгие паттерны)
'openai.com': [r'/blog/', r'/news/']
'anthropic.com': [r'/news/', r'/research/'] 
'mistral.ai': [r'/news/[^/]+']

# Tech Giants (корпоративная структура)  
'blog.google': [r'/technology/ai/']
'research.google': [r'/blog/']
'news.microsoft.com': [r'/source/topics/ai/']

# Robotics (специфичные пути)
'waymo.com': [r'/blog/\\d{4}/\\d{2}/']  # /blog/2024/08/
'kuka.com': [r'/company/press/news/\\d{4}/\\d{2}/[^/]+']
'kinovarobotics.com': [r'/p/[^/]+']  # /p/article-title
```

## 🛠️ Настройка новых источников

### Шаг 1: Анализ структуры URL
```python
# Пример для нового источника "example.com"
URLs из разметки:
- https://example.com/blog/ai-research-2024
- https://example.com/blog/machine-learning-advances  
- https://example.com/news/company-update

Исключить:
- https://example.com/about
- https://example.com/contact
```

### Шаг 2: Добавление паттерна
```python
# В url_extractor.py:domain_patterns
'example.com': [r'/blog/[^/]+', r'/news/[^/]+']
```

### Шаг 3: Проверка escape-sequences
```python
# Если markdown содержит \\\\\\\\:
escape_sources = [
    # ... existing sources
    'example.com'  # Добавить сюда
]
```

### Шаг 4: Тестирование
```python
from change_tracking.url_extractor import URLExtractor
extractor = URLExtractor()
urls = extractor.extract_urls_from_content(markdown, 'https://example.com/blog')
print(f"Найдено {len(urls)} URL")
```

## 🚨 Распространенные проблемы

### 1. Неправильный domain_pattern
**Симптом**: 0 URL извлекается, но ссылки есть в markdown
```python
# ❌ Неправильно:
'writer.com': [r'/blog/[^/]+']  # URL имеют /engineering/

# ✅ Правильно:  
'writer.com': [r'/engineering/[^/]+']
```

### 2. Слишком строгий паттерн
**Симптом**: Пропускаются релевантные URL
```python
# ❌ Слишком строго:
'pathai.com': [r'/news/[^/]+$']  # Не работает для /news/subfolder/

# ✅ Правильно:
'pathai.com': [r'/news/']  # Ловит всё в /news/
```

### 3. Пропущены escape-sequences
**Симптом**: 0 URL при наличии ссылок с `\\\\\\\\` в markdown
```python
# ✅ Решение:
escape_sources = [..., 'domain.com']
```

## 📈 Метрики эффективности

### До оптимизации (07.08.2025)
- **27 источников работали** (55%)
- **280 URL** в базе
- Множество источников возвращали 0 URL

### После оптимизации (11.08.2025)  
- **47 источников работают** (100%)
- **985+ URL** в базе
- Каждый источник извлекает минимум 6+ URL

### Топ источники по URL
1. **kuka**: 111 URL (escape_sources + domain_patterns)
2. **fanuc**: 109 URL (domain_patterns)  
3. **nscale**: 60 URL (общие паттерны)
4. **perplexity**: 57 URL (смена URL + escape_sources)
5. **crusoe**: 48 URL (escape_sources)

---

**🔗 См. также:**
- [Source Mapping](source-mapping.md) — Конфигурация источников
- [Escape Processing](escape-processing.md) — Обработка escape-последовательностей  
- [Processing Flow](../FLOW.md#url-extraction) — Процесс извлечения URL