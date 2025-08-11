# Источники новостей AI News Parser

Всего в системе **78 источников**: 30 RSS источников + 48 tracking источников.

## 📡 RSS источники (30)

RSS источники обрабатываются через RSS Discovery фазу и загружают статьи в таблицу `articles`.

### Конфигурация
- **Файл**: `services/sources_extract.json`
- **Обработка**: `services/rss_discovery.py`
- **Команда**: `python core/main.py --rss-discover`

### Список источников

| ID | Название | RSS URL |
|----|----------|---------|
| google_alerts_gpt | Google Alerts - GPT | https://www.google.com/alerts/feeds/04064620169352565923/8993086433604850503 |
| google_alerts_ai | Google Alerts - AI | https://www.google.com/alerts/feeds/04064620169352565923/339785620834888674 |
| google_alerts_space | Google Alerts - Space | https://www.google.ru/alerts/feeds/04064620169352565923/14062140338483053459 |
| google_alerts_drone | Google Alerts - Drone | https://www.google.ru/alerts/feeds/04064620169352565923/4150197778555265219 |
| google_alerts_war | Google Alerts - War | https://www.google.ru/alerts/feeds/04064620169352565923/15279248140888128705 |
| amazon_ai | Amazon AI Blog | https://www.amazon.science/index.rss |
| apple_ml | Apple Machine Learning | https://machinelearning.apple.com/rss.xml |
| ars_technica_ai | Ars Technica AI | https://arstechnica.com/ai/rss |
| databricks | Databricks Blog | https://www.databricks.com/blog/feed.xml |
| datarobot | DataRobot Blog | https://www.datarobot.com/blog/feed/ |
| forbes_ai | Forbes AI | https://www.forbes.com/innovation/feed2 |
| google_ai | Google AI Blog | https://research.google/blog/rss |
| google_deepmind | Google DeepMind Blog | https://deepmind.google/blog/rss.xml |
| hugging_face | Hugging Face Blog | https://huggingface.co/blog/feed.xml |
| ibm_ai | IBM Newsroom | https://newsroom.ibm.com/announcements?pagetemplate=rss |
| microsoft_ai | Microsoft Research Blog | https://www.microsoft.com/en-us/research/feed/ |
| mit_news_ai | MIT News AI | https://news.mit.edu/topic/mitartificial-intelligence2-rss.xml |
| mit_technology_review_ai | MIT Technology Review AI | https://www.technologyreview.com/topic/artificial-intelligence/feed/ |
| nvidia_edge_ai | NVIDIA Edge AI Blog | https://blogs.nvidia.com/rss |
| openai | OpenAI News | https://openai.com/blog/rss.xml |
| palantir | Palantir Blog | https://blog.palantir.com/feed |
| pytorch_blog | PyTorch Blog | https://pytorch.org/feed/ |
| salesforce_ai | Salesforce AI Research | https://blog.salesforceairesearch.com/rss/ |
| stanford_ai_lab | Stanford AI Lab | https://ai.stanford.edu/feed/ |
| techcrunch_ai | TechCrunch AI | https://techcrunch.com/category/artificial-intelligence/rss |
| tensorflow_blog | TensorFlow Blog | https://blog.tensorflow.org/rss.xml |
| the_decoder | The Decoder | https://the-decoder.com/rss |
| the_verge_ai | The Verge AI | https://www.theverge.com/rss/index.xml |
| venturebeat_ai | VentureBeat AI | https://venturebeat.com/category/ai/feed/ |
| wired_ai | Wired AI | https://www.wired.com/feed/rss |

## 🔍 Tracking источники (48)

Tracking источники отслеживают изменения на веб-страницах через Change Tracking модуль.

### Конфигурация
- **Файл**: `data/tracking_sources.json`
- **Обработка**: `change_tracking/monitor.py`
- **Команда**: `python core/main.py --change-tracking --scan`

### Список источников по категориям

