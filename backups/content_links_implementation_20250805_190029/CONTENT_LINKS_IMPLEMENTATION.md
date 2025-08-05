# Content Links Implementation Plan
# Реализация извлечения анкорных ссылок и YouTube видео

> **Статус**: 🚧 В разработке  
> **Дата**: 5 августа 2025  
> **Бекап**: `backups/content_links_implementation_20250805_190029/`

## 🎯 ЦЕЛЬ ПРОЕКТА

Дополнить существующий Extract API пайплайн возможностью извлечения и сохранения:
- **Анкорных ссылок** из оригинального контента с их якорными текстами
- **YouTube видео** и других встроенных медиа
- **Правильной интеграции** ссылок в переведенный контент при публикации

## 🔍 ТЕКУЩАЯ ПРОБЛЕМА

### Что работает сейчас:
- ✅ Extract API извлекает основной контент
- ✅ Изображения сохраняются в `media_files`
- ✅ LLM переводит текст на русский
- ✅ Публикация в WordPress

### Что НЕ работает:
- ❌ Анкорные ссылки из текста теряются
- ❌ YouTube видео не встраиваются
- ❌ Переведенный текст не содержит ссылок из оригинала

### Пример проблемы:
**Оригинал**: `[Watch this video on YouTube](https://youtu.be/CEcEM_xu_Uc)`  
**После Extract**: Ссылка пропадает  
**В переводе**: Нет ни ссылки, ни видео

## 🏗️ АРХИТЕКТУРА РЕШЕНИЯ

### Двухэтапная обработка:
1. **Extract API** → основной контент (как сейчас)
2. **Scrape API** → все ссылки с анкорными текстами

### Маркерная система:
1. **Извлечение**: Ссылки заменяются на маркеры `{{LINK_001}}`
2. **Перевод**: LLM переводит текст, сохраняя маркеры
3. **Восстановление**: Маркеры заменяются на HTML ссылки

## 📊 СХЕМА БАЗЫ ДАННЫХ

### Новая таблица `content_links`:
```sql
CREATE TABLE content_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id TEXT NOT NULL,
    anchor_text TEXT NOT NULL,           -- "Watch this video"
    url TEXT NOT NULL,                   -- "https://youtu.be/..."
    link_type TEXT DEFAULT 'inline',     -- 'inline', 'youtube', 'reference'
    position_marker TEXT NOT NULL,       -- "{{LINK_001}}"
    position_in_content INTEGER,         -- позиция в тексте
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES articles(article_id)
);

CREATE INDEX idx_content_links_article_id ON content_links(article_id);
CREATE INDEX idx_content_links_marker ON content_links(position_marker);
```

### Обновление таблицы `articles`:
```sql
-- Добавляем поле для контента с маркерами
ALTER TABLE articles ADD COLUMN content_with_markers TEXT;
```

## 🔧 ПЛАН РЕАЛИЗАЦИИ

### Фаза 1: Модификация FirecrawlClient

#### 1.1 Добавить scrape метод:
```python
async def scrape_content(self, url: str) -> Dict[str, Any]:
    """
    Scrape для получения ссылок и HTML
    
    Returns:
        {
            'links': [{'url': '...', 'text': '...'}],
            'html': '<html>...',
            'markdown': '# Title...'
        }
    """
    payload = {
        'url': url,
        'formats': ['links', 'html', 'markdown']
    }
    # Реализация запроса к Scrape API
```

#### 1.2 Добавить парсер ссылок:
```python
def extract_links_with_anchors(self, html: str, markdown: str) -> List[Dict]:
    """
    Извлекает все ссылки с анкорными текстами
    
    Returns:
        [
            {
                'anchor_text': 'Watch this video',
                'url': 'https://youtu.be/CEcEM_xu_Uc',
                'link_type': 'youtube',
                'position_marker': '{{LINK_001}}'
            }
        ]
    """
    # 1. Парсим HTML для <a href="...">text</a>
    # 2. Определяем тип ссылки (youtube, inline, reference)
    # 3. Генерируем уникальные маркеры
    # 4. Возвращаем структурированные данные
```

### Фаза 2: Модификация ContentParser

#### 2.1 Двухэтапная обработка:
```python
async def parse_article(self, article_id: str, url: str, source_id: str):
    # ШАГ 1: Extract API (существующий код)
    extracted_data = await self.firecrawl_client.extract_with_retry(url)
    
    # ШАГ 2: Scrape API для ссылок (НОВОЕ)
    scraped_data = await self.firecrawl_client.scrape_content(url)
    links = await self.firecrawl_client.extract_links_with_anchors(
        scraped_data['html'], 
        scraped_data['markdown']
    )
    
    # ШАГ 3: Вставка маркеров в контент (НОВОЕ)
    marked_content = self._insert_link_markers(extracted_data['content'], links)
    
    # ШАГ 4: Сохранение
    await self._save_article_content(article_id, extracted_data, marked_content)
    await self._save_content_links(article_id, links)
```

#### 2.2 Маркировка ссылок:
```python
def _insert_link_markers(self, content: str, links: List[Dict]) -> str:
    """
    Заменяет ссылки в контенте на маркеры
    
    Input: "Read more about [OpenAI GPT-5](https://openai.com/gpt5)"
    Output: "Read more about {{LINK_001}}"
    """
    # 1. Находим все ссылки в markdown формате
    # 2. Заменяем на маркеры
    # 3. Обновляем position_marker в links
    # 4. Возвращаем маркированный контент
```

