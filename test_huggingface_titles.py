#!/usr/bin/env python3
"""
Тест новых заголовков на реальном HuggingFace источнике
"""
import asyncio
import sys

sys.path.append('/Users/skynet/Desktop/AI DEV/ainews-clean')

from change_tracking.monitor import ChangeMonitor


async def test_huggingface():
    """Тест HuggingFace источника"""
    print("🧪 Тестируем HuggingFace с новыми заголовками")
    print("=" * 60)
    
    monitor = ChangeMonitor()
    
    # Сканируем только HuggingFace
    hf_url = "https://huggingface.co/blog"
    
    print(f"🔍 Сканируем: {hf_url}")
    
    try:
        # Запускаем сканирование одного источника
        result = await monitor.scan_webpage(hf_url)
        
        print(f"\n📊 Результат сканирования:")
        print(f"   Статус: {result.get('status')}")
        print(f"   Источник: {result.get('source_domain')}")
        print(f"   URL найдено: {result.get('urls_found', 0)}")
        
        if result.get('urls_found', 0) > 0:
            print(f"\n✅ Найдены URL! Теперь проверим заголовки в БД...")
            
            # Проверяем что попало в tracked_urls 
            import sqlite3
            from pathlib import Path
            
            db_path = Path('/Users/skynet/Desktop/AI DEV/ainews-clean/data/change_tracking.db')
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("""
                    SELECT article_title, article_url, discovered_at
                    FROM tracked_urls 
                    WHERE source_page_url = ?
                      AND discovered_at > datetime('now', '-5 minutes')
                    ORDER BY discovered_at DESC
                    LIMIT 5
                """, (hf_url,))
                
                recent_urls = cursor.fetchall()
                
            if recent_urls:
                print(f"\n🎯 Новые заголовки из HuggingFace:")
                for i, (title, url, discovered) in enumerate(recent_urls, 1):
                    print(f"   {i}. '{title}'")
                    print(f"      URL: {url[:70]}...")
                    print(f"      Время: {discovered}")
                    print()
                    
                print(f"✅ Видим {len(recent_urls)} новых заголовков!")
                
                # Проверяем качество
                good_titles = [title for title, _, _ in recent_urls if len(title) > 10]
                print(f"📈 Качественных заголовков: {len(good_titles)} из {len(recent_urls)}")
                
            else:
                print(f"⚠️ Новые URL не найдены в БД")
        else:
            print(f"⚠️ URL не найдены при сканировании")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_huggingface())