#### AI Companies (17)
- anthropic - Anthropic News
- google_ai_blog - Google AI Blog  
- openai_tracking - OpenAI News
- microsoft_ai_news - Microsoft AI News
- mistral - Mistral AI News
- cohere - Cohere Blog
- ai21 - AI21 Labs Blog
- stability - Stability AI News
- google_cloud_ai - Google Cloud AI Blog
- aws_ai - AWS AI Blog
- scale - Scale AI Blog
- together - Together AI Blog
- elevenlabs - ElevenLabs Blog
- writer - Writer Engineering Blog
- crusoe - Crusoe AI Blog
- lambda - Lambda Labs Blog

#### AI Research (5)
- google_research - Google Research Blog
- deepmind - DeepMind Blog
- mit_news - MIT News - AI
- stanford_ai - Stanford AI Lab
- huggingface - Hugging Face Blog

#### AI Robotics (10)
- waymo - Waymo Blog
- standardbots - Standard Bots Blog
- abb_robotics - ABB Robotics News
- fanuc - FANUC America News
- kuka - KUKA Robotics News
- kinova - Kinova Robotics Press
- doosan_robotics - Doosan Robotics News
- manus - Manus Blog

#### AI Healthcare (4)
- openevidence - OpenEvidence Announcements
- tempus - Tempus Tech Blog
- pathai - PathAI News
- augmedix - Augmedix Resources

#### AI Platforms (5)
- databricks_tracking - Databricks Blog
- instabase - Instabase Blog
- b12 - B12 Blog
- mindfoundry - Mind Foundry Blog
- nscale - nScale Blog

#### AI Audio (5)
- elevenlabs - ElevenLabs Blog
- soundhound - SoundHound Voice AI Blog
- suno - Suno AI Blog (AI музыка)
- audioscenic - AudioScenic News

#### AI Finance (2)
- alpha_sense - AlphaSense Blog
- appzen - AppZen Blog

#### Другие категории (5)
- c3ai - C3 AI Blog (ai_enterprise)
- uizard - Uizard Blog (ai_design)
- perplexity - Perplexity AI Blog (AI поисковик)
- cerebras - Cerebras AI Blog (AI чипы)
- runway - Runway ML Research (генеративное видео)

## 🗄️ База данных

### Таблица `sources`
- **Всего записей**: 78 (30 RSS + 48 tracking)
- **Основные поля**:
  - `source_id` - уникальный идентификатор
  - `name` - название источника
  - `url` - основной URL
  - `rss_url` - RSS feed URL (для RSS источников)
  - `category` - категория источника
  - `last_parsed` - последняя проверка
  - `total_articles` - всего статей найдено

## 📝 Работа с источниками

### Добавить новый RSS источник

1. Отредактировать файл `services/sources_extract.json`:
```json
{
  "id": "new_source",
  "name": "New Source Name",
  "url": "https://example.com",
  "rss_url": "https://example.com/rss"
}
```

2. Добавить в БД:
```sql
INSERT INTO sources (source_id, name, url, rss_url, has_rss) 
VALUES ('new_source', 'New Source Name', 'https://example.com', 'https://example.com/rss', 1);
```

3. Добавить маппинг в `monitoring/static/pipeline-logs.js`:
```javascript
'new_source': 'New Source Name',
```

### Добавить новый tracking источник

1. Отредактировать файл `data/tracking_sources.json`:
```json
{
  "source_id": "new_tracking",
  "name": "New Tracking Source",
  "url": "https://example.com/news",
  "rss_url": "https://example.com/rss",
  "type": "web",
  "category": "ai_companies"
}
```

2. Добавить в БД:
```sql
INSERT INTO sources (source_id, name, url, rss_url, category) 
VALUES ('new_tracking', 'New Tracking Source', 'https://example.com/news', 'https://example.com/rss', 'ai_companies');
```

3. Добавить маппинг в `monitoring/static/pipeline-logs.js`

### Проверка источников

```bash
# Проверить все RSS источники
python core/main.py --list-sources

# Запустить RSS Discovery
python core/main.py --rss-discover

# Запустить tracking scan
python core/main.py --change-tracking --scan --limit 5
```

## 📊 Статистика

```bash
# Показать статистику по источникам
python core/main.py --stats

# SQL запрос для проверки источников в БД
sqlite3 data/ainews.db "SELECT source_id, name, total_articles FROM sources ORDER BY total_articles DESC LIMIT 10"
```

---

**Последнее обновление**: 8 августа 2025
**Версия**: 1.0