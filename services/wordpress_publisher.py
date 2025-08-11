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
from openai import OpenAI
from httpx import ReadError, ConnectError, TimeoutException

from core.database import Database
from core.config import Config
from app_logging import get_logger
from services.prompts_loader import load_prompt

logger = get_logger('services.wordpress_publisher')


class WordPressPublisher:
    """Service for preparing articles for WordPress publishing"""
    
    # Allowed categories (exact list from WordPress)
    ALLOWED_CATEGORIES = [
        "LLM", "Машинное обучение", "Железо", "Digital", 
        "Люди", "Финансы", "Наука", "Обучение",
        "Безопасность", "Творчество", "Здоровье", "Космос", "Война", "Политика",
        "Гаджеты", "Игры", "Разработка"
    ]
    
    def __init__(self, config: Config, db: Database):
        self.config = config
        self.db = db
        # DeepSeek API uses OpenAI-compatible client but different base URL
        self.deepseek_client = openai.OpenAI(
            api_key=config.openai_api_key,
            base_url="https://api.deepseek.com"
        )
        # GPT-4o fallback client
        self.openai_client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
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
        
        # Get parsed articles that haven't been translated yet
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
        """Get articles that are parsed but not yet translated"""
        query = """
        SELECT a.article_id, a.title, a.content, a.summary, a.tags, 
               a.categories, a.language, a.url, a.source_id, a.published_date
        FROM articles a
        LEFT JOIN wordpress_articles w ON a.article_id = w.article_id
        WHERE a.content_status = 'parsed' 
          AND a.media_status = 'ready'
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
            
            response = None
            
            # Try DeepSeek first with retry
            for attempt in range(3):
                try:
                    # Log BEFORE sending request (no icon - just info)
                    from app_logging import log_operation
                    log_operation(f'DeepSeek ({attempt + 1}/3) начинает перевод статьи...',
                        model=self.config.wordpress_llm_model,
                        processing_stage='article_translation',
                        article_id=article.get('article_id'),
                        phase='wordpress_prep',
                        retry_attempt=attempt + 1,
                        max_attempts=3
                    )
                    
                    logger.info(f"Calling DeepSeek API (attempt {attempt + 1}/3) with model: {self.config.wordpress_llm_model}")
                    response = self.deepseek_client.chat.completions.create(
                        model=self.config.wordpress_llm_model,
                        messages=[
                            {"role": "system", "content": self._get_system_prompt()},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        timeout=90  # 90 seconds timeout for DeepSeek
                    )
                    logger.info("DeepSeek API responded successfully")
                    
                    # Log LLM operation with detailed tracking
                    from app_logging import log_operation
                    tokens_input = len(prompt) // 4
                    tokens_output = len(response.choices[0].message.content) // 4
                    cost_usd = (tokens_input * 0.14 + tokens_output * 0.28) / 1_000_000
                    log_operation(f'✅ DeepSeek ({attempt + 1}/3) перевод завершен ({tokens_input + tokens_output} токенов)',
                        model=self.config.wordpress_llm_model,
                        tokens_input=tokens_input,
                        tokens_output=tokens_output,
                        tokens_approx=tokens_input + tokens_output,
                        cost_usd=cost_usd,
                        success=True,
                        retry_attempt=attempt + 1,
                        max_attempts=3,
                        processing_stage='article_translation',
                        article_id=article.get('article_id'),
                        phase='wordpress_prep'
                    )
                    break  # Success, exit retry loop
                except (Exception, TimeoutError, ReadError, ConnectError, TimeoutException) as api_error:
                    error_type = type(api_error).__name__
                    logger.warning(f"DeepSeek API attempt {attempt + 1} failed ({error_type}): {str(api_error)}")
                    
                    # Log failed LLM attempt
                    from app_logging import log_error, log_operation
                    fallback_reason = 'timeout' if isinstance(api_error, (TimeoutError, TimeoutException)) else \
                                    'network_error' if isinstance(api_error, (ReadError, ConnectError)) else \
                                    'api_error'
                    
                    log_operation(f'❌ DeepSeek ({attempt + 1}/3) ошибка: {fallback_reason}',
                        model=self.config.wordpress_llm_model,
                        success=False,
                        retry_attempt=attempt + 1,
                        max_attempts=3,
                        fallback_reason=fallback_reason,
                        processing_stage='article_translation',
                        article_id=article.get('article_id'),
                        phase='wordpress_prep',
                        error_message=str(api_error)[:200]
                    )
                    
                    # Special handling for network/timeout errors
                    if "receive_response_body" in str(api_error) or isinstance(api_error, (ReadError, TimeoutError, TimeoutException)):
                        logger.warning("DeepSeek API hanging on response body - forcing fallback")
                    
                    # Wait 5 seconds between attempts (except after the last one)
                    if attempt < 2:  # Not the last attempt
                        import asyncio
                        import time
                        logger.info("Waiting 5 seconds before next attempt...")
                        time.sleep(5)
                    
                    if attempt == 2:  # Last attempt failed
                        # Fallback to GPT-4o
                        try:
                            logger.info("Falling back to GPT-4o...")
                            response = self.openai_client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role": "system", "content": self._get_system_prompt()},
                                    {"role": "user", "content": prompt}
                                ],
                                temperature=0.7,
                                timeout=60  # 60 seconds timeout for GPT-4o
                            )
                            logger.info("GPT-4o responded successfully")
                            
                            # Log LLM fallback operation with detailed tracking
                            from app_logging import log_operation
                            tokens_input = len(prompt) // 4
                            tokens_output = len(response.choices[0].message.content) // 4
                            cost_usd = (tokens_input * 5.0 + tokens_output * 15.0) / 1_000_000
                            log_operation(f'⚠️ Fallback на GPT-4o после 3 неудач DeepSeek ({tokens_input + tokens_output} токенов)',
                                model='gpt-4o',
                                tokens_input=tokens_input,
                                tokens_output=tokens_output,
                                tokens_approx=tokens_input + tokens_output,
                                cost_usd=cost_usd,
                                success=True,
                                fallback=True,
                                fallback_reason='deepseek_failed',
                                processing_stage='article_translation',
                                article_id=article.get('article_id'),
                                phase='wordpress_prep'
                            )
                        except Exception as openai_error:
                            logger.error(f"GPT-4o fallback also failed: {str(openai_error)}")
                            
                            # Log failed fallback attempt
                            from app_logging import log_operation
                            log_operation('❌ GPT-4o fallback также не удался',
                                model='gpt-4o',
                                success=False,
                                fallback=True,
                                fallback_reason='gpt4o_failed',
                                processing_stage='article_translation',
                                article_id=article.get('article_id'),
                                phase='wordpress_prep',
                                error_message=str(openai_error)[:200]
                            )
                            return None
            
            if not response:
                logger.error("No response from any LLM")
                return None
            
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
    
    async def _generate_tags_with_llm(self, translated_article: Dict[str, Any]) -> List[str]:
        """Generate tags for translated article using existing tags list"""
        try:
            # Load existing clean tags
            import json
            import asyncio
            with open('data/wordpress_tags_clean.json', 'r', encoding='utf-8') as f:
                existing_tags = json.load(f)
            
            # Extract just tag names for the prompt
            tag_names = [tag['name'] for tag in existing_tags]
            
            # Загружаем промпт из файла
            prompt = load_prompt('tag_generator',
                title=translated_article['title'],
                content=translated_article['content'][:2000],
                available_tags=json.dumps(tag_names, ensure_ascii=False)
            )

            response = None
            
            # Try DeepSeek first with retries
            for attempt in range(3):
                try:
                    # Log BEFORE sending request (no icon - just info)
                    from app_logging import log_operation
                    log_operation(f'DeepSeek ({attempt + 1}/3) начинает генерацию тегов...',
                        model='deepseek-chat',
                        processing_stage='tag_generation',
                        article_id=translated_article.get('article_id'),
                        phase='wordpress_prep',
                        retry_attempt=attempt + 1,
                        max_attempts=3
                    )
                    
                    logger.info(f"Calling DeepSeek API for tag generation (attempt {attempt + 1}/3)...")
                    
                    response = self.deepseek_client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,  # Low temperature for consistent tag selection
                        timeout=30
                    )
                    logger.info("DeepSeek API responded successfully for tags")
                    
                    # Log successful DeepSeek tag generation
                    from app_logging import log_operation
                    tokens_input = len(prompt) // 4
                    tokens_output = len(response.choices[0].message.content) // 4
                    cost_usd = (tokens_input * 0.14 + tokens_output * 0.28) / 1_000_000
                    log_operation(f'✅ DeepSeek ({attempt + 1}/3) теги сгенерированы ({tokens_input + tokens_output} токенов)',
                        model='deepseek-chat',
                        tokens_input=tokens_input,
                        tokens_output=tokens_output,
                        tokens_approx=tokens_input + tokens_output,
                        cost_usd=cost_usd,
                        success=True,
                        retry_attempt=attempt + 1,
                        max_attempts=3,
                        processing_stage='tag_generation',
                        article_id=translated_article.get('article_id'),
                        phase='wordpress_prep'
                    )
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    logger.warning(f"DeepSeek tag generation attempt {attempt + 1} failed: {e}")
                    
                    # Log failed attempt
                    from app_logging import log_operation
                    fallback_reason = 'timeout' if 'timeout' in str(e).lower() else 'api_error'
                    log_operation(f'❌ DeepSeek ({attempt + 1}/3) ошибка генерации тегов: {fallback_reason}',
                        model='deepseek-chat',
                        success=False,
                        retry_attempt=attempt + 1,
                        max_attempts=3,
                        fallback_reason=fallback_reason,
                        processing_stage='tag_generation',
                        article_id=translated_article.get('article_id'),
                        phase='wordpress_prep',
                        error_message=str(e)[:200]
                    )
                    
                    if attempt < 2:  # Not the last attempt
                        wait_time = 3 + attempt * 2  # 3, 5 seconds
                        logger.info(f"Waiting {wait_time} seconds before retry...")
                        await asyncio.sleep(wait_time)
                    else:
                        # All attempts failed, try fallback to GPT-3.5
                        logger.info("All DeepSeek attempts failed, falling back to GPT-3.5-turbo...")
                        try:
                            response = self.openai_client.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {"role": "user", "content": prompt}
                                ],
                                temperature=0.3,
                                timeout=30
                            )
                            logger.info("GPT-3.5-turbo responded successfully for tags")
                            
                            # Log GPT-3.5 fallback success
                            tokens_input = len(prompt) // 4
                            tokens_output = len(response.choices[0].message.content) // 4
                            cost_usd = (tokens_input * 0.5 + tokens_output * 1.5) / 1_000_000
                            log_operation(f'⚠️ Fallback на GPT-3.5 для тегов после 3 неудач DeepSeek ({tokens_input + tokens_output} токенов)',
                                model='gpt-3.5-turbo',
                                tokens_input=tokens_input,
                                tokens_output=tokens_output,
                                tokens_approx=tokens_input + tokens_output,
                                cost_usd=cost_usd,
                                success=True,
                                fallback=True,
                                fallback_reason='deepseek_failed',
                                processing_stage='tag_generation',
                                article_id=translated_article.get('article_id'),
                                phase='wordpress_prep'
                            )
                        except Exception as gpt_error:
                            logger.error(f"GPT-3.5-turbo also failed: {gpt_error}")
                            
                            # Log GPT-3.5 fallback failure
                            log_operation('❌ GPT-3.5 fallback для тегов также не удался',
                                model='gpt-3.5-turbo',
                                success=False,
                                fallback=True,
                                fallback_reason='gpt35_failed',
                                processing_stage='tag_generation',
                                article_id=translated_article.get('article_id'),
                                phase='wordpress_prep',
                                error_message=str(gpt_error)[:200]
                            )
                            return []
            
            if not response:
                logger.error("No response from any LLM for tag generation")
                return []
            
            # Note: LLM operation already logged above
            
            # Parse response
            content = response.choices[0].message.content.strip()
            logger.debug(f"Tags response: {content}")
            
            # Try to extract JSON array
            try:
                if content.startswith('['):
                    tags = json.loads(content)
                else:
                    # Try to find JSON array in the response
                    import re
                    json_match = re.search(r'\[.*?\]', content, re.DOTALL)
                    if json_match:
                        tags = json.loads(json_match.group())
                    else:
                        logger.warning(f"No JSON array found in tags response: {content}")
                        return []
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse tags JSON: {e}. Response: {content}")
                return []
            
            # Validate and limit tags
            if not isinstance(tags, list):
                logger.warning(f"Tags is not a list: {tags}")
                return []
            
            # Ensure tags are strings and limit to 5
            tags = [str(tag) for tag in tags[:5]]
            
            logger.info(f"Generated tags: {tags}")
            return tags
            
        except Exception as e:
            logger.error(f"Failed to generate tags: {e}")
            return []
    
    def _build_llm_prompt(self, article: Dict[str, Any]) -> str:
        """Build prompt for LLM processing"""
        
        # Загружаем промпт из файла
        prompt = load_prompt('article_translator',
            title=article['title'],
            url=article['url'],
            published_date=article['published_date'],
            tags=article.get('tags', ''),
            categories=article.get('categories', ''),
            content=article['content'][:8000] if article['content'] else article.get('summary', ''),
            allowed_categories=', '.join(self.ALLOWED_CATEGORIES)
        )
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for LLM"""
        return load_prompt('article_translator')
    
    def _validate_llm_response(self, response: Dict[str, Any]) -> bool:
        """Validate LLM response format and content"""
        # Tags теперь не обязательны - будут генерироваться отдельно
        required_fields = ['title', 'content', 'excerpt', 'slug', 'categories']
        
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
        
        # Tags validation removed - will be handled separately
        
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
                    
                    # ВАЖНО: Всегда обновляем контент для замены плейсхолдеров
                    # Это удалит плейсхолдеры если нет изображений или заменит их на реальные URL
                    logger.info(f"Replacing placeholders for post {wp_post_id}")
                    updated_content = self._replace_image_placeholders(article['content'], article['article_id'])
                    
                    # Обновляем контент поста в WordPress только если контент изменился
                    if updated_content != article['content']:
                        if self._update_post_content(wp_post_id, updated_content):
                            logger.info(f"✅ Post {wp_post_id} content updated (placeholders processed)")
                        else:
                            logger.warning(f"⚠️ Failed to update post {wp_post_id} content")
                    else:
                        logger.info(f"No placeholders found in post {wp_post_id}, content unchanged")
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
    
    def _replace_image_placeholders(self, content: str, article_id: Optional[str]) -> str:
        """Replace [IMAGE_N] placeholders with actual HTML image tags
        
        Args:
            content: Article content with [IMAGE_N] placeholders
            article_id: Article ID to fetch images from database
            
        Returns:
            Content with placeholders replaced by HTML image tags
        """
        if not article_id:
            logger.warning("No article_id provided for placeholder replacement")
            return content
            
        # Check if content has placeholders
        import re
        placeholder_pattern = r'\[IMAGE_(\d+)\]'
        placeholders = re.findall(placeholder_pattern, content)
        
        if not placeholders:
            logger.info("No image placeholders found in content")
            return content
            
        logger.info(f"Found {len(placeholders)} image placeholders to replace")
        
        try:
            # Get images from database ordered by image_order
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        COALESCE(wp_source_url, url) as display_url,
                        alt_text,
                        image_order,
                        wp_media_id
                    FROM media_files
                    WHERE article_id = ?
                      AND image_order IS NOT NULL
                      AND image_order > 0
                      AND status = 'completed'
                    ORDER BY image_order
                """, (article_id,))
                
                images = cursor.fetchall()
                
                if not images:
                    logger.warning(f"No images with image_order found for article {article_id}")
                    # Remove placeholders if no images
                    content = re.sub(placeholder_pattern, '', content)
                    return content
                
                # Create mapping of order to image data
                image_map = {}
                for img in images:
                    image_map[str(img['image_order'])] = {
                        'display_url': img['display_url'],
                        'alt_text': img['alt_text'] or '',
                        'wp_media_id': img['wp_media_id']
                    }
                
                # Replace each placeholder
                def replace_placeholder(match):
                    order_num = match.group(1)
                    if order_num in image_map:
                        img_data = image_map[order_num]
                        # WordPress-compatible HTML format with proper class
                        wp_class = f"wp-image-{img_data['wp_media_id']}" if img_data['wp_media_id'] else "wp-image-auto"
                        html = f'''<figure class="wp-block-image size-large">
<img src="{img_data['display_url']}" alt="{img_data['alt_text']}" class="{wp_class}"/>
</figure>'''
                        logger.info(f"Replaced [IMAGE_{order_num}] with image")
                        return html
                    else:
                        logger.warning(f"No image found for [IMAGE_{order_num}]")
                        return ''  # Remove placeholder if no matching image
                
                # Replace all placeholders
                content = re.sub(placeholder_pattern, replace_placeholder, content)
                
                logger.info(f"Successfully replaced {len(images)} image placeholders")
                
        except Exception as e:
            logger.error(f"Error replacing image placeholders: {e}")
            # On error, remove all placeholders to avoid broken content
            content = re.sub(placeholder_pattern, '', content)
            
        return content
    
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
        
        # ИЗМЕНЕНО: Не заменяем плейсхолдеры здесь - оставляем их для последующей замены
        # после загрузки медиа в WordPress
        # content = self._replace_image_placeholders(article['content'], article.get('article_id'))
        content = article['content']  # Используем контент как есть, с плейсхолдерами [IMAGE_N]
        
        post_data = {
            'title': article['title'],
            'content': content,
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
        
        # Выбираем метод публикации в зависимости от настроек
        if self.config.use_custom_meta_endpoint:
            logger.info("Using Custom Post Meta Endpoint for publishing")
            return self._create_wordpress_post_via_custom_endpoint(post_data)
        else:
            logger.info("Using standard WordPress REST API for publishing")
            return self._create_wordpress_post_standard(post_data)
    
    def _create_wordpress_post_standard(self, post_data: Dict[str, Any]) -> Optional[int]:
        """Create a post in WordPress via standard REST API"""
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
    
    def _clean_text(self, text: str) -> str:
        """Просто очищает текст без ограничений длины"""
        if not text:
            return ""
        return text.strip()
    
    def _parse_json_field(self, field) -> list:
        """Парсит JSON поле из БД или возвращает как есть если уже список"""
        if isinstance(field, str):
            try:
                return json.loads(field)
            except (json.JSONDecodeError, TypeError):
                return []
        elif isinstance(field, list):
            return field
        else:
            return []
    
    def _create_wordpress_post_via_custom_endpoint(self, post_data: Dict[str, Any]) -> Optional[int]:
        """Create post via Custom Post Meta Endpoint plugin"""
        try:
            # Получаем meta данные
            meta = post_data.get('meta', {})
            
            # DEBUG: Проверяем что в meta
            logger.debug(f"Meta keys: {list(meta.keys())}")
            logger.debug(f"SEO title in meta: {meta.get('_yoast_wpseo_title', 'NOT FOUND')}")
            logger.debug(f"SEO desc in meta: {meta.get('_yoast_wpseo_metadesc', 'NOT FOUND')}")
            
            # DEBUG: Проверяем SEO поля
            if '_yoast_wpseo_title' in meta:
                seo_title = self._clean_text(meta.get('_yoast_wpseo_title', ''))
                logger.debug(f"SEO title: {seo_title[:50]}...")
            if '_yoast_wpseo_metadesc' in meta:
                seo_desc = self._clean_text(meta.get('_yoast_wpseo_metadesc', ''))
                logger.debug(f"SEO desc: {seo_desc[:50]}...")
            
            # Преобразуем формат данных для плагина
            custom_data = {
                'title': post_data['title'],
                'content': post_data['content'],
                'excerpt': post_data.get('excerpt', ''),
                'slug': post_data['slug'],
                'status': post_data.get('status', 'draft'),
                'categories': self._parse_json_field(post_data.get('categories', [])),
                'tags': self._parse_json_field(post_data.get('tags', [])),
                # SEO поля БЕЗ ОГРАНИЧЕНИЙ - простая очистка
                'seo_title': self._clean_text(meta.get('_yoast_wpseo_title', '')) if '_yoast_wpseo_title' in meta else None,
                'seo_description': self._clean_text(meta.get('_yoast_wpseo_metadesc', '')) if '_yoast_wpseo_metadesc' in meta else None,
                'focus_keyword': meta.get('_yoast_wpseo_focuskw')
            }
            
            # Убираем None значения для чистоты
            custom_data = {k: v for k, v in custom_data.items() if v is not None}
            
            # URL эндпоинта плагина
            url = "https://ailynx.ru/wp-json/custom-post-meta/v1/posts/"
            
            # Аутентификация
            auth = HTTPBasicAuth(self.config.wordpress_username, 
                               self.config.wordpress_app_password)
            
            # Заголовки с API ключом
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': self.config.custom_post_meta_api_key
            }
            
            logger.info(f"Sending request to Custom Post Meta Endpoint")
            logger.debug(f"Data: {custom_data}")
            
            # Отправка запроса
            response = requests.post(
                url,
                json=custom_data,
                auth=auth,
                headers=headers,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                post_id = result.get('post_id') or result.get('id')
                
                # Логируем полезную информацию из ответа
                if result.get('success'):
                    logger.info(f"Successfully created post via Custom Meta Endpoint: {post_id}")
                    logger.info(f"Post URL: {result.get('post_url', 'N/A')}")
                    
                    # Логируем SEO scores если есть
                    if 'seo_scores' in result:
                        seo = result['seo_scores']
                        if seo.get('yoast_available'):
                            logger.info(f"SEO Score: {seo.get('seo_score', 'N/A')}, Readability: {seo.get('readability_score', 'N/A')}")
                    
                    # Логируем какие мета-поля были установлены
                    if 'meta_fields_set' in result:
                        logger.info(f"Meta fields set: {', '.join(result['meta_fields_set'])}")
                
                return post_id
            else:
                logger.error(f"Custom Meta Endpoint error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating post via Custom Meta Endpoint: {str(e)}")
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
    
    def _update_post_content(self, wp_post_id: int, new_content: str) -> bool:
        """Обновляет контент существующего поста в WordPress
        
        Args:
            wp_post_id: ID поста в WordPress
            new_content: Новый контент с замененными плейсхолдерами
            
        Returns:
            True если обновление прошло успешно, иначе False
        """
        try:
            url = f"{self.config.wordpress_api_url}/posts/{wp_post_id}"
            auth = HTTPBasicAuth(self.config.wordpress_username, 
                               self.config.wordpress_app_password)
            
            # Подготавливаем данные для обновления
            update_data = {
                'content': new_content
            }
            
            logger.info(f"Updating content for WordPress post {wp_post_id}")
            
            # Отправляем запрос на обновление
            response = requests.post(  # WordPress REST API поддерживает POST для обновления
                url,
                json=update_data,
                auth=auth,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Successfully updated post {wp_post_id} content with local media URLs")
                return True
            else:
                logger.error(f"Failed to update post content: {response.status_code} - {response.text[:200]}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating post content for {wp_post_id}: {str(e)}")
            return False
    
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
                    # ОТКЛЮЧЕНО: Старая система вставки изображений
                    # Теперь используем систему меток [IMAGE_N] которые заменяются в _prepare_wordpress_post
                    # insert_result = self._insert_images_into_post(wp_post_id, article_id)
                    # if not insert_result:
                    #     logger.warning(f"Failed to insert images into post {wp_post_id}")
                    return True
                
                uploaded_media_ids = []
                
                for i, media in enumerate(media_files):
                    try:
                        # Пауза между медиафайлами (кроме первого)
                        if i > 0:
                            import time
                            logger.info("Waiting 3 seconds before next media file...")
                            time.sleep(3)
                        
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
                                    None  # No caption translation
                                )
                                uploaded_media_ids.append(wp_media_id)
                                logger.info(f"Successfully uploaded media {media['media_id']} as WP media {wp_media_id}")
                        
                    except Exception as e:
                        logger.error(f"Error processing media {media.get('media_id')}: {str(e)}")
                
                # ОТКЛЮЧЕНО: Старая система вставки изображений
                # Теперь изображения вставляются через метки [IMAGE_N] в _prepare_wordpress_post
                # if uploaded_media_ids:
                #     logger.info(f"Inserting {len(uploaded_media_ids)} images into post {wp_post_id}")
                #     insert_result = self._insert_images_into_post(wp_post_id, article_id)
                #     if not insert_result:
                #         logger.warning(f"Failed to insert images into post {wp_post_id}")
                
                if uploaded_media_ids:
                    logger.info(f"Successfully uploaded {len(uploaded_media_ids)} media files, images inserted via [IMAGE_N] placeholders")
                    
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
                                    None  # No caption translation
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
                
                # ОТКЛЮЧЕНО: Старая система вставки изображений  
                # Теперь изображения вставляются через метки [IMAGE_N] в _prepare_wordpress_post
                # if results['uploaded'] > 0:
                #     logger.info(f"Inserting images into post {article['wp_post_id']}")
                #     if self._insert_images_into_post(article['wp_post_id'], article['article_id']):
                #         logger.info(f"Successfully inserted images into post")
                #     else:
                #         logger.warning(f"Failed to insert images into post")
                
                if results['uploaded'] > 0:
                    logger.info(f"Successfully uploaded {results['uploaded']} images, inserted via [IMAGE_N] placeholders")
                
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
        """Translate media metadata using GPT-3.5 Turbo"""
        try:
            # Skip if no meaningful content to translate
            if not metadata.get('alt_text') and not metadata.get('caption'):
                logger.info("No metadata to translate, using defaults")
                return {
                    'alt_text_ru': metadata.get('article_title', 'Изображение'),
                    'slug': self._generate_slug(metadata.get('article_title', 'image'))
                }
            
            # Загружаем промпт из файла
            prompt = load_prompt('image_metadata',
                article_title=metadata.get('article_title', ''),
                alt_text=metadata.get('alt_text', '')
            )
            
            logger.debug(f"Translating metadata with prompt length: {len(prompt)}")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
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
    
    def _get_wordpress_media_url(self, wp_media_id: int) -> Optional[str]:
        """
        Получить WordPress URL для загруженного медиа файла
        
        Args:
            wp_media_id: ID медиа в WordPress
            
        Returns:
            WordPress URL (source_url) или None если не удалось получить
        """
        try:
            logger.info(f"🔗 Получение WordPress URL для медиа ID {wp_media_id}")
            
            # ВАЖНО: Добавляем авторизацию как в других WordPress запросах
            response = requests.get(
                f"{self.config.wordpress_api_url}/media/{wp_media_id}",
                auth=HTTPBasicAuth(
                    self.config.wordpress_username, 
                    self.config.wordpress_app_password
                ),
                timeout=30
            )
            
            logger.info(f"WordPress media API response: HTTP {response.status_code}")
            
            if response.status_code == 200:
                media_data = response.json()
                source_url = media_data.get('source_url')
                if source_url:
                    logger.info(f"✅ Получен WordPress URL для медиа {wp_media_id}: {source_url}")
                    return source_url
                else:
                    logger.warning(f"⚠️ Нет source_url в ответе для медиа {wp_media_id}. Ответ: {media_data}")
            elif response.status_code == 401:
                logger.error(f"❌ Ошибка авторизации при получении медиа {wp_media_id}: HTTP {response.status_code}")
            else:
                logger.error(f"❌ Ошибка получения медиа {wp_media_id}: HTTP {response.status_code}, текст: {response.text}")
                
        except Exception as e:
            logger.error(f"Error getting WordPress media URL: {str(e)}")
        
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
                
                # Update metadata - только alt_text и title
                update_data = {
                    'title': metadata['alt_text_ru'],      # Заголовок на русском
                    'alt_text': metadata['alt_text_ru'],   # Alt текст на русском
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
            # Получаем WordPress URL для загруженного медиа
            wp_source_url = None
            if wp_media_id:
                wp_source_url = self._get_wordpress_media_url(wp_media_id)
            
            with self.db.get_connection() as conn:
                conn.execute("""
                    UPDATE media_files
                    SET wp_media_id = ?,
                        wp_upload_status = 'uploaded',
                        wp_uploaded_at = ?,
                        alt_text_ru = ?,
                        wp_source_url = ?
                    WHERE id = ?
                """, (
                    wp_media_id,
                    datetime.now(),
                    alt_text_ru,
                    wp_source_url,
                    media_id
                ))
            logger.info(f"Saved upload result for media {media_id} with WP URL: {wp_source_url}")
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
                        m.alt_text_ru
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
                                    
                                    # Создаём простой HTML для картинки без подписи
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