#!/usr/bin/env python3
"""
Дебаг для проверки что возвращает Firecrawl API
"""
import asyncio
import os
import sys

# Добавляем путь к проекту
sys.path.append('/Users/skynet/Desktop/AI DEV/ainews-clean')

from services.firecrawl_client import FirecrawlClient


async def debug_firecrawl():
    """Дебаг Firecrawl API"""
    print("🔍 Дебаг Firecrawl API")
    print("=" * 60)
    
    test_url = "https://huggingface.co/blog/jjokah/small-language-model"
    
    try:
        async with FirecrawlClient() as firecrawl_client:
            print(f"📡 Запрос к: {test_url}")
            
            scraped_data = await firecrawl_client.scrape_url(
                test_url, 
                formats=['markdown']
            )
            
            print(f"\n📋 Ключи в ответе: {list(scraped_data.keys())}")
            
            if 'metadata' in scraped_data:
                metadata = scraped_data['metadata']
                print(f"📋 Ключи в metadata: {list(metadata.keys())}")
                print(f"📜 Title: '{metadata.get('title', 'НЕТ ЗАГОЛОВКА')}'")
            else:
                print("❌ Нет metadata в ответе")
                
            # Посмотрим на markdown
            markdown = scraped_data.get('markdown', '')
            if markdown:
                lines = markdown.split('\n')[:10]
                print(f"\n📄 Первые 10 строк markdown:")
                for i, line in enumerate(lines, 1):
                    print(f"   {i:2}. {line}")
            else:
                print("❌ Нет markdown в ответе")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_firecrawl())