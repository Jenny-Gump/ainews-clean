"""
WordPress Publisher Service
Handles article translation, rewriting, and preparation for WordPress publishing
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import openai
import re
from transliterate import translit
import requests
from requests.auth import HTTPBasicAuth
import base64
import mimetypes
import os

from core.database import Database
from core.config import Config
from app_logging import get_logger

logger = get_logger('services.wordpress_publisher')


class WordPressPublisher:
    """Service for preparing articles for WordPress publishing"""
    
    # Allowed categories (exact list from WordPress)
    ALLOWED_CATEGORIES = [
        "LLM", "Машинное обучение", "Техника", "Digital", 
        "Люди", "Финансы", "Наука", "Обучение", "Другие индустрии",
        "Безопасность", "Творчество", "Здоровье", "Космос", "Война", "Политика",
        "Гаджеты", "Игры", "Разработка"
    ]
    
    def __init__(self, config: Config, db: Database):
        self.config = config
        self.db = db
        # DeepSeek API uses OpenAI-compatible client but different base URL
        self.client = openai.OpenAI(
            api_key=config.openai_api_key,
            base_url="https://api.deepseek.com"
        )
        
    def process_articles_batch(self, limit: int = 10) -> Dict[str, Any]:
        """Process a batch of articles for WordPress"""
        logger.info(f"Starting WordPress publishing process for {limit} articles")
        
        results = {
            'processed': 0,
            'succeeded': 0,
            'failed': 0,
            'errors': []
        }
        
        # Get completed articles that haven't been translated yet
        articles = self._get_pending_articles(limit)
        
        if not articles:
            logger.info("No articles to process")
            return results
        
        logger.info(f"Found {len(articles)} articles to process")
        
        for article in articles:
            try:
                logger.info(f"Processing article: {article['title'][:50]}...")
                
                # Check if already processed
                if self._is_already_processed(article['article_id']):
                    logger.info(f"Article {article['article_id']} already processed, skipping")
                    continue
                
                # Translate and rewrite the article
                wp_data = self._process_article_with_llm(article)
                
                if wp_data:
                    # Validate the response
                    if self._validate_llm_response(wp_data):
                        # Save to WordPress table
                        self._save_wordpress_article(article['article_id'], wp_data)
                        results['succeeded'] += 1
                        logger.info(f"Successfully processed article: {article['article_id']}")
                    else:
                        logger.error(f"Invalid LLM response for article {article['article_id']}")
                        results['failed'] += 1
                        results['errors'].append({
                            'article_id': article['article_id'],
                            'error': 'Invalid LLM response format'
                        })
                        # Save failed status to database
                        self._save_failed_article(article['article_id'], 'Invalid LLM response format')
                else:
                    results['failed'] += 1
                    # Save failed status when LLM returns None
                    self._save_failed_article(article['article_id'], 'LLM processing failed')
                    
                results['processed'] += 1
                
            except Exception as e:
                logger.error(f"Error processing article {article.get('article_id')}: {str(e)}")
                results['failed'] += 1
                error_msg = str(e)
                if isinstance(e, TimeoutError):
                    error_msg = "Translation timeout after 3 minutes"
                results['errors'].append({
                    'article_id': article.get('article_id'),
                    'error': error_msg
                })
                # Save failed status to database
                self._save_failed_article(article.get('article_id'), error_msg)
        
        return results
    
    def _get_pending_articles(self, limit: int) -> List[Dict[str, Any]]:
        """Get articles that are completed but not yet translated"""
        query = """
        SELECT a.article_id, a.title, a.content, a.summary, a.tags, 
               a.categories, a.language, a.url, a.source_id, a.published_date
        FROM articles a
        LEFT JOIN wordpress_articles w ON a.article_id = w.article_id
        WHERE a.content_status = 'completed' 
          AND a.content IS NOT NULL
          AND w.id IS NULL
        ORDER BY a.published_date DESC
        LIMIT ?
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (limit,))
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def _is_already_processed(self, article_id: str) -> bool:
        """Check if article already exists in wordpress_articles table"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id FROM wordpress_articles WHERE article_id = ?",
                (article_id,)
            )
            return cursor.fetchone() is not None
    
    
    def _process_article_with_llm(self, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process article with LLM for translation and rewriting"""
        try:
            # Prepare the prompt
            prompt = self._build_llm_prompt(article)
            logger.debug(f"Prompt length: {len(prompt)} chars")
            
            # Call DeepSeek API with timeout
            logger.info(f"Calling DeepSeek API with model: {self.config.wordpress_llm_model}")
            try:
                response = self.client.chat.completions.create(
                    model=self.config.wordpress_llm_model,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    timeout=180  # 3 minutes timeout
                )
            except Exception as timeout_error:
                if "timeout" in str(timeout_error).lower():
                    logger.error(f"API timeout after 3 minutes for article {article.get('article_id')}")
                    raise TimeoutError("DeepSeek API timeout after 3 minutes")
                raise
            
            # Parse the response
            content = response.choices[0].message.content
            logger.info(f"Received LLM response, length: {len(content)} chars")
            logger.debug(f"Raw LLM response: {content[:200]}...")
            
            # Try to extract JSON from the response
            try:
                logger.debug("Attempting to parse JSON directly")
                result = json.loads(content)
                logger.info("Successfully parsed JSON response")
            except json.JSONDecodeError:
                logger.warning("Direct JSON parsing failed, trying regex extraction")
                # Try to find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        logger.info("Successfully extracted and parsed JSON using regex")
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON from response: {content[:500]}")
                        return None
                else:
                    logger.error(f"No JSON found in response: {content[:500]}")
                    return None
            
            # No media processing needed
            
            # Add metadata
            result['llm_model'] = self.config.wordpress_llm_model
            result['source_language'] = article.get('language', 'en')
            
            return result
            
        except Exception as e:
            logger.error(f"LLM processing error: {str(e)}")
            return None
    
    def _build_llm_prompt(self, article: Dict[str, Any]) -> str:
        """Build prompt for LLM processing"""
        
        prompt = f"""
Переведи и адаптируй эту статью об искусственном интеллекте для русскоязычной аудитории.

ИСХОДНАЯ СТАТЬЯ:
Заголовок: {article['title']}
URL: {article['url']}
Дата: {article['published_date']}
Исходные теги: {article.get('tags', '')}
Исходные категории: {article.get('categories', '')}

КОНТЕНТ:
{article['content'][:8000] if article['content'] else article.get('summary', '')}

ТРЕБОВАНИЯ К КАТЕГОРИЯМ:
⚠️ ВАЖНО: Выбери СТРОГО ОДНУ категорию из этого списка (не больше!):
{', '.join(self.ALLOWED_CATEGORIES)}

Правила выбора категории:
- LLM: если главная тема - языковые модели (GPT, Claude, Gemini и т.д.)
- Машинное обучение: алгоритмы, методы, исследования ML
- Техника: железо, чипы, GPU, TPU, инфраструктура для AI
- Digital: цифровизация, соцсети, e-commerce с AI
- Люди: персоналии, интервью, карьерные истории в AI
- Финансы: инвестиции в AI, финтех, алготрейдинг
- Наука: научные открытия с помощью AI
- Обучение: курсы, образование в сфере AI
- Безопасность: этика AI, регулирование, защита от AI-угроз
- Творчество: AI в искусстве, генерация контента, музыка
- Здоровье: AI в медицине, диагностика, фармацевтика
- Космос: AI в космосе, спутниках, астрономии, космических агентствах
- Война: военные разработки AI, дроны, оборонные технологии
- Политика: госрегулирование AI, национальные стратегии, геополитика AI
- Гаджеты: смартфоны с AI-функциями, умные устройства, носимая электроника, AI-процессоры в телефонах
- Игры: AI в геймдеве, игровые движки с AI, NPC на основе AI, генерация контента для игр
- Разработка: программирование с AI, кодинг-ассистенты, AI для разработчиков, инструменты и фреймворки
- Другие индустрии: если не подходит ни одна категория выше

ТРЕБОВАНИЯ К ТЕГАМ:
⚠️ ВАЖНО: Максимум 5 тегов на статью! Выбери самые релевантные.
НЕ используй номера версий в тегах (используй "ChatGPT", а НЕ "ChatGPT-4o")
Включи теги из 3 групп в порядке важности:
1. Главные AI модели/продукты (ChatGPT, Claude, Gemini, без версий!)
2. Ключевые компании (OpenAI, Google, Microsoft)
3. Важные персоны (если играют центральную роль в новости)

ФОРМАТ ОТВЕТА (строго JSON):
{{
  "title": "Заголовок новости на русском",
  "content": "Полный текст статьи в HTML формате",
  "excerpt": "Краткая аннотация статьи (150-200 символов)",
  "slug": "url-slug-transliteratsiya",
  "categories": ["ОДНА категория из списка выше"],
  "tags": ["тег1", "тег2", "тег3"],
  "_yoast_wpseo_title": "SEO заголовок (до 60 символов)",
  "_yoast_wpseo_metadesc": "SEO описание (до 160 символов)",
  "focus_keyword": "главное ключевое слово"
}}
"""
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for LLM"""
        return """You are a 35-year-old expert in programming and machine learning — a seasoned engineer with deep technical knowledge and strong awareness of current AI trends. You are now working as an editor and translator for an AI-focused journal.

