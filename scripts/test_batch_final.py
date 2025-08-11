#!/usr/bin/env python3
"""
Final Batch Testing Script
Тестирует оставшиеся источники AI/tech companies
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

# Оставшиеся источники для тестирования
SOURCES_TO_TEST = [
    {
        "id": "pathai",
        "name": "PathAI News",
        "url": "https://www.pathai.com/news/"
    },
    {
        "id": "augmedix",
        "name": "Augmedix Resources",
        "url": "https://www.augmedix.com/resources"
    },
    {
        "id": "openevidence",
        "name": "OpenEvidence Announcements",
        "url": "https://www.openevidence.com/announcements"
    },
    {
        "id": "b12",
        "name": "B12 Blog",
        "url": "https://www.b12.io/blog/"
    },
    {
        "id": "appzen",
        "name": "AppZen Blog",
        "url": "https://www.appzen.com/blog"
    },
    {
        "id": "alpha_sense",
        "name": "AlphaSense Blog",
        "url": "https://www.alpha-sense.com/blog/"
    },
    {
        "id": "mindfoundry",
        "name": "Mind Foundry Blog",
        "url": "https://www.mindfoundry.ai/blog"
    },
    {
        "id": "nscale",
        "name": "nScale Blog",
        "url": "https://www.nscale.com/blog"
    },
    {
        "id": "audioscenic",
        "name": "AudioScenic News",
        "url": "https://www.audioscenic.com/news"
    },
    {
        "id": "soundhound",
        "name": "SoundHound Voice AI Blog",
        "url": "https://www.soundhound.com/voice-ai-blog/"
    },
    {
        "id": "uizard",
        "name": "Uizard Blog", 
        "url": "https://uizard.io/blog/"
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

def smart_pattern_analysis(source_id: str, content: str, url: str):
    """Умный анализ контента для создания patterns"""
    print(f"\n🧠 SMART ANALYSIS FOR {source_id.upper()}")
    print(f"Content length: {len(content)} characters")
    print("=" * 60)
    
    # Извлекаем домен
    domain = url.split('/')[2] if '://' in url else ''
    base_domain = domain.replace('www.', '')
    
    # Ищем ссылки с правильным доменом
    domain_patterns = [
        rf'\[([^\]]+)\]\((https://[^)]*{re.escape(base_domain)}/[^)]+)\)',
        rf'\[([^\]]+)\]\((https://[^)]*{re.escape(domain)}/[^)]+)\)',
    ]
    
    all_domain_links = []
    
    for pattern in domain_patterns:
        matches = list(re.finditer(pattern, content, re.IGNORECASE))
        print(f"Domain pattern found: {len(matches)} matches")
        
        for match in matches:
            groups = match.groups()
            if len(groups) >= 2:
                text, link_url = groups[0], groups[1]
                all_domain_links.append((text, link_url))
    
    if not all_domain_links:
        print("❌ No domain-specific links found")
        return None
    
    # Фильтруем релевантные ссылки
    relevant_links = []
    keywords = ['blog', 'post', 'article', 'news', 'announcement', 'press', 'release', 
                'insight', 'update', 'story', 'resource', 'publication']
    
    for text, link_url in all_domain_links:
        combined = (text + link_url).lower()
        
        # Исключаем навигационные и служебные ссылки
        if any(exclude in combined for exclude in 
               ['contact', 'about', 'careers', 'privacy', 'terms', 'cookie', 'login', 'signup']):
            continue
            
        # Включаем если есть релевантные ключевые слова
        if any(keyword in combined for keyword in keywords):
            relevant_links.append((text, link_url))
            print(f"  ✓ [{text[:50]}...] -> {link_url}")
    
    if not relevant_links:
        print("❌ No relevant links found")
        return None
    
    # Анализируем структуры URL
    url_structures = {}
    for text, link_url in relevant_links:
        # Извлекаем структуру пути
        parts = link_url.split('/')
        if len(parts) >= 4:
            path_structure = '/'.join(parts[3:5])  # path после домена
            if path_structure not in url_structures:
                url_structures[path_structure] = []
            url_structures[path_structure].append((text, link_url))
    
    print(f"URL structures found: {len(url_structures)}")
    for structure, links in url_structures.items():
        print(f"  {structure}: {len(links)} links")
    
    # Создаем patterns на основе самых популярных структур
    patterns = []
    escaped_domain = base_domain.replace('.', '\\.')
    
    for structure, links in sorted(url_structures.items(), key=lambda x: len(x[1]), reverse=True)[:3]:
        if len(links) >= 2:  # Минимум 2 ссылки для pattern
            # Создаем pattern для этой структуры
            pattern_path = structure
            if '/' in structure:
                pattern_path = structure.split('/')[0] + '/[^)]+'
            
            pattern = f"\\]\\((https://[^)]*{escaped_domain}/{pattern_path})\\)"
            patterns.append(pattern)
    
    if not patterns:
        print("❌ No usable patterns generated")
        return None
    
    return {
        "patterns": patterns,
        "relevant_links": relevant_links,
        "url_structures": url_structures
    }

def test_patterns(patterns: list, content: str):
    """Тестируем patterns на реальном контенте"""
    print(f"\n🧪 TESTING {len(patterns)} PATTERNS")
    
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
                    
                    # Пытаемся извлечь title из окружающего контекста
                    match_start = match.start()
                    context_start = max(0, match_start - 150)
                    context_end = min(len(content), match_start + 50)
                    context = content[context_start:context_end]
                    
                    title = "No title"
                    
                    # Ищем title в различных форматах
                    title_patterns = [
                        r'\[([^\]]+)\]\([^)]*\)',  # [title](url)
                        r'\*\*([^*]+)\*\*',       # **title**
                        r'###?\s*([^\n]+)',       # ## title or ### title
                        r'^([^[\]#\n]{15,80})$'   # Простая строка как title
                    ]
                    
                    for tp in title_patterns:
                        tm = re.search(tp, context, re.MULTILINE)
                        if tm:
                            title = tm.group(1).strip()
                            break
                    
                    print(f"   {j}. [{title[:50]}{'...' if len(title) > 50 else ''}]")
                    print(f"      URL: {url}")
                    
                    all_matches.append({'title': title, 'url': url})
                    
        except re.error as e:
            print(f"   ❌ Regex error: {e}")
    
    return all_matches

def create_extractor_config(source_id: str, name: str, url: str, patterns: list, matches: list):
    """Создает конфигурацию extractor'а"""
    title_extractions = [
        "\\[([^\\]]+)\\]\\(",
        "\\*\\*([^*]+)\\*\\*",
        "### ([^\\n]+)",
        "## ([^\\n]+)",
        "^([^\\[\\]\\n]{15,100})$"
    ]
    
    return {
        "name": name,
        "url": url,
        "patterns": patterns,
        "title_extraction": title_extractions,
        "title_cleanup": [
            f"^{name.split()[0]}:\\s*",
            "^\\*\\*|\\*\\*$",
            "\\s+$",
            "\\\\$",
            "^Read more\\s*",
            "^Learn more\\s*"
        ],
        "exclude_urls": [
            "/contact", "/about", "/careers", "/pricing", 
            "/page/", "/category/", "/tag/", "/#", "/search",
            "/privacy", "/terms", "/cookie"
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
        
        # Обновляем метаданные
        config_data['metadata']['last_updated'] = '2025-08-11'
        
        # Сохраняем обновленную конфигурацию
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Configuration updated in {config_path}")
        
    except Exception as e:
        print(f"❌ Failed to update config: {e}")

def main():
    """Основная функция финального тестирования"""
    print("🏁 STARTING FINAL BATCH TESTING")
    print(f"Sources to test: {len(SOURCES_TO_TEST)}")
    print("=" * 80)
    
    updated_configs = {}
    failed_sources = []
    
    for i, source in enumerate(SOURCES_TO_TEST, 1):
        print(f"\n\n{'='*80}")
        print(f"TESTING SOURCE {i}/{len(SOURCES_TO_TEST)}: {source['name']}")
        print(f"{'='*80}")
        
        # 1. Получаем контент
        print(f"📥 Fetching content from {source['url']}")
        content, error = fetch_content_firecrawl(source['url'], timeout=120000)
        
        if error:
            print(f"❌ Failed to fetch content: {error}")
            failed_sources.append((source['id'], error))
            continue
            
        if not content or len(content) < 200:
            error_msg = f"Content too short: {len(content) if content else 0} characters"
            print(f"❌ {error_msg}")
            failed_sources.append((source['id'], error_msg))
            continue
            
        print(f"✅ Content fetched: {len(content)} characters")
        
        # Сохраняем контент
        content_file = Path(__file__).parent / f"content_{source['id']}.md"
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"💾 Content saved to {content_file}")
        
        # 2. Умный анализ
        analysis = smart_pattern_analysis(source['id'], content, source['url'])
        
        if not analysis:
            failed_sources.append((source['id'], "No usable patterns"))
            continue
        
        # 3. Тестируем patterns
        matches = test_patterns(analysis['patterns'], content)
        
        if matches:
            # 4. Создаем конфигурацию
            config_entry = create_extractor_config(
                source['id'], source['name'], source['url'], 
                analysis['patterns'], matches
            )
            updated_configs[source['id']] = config_entry
            
            print(f"\n✅ SUCCESS: {source['id']}")
            print(f"   Patterns: {len(analysis['patterns'])}")
            print(f"   Matches found: {len(matches)}")
            print(f"   Unique URLs: {len(set(match['url'] for match in matches))}")
        else:
            failed_sources.append((source['id'], "No matches found"))
        
        # Rate limiting
        if i < len(SOURCES_TO_TEST):
            print(f"⏳ Waiting 4 seconds before next source...")
            time.sleep(4)
    
    # 5. Финальные результаты
    print(f"\n\n📊 FINAL BATCH RESULTS")
    print(f"{'='*80}")
    print(f"✅ Successful: {len(updated_configs)} sources")
    print(f"❌ Failed: {len(failed_sources)} sources")
    
    if updated_configs:
        print(f"\nSuccessful sources:")
        for source_id in updated_configs.keys():
            print(f"  ✓ {source_id}")
    
    if failed_sources:
        print(f"\nFailed sources:")
        for source_id, reason in failed_sources:
            print(f"  ✗ {source_id}: {reason}")
    
    # 6. Обновляем конфигурацию
    if updated_configs:
        print(f"\n📝 UPDATING CONFIGURATION FILE")
        update_config_file(updated_configs)
        
        print(f"\n🎉 FINAL TESTING COMPLETED!")
        print(f"Total sources configured in this batch: {len(updated_configs)}")
    else:
        print(f"\n❌ NO SOURCES SUCCESSFULLY CONFIGURED")

if __name__ == "__main__":
    main()