#!/usr/bin/env python3
"""
Extract RSS Discovery Service - RSS поиск для Extract API системы
Адаптированная версия для параллельной Extract API системы
"""
import os
import asyncio
import aiohttp
import feedparser
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import hashlib
from dotenv import load_dotenv
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import Database
from app_logging import get_logger

# Load environment variables
load_dotenv()


class ExtractRSSDiscovery:
    """
    Сервис для обнаружения новых статей через RSS ленты
    Сохраняет только базовую информацию со статусом 'pending'
    """
    
    def __init__(self):
        self.logger = get_logger('extract_system.rss_discovery')
        self.db = Database()
        
        # Загружаем источники с RSS для Extract API системы
        self.rss_sources = self._load_rss_sources()
        
        # Настройки
        self.batch_size = 10  # Размер батча для параллельной обработки RSS
        self.default_days_back = 7  # По умолчанию проверяем 7 дней назад
        
        self.logger.info(
            f"ExtractRSSDiscovery initialized",
            rss_sources_count=len(self.rss_sources)
        )
    
    def _load_rss_sources(self) -> List[Dict]:
        """Загружает источники с RSS из sources_extract.json"""
        sources = []
        
        try:
            # Загружаем из sources_extract.json для Extract API системы
            sources_path = os.path.join(os.path.dirname(__file__), 'sources_extract.json')
            with open(sources_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Фильтруем только источники с RSS
            for source in data['sources']:
                if source.get('rss_url'):
                    sources.append({
                        'id': source['id'],
                        'name': source['name'],
                        'url': source['url'],
                        'rss_url': source['rss_url']
                    })
                    
            self.logger.info(f"Loaded {len(sources)} RSS sources from sources_extract.json")
            
        except Exception as e:
            self.logger.error(f"Error loading RSS sources for Extract API: {e}")
            
        return sources
    
    def load_sources(self) -> List[Dict]:
        """Публичный метод для получения списка источников"""
        return self.rss_sources
    
    def _generate_article_id(self, url: str) -> str:
        """Генерирует article_id из URL (первые 16 символов SHA256)"""
        return hashlib.sha256(url.encode()).hexdigest()[:16]
    
    def _resolve_google_redirect(self, url: str) -> str:
        """Резолвит Google redirect ссылки синхронно"""
        if 'google.com/url' not in url:
            return url
            
        try:
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            if 'url' in params:
                final_url = params['url'][0]
                return final_url
        except Exception as e:
            self.logger.debug(f"Could not parse Google redirect: {e}")
            
        return url
    
    def _is_blocked_domain(self, url: str) -> bool:
        """Проверяет, является ли домен заблокированным (соцсети и т.д.)"""
        blocked_domains = {
            'youtube.com', 'www.youtube.com', 'youtu.be', 'm.youtube.com',
            'facebook.com', 'www.facebook.com', 'm.facebook.com', 'fb.com',
            'instagram.com', 'www.instagram.com',
            'twitter.com', 'www.twitter.com', 'x.com', 'www.x.com',
            'reddit.com', 'www.reddit.com', 'm.reddit.com',
            'linkedin.com', 'www.linkedin.com',
            'tiktok.com', 'www.tiktok.com',
            'telegram.org', 'www.telegram.org', 't.me',
            'discord.com', 'www.discord.com', 'discord.gg',
            'pinterest.com', 'www.pinterest.com',
            'snapchat.com', 'www.snapchat.com',
            'whatsapp.com', 'www.whatsapp.com'
        }
        
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Убираем www. префикс для проверки
            domain_clean = domain.replace('www.', '')
            
            return domain in blocked_domains or domain_clean in blocked_domains
        except Exception:
            return False
    
    async def fetch_rss_feed(self, session: aiohttp.ClientSession, source: Dict) -> Tuple[str, List[Dict]]:
        """
        Загружает и парсит RSS ленту
        
        Returns:
            Tuple[source_id, List[articles]]
        """
        source_id = source['id']
        rss_url = source['rss_url']
        articles = []
        
        try:
            # Получаем глобальный last_parsed timestamp
            global_last_parsed = self.db.get_global_last_parsed()
            try:
                last_parsed = datetime.fromisoformat(global_last_parsed.replace('Z', '+00:00'))
                # Ensure timezone awareness
                if last_parsed.tzinfo is None:
                    last_parsed = last_parsed.replace(tzinfo=timezone.utc)
            except:
                # Fallback if parsing fails
                last_parsed = datetime.now(timezone.utc) - timedelta(days=self.default_days_back)
            
            self.logger.debug(
                f"Fetching RSS for {source_id}",
                rss_url=rss_url,
                last_parsed=last_parsed.isoformat()
            )
            
            # Загружаем RSS
            async with session.get(rss_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    self.logger.warning(
                        f"RSS fetch failed for {source_id}",
                        status=response.status,
                        url=rss_url
                    )
                    return source_id, []
                
                content = await response.text()
            
            # Парсим RSS
            feed = feedparser.parse(content)
            
            if feed.bozo:
                self.logger.warning(
                    f"RSS parse warning for {source_id}",
                    error=str(feed.bozo_exception)
                )
            
            # Обрабатываем записи (максимум 5 на источник)
            articles_found = 0
            MAX_ARTICLES_PER_SOURCE = 5
            
            for entry in feed.entries:
                if articles_found >= MAX_ARTICLES_PER_SOURCE:
                    break
                # Извлекаем дату публикации
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                
                # Пропускаем старые статьи
                if published and published <= last_parsed:
                    continue
                
                # Проверяем URL
                url = entry.get('link', '')
                if not url:
                    continue
                
                # Резолвим Google redirects и проверяем на заблокированные домены
                final_url = self._resolve_google_redirect(url)
                if self._is_blocked_domain(final_url):
                    self.logger.debug(f"Skipped blocked domain: {final_url[:100]}")
                    continue
                
                # Проверяем, нет ли уже в БД
                if self.db.article_exists(url):
                    self.logger.debug(f"Article already exists: {url[:100]}")
                    continue
                
                # Извлекаем данные
                title = entry.get('title', '').strip()
                description = entry.get('summary', '').strip()
                
                if not title:
                    self.logger.warning(f"Skipping article without title: {url}")
                    continue
                
                articles.append({
                    'article_id': self._generate_article_id(url),
                    'source_id': source_id,
                    'url': url,
                    'title': title,
                    'description': description,
                    'published_date': published,
                    'content_status': 'pending',
                    'discovered_via': 'rss'
                })
                articles_found += 1
            
            self.logger.info(
                f"RSS discovery for {source_id}",
                total_entries=len(feed.entries),
                new_articles=len(articles),
                last_parsed=last_parsed.isoformat()
            )
            
        except asyncio.TimeoutError:
            self.logger.error(f"RSS timeout for {source_id}: {rss_url}")
        except Exception as e:
            self.logger.error(
                f"RSS error for {source_id}",
                error=str(e),
                url=rss_url
            )
        
        return source_id, articles
    
    async def discover_from_sources(self, source_ids: Optional[List[str]] = None, progress_tracker=None) -> Dict:
        """
        Обнаруживает новые статьи из RSS лент
        
        Args:
            source_ids: Список ID источников (если None - все RSS источники)
            progress_tracker: Optional ParsingProgressTracker instance
            
        Returns:
            Статистика обнаружения
        """
        # Фильтруем источники
        if source_ids:
            sources_to_process = [
                s for s in self.rss_sources 
                if s['id'] in source_ids
            ]
        else:
            sources_to_process = self.rss_sources
        
        if not sources_to_process:
            self.logger.warning("No RSS sources to process")
            return {'sources_processed': 0, 'articles_discovered': 0, 'articles_saved': 0}
        
        self.logger.info(
            "Starting RSS discovery",
            sources_count=len(sources_to_process)
        )
        
        # Start RSS discovery phase tracking
        if progress_tracker:
            progress_tracker.start_phase('rss_discovery', len(sources_to_process))
        
        stats = {
            'sources_processed': 0,
            'articles_discovered': 0,
            'articles_saved': 0,
            'errors': 0,
            'new_articles': 0
        }
        
        # Создаем HTTP сессию
        connector = aiohttp.TCPConnector(limit=10)
        async with aiohttp.ClientSession(connector=connector) as session:
            
            # Обрабатываем батчами для контроля нагрузки
            for i in range(0, len(sources_to_process), self.batch_size):
                batch = sources_to_process[i:i + self.batch_size]
                
                # Параллельно загружаем RSS ленты в батче
                tasks = [
                    self.fetch_rss_feed(session, source)
                    for source in batch
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Обрабатываем результаты
                for result in results:
                    if isinstance(result, Exception):
                        self.logger.error(f"Batch processing error: {result}")
                        stats['errors'] += 1
                        if progress_tracker:
                            progress_tracker.update_phase_progress('rss_discovery', {
                                'processed_feeds': 1,
                                'errors': 1
                            })
                        continue
                    
                    source_id, articles = result
                    stats['sources_processed'] += 1
                    stats['articles_discovered'] += len(articles)
                    
                    # Update progress tracker
                    if progress_tracker:
                        source_name = next((s['name'] for s in self.rss_sources if s['id'] == source_id), source_id)
                        progress_tracker.update_source(source_id, source_name)
                        progress_tracker.update_phase_progress('rss_discovery', {
                            'processed_feeds': 1,
                            'total_articles_found': len(articles)
                        })
                    
                    # Сохраняем статьи в БД
                    for article in articles:
                        try:
                            # Используем insert_article метод из database.py
                            saved_id = self.db.insert_article(article)
                            if saved_id:
                                stats['articles_saved'] += 1
                                stats['new_articles'] += 1
                                if progress_tracker:
                                    progress_tracker.update_phase_progress('rss_discovery', {
                                        'new_articles_found': 1
                                    })
                            else:
                                # insert_article возвращает None если статья уже существует
                                self.logger.debug(f"Article not saved (duplicate?): {article['url'][:100]}")
                        except Exception as e:
                            self.logger.error(
                                f"Error saving article",
                                error=str(e),
                                url=article['url'][:100]
                            )
                            stats['errors'] += 1
                    
                    # Note: Global last_parsed is now managed centrally, not per-source
                    # This prevents the synchronization issues we had before
                
                # Небольшая задержка между батчами
                if i + self.batch_size < len(sources_to_process):
                    await asyncio.sleep(1)
        
        # Обновляем глобальный last_parsed timestamp после завершения
        if stats['new_articles'] > 0:
            try:
                current_time = datetime.now(timezone.utc)
                timestamp_str = current_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                self.db.set_global_last_parsed(timestamp_str)
                self.logger.info(f"Updated global last_parsed to: {timestamp_str}")
            except Exception as e:
                self.logger.error(f"Error updating global last_parsed: {e}")
        
        # Финальная статистика и завершение
        self.logger.info(
            f"RSS discovery completed: {stats['sources_processed']} источников обработано, "
            f"{stats['new_articles']} новых статей найдено, "
            f"{stats['articles_saved']} статей сохранено, "
            f"{stats['errors']} ошибок"
        )
        
        # Финальное сообщение о завершении фазы
        self.logger.info("===== RSS DISCOVERY PHASE COMPLETED =====")
        
        # Complete RSS discovery phase
        if progress_tracker:
            progress_tracker.complete_phase('rss_discovery')
        
        return stats
    
    async def discover_with_playwright_fallback(self, source_ids: List[str]) -> Dict:
        """
        Обнаружение с fallback на Playwright для проблемных RSS
        (Будет реализовано позже при необходимости)
        """
        # TODO: Implement Playwright fallback for problematic RSS feeds
        return await self.discover_from_sources(source_ids)


async def test_rss_discovery():
    """Тестирует RSS Discovery на нескольких источниках"""
    
    discovery = RssDiscoveryService()
    
    # Тестируем на небольшом наборе источников
    test_sources = ['openai', 'google_ai', 'microsoft_ai']
    
    print(f"Testing RSS Discovery on sources: {test_sources}")
    print(f"Available RSS sources: {len(discovery.rss_sources)}")
    
    # Запускаем discovery
    stats = await discovery.discover_from_sources(test_sources)
    
    print("\nDiscovery Results:")
    print(f"Sources processed: {stats['sources_processed']}")
    print(f"Articles discovered: {stats['articles_discovered']}")
    print(f"Articles saved: {stats['articles_saved']}")
    print(f"Errors: {stats['errors']}")
    
    # Проверяем pending статьи в БД
    db = Database()
    pending_count = db.get_pending_articles_count()
    print(f"\nTotal pending articles in DB: {pending_count}")


if __name__ == "__main__":
    asyncio.run(test_rss_discovery())