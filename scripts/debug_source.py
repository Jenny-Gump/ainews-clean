#!/usr/bin/env python3
"""
Source Debug Utility
Получает реальный markdown контент от Firecrawl для анализа паттернов извлечения URL
"""

import sys
import json
import re
import argparse
import asyncio
from pathlib import Path

# Добавляем пути к системе
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import Config
from services.firecrawl_client import FirecrawlClient
from app_logging import get_logger


class SourceDebugger:
    """Утилита для анализа источников и создания extractors"""
    
    def __init__(self):
        self.logger = get_logger('source_debugger')
        self.config = Config()
        self.firecrawl = FirecrawlClient()
        
        # Загружаем конфигурацию extractors
        self.extractors_config_path = Path(__file__).parent.parent / 'services' / 'source_extractors.json'
        self.load_extractors_config()
        
    def load_extractors_config(self):
        """Загружает конфигурацию extractors"""
        try:
            with open(self.extractors_config_path, 'r', encoding='utf-8') as f:
                self.extractors_config = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load extractors config: {e}")
            self.extractors_config = {"extractors": {}}
    
    def get_source_info(self, source_id: str):
        """Получает информацию об источнике из конфигурации"""
        if source_id in self.extractors_config.get("extractors", {}):
            return self.extractors_config["extractors"][source_id]
        else:
            self.logger.error(f"Source {source_id} not found in extractors config")
            return None
    
    async def fetch_source_content(self, source_id: str, show_content: bool = False):
        """Получает markdown контент источника через Firecrawl"""
        source_info = self.get_source_info(source_id)
        if not source_info:
            return None
            
        url = source_info['url']
        self.logger.info(f"Fetching content from: {url}")
        
        try:
            # Получаем markdown контент
            async with self.firecrawl:
                result = await self.firecrawl.scrape_url(url, formats=['markdown'])
            
            if not result or not result.get('success'):
                self.logger.error(f"Failed to fetch content from {url}")
                return None
                
            markdown = result.get('data', {}).get('markdown', '')
            
            if not markdown:
                self.logger.warning(f"No markdown content received from {url}")
                return None
            
            # Сохраняем контент для анализа
            content_file = Path(__file__).parent / f"content_{source_id}.md"
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            self.logger.info(f"Content saved to: {content_file}")
            self.logger.info(f"Content length: {len(markdown)} characters")
            
            if show_content:
                print(f"\n=== MARKDOWN CONTENT FOR {source_id.upper()} ===")
                print(f"URL: {url}")
                print(f"Length: {len(markdown)} characters")
                print("=" * 60)
                print(markdown[:2000])  # Показываем первые 2000 символов
                if len(markdown) > 2000:
                    print(f"\n... (truncated, full content in {content_file})")
                print("=" * 60)
                
            return markdown
            
        except Exception as e:
            self.logger.error(f"Error fetching content from {url}: {e}")
            return None
    
    async def analyze_links(self, source_id: str, content: str = None):
        """Анализирует ссылки в markdown контенте"""
        if not content:
            content = await self.fetch_source_content(source_id)
            if not content:
                return
        
        source_info = self.get_source_info(source_id)
        base_url = source_info['url']
        
        print(f"\n=== LINK ANALYSIS FOR {source_id.upper()} ===")
        
        # Извлекаем все markdown ссылки
        link_patterns = [
            r'\[([^\]]*)\]\((https?://[^)]+)\)',  # [text](url)
            r'<(https?://[^>]+)>',                # <url>
            r'href=["\']([^"\']+)["\']',          # href="url"
        ]
        
        all_links = []
        
        for pattern in link_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                if pattern == r'<(https?://[^>]+)>':
                    all_links.append(('', match.group(1)))
                elif pattern == r'href=["\']([^"\']+)["\']':
                    all_links.append(('', match.group(1)))
                else:
                    all_links.append((match.group(1), match.group(2)))
        
        # Фильтруем ссылки по домену
        domain = base_url.replace('https://', '').replace('http://', '').split('/')[0]
        relevant_links = []
        
        for title, url in all_links:
            if domain.replace('www.', '') in url or url.startswith('/'):
                relevant_links.append((title, url))
        
        print(f"Found {len(relevant_links)} relevant links:")
        
        for i, (title, url) in enumerate(relevant_links[:10], 1):
            print(f"{i}. [{title[:50]}{'...' if len(title) > 50 else ''}]")
            print(f"   URL: {url}")
            
        if len(relevant_links) > 10:
            print(f"... and {len(relevant_links) - 10} more links")
            
        return relevant_links
    
    async def test_patterns(self, source_id: str):
        """Тестирует существующие patterns для источника"""
        source_info = self.get_source_info(source_id)
        if not source_info:
            return
            
        content = await self.fetch_source_content(source_id)
        if not content:
            return
            
        patterns = source_info.get('patterns', [])
        
        print(f"\n=== PATTERN TESTING FOR {source_id.upper()} ===")
        print(f"Testing {len(patterns)} patterns:")
        
        for i, pattern in enumerate(patterns, 1):
            print(f"\nPattern {i}: {pattern}")
            matches = re.finditer(pattern, content, re.IGNORECASE)
            match_count = 0
            
            for match in matches:
                match_count += 1
                if match_count <= 5:  # Показываем первые 5 совпадений
                    if len(match.groups()) >= 2:
                        title, url = match.group(1), match.group(2)
                        print(f"  Match {match_count}: [{title[:40]}] -> {url}")
                    else:
                        print(f"  Match {match_count}: {match.group(0)}")
            
            if match_count == 0:
                print(f"  No matches found for pattern {i}")
            else:
                print(f"  Total matches: {match_count}")
    
    async def suggest_patterns(self, source_id: str):
        """Предлагает паттерны на основе анализа контента"""
        content = await self.fetch_source_content(source_id)
        if not content:
            return
            
        links = await self.analyze_links(source_id, content)
        if not links:
            return
            
        source_info = self.get_source_info(source_id)
        base_domain = source_info['url'].replace('https://', '').replace('http://', '').split('/')[0]
        
        print(f"\n=== PATTERN SUGGESTIONS FOR {source_id.upper()} ===")
        
        # Анализируем структуру URL
        url_patterns = set()
        for title, url in links:
            if base_domain.replace('www.', '') in url:
                # Создаем паттерн на основе реального URL
                escaped_domain = re.escape(base_domain.replace('www.', ''))
                url_path = url.split(base_domain)[-1] if base_domain in url else url
                
                # Создаем generic паттерн
                generic_pattern = url_path
                generic_pattern = re.sub(r'/[^/]+$', '/[^/]+', generic_pattern)  # Заменяем последний сегмент
                generic_pattern = re.sub(r'\d{4}', r'\\d{4}', generic_pattern)   # Года
                generic_pattern = re.sub(r'-\w+', r'-[^/]+', generic_pattern)    # Slug части
                
                pattern = f"\\[([^\\]]+)\\]\\((https://{escaped_domain}{re.escape(generic_pattern)})\\)"
                url_patterns.add(pattern)
        
        print("Suggested patterns:")
        for i, pattern in enumerate(url_patterns, 1):
            print(f"{i}. {pattern}")
            
        # Также предлагаем href паттерн
        href_pattern = f'href=["\'](https://{re.escape(base_domain)}/[^"\']+)["\'"]'
        print(f"{len(url_patterns) + 1}. {href_pattern}")


async def main():
    """Основная функция утилиты"""
    parser = argparse.ArgumentParser(description='Debug source extractors')
    parser.add_argument('--source', required=True, help='Source ID to debug')
    parser.add_argument('--show-content', action='store_true', help='Show markdown content')
    parser.add_argument('--analyze-links', action='store_true', help='Analyze links in content')
    parser.add_argument('--test-patterns', action='store_true', help='Test existing patterns')
    parser.add_argument('--suggest-patterns', action='store_true', help='Suggest new patterns')
    
    args = parser.parse_args()
    
    debugger = SourceDebugger()
    
    if args.show_content:
        await debugger.fetch_source_content(args.source, show_content=True)
    
    if args.analyze_links:
        await debugger.analyze_links(args.source)
        
    if args.test_patterns:
        await debugger.test_patterns(args.source)
        
    if args.suggest_patterns:
        await debugger.suggest_patterns(args.source)
        
    # По умолчанию показываем контент
    if not any([args.show_content, args.analyze_links, args.test_patterns, args.suggest_patterns]):
        await debugger.fetch_source_content(args.source, show_content=True)


if __name__ == "__main__":
    asyncio.run(main())