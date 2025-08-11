#!/usr/bin/env python3
"""
Fix Batch 3 Issues
Исправляем проблемы с tempus (неправильные patterns) и databricks (404)
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

def fix_tempus():
    """Исправляем tempus patterns на основе реального контента"""
    print("\n" + "="*60)
    print("FIXING TEMPUS PATTERNS")
    print("="*60)
    
    # Из анализа контента видим правильные URL patterns
    content = open("/Users/skynet/Desktop/AI DEV/ainews-clean/scripts/content_tempus.md", 'r').read()
    
    # Правильные patterns на основе реального контента
    correct_patterns = [
        "\\]\\((https://www\\.tempus\\.com/tech-videos/[^)]+)\\)"  # tech-videos, не tech-blog
    ]
    
    title_extractions = [
        "#### \\[([^\\]]+)\\]\\(",  # #### [title](url)
        "\\*\\*([^*]+)\\*\\*"      # **title**
    ]
    
    # Тестируем новые patterns
    print(f"Content length: {len(content)} characters")
    
    all_matches = []
    for i, pattern in enumerate(correct_patterns, 1):
        print(f"\nTesting pattern {i}: {pattern}")
        
        try:
            matches = list(re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE))
            print(f"   Found: {len(matches)} matches")
            
            for j, match in enumerate(matches[:10], 1):
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
    
    if all_matches:
        print(f"\n✅ Tempus fixed! Found {len(all_matches)} matches")
        return {
            "name": "Tempus Tech Blog",
            "url": "https://www.tempus.com/tech-blog/",
            "patterns": correct_patterns,
            "title_extraction": title_extractions,
            "title_cleanup": [
                "^Tempus:\\s*",
                "^\\*\\*|\\*\\*$",
                "\\s+$"
            ],
            "exclude_urls": [
                "/contact", "/about", "/careers", "/pricing", "/page/", "/category/", "/tag/"
            ],
            "status": "tested_real"
        }
    else:
        print("❌ No matches found for tempus")
        return None

def test_databricks_alternatives():
    """Тестируем альтернативные URL для Databricks"""
    print("\n" + "="*60)
    print("TESTING DATABRICKS ALTERNATIVES")
    print("="*60)
    
    # Попробуем разные URL для Databricks
    alternative_urls = [
        "https://www.databricks.com/blog",
        "https://databricks.com/blog", 
        "https://www.databricks.com/blog/category/engineering",
        "https://www.databricks.com/blog/category/artificial-intelligence",
        "https://www.databricks.com/blog/tag/ai"
    ]
    
    for i, url in enumerate(alternative_urls, 1):
        print(f"\n{i}. Testing: {url}")
        
        content, error = fetch_content_firecrawl(url, timeout=60000)
        
        if error:
            print(f"   ❌ Error: {error}")
            continue
            
        if not content or len(content) < 200:
            print(f"   ❌ No meaningful content ({len(content) if content else 0} chars)")
            continue
        
        print(f"   ✅ Success! {len(content)} characters")
        
        # Сохраняем контент для анализа
        content_file = Path(__file__).parent / f"content_databricks_alt{i}.md"
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"   💾 Saved to {content_file}")
        
        # Быстрый анализ ссылок
        blog_links = re.findall(r'\[([^\]]+)\]\((https://[^)]*databricks\.com/blog/[^)]+)\)', content)
        print(f"   📊 Found {len(blog_links)} blog links")
        
        if blog_links:
            print(f"   📝 First few links:")
            for j, (title, link) in enumerate(blog_links[:3], 1):
                print(f"      {j}. [{title[:50]}...] -> {link}")
            
            # Создаем patterns
            patterns = ["\\]\\((https://[^)]*databricks\\.com/blog/[^)]+)\\)"]
            title_extractions = ["\\[([^\\]]+)\\]\\(", "\\*\\*([^*]+)\\*\\*"]
            
            return url, {
                "name": "Databricks AI Blog",
                "url": url,
                "patterns": patterns,
                "title_extraction": title_extractions,
                "title_cleanup": [
                    "^Databricks:\\s*",
                    "^\\*\\*|\\*\\*$",
                    "\\s+$"
                ],
                "exclude_urls": [
                    "/contact", "/about", "/careers", "/pricing", "/page/", "/category/", "/tag/"
                ],
                "status": "tested_real"
            }
        
        # Небольшая пауза между запросами
        time.sleep(2)
    
    return None, None

def update_config_file(source_configs: dict):
    """Обновляет source_extractors.json с исправленными конфигурациями"""
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
    """Основная функция исправления"""
    print("🔧 FIXING BATCH 3 ISSUES")
    print("="*80)
    
    updated_configs = {}
    
    # 1. Исправляем tempus
    tempus_config = fix_tempus()
    if tempus_config:
        updated_configs['tempus'] = tempus_config
    
    # 2. Исправляем databricks
    databricks_url, databricks_config = test_databricks_alternatives()
    if databricks_config:
        updated_configs['databricks_tracking'] = databricks_config
        print(f"✅ Databricks fixed with URL: {databricks_url}")
    else:
        print("❌ Could not fix databricks")
    
    # 3. Обновляем конфигурацию
    if updated_configs:
        print(f"\n📝 UPDATING CONFIGURATION")
        update_config_file(updated_configs)
        print(f"\n🎉 FIXES COMPLETED!")
        print(f"✅ Fixed sources: {list(updated_configs.keys())}")
    else:
        print("\n❌ NO FIXES APPLIED")

if __name__ == "__main__":
    main()