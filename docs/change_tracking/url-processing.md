# URL Processing & Source Configuration

**Версия**: 2.0  
**Последнее обновление**: 19 августа 2025  
**Модули**: `url_extractor.py`, `tracking_sources.json`

## 📋 Обзор
Комплексная система обработки URL и конфигурации источников, включающая паттерны фильтрации, обработку escape-последовательностей и маппинг источников.

---

## 🗺️ Source Mapping - Конфигурация источников

### Основная конфигурация
**Файл**: `data/tracking_sources.json`  
**Количество**: 66 источников (47 активных для Change Tracking)

### Структура источника
```json
{
  "source_id": "anthropic",
  "name": "Anthropic",
  "url": "https://www.anthropic.com/news",
  "rss_url": null,
  "type": "change_tracking",
  "category": "ai_companies",
  "priority": 1,
  "active": true
}
```

### Категории источников

| Категория | Количество | Примеры |
|-----------|------------|---------|
| **ai_companies** | 15 | Anthropic, OpenAI, Mistral, Cohere |
| **tech_giants** | 8 | Google Research, Microsoft, AWS |
| **platforms** | 10 | HuggingFace, Databricks, Scale |
| **robotics** | 12 | Waymo, ABB, Fanuc, Kuka |
| **healthcare** | 5 | Tempus, PathAI, OpenEvidence |
| **other** | 16 | Writer, Uizard, SoundHound |

### Топ источники по URL
1. **kuka**: 111 URL
2. **fanuc**: 109 URL  
3. **nscale**: 60 URL
4. **perplexity**: 57 URL
5. **crusoe**: 48 URL

---

## 🎯 URL Patterns System

### Domain Patterns
**Местоположение**: `url_extractor.py:34-125`

Карта доменов и разрешенных путей:

```python
domain_patterns = {
    # AI Companies - строгие паттерны
    'openai.com': [r'/blog/', r'/news/', r'/index/'],
    'anthropic.com': [r'/news/', r'/research/'],
    'mistral.ai': [r'/news/[^/]+'],
    
    # Tech Giants - корпоративная структура
    'blog.google': [r'/technology/ai/'],
    'research.google': [r'/blog/'],
    'deepmind.google': [r'/blog/', r'/discover/'],
    
    # Platforms - широкие паттерны
    'huggingface.co': [r'/blog/', r'/papers/'],
    'databricks.com': [r'/blog/'],
    
    # Robotics - специфичные форматы
    'waymo.com': [r'/blog/\d{4}/\d{2}/'],  # /blog/2024/08/
    'kuka.com': [r'/company/press/news/\d{4}/\d{2}/[^/]+'],
    
    # Специальные случаи
    'writer.com': [r'/engineering/[^/]+'],  # НЕ /blog/!
    'perplexity.ai': [r'/hub/']
}
```

### Exclude Patterns
Паттерны для исключения нерелевантных URL:

```python
exclude_patterns = [
    # Технические URL
    r'/_next/',      # Next.js ресурсы
    r'/people/',     # Страницы авторов
    r'/topics/',     # Категории
    
    # Медиа файлы
    r'\.jpg$', r'\.png$', r'\.gif$',
    r'\.css$', r'\.js$', r'\.pdf$',
    
    # Социальные сети
    r'facebook\.com', r'twitter\.com',
    
    # Служебные страницы
    r'/contact', r'/about', r'/careers'
]
```

---

## 🔧 Escape Processing - Обработка спецсимволов

### Проблема escape-последовательностей
21 источник возвращает markdown с escape-последовательностями вида `\\\\\\\\\\\\`:

```markdown
# Пример от deepmind.google:
[Introducing Gemma 2\\\\\\\\\\\\\\2024-08-01](https://deepmind.google/blog/gemma-2)
```

### Список проблемных источников
```python
escape_sources = [
    'deepmind.google', 'new.abb.com', 'scale.com', 
    'stability.ai', 'waymo.com', 'c3.ai', 'crusoe.ai',
    'cursor.com', 'databricks.com', 'research.google',
    'instabase.com', 'kinovarobotics.com', 'kuka.com',
    'manus.im', 'openevidence.com', 'huggingface.co',
    'pathai.com', 'www.perplexity.ai', 'soundhound.com',
    'uizard.io', 'writer.com'
]
```

### Решение - адаптивная обработка
```python
def extract_urls_from_content(self, content, source_page_url):
    domain = urlparse(source_page_url).netloc.replace('www.', '')
    
    # Применяем обработку escape только для известных источников
    if domain in self.escape_sources:
        # Агрессивная замена для escape источников
        content = re.sub(r'\\{2,}', '', content)
        
        # Специальный паттерн для таких источников
        pattern = r'\[([^\]]+?)\]\(([^)]+)\)'
    else:
        # Стандартный паттерн для обычных источников
        pattern = r'\[([^\]]+)\]\((https?://[^)]+)\)'
    
    # Извлечение URL
    matches = re.findall(pattern, content)
    return self._filter_urls(matches, source_page_url)
```

