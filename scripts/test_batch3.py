#!/usr/bin/env python3
"""
Batch Testing Script - Round 3
Тестирует следующие 5 источников с реальным контентом через Firecrawl
"""

import requests
import json
import sys
import re
import time
from pathlib import Path

# Добавляем пути к системе
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import Config

config = Config()

# Источники для тестирования
SOURCES_TO_TEST = [
    {
        "id": "databricks_tracking",
        "name": "Databricks AI Blog",
        "url": "https://www.databricks.com/blog/category/engineering/ai"
    },
    {
        "id": "stanford_ai", 
        "name": "Stanford AI Lab",
        "url": "https://ai.stanford.edu/"
    },
    {
        "id": "suno",
        "name": "Suno AI Blog", 
        "url": "https://suno.com/blog"
    },
    {
        "id": "waymo",
        "name": "Waymo Blog",
        "url": "https://waymo.com/blog/"
    },
    {
        "id": "tempus",
        "name": "Tempus Tech Blog",
        "url": "https://www.tempus.com/tech-blog/"
    }
]

def fetch_content_firecrawl(url: str, timeout: int = 60000):
    """Получаем реальный markdown через Firecrawl API"""
    api_url = "https://api.firecrawl.dev/v1/scrape"
    headers = {
        "Authorization": f"Bearer {config.FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "url": url,
        "formats": ["markdown"],
        "timeout": timeout
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                markdown = result.get("data", {}).get("markdown", "")
                return markdown, None
            else:
                return None, f"API error: {result}"
        else:
            return None, f"HTTP Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return None, f"Exception: {str(e)}"

def analyze_content_structure(content: str, source_id: str):
    """Анализирует структуру markdown и предлагает patterns"""
    print(f"\n🔍 ANALYZING CONTENT STRUCTURE FOR {source_id.upper()}")
    print(f"Content length: {len(content)} characters")
    print("=" * 60)
    
    # Ищем различные типы ссылок
    link_patterns = [
        r'\[([^\]]+)\]\((https://[^)]+)\)',  # Markdown links
        r'<a[^>]*href="(https://[^"]+)"[^>]*>([^<]*)</a>',  # HTML links
        r'https://[^\s\])\}]+',  # Plain URLs
    ]
    
    all_links = []
    for i, pattern in enumerate(link_patterns):
        matches = list(re.finditer(pattern, content, re.IGNORECASE))
        print(f"Pattern {i+1} ({pattern}): {len(matches)} matches")
        
        for match in matches[:5]:  # Show first 5
            groups = match.groups()
            if len(groups) >= 2:
                text, url = groups[0], groups[1]
                print(f"  - [{text[:50]}...] -> {url}")
                all_links.append((text, url))
            elif len(groups) == 1:
                url = groups[0] if groups[0].startswith('https://') else match.group(0)
                print(f"  - {url}")
                all_links.append(("", url))
    
    # Анализируем найденные ссылки 
    print(f"\n📊 LINK ANALYSIS:")
    print(f"Total links found: {len(all_links)}")
    
    # Группируем по доменам
    domain_counts = {}
    relevant_links = []
    
    for text, url in all_links:
        domain = url.split('/')[2] if '://' in url else 'unknown'
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        # Проверяем релевантность (содержит ключевые слова AI/ML)
        if any(keyword.lower() in (text + url).lower() for keyword in 
               ['ai', 'ml', 'machine learning', 'neural', 'model', 'algorithm', 'data', 'blog', 'article', 'news']):
            relevant_links.append((text, url))
    
    print(f"Domains found:")
    for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {domain}: {count} links")
    
    print(f"Relevant links (with AI/ML keywords): {len(relevant_links)}")
    
    return relevant_links, domain_counts

def generate_patterns(source_id: str, url: str, relevant_links: list):
    """Генерирует patterns на основе анализа ссылок"""
    print(f"\n🎯 GENERATING PATTERNS FOR {source_id.upper()}")
    
    domain = url.split('/')[2] if '://' in url else ''
    base_domain = domain.replace('www.', '')
    
    patterns = []
    title_extractions = []
    exclude_urls = []
    
    # Анализируем структуру найденных ссылок
    for text, link_url in relevant_links:
        if base_domain in link_url:
            # Определяем паттерн URL
            url_pattern = link_url.replace(domain, base_domain.replace('.', '\\.'))
            url_pattern = re.sub(r'/[^/]+/?$', '/[^)]+', url_pattern)
            
            # Создаем markdown link pattern
            if text:
                pattern = f"\\]\\(({url_pattern})\\)"
                patterns.append(pattern)
                
                # Определяем pattern для извлечения заголовка
                if '**' in text:
                    title_extractions.append("\\*\\*([^*]+)\\*\\*")
                elif text:
                    title_extractions.append("\\[([^\\]]+)\\]\\(")
    
    # Убираем дубликаты
    patterns = list(dict.fromkeys(patterns))
    title_extractions = list(dict.fromkeys(title_extractions))
    
    # Стандартные исключения
    exclude_urls = ["/contact", "/about", "/careers", "/pricing", "/page/", "/category/", "/tag/"]
    
    return patterns[:3], title_extractions[:2], exclude_urls  # Ограничиваем количество

def create_extractor_config(source_id: str, name: str, url: str, patterns: list, 
                          title_extractions: list, exclude_urls: list):
    """Создает конфигурацию extractor'а"""
    return {
        "name": name,
        "url": url,
        "patterns": patterns,
        "title_extraction": title_extractions,
        "title_cleanup": [
            f"^{name.split()[0]}:\\s*",
            "^\\*\\*|\\*\\*$",
            "\\s+$"
        ],
        "exclude_urls": exclude_urls,
        "status": "tested_real"
    }

def test_patterns_on_content(patterns: list, title_extractions: list, content: str):
    """Тестирует созданные patterns на реальном контенте"""
    print(f"\n🧪 TESTING GENERATED PATTERNS")
    
    all_matches = []
    
    for i, pattern in enumerate(patterns, 1):
        print(f"\nPattern {i}: {pattern}")
        
        try:
            matches = list(re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE))
            print(f"   Found: {len(matches)} matches")
            
            for j, match in enumerate(matches[:5], 1):  # Show first 5
                groups = match.groups()
                if len(groups) >= 1:
                    url = groups[-1] if groups[-1].startswith('https://') else groups[0]
                    
                    # Пытаемся извлечь title
                    title = "No title"
                    for title_pattern in title_extractions:
                        title_match = re.search(title_pattern, match.group(0))
                        if title_match:
                            title = title_match.group(1).strip()
                            break
                    
                    print(f"   {j}. [{title[:60]}{'...' if len(title) > 60 else ''}]")
                    print(f"      URL: {url}")
                    
                    all_matches.append({'title': title, 'url': url})
                    
        except re.error as e:
            print(f"   ❌ Regex error: {e}")
    
    return all_matches

