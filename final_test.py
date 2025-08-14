#!/usr/bin/env python3
"""
Финальный тест новой функциональности получения заголовков
"""
import asyncio
import sys

sys.path.append('/Users/skynet/Desktop/AI DEV/ainews-clean')

from change_tracking.url_extractor import URLExtractor
from services.firecrawl_client import FirecrawlClient


async def final_test():
    """Финальный тест"""
    print("🧪 ФИНАЛЬНЫЙ ТЕСТ: Качество заголовков")
    print("=" * 60)
    
    # Реальный markdown из HuggingFace блога  
    real_markdown = """
    [Feb 22](https://huggingface.co/blog/jjokah/small-language-model)
    [Feb 5](https://huggingface.co/blog/hexgrad/g2p)
    """
    
    source_url = "https://huggingface.co/blog"
    
    try:
        url_extractor = URLExtractor()
        
        print("📋 СТАРЫЙ СПОСОБ (заголовки из ссылок):")
        old_results = await url_extractor.extract_urls_from_content(
            real_markdown, 
            source_url,
            use_page_titles=False
        )
        
        for i, result in enumerate(old_results, 1):
            print(f"   {i}. '{result['article_title']}'")
            print(f"      URL: {result['article_url']}")
        
        print(f"\n🚀 НОВЫЙ СПОСОБ (заголовки из Firecrawl API):")
        
        async with FirecrawlClient() as firecrawl_client:
            new_results = await url_extractor.extract_urls_from_content(
                real_markdown,
                source_url, 
                use_page_titles=True,
                firecrawl_client=firecrawl_client
            )
            
            for i, result in enumerate(new_results, 1):
                print(f"   {i}. '{result['article_title']}'")
                print(f"      URL: {result['article_url']}")
                
        print(f"\n📊 СРАВНЕНИЕ КАЧЕСТВА:")
        print(f"   Старые заголовки: {[r['article_title'] for r in old_results]}")
        print(f"   Новые заголовки:  {[r['article_title'] for r in new_results]}")
        
        # Проверяем что новые заголовки действительно лучше
        old_avg_length = sum(len(r['article_title']) for r in old_results) / len(old_results) if old_results else 0
        new_avg_length = sum(len(r['article_title']) for r in new_results) / len(new_results) if new_results else 0
        
        print(f"\n📈 МЕТРИКИ:")
        print(f"   Средняя длина старых заголовков: {old_avg_length:.1f} символов")
        print(f"   Средняя длина новых заголовков:  {new_avg_length:.1f} символов")
        
        if new_avg_length > old_avg_length * 2:
            print(f"\n✅ УСПЕХ! Качество заголовков значительно улучшилось!")
            print(f"   Увеличение качества: {(new_avg_length/old_avg_length*100-100):.0f}%")
        else:
            print(f"\n⚠️ Улучшение не столь заметно")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(final_test())