---

## 🔍 Алгоритм фильтрации URL

### Функция _is_article_url()
**Местоположение**: `url_extractor.py:416-475`

```python
def _is_article_url(self, url: str, source_page_url: str) -> bool:
    # 1. Исключить сам источник
    if url == source_page_url:
        return False
    
    # 2. Проверить exclude_patterns
    for pattern in self.exclude_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return False
    
    # 3. Проверить домен
    if not same_domain(url, source_page_url):
        return False
    
    # 4. URL должен быть длиннее базовой страницы
    if len(url_path) <= len(source_path):
        return False
    
    # 5. Проверить domain patterns
    if source_domain in self.domain_patterns:
        allowed_patterns = self.domain_patterns[source_domain]
        for pattern in allowed_patterns:
            if re.search(pattern, url_path, re.IGNORECASE):
                return True
        return False
    
    # 6. Для неизвестных доменов - общие паттерны
    news_patterns = [r'/news/', r'/blog/', r'/2024/', r'/2025/']
    return any(re.search(p, url, re.IGNORECASE) for p in news_patterns)
```

---

## 📊 Примеры работы

### Успешные совпадения
```
✅ https://openai.com/blog/gpt-4-turbo
   domain_patterns['openai.com'] = [r'/blog/'] → MATCH

✅ https://writer.com/engineering/ai-agents  
   domain_patterns['writer.com'] = [r'/engineering/'] → MATCH

✅ https://waymo.com/blog/2024/08/autonomous-driving
   domain_patterns['waymo.com'] = [r'/blog/\d{4}/\d{2}/'] → MATCH
```

### Исключенные URL
```
❌ https://openai.com/about
   exclude_patterns = [r'/about'] → EXCLUDED

❌ https://scale.com/_next/static/css/main.css
   exclude_patterns = [r'/_next/'] → EXCLUDED

❌ https://anthropic.com/image.jpg
   exclude_patterns = [r'\.jpg$'] → EXCLUDED
```

---

## 🛠️ Настройка новых источников

### Шаг 1: Добавление в tracking_sources.json
```json
{
  "source_id": "example_ai",
  "name": "Example AI",
  "url": "https://example.ai/blog",
  "type": "change_tracking",
  "category": "ai_companies",
  "active": true
}
```

### Шаг 2: Анализ структуры URL
```python
# Извлечь пример URL из markdown
URLs найденные:
- https://example.ai/blog/ai-research-2024
- https://example.ai/blog/machine-learning
- https://example.ai/news/company-update

Исключить:
- https://example.ai/about
- https://example.ai/contact
```

### Шаг 3: Добавление паттерна
```python
# В url_extractor.py:domain_patterns
'example.ai': [r'/blog/[^/]+', r'/news/[^/]+']
```

### Шаг 4: Проверка escape-sequences
```python
# Если markdown содержит \\\\\\\\:
escape_sources = [
    # ... existing sources
    'example.ai'  # Добавить сюда
]
```

### Шаг 5: Тестирование
```python
from change_tracking.url_extractor import URLExtractor
extractor = URLExtractor()
urls = extractor.extract_urls_from_content(markdown, 'https://example.ai/blog')
print(f"Найдено {len(urls)} URL")
```

---

## 🚨 Распространенные проблемы

### 1. Неправильный domain_pattern
**Симптом**: 0 URL извлекается, но ссылки есть в markdown
```python
# ❌ Неправильно
'writer.com': [r'/blog/[^/]+']  # URL имеют /engineering/

# ✅ Правильно  
'writer.com': [r'/engineering/[^/]+']
```

### 2. Слишком строгий паттерн
**Симптом**: Пропускаются релевантные URL
```python
# ❌ Слишком строго
'pathai.com': [r'/news/[^/]+$']  # Не работает для /news/subfolder/

# ✅ Правильно
'pathai.com': [r'/news/']  # Ловит всё в /news/
```

### 3. Пропущены escape-sequences
**Симптом**: 0 URL при наличии ссылок с `\\\\\\\\` в markdown
```python
# ✅ Решение
escape_sources = [..., 'domain.com']
```

---

## 📈 Метрики эффективности

### До оптимизации (07.08.2025)
- **27 источников работали** (55%)
- **280 URL** в базе
- Множество источников возвращали 0 URL

### После оптимизации (19.08.2025)  
- **47 источников работают** (100%)
- **1050+ URL** в базе
- Каждый источник извлекает минимум 6+ URL
- **Среднее время**: 3 сек/источник

---

## 🔗 См. также
- [Technical Fixes](technical-fixes.md) - Исправления и оптимизации
- [Database Schema](database-schema.md) - Структура базы данных
- [API Commands](api-commands.md) - Команды и примеры