#!/usr/bin/env python3
"""
Change Monitor
Отслеживание изменений на веб-страницах через Firecrawl changeTracking API
"""
import asyncio
import hashlib
import uuid
import json
import gc  # Для принудительной очистки памяти
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse
from pathlib import Path
import time

from app_logging import get_logger, log_error, log_operation
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
        
        # ИСПРАВЛЕНИЕ FK BUG: Специальные маппинги для проблемных доменов
        domain_mappings = {
            'huggingface.co': 'hugging_face',
            'www.huggingface.co': 'hugging_face',
            'doosanrobotics.com': 'doosan_robotics',
            'www.doosanrobotics.com': 'doosan_robotics'
        }
        
        domain = urlparse(url).netloc.lower()
        if domain in domain_mappings:
            return domain_mappings[domain]
        
        # Fallback to domain-based ID (for backward compatibility)
        clean_domain = domain.replace('.', '_')
        if clean_domain.startswith('www_'):
            clean_domain = clean_domain[4:]
        return clean_domain
    
    async def scan_webpage(self, url: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Сканирует веб-страницу и отслеживает изменения
        
        Args:
            url: URL веб-страницы для мониторинга
            max_retries: Максимальное количество попыток (по умолчанию 3)
            
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
                    urls_found = result.get('extracted_urls', 0)
                    # Если 0 URLs - это ОШИБКА, не успех
                    success = urls_found > 0
                    message = f'✅ Changed: {domain} ({urls_found} new URLs)' if success else f'❌ Changed but 0 URLs: {domain}'
                    log_operation(
                        'change_tracking_source_changed',
                        phase='change_tracking',
                        message=message,
                        source_id=source_id,
                        url=url,
                        urls_found=urls_found,
                        success=success
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
                    # Unchanged тоже может быть ошибкой если источник постоянно возвращает 0 URLs
                    # Получаем детальную статистику URL
                    url_stats = result.get('url_stats', {})
                    total_checked = url_stats.get('total_extracted', 0)
                    new_urls = url_stats.get('new_urls', 0)
                    
                    # Формируем сообщение в зависимости от результатов
                    if new_urls > 0:
                        message = f'⏸️ No changes: {domain} ({total_checked} URLs checked, {new_urls} new)'
                    elif total_checked > 0:
                        message = f'⏸️ No changes: {domain} ({total_checked} URLs checked, all existing)'
                    else:
                        message = f'⏸️ No changes: {domain} (0 URLs found)'
                    
                    success = True  # unchanged обычно OK, но если 0 URLs - проблема логируется отдельно
                    log_operation(
                        'change_tracking_source_unchanged',
                        phase='change_tracking',
                        message=message,
                        source_id=source_id,
                        url=url,
                        urls_found=new_urls,
                        urls_checked=total_checked,
                        success=success
                    )
                return result
            
            # Если не последняя попытка - ждем немного перед следующей (упрощенная версия)
            if attempt < max_retries - 1:
                wait_time = 2  # Фиксированная задержка 2 секунды вместо exponential backoff
                self.logger.warning(f"Retrying {url} in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
        
        # Если все попытки неудачны
        error_msg = f"Failed to scan {url} after {max_retries} attempts"
        self.logger.error(error_msg)
        
        # Логируем в errors.jsonl
        log_error('tracking_scan_failed', error_msg,
                 source_id=source_id,
                 url=url,
                 module='monitor',
                 max_retries=max_retries)
        
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
            # Убрана искусственная задержка для ускорения
            
            async with self.firecrawl as client:
                # Скрейпим страницу с changeTracking
                scraped_data = await asyncio.wait_for(
                    client.scrape_url(
                        url,
                        formats=['markdown', 'changeTracking']
                    ),
                    timeout=60  # Единый таймаут 60 секунд на источник
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
                        # Создаем новую запись (БЕЗ полного контента для экономии памяти)
                        success = self.db.create_tracked_article(
                            article_id=article_id,
                            source_id=source_id,
                            url=url,
                            title=title,
                            content='',  # НЕ сохраняем полный контент
                            content_hash=content_hash
                        )
                        
                        if not success:
                            raise Exception("Failed to create tracked article")
                    
                    # При первом сканировании сохраняем базовый список URL для будущих сравнений
                    try:
                        # НЕ используем page_titles для baseline - избегаем множественных API вызовов
                        extracted_urls = await self.url_extractor.extract_urls_from_content(
                            markdown_content, 
                            url, 
                            use_page_titles=False, 
                            firecrawl_client=None
                        )
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
                        content='',  # НЕ сохраняем полный контент для экономии памяти
                        content_hash=content_hash,
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
                        url_stats = await self.extract_article_urls(url, markdown_content)
                        result['extracted_urls'] = url_stats['new_urls']  # Для обратной совместимости
                        result['url_stats'] = url_stats  # Полная статистика
                        
                        if url_stats['new_urls'] > 0:
                            self.logger.info(f"Extracted {url_stats['total_extracted']} URLs from {url} (CHANGED): {url_stats['new_urls']} new, {url_stats['existing_urls']} existing")
                        else:
                            # Источник изменился но новых URL не найдено
                            source_id = self._get_source_id(url)
                            if url_stats['total_extracted'] > 0:
                                self.logger.warning(f"⚠️ CHANGED source {source_id}: checked {url_stats['total_extracted']} URLs, all existing")
                            else:
                                error_msg = f"CHANGED source {source_id} but extracted 0 URLs - patterns may be broken"
                                self.logger.error(f"❌ {error_msg}")
                                log_error('changed_source_no_urls', error_msg,
                                         source_id=source_id, url=url, 
                                         module='change_tracking.monitor')
                    except Exception as e:
                        self.logger.warning(f"Error extracting URLs from {url}: {e}")
                        result['extracted_urls'] = 0
                        result['url_stats'] = {'total_extracted': 0, 'new_urls': 0, 'existing_urls': 0}
                elif result.get('status') == 'unchanged' and markdown_content:
                    # Извлекаем URL даже если страница не изменилась (могли добавиться новые статьи)
                    try:
                        url_stats = await self.extract_article_urls(url, markdown_content)
                        result['extracted_urls'] = url_stats['new_urls']  # Для обратной совместимости
                        result['url_stats'] = url_stats  # Полная статистика
                        
                        if url_stats['new_urls'] > 0:
                            self.logger.info(f"Extracted {url_stats['total_extracted']} URLs from {url} (UNCHANGED): {url_stats['new_urls']} new, {url_stats['existing_urls']} existing")
                        else:
                            # Источник не изменился и новых URL нет
                            source_id = self._get_source_id(url)
                            if url_stats['total_extracted'] > 0:
                                self.logger.info(f"ℹ️ UNCHANGED source {source_id}: checked {url_stats['total_extracted']} URLs, all existing")
                            else:
                                error_msg = f"UNCHANGED source {source_id} has 0 URLs - patterns may be broken"
                                self.logger.error(f"❌ {error_msg}")
                                log_error('unchanged_source_no_urls', error_msg,
                                         source_id=source_id, url=url,
                                         module='change_tracking.monitor')
                    except Exception as e:
                        self.logger.warning(f"Error extracting URLs from {url}: {e}")
                        result['extracted_urls'] = 0
                        result['url_stats'] = {'total_extracted': 0, 'new_urls': 0, 'existing_urls': 0}
                elif result.get('status') == 'new':
                    # При первом сканировании НЕ извлекаем URL (сохраняем как baseline)
                    self.logger.info(f"NEW page tracked: {url} - URL extraction skipped (first scan)")
                    result['extracted_urls'] = 0
                
                # Очищаем большие переменные для освобождения памяти
                markdown_content = None
                scraped_data = None
                del markdown_content
                if 'scraped_data' in locals():
                    del scraped_data
                
        except asyncio.TimeoutError as e:
            error_msg = f"Timeout scanning {url} after 60s"
            self.logger.error(error_msg)
            
            # Логируем таймаут в errors.jsonl
            log_error('tracking_timeout', error_msg,
                     url=url,
                     module='monitor',
                     timeout_seconds=60)
            
            # Принудительно закрыть сессию чтобы не зависало
            if hasattr(self, 'firecrawl') and self.firecrawl:
                try:
                    await self.firecrawl.close()
                    self.logger.info(f"Force closed Firecrawl session after timeout for {url}")
                except Exception as close_error:
                    self.logger.warning(f"Error closing Firecrawl session: {close_error}")
            result.update({
                'error': f'Timeout after 60s',
                'status': 'error'
            })
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
    
    async def scan_sources_sequential(self, limit: Optional[int] = None, only_unscanned: bool = False) -> Dict[str, Any]:
        """
        Сканирует источники СТРОГО ПОСЛЕДОВАТЕЛЬНО без батчей
        
        Args:
            limit: Максимальное количество источников для сканирования
            only_unscanned: Если True, сканирует только неотсканированные источники
            
        Returns:
            Сводные результаты
        """
        from app_logging import log_operation, log_error
        from urllib.parse import urlparse
        
        urls = self.load_sources_from_file(only_unscanned=only_unscanned)
        
        if limit:
            urls = urls[:limit]
        
        total = len(urls)
        mode_text = " (unscanned only)" if only_unscanned else ""
        self.logger.info(f"Sequential scanning {total} sources{mode_text}")
        
        # Логируем начало последовательного сканирования
        log_operation(
            'change_tracking_sequential_start',
            phase='change_tracking',
            message=f'🔄 Starting sequential scan: {total} sources',
            total_sources=total,
            mode='sequential',
            success=True
        )
        
        # Создаём/очищаем файл прогресса
        try:
            with open('logs/progress.log', 'w') as f:
                f.write(f"{datetime.now().isoformat()} | STARTED: Change Tracking scan of {total} sources\n")
                f.write(f"{'='*60}\n")
        except Exception as e:
            self.logger.debug(f"Could not create progress log: {e}")
        
        results = {
            'total': total,
            'new': 0,
            'changed': 0,
            'unchanged': 0,
            'errors': 0,
            'details': []
        }
        
        for i, url in enumerate(urls, 1):
            source_id = self._get_source_id(url)
            domain = urlparse(url).netloc
            
            # ВСЕГДА логируем начало с прогрессом
            log_operation(
                'change_tracking_source_start',
                phase='change_tracking',
                message=f'[{i}/{total}] 🔍 Scanning: {domain}',
                source_id=source_id,
                url=url,
                progress=f'{i}/{total}',
                success=True
            )
            
            try:
                # Сканируем источник с таймаутом (60 сек на попытку × 3 попытки = 180 сек максимум)
                result = await asyncio.wait_for(
                    self.scan_webpage(url),
                    timeout=180  # 3 минуты максимум на источник
                )
                
                # Обновляем счетчики
                status = result.get('status', 'error')
                if status == 'new':
                    results['new'] += 1
                elif status == 'changed':
                    results['changed'] += 1
                elif status == 'unchanged':
                    results['unchanged'] += 1
                else:
                    results['errors'] += 1
                
                # Сохраняем только минимальную информацию для экономии памяти
                results['details'].append({
                    'url': result.get('url'),
                    'status': result.get('status'),
                    'urls_found': result.get('extracted_urls', 0)
                })
                
                # Логируем успешное завершение
                log_operation(
                    'change_tracking_source_complete',
                    phase='change_tracking',
                    message=f'[{i}/{total}] ✅ Completed: {domain} ({status})',
                    source_id=source_id,
                    url=url,
                    status=status,
                    progress=f'{i}/{total}',
                    success=True
                )
                
            except asyncio.TimeoutError as e:
                results['errors'] += 1
                error_msg = f"Timeout scanning {url} after 60s"
                self.logger.error(error_msg)
                
                # Логируем таймаут
                log_error('tracking_timeout', error_msg,
                    source_id=source_id,
                    url=url,
                    module='change_tracking.monitor'
                )
                
                log_operation(
                    'change_tracking_source_timeout',
                    phase='change_tracking',
                    message=f'[{i}/{total}] ⏱️ Timeout: {domain}',
                    source_id=source_id,
                    url=url,
                    progress=f'{i}/{total}',
                    error='Timeout after 60s',
                    success=False
                )
                
                results['details'].append({
                    'url': url,
                    'status': 'error',
                    'urls_found': 0
                })
                
            except Exception as e:
                results['errors'] += 1
                error_msg = f"Error scanning {url}: {str(e)}"
                self.logger.error(error_msg)
                
                # Логируем ошибку
                log_error('tracking_scan_error', error_msg,
                    source_id=source_id,
                    url=url,
                    error=str(e),
                    module='change_tracking.monitor'
                )
                
                log_operation(
                    'change_tracking_source_error',
                    phase='change_tracking',
                    message=f'[{i}/{total}] ❌ Error: {domain}',
                    source_id=source_id,
                    url=url,
                    progress=f'{i}/{total}',
                    error=str(e),
                    success=False
                )
                
                results['details'].append({
                    'url': url,
                    'status': 'error',
                    'urls_found': 0
                })
                
            finally:
                # Очистка памяти после КАЖДОГО источника
                gc.collect()
                
                # СБРОС CONNECTION POOL каждые 10 источников
                if i % 10 == 0:  # Каждые 10 источников
                    self.logger.info(f"Progress: {i}/{total} sources processed - resetting connection pool")
                    
                    # Логирование прогресса в файл для мониторинга
                    try:
                        import psutil
                        process = psutil.Process()
                        memory_mb = process.memory_info().rss / 1024 / 1024
                        with open('logs/progress.log', 'a') as f:
                            f.write(f"{datetime.now().isoformat()} | Progress: {i}/{total} sources | Memory: {memory_mb:.1f}MB | Status: Running\n")
                            f.flush()  # Сразу записываем на диск
                    except Exception as e:
                        self.logger.debug(f"Could not write progress: {e}")
                    
                    # КРИТИЧНО: Сбрасываем Supabase клиент для очистки соединений
                    if hasattr(self.db, 'supabase') and hasattr(self.db.supabase, 'reset_client'):
                        self.db.supabase.reset_client()
                        self.logger.info("✅ Supabase connection pool reset after 10 sources")
                    
                    # Дополнительная глубокая очистка памяти каждые 10 источников
                    gc.collect(2)  # Полная сборка мусора всех поколений
                    self.logger.debug(f"Deep memory cleanup performed after {i} sources")
                    
                    # Очищаем накопленные результаты для экономии памяти
                    # Сохраняем только последние 10 для отладки
                    if len(results['details']) > 10:
                        results['details'] = results['details'][-10:]
                        self.logger.debug(f"Trimmed results details to last 10 entries")
        
        # Логируем итоговую сводку
        log_operation(
            'change_tracking_sequential_complete',
            phase='change_tracking',
            message=f'📊 Sequential scan complete: {results["changed"]} changed, {results["new"]} new, {results["unchanged"]} unchanged, {results["errors"]} errors',
            total=results['total'],
            changed=results['changed'],
            new=results['new'],
            unchanged=results['unchanged'],
            errors=results['errors'],
            success=True
        )
        
        # Финальная запись в progress.log
        try:
            with open('logs/progress.log', 'a') as f:
                f.write(f"{'='*60}\n")
                f.write(f"{datetime.now().isoformat()} | COMPLETED: {results['total']} sources scanned\n")
                f.write(f"Results: {results['changed']} changed, {results['new']} new, {results['unchanged']} unchanged, {results['errors']} errors\n")
        except Exception as e:
            self.logger.debug(f"Could not write final progress: {e}")
        
        # Обновляем статус завершения в global_config
        try:
            from services.supabase_client import SupabaseClient
            supabase_client = SupabaseClient()
            supabase_client.supabase.table('global_config').upsert({
                'key': 'change_tracking_last_scan',
                'value': datetime.now(timezone.utc).isoformat(),
                'description': 'Last change tracking scan completion timestamp',
                'updated_at': datetime.now(timezone.utc).isoformat()
            }, on_conflict='key').execute()
            
            # Также обновляем статус процесса
            supabase_client.supabase.table('global_config').upsert({
                'key': 'change_tracking_status',
                'value': 'completed',
                'description': 'Change tracking process status',
                'updated_at': datetime.now(timezone.utc).isoformat()
            }, on_conflict='key').execute()
            
            self.logger.info("Updated change tracking status in global_config")
        except Exception as e:
            self.logger.warning(f"Could not update global_config: {e}")
        
        self.logger.info(f"Sequential scan complete: {results['new']} new, "
                        f"{results['changed']} changed, "
                        f"{results['unchanged']} unchanged, "
                        f"{results['errors']} errors")
        
        # Ensure proper process termination
        import sys
        sys.stdout.flush()
        sys.stderr.flush()
        
        return results
    
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
    
    async def extract_article_urls(self, source_page_url: str, markdown_content: str) -> dict:
        """
        Извлекает URL статей из markdown контента и сохраняет в БД
        
        Args:
            source_page_url: URL страницы-источника
            markdown_content: Markdown контент страницы
            
        Returns:
            Словарь с детальной статистикой:
            {
                'total_extracted': количество всех найденных URL,
                'new_urls': количество новых URL,
                'existing_urls': количество уже существующих URL
            }
        """
        try:
            # Извлекаем URL из markdown контента
            # ВРЕМЕННО ОТКЛЮЧАЕМ реальные заголовки для стабильности системы
            extracted_urls = await self.url_extractor.extract_urls_from_content(
                markdown_content, 
                source_page_url,
                use_page_titles=False,
                firecrawl_client=None
            )
            
            if not extracted_urls:
                # КРИТИЧЕСКАЯ ОШИБКА: источник не вернул URL - паттерны могут быть сломаны
                source_id = self._get_source_id(source_page_url)
                domain = urlparse(source_page_url).netloc
                
                # Двойное логирование для видимости проблемы
                error_msg = f"Source {source_id} ({domain}) returned 0 URLs - patterns may be broken"
                self.logger.error(f"❌ {error_msg}")
                
                # Централизованное логирование для анализа
                log_error('source_no_urls_extracted', 
                         error_msg,
                         source_id=source_id,
                         url=source_page_url,
                         domain=domain,
                         module='change_tracking.monitor',
                         operation='extract_article_urls')
                return {'total_extracted': 0, 'new_urls': 0, 'existing_urls': 0}
            
            # Получаем существующие URL для этого источника с таймаутом
            existing_urls = self.db.get_existing_urls_for_source(source_page_url)
            
            # Считаем общую статистику
            total_extracted = len(extracted_urls)
            # Исправлено: правильное пересечение множеств
            extracted_article_urls = set(url_data['article_url'] for url_data in extracted_urls)
            existing_count = len(existing_urls.intersection(extracted_article_urls))
            
            # Находим только новые URL
            new_urls = self.url_extractor.find_new_urls(extracted_urls, existing_urls)
            
            if new_urls:
                # Сохраняем только новые URL с таймаутом
                stored_count = self.db.store_tracked_urls(source_page_url, new_urls)
                
                self.logger.info(f"Found {total_extracted} URLs total, {stored_count} new, {existing_count} existing from {source_page_url}")
                return {
                    'total_extracted': total_extracted,
                    'new_urls': stored_count,
                    'existing_urls': existing_count
                }
            else:
                self.logger.debug(f"No new URLs found for {source_page_url} (total: {total_extracted}, all existing)")
                return {
                    'total_extracted': total_extracted,
                    'new_urls': 0,
                    'existing_urls': total_extracted
                }
                
        except Exception as e:
            self.logger.error(f"Error in extract_article_urls for {source_page_url}: {e}")
            return {'total_extracted': 0, 'new_urls': 0, 'existing_urls': 0}
    
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
                    url_stats = await self.extract_article_urls(
                        article['url'], 
                        article['content']
                    )
                    total_urls += url_stats['total_extracted']
                    new_urls += url_stats['new_urls']
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
            
            self.logger.info(f"Found {len(new_urls)} URLs to export")
            
            # Логируем только начало экспорта
            log_operation(
                'change_tracking_export_start',
                phase='change_tracking',
                message=f'📤 Starting export of {len(new_urls)} URLs',
                total_urls=len(new_urls),
                success=True
            )
            
            # Экспортируем в таблицу articles (логирование будет внутри)
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
        from services.supabase_client import SupabaseClient
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
            
            # Получаем изменившиеся статьи используя Supabase
            main_db = SupabaseClient()
            changed_articles = []
            
            self.logger.info("Getting changed articles from tracking database...")
            self.logger.info(f"Export limit parameter: {limit} (type: {type(limit)})")
            
            # Получаем ссылку на Supabase client для прямых запросов
            from core.db_config import DatabaseConfig
            self.supabase = DatabaseConfig.get_database()
            
            try:
                # Проверяем что limit корректный
                if limit is None or not isinstance(limit, int):
                    limit = 100
                    self.logger.warning(f"Invalid limit, using default: {limit}")
                
                # Получаем статьи по ID без content сначала
                # ИСПРАВЛЕНИЕ SQLite БАГ: Используем Supabase API (синхронный вызов)
                try:
                    # Supabase операция - синхронная, но быстрая
                    response = self.supabase.client.table('tracked_articles')\
                        .select('article_id')\
                        .eq('change_detected', True)\
                        .eq('exported_to_main', False)\
                        .order('last_checked', desc=True)\
                        .limit(limit)\
                        .execute()
                    
                    article_ids = [row['article_id'] for row in response.data] if response.data else []
                except Exception as e:
                    self.logger.error(f"Error querying Supabase for article IDs: {e}")
                    article_ids = []
                
                self.logger.info(f"Found {len(article_ids)} article IDs to export")
                
                # Теперь получаем данные для каждого ID через Supabase API
                changed_articles = []
                for article_id in article_ids:
                    try:
                        # ИСПРАВЛЕНИЕ SQLite БАГ: Используем Supabase API вместо SQL cursor
                        response = self.supabase.client.table('tracked_articles')\
                            .select('article_id, source_id, url, title, description, published_date, content')\
                            .eq('article_id', article_id)\
                            .limit(1)\
                            .execute()
                        
                        if response.data and len(response.data) > 0:
                            row = response.data[0]
                            article_data = {
                                'article_id': row['article_id'],
                                'source_id': row['source_id'], 
                                'url': row['url'],
                                'title': row['title'],
                                'description': row.get('description', ''),
                                'published_date': row.get('published_date', ''),
                                'content': row.get('content', '')
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