#!/usr/bin/env python3
"""
Content Parser Service - Hybrid Scrape + DeepSeek AI parser
Uses Firecrawl Scrape API for raw content + DeepSeek AI for intelligent cleaning
Preserves anchor links and adds [IMAGE_N] placeholders
"""
import asyncio
import time
import json
import re
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from openai import OpenAI

from core.database import Database
from app_logging import get_logger
from .firecrawl_client import FirecrawlClient, FirecrawlError
from .prompts_loader import load_prompt


class ContentParser:
    """
    Clean content parser using FirecrawlClient service
    Handles article content extraction and database updates
    """
    
    def __init__(self):
        self.logger = get_logger('services.content_parser')
        self.db = Database()
        self.firecrawl_client = None
        
        # DeepSeek AI client for content cleaning
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        if self.deepseek_api_key:
            self.deepseek_client = OpenAI(
                api_key=self.deepseek_api_key,
                base_url="https://api.deepseek.com/v1"
            )
        else:
            self.logger.warning("DEEPSEEK_API_KEY not found, will use raw content")
            self.deepseek_client = None
        
        # Statistics
        self.stats = {
            'articles_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'database_saves': 0,
            'database_failures': 0,
            'deepseek_cleanings': 0,
            'deepseek_failures': 0
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.firecrawl_client = FirecrawlClient()
        await self.firecrawl_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.firecrawl_client:
            await self.firecrawl_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def _save_article_content(self, article_id: str, extracted_data: Dict[str, Any], source_id: str) -> bool:
        """
        Save extracted content to database
        
        Args:
            article_id: Article ID
            extracted_data: Data from Firecrawl Extract API
            source_id: Source ID for media tracking
            
        Returns:
            True if saved successfully
        """
        try:
            with self.db.get_connection() as conn:
                # Update article with extracted content
                update_data = {
                    'content': extracted_data.get('content', ''),
                    'content_status': 'parsed',
                    'parsed_at': datetime.now(timezone.utc).isoformat()
                }
                
                conn.execute("""
                    UPDATE articles SET
                        content = ?,
                        content_status = ?,
                        parsed_at = ?
                    WHERE article_id = ?
                """, (
                    update_data['content'],
                    update_data['content_status'],
                    update_data['parsed_at'],
                    article_id
                ))
                
                # Save media files using proper database method
                images = extracted_data.get('images', [])
                media_count = 0
                
                for img in images[:5]:  # Limit to 5 images max
                    if img.get('url'):
                        try:
                            # Insert media directly in the same connection to avoid database lock
                            media_id = Database.generate_media_id(article_id, img['url'])
                            conn.execute("""
                                INSERT OR IGNORE INTO media_files (
                                    media_id, article_id, source_id, url, type,
                                    alt_text, caption, status, created_at, image_order
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
                            """, (
                                media_id,
                                article_id,
                                source_id,
                                img['url'],
                                'image',
                                img.get('alt_text'),
                                img.get('caption'),
                                datetime.now(timezone.utc).isoformat(),
                                img.get('order', media_count + 1)  # Use order from DeepSeek or fallback
                            ))
                            if conn.total_changes > 0:
                                media_count += 1
                        except Exception as e:
                            self.logger.warning(f"Failed to save media {img['url']}: {e}")
                
                # Update media count and media_status
                if media_count > 0:
                    # Есть медиафайлы - ставим статус 'processing' (будет обрабатываться в Phase 3)
                    media_status = 'processing'
                else:
                    # Нет медиафайлов - готово к Phase 4
                    media_status = 'ready'
                
                conn.execute("""
                    UPDATE articles SET media_count = ?, media_status = ? WHERE article_id = ?
                """, (media_count, media_status, article_id))
                
                self.stats['database_saves'] += 1
                self.logger.info(f"Saved content for {article_id}: "
                              f"content={len(update_data['content'])} chars, "
                              f"media={media_count}")
                
                return True
                
        except Exception as e:
            self.stats['database_failures'] += 1
            self.logger.error(f"Failed to save content for {article_id}: {e}")
            return False
    
    def _mark_article_failed(self, article_id: str, error_message: str):
        """Mark article as failed in database"""
        try:
            with self.db.get_connection() as conn:
                conn.execute("""
                    UPDATE articles SET
                        content_status = 'failed',
                        content_error = ?,
                        parsed_at = ?
                    WHERE article_id = ?
                """, (error_message, datetime.now(timezone.utc).isoformat(), article_id))
                
        except Exception as e:
            self.logger.error(f"Failed to mark article {article_id} as failed: {e}")
    
    async def _clean_content_with_deepseek(self, raw_markdown: str, url: str) -> Dict[str, Any]:
        """Clean content with DeepSeek AI and add image placeholders"""
        if not self.deepseek_client:
            self.logger.warning("DeepSeek client not available, returning raw content")
            return {
                'content': raw_markdown,
                'images': [],
                'success': True
            }
        
        
        # Загружаем промпт из файла
        system_prompt = load_prompt('content_cleaner')
        
        user_prompt = f"""URL: {url}

Очисти этот контент, оставив только основную статью:

{raw_markdown[:10000]}"""  # Limit to 10k chars to avoid token limits
        
        # Log start of DeepSeek content cleaning - only when actually starting API call
        from app_logging import log_operation
        log_operation('DeepSeek (1/3) начинает очистку контента...',
            model='deepseek-chat',
            processing_stage='content_cleaning',
            phase='content_parsing',
            retry_attempt=1,
            max_attempts=3,
            url=url[:100]
        )
        
        start_time = time.time()
        try:
            response = self.deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4000,
                temperature=0.1,
                timeout=60
            )
            
            raw_response = response.choices[0].message.content.strip()
            processing_time = time.time() - start_time
            
            # Parse JSON response (remove markdown wrapper if present)
            json_text = raw_response
            if raw_response.startswith('```json'):
                lines = raw_response.split('\n')
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip() == '```json':
                        in_json = True
                        continue
                    elif line.strip() == '```' and in_json:
                        break
                    elif in_json:
                        json_lines.append(line)
                json_text = '\n'.join(json_lines)
            
            json_response = json.loads(json_text)
            
            # Check content length (300 words minimum to prevent paywall/empty articles)
            content = json_response.get('content', '')
            word_count = len(content.split()) if content else 0
            
            if word_count < 300:
                self.stats['deepseek_failures'] += 1
                self.logger.warning(f"Content too short: {word_count} words < 300 minimum. Likely paywall content.")
                
                # Log failed content cleaning (too short)
                from app_logging import log_operation
                tokens_input = len(system_prompt + user_prompt) // 4
                tokens_output = len(raw_response) // 4
                cost_usd = (tokens_input * 0.14 + tokens_output * 0.28) / 1_000_000
                log_operation(f'❌ DeepSeek (1/3) контент слишком короткий: {word_count} слов < 300 минимум',
                    model='deepseek-chat',
                    tokens_input=tokens_input,
                    tokens_output=tokens_output,
                    tokens_approx=tokens_input + tokens_output,
                    cost_usd=cost_usd,
                    success=False,
                    retry_attempt=1,
                    max_attempts=3,
                    processing_stage='content_cleaning',
                    content_length=len(raw_markdown),
                    word_count=word_count,
                    duration_seconds=processing_time,
                    url=url[:100],  # Truncate URL for logging
                    failure_reason='content_too_short'
                )
                
                return {
                    'content': content,
                    'images': json_response.get('images', []),
                    'success': False,
                    'error': f'Content too short: {word_count} words < 300 minimum'
                }
            
            self.stats['deepseek_cleanings'] += 1
            self.logger.info(f"DeepSeek cleaned content: {len(content)} chars, {word_count} words, "
                           f"{len(json_response.get('images', []))} images")
            
            # Log successful content cleaning
            from app_logging import log_operation
            tokens_input = len(system_prompt + user_prompt) // 4
            tokens_output = len(raw_response) // 4
            cost_usd = (tokens_input * 0.14 + tokens_output * 0.28) / 1_000_000
            images_count = len(json_response.get('images', []))
            log_operation(f'✅ DeepSeek (1/3) очистил контент: {word_count} слов, {images_count} изображений ({tokens_input + tokens_output} токенов)',
                model='deepseek-chat',
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                tokens_approx=tokens_input + tokens_output,
                cost_usd=cost_usd,
                success=True,
                retry_attempt=1,
                max_attempts=3,
                processing_stage='content_cleaning',
                content_length=len(raw_markdown),
                word_count=word_count,
                duration_seconds=processing_time,
                url=url[:100],  # Truncate URL for logging
                images_found=images_count
            )
            
            return {
                'content': content,
                'images': json_response.get('images', []),
                'success': True
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.stats['deepseek_failures'] += 1
            self.logger.error(f"DeepSeek cleaning failed: {e}")
            
            # Log failed content cleaning (exception)
            from app_logging import log_operation
            fallback_reason = 'timeout' if 'timeout' in str(e).lower() else \
                            'json_parse_error' if 'json' in str(e).lower() else \
                            'api_error'
            log_operation(f'❌ DeepSeek (1/3) ошибка очистки: {fallback_reason}',
                model='deepseek-chat',
                success=False,
                retry_attempt=1,
                max_attempts=3,
                processing_stage='content_cleaning',
                content_length=len(raw_markdown),
                duration_seconds=processing_time,
                url=url[:100],  # Truncate URL for logging
                fallback_reason=fallback_reason,
                error_message=str(e)[:200]  # Truncate error message
            )
            
            # Return raw content on failure
            return {
                'content': raw_markdown,
                'images': [],
                'success': False,
                'error': str(e)
            }
    
    def _extract_real_url(self, url: str) -> str:
        """Extract real URL from Google redirect"""
        import urllib.parse as urlparse
        
        # Check if it's a Google redirect URL
        if 'google.com/url?' in url and 'url=' in url:
            try:
                # Parse the URL parameters
                parsed = urlparse.urlparse(url)
                params = urlparse.parse_qs(parsed.query)
                
                # Extract the real URL from 'url' parameter
                if 'url' in params:
                    real_url = params['url'][0]
                    self.logger.info(f"Extracted real URL: {real_url} from redirect: {url[:100]}...")
                    return real_url
            except Exception as e:
                self.logger.warning(f"Failed to extract real URL from {url}: {e}")
        
        return url

    async def parse_article(self, article_id: str, url: str, source_id: str) -> Dict[str, Any]:
        """
        Parse a single article using Firecrawl Extract API
        
        Args:
            article_id: Article ID
            url: Article URL (may be Google redirect)
            source_id: Source ID
            
        Returns:
            Parsing result with success status and metadata
        """
        start_time = time.time()
        self.stats['articles_processed'] += 1
        
        # Extract real URL from Google redirects
        real_url = self._extract_real_url(url)
        
        self.logger.info(f"Starting content extraction for: {real_url}")
        
        try:
            # Check if firecrawl client is initialized
            if not self.firecrawl_client:
                raise Exception("FirecrawlClient not initialized. Use async context manager.")
            
            # Log Firecrawl start
            from app_logging import log_operation
            log_operation('Firecrawl начинает извлечение контента...',
                phase='content_parsing',
                processing_stage='content_extraction',
                url=real_url[:100]
            )
            
            # Use SCRAPE instead of extract to get raw markdown
            scrape_result = await self.firecrawl_client.scrape_with_retry(real_url)
            
            # Get raw markdown content
            raw_markdown = scrape_result.get('markdown', '')
            if not raw_markdown:
                raise Exception("No markdown content from scrape")
            
            # Log successful Firecrawl completion
            log_operation(f'✅ Firecrawl извлек {len(raw_markdown)} символов markdown контента',
                phase='content_parsing',
                processing_stage='content_extraction',
                success=True,
                content_length=len(raw_markdown),
                url=real_url[:100]
            )
            
            # DeepSeek will log its own status when actually starting
            
            # Clean content with DeepSeek AI and add image placeholders
            cleaned_data = await self._clean_content_with_deepseek(raw_markdown, url)
            
            # Check if content cleaning was successful (not too short/paywall)
            if not cleaned_data.get('success', False):
                error_message = cleaned_data.get('error', 'Content cleaning failed')
                raise Exception(error_message)
            
            # Prepare data for saving
            extracted_data = {
                'content': cleaned_data['content'],
                'images': cleaned_data.get('images', []),
                'metadata': scrape_result.get('metadata', {})
            }
            
            # Save to database
            save_success = await self._save_article_content(article_id, extracted_data, source_id)
            
            if not save_success:
                raise Exception("Failed to save extracted data to database")
            
            processing_time = time.time() - start_time
            self.stats['successful_extractions'] += 1
            
            result = {
                "success": True,
                "article_id": article_id,
                "url": url,
                "processing_time": processing_time,
                "content_length": len(extracted_data.get('content', '')),
                "media_count": len(extracted_data.get('images', []))
            }
            
            self.logger.info(f"Successfully parsed article in {processing_time:.1f}s: "
                          f"content={result['content_length']} chars, "
                          f"media={result['media_count']}")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.stats['failed_extractions'] += 1
            
            error_message = str(e)
            self.logger.error(f"Failed to parse article {article_id} in {processing_time:.1f}s: {error_message}")
            
            # Mark article as failed in database
            self._mark_article_failed(article_id, error_message)
            
            return {
                "success": False,
                "article_id": article_id,
                "url": url,
                "error": error_message,
                "processing_time": processing_time
            }
    
    async def parse_single_article(self, article_id: str, url: str, source_id: str) -> Dict[str, Any]:
        """
        Alias for parse_article - for compatibility with the calling code
        
        Args:
            article_id: Article ID
            url: Article URL
            source_id: Source ID
            
        Returns:
            Parsing result with success status and metadata
        """
        return await self.parse_article(article_id, url, source_id)
    
    def get_pending_articles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get articles pending content extraction
        
        Args:
            limit: Maximum number of articles to return
            
        Returns:
            List of articles pending extraction
        """
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT article_id, url, source_id, title
                    FROM articles 
                    WHERE content_status = 'pending'
                    ORDER BY published_date DESC
                    LIMIT ?
                """, (limit,))
                
                articles = []
                for row in cursor.fetchall():
                    articles.append({
                        'article_id': row[0],
                        'url': row[1],
                        'source_id': row[2],
                        'title': row[3]
                    })
                
                return articles
                
        except Exception as e:
            self.logger.error(f"Failed to get pending articles: {e}")
            return []
    
    async def process_pending_articles(self, batch_size: int = 10, max_articles: Optional[int] = None) -> Dict[str, Any]:
        """
        Process pending articles in batches
        
        Args:
            batch_size: Number of articles to process in each batch
            max_articles: Maximum total articles to process (None for all)
            
        Returns:
            Processing summary statistics
        """
        total_processed = 0
        total_successful = 0
        total_failed = 0
        
        self.logger.info(f"Starting batch processing: batch_size={batch_size}, max_articles={max_articles}")
        
        while True:
            # Get next batch of pending articles
            remaining = None if max_articles is None else max_articles - total_processed
            current_batch_size = min(batch_size, remaining) if remaining is not None else batch_size
            
            if current_batch_size <= 0:
                break
            
            pending_articles = self.get_pending_articles(current_batch_size)
            
            if not pending_articles:
                self.logger.info("No more pending articles found")
                break
            
            self.logger.info(f"Processing batch of {len(pending_articles)} articles")
            
            # Process articles in current batch (sequentially to avoid rate limits)
            for article in pending_articles:
                result = await self.parse_article(
                    article['article_id'],
                    article['url'],
                    article['source_id']
                )
                
                if result['success']:
                    total_successful += 1
                else:
                    total_failed += 1
                
                total_processed += 1
                
                # Add small delay between articles to respect rate limits
                await asyncio.sleep(1.0)
            
            # Check if we've reached the limit
            if max_articles and total_processed >= max_articles:
                break
        
        summary = {
            'total_processed': total_processed,
            'successful': total_successful,
            'failed': total_failed,
            'success_rate': (total_successful / max(1, total_processed)) * 100
        }
        
        self.logger.info(f"Completed batch processing: {summary}")
        return summary
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get content parser statistics"""
        firecrawl_stats = {}
        if self.firecrawl_client:
            firecrawl_stats = self.firecrawl_client.get_statistics()
        
        return {
            'parser_stats': self.stats.copy(),
            'firecrawl_stats': firecrawl_stats
        }
    
    def reset_statistics(self):
        """Reset statistics"""
        self.stats = {
            'articles_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'database_saves': 0,
            'database_failures': 0
        }
        
        if self.firecrawl_client:
            self.firecrawl_client.reset_statistics()


# Convenience functions
async def parse_single_article(article_id: str, url: str, source_id: str) -> Dict[str, Any]:
    """
    Convenience function to parse a single article
    
    Args:
        article_id: Article ID
        url: Article URL
        source_id: Source ID
        
    Returns:
        Parsing result
    """
    async with ContentParser() as parser:
        return await parser.parse_article(article_id, url, source_id)


async def process_pending_articles(batch_size: int = 10, max_articles: Optional[int] = None) -> Dict[str, Any]:
    """
    Convenience function to process pending articles
    
    Args:
        batch_size: Batch size for processing
        max_articles: Maximum articles to process
        
    Returns:
        Processing summary
    """
    async with ContentParser() as parser:
        return await parser.process_pending_articles(batch_size, max_articles)