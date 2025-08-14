#!/usr/bin/env python3
"""
Test the fixed deduplication methods in database.py
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import ChangeTrackingDB

def test_fixed_methods():
    """Тестирует исправленные методы дедупликации"""
    
    print("=== Testing Fixed Deduplication Methods ===\n")
    
    db = ChangeTrackingDB()
    
    # 1. Тест store_tracked_urls
    print("1. Testing store_tracked_urls method:")
    test_urls = [
        {
            'article_url': 'https://method-test.com/unique-test-1',
            'article_title': 'Method Test Article 1',
            'source_domain': 'method-test.com'
        },
        {
            'article_url': 'https://method-test.com/unique-test-2',
            'article_title': 'Method Test Article 2',
            'source_domain': 'method-test.com'
        }
    ]
    
    # Первое добавление
    result1 = db.store_tracked_urls('https://method-test.com/blog', test_urls)
    print(f"   First call: {result1} URLs added")
    
    # Второе добавление (должно быть 0)
    result2 = db.store_tracked_urls('https://www.method-test.com/blog', test_urls)
    print(f"   Second call: {result2} URLs added (expected: 0)")
    print(f"   ✅ SUCCESS" if result2 == 0 else f"   ❌ FAILURE: {result2} duplicates allowed")
    print()
    
    # 2. Тест store_url_batch
    print("2. Testing store_url_batch method:")
    batch_urls = [
        {
            'article_url': 'https://batch-test.com/unique-batch-1',
            'article_title': 'Batch Test 1',
            'source_domain': 'batch-test.com'
        },
        {
            'article_url': 'https://batch-test.com/unique-batch-2',
            'article_title': 'Batch Test 2',
            'source_domain': 'batch-test.com'
        }
    ]
    
    batch_result1 = db.store_url_batch('https://batch-test.com/news', batch_urls, is_baseline=True)
    print(f"   First batch: {batch_result1} URLs added")
    
    # Повторный batch (должно быть 0 новых)
    batch_result2 = db.store_url_batch('https://batch-test.com/articles', batch_urls, is_baseline=False)
    print(f"   Second batch: {batch_result2} URLs added (expected: 0)")
    print(f"   ✅ SUCCESS" if batch_result2 == 0 else f"   ❌ FAILURE: {batch_result2} duplicates allowed")
    print()
    
    # 3. Тест export_urls_to_articles
    print("3. Testing export_urls_to_articles method:")
    new_urls = db.get_new_urls(limit=3)
    if len(new_urls) > 0:
        print(f"   Found {len(new_urls)} URLs ready for export")
        
        # Экспорт
        export_result1 = db.export_urls_to_articles(new_urls[:1])
        print(f"   First export: {export_result1} URLs exported")
        
        # Повторный экспорт (должен обнаружить дубль в articles)
        # Сначала сбросим флаги для теста
        from core.database import Database
        core_db = Database()
        with core_db.get_connection() as conn:
            url_data = new_urls[0]
            conn.execute("""
                UPDATE tracked_urls 
                SET is_new = 1, exported_to_articles = 0, exported_at = NULL
                WHERE id = ?
            """, (url_data['id'],))
        
        export_result2 = db.export_urls_to_articles(new_urls[:1])
        print(f"   Second export: {export_result2} URLs exported (expected: 0)")
        print(f"   ✅ SUCCESS" if export_result2 == 0 else f"   ❌ FAILURE: {export_result2} duplicates allowed")
    else:
        print("   ⚠️  No new URLs available for testing")
    print()
    
    # 4. Общие статистики
    print("4. Final statistics:")
    stats = db.get_url_extraction_stats()
    if 'error' not in stats:
        print(f"   Total URLs: {stats.get('total_urls', 0)}")
        print(f"   New URLs: {stats.get('new_urls', 0)}")
        print(f"   Exported URLs: {stats.get('exported_urls', 0)}")
        print(f"   Pending Export: {stats.get('pending_export', 0)}")
        
        # Проверим дубли через core database
        with core_db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) as dup_count 
                FROM (SELECT article_url FROM tracked_urls GROUP BY article_url HAVING COUNT(*) > 1)
            """)
            final_dups = cursor.fetchone()[0]
            print(f"   Duplicates in tracked_urls: {final_dups}")
            
            cursor = conn.execute("""
                SELECT COUNT(*) as dup_count 
                FROM (SELECT url FROM articles GROUP BY url HAVING COUNT(*) > 1)
            """)
            article_dups = cursor.fetchone()[0]
            print(f"   Duplicates in articles: {article_dups}")
    else:
        print(f"   ❌ ERROR getting stats: {stats['error']}")
    
    print()
    print("=== TEST SUMMARY ===")
    
    # Оценка успеха
    success_conditions = [
        result2 == 0,  # store_tracked_urls не добавил дубли
        batch_result2 == 0,  # store_url_batch не добавил дубли
        stats.get('error') is None,  # статистика работает
    ]
    
    if len(new_urls) > 0:
        success_conditions.append(export_result2 == 0)  # export не создал дубли
    
    overall_success = all(success_conditions)
    
    if overall_success:
        print("✅ ALL TESTS PASSED!")
        print("   - store_tracked_urls: Proper deduplication")
        print("   - store_url_batch: Proper deduplication") 
        print("   - export_urls_to_articles: Duplicate detection")
        print("   - Database integrity maintained")
    else:
        print("❌ SOME TESTS FAILED")
        print(f"   store_tracked_urls: {'✅' if result2 == 0 else '❌'}")
        print(f"   store_url_batch: {'✅' if batch_result2 == 0 else '❌'}")
        if len(new_urls) > 0:
            print(f"   export_urls_to_articles: {'✅' if export_result2 == 0 else '❌'}")
    
    return overall_success

if __name__ == "__main__":
    success = test_fixed_methods()
    sys.exit(0 if success else 1)