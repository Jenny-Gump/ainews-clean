#!/usr/bin/env python3
"""
Change Tracking Database Operations
Изолированная работа с таблицей tracked_articles
"""

import sqlite3
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Set
from pathlib import Path
from urllib.parse import urlparse

from app_logging import get_logger
from core.database import Database


class ChangeTrackingDB:
    """Управление базой данных для отслеживания изменений"""
    
    def __init__(self):
        self.logger = get_logger('change_tracking.database')
        self.db = Database()
    
    def create_tracked_article(
        self, 
        article_id: str, 
        source_id: str, 
        url: str, 
        title: str,
        content: str = "",
        content_hash: str = ""
    ) -> bool:
        """Создает новую запись отслеживания"""
        try:
            with self.db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO tracked_articles (
                        article_id, source_id, url, title,
                        content, current_hash, change_detected,
                        change_status, last_checked
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article_id, source_id, url, title,
                    content, content_hash, 1,
                    'new', datetime.now(timezone.utc).isoformat()
                ))
                
            self.logger.info(f"Created tracked article: {article_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating tracked article {article_id}: {e}")
            return False
    
    def update_tracked_article(
        self,
        article_id: str,
        content: str,
        new_hash: str,
        change_status: str = 'changed'
    ) -> bool:
        """Обновляет существующую запись при изменении"""
        try:
            with self.db.get_connection() as conn:
                conn.execute("""
                    UPDATE tracked_articles 
                    SET previous_hash = current_hash,
                        current_hash = ?,
                        content = ?,
                        change_detected = 1,
                        change_status = ?,
                        last_checked = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE article_id = ?
                """, (
                    new_hash, content, change_status,
                    datetime.now(timezone.utc).isoformat(),
                    article_id
                ))
                
            self.logger.info(f"Updated tracked article: {article_id} ({change_status})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating tracked article {article_id}: {e}")
            return False
    
    def mark_unchanged(self, article_id: str) -> bool:
        """Отмечает статью как не изменившуюся"""
        try:
            with self.db.get_connection() as conn:
                conn.execute("""
                    UPDATE tracked_articles 
                    SET last_checked = ?,
                        change_detected = 0,
                        change_status = 'unchanged'
                    WHERE article_id = ?
                """, (
                    datetime.now(timezone.utc).isoformat(),
                    article_id
                ))
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error marking unchanged {article_id}: {e}")
            return False
    
    def get_tracked_article_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Получает отслеживаемую статью по URL"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM tracked_articles WHERE url = ?",
                    (url,)
                )
                row = cursor.fetchone()
                
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting tracked article by URL {url}: {e}")
            return None
    
    def get_tracking_stats(self) -> Dict[str, Any]:
        """Получает статистику отслеживания"""
        stats = {}
        
        try:
            with self.db.get_connection() as conn:
                # Общее количество
                cursor = conn.execute("SELECT COUNT(*) FROM tracked_articles")
                result = cursor.fetchone()
                stats['total_tracked'] = result[0] if result else 0
                
                # По статусам
                cursor = conn.execute("""
                    SELECT change_status, COUNT(*) 
                    FROM tracked_articles 
                    GROUP BY change_status
                """)
                status_counts = cursor.fetchall()
                stats['by_status'] = {row[0] or 'unknown': row[1] for row in status_counts}
                
                # Последние изменения
                cursor = conn.execute("""
                    SELECT url, change_status, last_checked 
                    FROM tracked_articles 
                    WHERE change_detected = 1
                    ORDER BY last_checked DESC 
                    LIMIT 10
                """)
                stats['recent_changes'] = [
                    {'url': row[0], 'status': row[1], 'checked': row[2]}
                    for row in cursor.fetchall()
                ]
                
                # Источники
                cursor = conn.execute("""
                    SELECT source_id, COUNT(*) 
                    FROM tracked_articles 
                    GROUP BY source_id
                """)
                stats['by_source'] = {row[0]: row[1] for row in cursor.fetchall()}
                
        except Exception as e:
            self.logger.error(f"Error getting tracking stats: {e}")
            stats = {'error': str(e)}
        
        return stats
    
    def get_changed_articles(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получает статьи с изменениями для экспорта"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM tracked_articles 
                    WHERE change_detected = 1 
                    AND exported_to_main = 0
                    ORDER BY last_checked DESC
                    LIMIT ?
                """, (limit,))
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Error getting changed articles: {e}")
            return []
    
    def mark_exported(self, article_ids: List[str]) -> bool:
        """Отмечает статьи как экспортированные"""
        try:
            with self.db.get_connection() as conn:
                for article_id in article_ids:
                    conn.execute("""
                        UPDATE tracked_articles 
                        SET exported_to_main = 1,
                            exported_at = ?
                        WHERE article_id = ?
                    """, (
                        datetime.now(timezone.utc).isoformat(),
                        article_id
                    ))
                    
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
            
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM tracked_articles 
                    WHERE created_at < ?
                    AND exported_to_main = 1
                """, (cutoff_date.isoformat(),))
                
                deleted_count = cursor.rowcount
                
            self.logger.info(f"Cleaned up {deleted_count} old tracking records")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old records: {e}")
            return 0
    
    def get_all_tracked_urls(self) -> List[Dict[str, Any]]:
        """Получает все отслеживаемые URL"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("SELECT url FROM tracked_articles")
                return [{'url': row[0]} for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting tracked URLs: {e}")
            return []
    
    def get_sources_with_errors(self) -> List[str]:
        """Получает источники с ошибками для повторного сканирования"""
        try:
            with self.db.get_connection() as conn:
                # Пока что возвращаем пустой список, так как нет столбца для ошибок
                # В будущем здесь будет запрос для источников со статусом 'error'
                return []
        except Exception as e:
            self.logger.error(f"Error getting sources with errors: {e}")
            return []
    
    # ========================================
    # URL Extraction Methods
    # ========================================
    
    def store_tracked_urls(
        self, 
        source_page_url: str, 
        urls_data: List[Dict[str, str]]
    ) -> int:
        """
        Сохраняет извлеченные URL в таблицу tracked_urls
        
        Args:
            source_page_url: URL страницы-каталога
            urls_data: Список словарей с данными URL
            
        Returns:
            Количество добавленных новых URL
        """
        if not urls_data:
            return 0
            
        try:
            new_count = 0
            with self.db.get_connection() as conn:
                for url_data in urls_data:
                    try:
                        conn.execute("""
                            INSERT INTO tracked_urls (
                                source_page_url, article_url, article_title, 
                                source_domain, is_new, exported_to_articles
                            ) VALUES (?, ?, ?, ?, 1, 0)
                        """, (
                            source_page_url,
                            url_data['article_url'],
                            url_data.get('article_title', ''),
                            url_data['source_domain']
                        ))
                        new_count += 1
                    except sqlite3.IntegrityError:
                        # URL уже существует (UNIQUE constraint)
                        continue
                        
            if new_count > 0:
                self.logger.info(f"Stored {new_count} new URLs from {source_page_url}")
            else:
                self.logger.debug(f"No new URLs found for {source_page_url}")
                
            return new_count
            
        except Exception as e:
            self.logger.error(f"Error storing tracked URLs: {e}")
            return 0
    
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
            with self.db.get_connection() as conn:
                for url_data in urls_data:
                    try:
                        conn.execute("""
                            INSERT INTO tracked_urls (
                                source_page_url, article_url, article_title, 
                                source_domain, is_new, exported_to_articles
                            ) VALUES (?, ?, ?, ?, 0, 0)
                        """, (
                            source_page_url,
                            url_data['article_url'],
                            url_data.get('article_title', ''),
                            url_data['source_domain']
                        ))
                        baseline_count += 1
                    except sqlite3.IntegrityError:
                        # URL уже существует (UNIQUE constraint)
                        continue
                        
            if baseline_count > 0:
                self.logger.info(f"Stored {baseline_count} baseline URLs from {source_page_url}")
            else:
                self.logger.debug(f"No baseline URLs stored for {source_page_url}")
                
            return baseline_count
            
        except Exception as e:
            self.logger.error(f"Error storing baseline URLs: {e}")
            return 0
    
    def get_existing_urls_for_source(self, source_page_url: str) -> Set[str]:
        """Получает существующие URL для определенной страницы источника"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT article_url 
                    FROM tracked_urls 
                    WHERE source_page_url = ?
                """, (source_page_url,))
                
                return {row[0] for row in cursor.fetchall()}
                
        except Exception as e:
            self.logger.error(f"Error getting existing URLs for {source_page_url}: {e}")
            return set()
    
    def mark_urls_as_old(self, source_page_url: str) -> bool:
        """Помечает все URL для данного источника как старые (is_new = 0)"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    UPDATE tracked_urls 
                    SET is_new = 0 
                    WHERE source_page_url = ? AND is_new = 1
                """, (source_page_url,))
                
                updated_count = cursor.rowcount
                if updated_count > 0:
                    self.logger.debug(f"Marked {updated_count} URLs as old for {source_page_url}")
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error marking URLs as old: {e}")
            return False
    
    def get_new_urls(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получает новые неэкспортированные URL"""
        # Исправление: проверяем limit на None для предотвращения datatype mismatch
        if limit is None:
            limit = 100
            
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, source_page_url, article_url, article_title, 
                           source_domain, discovered_at
                    FROM tracked_urls 
                    WHERE is_new = 1 AND exported_to_articles = 0
                    ORDER BY discovered_at DESC
                    LIMIT ?
                """, (limit,))
                
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Error getting new URLs: {e}")
            return []
    
    def export_urls_to_articles(self, new_urls: List[Dict[str, Any]]) -> int:
        """
        Экспортирует новые URL в таблицу articles
        
        Args:
            new_urls: Список новых URL для экспорта
            
        Returns:
            Количество успешно экспортированных URL
        """
        if not new_urls:
            return 0
            
        exported_count = 0
        
        try:
            with self.db.get_connection() as conn:
                for url_data in new_urls:
                    try:
                        # Генерируем уникальный ID для статьи
                        article_id = str(uuid.uuid4())[:8]
                        source_domain = url_data['source_domain']
                        article_url = url_data['article_url']
                        title = url_data.get('article_title', 'Untitled Article')
                        
                        # Создаем source если не существует
                        source_id = self._ensure_source_exists(conn, source_domain, article_url)
                        
                        # Добавляем статью в articles
                        conn.execute("""
                            INSERT INTO articles (
                                article_id, source_id, url, title,
                                content_status, media_status, discovered_via
                            ) VALUES (?, ?, ?, ?, 'pending', 'pending', 'change_tracking')
                        """, (article_id, source_id, article_url, title))
                        
                        # Помечаем URL как экспортированный и сбрасываем флаг is_new
                        conn.execute("""
                            UPDATE tracked_urls 
                            SET exported_to_articles = 1, 
                                exported_at = ?,
                                is_new = 0
                            WHERE id = ?
                        """, (
                            datetime.now(timezone.utc).isoformat(),
                            url_data['id']
                        ))
                        
                        exported_count += 1
                        
                    except sqlite3.IntegrityError as e:
                        # URL уже существует в articles
                        self.logger.warning(f"Article URL already exists: {article_url}")
                        # Все равно помечаем как экспортированный и сбрасываем is_new
                        conn.execute("""
                            UPDATE tracked_urls 
                            SET exported_to_articles = 1, 
                                exported_at = ?,
                                is_new = 0
                            WHERE id = ?
                        """, (
                            datetime.now(timezone.utc).isoformat(),
                            url_data['id']
                        ))
                        continue
                        
                    except Exception as e:
                        self.logger.error(f"Error exporting URL {article_url}: {e}")
                        continue
                        
            self.logger.info(f"Exported {exported_count} URLs to articles table")
            return exported_count
            
        except Exception as e:
            self.logger.error(f"Error in export_urls_to_articles: {e}")
            return 0
    
    def _ensure_source_exists(self, conn, source_domain: str, sample_url: str) -> str:
        """Создает source если не существует, возвращает source_id"""
        source_id = source_domain
        
        try:
            # Проверяем существование
            cursor = conn.execute("SELECT source_id FROM sources WHERE source_id = ?", (source_id,))
            if cursor.fetchone():
                return source_id
            
            # Создаем новый источник
            parsed_url = urlparse(sample_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Красивое имя из domain
            name = source_domain.replace('_', ' ').title()
            
            conn.execute("""
                INSERT INTO sources (
                    source_id, name, url, type, has_rss, 
                    success_rate, total_articles
                ) VALUES (?, ?, ?, 'change_tracking', 0, 0.0, 0)
            """, (source_id, name, base_url))
            
            self.logger.info(f"Created new source: {source_id} ({name})")
            return source_id
            
        except Exception as e:
            self.logger.error(f"Error ensuring source exists for {source_domain}: {e}")
            return source_id
    
    def get_url_extraction_stats(self) -> Dict[str, Any]:
        """Получает статистику извлечения URL"""
        try:
            with self.db.get_connection() as conn:
                # Общая статистика
                cursor = conn.execute("SELECT COUNT(*) FROM tracked_urls")
                total_urls = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM tracked_urls WHERE is_new = 1")
                new_urls = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM tracked_urls WHERE exported_to_articles = 1")
                exported_urls = cursor.fetchone()[0]
                
                # По доменам
                cursor = conn.execute("""
                    SELECT source_domain, COUNT(*) 
                    FROM tracked_urls 
                    GROUP BY source_domain
                    ORDER BY COUNT(*) DESC
                    LIMIT 10
                """)
                top_domains = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Последние добавленные
                cursor = conn.execute("""
                    SELECT article_url, article_title, source_domain, discovered_at
                    FROM tracked_urls 
                    WHERE is_new = 1 
                    ORDER BY discovered_at DESC
                    LIMIT 10
                """)
                recent_urls = [
                    {
                        'url': row[0], 'title': row[1], 
                        'domain': row[2], 'discovered': row[3]
                    } 
                    for row in cursor.fetchall()
                ]
                
                return {
                    'total_urls': total_urls,
                    'new_urls': new_urls,
                    'exported_urls': exported_urls,
                    'pending_export': new_urls - exported_urls,
                    'top_domains': top_domains,
                    'recent_urls': recent_urls
                }
                
        except Exception as e:
            self.logger.error(f"Error getting URL extraction stats: {e}")
            return {'error': str(e)}