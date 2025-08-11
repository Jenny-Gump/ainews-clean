#!/usr/bin/env python3
"""
Fix Batch 4 Issues
Исправляем проблемы с google_research, google_cloud_ai, standardbots, abb_robotics
"""

import json
import sys
import re
from pathlib import Path

# Добавляем пути к системе
sys.path.insert(0, str(Path(__file__).parent.parent))

def analyze_and_fix_google_research():
    """Исправляем Google Research patterns"""
    print("\n" + "="*60)
    print("FIXING GOOGLE RESEARCH PATTERNS")
    print("="*60)
    
    try:
        content = open("/Users/skynet/Desktop/AI DEV/ainews-clean/scripts/content_google_research.md", 'r').read()
    except:
        print("❌ Cannot read content file")
        return None
    
    print(f"Content length: {len(content)} characters")
    
    # Анализируем реальные ссылки в контенте
    blog_links = re.findall(r'\]\((https://research\.google/blog/[^)]+)\)', content)
    print(f"Found {len(blog_links)} Google Research blog links")
    
    if blog_links:
        print("Sample links:")
        for i, link in enumerate(blog_links[:5], 1):
            print(f"  {i}. {link}")
        
        # Создаем правильные patterns
        patterns = ["\\]\\((https://research\\.google/blog/[^)]+)\\)"]
        title_extractions = [
            "\\n([^\\\\\\n]+)\\\\\\\\",  # Title after date
            "^([^\\[\\]\\n]{20,100})$"   # Clean line as title
        ]
        
        # Тестируем patterns
        print(f"\nTesting patterns:")
        all_matches = []
        
        for i, pattern in enumerate(patterns, 1):
            print(f"Pattern {i}: {pattern}")
            
            try:
                matches = list(re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE))
                print(f"   Found: {len(matches)} matches")
                
                for j, match in enumerate(matches[:5], 1):
                    url = match.groups()[0]
                    
                    # Пытаемся извлечь title из окружающего контекста
                    full_match = match.group(0)
                    start_pos = match.start()
                    context = content[max(0, start_pos-200):start_pos+200]
                    
                    title = "No title"
                    
                    # Ищем title в контексте
                    title_match = re.search(r'(\d{4})\\\\\\\\([^\\\\]+)\\\\', context)
                    if title_match:
                        title = title_match.group(2).strip()
                    
                    print(f"   {j}. [{title[:60]}{'...' if len(title) > 60 else ''}]")
                    print(f"      URL: {url}")
                    
                    all_matches.append({'title': title, 'url': url})
                    
            except re.error as e:
                print(f"   ❌ Regex error: {e}")
        
        if all_matches:
            return {
                "name": "Google Research Blog",
                "url": "https://research.google/blog/",
                "patterns": patterns,
                "title_extraction": title_extractions,
                "title_cleanup": [
                    "^Google:\\s*",
                    "^Google Research:\\s*",
                    "\\\\\\\\.*$",
                    "^\\s*\\n",
                    "\\s+$"
                ],
                "exclude_urls": [
                    "/page/", "/tag/", "/category/", "/#"
                ],
                "status": "tested_real"
            }
    
    return None

def analyze_and_fix_google_cloud_ai():
    """Исправляем Google Cloud AI patterns"""
    print("\n" + "="*60)
    print("FIXING GOOGLE CLOUD AI PATTERNS") 
    print("="*60)
    
    try:
        content = open("/Users/skynet/Desktop/AI DEV/ainews-clean/scripts/content_google_cloud_ai.md", 'r').read()
    except:
        print("❌ Cannot read content file")
        return None
    
    print(f"Content length: {len(content)} characters")
    
    # Анализируем реальные ссылки в контенте
    blog_links = re.findall(r'\]\((https://cloud\.google\.com/blog/products/ai-machine-learning/[^)]+)\)', content)
    print(f"Found {len(blog_links)} Google Cloud AI blog links")
    
    if blog_links:
        print("Sample links:")
        for i, link in enumerate(blog_links[:5], 1):
            print(f"  {i}. {link}")
        
        # Создаем правильные patterns
        patterns = ["\\]\\((https://cloud\\.google\\.com/blog/products/ai-machine-learning/[^)]+)\\)"]
        title_extractions = [
            "\\*\\*([^*]+)\\*\\*",  # **title**
            "\\[([^\\]]+)\\]\\(",   # [title](url)
        ]
        
        # Тестируем patterns
        print(f"\nTesting patterns:")
        all_matches = []
        
        for i, pattern in enumerate(patterns, 1):
            print(f"Pattern {i}: {pattern}")
            
            try:
                matches = list(re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE))
                print(f"   Found: {len(matches)} matches")
                
                for j, match in enumerate(matches[:5], 1):
                    url = match.groups()[0]
                    
                    # Пытаемся извлечь title
                    context_start = max(0, match.start() - 100)
                    context_end = min(len(content), match.end() + 100)
                    context = content[context_start:context_end]
                    
                    title = "No title"
                    for title_pattern in title_extractions:
                        title_match = re.search(title_pattern, context)
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
                "name": "Google Cloud AI Blog",
                "url": "https://cloud.google.com/blog/products/ai-machine-learning",
                "patterns": patterns,
                "title_extraction": title_extractions,
                "title_cleanup": [
                    "^Google:\\s*",
                    "^Google Cloud:\\s*",
                    "^\\*\\*|\\*\\*$",
                    "\\s+$"
                ],
                "exclude_urls": [
                    "/page/", "/tag/", "/category/", "/#"
                ],
                "status": "tested_real"
            }
    
    return None

