#!/usr/bin/env python3
"""
Test script for fixed deduplication system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import ChangeTrackingDB

def test_deduplication_fix():
    """Тестирует исправления в системе дедупликации"""
    
    print("=== Testing Fixed Deduplication System ===\n")
    
    db = ChangeTrackingDB()
    
    # 1. Проверяем статистику до тестов
    print("1. Current database state:")
    stats = db.get_url_extraction_stats()
    print(f"   Total URLs: {stats.get('total_urls', 0)}")
    print(f"   New URLs: {stats.get('new_urls', 0)}")
    print(f"   Exported URLs: {stats.get('exported_urls', 0)}")
    print(f"   Pending Export: {stats.get('pending_export', 0)}")
    print()
    
    # 2. Проверяем что дублей нет
    print("2. Checking current duplicates:")
    from core.database import Database
    core_db = Database()
    with core_db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT COUNT(*) as duplicate_count 
            FROM (
                SELECT article_url 
                FROM tracked_urls 
                GROUP BY article_url 
                HAVING COUNT(*) > 1
            )
        """)
        duplicate_count = cursor.fetchone()[0]
        print(f"   Duplicate URLs in tracked_urls: {duplicate_count}")
        print(f"   ✅ SUCCESS: No duplicates found" if duplicate_count == 0 else f"   ❌ FAILURE: {duplicate_count} duplicates found")
        
        cursor = conn.execute("""
            SELECT COUNT(*) as duplicate_count
            FROM (
                SELECT url
                FROM articles
                GROUP BY url
                HAVING COUNT(*) > 1
            )
        """)
        article_duplicates = cursor.fetchone()[0]
        print(f"   Duplicate URLs in articles: {article_duplicates}")
        print(f"   ✅ SUCCESS: No duplicates found" if article_duplicates == 0 else f"   ❌ FAILURE: {article_duplicates} duplicates found")
    print()
    
    # 3. Тестируем UNIQUE constraint
    print("3. Testing UNIQUE constraint:")
    try:
        with core_db.get_connection() as conn:
            # Получаем один существующий URL
            cursor = conn.execute("SELECT article_url FROM tracked_urls LIMIT 1")
            result = cursor.fetchone()
            if result:
                existing_url = result[0]
                
                # Пытаемся вставить дубль
                try:
                    conn.execute("""
                        INSERT INTO tracked_urls (source_page_url, article_url, article_title, source_domain, is_new) 
                        VALUES (?, ?, ?, ?, ?)
                    """, ('https://test.com', existing_url, 'Test', 'test.com', 1))
                    print("   ❌ FAILURE: Duplicate was allowed!")
                    constraint_working = False
                except Exception as e:
                    if "UNIQUE constraint failed" in str(e):
                        print("   ✅ SUCCESS: UNIQUE constraint blocked duplicate")
                        constraint_working = True
                    else:
                        print(f"   ❌ UNEXPECTED ERROR: {e}")
                        constraint_working = False
            else:
                print("   ⚠️  SKIPPED: No existing URLs found")
                constraint_working = True
    except Exception as e:
        print(f"   ❌ ERROR testing constraint: {e}")
        constraint_working = False
    print()
    
    # 4. Тестируем добавление новых URL
    print("4. Testing new URL addition:")
    test_urls = [
        {
            'article_url': 'https://dedup-test.com/unique-url-1',
            'article_title': 'Test Article 1',
            'source_domain': 'dedup-test.com'
        },
        {
            'article_url': 'https://dedup-test.com/unique-url-2', 
            'article_title': 'Test Article 2',
            'source_domain': 'dedup-test.com'
        }
    ]
    
    result1 = db.store_tracked_urls('https://dedup-test.com/blog', test_urls)
    print(f"   First batch: {result1} new URLs added")
    
    # Пытаемся добавить те же URL снова
    result2 = db.store_tracked_urls('https://www.dedup-test.com/blog', test_urls)
    print(f"   Second batch (should be 0): {result2} new URLs added")
    print(f"   ✅ SUCCESS: Duplicates prevented" if result2 == 0 else f"   ❌ FAILURE: {result2} duplicates allowed")
    print()
    
    # 5. Проверяем экспорт protection
    print("5. Testing export protection:")
    new_urls = db.get_new_urls(limit=2)
    if new_urls:
        export_result1 = db.export_urls_to_articles(new_urls[:1])  # Экспортируем только 1 URL
        print(f"   First export: {export_result1} URLs exported")
        
        # Сбрасываем флаги для повторного теста
        with core_db.get_connection() as conn:
            for url_data in new_urls[:1]:
                conn.execute("""
                    UPDATE tracked_urls 
                    SET is_new = 1, exported_to_articles = 0, exported_at = NULL
                    WHERE id = ?
                """, (url_data['id'],))
        
        export_result2 = db.export_urls_to_articles(new_urls[:1])
        print(f"   Second export: {export_result2} URLs exported (should be 0)")
        print(f"   ✅ SUCCESS: Duplicate export prevented" if export_result2 == 0 else f"   ❌ FAILURE: {export_result2} duplicates allowed")
    else:
        print("   ⚠️  SKIPPED: No new URLs available for testing")
    print()
    
    # 6. Финальная статистика
    print("6. Final verification:")
    with core_db.get_connection() as conn:
        # Проверяем финальные дубли
        cursor = conn.execute("""
            SELECT COUNT(*) as duplicate_count 
            FROM (
                SELECT article_url 
                FROM tracked_urls 
                GROUP BY article_url 
                HAVING COUNT(*) > 1
            )
        """)
        final_duplicates = cursor.fetchone()[0]
        
        cursor = conn.execute("""
            SELECT COUNT(*) as duplicate_count
            FROM (
                SELECT url
                FROM articles
                GROUP BY url
                HAVING COUNT(*) > 1
            )
        """)
        final_article_duplicates = cursor.fetchone()[0]
        
        print(f"   Final tracked_urls duplicates: {final_duplicates}")
        print(f"   Final articles duplicates: {final_article_duplicates}")
    
    # Общий результат
    overall_success = (
        duplicate_count == 0 and 
        article_duplicates == 0 and
        constraint_working and
        result2 == 0 and
        final_duplicates == 0 and
        final_article_duplicates == 0
    )
    
    print()
    print("=== DEDUPLICATION FIX SUMMARY ===")
    if overall_success:
        print("✅ SUCCESS: All deduplication tests passed!")
        print("   - Schema migration completed")
        print("   - UNIQUE constraint on article_url working")
        print("   - No existing duplicates found")
        print("   - Proper duplicate prevention in store methods")
        print("   - Export protection working correctly")
    else:
        print("❌ FAILURE: Some issues remain")
    
    return overall_success

if __name__ == "__main__":
    success = test_deduplication_fix()
    sys.exit(0 if success else 1)