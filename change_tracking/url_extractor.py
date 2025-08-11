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

from app_logging import get_logger


class URLExtractor:
    """Извлекает URL статей из markdown контента"""
    
    def __init__(self):
        self.logger = get_logger('change_tracking.url_extractor')
        
        # Загружаем маппинг источников для правильного source_id
        self.tracking_sources = self._load_tracking_sources()
        
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
            'openai.com': [r'/blog/', r'/news/'],
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
            'news.microsoft.com': [r'/source/topics/ai/'],
            'cloud.google.com': [r'/blog/products/ai-machine-learning/'],
            'aws.amazon.com': [r'/blogs/machine-learning/'],
            
            # Platforms & Infrastructure
            'huggingface.co': [r'/blog/', r'/papers/'],
            'blog.cloudflare.com': [r'/[a-z0-9-]+/?$'],  # Улучшенный паттерн
            'cursor.com': [r'/blog/[^/]+'],  # Статьи в /blog/
            'cursor.sh': [r'/blog/[^/]+'],  # Альтернативный домен Cursor
            'crusoe.ai': [r'/resources/blog/[^/]+'],  # ИСПРАВЛЕНО
            'www.crusoe.ai': [r'/resources/blog/[^/]+'],  # С www
            'cerebras.ai': [r'/blog/[^/]+'],
            'lambda.ai': [r'/blog/[^/]+'],
            'scale.com': [r'/blog/[^/]+'],
            'databricks.com': [r'/blog/'],
            'together.ai': [r'/blog/[^/]+'],
            
            # News & Media
            'blog.perplexity.ai': [r'/[^/]+$'],
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
            'standardbots.com': [r'/blog/[^/]+'],
            'new.abb.com': [r'/news/'],
            'fanucamerica.com': [r'/news/'],
            'kinovarobotics.com': [r'/news/'],
            'doosanrobotics.com': [r'/news/'],
            'manus.im': [r'/blog/[^/]+'],
            
            # Healthcare AI
            'tempus.com': [r'/blog/[^/]+'],
            'pathai.com': [r'/news/[^/]+'],
            'augmedix.com': [r'/press-room/[^/]+'],
            'openevidence.com': [r'/announcements/[^/]+'],
            
            # Academic & Research
            'news.mit.edu': [r'/\d{4}/'],
            'ai.stanford.edu': [r'/blog/'],
            
            # Other
            'writer.com': [r'/blog/[^/]+'],
            'uizard.io': [r'/blog/[^/]+'],
            'soundhound.com': [r'/blog/[^/]+'],
            'audioscenic.com': [r'/news/[^/]+'],
            'suno.com': [r'/blog/[^/]+'],
            'research.runwayml.com': [r'/papers/[^/]+'],
            
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
        
    def extract_urls_from_content(
        self, 
        markdown_content: str, 
        source_page_url: str
    ) -> List[Dict[str, str]]:
        """
        Извлекает URL статей из markdown контента
        
        Args:
            markdown_content: Markdown контент страницы
            source_page_url: URL исходной страницы
            
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
        
        # Извлекаем все ссылки из markdown
        all_links = self._extract_all_links(markdown_content)
        
        # Фильтруем и обрабатываем ссылки
        for title, url in all_links:
            # Нормализуем URL
            normalized_url = self._normalize_url(url, base_url)
            
            if not normalized_url:
                continue
                
            # Очищаем заголовок
            clean_title = self._clean_title(title)
            if not clean_title:
                continue  # Пропускаем если заголовок нерелевантный
                
            # Проверяем что это релевантная статья
            if self._is_article_url(normalized_url, source_page_url):
                found_urls.append({
                    'article_url': normalized_url,
                    'article_title': clean_title,
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
        return unique_urls
    
    def _extract_all_links(self, content: str) -> List[tuple]:
        """Извлекает все ссылки из markdown контента"""
        links = []
        
        # Предварительная очистка для Cursor-style markdown
        # Убираем \\\\ которые используются для переносов строк в некоторых markdown форматах
        # Некоторые системы экранируют их дважды, поэтому убираем все варианты
        cleaned_content = content.replace('\\\\', ' ').replace('\\', ' ')
        
        # Также ищем ссылки в формате ](url) в конце multiline блоков
        # Паттерн для multiline markdown: текст может быть на нескольких строках
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