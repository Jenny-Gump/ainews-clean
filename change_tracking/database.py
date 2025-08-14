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

from app_logging import get_logger
from core.db_config import DatabaseConfig


class ChangeTrackingDB:
    """Управление базой данных для отслеживания изменений через Supabase"""
    
    def __init__(self):
        self.logger = get_logger('change_tracking.database')
        self.supabase = DatabaseConfig.get_database()  # Supabase client
    
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
            self.logger.error(f"Error creating tracked article {article_id}: {e}")
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
            self.logger.error(f"Error getting tracked article by URL {url}: {e}")
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
        Сохраняет извлеченные URL в таблицу tracked_urls в Supabase
        
        Args:
            source_page_url: URL страницы-каталога
            urls_data: Список словарей с данными URL
            
        Returns:
            Количество добавленных новых URL
        """
        if not urls_data:
            return 0
            
        return self.add_tracked_urls(urls_data)
    
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
                    self.logger.error(f"Error adding baseline URL {url_data.get('article_url', 'unknown')}: {e}")
                    continue
                        
            if baseline_count > 0:
                self.logger.info(f"Stored {baseline_count} baseline URLs from {source_page_url}")
            else:
                self.logger.debug(f"No baseline URLs stored for {source_page_url}")
                
            return baseline_count
            
        except Exception as e:
            self.logger.error(f"Error storing baseline URLs: {e}")
            return 0
    
    def add_tracked_urls(self, urls_data: List[Dict[str, Any]]) -> int:
        """Добавляет новые отслеживаемые URL в Supabase"""
        try:
            new_count = 0
            for url_data in urls_data:
                try:
                    # Проверяем существует ли уже этот URL
                    existing = self.supabase.client.table('tracked_urls')\
                        .select('id')\
                        .eq('source_page_url', url_data['source_page_url'])\
                        .eq('article_url', url_data['article_url'])\
                        .limit(1)\
                        .execute()
                    
                    if existing.data and len(existing.data) > 0:
                        continue  # URL уже существует
                    
                    # Добавляем новый URL
                    insert_data = {
                        'source_page_url': url_data['source_page_url'],
                        'article_url': url_data['article_url'],
                        'article_title': url_data.get('title', 'Untitled'),
                        'source_domain': url_data['source_domain'],
                        'is_new': True,
                        'exported_to_articles': False
                    }
                    
                    response = self.supabase.client.table('tracked_urls').insert(insert_data).execute()
                    
                    if response.data:
                        new_count += 1
                        self.logger.debug(f"Added new tracked URL: {url_data['article_url']}")
                        
                except Exception as e:
                    self.logger.error(f"Error adding tracked URL {url_data.get('article_url', 'unknown')}: {e}")
                    continue
            
            self.logger.info(f"Added {new_count} new tracked URLs to Supabase")
            return new_count
            
        except Exception as e:
            self.logger.error(f"Error in add_tracked_urls: {e}")
            return 0
    
    def get_existing_urls_for_source(self, source_page_url: str) -> Set[str]:
        """Получает существующие URL для определенной страницы источника"""
        try:
            response = self.supabase.client.table('tracked_urls')\
                .select('article_url')\
                .eq('source_page_url', source_page_url)\
                .execute()
            
            if response.data:
                return {row['article_url'] for row in response.data}
            return set()
            
        except Exception as e:
            self.logger.error(f"Error getting existing URLs for {source_page_url}: {e}")
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
        """Экспортирует новые URL в таблицу articles через Supabase"""
        if not new_urls:
            return 0
            
        exported_count = 0
        
        try:
            for url_data in new_urls:
                try:
                    # Генерируем уникальный ID для статьи
                    article_id = f"ct_{str(uuid.uuid4())[:8]}"  # ct_ prefix для change tracking
                    source_domain = url_data['source_domain']
                    article_url = url_data['article_url']
                    title = url_data.get('article_title', 'Untitled Article')
                    
                    # Проверяем дубликаты в Supabase
                    if hasattr(self.supabase, 'article_exists') and self.supabase.article_exists(article_url):
                        self.logger.debug(f"URL already exists in Supabase: {article_url}")
                        # Помечаем как экспортированный и продолжаем
                        self.supabase.client.table('tracked_urls')\
                            .update({
                                'exported_to_articles': True,
                                'exported_at': datetime.now(timezone.utc).isoformat(),
                                'is_new': False
                            })\
                            .eq('id', url_data['id'])\
                            .execute()
                        continue
                    
                    # Создаем source в Supabase если не существует
                    source_id = self._ensure_supabase_source_exists(source_domain, article_url)
                    
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
                    
                    if hasattr(self.supabase, 'insert_article'):
                        result = self.supabase.insert_article(article_data)
                        if result:
                            # Помечаем URL как экспортированный в tracking DB
                            self.supabase.client.table('tracked_urls')\
                                .update({
                                    'exported_to_articles': True,
                                    'exported_at': datetime.now(timezone.utc).isoformat(),
                                    'is_new': False
                                })\
                                .eq('id', url_data['id'])\
                                .execute()
                            
                            exported_count += 1
                            self.logger.debug(f"Exported URL to Supabase articles: {article_url}")
                        else:
                            self.logger.warning(f"Failed to insert article to Supabase: {article_url}")
                    else:
                        self.logger.error("Supabase client doesn't have insert_article method")
                        break
                    
                except Exception as e:
                    self.logger.error(f"Error exporting URL {url_data.get('article_url', 'unknown')}: {e}")
                    continue
                    
            self.logger.info(f"Successfully exported {exported_count} URLs to Supabase articles table")
            return exported_count
            
        except Exception as e:
            self.logger.error(f"Error in export_urls_to_articles: {e}")
            return 0
    
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