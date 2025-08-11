#!/usr/bin/env python3
"""
Web Monitor Service
Мониторинг веб-страниц (не RSS) на предмет новых статей и изменений
"""

import asyncio
import hashlib
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse

from app_logging import get_logger
from core.database import Database
from services.firecrawl_client import FirecrawlClient


def generate_id() -> str:
    """Generate a unique ID for articles"""
    return str(uuid.uuid4())[:8]


class WebMonitor:
    """Мониторинг изменений на веб-страницах"""
    
    def __init__(self):
        self.logger = get_logger('services.web_monitor')
        self.db = Database()
        self.firecrawl = FirecrawlClient()
        
    def _generate_hash(self, content: str) -> str:
        """Generate hash for content comparison"""
        if not content:
            return ""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    async def monitor_webpage(self, url: str, extract_links: bool = True) -> Dict[str, Any]:
        """
        Мониторит веб-страницу и находит статьи/изменения
        
        Args:
            url: URL веб-страницы для мониторинга
            extract_links: Извлекать ли ссылки на статьи со страницы
            
        Returns:
            Dict с результатами мониторинга
        """
        self.logger.info(f"Monitoring webpage: {url}")
        
        results = {
            'url': url,
            'status': 'pending',
            'articles_found': [],
            'changes_detected': [],
            'errors': [],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            async with self.firecrawl as client:
                # Сначала проверяем изменения на самой странице
                self.logger.debug(f"Checking page changes: {url}")
                
                # Получаем содержимое страницы с changeTracking
                scraped_data = await client.scrape_url(
                    url,
                    formats=['markdown', 'changeTracking', 'links']
                )
                
                # Извлекаем данные
                markdown_content = scraped_data.get('markdown', '')
                change_tracking = scraped_data.get('changeTracking', {})
                links = scraped_data.get('links', [])
                
                # Генерируем хэш для отслеживания изменений
                content_hash = self._generate_hash(markdown_content)
                
                # Проверяем, отслеживали ли мы эту страницу ранее
                with self.db.get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT article_id, current_hash FROM tracked_articles WHERE url = ?",
                        (url,)
                    )
                    existing = cursor.fetchone()
                
                if existing:
                    # Страница уже отслеживается
                    if existing[1] != content_hash:
                        self.logger.info(f"Changes detected on: {url}")
                        results['changes_detected'].append({
                            'url': url,
                            'previous_hash': existing[1],
                            'current_hash': content_hash,
                            'change_status': 'changed'
                        })
                        
                        # Обновляем в БД
                        with self.db.get_connection() as conn:
                            conn.execute("""
                                UPDATE tracked_articles 
                                SET previous_hash = current_hash,
                                    current_hash = ?,
                                    content = ?,
                                    change_detected = 1,
                                    change_status = 'changed',
                                    last_checked = ?,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE url = ?
                            """, (content_hash, markdown_content, 
                                  datetime.now(timezone.utc).isoformat(), url))
                else:
                    # Новая страница для отслеживания
                    self.logger.info(f"New page for tracking: {url}")
                    
                    # Извлекаем заголовок из контента
                    title = self._extract_title(markdown_content, url)
                    
                    # Добавляем в отслеживание
                    article_id = generate_id()
                    source_id = urlparse(url).netloc.replace('.', '_')
                    
                    with self.db.get_connection() as conn:
                        conn.execute("""
                            INSERT INTO tracked_articles (
                                article_id, source_id, url, title,
                                content, current_hash, change_detected,
                                change_status, last_checked
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            article_id, source_id, url, title,
                            markdown_content, content_hash, 1,
                            'new', datetime.now(timezone.utc).isoformat()
                        ))
                    
                    results['changes_detected'].append({
                        'url': url,
                        'article_id': article_id,
                        'change_status': 'new'
                    })
                
                # Если нужно извлечь ссылки на статьи
                if extract_links and links:
                    self.logger.info(f"Found {len(links)} links on page")
                    
                    # Фильтруем ссылки (ищем потенциальные статьи)
                    article_links = self._filter_article_links(links, url)
                    
                    self.logger.info(f"Filtered to {len(article_links)} potential articles")
                    
                    # Проверяем каждую ссылку
                    for link in article_links[:20]:  # Ограничиваем количество
                        try:
                            # Проверяем, не отслеживаем ли уже эту статью
                            with self.db.get_connection() as conn:
                                cursor = conn.execute(
                                    "SELECT article_id FROM tracked_articles WHERE url = ?",
                                    (link,)
                                )
                                if cursor.fetchone():
                                    continue  # Уже отслеживаем
                            
                            # Получаем содержимое статьи
                            article_data = await client.scrape_url(
                                link,
                                formats=['markdown', 'changeTracking']
                            )
                            
                            article_content = article_data.get('markdown', '')
                            if article_content:
                                # Извлекаем заголовок
                                article_title = self._extract_title(article_content, link)
                                
                                # Добавляем в результаты
                                results['articles_found'].append({
                                    'url': link,
                                    'title': article_title,
                                    'source_url': url,
                                    'content_preview': article_content[:500]
                                })
                                
                                # Сохраняем в БД для отслеживания
                                article_id = generate_id()
                                source_id = urlparse(url).netloc.replace('.', '_')
                                
                                with self.db.get_connection() as conn:
                                    conn.execute("""
                                        INSERT INTO tracked_articles (
                                            article_id, source_id, url, title,
                                            content, current_hash, change_detected,
                                            change_status, last_checked,
                                            published_date
                                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        article_id, source_id, link, article_title,
                                        article_content, self._generate_hash(article_content),
                                        1, 'new', datetime.now(timezone.utc).isoformat(),
                                        datetime.now(timezone.utc).isoformat()
                                    ))
                                
                        except Exception as e:
                            self.logger.warning(f"Error processing link {link}: {e}")
                            results['errors'].append({
                                'url': link,
                                'error': str(e)
                            })
                
                results['status'] = 'completed'
                self.logger.info(f"Monitoring completed: {len(results['articles_found'])} articles, "
                               f"{len(results['changes_detected'])} changes")
                
        except Exception as e:
            self.logger.error(f"Error monitoring {url}: {e}")
            results['status'] = 'failed'
            results['errors'].append({
                'url': url,
                'error': str(e)
            })
        
        return results
    
    def _extract_title(self, markdown_content: str, url: str) -> str:
        """Извлекает заголовок из markdown контента"""
        lines = markdown_content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
            elif line.startswith('## '):
                return line[3:].strip()
        
        # Fallback to URL
        return urlparse(url).path.strip('/').replace('-', ' ').replace('_', ' ').title()
    
    def _filter_article_links(self, links: List[str], base_url: str) -> List[str]:
        """Фильтрует ссылки, оставляя только потенциальные статьи"""
        filtered = []
        base_domain = urlparse(base_url).netloc
        
        # Ключевые слова для статей
        article_keywords = [
            'blog', 'post', 'article', 'news', 'story',
            '2024', '2025', 'announcement', 'release'
        ]
        
        # Исключаемые паттерны
        exclude_patterns = [
            'tag/', 'category/', 'author/', 'page/', 'about',
            'contact', 'privacy', 'terms', '.pdf', '.zip',
            'subscribe', 'login', 'register', '#'
        ]
        
        for link in links:
            # Проверяем, что это абсолютный URL
            if not link.startswith('http'):
                continue
                
            # Проверяем, что это тот же домен
            if urlparse(link).netloc != base_domain:
                continue
            
            # Исключаем нежелательные паттерны
            if any(pattern in link.lower() for pattern in exclude_patterns):
                continue
            
            # Приоритет статьям с ключевыми словами
            if any(keyword in link.lower() for keyword in article_keywords):
                filtered.append(link)
            # Или если путь достаточно длинный (вероятно статья)
            elif len(urlparse(link).path) > 20:
                filtered.append(link)
        
        # Убираем дубликаты
        return list(set(filtered))
    
    async def monitor_multiple_pages(self, urls: List[str]) -> Dict[str, Any]:
        """Мониторит несколько страниц параллельно"""
        results = {
            'total_monitored': 0,
            'total_articles': 0,
            'total_changes': 0,
            'total_errors': 0,
            'details': []
        }
        
        tasks = []
        for url in urls:
            tasks.append(self.monitor_webpage(url))
        
        # Выполняем параллельно
        page_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(page_results):
            if isinstance(result, Exception):
                self.logger.error(f"Error monitoring {urls[i]}: {result}")
                results['total_errors'] += 1
                results['details'].append({
                    'url': urls[i],
                    'status': 'error',
                    'error': str(result)
                })
            else:
                results['total_monitored'] += 1
                results['total_articles'] += len(result.get('articles_found', []))
                results['total_changes'] += len(result.get('changes_detected', []))
                results['total_errors'] += len(result.get('errors', []))
                results['details'].append(result)
        
        return results
    
    async def export_to_main(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Экспортирует найденные статьи в основную таблицу articles"""
        self.logger.info("Exporting tracked articles to main database")
        
        results = {
            'exported': 0,
            'duplicates': 0,
            'errors': 0,
            'articles': []
        }
        
        # Получаем статьи для экспорта
        with self.db.get_connection() as conn:
            query = """
                SELECT article_id, source_id, url, title, content, published_date
                FROM tracked_articles
                WHERE change_detected = 1 
                AND exported_to_main = 0
                AND change_status IN ('new', 'changed')
            """
            if limit:
                query += f" LIMIT {limit}"
            
            cursor = conn.execute(query)
            articles = cursor.fetchall()
        
        self.logger.info(f"Found {len(articles)} articles to export")
        
        for article in articles:
            article_id, source_id, url, title, content, published_date = article
            
            try:
                # Проверяем дубликаты
                with self.db.get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT article_id FROM articles WHERE url = ?",
                        (url,)
                    )
                    if cursor.fetchone():
                        results['duplicates'] += 1
                        continue
                
                # Экспортируем в основную таблицу
                new_id = generate_id()
                with self.db.get_connection() as conn:
                    conn.execute("""
                        INSERT INTO articles (
                            article_id, source_id, url, title,
                            content, content_status, discovered_via,
                            published_date, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        new_id, source_id, url, title,
                        content, 'pending', 'web_monitoring',
                        published_date
                    ))
                
                # Помечаем как экспортированную
                with self.db.get_connection() as conn:
                    conn.execute("""
                        UPDATE tracked_articles 
                        SET exported_to_main = 1,
                            exported_at = CURRENT_TIMESTAMP
                        WHERE article_id = ?
                    """, (article_id,))
                
                results['exported'] += 1
                results['articles'].append({
                    'article_id': new_id,
                    'url': url,
                    'title': title
                })
                
            except Exception as e:
                self.logger.error(f"Error exporting {article_id}: {e}")
                results['errors'] += 1
        
        self.logger.info(f"Export completed: {results['exported']} exported, "
                        f"{results['duplicates']} duplicates, {results['errors']} errors")
        
        return results