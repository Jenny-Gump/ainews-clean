#!/usr/bin/env python3
"""
Change Tracking Database Operations for Supabase
Полная реализация на Supabase вместо SQLite
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Set
from pathlib import Path
from urllib.parse import urlparse
import time

from app_logging import get_logger, log_error
from core.db_config import DatabaseConfig


class ChangeTrackingDB:
    """Управление базой данных для отслеживания изменений через Supabase"""
    
    def __init__(self):
        self.logger = get_logger('change_tracking.database')
        self.supabase = DatabaseConfig.get_database()  # Supabase client
        self.supabase_timeout = 30  # Таймаут для Supabase запросов в секундах
    
    def _execute_with_timeout(self, query_func, query_name: str, timeout: int = None):
        """
        Выполняет Supabase запрос с таймаутом и централизованным логированием
        
        Args:
            query_func: Функция запроса к Supabase
            query_name: Имя запроса для логирования
            timeout: Таймаут в секундах
            
        Returns:
            Результат запроса или None при ошибке
        """
        from app_logging import log_operation
        import concurrent.futures
        
        timeout = timeout or self.supabase_timeout
        
        # Логируем начало операции
        log_operation(
            'supabase_query_start',
            phase='database',
            message=f'🔍 Supabase query: {query_name}',
            query_name=query_name,
            timeout_seconds=timeout,
            success=True
        )
        
        start_time = time.time()
        
        try:
            # Используем ThreadPoolExecutor для таймаута
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(query_func)
                result = future.result(timeout=timeout)
            
            duration = time.time() - start_time
            
            # Логируем успешное завершение
            log_operation(
                'supabase_query_complete',
                phase='database',
                message=f'✅ Supabase query completed: {query_name}',
                query_name=query_name,
                duration_seconds=duration,
                success=True
            )
            
            if duration > 5:
                self.logger.warning(f"Slow Supabase query: {query_name} took {duration:.2f}s")
                log_operation(
                    'supabase_slow_query',
                    phase='database',
                    message=f'⚠️ Slow query: {query_name} ({duration:.2f}s)',
                    query_name=query_name,
                    duration_seconds=duration,
                    success=True
                )
            
            return result
            
        except concurrent.futures.TimeoutError:
            duration = time.time() - start_time
            error_msg = f"Supabase query timeout: {query_name} after {duration:.2f}s"
            self.logger.error(error_msg)
            
            # Централизованное логирование таймаута
            log_error('supabase_timeout', error_msg, 
                     query_name=query_name, 
                     timeout_seconds=timeout,
                     actual_duration=duration,
                     module='change_tracking.database')
            
            log_operation(
                'supabase_query_timeout',
                phase='database',
                message=f'❌ Query timeout: {query_name}',
                query_name=query_name,
                duration_seconds=duration,
                timeout_seconds=timeout,
                success=False
            )
            return None
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Supabase query failed: {query_name} after {duration:.2f}s: {str(e)}"
            self.logger.error(error_msg)
            
            # Централизованное логирование ошибки
            log_error('supabase_error', error_msg,
                     query_name=query_name,
                     error=str(e),
                     duration_seconds=duration,
                     module='change_tracking.database')
            
            log_operation(
                'supabase_query_error',
                phase='database',
                message=f'❌ Query failed: {query_name}',
                query_name=query_name,
                error=str(e),
                duration_seconds=duration,
                success=False
            )
            return None
    
    def create_tracked_article(
        self, 
        article_id: str, 
        source_id: str, 
        url: str, 
        title: str,
        content: str = "",
        content_hash: str = ""
    ) -> bool:
        """Создает новую запись отслеживания в Supabase"""
        try:
            article_data = {
                'article_id': article_id,
                'source_id': source_id,
                'url': url,
                'title': title,
                'content': content,
                'current_hash': content_hash,
                'change_detected': True,
                'change_status': 'new',
                'last_checked': datetime.now(timezone.utc).isoformat()
            }
            
            response = self.supabase.client.table('tracked_articles').insert(article_data).execute()
            
            self.logger.info(f"Created tracked article: {article_id}")
            return True
            
        except Exception as e:
            # ИСПРАВЛЕНИЕ FK BUG: Специальная обработка Foreign Key ошибок
            if 'foreign key constraint' in str(e).lower():
                error_msg = f"Source '{article_data['source_id']}' not found in sources table - skipping article"
                self.logger.error(f"❌ {error_msg}")
                self.logger.error(f"   Article URL: {article_data['url']}")
                self.logger.error(f"   Please add source '{article_data['source_id']}' to sources table or fix source mapping")
                
                # Логируем в errors.jsonl
                log_error('foreign_key_constraint', error_msg,
                         source_id=article_data['source_id'],
                         article_url=article_data['url'],
                         article_id=article_id,
                         module='change_tracking_database')
                return False  # Мягкий отказ вместо зависания
            else:
                error_msg = f"Error creating tracked article {article_id}"
                self.logger.error(f"{error_msg}: {e}")
                
                # Логируем в errors.jsonl
                log_error('tracked_article_creation_failed', error_msg,
                         article_id=article_id,
                         source_id=source_id,
                         url=url,
                         error_type=type(e).__name__,
                         module='change_tracking_database')
                return False
    
    def get_tracked_article_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Получает отслеживаемую статью по URL из Supabase"""
        try:
            response = self.supabase.client.table('tracked_articles')\
                .select('*')\
                .eq('url', url)\
                .limit(1)\
                .execute()
                
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
                
        except Exception as e:
            error_msg = f"Error getting tracked article by URL"
            self.logger.error(f"{error_msg} {url}: {e}")
            
            # Логируем в errors.jsonl
            log_error('tracked_article_fetch_failed', error_msg,
                     url=url[:200],
                     error_type=type(e).__name__,
                     module='change_tracking_database')
            return None
    
    def update_tracked_article(
        self,
        article_id: str,
        content: str = None,
        content_hash: str = None,
        change_detected: bool = None,
        change_status: str = None
    ) -> bool:
        """Обновляет запись отслеживания в Supabase"""
        try:
            update_data = {
                'last_checked': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            if content is not None:
                update_data['content'] = content
            if content_hash is not None:
                update_data['current_hash'] = content_hash
            if change_detected is not None:
                update_data['change_detected'] = change_detected
            if change_status is not None:
                update_data['change_status'] = change_status
            
            response = self.supabase.client.table('tracked_articles')\
                .update(update_data)\
                .eq('article_id', article_id)\
                .execute()
            
            self.logger.debug(f"Updated tracked article: {article_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating tracked article {article_id}: {e}")
            return False
    
    def mark_unchanged(self, article_id: str) -> bool:
        """Отмечает статью как не изменившуюся"""
        try:
            update_data = {
                'last_checked': datetime.now(timezone.utc).isoformat(),
                'change_detected': False,
                'change_status': 'unchanged'
            }
            
            response = self.supabase.client.table('tracked_articles')\
                .update(update_data)\
                .eq('article_id', article_id)\
                .execute()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error marking unchanged {article_id}: {e}")
            return False
    
    def get_tracking_stats(self) -> Dict[str, Any]:
        """Получает статистику отслеживания"""
        stats = {}
        
        try:
            # Общее количество
            response = self.supabase.client.table('tracked_articles').select('count', count='exact').execute()
            stats['total_tracked'] = response.count if response else 0
            
            # По статусам (упрощенно для Supabase)
            stats['by_status'] = {'unknown': 0}
            
            # Последние изменения
            response = self.supabase.client.table('tracked_articles')\
                .select('url, change_status, last_checked')\
                .eq('change_detected', True)\
                .order('last_checked', desc=True)\
                .limit(10)\
                .execute()
            
            if response.data:
                stats['recent_changes'] = [
                    {'url': row['url'], 'status': row['change_status'], 'checked': row['last_checked']}
                    for row in response.data
                ]
            else:
                stats['recent_changes'] = []
            
            # Источники (упрощенно)
            stats['by_source'] = {}
                
        except Exception as e:
            self.logger.error(f"Error getting tracking stats: {e}")
            stats = {'error': str(e)}
        
        return stats
    
    def get_changed_articles(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получает статьи с изменениями для экспорта"""
        try:
            response = self.supabase.client.table('tracked_articles')\
                .select('*')\
                .eq('change_detected', True)\
                .order('last_checked', desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            self.logger.error(f"Error getting changed articles: {e}")
            return []
    
    def mark_exported(self, article_ids: List[str]) -> bool:
        """Отмечает статьи как экспортированные"""
        try:
            for article_id in article_ids:
                update_data = {
                    'exported_to_main': True,
                    'exported_at': datetime.now(timezone.utc).isoformat()
                }
                
                self.supabase.client.table('tracked_articles')\
                    .update(update_data)\
                    .eq('article_id', article_id)\
                    .execute()
                    
            self.logger.info(f"Marked {len(article_ids)} articles as exported")
            return True
            
        except Exception as e:
            self.logger.error(f"Error marking articles as exported: {e}")
            return False
    
    def cleanup_old_records(self, days_old: int = 30) -> int:
        """Удаляет старые записи"""
        try:
            cutoff_date = datetime.now(timezone.utc)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_old)
            
            # Для Supabase это более сложная операция
            self.logger.info(f"Cleanup old records not implemented for Supabase yet")
            return 0
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old records: {e}")
            return 0
    
    def get_all_tracked_urls(self) -> List[Dict[str, Any]]:
        """Получает все отслеживаемые URL"""
        try:
            response = self.supabase.client.table('tracked_articles').select('url').execute()
            
            if response.data:
                return [{'url': row['url']} for row in response.data]
            return []
                
        except Exception as e:
            self.logger.error(f"Error getting tracked URLs: {e}")
            return []
    
    def get_sources_with_errors(self) -> List[str]:
        """Получает источники с ошибками для повторного сканирования"""
        try:
            # Пока что возвращаем пустой список, так как нет столбца для ошибок
            # В будущем здесь будет запрос для источников со статусом 'error'
            return []
        except Exception as e:
            self.logger.error(f"Error getting sources with errors: {e}")
            return []
    
    # ========================================
    # URL Extraction Methods - Supabase version
    # ========================================
    
    def store_tracked_urls(
        self, 
        source_page_url: str, 
        urls_data: List[Dict[str, str]]
    ) -> int:
        """
        Сохраняет извлеченные URL в таблицу tracked_urls в Supabase с таймаутом
        
        Args:
            source_page_url: URL страницы-каталога
            urls_data: Список словарей с данными URL
            
        Returns:
            Количество добавленных новых URL
        """
        if not urls_data:
            return 0
        
        # ИСПРАВЛЕНИЕ БАГА: Добавляем source_page_url к каждому URL перед сохранением
        enriched_urls = []
        for url_data in urls_data:
            enriched_data = url_data.copy()
            enriched_data['source_page_url'] = source_page_url
            enriched_urls.append(enriched_data)
            
        return self.add_tracked_urls(enriched_urls)
    
    def store_baseline_urls(
        self, 
        source_page_url: str, 
        urls_data: List[Dict[str, str]]
    ) -> int:
        """
        Сохраняет базовый список URL при первом сканировании (is_new=False)
        
        Args:
            source_page_url: URL страницы-каталога
            urls_data: Список словарей с данными URL
            
        Returns:
            Количество добавленных baseline URL
        """
        if not urls_data:
            return 0
            
        try:
            baseline_count = 0
            for url_data in urls_data:
                try:
                    # Проверяем существует ли уже этот URL
                    existing = self.supabase.client.table('tracked_urls')\
                        .select('id')\
                        .eq('source_page_url', source_page_url)\
                        .eq('article_url', url_data['article_url'])\
                        .limit(1)\
                        .execute()
                    
                    if existing.data and len(existing.data) > 0:
                        continue  # URL уже существует
                    
                    # Добавляем новый baseline URL (is_new=False)
                    insert_data = {
                        'source_page_url': source_page_url,
                        'article_url': url_data['article_url'],
                        'article_title': url_data.get('article_title', ''),
                        'source_domain': url_data['source_domain'],
                        'is_new': False,  # Baseline URLs
                        'exported_to_articles': False
                    }
                    
                    response = self.supabase.client.table('tracked_urls').insert(insert_data).execute()
                    
                    if response.data:
                        baseline_count += 1
                        
                except Exception as e:
                    error_msg = f"Error adding baseline URL {url_data.get('article_url', 'unknown')[:100]}"
                    self.logger.error(f"{error_msg}: {e}")
                    
                    # Логируем в errors.jsonl
                    log_error('baseline_url_add_failed', error_msg,
                             source_page_url=source_page_url,
                             article_url=url_data.get('article_url', 'unknown')[:200],
                             error_type=type(e).__name__,
                             module='change_tracking_database')
                    continue
                        
            if baseline_count > 0:
                self.logger.info(f"Stored {baseline_count} baseline URLs from {source_page_url}")
            else:
                self.logger.debug(f"No baseline URLs stored for {source_page_url}")
                
            return baseline_count
            
        except Exception as e:
            error_msg = f"Error storing baseline URLs"
            self.logger.error(f"{error_msg}: {e}")
            
            # Логируем в errors.jsonl
            log_error('baseline_urls_store_failed', error_msg,
                     source_page_url=source_page_url,
                     urls_count=len(urls_data),
                     error_type=type(e).__name__,
                     module='change_tracking_database')
            return 0
    
    def add_tracked_urls(self, urls_data: List[Dict[str, Any]]) -> int:
        """Добавляет новые отслеживаемые URL в Supabase с батч-обработкой и таймаутом"""
        if not urls_data:
            return 0
            
        try:
            # ОПТИМИЗАЦИЯ: Батч-проверка существующих URL одним запросом
            source_page_url = urls_data[0]['source_page_url']
            article_urls = [url_data['article_url'] for url_data in urls_data]
            
            # Получаем ВСЕ существующие URL одним запросом с таймаутом
            query_name = f"check_existing_urls({source_page_url[:50]}..., {len(article_urls)} urls)"
            
            def _check_existing():
                return self.supabase.client.table('tracked_urls')\
                    .select('article_url')\
                    .eq('source_page_url', source_page_url)\
                    .in_('article_url', article_urls)\
                    .execute()
            
            existing_response = self._execute_with_timeout(_check_existing, query_name)
            
            if existing_response and existing_response.data:
                existing_urls = {row['article_url'] for row in existing_response.data}
            else:
                existing_urls = set()
            
            # Фильтруем только новые URL
            new_urls_to_insert = []
            for url_data in urls_data:
                if url_data['article_url'] not in existing_urls:
                    insert_data = {
                        'source_page_url': url_data['source_page_url'],
                        'article_url': url_data['article_url'],
                        'article_title': url_data.get('title', 'Untitled'),
                        'source_domain': url_data['source_domain'],
                        'is_new': True,
                        'exported_to_articles': False
                    }
                    new_urls_to_insert.append(insert_data)
            
            if not new_urls_to_insert:
                self.logger.debug(f"All {len(urls_data)} URLs already exist")
                return 0
            
            # ОПТИМИЗАЦИЯ: Батч-вставка всех новых URL одним запросом с таймаутом
            query_name = f"batch_insert_urls({len(new_urls_to_insert)} urls)"
            
            def _batch_insert():
                return self.supabase.client.table('tracked_urls').insert(new_urls_to_insert).execute()
            
            response = self._execute_with_timeout(_batch_insert, query_name)
            
            if response and response.data:
                new_count = len(response.data)
                self.logger.info(f"Added {new_count} new tracked URLs to Supabase (batch insert)")
                return new_count
            else:
                self.logger.warning("Batch insert returned no data")
                return 0
                    
        except Exception as e:
            self.logger.error(f"Error in add_tracked_urls: {e}")
            return 0
    
    def get_existing_urls_for_source(self, source_page_url: str) -> Set[str]:
        """Получает существующие URL для определенной страницы источника с таймаутом"""
        query_name = f"get_existing_urls_for_source({source_page_url[:50]}...)"
        
        def _query():
            return self.supabase.client.table('tracked_urls')\
                .select('article_url')\
                .eq('source_page_url', source_page_url)\
                .execute()
        
        response = self._execute_with_timeout(_query, query_name)
        
        if response and response.data:
            return {row['article_url'] for row in response.data}
        return set()
    
    def mark_urls_as_old(self, source_page_url: str) -> bool:
        """Помечает все URL для данного источника как старые (is_new = 0)"""
        try:
            update_data = {'is_new': False}
            
            response = self.supabase.client.table('tracked_urls')\
                .update(update_data)\
                .eq('source_page_url', source_page_url)\
                .eq('is_new', True)\
                .execute()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error marking URLs as old: {e}")
            return False
    
    def get_new_urls(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получает новые неэкспортированные URL"""
        try:
            response = self.supabase.client.table('tracked_urls')\
                .select('id, source_page_url, article_url, article_title, source_domain, discovered_at')\
                .eq('is_new', True)\
                .eq('exported_to_articles', False)\
                .order('discovered_at', desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            self.logger.error(f"Error getting new URLs: {e}")
            return []
    
    def export_urls_to_articles(self, new_urls: List[Dict[str, Any]]) -> int:
        """Экспортирует новые URL в таблицу articles через Supabase с улучшенной обработкой"""
        if not new_urls:
            return 0
        
        from app_logging import log_operation
        from urllib.parse import urlparse
        
        exported_count = 0
        failed_count = 0
        skipped_count = 0
        
        total_urls = len(new_urls)
        self.logger.info(f"Starting export of {total_urls} URLs")
        
        # Проверяем наличие необходимых методов в начале
        if not hasattr(self.supabase, 'insert_article'):
            self.logger.error("CRITICAL: Supabase client doesn't have insert_article method")
            return 0
        
        # ОПТИМИЗАЦИЯ: Батч-проверка существующих URL
        self.logger.info("Performing batch check for existing URLs...")
        try:
            urls_to_check = [url_data['article_url'] for url_data in new_urls]
            
            # Получаем все существующие URL одним запросом
            existing_response = self.supabase.client.table('articles')\
                .select('url')\
                .in_('url', urls_to_check)\
                .execute()
            
            existing_urls = {row['url'] for row in existing_response.data} if existing_response.data else set()
            self.logger.info(f"Found {len(existing_urls)} existing URLs in articles table")
            
        except Exception as e:
            self.logger.error(f"Batch check failed: {e}, falling back to individual checks")
            existing_urls = set()
        
        # Обрабатываем каждый URL по отдельности для надежности
        for idx, url_data in enumerate(new_urls, 1):
            try:
                # Логируем прогресс каждого URL
                article_url = url_data.get('article_url', '')
                source_domain = url_data.get('source_domain', '')
                domain = urlparse(article_url).netloc if article_url else source_domain
                
                log_operation(
                    'change_tracking_export_url',
                    phase='change_tracking',
                    message=f'📤 Exporting [{idx}/{total_urls}]: {domain}',
                    url=article_url,
                    url_index=idx,
                    total_urls=total_urls,
                    success=True
                )
                
                # Мониторинг производительности
                operation_start = time.time()
                
                # Генерируем уникальный ID для статьи
                article_id = f"ct_{str(uuid.uuid4())[:8]}"
                title = url_data.get('article_title', 'Untitled Article')
                
                self.logger.debug(f"Processing URL {idx}/{total_urls}: {article_url}")
                
                # Проверяем дубликаты используя батч-результат
                if article_url in existing_urls:
                    self.logger.debug(f"URL already exists (batch check): {article_url[:100]}")
                    # Помечаем как экспортированный даже если дубликат
                    self._mark_url_as_exported(url_data['id'])
                    skipped_count += 1
                    continue
                
                # Дополнительная проверка только если не найден в батче (на случай race condition)
                if not article_url in existing_urls and hasattr(self.supabase, 'article_exists'):
                    try:
                        exists = self.supabase.article_exists(article_url)
                        if exists:
                            self.logger.debug(f"URL exists (individual check): {article_url[:100]}")
                            self._mark_url_as_exported(url_data['id'])
                            skipped_count += 1
                            continue
                    except Exception as e:
                        self.logger.warning(f"Individual check failed for {article_url[:100]}: {e}")
                        # Продолжаем даже если проверка не удалась
                
                # Создаем source в Supabase если не существует
                try:
                    source_id = self._ensure_supabase_source_exists(source_domain, article_url)
                except Exception as e:
                    self.logger.error(f"Failed to ensure source for {source_domain}: {e}")
                    failed_count += 1
                    continue
                
                # Добавляем в Supabase articles
                article_data = {
                    'article_id': article_id,
                    'source_id': source_id,
                    'url': article_url,
                    'title': title,
                    'content_status': 'pending',
                    'media_status': 'pending',
                    'discovered_via': 'change_tracking',
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                
                # Вставляем статью с обработкой ошибок
                try:
                    result = self.supabase.insert_article(article_data)
                    
                    if result:
                        # Успешно вставлено - помечаем как экспортированный
                        self._mark_url_as_exported(url_data['id'])
                        exported_count += 1
                        
                        # Логируем успех
                        operation_duration = time.time() - operation_start
                        self.logger.info(f"✅ Exported [{idx}/{total_urls}]: {article_url} ({operation_duration:.2f}s)")
                        
                        # Добавляем небольшую задержку чтобы не перегружать API
                        if idx < total_urls:
                            time.sleep(0.1)
                    else:
                        self.logger.warning(f"Insert returned False for: {article_url}")
                        failed_count += 1
                        
                except Exception as e:
                    error_msg = f"Failed to insert article"
                    self.logger.error(f"{error_msg} {article_url}: {e}")
                    
                    # Логируем в errors.jsonl
                    log_error('article_export_failed', error_msg,
                             article_url=article_url[:200],
                             article_id=article_id,
                             source_id=source_id,
                             error_type=type(e).__name__,
                             module='change_tracking_database')
                    failed_count += 1
                    continue
                    
            except Exception as e:
                self.logger.error(f"Unexpected error processing URL {idx}/{total_urls}: {e}")
                failed_count += 1
                continue
        
        # Финальная статистика
        self.logger.info(f"Export completed: {exported_count} exported, {skipped_count} skipped (duplicates), {failed_count} failed")
        
        if failed_count > 0:
            self.logger.warning(f"⚠️ {failed_count} URLs failed to export and will be retried on next run")
        
        return exported_count
    
    def _mark_url_as_exported(self, url_id: int) -> bool:
        """Помечает URL как экспортированный в tracked_urls"""
        try:
            self.supabase.client.table('tracked_urls')\
                .update({
                    'exported_to_articles': True,
                    'exported_at': datetime.now(timezone.utc).isoformat(),
                    'is_new': False
                })\
                .eq('id', url_id)\
                .execute()
            return True
        except Exception as e:
            self.logger.error(f"Failed to mark URL {url_id} as exported: {e}")
            return False
    
    def _ensure_supabase_source_exists(self, source_domain: str, sample_url: str) -> str:
        """Создает source в Supabase если не существует, возвращает source_id"""
        source_id = source_domain
        
        try:
            if not hasattr(self.supabase, 'upsert_source'):
                self.logger.warning("Supabase client doesn't have upsert_source method, using domain as source_id")
                return source_id
            
            # Создаем/обновляем источник в Supabase
            parsed_url = urlparse(sample_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Красивое имя из domain
            name = source_domain.replace('_', ' ').title().replace('Com', '.com')
            
            source_data = {
                'source_id': source_id,
                'name': name,
                'url': base_url,
                'feed_url': None,
                'language': 'en',
                'active': True,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = self.supabase.upsert_source(source_data)
            if result:
                self.logger.debug(f"Ensured Supabase source exists: {source_id} ({name})")
            else:
                self.logger.warning(f"Failed to upsert source to Supabase: {source_id}")
            
            return source_id
            
        except Exception as e:
            self.logger.error(f"Error ensuring Supabase source {source_id}: {e}")
            return source_id
    
    def get_url_extraction_stats(self) -> Dict[str, Any]:
        """Получает статистику извлечения URL"""
        try:
            # Общая статистика
            total_response = self.supabase.client.table('tracked_urls').select('count', count='exact').execute()
            total_urls = total_response.count if total_response else 0
            
            new_response = self.supabase.client.table('tracked_urls').select('count', count='exact').eq('is_new', True).execute()
            new_urls = new_response.count if new_response else 0
            
            exported_response = self.supabase.client.table('tracked_urls').select('count', count='exact').eq('exported_to_articles', True).execute()
            exported_urls = exported_response.count if exported_response else 0
            
            return {
                'total_urls': total_urls,
                'new_urls': new_urls,
                'exported_urls': exported_urls
            }
            
        except Exception as e:
            self.logger.error(f"Error getting URL extraction stats: {e}")
            return {
                'total_urls': 0,
                'new_urls': 0,
                'exported_urls': 0
            }