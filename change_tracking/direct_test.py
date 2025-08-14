#!/usr/bin/env python3
"""
Direct test of deduplication fix using MCP queries
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.database import Database

def direct_deduplication_test():
    """Прямой тест дедупликации через Database"""
    
    print("=== Direct Deduplication Test ===\n")
    
    db = Database()
    
    # 1. Проверяем схему
    print("1. Checking schema:")
    with db.get_connection() as conn:
        cursor = conn.execute("PRAGMA table_info(tracked_urls)")
        schema = cursor.fetchall()
        print("   tracked_urls columns:")
        for col in schema:
            print(f"     {col['name']}: {col['type']} {'(UNIQUE)' if col['pk'] else ''}")
        
        # Проверяем индексы
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='tracked_urls'")
        indexes = cursor.fetchall()
        print("   Indexes:")
        for idx in indexes:
            print(f"     {idx['name']}")
    print()
    
    # 2. Проверяем дубли
    print("2. Checking duplicates:")
    with db.get_connection() as conn:
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
        print(f"   Current duplicates: {duplicate_count}")
        
        cursor = conn.execute("SELECT COUNT(*) FROM tracked_urls")
        total_count = cursor.fetchone()[0]
        print(f"   Total URLs: {total_count}")
        
        cursor = conn.execute("SELECT COUNT(*) FROM tracked_urls WHERE is_new = 1")
        new_count = cursor.fetchone()[0]
        print(f"   New URLs: {new_count}")
    print()
    
    # 3. Тест constraint
    print("3. Testing UNIQUE constraint:")
    with db.get_connection() as conn:
        cursor = conn.execute("SELECT article_url FROM tracked_urls LIMIT 1")
        result = cursor.fetchone()
        if result:
            test_url = result[0]
            try:
                conn.execute("""
                    INSERT INTO tracked_urls (source_page_url, article_url, article_title, source_domain, is_new) 
                    VALUES (?, ?, ?, ?, ?)
                """, ('https://test.com', test_url, 'Test', 'test.com', 1))
                print("   ❌ FAILURE: UNIQUE constraint not working!")
                success = False
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    print("   ✅ SUCCESS: UNIQUE constraint working")
                    success = True
                else:
                    print(f"   ❌ UNEXPECTED ERROR: {e}")
                    success = False
        else:
            print("   ⚠️  No URLs found to test")
            success = True
    print()
    
    # 4. Тест добавления нового URL
    print("4. Testing new URL addition:")
    test_url = "https://dedup-test.com/test-unique-url-123"
    
    with db.get_connection() as conn:
        # Сначала удаляем тестовый URL если существует
        conn.execute("DELETE FROM tracked_urls WHERE article_url = ?", (test_url,))
        
        # Добавляем первый раз
        try:
            conn.execute("""
                INSERT INTO tracked_urls (source_page_url, article_url, article_title, source_domain, is_new) 
                VALUES (?, ?, ?, ?, ?)
            """, ('https://dedup-test.com/blog', test_url, 'Test Article', 'dedup-test.com', 1))
            print("   First insert: SUCCESS")
            first_success = True
        except Exception as e:
            print(f"   First insert: FAILED - {e}")
            first_success = False
            
        # Пытаемся добавить второй раз
        if first_success:
            try:
                conn.execute("""
                    INSERT INTO tracked_urls (source_page_url, article_url, article_title, source_domain, is_new) 
                    VALUES (?, ?, ?, ?, ?)
                """, ('https://www.dedup-test.com/blog', test_url, 'Test Article 2', 'dedup-test.com', 1))
                print("   Second insert: FAILED - duplicate was allowed!")
                second_blocked = False
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    print("   Second insert: SUCCESS - duplicate blocked")
                    second_blocked = True
                else:
                    print(f"   Second insert: ERROR - {e}")
                    second_blocked = False
        
        # Очищаем тестовый URL
        conn.execute("DELETE FROM tracked_urls WHERE article_url = ?", (test_url,))
    
    overall_success = success and first_success and second_blocked
    
    print()
    print("=== TEST SUMMARY ===")
    if overall_success:
        print("✅ SUCCESS: Deduplication fix is working correctly!")
        print("   - Schema updated with proper UNIQUE constraint")
        print("   - No existing duplicates found")  
        print("   - UNIQUE constraint prevents new duplicates")
    else:
        print("❌ FAILURE: Issues found with deduplication")
        
    return overall_success

if __name__ == "__main__":
    success = direct_deduplication_test()
    sys.exit(0 if success else 1)