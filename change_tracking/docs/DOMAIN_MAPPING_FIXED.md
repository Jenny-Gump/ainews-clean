# ✅ Domain Mapping - ИСПРАВЛЕНО

**Дата исправления**: 2025-08-10  
**Статус**: ПРОБЛЕМА РЕШЕНА  
**Результат**: Система теперь использует единый маппинг источников

---

## 🎯 Что было исправлено

### 1. URLExtractor синхронизирован с ChangeMonitor
- **Файл**: `change_tracking/url_extractor.py`
- **Изменения**:
  - Добавлена загрузка `tracking_sources.json` при инициализации
  - Метод `_get_source_domain()` теперь использует правильные source_id из JSON
  - Fallback к генерации из домена только если источник не найден в маппинге

### 2. Исправлены существующие данные
- **Таблица**: `tracked_urls`
- **Обновлено**: 195 записей
- **Изменения маппинга**:
  ```
  b12_io → b12
  huggingface_co → huggingface
  openai_com → openai_tracking
  nscale_com → nscale
  suno_com → suno
  anthropic_com → anthropic
  cohere_com → cohere
  hai_stanford_edu → stanford_ai
  elevenlabs_io → elevenlabs
  aws_amazon_com → aws_ai
  together_ai → together
  cloud_google_com → google_cloud_ai
  alpha_sense_com → alpha_sense
  news_microsoft_com → microsoft_ai_news
  blog_google → google_ai_blog
  lambda_ai → lambda
  cerebras_ai → cerebras
  doosanrobotics_com → doosan_robotics
  ```

---

## 📋 Как работает система теперь

### Единый источник правды: tracking_sources.json

```json
{
  "source_id": "huggingface",      // Главный идентификатор
  "name": "Hugging Face Blog",
  "url": "https://huggingface.co/blog",
  "rss_url": "https://huggingface.co/blog/feed.xml",
  "type": "web",
  "category": "ai_platforms"
}
```

### Процесс работы:

1. **ChangeMonitor сканирует страницу**
   - Загружает `tracking_sources.json` при старте
   - Определяет `source_id` по URL из маппинга
   - Сохраняет в `tracked_articles.source_id`

2. **URLExtractor извлекает URL**
   - Также загружает `tracking_sources.json`
   - Использует тот же `source_id` для `tracked_urls.source_domain`
   - URL правильно связываются с источниками

3. **Экспорт работает корректно**
   - JOIN между таблицами теперь успешен
   - URL правильно ассоциированы с источниками

---

## 🔍 Проверка работы

### SQL запрос для проверки маппинга:
```sql
SELECT 
    ta.source_id,
    tu.source_domain,
    COUNT(tu.id) as url_count
FROM tracked_articles ta
LEFT JOIN tracked_urls tu ON ta.source_id = tu.source_domain
WHERE ta.change_status = 'changed'
GROUP BY ta.source_id, tu.source_domain;
```

### Результат после исправления:
```
source_id        | source_domain    | url_count
-----------------|------------------|----------
b12              | b12              | 36
huggingface      | huggingface      | 1
nscale           | nscale           | 19
openai_tracking  | openai_tracking  | 19
suno             | suno             | 3
```

---

## 📊 Код исправлений

### url_extractor.py - новые методы:

```python
def _load_tracking_sources(self) -> Dict[str, str]:
    """Загружает маппинг URL -> source_id из tracking_sources.json"""
    sources_map = {}
    json_file = Path(__file__).parent.parent / 'data' / 'tracking_sources.json'
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for source in data.get('tracking_sources', []):
                sources_map[source['url']] = source['source_id']
                sources_map[source['url'].rstrip('/')] = source['source_id']
        self.logger.info(f"URLExtractor loaded {len(sources_map)} tracking sources")
    except Exception as e:
        self.logger.error(f"Failed to load tracking_sources.json: {e}")
    
    return sources_map

def _get_source_domain(self, source_page_url: str) -> str:
    """Получает правильный source_id из tracking_sources.json"""
    clean_url = source_page_url.rstrip('/')
    
    # Проверяем точное совпадение URL
    if clean_url in self.tracking_sources:
        return self.tracking_sources[clean_url]
    
    # Проверяем без www
    if clean_url.startswith('https://www.'):
        no_www = clean_url.replace('https://www.', 'https://')
        if no_www in self.tracking_sources:
            return self.tracking_sources[no_www]
    
    # Fallback к генерации из домена
    try:
        domain = urlparse(source_page_url).netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain.replace('.', '_').replace('-', '_')
    except:
        return 'unknown_source'
```

---

## ✅ Результаты

1. **Маппинг исправлен** - source_id и source_domain теперь совпадают
2. **Данные очищены** - 195 записей обновлены на правильные source_id
3. **Система работает** - новые URL будут правильно связываться с источниками
4. **Экспорт функционирует** - JOIN между таблицами успешен

---

## 📝 Дополнительные замечания

### Проблема с извлечением URL из HuggingFace
- Извлекается только 1 URL вместо 70+
- Проблема НЕ в маппинге, а в паттернах фильтрации
- Требует отдельного исследования и исправления

### Рекомендации
1. При добавлении новых источников ВСЕГДА обновлять `tracking_sources.json`
2. Использовать `source_id` как главный идентификатор везде
3. Регулярно проверять соответствие маппинга SQL запросом выше

---

**Автор**: AI News Parser Team  
**Версия**: 1.0 - FIXED