Your primary task is to translate and adapt international AI news into Russian, strictly following the principles of classical journalism: report facts clearly, cite sources properly, and avoid distortion or bias.

At the same time, you write with personality — confident, insightful, and occasionally ironic. You're not afraid to highlight overhype, risks, or contradictions in the AI field, while still maintaining an overall positive and future-oriented attitude toward the technology.

Each piece must be:
- Translated into **fluent, high-quality Russian**
- Faithful to the original meaning, but engaging and lively
- Structured clearly, avoiding technical jargon unless necessary

You must include:
- A **neutral retelling of the news** with proper context
- At the end, add your commentary as a regular paragraph (300-500 characters)
- DO NOT format your opinion separately or use headings like "Мнение автора"
- Your commentary should flow naturally as the final paragraph of the article

⚠️ You must return the final result strictly in **JSON format**."""
    
    def _validate_llm_response(self, response: Dict[str, Any]) -> bool:
        """Validate LLM response format and content"""
        required_fields = ['title', 'content', 'excerpt', 'slug', 'categories', 'tags']
        
        # Check required fields
        for field in required_fields:
            if field not in response:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate categories
        if not isinstance(response['categories'], list):
            logger.error("Categories must be an array")
            return False
        
        # Ensure exactly one category
        if len(response['categories']) != 1:
            logger.error(f"Must have exactly 1 category, got {len(response['categories'])}")
            return False
        
        for category in response['categories']:
            if category not in self.ALLOWED_CATEGORIES:
                logger.error(f"Invalid category: {category}. Allowed: {self.ALLOWED_CATEGORIES}")
                return False
        
        # Validate tags
        if not isinstance(response['tags'], list):
            logger.error("Tags must be an array")
            return False
        
        # Check tags count (max 5)
        if len(response['tags']) > 5:
            logger.error(f"Too many tags: {len(response['tags'])}. Maximum 5 allowed")
            return False
        
        # Validate slug format (alphanumeric + hyphens)
        if not re.match(r'^[a-z0-9-]+$', response['slug']):
            logger.error(f"Invalid slug format: {response['slug']}")
            return False
        
        return True  
    
    
    
    def _generate_slug(self, title: str) -> str:
        """Generate URL slug from title"""
        try:
            # Transliterate to Latin
            slug = translit(title, 'ru', reversed=True)
        except:
            # Fallback to simple replacement
            slug = title
        
        # Clean and format
        slug = slug.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        
        return slug[:50]  # Limit length
    
    def _save_wordpress_article(self, article_id: str, wp_data: Dict[str, Any]) -> None:
        """Save processed article to wordpress_articles table"""
        
        # Generate slug if not provided or invalid
        if not wp_data.get('slug') or not re.match(r'^[a-z0-9-]+$', wp_data.get('slug', '')):
            wp_data['slug'] = self._generate_slug(wp_data['title'])
        
        # Insert into wordpress_articles
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO wordpress_articles (
                    article_id, title, content, excerpt, slug,
                    categories, tags, _yoast_wpseo_title, _yoast_wpseo_metadesc,
                    focus_keyword, featured_image_index, images_data,
                    translation_status, translated_at, source_language,
                    target_language, llm_model
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article_id,
                wp_data['title'],
                wp_data['content'],
                wp_data.get('excerpt'),
                wp_data['slug'],
                json.dumps(wp_data.get('categories', []), ensure_ascii=False),
                json.dumps(wp_data.get('tags', []), ensure_ascii=False),
                wp_data.get('_yoast_wpseo_title'),
                wp_data.get('_yoast_wpseo_metadesc'),
                wp_data.get('focus_keyword'),
                0,  # featured_image_index - no images
                '{}',  # images_data - empty
                'translated',
                datetime.now(),
                wp_data.get('source_language', 'en'),
                'ru',
                wp_data.get('llm_model')
            ))
            
            # Update article status to 'published' in articles table
            conn.execute("""
                UPDATE articles 
                SET content_status = 'published' 
                WHERE article_id = ?
            """, (article_id,))
        logger.info(f"Saved WordPress article for {article_id} and marked as published")
    
    def _save_failed_article(self, article_id: str, error: str) -> None:
        """Save failed translation attempt to wordpress_articles table"""
        try:
            # Get minimal article info for failed record
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT title FROM articles WHERE article_id = ?",
                    (article_id,)
                )
                row = cursor.fetchone()
                title = row[0] if row else "Unknown Article"
                
                # Insert failed record
                conn.execute("""
                    INSERT INTO wordpress_articles (
                        article_id, title, content, slug,
                        translation_status, translation_error, translated_at,
                        target_language, llm_model
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article_id,
                    title,
                    '',  # empty content
                    self._generate_slug(title),
                    'failed',
                    error,
                    datetime.now(),
                    'ru',
                    self.config.wordpress_llm_model
                ))
                
                # Update article status to 'failed' in articles table
                conn.execute("""
                    UPDATE articles 
                    SET content_status = 'failed' 
                    WHERE article_id = ?
                """, (article_id,))
            logger.info(f"Saved failed translation for {article_id}: {error}")
        except Exception as e:
            logger.error(f"Error saving failed article {article_id}: {str(e)}")
    
    def publish_to_wordpress(self, limit: int = 5) -> Dict[str, Any]:
        """Publish translated articles to WordPress"""
        logger.info(f"Starting WordPress publishing for {limit} articles")
        
        results = {
            'processed': 0,
            'published': 0,
            'failed': 0,
            'errors': []
        }
        
        # Check WordPress configuration
        if not all([self.config.wordpress_api_url, 
                   self.config.wordpress_username, 
                   self.config.wordpress_app_password]):
            logger.error("WordPress API configuration missing")
            results['errors'].append({
                'error': 'WordPress API not configured in .env file'
            })
            return results
        
        # Get translated articles not yet published
        articles = self._get_unpublished_articles(limit)
        
        if not articles:
            logger.info("No articles to publish")
            return results
        
        logger.info(f"Found {len(articles)} articles to publish")
        
        for article in articles:
            try:
                logger.info(f"Publishing article: {article['title'][:50]}...")
                
                # Prepare WordPress post data
                wp_post_data = self._prepare_wordpress_post(article)
                
                # Create post in WordPress
                wp_post_id = self._create_wordpress_post(wp_post_data)
                
                if wp_post_id:
                    # Update database with WordPress post ID
                    self._mark_as_published(article['id'], wp_post_id)
                    results['published'] += 1
                    logger.info(f"Successfully published article with WordPress ID: {wp_post_id}")
                    
                    # Автоматически обрабатываем медиафайлы
                    logger.info(f"Checking for media files for article {article['article_id']}")
                    media_result = self._process_media_for_article(
                        article['article_id'], 
                        wp_post_id,
                        article['title']
                    )
                    if media_result:
                        logger.info(f"Media processing completed for article {article['article_id']}")
                    else:
                        logger.warning(f"Media processing failed or no media found for article {article['article_id']}")
                else:
                    results['failed'] += 1
                    
                results['processed'] += 1
                
            except Exception as e:
                logger.error(f"Error publishing article {article.get('id')}: {str(e)}")
                results['failed'] += 1
                results['errors'].append({
                    'article_id': article.get('article_id'),
                    'error': str(e)
                })
        
        return results
    
    def _get_unpublished_articles(self, limit: int) -> List[Dict[str, Any]]:
        """Get translated articles that haven't been published to WordPress"""
        query = """
        SELECT id, article_id, title, content, excerpt, slug,
               categories, tags, _yoast_wpseo_title, _yoast_wpseo_metadesc,
               focus_keyword
        FROM wordpress_articles
        WHERE translation_status = 'translated' 
          AND published_to_wp = 0
        ORDER BY translated_at DESC
        LIMIT ?
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (limit,))
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def _prepare_wordpress_post(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare article data for WordPress API"""
        # Parse JSON fields
        categories = json.loads(article['categories']) if article['categories'] else []
        tags = json.loads(article['tags']) if article['tags'] else []
        
        # Get category mapping
        category_mapping = self.get_category_tag_mapping()
        
        # Map category names to IDs
        category_ids = []
        for cat_name in categories:
            if cat_name in category_mapping['categories']:
                category_ids.append(category_mapping['categories'][cat_name])
            else:
                logger.warning(f"Category '{cat_name}' not found in WordPress")
        
        # If no categories mapped, use "Новости" as default
        if not category_ids and 'Новости' in category_mapping['categories']:
            category_ids.append(category_mapping['categories']['Новости'])
        
        post_data = {
            'title': article['title'],
            'content': article['content'],
            'excerpt': article['excerpt'] or '',
            'slug': article['slug'],
            'status': 'draft',  # Start with draft for safety
            'categories': category_ids,
            'meta': {}
        }
        
        # Add Yoast SEO fields if available
        if article.get('_yoast_wpseo_title'):
            post_data['meta']['_yoast_wpseo_title'] = article['_yoast_wpseo_title']
        if article.get('_yoast_wpseo_metadesc'):
            post_data['meta']['_yoast_wpseo_metadesc'] = article['_yoast_wpseo_metadesc']
        if article.get('focus_keyword'):
            post_data['meta']['_yoast_wpseo_focuskw'] = article['focus_keyword']
        
        # Handle tags - create them if they don't exist
        tag_ids = []
        for tag_name in tags[:10]:  # Limit to 10 tags
            if tag_name in category_mapping['tags']:
                tag_ids.append(category_mapping['tags'][tag_name])
            else:
                # Try to create the tag
                tag_id = self._create_tag(tag_name)
                if tag_id:
                    tag_ids.append(tag_id)
        
        if tag_ids:
            post_data['tags'] = tag_ids
        
        return post_data
    
    def _create_wordpress_post(self, post_data: Dict[str, Any]) -> Optional[int]:
        """Create a post in WordPress via REST API"""
        try:
            url = f"{self.config.wordpress_api_url}/posts"
            
            # Prepare authentication
            auth = HTTPBasicAuth(self.config.wordpress_username, 
                               self.config.wordpress_app_password)
            
            # Make the request
            response = requests.post(
                url,
                json=post_data,
                auth=auth,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 201:
                wp_post = response.json()
                return wp_post.get('id')
            else:
                logger.error(f"WordPress API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating WordPress post: {str(e)}")
            return None
    
    def _mark_as_published(self, wordpress_article_id: int, wp_post_id: int) -> None:
        """Mark article as published in database"""
        with self.db.get_connection() as conn:
            conn.execute("""
                UPDATE wordpress_articles
                SET published_to_wp = 1,
                    wp_post_id = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (wp_post_id, wordpress_article_id))
        logger.info(f"Marked article {wordpress_article_id} as published with WP ID {wp_post_id}")
    
    def get_category_tag_mapping(self) -> Dict[str, Any]:
        """Get mapping of category and tag names to WordPress IDs"""
        # This method would fetch categories and tags from WordPress
        # and create a mapping for use in publishing
        
        mapping = {
            'categories': {},
            'tags': {}
        }
        
        try:
            # Get categories
            url = f"{self.config.wordpress_api_url}/categories"
            auth = HTTPBasicAuth(self.config.wordpress_username, 
                               self.config.wordpress_app_password)
            
            response = requests.get(url, auth=auth, params={'per_page': 100})
            if response.status_code == 200:
                for category in response.json():
                    mapping['categories'][category['name']] = category['id']
            
            # Get tags
            url = f"{self.config.wordpress_api_url}/tags"
            response = requests.get(url, auth=auth, params={'per_page': 100})
            if response.status_code == 200:
                for tag in response.json():
                    mapping['tags'][tag['name']] = tag['id']
            
            logger.info(f"Loaded {len(mapping['categories'])} categories and {len(mapping['tags'])} tags")
            return mapping
            
        except Exception as e:
            logger.error(f"Error fetching WordPress taxonomies: {str(e)}")
            return mapping
    
    def _create_tag(self, tag_name: str) -> Optional[int]:
        """Create a tag in WordPress if it doesn't exist"""
        try:
            url = f"{self.config.wordpress_api_url}/tags"
            auth = HTTPBasicAuth(self.config.wordpress_username, 
                               self.config.wordpress_app_password)
            
            data = {
                'name': tag_name,
                'slug': self._generate_slug(tag_name)
            }
            
            response = requests.post(url, json=data, auth=auth)
            
            if response.status_code == 201:
                tag = response.json()
                logger.info(f"Created tag '{tag_name}' with ID {tag['id']}")
                return tag['id']
            else:
                logger.error(f"Failed to create tag '{tag_name}': {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating tag '{tag_name}': {str(e)}")
            return None
    
    def _process_media_for_article(self, article_id: str, wp_post_id: int, article_title: str) -> bool:
        """Обрабатывает медиафайлы для только что опубликованной статьи"""
        try:
            # Проверяем наличие медиафайлов
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) 
                    FROM media_files 
                    WHERE article_id = ? 
                      AND file_path IS NOT NULL
                """, (article_id,))
                media_count = cursor.fetchone()[0]
                
                if media_count == 0:
                    logger.info(f"No media files found for article {article_id}")
                    return True
                
                logger.info(f"Found {media_count} media files for article {article_id}")
                
                # Получаем медиафайлы для загрузки
                media_files = self._get_media_for_upload(article_id)
                
                if not media_files:
                    logger.info(f"All media files already uploaded for article {article_id}")
                    # Но всё равно нужно вставить картинки в пост
                    insert_result = self._insert_images_into_post(wp_post_id, article_id)
                    if not insert_result:
                        logger.warning(f"Failed to insert images into post {wp_post_id}")
                    return True
                
                uploaded_media_ids = []
                
                for media in media_files:
                    try:
                        # Подготовка метаданных для перевода
                        metadata_to_translate = {
                            'alt_text': media.get('alt_text', ''),
                            'caption': media.get('caption', ''),
                            'article_title': article_title
                        }
                        
                        # Переводим метаданные
                        translated = self._translate_media_metadata(metadata_to_translate)
                        
                        if translated:
                            # Загружаем файл в WordPress
                            wp_media_id = self._upload_single_media(
                                file_path=media['file_path'],
                                post_id=wp_post_id,
                                metadata=translated
                            )
                            
                            if wp_media_id:
                                # Сохраняем результат в БД
                                self._save_media_upload_result(
                                    media['media_id'], 
                                    wp_media_id,
                                    translated.get('alt_text_ru'),
                                    translated.get('caption_ru')
                                )
                                uploaded_media_ids.append(wp_media_id)
                                logger.info(f"Successfully uploaded media {media['media_id']} as WP media {wp_media_id}")
                        
                    except Exception as e:
                        logger.error(f"Error processing media {media.get('media_id')}: {str(e)}")
                
                # Если загрузили медиафайлы, вставляем их в статью
                if uploaded_media_ids:
                    logger.info(f"Inserting {len(uploaded_media_ids)} images into post {wp_post_id}")
                    insert_result = self._insert_images_into_post(wp_post_id, article_id)
                    if not insert_result:
                        logger.warning(f"Failed to insert images into post {wp_post_id}")
                    
                return True
                
        except Exception as e:
            logger.error(f"Error in _process_media_for_article: {str(e)}")
            return False
    
    def upload_media_to_wordpress(self, limit: int = 10) -> Dict[str, Any]:
        """Upload media files to WordPress for published articles"""
        logger.info(f"Starting media upload to WordPress (limit: {limit})")
        
        results = {
            'processed': 0,
            'uploaded': 0,
            'failed': 0,
            'errors': []
        }
        
        # Get articles that need media upload
        articles = self._get_articles_needing_media_upload(limit)
        
        if not articles:
            logger.info("No articles need media upload")
            return results
        
        logger.info(f"Found {len(articles)} articles needing media upload")
        
        for article in articles:
            try:
                logger.info(f"Processing media for article: {article['title'][:50]}...")
                
                # Get media files for this article
                media_files = self._get_media_for_upload(article['article_id'])
                
                if not media_files:
                    logger.info(f"No media files found for article {article['article_id']}")
                    continue
                
                logger.info(f"Found {len(media_files)} media files to upload")
                
                for media in media_files:
                    try:
                        # Skip if already uploaded
                        if media.get('wp_media_id'):
                            logger.info(f"Media {media['media_id']} already uploaded, skipping")
                            continue
                        
                        # Prepare metadata for translation
                        metadata_to_translate = {
                            'alt_text': media.get('alt_text', ''),
                            'caption': media.get('caption', ''),
                            'article_title': article['title']
                        }
                        
                        # Translate metadata
                        translated = self._translate_media_metadata(metadata_to_translate)
                        
                        if translated:
                            # Upload file to WordPress
                            wp_media_id = self._upload_single_media(
                                file_path=media['file_path'],
                                post_id=article['wp_post_id'],
                                metadata=translated
                            )
                            
                            if wp_media_id:
                                # Save result in database
                                self._save_media_upload_result(
                                    media['media_id'], 
                                    wp_media_id,
                                    translated.get('alt_text_ru'),
                                    translated.get('caption_ru')
                                )
                                results['uploaded'] += 1
                                logger.info(f"Successfully uploaded media {media['media_id']} as WP media {wp_media_id}")
                            else:
                                results['failed'] += 1
                                results['errors'].append({
                                    'media_id': media['media_id'],
                                    'error': 'Failed to upload to WordPress'
                                })
                        else:
                            results['failed'] += 1
                            results['errors'].append({
                                'media_id': media['media_id'],
                                'error': 'Failed to translate metadata'
                            })
                            
                    except Exception as e:
                        logger.error(f"Error processing media {media.get('media_id')}: {str(e)}")
                        results['failed'] += 1
                        results['errors'].append({
                            'media_id': media.get('media_id'),
                            'error': str(e)
                        })
                
                # После загрузки всех медиафайлов вставляем их в статью
                if results['uploaded'] > 0:
                    logger.info(f"Inserting images into post {article['wp_post_id']}")
                    if self._insert_images_into_post(article['wp_post_id'], article['article_id']):
                        logger.info(f"Successfully inserted images into post")
                    else:
                        logger.warning(f"Failed to insert images into post")
                
                results['processed'] += 1
                
            except Exception as e:
                logger.error(f"Error processing article {article.get('article_id')}: {str(e)}")
                results['errors'].append({
                    'article_id': article.get('article_id'),
                    'error': str(e)
                })
        
        return results
    
    def _get_articles_needing_media_upload(self, limit: int) -> List[Dict[str, Any]]:
        """Get articles with wp_post_id that have media files not yet uploaded"""
        query = """
        SELECT DISTINCT
            w.article_id,
            w.wp_post_id,
            a.title
        FROM wordpress_articles w
        JOIN articles a ON w.article_id = a.article_id
        JOIN media_files m ON a.article_id = m.article_id
        WHERE w.published_to_wp = 1
          AND w.wp_post_id IS NOT NULL
          AND m.file_path IS NOT NULL
          AND (m.wp_upload_status IS NULL OR m.wp_upload_status = 'pending')
        LIMIT ?
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (limit,))
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def _get_media_for_upload(self, article_id: str) -> List[Dict[str, Any]]:
        """Get media files for an article that need to be uploaded"""
        query = """
        SELECT 
            id as media_id,
            article_id,
            url,
            file_path,
            alt_text,
            caption,
            mime_type,
            wp_media_id,
            wp_upload_status
        FROM media_files
        WHERE article_id = ?
          AND file_path IS NOT NULL
          AND (wp_upload_status IS NULL OR wp_upload_status = 'pending')
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.execute(query, (article_id,))
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def _translate_media_metadata(self, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Translate media metadata using DeepSeek Chat"""
        try:
            # Skip if no meaningful content to translate
            if not metadata.get('alt_text') and not metadata.get('caption'):
                logger.info("No metadata to translate, using defaults")
                return {
                    'alt_text_ru': metadata.get('article_title', 'Изображение'),
                    'caption_ru': '',
                    'slug': self._generate_slug(metadata.get('article_title', 'image'))
                }
            
            prompt = f"""ОБЯЗАТЕЛЬНО переведи метаданные изображения на РУССКИЙ язык.

Статья: {metadata.get('article_title', '')}
Alt текст (английский): {metadata.get('alt_text', '')}
Подпись (английский): {metadata.get('caption', '')}

⚠️ ВАЖНО: ВСЕ тексты должны быть на РУССКОМ языке!

Создай:
1. SEO-оптимизированный alt текст НА РУССКОМ (до 125 символов)
2. Подпись НА РУССКОМ, если есть оригинал (до 200 символов)
3. Человекочитаемый slug для файла (латиница, отражает суть)

Правила:
- ОБЯЗАТЕЛЬНО переведи английский текст на русский
- НЕ оставляй английские слова в alt_text_ru и caption_ru
- Если alt текст пустой или малоинформативный (например, "Image for...", "author"), создай осмысленный alt текст НА РУССКОМ на основе заголовка статьи

Примеры правильного перевода:
- "Apple Begins Selling New iPhone 16" → "Apple начинает продажи нового iPhone 16"
- "Tim Cook at conference" → "Тим Кук на конференции"

Верни JSON:
{{
    "alt_text_ru": "перевод alt текста НА РУССКОМ или новый осмысленный текст НА РУССКОМ",
    "caption_ru": "перевод подписи НА РУССКОМ или пустая строка",
    "slug": "seo-friendly-file-name"
}}"""
            
            logger.debug(f"Translating metadata with prompt length: {len(prompt)}")
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                timeout=30
            )
            
            content = response.choices[0].message.content
            logger.debug(f"Translation response: {content[:200]}...")
            
            # Parse JSON response
            try:
                result = json.loads(content)
                # Ensure slug is valid
                if 'slug' in result:
                    result['slug'] = re.sub(r'[^a-z0-9\-]', '', result['slug'].lower())
                    result['slug'] = result['slug'][:50]  # Limit length
                return result
            except json.JSONDecodeError:
                # Try to extract JSON from response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    logger.error("Failed to parse translation response")
                    return None
                    
        except Exception as e:
            logger.error(f"Error translating metadata: {str(e)}")
            return None
    
    def _upload_single_media(self, file_path: str, post_id: int, metadata: Dict[str, Any]) -> Optional[int]:
        """Upload a single media file to WordPress"""
        try:
            # Check if file exists
            # Handle different path formats
            if file_path.startswith('data/media/'):
                # Already full path
                full_path = file_path
            elif file_path.startswith('media/'):
                # Remove 'media/' prefix and join with config.MEDIA_DIR
                relative_path = file_path[6:]  # Remove 'media/' prefix
                full_path = os.path.join(self.config.MEDIA_DIR, relative_path)
            else:
                full_path = os.path.join(self.config.MEDIA_DIR, file_path)
            
            if not os.path.exists(full_path):
                logger.error(f"File not found: {full_path}")
                return None
            
            # Read file
            with open(full_path, 'rb') as f:
                file_data = f.read()
            
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(full_path)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            # Generate filename
            file_extension = os.path.splitext(file_path)[1]
            filename = f"{metadata['slug']}{file_extension}"
            
            logger.info(f"Uploading file: {filename} ({mime_type}, {len(file_data)} bytes)")
            
            # Prepare auth
            auth_string = base64.b64encode(
                f"{self.config.wordpress_username}:{self.config.wordpress_app_password}".encode()
            ).decode('utf-8')
            
            # Upload file
            response = requests.post(
                f"{self.config.wordpress_api_url}/media",
                headers={
                    'Authorization': f'Basic {auth_string}',
                    'Content-Type': mime_type,
                    'Content-Disposition': f'attachment; filename="{filename}"'
                },
                data=file_data,
                timeout=60
            )
            
            if response.status_code == 201:
                media = response.json()
                wp_media_id = media['id']
                logger.info(f"File uploaded successfully, WP media ID: {wp_media_id}")
                
                # Update metadata
                update_data = {
                    'title': metadata['alt_text_ru'],      # Заголовок на русском
                    'alt_text': metadata['alt_text_ru'],   # Alt текст на русском
                    'caption': metadata['caption_ru'],      # Подпись на русском
                    'description': metadata['caption_ru'],  # Описание на русском
                    'post': post_id  # Associate with post
                }
                
                update_response = requests.post(
                    f"{self.config.wordpress_api_url}/media/{wp_media_id}",
                    headers={
                        'Authorization': f'Basic {auth_string}',
                        'Content-Type': 'application/json'
                    },
                    json=update_data,
                    timeout=30
                )
                
                if update_response.status_code in [200, 201]:
                    logger.info(f"Media metadata updated successfully")
                else:
                    logger.warning(f"Failed to update metadata: {update_response.status_code}")
                
                return wp_media_id
            else:
                logger.error(f"Failed to upload file: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error uploading media: {str(e)}")
            return None
    
    def _save_media_upload_result(self, media_id: str, wp_media_id: int, 
                                 alt_text_ru: Optional[str], caption_ru: Optional[str]) -> None:
        """Save media upload result to database"""
        try:
            with self.db.get_connection() as conn:
                conn.execute("""
                    UPDATE media_files
                    SET wp_media_id = ?,
                        wp_upload_status = 'uploaded',
                        wp_uploaded_at = ?,
                        alt_text_ru = ?,
                        caption_ru = ?
                    WHERE id = ?
                """, (
                    wp_media_id,
                    datetime.now(),
                    alt_text_ru,
                    caption_ru,
                    media_id
                ))
            logger.info(f"Saved upload result for media {media_id}")
        except Exception as e:
            logger.error(f"Error saving upload result: {str(e)}")
    
    def _insert_images_into_post(self, wp_post_id: int, article_id: str) -> bool:
        """Вставляет картинки в статью по правилам:
        - 1 картинка: только в обложку (featured image)
        - 2+ картинки: первая в обложку, остальные через каждые 2 абзаца
        """
        try:
            # Получаем загруженные медиафайлы для статьи
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        m.wp_media_id,
                        m.alt_text_ru,
                        m.caption_ru
                    FROM media_files m
                    WHERE m.article_id = ?
                      AND m.wp_media_id IS NOT NULL
                    ORDER BY m.id
                """, (article_id,))
                
                media_items = cursor.fetchall()
                
                if not media_items:
                    logger.info(f"No uploaded media found for article {article_id}")
                    return True
                
                # Подготовка аутентификации
                auth_string = base64.b64encode(
                    f"{self.config.wordpress_username}:{self.config.wordpress_app_password}".encode()
                ).decode('utf-8')
                
                headers = {
                    'Authorization': f'Basic {auth_string}',
                    'Content-Type': 'application/json'
                }
                
                # Сначала пробуем получить контент из базы данных
                cursor = conn.execute("""
                    SELECT content 
                    FROM wordpress_articles 
                    WHERE wp_post_id = ?
                """, (wp_post_id,))
                row = cursor.fetchone()
                
                current_content = ""
                if row and row[0]:
                    current_content = row[0]
                    logger.info(f"Using content from database: {len(current_content)} chars")
                else:
                    # Если в БД нет контента, пробуем получить из WordPress
                    logger.warning(f"No content found in database for post {wp_post_id}, trying WordPress API")
                    post_response = requests.get(
                        f"{self.config.wordpress_api_url}/posts/{wp_post_id}?context=edit",
                        headers={'Authorization': f'Basic {auth_string}'},
                        timeout=30
                    )
                    
                    if post_response.status_code == 200:
                        post_data = post_response.json()
                        current_content = post_data.get('content', {}).get('raw', '')
                        if current_content:
                            logger.info(f"Using content from WordPress: {len(current_content)} chars")
                    
                    if not current_content:
                        logger.error(f"No content found for post {wp_post_id} in database or WordPress")
                        return False
                
                # Если только одна картинка - делаем её обложкой
                if len(media_items) == 1:
                    update_data = {
                        'featured_media': media_items[0][0]  # wp_media_id
                    }
                    
                    response = requests.post(
                        f"{self.config.wordpress_api_url}/posts/{wp_post_id}",
                        headers=headers,
                        json=update_data,
                        timeout=30
                    )
                    
                    if response.status_code in [200, 201]:
                        logger.info(f"Set featured image {media_items[0][0]} for post {wp_post_id}")
                        return True
                    else:
                        logger.error(f"Failed to set featured image: {response.status_code}")
                        return False
                
                # Если несколько картинок
                else:
                    # Первая картинка - в обложку
                    featured_media_id = media_items[0][0]
                    
                    # Остальные - вставляем в текст
                    # Используем regex для правильного разбиения с сохранением тегов
                    import re
                    # Разбиваем по закрывающему тегу параграфа, сохраняя сам тег
                    parts = re.split(r'(</p>)', current_content)
                    logger.info(f"Split content into {len(parts)} parts")
                    
                    # Собираем параграфы обратно (текст + закрывающий тег)
                    paragraphs = []
                    for i in range(0, len(parts)-1, 2):
                        if i+1 < len(parts) and parts[i].strip():  # Не пустой контент и есть закрывающий тег
                            paragraphs.append(parts[i] + parts[i+1])
                    
                    logger.info(f"Found {len(paragraphs)} paragraphs in content")
                    if len(paragraphs) == 0:
                        # Если нет тегов </p>, попробуем разделить по \n\n
                        paragraphs = [f"<p>{p.strip()}</p>" for p in current_content.split('\n\n') if p.strip()]
                        logger.info(f"Fallback: created {len(paragraphs)} paragraphs from double newlines")
                    
                    # Равномерно распределяем изображения между параграфами
                    modified_content = []
                    images_to_insert = media_items[1:]  # Все кроме первой (которая будет featured)
                    
                    if len(images_to_insert) > 0 and len(paragraphs) > 0:
                        # Рассчитываем позиции для вставки изображений
                        # Распределяем равномерно по доступным позициям
                        insert_positions = []
                        
                        if len(paragraphs) == 1:
                            # Если только 1 параграф, вставляем в конец
                            insert_positions = [0]
                        elif len(images_to_insert) <= len(paragraphs) - 1:
                            # Если изображений меньше чем позиций, распределяем равномерно
                            step = (len(paragraphs) - 1) / len(images_to_insert)
                            insert_positions = [int(i * step) for i in range(len(images_to_insert))]
                        else:
                            # Если изображений больше чем позиций, вставляем после каждого параграфа
                            insert_positions = list(range(min(len(paragraphs) - 1, len(images_to_insert))))
                        
                        logger.info(f"Will insert {len(images_to_insert)} images at positions: {insert_positions}")
                        
                        image_index = 0
                        for i, paragraph in enumerate(paragraphs):
                            modified_content.append(paragraph)
                            
                            # Проверяем, нужно ли вставить изображение после этого параграфа
                            if i in insert_positions and image_index < len(images_to_insert):
                                media_id = images_to_insert[image_index][0]
                                alt_text = images_to_insert[image_index][1]
                                caption = images_to_insert[image_index][2]
                                
                                logger.info(f"Inserting image {image_index + 1} after paragraph {i+1}")
                                
                                # Получаем URL картинки
                                media_response = requests.get(
                                    f"{self.config.wordpress_api_url}/media/{media_id}",
                                    headers={'Authorization': f'Basic {auth_string}'},
                                    timeout=30
                                )
                                
                                if media_response.status_code == 200:
                                    media_data = media_response.json()
                                    image_url = media_data.get('source_url', '')
                                    
                                    if not image_url:
                                        logger.error(f"No source_url found for media {media_id}")
                                        image_index += 1
                                        continue
                                    
                                    logger.info(f"Got image URL: {image_url}")
                                    
                                    # Создаём простой HTML для картинки
                                    if caption:
                                        image_html = f'<p><img src="{image_url}" alt="{alt_text}" /><br/><em>{caption}</em></p>'
                                    else:
                                        image_html = f'<p><img src="{image_url}" alt="{alt_text}" /></p>'
                                    
                                    modified_content.append(image_html)
                                    image_index += 1
                                else:
                                    logger.error(f"Failed to get media info: {media_response.status_code}")
                                    image_index += 1
                    else:
                        # Если нет изображений для вставки, просто копируем параграфы
                        for paragraph in paragraphs:
                            modified_content.append(paragraph)
                    
                    # Обновляем статью
                    final_content = ''.join(modified_content)
                    logger.info(f"Final content length: {len(final_content)}, images: {final_content.count('<img')}")
                    
                    update_data = {
                        'content': final_content,
                        'featured_media': featured_media_id
                    }
                    
                    response = requests.post(
                        f"{self.config.wordpress_api_url}/posts/{wp_post_id}",
                        headers=headers,
                        json=update_data,
                        timeout=30
                    )
                    
                    if response.status_code in [200, 201]:
                        logger.info(f"Successfully inserted {len(media_items)} images into post {wp_post_id}")
                        # Проверяем результат
                        check_response = requests.get(
                            f"{self.config.wordpress_api_url}/posts/{wp_post_id}?context=edit",
                            headers={'Authorization': f'Basic {auth_string}'},
                            timeout=30
                        )
                        if check_response.status_code == 200:
                            check_data = check_response.json()
                            saved_content = check_data.get('content', {}).get('raw', '')
                            logger.info(f"Saved content has {saved_content.count('<img')} images")
                        return True
                    else:
                        logger.error(f"Failed to update post with images: {response.status_code} - {response.text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error inserting images into post: {str(e)}")
            return False