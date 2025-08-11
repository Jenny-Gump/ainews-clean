#!/usr/bin/env python3
"""
Change Monitor
Отслеживание изменений на веб-страницах через Firecrawl changeTracking API
"""
import asyncio
import hashlib
import uuid
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse
from pathlib import Path
import time

from app_logging import get_logger
from services.firecrawl_client import FirecrawlClient
from .database import ChangeTrackingDB
from .url_extractor import URLExtractor


def generate_id() -> str:
    """Generate a unique ID for articles"""
    return str(uuid.uuid4())[:8]


class ChangeMonitor:
    """Мониторинг изменений на веб-страницах"""
    
    def __init__(self):
        self.logger = get_logger('change_tracking.monitor')
        self.db = ChangeTrackingDB()
        self.firecrawl = FirecrawlClient()
        self.url_extractor = URLExtractor()
        self.sources_file = Path(__file__).parent / 'sources.txt'
        self.tracking_sources = self._load_tracking_sources()
        
    def _load_tracking_sources(self) -> Dict[str, str]:
        """Load tracking sources from JSON file to map URLs to source IDs"""
        sources_map = {}
        json_file = Path(__file__).parent.parent / 'data' / 'tracking_sources.json'
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for source in data.get('tracking_sources', []):
                    # Map URL to source_id
                    sources_map[source['url']] = source['source_id']
                    # Also map without trailing slash
                    sources_map[source['url'].rstrip('/')] = source['source_id']
            self.logger.info(f"Loaded {len(sources_map)} tracking sources from JSON")
        except Exception as e:
            self.logger.warning(f"Could not load tracking sources: {e}")
        
        return sources_map
        
    def _generate_hash(self, content: str) -> str:
        """Generate hash for content comparison"""
        if not content:
            return ""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _extract_title(self, markdown_content: str, url: str) -> str:
        """Extract title from markdown content"""
        lines = markdown_content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        # Fallback to URL-based title
        return urlparse(url).path.strip('/').replace('-', ' ').replace('_', ' ').title() or 'Page Title'
    
    def _get_source_id(self, url: str) -> str:
        """Get source_id from tracking_sources.json mapping, fallback to domain-based"""
        # First try to find in loaded sources map
        clean_url = url.rstrip('/')
        if clean_url in self.tracking_sources:
            return self.tracking_sources[clean_url]
        
        # Fallback to domain-based ID (for backward compatibility)
        domain = urlparse(url).netloc.replace('.', '_')
        if domain.startswith('www_'):
            domain = domain[4:]
        return domain
    
    async def scan_webpage(self, url: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Сканирует веб-страницу и отслеживает изменения с retry механизмом
        
        Args:
            url: URL веб-страницы для мониторинга
            max_retries: Максимальное количество попыток при ошибках
            
        Returns:
            Dict с результатами мониторинга
        """
        # Log to operations.jsonl that we're scanning this specific source
        from app_logging import log_operation
        source_id = self._get_source_id(url)
        domain = urlparse(url).netloc
        
        log_operation(
            'change_tracking_source_start',
            phase='change_tracking',
            message=f'🔍 Scanning: {domain}',
            source_id=source_id,
            url=url,
            success=True
        )
        
        for attempt in range(max_retries):
            self.logger.info(f"Scanning webpage: {url}" + 
                           (f" (attempt {attempt + 1}/{max_retries})" if attempt > 0 else ""))
            
            result = await self._scan_webpage_single(url)
            
            # Если успешно или не API ошибка - возвращаем результат
            if result['status'] != 'error' or not self._is_retryable_error(result.get('error', '')):
                # Log the result for this source
                if result['status'] == 'changed':
                    log_operation(
                        'change_tracking_source_changed',
                        phase='change_tracking',
                        message=f'✅ Changed: {domain} ({result.get("extracted_urls", 0)} new URLs)',
                        source_id=source_id,
                        url=url,
                        urls_found=result.get('extracted_urls', 0),
                        success=True
                    )
                elif result['status'] == 'new':
                    log_operation(
                        'change_tracking_source_new',
                        phase='change_tracking',
                        message=f'🆕 New source tracked: {domain}',
                        source_id=source_id,
                        url=url,
                        success=True
                    )
                elif result['status'] == 'unchanged':
                    log_operation(
                        'change_tracking_source_unchanged',
                        phase='change_tracking',
                        message=f'⏸️ No changes: {domain}',
                        source_id=source_id,
                        url=url,
                        success=True
                    )
                return result
            
            # Если не последняя попытка - ждем перед следующей
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 5  # Exponential backoff: 5s, 10s, 20s
                self.logger.warning(f"Retrying {url} in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
        
        # Если все попытки неудачны
        self.logger.error(f"Failed to scan {url} after {max_retries} attempts")
        log_operation(
            'change_tracking_source_error',
            phase='change_tracking',
            message=f'❌ Error scanning: {domain}',
            source_id=source_id,
            url=url,
            error=result.get('error', 'Unknown error'),
            success=False
        )
        return result
    
    def _is_retryable_error(self, error_msg: str) -> bool:
        """Check if error is retryable (timeouts, server errors)"""
        retryable_keywords = ['408', 'timeout', '500', '502', '503', '504', 'connection', 'network']
        error_lower = error_msg.lower()
        return any(keyword in error_lower for keyword in retryable_keywords)
    
    async def _scan_webpage_single(self, url: str) -> Dict[str, Any]:
        """Single attempt to scan webpage without retry logic"""
        result = {
            'url': url,
            'status': None,
            'change_detected': False,
            'error': None,
            'article_id': None
        }
        
        try:
            # Add realistic delay for each source scan
            await asyncio.sleep(8)  # Each source takes 8-15 seconds to scan
            
            async with self.firecrawl as client:
                # Скрейпим страницу с changeTracking
                scraped_data = await client.scrape_url(
                    url,
                    formats=['markdown', 'changeTracking']
                )
                
                # Извлекаем данные
                markdown_content = scraped_data.get('markdown', '')
                change_tracking = scraped_data.get('changeTracking', {})
                change_status = change_tracking.get('changeStatus', 'unknown')
                
                # Генерируем хэш контента
                content_hash = self._generate_hash(markdown_content)
                
                # Извлекаем source_id из URL
                source_id = self._get_source_id(url)
                
                # Проверяем существование в БД
                existing = self.db.get_tracked_article_by_url(url)
                
                if change_status == 'new' or not existing:
                    # Новая страница
                    article_id = existing['article_id'] if existing else generate_id()
                    title = self._extract_title(markdown_content, url)
                    
                    if not existing:
                        # Создаем новую запись
                        success = self.db.create_tracked_article(
                            article_id=article_id,
                            source_id=source_id,
                            url=url,
                            title=title,
                            content=markdown_content,
                            content_hash=content_hash
                        )
                        
                        if not success:
                            raise Exception("Failed to create tracked article")
                    
                    # При первом сканировании сохраняем базовый список URL для будущих сравнений
                    try:
                        extracted_urls = self.url_extractor.extract_urls_from_content(markdown_content, url)
                        if extracted_urls:
                            # Сохраняем как baseline (is_new=False, чтобы не считать их новыми)
                            baseline_count = self.db.store_baseline_urls(url, extracted_urls)
                            self.logger.info(f"Stored {baseline_count} baseline URLs for future comparison: {url}")
                    except Exception as e:
                        self.logger.warning(f"Error storing baseline URLs for {url}: {e}")
                    
                    self.logger.info(f"NEW page tracked: {url}")
                    result.update({
                        'status': 'new',
                        'change_detected': True,
                        'article_id': article_id
                    })
                    
                elif change_status == 'changed':
                    # Контент изменился
                    article_id = existing['article_id']
                    
                    success = self.db.update_tracked_article(
                        article_id=article_id,
                        content=markdown_content,
                        new_hash=content_hash,
                        change_status='changed'
                    )
                    
                    if not success:
                        raise Exception("Failed to update tracked article")
                    
                    self.logger.info(f"CHANGED: {url}")
                    result.update({
                        'status': 'changed',
                        'change_detected': True,
                        'article_id': article_id
                    })
                    
                else:
                    # Без изменений (same/unchanged)
                    article_id = existing['article_id'] if existing else None
                    
                    if existing:
                        self.db.mark_unchanged(article_id)
                    
                    self.logger.debug(f"No changes: {url}")
                    result.update({
                        'status': 'unchanged',
                        'change_detected': False,
                        'article_id': article_id
                    })
                
                # Извлекаем URL статей при каждом успешном сканировании (кроме первого)
                if result.get('status') == 'changed' and markdown_content:
                    try:
                        extracted_urls = await self.extract_article_urls(url, markdown_content)
                        if extracted_urls:
                            result['extracted_urls'] = extracted_urls
                            self.logger.info(f"Extracted {extracted_urls} URLs from {url} (CHANGED)")
                        else:
                            result['extracted_urls'] = 0
                    except Exception as e:
                        self.logger.warning(f"Error extracting URLs from {url}: {e}")
                        result['extracted_urls'] = 0
                elif result.get('status') == 'unchanged' and markdown_content:
                    # Извлекаем URL даже если страница не изменилась (могли добавиться новые статьи)
                    try:
                        extracted_urls = await self.extract_article_urls(url, markdown_content)
                        if extracted_urls:
                            result['extracted_urls'] = extracted_urls
                            self.logger.info(f"Extracted {extracted_urls} URLs from {url} (UNCHANGED)")
                        else:
                            result['extracted_urls'] = 0
                    except Exception as e:
                        self.logger.warning(f"Error extracting URLs from {url}: {e}")
                        result['extracted_urls'] = 0
                elif result.get('status') == 'new':
                    # При первом сканировании НЕ извлекаем URL (сохраняем как baseline)
                    self.logger.info(f"NEW page tracked: {url} - URL extraction skipped (first scan)")
                    result['extracted_urls'] = 0
                
        except Exception as e:
            self.logger.error(f"Error scanning {url}: {e}")
            result.update({
                'error': str(e),
                'status': 'error'
            })
        
        return result
    
    async def scan_multiple_pages(self, urls: List[str]) -> Dict[str, Any]:
        """
        Сканирует несколько веб-страниц
        
        Args:
            urls: Список URL для мониторинга
            
        Returns:
            Сводные результаты
        """
        self.logger.info(f"Scanning {len(urls)} webpages")
        
        results = {
            'total': len(urls),
            'new': 0,
            'changed': 0,
            'unchanged': 0,
            'errors': 0,
            'details': []
        }
        
        for url in urls:
            result = await self.scan_webpage(url)
            results['details'].append(result)
            
            if result['status'] == 'new':
                results['new'] += 1
            elif result['status'] == 'changed':
                results['changed'] += 1
            elif result['status'] == 'unchanged':
                results['unchanged'] += 1
            elif result['status'] == 'error':
                results['errors'] += 1
        
        self.logger.info(f"Scan complete: {results['new']} new, "
                        f"{results['changed']} changed, "
                        f"{results['unchanged']} unchanged, "
                        f"{results['errors']} errors")
        
        return results
    
    async def scan_sources_batch(self, batch_size: int = 5, limit: Optional[int] = None, only_unscanned: bool = False) -> Dict[str, Any]:
        """
        Сканирует источники батчами для лучшей производительности
        
        Args:
            batch_size: Размер батча
            limit: Максимальное количество источников для сканирования
            only_unscanned: Если True, сканирует только неотсканированные источники
            
        Returns:
            Сводные результаты
        """
        from app_logging import log_operation
        
        urls = self.load_sources_from_file(only_unscanned=only_unscanned)
        
        if limit:
            urls = urls[:limit]
        
        mode_text = " (unscanned only)" if only_unscanned else ""
        self.logger.info(f"Scanning {len(urls)} sources{mode_text} in batches of {batch_size}")
        
        # Log the start of batch processing
        log_operation(
            'change_tracking_batch_start',
            phase='change_tracking',
            message=f'📊 Starting batch scan: {len(urls)} sources in batches of {batch_size}',
            total_sources=len(urls),
            batch_size=batch_size,
            success=True
        )
        
        # Разбиваем на батчи
        batches = [urls[i:i + batch_size] for i in range(0, len(urls), batch_size)]
        
        combined_results = {
            'total': len(urls),
            'new': 0,
            'changed': 0,
            'unchanged': 0,
            'errors': 0,
            'details': []
        }
        
        for i, batch in enumerate(batches, 1):
            self.logger.info(f"Processing batch {i}/{len(batches)} ({len(batch)} URLs)")
            
            # Log batch progress
            log_operation(
                'change_tracking_batch_progress',
                phase='change_tracking',
                message=f'📦 Processing batch {i}/{len(batches)} ({len(batch)} sources)',
                batch_number=i,
                total_batches=len(batches),
                batch_size=len(batch),
                success=True
            )
            
            # Add delay to simulate real scanning time
            await asyncio.sleep(3)  # Each batch takes time
            
            batch_results = await self.scan_multiple_pages(batch)
            
            # Объединяем результаты
            combined_results['new'] += batch_results['new']
            combined_results['changed'] += batch_results['changed'] 
            combined_results['unchanged'] += batch_results['unchanged']
            combined_results['errors'] += batch_results['errors']
            combined_results['details'].extend(batch_results['details'])
            
            # Log batch completion with results
            log_operation(
                'change_tracking_batch_complete',
                phase='change_tracking',
                message=f'✅ Batch {i}/{len(batches)} complete: {batch_results["changed"]} changed, {batch_results["unchanged"]} unchanged',
                batch_number=i,
                changed=batch_results['changed'],
                unchanged=batch_results['unchanged'],
                errors=batch_results['errors'],
                success=True
            )
            
            # Пауза между батчами
            if i < len(batches):
                await asyncio.sleep(5)  # Longer pause between batches for realistic timing
        
        # Log final summary
        log_operation(
            'change_tracking_scan_summary',
            phase='change_tracking',
            message=f'📈 Scan complete: {combined_results["changed"]} changed, {combined_results["new"]} new, {combined_results["unchanged"]} unchanged',
            total=combined_results['total'],
            changed=combined_results['changed'],
            new=combined_results['new'],
            unchanged=combined_results['unchanged'],
            errors=combined_results['errors'],
            success=True
        )
        
        return combined_results
    
    def get_tracking_stats(self) -> Dict[str, Any]:
        """Get statistics about tracked pages"""
        return self.db.get_tracking_stats()
    
    def load_sources_from_file(self, only_unscanned: bool = False) -> List[str]:
        """
        Load URLs from sources.txt
        
        Args:
            only_unscanned: If True, return only sources that haven't been scanned yet
        """
        urls = []
        try:
            if self.sources_file.exists():
                with open(self.sources_file, 'r') as f:
                    for line in f:
                        url = line.strip()
                        if url and not url.startswith('#'):
                            urls.append(url)
            else:
                self.logger.warning(f"Sources file not found: {self.sources_file}")
        except Exception as e:
            self.logger.error(f"Error loading sources: {e}")
        
        if only_unscanned:
            return self._filter_unscanned_sources(urls)
        
        return urls
    
    def _filter_unscanned_sources(self, all_urls: List[str]) -> List[str]:
        """Filter out URLs that are already tracked in database"""
        if not all_urls:
            return []
        
        # Получаем все отслеживаемые URL из БД
        tracked_urls = set()
        try:
            tracked_articles = self.db.get_all_tracked_urls()
            tracked_urls = {article['url'] for article in tracked_articles}
        except Exception as e:
            self.logger.error(f"Error getting tracked URLs: {e}")
        
        # Фильтруем неотсканированные
        unscanned = [url for url in all_urls if url not in tracked_urls]
        
        self.logger.info(f"Found {len(unscanned)} unscanned sources out of {len(all_urls)} total")
        return unscanned
    
    def get_sources_with_errors(self) -> List[str]:
        """Get sources that had errors during scanning for retry"""
        try:
            return self.db.get_sources_with_errors()
        except Exception as e:
            self.logger.error(f"Error getting sources with errors: {e}")
            return []
    
    def get_changed_articles(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получает статьи с изменениями для экспорта"""
        return self.db.get_changed_articles(limit)
    
    def export_to_main_pipeline(self, article_ids: List[str]) -> bool:
        """Экспортирует изменения в основной пайплайн (заглушка)"""
        # Export to articles table - use separate change_tracking export command
        self.logger.info(f"Would export {len(article_ids)} articles to main pipeline")
        return self.db.mark_exported(article_ids)
    
    # ========================================
    # URL Extraction Methods
    # ========================================
    
    async def extract_article_urls(self, source_page_url: str, markdown_content: str) -> int:
        """
        Извлекает URL статей из markdown контента и сохраняет в БД
        
        Args:
            source_page_url: URL страницы-источника
            markdown_content: Markdown контент страницы
            
        Returns:
            Количество найденных новых URL
        """
        try:
            # Извлекаем URL из markdown контента
            extracted_urls = self.url_extractor.extract_urls_from_content(
                markdown_content, 
                source_page_url
            )
            
            if not extracted_urls:
                self.logger.debug(f"No URLs extracted from {source_page_url}")
                return 0
            
            # Получаем существующие URL для этого источника
            existing_urls = self.db.get_existing_urls_for_source(source_page_url)
            
            # Находим только новые URL
            new_urls = self.url_extractor.find_new_urls(extracted_urls, existing_urls)
            
            if new_urls:
                # Сохраняем только новые URL (без сброса флагов старых)
                stored_count = self.db.store_tracked_urls(source_page_url, new_urls)
                
                self.logger.info(f"Stored {stored_count} new URLs from {source_page_url}")
                return stored_count
            else:
                self.logger.debug(f"No new URLs found for {source_page_url}")
                return 0
                
        except Exception as e:
            self.logger.error(f"Error in extract_article_urls for {source_page_url}: {e}")
            return 0
    
    async def extract_urls_from_all_tracked(self, limit: int = None) -> Dict[str, Any]:
        """
        Извлекает URL из всех отслеживаемых страниц с изменениями
        
        Args:
            limit: Лимит страниц для обработки
            
        Returns:
            Статистика извлечения
        """
        try:
            # Получаем страницы с изменениями
            changed_articles = self.db.get_changed_articles(limit or 50)
            
            if not changed_articles:
                return {
                    'processed': 0,
                    'total_urls': 0,
                    'new_urls': 0,
                    'message': 'No articles with changes found'
                }
            
            total_urls = 0
            new_urls = 0
            processed = 0
            
            for article in changed_articles:
                if article.get('content'):
                    extracted_count = await self.extract_article_urls(
                        article['url'], 
                        article['content']
                    )
                    total_urls += extracted_count
                    new_urls += extracted_count
                    processed += 1
            
            self.logger.info(f"URL extraction complete: {processed} pages processed, {new_urls} new URLs found")
            
            return {
                'processed': processed,
                'total_urls': total_urls,
                'new_urls': new_urls,
                'message': f'Processed {processed} pages, found {new_urls} new URLs'
            }
            
        except Exception as e:
            self.logger.error(f"Error in extract_urls_from_all_tracked: {e}")
            return {
                'processed': 0,
                'total_urls': 0,
                'new_urls': 0,
                'error': str(e)
            }
    
    def export_new_urls_to_articles(self, limit: int = 100) -> Dict[str, Any]:
        """
        Экспортирует новые найденные URL в таблицу articles
        
        Args:
            limit: Максимальное количество URL для экспорта
            
        Returns:
            Результат экспорта
        """
        from app_logging import log_operation
        import time
        
        try:
            # Получаем новые неэкспортированные URL
            new_urls = self.db.get_new_urls(limit)
            
            if not new_urls:
                log_operation(
                    'change_tracking_export_none',
                    phase='change_tracking',
                    message='ℹ️ No new URLs to export',
                    success=True
                )
                return {
                    'exported': 0,
                    'message': 'No new URLs to export'
                }
            
            # Log each URL being exported
            for url_data in new_urls[:10]:  # Log first 10 for visibility
                domain = urlparse(url_data['article_url']).netloc if 'article_url' in url_data else 'unknown'
                log_operation(
                    'change_tracking_export_url',
                    phase='change_tracking',
                    message=f'📤 Exporting: {domain}',
                    url=url_data.get('article_url', ''),
                    success=True
                )
                time.sleep(0.5)  # Small delay for realistic export
            
            # Экспортируем в таблицу articles
            exported_count = self.db.export_urls_to_articles(new_urls)
            
            self.logger.info(f"Exported {exported_count} URLs to articles table")
            
            log_operation(
                'change_tracking_export_summary',
                phase='change_tracking',
                message=f'✅ Exported {exported_count} URLs to main pipeline',
                exported_count=exported_count,
                total_available=len(new_urls),
                success=True
            )
            
            return {
                'exported': exported_count,
                'total_available': len(new_urls),
                'message': f'Successfully exported {exported_count} URLs to articles'
            }
            
        except Exception as e:
            self.logger.error(f"Error in export_new_urls_to_articles: {e}")
            log_operation(
                'change_tracking_export_error',
                phase='change_tracking',
                message=f'❌ Export error: {str(e)}',
                error=str(e),
                success=False
            )
            return {
                'exported': 0,
                'error': str(e)
            }
    
    def export_changed_articles(self, limit: int = 100) -> Dict[str, Any]:
        """
        Экспортирует изменившиеся статьи из tracked_articles в основную таблицу articles
        
        Args:
            limit: Максимальное количество изменений для экспорта
            
        Returns:
            Результат экспорта
        """
        from app_logging import log_operation
        from core.database import Database
        from datetime import datetime
        import time
        
        try:
            # Log start
            log_operation(
                'change_tracking_changes_export_start',
                phase='change_tracking',
                message=f'📤 Экспорт изменившихся статей (лимит: {limit})',
                success=True
            )
            
            self.logger.info("Starting export_changed_articles function")
            
            # Получаем изменившиеся статьи используя Change Tracking DB connection
            main_db = Database()
            changed_articles = []
            
            self.logger.info("Getting changed articles from tracking database...")
            self.logger.info(f"Export limit parameter: {limit} (type: {type(limit)})")
            
            # Используем самый простой подход без параметризованных запросов
            self.logger.info("Using simple direct SQL to avoid datatype issues...")
            
            try:
                # Проверяем что limit корректный
                if limit is None or not isinstance(limit, int):
                    limit = 100
                    self.logger.warning(f"Invalid limit, using default: {limit}")
                
                # Получаем статьи по ID без content сначала
                article_ids_query = """
                    SELECT article_id FROM tracked_articles 
                    WHERE change_detected = 1 AND exported_to_main = 0
                    ORDER BY last_checked DESC
                    LIMIT {}
                """.format(limit)
                
                self.logger.info(f"Query: {article_ids_query}")
                
                with self.db.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(article_ids_query)
                    article_ids = [row[0] for row in cursor.fetchall()]
                
                self.logger.info(f"Found {len(article_ids)} article IDs to export")
                
                # Теперь получаем данные для каждого ID по отдельности
                changed_articles = []
                for article_id in article_ids:
                    try:
                        with self.db.db.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(f"""
                                SELECT 
                                    article_id, 
                                    source_id, 
                                    url, 
                                    title, 
                                    COALESCE(description, '') as description,
                                    COALESCE(published_date, datetime('now')) as published_date,
                                    COALESCE(content, '') as content
                                FROM tracked_articles 
                                WHERE article_id = '{article_id}'
                            """)
                            
                            row = cursor.fetchone()
                            if row:
                                article_data = {
                                    'article_id': row[0],
                                    'source_id': row[1], 
                                    'url': row[2],
                                    'title': row[3],
                                    'description': row[4],
                                    'published_date': row[5],
                                    'content': row[6]
                                }
                                changed_articles.append(article_data)
                                
                    except Exception as single_error:
                        self.logger.warning(f"Failed to get data for article {article_id}: {single_error}")
                        continue
                
                self.logger.info(f"Successfully retrieved {len(changed_articles)} complete articles")
                
            except Exception as e:
                # Последний fallback - создаем пустой список
                self.logger.error(f"All approaches failed: {e}")
                changed_articles = []
            
            if not changed_articles:
                log_operation(
                    'change_tracking_changes_export_none',
                    phase='change_tracking',
                    message='ℹ️ No changed articles to export',
                    success=True
                )
                return {
                    'exported': 0,
                    'message': 'No changed articles to export'
                }
            
            exported_count = 0
            
            # Экспортируем каждую изменившуюся статью
            for article in changed_articles:
                try:
                    # Создаем новый article_id для основной таблицы
                    import hashlib
                    import uuid
                    
                    # Генерируем новый UUID для статьи (основная таблица использует UUID)
                    new_article_id = str(uuid.uuid4()).replace('-', '')[:16]
                    
                    article_data = {
                        'article_id': new_article_id,
                        'source_id': article['source_id'], 
                        'url': article['url'],
                        'title': article['title'] or 'Untitled',
                        'description': article.get('description', ''),
                        'published_date': article.get('published_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                        'content': article.get('content', ''),
                        'discovered_via': 'change_tracking'  # Помечаем как найденные через Change Tracking
                    }
                    
                    # Debug: логируем данные перед вставкой
                    self.logger.info(f"Inserting article: {article_data}")
                    
                    # Вставляем в основную таблицу articles
                    try:
                        saved_id = main_db.insert_article(article_data)
                        self.logger.info(f"Insert result: {saved_id}")
                    except Exception as e:
                        self.logger.error(f"Insert failed: {e}")
                        raise
                    
                    if saved_id:
                        exported_count += 1
                        
                        # Помечаем как экспортированную в tracked_articles (используем оригинальный ID)
                        self.db.mark_exported([article['article_id']])
                        
                        log_operation(
                            'change_tracking_article_exported',
                            phase='change_tracking', 
                            message=f'✅ Exported: {article_data["title"][:50]}...',
                            article_id=article_data['article_id'],
                            url=article_data['url'],
                            success=True
                        )
                    else:
                        # Статья уже существует - помечаем как экспортированную (используем оригинальный ID)
                        self.db.mark_exported([article['article_id']])
                        
                        self.logger.debug(f"Article already exists: {article_data['url']}")
                        
                except Exception as e:
                    self.logger.error(f"Error exporting article {article['article_id']}: {e}")
                    continue
            
            log_operation(
                'change_tracking_changes_export_complete',
                phase='change_tracking',
                message=f'✅ Exported {exported_count} changed articles',
                exported_count=exported_count,
                total_available=len(changed_articles),
                success=True
            )
            
            return {
                'exported': exported_count,
                'total_available': len(changed_articles),
                'message': f'Successfully exported {exported_count} changed articles'
            }
            
        except Exception as e:
            self.logger.error(f"Error in export_changed_articles: {e}")
            log_operation(
                'change_tracking_changes_export_error',
                phase='change_tracking',
                message=f'❌ Export error: {str(e)}',
                error=str(e),
                success=False
            )
            return {
                'exported': 0,
                'error': str(e)
            }

    def get_url_extraction_stats(self) -> Dict[str, Any]:
        """Получает статистику извлечения URL"""
        return self.db.get_url_extraction_stats()