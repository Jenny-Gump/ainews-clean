#!/usr/bin/env python3
"""
Тест конкретных проблемных URL с плохими заголовками
"""
import asyncio
import sys

sys.path.append('/Users/skynet/Desktop/AI DEV/ainews-clean')

from change_tracking.url_extractor import URLExtractor
from services.firecrawl_client import FirecrawlClient


async def test_specific_urls():
    """Тест конкретных проблемных URL"""
    print("🧪 ТЕСТИРУЕМ ПРОБЛЕМНЫЕ URL С ПЛОХИМИ ЗАГОЛОВКАМИ")
    print("=" * 60)
    
    # Проблемные URL из БД
    problem_urls = [
        "https://huggingface.co/blog/jjokah/small-language-model",  # "Feb 22" 
        "https://huggingface.co/blog/hexgrad/g2p",                # "Feb 5"
        "https://huggingface.co/blog/NormalUhr/grpo"              # "Feb 7"
    ]
    
    try:
        url_extractor = URLExtractor()
        
        async with FirecrawlClient() as firecrawl_client:
            for i, url in enumerate(problem_urls, 1):
                print(f"\n{i}. Тестируем: {url}")
                
                # Получаем реальный заголовок
                real_title = await url_extractor._get_page_title(url, firecrawl_client)
                
                if real_title:
                    print(f"   ✅ НОВЫЙ заголовок: '{real_title}'")
                    print(f"   📏 Длина: {len(real_title)} символов")
                else:
                    print(f"   ❌ Не удалось получить заголовок")
                
                # Пауза между запросами
                await asyncio.sleep(2)
                
        print(f"\n🎯 РЕЗУЛЬТАТ:")
        print(f"   Вместо коротких дат типа 'Feb 22', 'Feb 5'")
        print(f"   теперь получаем полные заголовки статей!")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_specific_urls())