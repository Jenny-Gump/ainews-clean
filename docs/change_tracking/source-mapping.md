# Source Mapping System - Change Tracking

**Файлы**: `data/tracking_sources.json`, `url_extractor.py:607-648`  
**Назначение**: Маппинг источников и их конфигурация

## 📋 Обзор

Source Mapping System управляет конфигурацией всех 47 источников в Change Tracking модуле. Система обеспечивает правильное маппирование URL источников на source_id для корректной идентификации и группировки статей.

## 🗂️ Структура конфигурации

### Основной файл: `data/tracking_sources.json`

```json
{
  "tracking_sources": [
    {
      "source_id": "anthropic",
      "name": "Anthropic News", 
      "url": "https://www.anthropic.com/news",
      "rss_url": "https://www.anthropic.com/news.rss",
      "type": "web",
      "category": "ai_companies"
    }
  ],
  "settings": {
    "default_limit": 20,
    "scan_interval_hours": 6,
    "export_after_scan": false,
    "tag_group_prefix": "tracking_"
  }
}
```

### Поля источника

| Поле | Тип | Описание | Пример |
|------|-----|----------|---------|
| **source_id** | string | Уникальный идентификатор | `"anthropic"` |
| **name** | string | Отображаемое название | `"Anthropic News"` |
| **url** | string | URL страницы для tracking | `"https://www.anthropic.com/news"` |
| **rss_url** | string | RSS feed (может быть пустым) | `"https://..."` |
| **type** | string | Тип источника | `"web"` |
| **category** | string | Категория источника | `"ai_companies"` |

## 📊 Категории источников

### AI Companies (13 источников)
```json
"ai_companies": [
  "anthropic", "openai_tracking", "mistral", "cohere", "ai21", 
  "stability", "perplexity", "cerebras", "elevenlabs"
]
```

### AI Platforms (8 источников)  
```json
"ai_platforms": [
  "huggingface", "databricks_tracking", "scale", "together",
  "instabase", "b12"
]
```

### AI Research (4 источника)
```json
"ai_research": [
  "google_research", "deepmind", "mit_news", "stanford_ai"
]
```

### Robotics (7 источников)
```json
"ai_robotics": [
  "waymo", "abb_robotics", "fanuc", "kinova", 
  "doosan_robotics", "manus"  
]
```

### Cloud AI (2 источника)
```json
"cloud_ai": [
  "google_cloud_ai", "aws_ai"
]
```

### Specialized категории
- **ai_audio**: `elevenlabs`, `soundhound`, `audioscenic`, `suno`
- **ai_healthcare**: `tempus`, `pathai`, `openevidence` 
- **ai_infrastructure**: `crusoe`, `lambda`, `nscale`, `cloudflare`
- **ai_finance**: `alpha_sense`, `appzen`
- **ai_enterprise**: `c3ai`
- **ai_writing**: `writer`
- **ai_design**: `uizard`
- **ai_development**: `cursor`

## 🔧 Source ID Mapping

### Функция `_get_source_domain()`
**Местоположение**: `url_extractor.py:626-648`

```python
def _get_source_domain(self, source_page_url: str) -> str:
    # 1. Точное совпадение URL
    clean_url = source_page_url.rstrip('/')
    if clean_url in self.tracking_sources:
        return self.tracking_sources[clean_url]
    
    # 2. Проверка без www
    if clean_url.startswith('https://www.'):
        no_www = clean_url.replace('https://www.', 'https://')
        if no_www in self.tracking_sources:
            return self.tracking_sources[no_www]
    
    # 3. Fallback к генерации из домена
    try:
        domain = urlparse(source_page_url).netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain.replace('.', '_').replace('-', '_')
    except:
        return 'unknown_source'
```

### Загрузка конфигурации
**Местоположение**: `url_extractor.py:607-624`

```python
def _load_tracking_sources(self) -> Dict[str, str]:
    sources_map = {}
    json_file = Path(__file__).parent.parent / 'data' / 'tracking_sources.json'
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for source in data.get('tracking_sources', []):
                # Маппим URL на source_id
                sources_map[source['url']] = source['source_id']
                # Также без trailing slash
                sources_map[source['url'].rstrip('/')] = source['source_id']
    except Exception as e:
        self.logger.error(f"Failed to load tracking_sources.json: {e}")
    
    return sources_map
```

## 🗺️ URL to Source ID маппинг

### Примеры успешного маппинга
```python
URL → source_id:
"https://www.anthropic.com/news" → "anthropic"
"https://openai.com/news/" → "openai_tracking" 
"https://huggingface.co/blog" → "huggingface"
"https://www.perplexity.ai/hub" → "perplexity"
"https://writer.com/engineering/" → "writer"
```

