#!/usr/bin/env python3
"""
URL Extractor for Change Tracking
Извлекает URL статей из markdown контента отслеживаемых страниц
"""
import re
import uuid
import json
from pathlib import Path
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Optional, Set
from datetime import datetime, timezone

from app_logging import get_logger, log_operation


class URLExtractor:
    """Извлекает URL статей из markdown контента"""
    
    def __init__(self):
        self.logger = get_logger('change_tracking.url_extractor')
        
        # Загружаем маппинг источников для правильного source_id
        self.tracking_sources = self._load_tracking_sources()
        
        # Для отслеживания уже залогированных ошибок паттернов (чтобы не спамить)
        self._logged_pattern_errors = set()
        
        # Паттерны для поиска ссылок в markdown
        self.markdown_link_patterns = [
            r'\[([^\]]*)\]\((https?://[^)]+)\)',     # [text](url)
            r'\[([^\]]*)\]:\s*(https?://\S+)',      # [text]: url
            r'<(https?://[^>]+)>',                   # <url>
        ]
        
        # Доменно-специфичные паттерны разрешенных URL
        self.domain_patterns = {
            # AI Companies
            'hai.stanford.edu': [r'/news/[^/]+'],  # Только статьи в /news/
            'openai.com': [r'/blog/', r'/news/', r'/index/', r'/[^/]+/$'],
            'anthropic.com': [r'/news/', r'/research/'],
            'mistral.ai': [r'/news/[^/]+'],
            'cohere.com': [r'/blog/[^/]+', r'/research/[^/]+'],
            'ai21.com': [r'/blog/[^/]+'],
            'stability.ai': [r'/news/[^/]+'],
            'elevenlabs.io': [r'/blog/[^/]+', r'/research/[^/]+'],
            
            # Tech Giants
            'blog.google': [r'/technology/ai/'],
            'research.google': [r'/blog/'],
            'deepmind.google': [r'/blog/', r'/discover/'],
            'news.microsoft.com': [r'/source/features/ai/', r'/source/topics/ai/'],
            'cloud.google.com': [r'/blog/products/ai-machine-learning/'],
            'aws.amazon.com': [r'/blogs/machine-learning/'],
            
            # Platforms & Infrastructure
            'huggingface.co': [r'/blog/', r'/papers/'],
            'blog.cloudflare.com': [r'/[a-z0-9-]+(-[a-z0-9-]*)*/?$'],  # Исправленный паттерн для статей
            'cursor.com': [r'/blog/[^/]+'],  # Статьи в /blog/
            'cursor.sh': [r'/blog/[^/]+'],  # Альтернативный домен Cursor
            'crusoe.ai': [r'/resources/blog/[^/]+'],  # ИСПРАВЛЕНО
            'www.crusoe.ai': [r'/resources/blog/[^/]+'],  # С www
            'cerebras.ai': [r'/blog/[^/]+'],  # ИСПРАВЛЕНО: добавлен www
            'www.cerebras.ai': [r'/blog/[^/]+'],  # Основной домен с www
            'lambda.ai': [r'/blog/[^/]+'],
            'scale.com': [r'/blog/[^/]+'],
            'databricks.com': [r'/blog/'],
            'together.ai': [r'/blog/[^/]+'],
            
            # News & Media
            # blog.perplexity.ai редиректит на www.perplexity.ai/hub
            'perplexity.ai': [r'/hub/blog/[^/]+'],  # Реальный путь к блогу
            'www.perplexity.ai': [r'/hub/blog/[^/]+'],  # Hub blog статьи
            'the-decoder.com': [r'/[^/]+/$'],
            'techcrunch.com': [r'/category/artificial-intelligence/'],
            'venturebeat.com': [r'/ai/'],
            'theverge.com': [r'/ai-artificial-intelligence/'],
            'arstechnica.com': [r'/ai/'],
            'wired.com': [r'/story/'],
            'forbes.com': [r'/sites/'],
            'technologyreview.com': [r'/\d{4}/\d{2}/'],
            
            # Enterprise & Business
            'c3.ai': [r'/blog/[^/]+'],
            'palantir.com': [r'/blog/[^/]+'],
            'datarobot.com': [r'/blog/[^/]+'],
            'instabase.com': [r'/blog/[^/]+'],
            'alpha-sense.com': [r'/blog/[^/]+'],
            'appzen.com': [r'/blog/[^/]+'],
            'b12.io': [r'/blog/[^/]+'],
            'mindfoundry.ai': [r'/blog/[^/]+'],
            'nscale.com': [r'/blog/[^/]+'],
            
            # Robotics
            'waymo.com': [r'/blog/\d{4}/\d{2}/'],
            'new.abb.com': [r'/news/'],
            'fanucamerica.com': [r'/news/'],
            'kinovarobotics.com': [r'/p/[^/]+'],  # Статьи в /p/
            'kuka.com': [r'/company/press/news/\d{4}/\d{2}/[^/]+'],  # Новости KUKA
            'doosanrobotics.com': [r'/news/'],
            'manus.im': [r'/blog/[^/]+'],
            
            # Healthcare AI
            'tempus.com': [r'/blog/[^/]+'],
            'pathai.com': [r'/news/'],
            'augmedix.com': [r'/press-room/[^/]+'],
            'openevidence.com': [r'/announcements/[^/]+'],
            
            # Academic & Research
            'news.mit.edu': [r'/\d{4}/'],
            'ai.stanford.edu': [r'/blog/'],
            
            # Other
            'writer.com': [r'/engineering/[^/]+'],
            'uizard.io': [r'/blog/[^/]+'],
            'soundhound.com': [r'/voice-ai-blog/[^/]+'],
            'audioscenic.com': [r'/news/[^/]+'],
            'suno.com': [r'/blog/[^/]+'],
            
            # Machine Learning Frameworks
            'pytorch.org': [r'/blog/'],
            'tensorflow.org': [r'/blog/'],
            'blog.salesforceairesearch.com': [r'/[^/]+/$'],
            
            # Apple & IBM
            'machinelearning.apple.com': [r'/\d{4}/\d{2}/'],
            'newsroom.ibm.com': [r'/\d{4}-\d{2}-\d{2}/'],
            'blogs.nvidia.com': [r'/blog/\d{4}/\d{2}/'],
        }
        
        # Паттерны для фильтрации нерелевантных URL
        self.exclude_patterns = [
            # КРИТИЧЕСКИ ВАЖНЫЕ ИСКЛЮЧЕНИЯ
            r'/_next/',      # Технические URL Next.js (изображения и др.)
            r'/people/',     # Страницы авторов
            r'/topics/',     # Страницы тем/категорий
            r'/resources/blog$',  # Страница списка блога (без конкретной статьи)
            
            # Навигационные элементы (часто захватываются как заголовки)
            r'Read more',
            r'Arrow Right',
            r'close banner',
            
            # Служебные страницы
            r'/contact',
            r'/about',
            r'/privacy',
            r'/terms',
            r'/legal',
            r'/careers',
            r'/jobs',
            r'/login',
            r'/register',
            r'/subscribe',
            r'/unsubscribe',
            
            # Социальные сети
            r'facebook\.com',
            r'twitter\.com',
            r'linkedin\.com',
            r'instagram\.com',
            r'youtube\.com',
            r'github\.com/[^/]+/?$',  # только корень github репозитория
            
            # Файлы и медиа
            r'\.jpg$',
            r'\.jpeg$', 
            r'\.png$',
            r'\.gif$',
            r'\.webp$',
            r'\.svg$',
            r'\.ico$',
            r'\.css$',
            r'\.js$',
            r'\.xml$',
            r'\.pdf$',
            r'\.zip$',
            r'\.rar$',
            r'\.tar\.gz$',
            
            # Thumbnail и другие изображения
            r'/thumbnail',
            r'/thumb',
            r'/avatar',
            r'/logo',
            r'/icon',
            r'/favicon',
            
            # Навигация и служебные разделы
            r'mailto:',
            r'#\w+',  # якорные ссылки
            r'/tag/',
            r'/category/',
            r'/author/',
            r'/search',
            r'/feed',
            r'/rss',
            r'/sitemap',
            r'/archive$',  # только если это просто /archive
            r'/page/\d+',  # пагинация
            
            # Структурные страницы (не новости)
            r'/department/',
            r'/school/',
            r'/faculty',
            r'/program',
            r'/course',
            r'/team',
            r'/staff',
            r'/office',
            r'/lab$',
            r'/center',
            r'/institute',
            r'/research$',
            r'/services',
            r'/products$',
            r'/solutions$',
            r'/platform',
            r'/api',
            r'/docs',
            r'/resources$',
            r'/support',
            r'/help',
            r'/faq',
            r'/pricing',
            r'/plans',
            
            # Служебные файлы
            r'robots\.txt',
            r'sitemap\.xml',
            r'manifest\.json',
        ]
        
    async def extract_urls_from_content(
        self, 
        markdown_content: str, 
        source_page_url: str,
        use_page_titles: bool = True,
        firecrawl_client = None
    ) -> List[Dict[str, str]]:
        """
        Извлекает URL статей из markdown контента
        
        Args:
            markdown_content: Markdown контент страницы
            source_page_url: URL исходной страницы
            use_page_titles: Если True, получает заголовки через Firecrawl API
            firecrawl_client: Клиент Firecrawl для получения заголовков
            
        Returns:
            List[Dict] со структурой:
            [
                {
                    'article_url': 'https://...',
                    'article_title': 'заголовок',
                    'source_domain': 'domain_name'
                }
            ]
        """
        if not markdown_content or not source_page_url:
            return []
            
        found_urls = []
        source_domain = self._get_source_domain(source_page_url)
        base_url = self._get_base_url(source_page_url)
        
        # Специальная обработка для источников с escape-последовательностями
        escape_sources = [
            'deepmind.google', 'new.abb.com', 'scale.com', 'stability.ai', 'waymo.com', 'c3.ai', 'crusoe.ai', 'cursor.com',
            'databricks.com', 'research.google', 'instabase.com', 'kinovarobotics.com', 'kuka.com', 'manus.im',
            'openevidence.com', 'huggingface.co', 'pathai.com', 'www.perplexity.ai', 'soundhound.com',
            'uizard.io', 'writer.com', 'b12.io', 'cerebras.ai', 'www.cerebras.ai'
        ]
        
        if any(domain in source_page_url for domain in escape_sources):
            found_urls.extend(self._extract_escape_links(markdown_content, source_page_url, source_domain))
        
        # Извлекаем все ссылки из markdown обычным способом
        all_links = self._extract_all_links(markdown_content)
        
        # Фильтруем и обрабатываем ссылки
        for title, url in all_links:
            # Нормализуем URL
            normalized_url = self._normalize_url(url, base_url)
            
            if not normalized_url:
                continue
                
            # Получаем заголовок
            if use_page_titles and firecrawl_client:
                # Пытаемся получить реальный заголовок через Firecrawl API
                real_title = await self._get_page_title(normalized_url, firecrawl_client)
                if real_title:
                    final_title = real_title
                    self.logger.info(f"✅ Using real title: {real_title[:50]}...")
                else:
                    final_title = self._clean_title(title)
                    self.logger.info(f"⚠️ Using fallback title: {final_title}")
            else:
                # Используем старый способ - очищаем заголовок из ссылки
                final_title = self._clean_title(title)
            
            if not final_title:
                continue  # Пропускаем если заголовок нерелевантный
                
            # Проверяем что это релевантная статья
            if self._is_article_url(normalized_url, source_page_url):
                found_urls.append({
                    'article_url': normalized_url,
                    'article_title': final_title,
                    'source_domain': source_domain
                })
        
        # Удаляем дубликаты по URL
        seen_urls = set()
        unique_urls = []
        for item in found_urls:
            if item['article_url'] not in seen_urls:
                seen_urls.add(item['article_url'])
                unique_urls.append(item)
        
        self.logger.info(f"Extracted {len(unique_urls)} unique URLs from {source_page_url}")
        
        # Log to operations for monitoring
        try:
            # Если 0 URLs - это НЕ успех
            success = len(unique_urls) > 0
            log_operation('change_tracking_urls_extracted',
                phase='change_tracking',
                source_url=source_page_url,
                urls_found=len(unique_urls),
                source_domain=source_domain,
                success=success
            )
            
            # Если 0 URLs - также логируем как ошибку
            if not success:
                from app_logging import log_error
                error_msg = f"URL extraction failed: 0 URLs from {source_domain}"
                self.logger.error(f"❌ {error_msg} - check patterns in url_extractor.py")
                log_error('url_extraction_zero_results', error_msg,
                         source_url=source_page_url,
                         source_domain=source_domain,
                         module='change_tracking.url_extractor')
        except Exception as e:
            self.logger.debug(f"Failed to log operation: {e}")
        
        return unique_urls
    
    def _extract_all_links(self, content: str) -> List[tuple]:
        """Извлекает все ссылки из markdown контента"""
        links = []
        
        # Предварительная очистка для Cursor-style markdown
        # Убираем \\\\ которые используются для переносов строк в некоторых markdown форматах
        # Некоторые системы экранируют их дважды, поэтому убираем все варианты
        cleaned_content = content.replace('\\\\', ' ').replace('\\', ' ')
        
        # Также ищем ссылки в формате ](url) в конце multiline блоков
        # Паттерн для multiline markdown: текст может быть на нескольких строками
        # Изменен паттерн чтобы учитывать пробелы и переносы строк между ] и (
        multiline_pattern = r'\[([^\]]+?)\]\s*\((https?://[^)]+)\)'
        # Добавлен флаг MULTILINE для корректной обработки переносов строк
        matches = re.finditer(multiline_pattern, cleaned_content, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        for match in matches:
            title = match.group(1).strip()
            url = match.group(2).strip()
            links.append((title, url))
        
        # Также ищем стандартные паттерны на оригинальном контенте
        for pattern in self.markdown_link_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                if pattern == r'<(https?://[^>]+)>':
                    # Для паттерна <url> нет текста
                    links.append(('', match.group(1)))
                elif len(match.groups()) >= 2:
                    links.append((match.group(1), match.group(2)))
                    
        return links
    
    def _extract_escape_links(self, content: str, source_page_url: str, source_domain: str) -> List[Dict[str, str]]:
        """Извлекает ссылки из контента с escape-последовательностями \\\\"""
        escape_links = []
        
        # Паттерн для DeepMind/ABB формата: текст\\\\еще текст\\\\дата](url)
        escape_pattern = r'([^]]*?(?:\\\\[^]]*?)*?)\]\((https?://[^)]+)\)'
        matches = re.finditer(escape_pattern, content, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            text_block = match.group(1)
            url = match.group(2).strip()
            
            # Нормализуем URL
            normalized_url = self._normalize_url(url, source_page_url)
            if not normalized_url or not self._is_article_url(normalized_url, source_page_url):
                continue
                
            # Извлекаем заголовок из текстового блока
            lines = text_block.split('\\\\')
            title = None
            longest_title = ''
            skip_categories = ['Models', 'Science', 'Research', 'Company', 'Responsibility & Safety',
                              'Press release', 'Group press release', 'Customer story']
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('![') and not line.startswith('http') and not line.startswith('['):
                    clean_line = line.replace('**', '').strip()
                    if clean_line not in skip_categories and len(clean_line) > len(longest_title):
                        longest_title = clean_line
            
            if longest_title:
                title = longest_title
            else:
                # Fallback: генерируем заголовок из URL
                title = self._generate_title_from_url(normalized_url)
            
            # Если все еще нет заголовка, используем дефолтный с контекстом
            if not title:
                title = f"Article from {source_domain}"
            
            escape_links.append({
                'article_url': normalized_url,
                'article_title': title,
                'source_domain': source_domain
            })
        
        return escape_links
    
    def _normalize_url(self, url: str, base_url: str) -> Optional[str]:
        """Нормализует и валидирует URL"""
        try:
            # Убираем пробелы
            url = url.strip()
            
            # Обрабатываем относительные URL
            if url.startswith('/'):
                url = urljoin(base_url, url)
            elif not url.startswith(('http://', 'https://')):
                # Пропускаем невалидные URL
                return None
                
            # Убираем якоря и параметры запроса для деплурации
            parsed = urlparse(url)
            
            # Приводим к HTTPS для деduplication (предпочитаем HTTPS)
            scheme = 'https'
            clean_url = f"{scheme}://{parsed.netloc}{parsed.path}"
            
            # Убираем trailing slash если это не корень
            if clean_url.endswith('/') and len(parsed.path) > 1:
                clean_url = clean_url.rstrip('/')
                
            return clean_url
            
        except Exception as e:
            self.logger.warning(f"Error normalizing URL {url}: {e}")
            return None
    
    def _is_article_url(self, url: str, source_page_url: str) -> bool:
        """Проверяет является ли URL релевантной статьей"""
        # Исключаем сам исходный URL
        if url == source_page_url:
            return False
            
        # Проверяем исключающие паттерны
        for pattern in self.exclude_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        # Проверяем что URL принадлежит тому же домену или поддомену
        source_domain = urlparse(source_page_url).netloc.lower()
        url_domain = urlparse(url).netloc.lower()
        
        # Разрешаем только URL с того же домена или его поддоменов
        if not (url_domain == source_domain or url_domain.endswith('.' + source_domain)):
            return False
            
        # URL должен быть длиннее чем базовая страница (т.е. содержать путь к статье)
        source_path = urlparse(source_page_url).path.rstrip('/')
        url_path = urlparse(url).path.rstrip('/')
        
        if len(url_path) <= len(source_path):
            return False
        
        # НОВАЯ ЛОГИКА: Используем доменно-специфичные паттерны если они есть
        if source_domain in self.domain_patterns:
            # Для известных доменов используем строгие паттерны
            allowed_patterns = self.domain_patterns[source_domain]
            for pattern in allowed_patterns:
                if re.search(pattern, url_path, re.IGNORECASE):
                    return True
            # Если не совпал ни один паттерн - отклоняем
            # ЛОГИРОВАНИЕ: паттерны не работают для этого домена (только раз за сессию)
            if source_domain not in self._logged_pattern_errors:
                self._logged_pattern_errors.add(source_domain)
                from app_logging import log_error
                error_msg = f"Pattern mismatch for {source_domain}: URL paths don't match configured patterns: {allowed_patterns}"
                self.logger.error(f"❌ {error_msg}")
                log_error('url_pattern_mismatch', error_msg,
                         domain=source_domain,
                         sample_url_path=url_path, 
                         patterns=str(allowed_patterns),
                         module='change_tracking.url_extractor')
            return False
            
        # Для неизвестных доменов используем общие новостные паттерны
        news_patterns = [
            r'/news/',
            r'/blog/',
            r'/press/',
            r'/announcement',
            r'/2024/',
            r'/2025/',
            r'/article/',
            r'/post/',
            r'/story/',
            r'/release/'
        ]
        
        # Если URL содержит новостные паттерны - определенно хорошо
        for pattern in news_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        # Для остальных URL проверяем что они не слишком короткие (вероятно структурные страницы)
        if len(url_path.split('/')) < 3:  # Например /about, /team - слишком короткие
            return False
            
        return True
    
    def _clean_title(self, title: str) -> str:
        """Очищает заголовок статьи"""
        if not title:
            return None
            
        # Убираем лишние пробелы и символы
        cleaned = re.sub(r'\s+', ' ', title.strip())
        
        # Убираем escape-последовательности
        cleaned = cleaned.replace('\\\\', ' ')  # Заменяем \\\\ на пробел
        cleaned = cleaned.replace('\\', '')      # Убираем одинарные слеши
        cleaned = re.sub(r'\s+', ' ', cleaned)   # Снова нормализуем пробелы
        
        # Убираем лишние разделители
        cleaned = cleaned.replace(' ・ ', ' - ')  # Японская точка на дефис
        cleaned = re.sub(r'\s*-\s*-\s*', ' - ', cleaned)  # Множественные дефисы
        
        # Исключаем markdown image alt text и другие нерелевантные заголовки
        invalid_titles = [
            '![', '!', 'submit', 'archive', 'more', 'learn more', 
            'see more', 'read more', 'click here', 'here', 'link',
            'image', 'photo', 'picture', 'logo', 'icon', 'thumbnail',
            'view more', 'more info', 'details', 'info', 'continue',
            'next', 'previous', 'back', 'home', 'menu', 'search',
            'contact', 'about', 'team', 'careers', 'join', 'apply',
            'subscribe', 'newsletter', 'follow', 'share', 'like',
            'download', 'get', 'try', 'start', 'sign up', 'login',
            'register', 'book', 'schedule', 'request', 'demo',
            'free', 'now', 'today', 'new', 'latest',
            # Дополнительные исключения для OpenAI и других сайтов
            'view all', 'see all', 'all posts', 'all articles',
            'load more', 'show more', 'explore', 'discover',
            'browse', 'filter', 'sort', 'category', 'tag',
            # НОВЫЕ исключения для навигационных элементов
            'read more arrow right', 'arrow right', 'arrow left',
            'close banner', 'close', 'read now', 'continue reading',
            'read article', 'read story', 'read post', 'full article',
            'full story', 'learn more arrow', 'arrow', '→', '←',
            'skip to content', 'skip', 'jump to', 'go to'
        ]
        
        if cleaned.lower() in invalid_titles:
            return None
            
        # Исключаем заголовки которые состоят только из символов
        if re.match(r'^[^\w\s]*$', cleaned):
            return None
            
        # Минимальная длина заголовка
        if len(cleaned) < 3:
            return None
            
        # Убираем markdown форматирование
        cleaned = re.sub(r'\*+', '', cleaned)  # жирный/курсив
        cleaned = re.sub(r'`+', '', cleaned)   # код
        cleaned = re.sub(r'#+\s*', '', cleaned)  # заголовки
        
        # Убираем HTML теги если есть
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        
        # Ограничиваем длину
        if len(cleaned) > 200:
            cleaned = cleaned[:200] + '...'
            
        final_title = cleaned.strip()
        
        # Финальная проверка на осмысленность
        if not final_title or len(final_title) < 3:
            return None
            
        return final_title
    
    def _generate_title_from_url(self, url: str) -> Optional[str]:
        """
        Генерирует заголовок из URL пути
        
        Примеры:
        /blog/ai-powered-hvac-optimization -> "AI Powered HVAC Optimization"
        /news/2024/05/new-model-release -> "New Model Release"
        """
        try:
            parsed = urlparse(url)
            path = parsed.path.rstrip('/')
            
            # Берем последний сегмент пути
            segments = [s for s in path.split('/') if s]
            if not segments:
                return None
                
            # Берем последний значимый сегмент (пропускаем даты и номера)
            title_segment = None
            for segment in reversed(segments):
                # Пропускаем сегменты которые выглядят как даты или номера
                if not re.match(r'^\d{4}$|^\d{2}$|^\d+$|^page-\d+$', segment):
                    title_segment = segment
                    break
                    
            if not title_segment:
                return None
                
            # Преобразуем дефисы и подчеркивания в пробелы
            title = title_segment.replace('-', ' ').replace('_', ' ')
            
            # Убираем расширения файлов если есть
            title = re.sub(r'\.(html?|php|aspx?)$', '', title, flags=re.IGNORECASE)
            
            # Капитализируем слова
            title_words = []
            for word in title.split():
                # Не капитализируем короткие служебные слова
                if len(word) <= 2 and word.lower() in ['a', 'an', 'at', 'by', 'in', 'of', 'on', 'or', 'to']:
                    title_words.append(word.lower())
                # Сохраняем аббревиатуры в верхнем регистре
                elif word.isupper() and len(word) > 1:
                    title_words.append(word)
                else:
                    title_words.append(word.capitalize())
            
            final_title = ' '.join(title_words)
            
            # Проверяем минимальную длину
            if len(final_title) < 3:
                return None
                
            return final_title
            
        except Exception as e:
            self.logger.warning(f"Error generating title from URL {url}: {e}")
            return None
    
    def _load_tracking_sources(self) -> Dict[str, str]:
        """Загружает маппинг URL -> source_id из tracking_sources.json"""
        sources_map = {}
        json_file = Path(__file__).parent.parent / 'data' / 'tracking_sources.json'
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for source in data.get('tracking_sources', []):
                    # Маппим URL на source_id
                    sources_map[source['url']] = source['source_id']
                    # Также без trailing slash
                    sources_map[source['url'].rstrip('/')] = source['source_id']
            self.logger.info(f"URLExtractor loaded {len(sources_map)} tracking sources from JSON")
        except Exception as e:
            self.logger.error(f"Failed to load tracking_sources.json: {e}")
        
        return sources_map
    
    def _get_source_domain(self, source_page_url: str) -> str:
        """Получает правильный source_id из tracking_sources.json"""
        # Используем тот же source_id что и ChangeMonitor
        clean_url = source_page_url.rstrip('/')
        
        # Проверяем точное совпадение URL
        if clean_url in self.tracking_sources:
            return self.tracking_sources[clean_url]
        
        # Проверяем без www
        if clean_url.startswith('https://www.'):
            no_www = clean_url.replace('https://www.', 'https://')
            if no_www in self.tracking_sources:
                return self.tracking_sources[no_www]
        
        # Fallback к генерации из домена (для обратной совместимости)
        try:
            domain = urlparse(source_page_url).netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain.replace('.', '_').replace('-', '_')
        except:
            return 'unknown_source'
    
    def _get_base_url(self, url: str) -> str:
        """Получает базовый URL (схема + домен)"""
        try:
            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc}"
        except:
            return url
    
    def generate_article_id(self) -> str:
        """Генерирует уникальный ID для статьи"""
        return str(uuid.uuid4())[:8]
    
    def find_new_urls(
        self, 
        current_urls: List[Dict[str, str]], 
        existing_urls: Set[str]
    ) -> List[Dict[str, str]]:
        """
        Находит новые URL которых не было в предыдущем скане
        
        Args:
            current_urls: Текущий список найденных URL
            existing_urls: Set существующих URL из БД
            
        Returns:
            Список новых URL
        """
        new_urls = []
        for url_data in current_urls:
            if url_data['article_url'] not in existing_urls:
                new_urls.append(url_data)
                
        self.logger.info(f"Found {len(new_urls)} new URLs out of {len(current_urls)} total")
        return new_urls
    
    async def _get_page_title(self, url: str, firecrawl_client) -> Optional[str]:
        """
        Получает реальный заголовок страницы через Firecrawl API
        
        Args:
            url: URL страницы
            firecrawl_client: Клиент Firecrawl
            
        Returns:
            Заголовок страницы или None если не удалось получить
        """
        
        # ФИЛЬТРАЦИЯ: не запрашиваем заголовки для служебных URL
        exclude_title_patterns = [
            r'/_next/',     # Next.js assets  
            r'/images/',    # Image URLs
            r'/static/',    # Static files
            r'\.svg$',      # SVG files
            r'\.jpg$',      # Image files
            r'\.png$',      # Image files
            r'\.gif$',      # Image files
            r'\.webp$',     # Image files
            r'cdn\.', r'-cdn\.', # CDN URLs
            r'twitter\.com', r'x\.com',  # Social media
            r'linkedin\.com', r'facebook\.com',  # Social media
            r'/press-kit',  # Large files
            r'support\.',   # Support sites (usually not articles)
        ]
        
        for pattern in exclude_title_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                self.logger.debug(f"⏩ Skipping title fetch for: {url} (matches {pattern})")
                return None
        
        try:
            self.logger.info(f"🔍 Fetching page title for: {url[:50]}...")
            
            # Rate limiting - пауза между запросами
            import asyncio
            await asyncio.sleep(2.0)  # 2 секунды пауза для стабильности
            
            # Запрашиваем только metadata для экономии токенов
            scraped_data = await firecrawl_client.scrape_url(
                url, 
                formats=['markdown']  # Минимальный формат
            )
            
            # Извлекаем заголовок из метаданных
            metadata = scraped_data.get('metadata', {})
            page_title = metadata.get('title', '').strip()
            
            if page_title and len(page_title) > 5:  # Минимальная проверка качества
                # Очищаем заголовок от лишних символов
                cleaned_title = page_title.replace('\n', ' ').replace('\r', ' ')
                cleaned_title = ' '.join(cleaned_title.split())  # Нормализуем пробелы
                
                self.logger.info(f"✅ Got page title: {cleaned_title[:50]}...")
                return cleaned_title
                
        except Exception as e:
            self.logger.warning(f"Failed to get page title for {url}: {e}")
            
        return None
    
    def get_stats(self, urls: List[Dict[str, str]]) -> Dict[str, int]:
        """Получает статистику извлеченных URL"""
        if not urls:
            return {'total': 0, 'domains': 0}
            
        domains = set(item['source_domain'] for item in urls)
        
        return {
            'total': len(urls),
            'domains': len(domains),
            'avg_title_length': sum(len(item.get('article_title', '')) for item in urls) // len(urls)
        }