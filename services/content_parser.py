#!/usr/bin/env python3
"""
Content Parser Service - Clean Extract API parser
Uses FirecrawlClient service for content extraction
Simplified and optimized for the new clean architecture
"""
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from core.database import Database
from app_logging import get_logger
from .firecrawl_client import FirecrawlClient, FirecrawlError


class ContentParser:
    """
    Clean content parser using FirecrawlClient service
    Handles article content extraction and database updates
    """
    
    def __init__(self):
        self.logger = get_logger('services.content_parser')
        self.db = Database()
        self.firecrawl_client = None
        
        # Statistics
        self.stats = {
            'articles_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'database_saves': 0,
            'database_failures': 0
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
                
                for img in images:
                    if img.get('url'):
                        try:
                            # Use database insert_media method that includes source_id
                            media_data = {
                                'article_id': article_id,
                                'source_id': source_id,
                                'url': img['url'],
                                'type': 'image',
                                'alt_text': img.get('alt_text'),
                                'caption': img.get('caption')
                            }
                            media_id = self.db.insert_media(media_data)
                            if media_id:
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
    
    async def parse_article(self, article_id: str, url: str, source_id: str) -> Dict[str, Any]:
        """
        Parse a single article using Firecrawl Extract API
        
        Args:
            article_id: Article ID
            url: Article URL
            source_id: Source ID
            
        Returns:
            Parsing result with success status and metadata
        """
        start_time = time.time()
        self.stats['articles_processed'] += 1
        
        self.logger.info(f"Starting content extraction for: {url}")
        
        try:
            # Check if firecrawl client is initialized
            if not self.firecrawl_client:
                raise Exception("FirecrawlClient not initialized. Use async context manager.")
            
            # Extract content using FirecrawlClient
            extracted_data = await self.firecrawl_client.extract_with_retry(url)
            
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