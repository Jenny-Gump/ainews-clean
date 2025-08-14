#!/usr/bin/env python3
"""
Дебаг процесса извлечения заголовков
"""
import asyncio
import os
import sys

# Добавляем путь к проекту
sys.path.append('/Users/skynet/Desktop/AI DEV/ainews-clean')

from change_tracking.url_extractor import URLExtractor
from services.firecrawl_client import FirecrawlClient


async def debug_extraction():
    """Дебаг извлечения заголовков"""
    print("🔍 Дебаг извлечения заголовков")
    print("=" * 60)
    
    # Тестовый markdown более похожий на реальный HuggingFace  
    test_markdown = """
    Recent posts:
    
    [Feb 22](https://huggingface.co/blog/jjokah/small-language-model) by jjokah
    [Feb 5](https://huggingface.co/blog/hexgrad/g2p) by hexgrad
    [Jan 30](https://huggingface.co/blog/community/fineweb-edu) by community
    """
    
    test_source_url = "https://huggingface.co/blog"
    
    try:
        url_extractor = URLExtractor()
        
        # Сначала проверим что извлекается из markdown
        print("1. Что извлекается из markdown:")
        all_links = url_extractor._extract_all_links(test_markdown)
        
        for i, (title, url) in enumerate(all_links, 1):
            print(f"   {i}. Заголовок: '{title}' -> URL: {url}")
        
        print(f"\n2. После очистки заголовков (старый способ):")
        for i, (title, url) in enumerate(all_links, 1):
            clean_title = url_extractor._clean_title(title)
            print(f"   {i}. '{title}' -> '{clean_title}'")
        
        print(f"\n3. Тест с реальным Firecrawl API:")
        async with FirecrawlClient() as firecrawl_client:
            # Тестируем только первый URL
            test_url = "https://huggingface.co/blog/jjokah/small-language-model"
            
            print(f"   Запрашиваем заголовок для: {test_url[:50]}...")
            real_title = await url_extractor._get_page_title(test_url, firecrawl_client)
            
            print(f"   Результат: '{real_title}'")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_extraction())