#!/usr/bin/env python3
"""
Batch Testing Script - Round 5
Тестирует следующие 5 источников: robotics companies
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

# Источники для тестирования (робототехника)
SOURCES_TO_TEST = [
    {
        "id": "fanuc",
        "name": "FANUC America News",
        "url": "https://www.fanucamerica.com/news-resources/articles/all"
    },
    {
        "id": "kuka",
        "name": "KUKA Robotics News",
        "url": "https://www.kuka.com/en-us/company/press/news"
    },
    {
        "id": "kinova",
        "name": "Kinova Robotics Press",
        "url": "https://www.kinovarobotics.com/press"
    },
    {
        "id": "doosan_robotics",
        "name": "Doosan Robotics News",
        "url": "https://www.doosanrobotics.com/en/about/promotion/news/"
    },
    {
        "id": "manus",
        "name": "Manus Blog",
        "url": "https://manus.im/blog"
    }
]

def fetch_content_firecrawl(url: str, timeout: int = 120000):
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
        response = requests.post(api_url, headers=headers, json=data, timeout=150)
        
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

def analyze_and_create_patterns(source_id: str, content: str, url: str):
    """Анализирует контент и создает patterns для источника"""
    print(f"\n🔍 ANALYZING {source_id.upper()}")
    print(f"Content length: {len(content)} characters")
    print("=" * 60)
    
    # Извлекаем домен для поиска релевантных ссылок  
    domain = url.split('/')[2] if '://' in url else ''
    base_domain = domain.replace('www.', '').replace('.', '\\.')
    
    # Ищем различные типы ссылок с доменом источника
    patterns_to_try = [
        rf'\[([^\]]+)\]\((https://[^)]*{re.escape(domain.replace("www.", ""))}/[^)]+)\)',
        rf'\[([^\]]+)\]\((https://[^)]*{re.escape(domain)}/[^)]+)\)',
    ]
    
    found_links = []
    
    for pattern_template in patterns_to_try:
        matches = list(re.finditer(pattern_template, content, re.IGNORECASE))
        print(f"Pattern search found: {len(matches)} matches")
        
        for match in matches[:10]:  # Показываем первые 10
            groups = match.groups()
            if len(groups) >= 2:
                text, link_url = groups[0], groups[1]
                
                # Фильтруем релевантные ссылки
                if any(keyword in (text + link_url).lower() for keyword in 
                       ['news', 'article', 'blog', 'post', 'press', 'announcement', 'release']):
                    found_links.append((text, link_url))
                    print(f"  - [{text[:50]}...] -> {link_url}")
    
    if not found_links:
        print("❌ No relevant links found")
        return None
        
    # Анализируем URL patterns
    url_paths = set()
    for text, link_url in found_links:
        # Извлекаем базовую структуру URL  
        parts = link_url.split('/')
        if len(parts) >= 4:
            # Создаем pattern на основе реальных URL
            base_pattern = '/'.join(parts[:4])  # https://domain.com/path
            if len(parts) > 4:
                base_pattern += '/' + parts[4] if not re.match(r'^\d+$', parts[4]) else '/[^)]+'
            else:
                base_pattern += '/[^)]+'
            
            # Заменяем домен на regex pattern
            pattern_url = base_pattern.replace(domain, base_domain)
            url_paths.add(pattern_url)
    
    # Создаем окончательные patterns
    patterns = []
    for path_pattern in list(url_paths)[:3]:  # Максимум 3 patterns
        pattern = f"\\]\\(({path_pattern})\\)"
        patterns.append(pattern)
    
    # Title extraction patterns
    title_extractions = [
        "\\[([^\\]]+)\\]\\(",
        "\\*\\*([^*]+)\\*\\*",
        "### ([^\\n]+)",
        "## ([^\\n]+)",
        "^([^\\[\\]\\n]{15,100})$"  # Чистые строки как заголовки
    ]
    
    # Тестируем созданные patterns
    print(f"\n🧪 TESTING PATTERNS FOR {source_id.upper()}")
    all_matches = []
    
    for i, pattern in enumerate(patterns, 1):
        print(f"Pattern {i}: {pattern}")
        
        try:
            matches = list(re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE))
            print(f"   Found: {len(matches)} matches")
            
            for j, match in enumerate(matches[:5], 1):
                groups = match.groups()
                if len(groups) >= 1:
                    url = groups[0]
                    
                    # Пытаемся извлечь title
                    title = "No title"
                    full_match = match.group(0)
                    context_start = max(0, match.start() - 100)
                    context = content[context_start:match.start()]
                    
                    for title_pattern in title_extractions:
                        title_match = re.search(title_pattern, full_match + context)
                        if title_match:
                            title = title_match.group(1).strip()
                            break
                    
                    print(f"   {j}. [{title[:60]}{'...' if len(title) > 60 else ''}]")
                    print(f"      URL: {url}")
                    
                    all_matches.append({'title': title, 'url': url})
                    
        except re.error as e:
            print(f"   ❌ Regex error: {e}")
    
    if all_matches:
        return {
            "patterns": patterns,
            "title_extractions": title_extractions,
            "matches": all_matches,
            "unique_urls": len(set(match['url'] for match in all_matches))
        }
    
    return None

def create_extractor_config(source_id: str, name: str, url: str, analysis_result: dict):
    """Создает конфигурацию extractor'а на основе анализа"""
    return {
        "name": name,
        "url": url,
        "patterns": analysis_result["patterns"],
        "title_extraction": analysis_result["title_extractions"],
        "title_cleanup": [
            f"^{name.split()[0]}:\\s*",
            "^\\*\\*|\\*\\*$",
            "\\s+$",
            "\\\\$"
        ],
        "exclude_urls": [
            "/contact", "/about", "/careers", "/pricing", 
            "/page/", "/category/", "/tag/", "/#", "/search"
        ],
        "status": "tested_real"
    }

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
    print("🚀 STARTING BATCH 5 TESTING (ROBOTICS COMPANIES)")
    print(f"Sources to test: {len(SOURCES_TO_TEST)}")
    print("=" * 80)
    
    updated_configs = {}
    
    for i, source in enumerate(SOURCES_TO_TEST, 1):
        print(f"\n\n{'='*80}")
        print(f"TESTING SOURCE {i}/{len(SOURCES_TO_TEST)}: {source['name']}")
        print(f"{'='*80}")
        
        # 1. Получаем реальный контент
        print(f"📥 Fetching content from {source['url']}")
        content, error = fetch_content_firecrawl(source['url'], timeout=120000)
        
        if error:
            print(f"❌ Failed to fetch content: {error}")
            continue
            
        if not content:
            print(f"❌ No content received")
            continue
            
        if len(content) < 200:
            print(f"❌ Content too short: {len(content)} characters")
            continue
            
        print(f"✅ Content fetched: {len(content)} characters")
        
        # Сохраняем контент для дальнейшего анализа
        content_file = Path(__file__).parent / f"content_{source['id']}.md"
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"💾 Content saved to {content_file}")
        
        # 2. Анализируем и создаем patterns
        analysis_result = analyze_and_create_patterns(source['id'], content, source['url'])
        
        if analysis_result:
            # Создаем конфигурацию
            config_entry = create_extractor_config(
                source['id'], source['name'], source['url'], analysis_result
            )
            updated_configs[source['id']] = config_entry
            
            print(f"\n✅ SUCCESS: {source['id']}")
            print(f"   Patterns: {len(analysis_result['patterns'])}")
            print(f"   Matches found: {len(analysis_result['matches'])}")
            print(f"   Unique URLs: {analysis_result['unique_urls']}")
        else:
            print(f"\n❌ FAILED: {source['id']} - No usable patterns found")
        
        # Rate limiting - пауза между запросами
        if i < len(SOURCES_TO_TEST):
            print(f"⏳ Waiting 5 seconds before next source...")
            time.sleep(5)
    
    # 3. Обновляем конфигурационный файл
    if updated_configs:
        print(f"\n\n📝 UPDATING CONFIGURATION FILE")
        print(f"Successfully tested sources: {len(updated_configs)}")
        update_config_file(updated_configs)
        
        print(f"\n🎉 BATCH 5 COMPLETED!")
        print(f"✅ Tested sources: {list(updated_configs.keys())}")
    else:
        print(f"\n❌ BATCH 5 FAILED - No sources successfully configured")

if __name__ == "__main__":
    main()