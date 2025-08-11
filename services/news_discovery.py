#!/usr/bin/env python3
"""
News Discovery Service
Использует Firecrawl Crawl API для эффективного обнаружения новых статей на новостных сайтах
"""

import asyncio
import hashlib
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse, urljoin
import uuid

from app_logging import get_logger
from core.database import Database
from services.firecrawl_client import FirecrawlClient


def generate_id() -> str:
    """Generate a unique ID for articles"""
    return str(uuid.uuid4())[:8]


class NewsDiscoveryService:
    """
    Сервис для обнаружения новых статей на новостных сайтах
    Использует Crawl API для эффективного сканирования
    """
    
    def __init__(self):
        self.logger = get_logger('services.news_discovery')
        self.db = Database()
        self.firecrawl = FirecrawlClient()
        
    def _generate_hash(self, content: str) -> str:
        """Generate hash for content comparison"""
        if not content:
            return ""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _extract_title(self, page_data: Dict) -> str:
        """Extract title from page data"""
        # Try different fields where title might be
        if page_data.get('title'):
            return page_data['title']
        
        # Try to extract from markdown content
        content = page_data.get('markdown', '')
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        
        # Fallback to URL
        url = page_data.get('url', '')
        return urlparse(url).path.strip('/').replace('-', ' ').replace('_', ' ').title()
    
    async def discover_news(
        self,
        source_url: str,
        limit: int = 20,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        max_depth: Optional[int] = 2
    ) -> Dict[str, Any]:
        """
        Обнаруживает новые статьи на новостном сайте
        
        Args:
            source_url: URL новостного раздела (например, https://openai.com/news/)
            limit: Максимальное количество страниц для сканирования
            include_paths: Пути для включения (например, ["/news/*", "/blog/*"])
            exclude_paths: Пути для исключения (например, ["/tag/*", "/author/*"])
            max_depth: Максимальная глубина сканирования
            
        Returns:
            Dict с результатами:
                - new_articles: Список новых найденных статей
                - existing_articles: Список уже отслеживаемых статей
                - total_crawled: Общее количество просканированных страниц
                - errors: Список ошибок
        """
        self.logger.info(f"Starting news discovery for: {source_url}")
        
        results = {
            'source_url': source_url,
            'new_articles': [],
            'existing_articles': [],
            'total_crawled': 0,
            'errors': [],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Определяем паттерны для новостей если не указаны
            if not include_paths:
                # Автоматически определяем паттерны на основе URL
                parsed = urlparse(source_url)
                path = parsed.path.strip('/')
                
                # Общие паттерны для новостных сайтов
                common_patterns = [
                    f"/{path}/*" if path else "/*",
                    "/blog/*",
                    "/posts/*",
                    "/articles/*",
                    "/*/2024/*",
                    "/*/2025/*"
                ]
                include_paths = common_patterns
                self.logger.debug(f"Auto-generated include paths: {include_paths}")
            
            # Исключаем служебные страницы
            if not exclude_paths:
                exclude_paths = [
                    "/tag/*",
                    "/tags/*",
                    "/category/*",
                    "/author/*",
                    "/page/*",
                    "/search/*",
                    "/about",
                    "/contact",
                    "/privacy",
                    "/terms"
                ]
            
            start_time = time.time()
            async with self.firecrawl as client:
                # Используем Crawl API для обнаружения всех страниц
                self.logger.info(f"Crawling {source_url} with limit={limit}")
                
                crawl_result = await client.crawl_website(
                    url=source_url,
                    limit=limit,
                    max_depth=max_depth,
                    include_paths=include_paths,
                    exclude_paths=exclude_paths
                )
                
                if not crawl_result.get('success'):
                    raise Exception(f"Crawl failed: {crawl_result}")
                
                pages = crawl_result.get('urls', [])
                results['total_crawled'] = len(pages)
                crawl_time = time.time() - start_time
                
                self.logger.info(f"Crawl found {len(pages)} pages in {crawl_time:.1f}s")
                
                # Log successful crawl operation
                from app_logging import log_operation
                log_operation('firecrawl_crawl',
                    source_url=source_url[:100],  # Truncate URL
                    pages_found=len(pages),
                    crawl_limit=limit,
                    max_depth=max_depth,
                    duration_seconds=crawl_time,
                    success=True,
                    # Firecrawl crawl cost estimation (rough)
                    cost_usd=len(pages) * 0.002  # ~$0.002 per page crawled
                )
                
                # Получаем источник из URL
                source_id = urlparse(source_url).netloc.replace('.', '_').replace('www', '')
                
                # Проверяем каждую найденную страницу
                for page_data in pages:
                    try:
                        page_url = page_data.get('url', '')
                        
                        # Пропускаем главную страницу
                        if page_url == source_url or page_url == source_url.rstrip('/'):
                            continue
                        
                        # Проверяем, отслеживаем ли уже эту статью
                        with self.db.get_connection() as conn:
                            cursor = conn.execute(
                                "SELECT article_id, current_hash FROM tracked_articles WHERE url = ?",
                                (page_url,)
                            )
                            existing = cursor.fetchone()
                        
                        # Извлекаем контент
                        content = page_data.get('markdown', '')
                        content_hash = self._generate_hash(content)
                        title = self._extract_title(page_data)
                        
                        if existing:
                            # Статья уже отслеживается
                            article_id, old_hash = existing
                            
                            # Проверяем изменения
                            if old_hash != content_hash:
                                # Контент изменился
                                with self.db.get_connection() as conn:
                                    conn.execute("""
                                        UPDATE tracked_articles 
                                        SET previous_hash = current_hash,
                                            current_hash = ?,
                                            content = ?,
                                            title = ?,
                                            change_detected = 1,
                                            change_status = 'changed',
                                            last_checked = ?,
                                            updated_at = CURRENT_TIMESTAMP
                                        WHERE article_id = ?
                                    """, (
                                        content_hash, content, title,
                                        datetime.now(timezone.utc).isoformat(),
                                        article_id
                                    ))
                                
                                self.logger.info(f"Content changed: {title[:60]}")
                            
                            results['existing_articles'].append({
                                'article_id': article_id,
                                'url': page_url,
                                'title': title,
                                'changed': old_hash != content_hash
                            })
                        else:
                            # Новая статья!
                            article_id = generate_id()
                            
                            # Сохраняем в tracked_articles
                            with self.db.get_connection() as conn:
                                conn.execute("""
                                    INSERT INTO tracked_articles (
                                        article_id, source_id, url, title,
                                        content, current_hash, change_detected,
                                        change_status, last_checked, published_date,
                                        created_at
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                                """, (
                                    article_id, source_id, page_url, title,
                                    content, content_hash, 1, 'new',
                                    datetime.now(timezone.utc).isoformat(),
                                    datetime.now(timezone.utc).isoformat()
                                ))
                            
                            results['new_articles'].append({
                                'article_id': article_id,
                                'url': page_url,
                                'title': title,
                                'source_id': source_id,
                                'content_preview': content[:500] if content else ''
                            })
                            
                            self.logger.info(f"NEW article discovered: {title[:60]}")
                            
                    except Exception as e:
                        self.logger.warning(f"Error processing page {page_data.get('url', 'unknown')}: {e}")
                        results['errors'].append({
                            'url': page_data.get('url', 'unknown'),
                            'error': str(e)
                        })
                
                # Логируем результаты
                total_time = time.time() - start_time
                self.logger.info(f"Discovery completed: {len(results['new_articles'])} new, "
                               f"{len(results['existing_articles'])} existing in {total_time:.1f}s")
                
                # Log discovery completion
                from app_logging import log_operation
                log_operation('news_discovery',
                    source_url=source_url[:100],  # Truncate URL
                    pages_crawled=results['total_crawled'],
                    new_articles=len(results['new_articles']),
                    existing_articles=len(results['existing_articles']),
                    changed_articles=len([a for a in results['existing_articles'] if a.get('status') == 'changed']),
                    errors_count=len(results['errors']),
                    duration_seconds=total_time,
                    success=True
                )
                
        except Exception as e:
            total_time = time.time() - start_time if 'start_time' in locals() else 0
            self.logger.error(f"Error during news discovery: {e}")
            results['errors'].append({
                'error': f"Discovery failed: {str(e)}",
                'source': source_url
            })
            
            # Log failed discovery
            from app_logging import log_operation
            failure_reason = 'crawl_failed' if 'crawl' in str(e).lower() else \
                           'firecrawl_error' if 'firecrawl' in str(e).lower() else \
                           'database_error' if 'database' in str(e).lower() else \
                           'discovery_error'
            
            log_operation('news_discovery',
                source_url=source_url[:100],  # Truncate URL
                duration_seconds=total_time,
                success=False,
                failure_reason=failure_reason,
                error_message=str(e)[:200]  # Truncate error
            )
        
        return results
    
    async def discover_multiple_sources(
        self,
        source_urls: List[str],
        limit_per_source: int = 10
    ) -> Dict[str, Any]:
        """
        Обнаруживает новости с нескольких источников параллельно
        
        Args:
            source_urls: Список URL новостных сайтов
            limit_per_source: Лимит страниц на источник
            
        Returns:
            Сводные результаты по всем источникам
        """
        start_time = time.time()
        self.logger.info(f"Starting discovery for {len(source_urls)} sources")
        
        overall_results = {
            'total_sources': len(source_urls),
            'total_new_articles': 0,
            'total_existing_articles': 0,
            'total_errors': 0,
            'sources': []
        }
        
        # Создаем задачи для параллельного выполнения
        tasks = []
        for url in source_urls:
            tasks.append(self.discover_news(url, limit=limit_per_source))
        
        # Выполняем параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error discovering {source_urls[i]}: {result}")
                overall_results['total_errors'] += 1
                overall_results['sources'].append({
                    'url': source_urls[i],
                    'status': 'error',
                    'error': str(result)
                })
            else:
                overall_results['total_new_articles'] += len(result.get('new_articles', []))
                overall_results['total_existing_articles'] += len(result.get('existing_articles', []))
                overall_results['total_errors'] += len(result.get('errors', []))
                overall_results['sources'].append(result)
        
        total_time = time.time() - start_time
        self.logger.info(f"Discovery completed: {overall_results['total_new_articles']} new articles total in {total_time:.1f}s")
        
        # Log multiple sources discovery completion
        from app_logging import log_operation
        log_operation('news_discovery_multiple',
            sources_count=len(source_urls),
            sources_successful=len([s for s in overall_results['sources'] if s.get('new_articles', 0) >= 0]),
            sources_failed=overall_results['total_errors'],
            total_new_articles=overall_results['total_new_articles'],
            total_existing_articles=overall_results['total_existing_articles'],
            duration_seconds=total_time,
            success=overall_results['total_errors'] < len(source_urls) / 2  # Success if <50% failed
        )
        
        return overall_results
    
    def get_discovery_stats(self) -> Dict[str, Any]:
        """Получает статистику по обнаруженным статьям"""
        stats = {}
        
        with self.db.get_connection() as conn:
            # Всего в tracked_articles
            cursor = conn.execute("SELECT COUNT(*) FROM tracked_articles")
            stats['total_tracked'] = cursor.fetchone()[0]
            
            # Новые статьи (не экспортированные)
            cursor = conn.execute("""
                SELECT COUNT(*) FROM tracked_articles 
                WHERE change_status = 'new' AND exported_to_main = 0
            """)
            stats['new_pending_export'] = cursor.fetchone()[0]
            
            # По источникам
            cursor = conn.execute("""
                SELECT source_id, COUNT(*) as cnt 
                FROM tracked_articles 
                GROUP BY source_id 
                ORDER BY cnt DESC
                LIMIT 10
            """)
            stats['top_sources'] = dict(cursor.fetchall())
            
            # Последние обнаруженные
            cursor = conn.execute("""
                SELECT url, title, created_at 
                FROM tracked_articles 
                WHERE change_status = 'new'
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            stats['latest_discoveries'] = [
                {'url': row[0], 'title': row[1], 'created': row[2]}
                for row in cursor.fetchall()
            ]
        
        return stats