def analyze_standardbots():
    """Анализируем StandardBots контент"""
    print("\n" + "="*60)
    print("ANALYZING STANDARDBOTS CONTENT")
    print("="*60)
    
    try:
        content = open("/Users/skynet/Desktop/AI DEV/ainews-clean/scripts/content_standardbots.md", 'r').read()
    except:
        print("❌ Cannot read content file")
        return None
    
    print(f"Content length: {len(content)} characters")
    print("Content preview:")
    print(content[:500])
    
    # Проверяем наличие реальных блог-постов
    if "blog" in content.lower() and len(content) > 1000:
        # Ищем любые релевантные ссылки
        all_links = re.findall(r'\[([^\]]+)\]\((https://[^)]+)\)', content)
        relevant_links = [link for link in all_links if 'standardbots.com' in link[1]]
        
        print(f"Found {len(relevant_links)} relevant links")
        
        if relevant_links:
            for i, (text, url) in enumerate(relevant_links[:5], 1):
                print(f"  {i}. [{text}] -> {url}")
    
    return None

def analyze_abb_robotics():
    """Анализируем ABB Robotics контент"""
    print("\n" + "="*60)
    print("ANALYZING ABB ROBOTICS CONTENT")
    print("="*60)
    
    try:
        content = open("/Users/skynet/Desktop/AI DEV/ainews-clean/scripts/content_abb_robotics.md", 'r').read()
    except:
        print("❌ Cannot read content file")
        return None
    
    print(f"Content length: {len(content)} characters")
    
    # Ищем новостные ссылки
    news_links = re.findall(r'\]\((https://new\.abb\.com/news/[^)]+)\)', content)
    print(f"Found {len(news_links)} ABB news links")
    
    if news_links:
        print("Sample news links:")
        for i, link in enumerate(news_links[:5], 1):
            print(f"  {i}. {link}")
        
        # Создаем patterns для новостей
        patterns = ["\\]\\((https://new\\.abb\\.com/news/[^)]+)\\)"]
        title_extractions = [
            "\\[([^\\]]+)\\]\\(",
            "^([^\\[\\]\\n]{20,100})$"
        ]
        
        # Тестируем patterns
        print(f"\nTesting patterns:")
        all_matches = []
        
        for i, pattern in enumerate(patterns, 1):
            print(f"Pattern {i}: {pattern}")
            
            try:
                matches = list(re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE))
                print(f"   Found: {len(matches)} matches")
                
                for j, match in enumerate(matches[:3], 1):
                    url = match.groups()[0]
                    
                    # Пытаемся извлечь title
                    context_start = max(0, match.start() - 150)
                    context = content[context_start:match.start()]
                    
                    title = "No title"
                    # Ищем предыдущую строку как заголовок
                    title_lines = context.split('\n')
                    for line in reversed(title_lines):
                        clean_line = line.strip()
                        if clean_line and len(clean_line) > 10 and not clean_line.startswith('[!['):
                            title = clean_line
                            break
                    
                    print(f"   {j}. [{title[:60]}{'...' if len(title) > 60 else ''}]")
                    print(f"      URL: {url}")
                    
                    all_matches.append({'title': title, 'url': url})
                    
            except re.error as e:
                print(f"   ❌ Regex error: {e}")
        
        if all_matches:
            return {
                "name": "ABB Robotics News",
                "url": "https://new.abb.com/products/robotics/news-and-media",
                "patterns": patterns,
                "title_extraction": title_extractions,
                "title_cleanup": [
                    "^ABB:\\s*",
                    "^ABB Robotics:\\s*",
                    "\\s+$"
                ],
                "exclude_urls": [
                    "/page/", "/tag/", "/category/", "/#"
                ],
                "status": "tested_real"
            }
    
    return None

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
    print("🔧 FIXING BATCH 4 ISSUES")
    print("="*80)
    
    updated_configs = {}
    
    # 1. Исправляем Google Research
    google_research_config = analyze_and_fix_google_research()
    if google_research_config:
        updated_configs['google_research'] = google_research_config
        print("✅ Google Research fixed")
    
    # 2. Исправляем Google Cloud AI
    google_cloud_config = analyze_and_fix_google_cloud_ai()
    if google_cloud_config:
        updated_configs['google_cloud_ai'] = google_cloud_config
        print("✅ Google Cloud AI fixed")
    
    # 3. Анализируем StandardBots (может не иметь блога)
    analyze_standardbots()
    
    # 4. Исправляем ABB Robotics
    abb_config = analyze_abb_robotics()
    if abb_config:
        updated_configs['abb_robotics'] = abb_config
        print("✅ ABB Robotics fixed")
    
    # 5. Обновляем конфигурацию
    if updated_configs:
        print(f"\n📝 UPDATING CONFIGURATION")
        update_config_file(updated_configs)
        print(f"\n🎉 BATCH 4 FIXES COMPLETED!")
        print(f"✅ Fixed sources: {list(updated_configs.keys())}")
    else:
        print("\n❌ NO FIXES APPLIED")

if __name__ == "__main__":
    main()