### Fallback маппинг (для неизвестных URL)
```python
"https://example.com/blog" → "example_com"
"https://new-site.ai/news" → "new_site_ai"
"https://sub.domain.com" → "sub_domain_com"
```

## 📈 Статистика источников

### По состоянию на 11.08.2025

| Категория | Количество | Топ источники по URL |
|-----------|------------|---------------------|
| **ai_robotics** | 7 | kuka (111), fanuc (109), kinova (13) |
| **ai_companies** | 13 | perplexity (57), anthropic (27), openai (19) |
| **ai_platforms** | 8 | nscale (60), crusoe (48), databricks (22) |
| **ai_research** | 4 | mit_news (15), google_research (12) |
| **ai_infrastructure** | 4 | cloudflare (20), crusoe (48), lambda (3) |

### URL распределение
```
Общий счет: 985+ URL
├── Top 10 источников: 585 URL (59%)
├── Средний уровень: 280 URL (28%) 
└── Малые источники: 120 URL (13%)
```

## 🛠️ Добавление нового источника

### Шаг 1: Добавление в tracking_sources.json
```json
{
  "source_id": "new_source",
  "name": "New AI Source",
  "url": "https://newsource.ai/blog/",
  "rss_url": "https://newsource.ai/blog/rss",
  "type": "web", 
  "category": "ai_companies"
}
```

### Шаг 2: Настройка URL patterns (при необходимости)
```python
# В url_extractor.py:domain_patterns
'newsource.ai': [r'/blog/[^/]+', r'/news/[^/]+']
```

### Шаг 3: Проверка escape-sequences (если нужно)
```python
# В url_extractor.py:escape_sources
escape_sources = [
    # ... existing sources
    'newsource.ai'  # если markdown содержит \\\\\\\\
]
```

### Шаг 4: Тестирование
```bash
cd "/Users/skynet/Desktop/AI DEV/ainews-clean"
python core/main.py --change-tracking --scan --limit 1
# Убедиться что новый источник работает
```

## 🔍 Диагностика источников

### Проверка маппинга
```python
from change_tracking.url_extractor import URLExtractor
extractor = URLExtractor()

# Проверить маппинг URL → source_id
source_id = extractor._get_source_domain('https://newsource.ai/blog/')
print(f"Source ID: {source_id}")  # Должен быть "new_source"
```

### Проверка всех источников
```bash
# Статистика по всем источникам  
python core/main.py --change-tracking --tracking-stats

# Найти источники с 0 URL
python -c "
from change_tracking.monitor import ChangeMonitor
import asyncio
monitor = ChangeMonitor()
# Логика для поиска неработающих источников
"
```

## 📊 Специальные случаи

### 1. Источники со сменой URL
**Пример**: Perplexity
```json
// Было:
"url": "https://blog.perplexity.ai/"

// Стало:  
"url": "https://www.perplexity.ai/hub"
```

### 2. Источники с поддоменами
**Пример**: Google Research
```json
"url": "https://research.google/blog/"  // НЕ research.google.com
```

### 3. Источники с специальными путями
**Пример**: Google Cloud AI
```json
"url": "https://cloud.google.com/blog/products/ai-machine-learning"
```

### 4. Удаленные источники
**Пример**: runway, standardbots - удалены из конфигурации как нерелевантные

## ⚠️ Важные замечания

### URL Normalization
- **Trailing slash**: URL автоматически обрабатываются с `/` и без
- **www prefix**: Система проверяет варианты с `www.` и без
- **Case insensitive**: Домены обрабатываются в нижнем регистре

### Маппинг приоритеты
1. **Точное совпадение** URL из tracking_sources.json
2. **www variant** (если основной URL не найден)
3. **Fallback генерация** из domain name

### Ограничения
- **source_id уникальность**: Каждый source_id должен быть уникальным
- **URL уникальность**: Каждый URL может принадлежать только одному источнику
- **JSON валидность**: Файл должен быть валидным JSON

## 🔄 Синхронизация с RSS системой

### Общие источники
Многие источники присутствуют и в RSS системе:
```json
"rss_url": "https://www.anthropic.com/news.rss"  // Используется RSS системой
"url": "https://www.anthropic.com/news"          // Используется Change Tracking
```

### Различия в источниках
- **Change Tracking**: 47 web источников
- **RSS система**: ~30 RSS feeds
- **Пересечение**: ~25 общих источников
- **Уникальные для CT**: Sources без RSS feeds

---

**🔗 См. также:**
- [URL Patterns](url-patterns.md) — Система фильтрации URL
- [Database Schema](database-schema.md) — Структура БД для источников
- [API Commands](api-commands.md) — Команды для работы с источниками