#### 2.3 Сохранение ссылок:
```python
async def _save_content_links(self, article_id: str, links: List[Dict]):
    """Сохраняет ссылки в таблицу content_links"""
    for link in links:
        conn.execute("""
            INSERT INTO content_links 
            (article_id, anchor_text, url, link_type, position_marker)
            VALUES (?, ?, ?, ?, ?)
        """, (
            article_id,
            link['anchor_text'],
            link['url'],
            link['link_type'],
            link['position_marker']
        ))
```

### Фаза 3: Модификация WordPressPublisher

#### 3.1 Загрузка ссылок при подготовке:
```python
def _get_pending_articles(self, limit: int):
    query = """
    SELECT a.*, 
           GROUP_CONCAT(cl.position_marker || ':::' || cl.anchor_text || ':::' || 
                       cl.url || ':::' || cl.link_type) as content_links
    FROM articles a
    LEFT JOIN wordpress_articles w ON a.article_id = w.article_id
    LEFT JOIN content_links cl ON a.article_id = cl.article_id
    WHERE a.content_status = 'completed' AND w.id IS NULL
    GROUP BY a.article_id
    LIMIT ?
    """
    # Парсим content_links и структурируем данные
```

#### 3.2 Обновление промпта для LLM:
```python
def _build_llm_prompt(self, article: Dict[str, Any]) -> str:
    content_links = article.get('content_links', [])
    
    links_info = ""
    if content_links:
        links_info = """
ВАЖНО - ССЫЛКИ В ТЕКСТЕ:
В тексте есть маркеры ссылок, которые нужно сохранить:

"""
        for link in content_links:
            links_info += f"- {link['position_marker']}: \"{link['anchor_text']}\" -> {link['url']}\n"
        
        links_info += """
ПРАВИЛА ДЛЯ ССЫЛОК:
1. ОБЯЗАТЕЛЬНО сохрани ВСЕ маркеры {{LINK_XXX}} в переведенном тексте
2. Переведи анкорный текст, но добавь маркер в конце
3. Пример: "Watch this video {{LINK_001}}" -> "Посмотрите это видео {{LINK_001}}"
4. НЕ удаляй и НЕ изменяй маркеры!

"""
    
    prompt = f"""
{links_info}

ИСХОДНАЯ СТАТЬЯ:
Заголовок: {article['title']}
URL: {article['url']}

КОНТЕНТ:
{article['content_with_markers'] or article['content']}

[остальной промпт как раньше]
"""
```

#### 3.3 Постобработка ответа LLM:
```python
def _restore_links_in_content(self, content: str, links: List[Dict]) -> str:
    """
    Заменяет маркеры обратно на HTML ссылки
    
    Input: "Посмотрите это видео {{LINK_001}}"
    Output: "Посмотрите это видео <a href='https://youtu.be/xxx'>видео</a>"
    """
    for link in links:
        marker = link['position_marker']
        
        if link['link_type'] == 'youtube':
            # YouTube embed для WordPress
            video_id = self._extract_youtube_id(link['url'])
            embed = f"""
            <figure class="wp-block-embed is-type-video is-provider-youtube">
                <div class="wp-block-embed__wrapper">
                    https://youtu.be/{video_id}
                </div>
            </figure>
            """
            content = content.replace(marker, embed)
            
        else:
            # Обычная ссылка
            html_link = f'<a href="{link["url"]}" target="_blank" rel="noopener">{link["translated_anchor"]}</a>'
            content = content.replace(marker, html_link)
    
    return content
```

## 🧪 ТЕСТОВЫЕ СЦЕНАРИИ

### Тест 1: Обычные ссылки
**Input**: `Read more about [OpenAI](https://openai.com)`  
**Expected**: В переводе должна быть ссылка на openai.com

### Тест 2: YouTube видео
**Input**: `[Watch video](https://youtu.be/CEcEM_xu_Uc)`  
**Expected**: WordPress embed блок с YouTube видео

### Тест 3: Множественные ссылки
**Input**: Статья с 5+ ссылками  
**Expected**: Все ссылки сохранены и корректно переведены

### Тест 4: Ошибки LLM
**Input**: LLM удаляет маркеры  
**Expected**: Система должна обнаружить и логировать ошибку

## 🔄 ПЛАН ОТКАТА

### При критических ошибках:
1. **Остановить обработку**: `pkill -f "python core/main.py"`
2. **Восстановить файлы**: 
   ```bash
   cd /Users/skynet/Desktop/AI\ DEV/ainews-clean
   cp -r backups/content_links_implementation_20250805_190029/* .
   ```
3. **Восстановить БД**: 
   ```bash
   sqlite3 data/ainews.db < backups/content_links_implementation_20250805_190029/ainews_dump.sql
   ```
4. **Проверить работоспособность**:
   ```bash
   python core/main.py --stats
   ```

### При частичных проблемах:
- Отключить новую функциональность через конфиг
- Использовать fallback на старую логику
- Логировать проблемы для исправления

## 📈 МЕТРИКИ УСПЕХА

1. **100% сохранение ссылок** из оригинальных статей
2. **Корректное встраивание YouTube** видео в WordPress
3. **Читаемые переведенные анкоры** на русском языке
4. **Стабильность системы** без падений производительности
5. **Обратная совместимость** со старыми статьями

## 🚀 ЗАПУСК В ПРОДАКШН

### Критерии готовности:
- [ ] Все тесты пройдены
- [ ] 10+ статей обработано успешно
- [ ] WordPress корректно отображает ссылки
- [ ] Система мониторинга не показывает ошибок
- [ ] Создан свежий бекап

### Команды для запуска:
```bash
# Тестовый прогон
python core/main.py --parse-pending --limit 3

# Полный цикл
python core/main.py --rss-full
python core/main.py --wordpress-prepare --limit 5
python core/main.py --wordpress-publish --limit 5
```

---

> 💡 **Важно**: После успешного запуска удалить этот файл и убрать упоминания из CLAUDE.md