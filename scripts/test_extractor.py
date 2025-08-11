#!/usr/bin/env python3
"""
Source Extractor Tester
Тестирует паттерны извлечения URL для конкретных источников
"""

import sys
import json
import re
from pathlib import Path

# Добавляем пути к системе
sys.path.insert(0, str(Path(__file__).parent.parent))


class ExtractorTester:
    """Тестирует extractors на реальном контенте"""
    
    def __init__(self):
        # Загружаем конфигурацию extractors
        self.extractors_config_path = Path(__file__).parent.parent / 'services' / 'source_extractors.json'
        self.load_extractors_config()
        
    def load_extractors_config(self):
        """Загружает конфигурацию extractors"""
        try:
            with open(self.extractors_config_path, 'r', encoding='utf-8') as f:
                self.extractors_config = json.load(f)
        except Exception as e:
            print(f"Failed to load extractors config: {e}")
            self.extractors_config = {"extractors": {}}
    
    def get_source_config(self, source_id: str):
        """Получает конфигурацию источника"""
        return self.extractors_config.get("extractors", {}).get(source_id)
    
    def test_patterns(self, source_id: str, content: str = None):
        """Тестирует patterns для источника"""
        config = self.get_source_config(source_id)
        if not config:
            print(f"❌ No config found for source: {source_id}")
            return
            
        # Используем контент из файла если не передан
        if not content:
            content_file = Path(__file__).parent / f"content_{source_id}.md"
            if content_file.exists():
                with open(content_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                print(f"❌ No content file found: {content_file}")
                return
        
        print(f"\n🎯 TESTING PATTERNS FOR {source_id.upper()}")
        print(f"URL: {config['url']}")
        print(f"Content length: {len(content)} characters")
        print("=" * 60)
        
        patterns = config.get('patterns', [])
        all_matches = []
        
        for i, pattern in enumerate(patterns, 1):
            print(f"\n📋 Pattern {i}: {pattern}")
            
            try:
                matches = list(re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE))
                print(f"   Found: {len(matches)} matches")
                
                for j, match in enumerate(matches[:10], 1):  # Показываем первые 10
                    groups = match.groups()
                    if len(groups) >= 1:
                        url = groups[-1] if groups[-1].startswith('https://') else groups[0]
                        title = "Title extraction needed"
                        
                        # Пытаемся извлечь title
                        title_patterns = config.get('title_extraction', [])
                        for title_pattern in title_patterns:
                            title_match = re.search(title_pattern, match.group(0))
                            if title_match:
                                title = title_match.group(1).strip()
                                break
                        
                        print(f"   {j}. [{title[:60]}{'...' if len(title) > 60 else ''}]")
                        print(f"      URL: {url}")
                        
                        all_matches.append({
                            'title': title,
                            'url': url,
                            'pattern': i
                        })
                    
            except re.error as e:
                print(f"   ❌ Regex error: {e}")
        
        print(f"\n📊 SUMMARY")
        print(f"Total matches found: {len(all_matches)}")
        print(f"Unique URLs: {len(set(match['url'] for match in all_matches))}")
        
        # Показываем несколько примеров
        if all_matches:
            print(f"\n📝 SAMPLE RESULTS (first 5):")
            for i, match in enumerate(all_matches[:5], 1):
                clean_title = self.clean_title(match['title'], config.get('title_cleanup', []))
                print(f"{i}. {clean_title}")
                print(f"   {match['url']}")
    
    def clean_title(self, title: str, cleanup_rules: list) -> str:
        """Применяет правила очистки заголовка"""
        cleaned = title
        for rule in cleanup_rules:
            cleaned = re.sub(rule, '', cleaned).strip()
        return cleaned


def main():
    """Основная функция"""
    if len(sys.argv) != 2:
        print("Usage: python test_extractor.py <source_id>")
        sys.exit(1)
    
    source_id = sys.argv[1]
    tester = ExtractorTester()
    tester.test_patterns(source_id)


if __name__ == "__main__":
    main()