def update_config_file(source_configs: dict):
    """Обновляет source_extractors.json с новыми конфигурациями"""
    config_path = Path(__file__).parent.parent / 'services' / 'source_extractors.json'
    
    try:
        # Загружаем существующую конфигурацию
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Обновляем extractors
        for source_id, source_config in source_configs.items():
            config_data['extractors'][source_id] = source_config
            print(f"✅ Updated config for {source_id}")
        
        # Сохраняем обновленную конфигурацию
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Configuration updated in {config_path}")
        
    except Exception as e:
        print(f"❌ Failed to update config: {e}")

def main():
    """Основная функция тестирования"""
    print("🚀 STARTING BATCH 3 TESTING")
    print(f"Sources to test: {len(SOURCES_TO_TEST)}")
    print("=" * 80)
    
    updated_configs = {}
    
    for i, source in enumerate(SOURCES_TO_TEST, 1):
        print(f"\n\n{'='*80}")
        print(f"TESTING SOURCE {i}/{len(SOURCES_TO_TEST)}: {source['name']}")
        print(f"{'='*80}")
        
        # 1. Получаем реальный контент
        print(f"📥 Fetching content from {source['url']}")
        content, error = fetch_content_firecrawl(source['url'], timeout=120000)  # 2 minutes
        
        if error:
            print(f"❌ Failed to fetch content: {error}")
            continue
            
        if not content:
            print(f"❌ No content received")
            continue
            
        print(f"✅ Content fetched: {len(content)} characters")
        
        # Сохраняем контент для дальнейшего анализа
        content_file = Path(__file__).parent / f"content_{source['id']}.md"
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"💾 Content saved to {content_file}")
        
        # 2. Анализируем структуру
        relevant_links, domain_counts = analyze_content_structure(content, source['id'])
        
        if not relevant_links:
            print(f"⚠️  No relevant links found for {source['id']}")
            continue
        
        # 3. Генерируем patterns
        patterns, title_extractions, exclude_urls = generate_patterns(
            source['id'], source['url'], relevant_links
        )
        
        if not patterns:
            print(f"⚠️  No patterns generated for {source['id']}")
            continue
        
        # 4. Тестируем patterns
        matches = test_patterns_on_content(patterns, title_extractions, content)
        
        # 5. Создаем конфигурацию
        if matches:
            config_entry = create_extractor_config(
                source['id'], source['name'], source['url'],
                patterns, title_extractions, exclude_urls
            )
            updated_configs[source['id']] = config_entry
            
            print(f"\n✅ SUCCESS: {source['id']}")
            print(f"   Patterns: {len(patterns)}")
            print(f"   Matches found: {len(matches)}")
            print(f"   Unique URLs: {len(set(match['url'] for match in matches))}")
        else:
            print(f"\n❌ FAILED: {source['id']} - No matches found")
        
        # Rate limiting - пауза между запросами
        if i < len(SOURCES_TO_TEST):
            print(f"⏳ Waiting 3 seconds before next source...")
            time.sleep(3)
    
    # 6. Обновляем конфигурационный файл
    if updated_configs:
        print(f"\n\n📝 UPDATING CONFIGURATION FILE")
        print(f"Successfully tested sources: {len(updated_configs)}")
        update_config_file(updated_configs)
        
        print(f"\n🎉 BATCH 3 COMPLETED!")
        print(f"✅ Tested sources: {list(updated_configs.keys())}")
    else:
        print(f"\n❌ BATCH 3 FAILED - No sources successfully configured")

if __name__ == "__main__":
    main()