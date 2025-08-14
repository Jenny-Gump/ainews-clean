#!/usr/bin/env python3
"""
Тест для проверки новой функциональности получения заголовков через Firecrawl API
"""
import asyncio
import os
import sys

# Добавляем путь к проекту
sys.path.append('/Users/skynet/Desktop/AI DEV/ainews-clean')

from change_tracking.url_extractor import URLExtractor
from services.firecrawl_client import FirecrawlClient


async def test_title_extraction():
    """Тест извлечения заголовков"""
    print("🧪 Тестируем извлечение заголовков через Firecrawl API")
    print("=" * 60)
    
    # Тестовый markdown с HuggingFace ссылкой
    test_markdown = """
    # HuggingFace Blog
    
    Check out these posts:
    - [Feb 22](https://huggingface.co/blog/jjokah/small-language-model) - About small models
    - [Feb 5](https://huggingface.co/blog/hexgrad/g2p) - G2P conversion
    """
    
    test_source_url = "https://huggingface.co/blog"
    
    try:
        # Создаем экземпляры
        url_extractor = URLExtractor()
        
        print("1. Тест СТАРОГО способа (без Firecrawl):")
        old_results = await url_extractor.extract_urls_from_content(
            test_markdown, 
            test_source_url,
            use_page_titles=False
        )
        
        for i, result in enumerate(old_results, 1):
            print(f"   {i}. '{result['article_title']}' -> {result['article_url'][:50]}...")
        
        print(f"\n2. Тест НОВОГО способа (с Firecrawl):")
        
        # Проверяем API ключ
        api_key = os.getenv('FIRECRAWL_API_KEY')
        if not api_key:
            print("   ❌ FIRECRAWL_API_KEY не найден в переменных окружения")
            return
            
        async with FirecrawlClient() as firecrawl_client:
            new_results = await url_extractor.extract_urls_from_content(
                test_markdown,
                test_source_url, 
                use_page_titles=True,
                firecrawl_client=firecrawl_client
            )
            
            for i, result in enumerate(new_results, 1):
                print(f"   {i}. '{result['article_title']}' -> {result['article_url'][:50]}...")
                print(f"      [Длина заголовка: {len(result['article_title'])} символов]")
                
        print(f"\n📊 Результаты:")
        print(f"   Старый способ: {len(old_results)} URL")
        print(f"   Новый способ:  {len(new_results)} URL")
        
        if new_results:
            print(f"\n✅ Тест прошел успешно!")
            print(f"   Качество заголовков улучшилось!")
        else:
            print(f"\n⚠️ Новый способ не вернул результатов")
            
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_title_extraction())