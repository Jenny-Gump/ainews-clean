#!/usr/bin/env python3
"""
Финальный скрипт миграции данных из SQLite в Supabase
Использует прямое подключение к базам данных
"""

import sqlite3
import os
from datetime import datetime
import json
from supabase import create_client, Client
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Конфигурация
SQLITE_ARTICLES_DB = "/Users/skynet/Desktop/AI DEV/ainews-clean/data/ainews.db"
SQLITE_MONITORING_DB = "/Users/skynet/Desktop/AI DEV/ainews-clean/data/monitoring.db"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

# Подключение к Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def migrate_media_files():
    """Миграция media_files"""
    print("\n=== Миграция media_files ===")
    
    conn = sqlite3.connect(SQLITE_ARTICLES_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Получаем все media_files
    cursor.execute("SELECT * FROM media_files WHERE id > 3602 ORDER BY id LIMIT 300")
    records = cursor.fetchall()
    
    migrated = 0
    errors = 0
    
    for record in records:
        try:
            data = {
                'article_id': record['article_id'],
                'url': record['url'],
                'local_path': record['file_path'],
                'alt_text': record['alt_text'],
                'alt_text_ru': record['alt_text_ru'],
                'width': record['width'],
                'height': record['height'],
                'file_size': record['file_size'],
                'mime_type': record['mime_type'] or 'image/jpeg',
                'status': record['status'] or 'pending',
                'created_at': record['created_at']
            }
            
            # Вставка в Supabase
            result = supabase.table('media_files').insert(data).execute()
            migrated += 1
            
            if migrated % 10 == 0:
                print(f"  Мигрировано: {migrated}/{len(records)}")
                
        except Exception as e:
            errors += 1
            print(f"  Ошибка для media_id {record['media_id']}: {str(e)[:100]}")
    
    conn.close()
    print(f"✅ media_files: мигрировано {migrated}, ошибок {errors}")
    return migrated, errors

def migrate_wordpress_articles():
    """Миграция wordpress_articles"""
    print("\n=== Миграция wordpress_articles ===")
    
    conn = sqlite3.connect(SQLITE_ARTICLES_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Получаем все wordpress_articles
    cursor.execute("SELECT * FROM wordpress_articles WHERE id > 1 ORDER BY id LIMIT 200")
    records = cursor.fetchall()
    
    migrated = 0
    errors = 0
    
    for record in records:
        try:
            # Подготовка данных
            categories = record['categories']
            if categories and isinstance(categories, str):
                try:
                    categories = json.loads(categories)
                except:
                    categories = [categories]
            
            tags = record['tags']
            if tags and isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except:
                    tags = [tags]
            
            images_data = record['images_data']
            if images_data and isinstance(images_data, str):
                try:
                    images_data = json.loads(images_data)
                except:
                    images_data = None
            
            data = {
                'article_id': record['article_id'],
                'title': record['title'],
                'content': record['content'][:50000],  # Ограничение на размер
                'excerpt': record['excerpt'],
                'slug': record['slug'],
                'categories': categories,
                'tags': tags,
                '_yoast_wpseo_title': record['_yoast_wpseo_title'],
                '_yoast_wpseo_metadesc': record['_yoast_wpseo_metadesc'],
                'focus_keyword': record['focus_keyword'],
                'featured_image_index': record['featured_image_index'],
                'images_data': images_data,
                'translation_status': record['translation_status'] or 'completed',
                'translated_at': record['translated_at'],
                'published_to_wp': bool(record['published_to_wp']),
                'wp_post_id': record['wp_post_id'],
                'target_language': 'ru',
                'llm_model': record['llm_model'],
                'created_at': record['created_at']
            }
            
            # Вставка в Supabase
            result = supabase.table('wordpress_articles').insert(data).execute()
            migrated += 1
            
            if migrated % 10 == 0:
                print(f"  Мигрировано: {migrated}/{len(records)}")
                
        except Exception as e:
            errors += 1
            print(f"  Ошибка для article_id {record['article_id']}: {str(e)[:100]}")
    
    conn.close()
    print(f"✅ wordpress_articles: мигрировано {migrated}, ошибок {errors}")
    return migrated, errors

def migrate_monitoring_sample():
    """Миграция sample данных из monitoring для тестирования"""
    print("\n=== Миграция monitoring данных (sample) ===")
    
    conn = sqlite3.connect(SQLITE_MONITORING_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Мигрируем последние 100 записей из performance_metrics
    cursor.execute("""
        SELECT * FROM performance_metrics 
        ORDER BY timestamp DESC 
        LIMIT 100
    """)
    records = cursor.fetchall()
    
    migrated = 0
    for record in records:
        try:
            details = record['details']
            if details and isinstance(details, str):
                try:
                    details = json.loads(details)
                except:
                    details = None
            
            data = {
                'timestamp': record['timestamp'],
                'metric_type': record['metric_type'],
                'operation': record['operation'],
                'duration_ms': record['duration_ms'],
                'success': bool(record['success']),
                'error_message': record['error_message'],
                'details': details
            }
            
            result = supabase.table('performance_metrics').insert(data).execute()
            migrated += 1
            
        except Exception as e:
            print(f"  Ошибка: {str(e)[:100]}")
    
    conn.close()
    print(f"✅ performance_metrics: мигрировано {migrated} записей")
    return migrated

def check_migration_status():
    """Проверка статуса миграции"""
    print("\n=== Проверка статуса миграции ===")
    
    tables = ['sources', 'articles', 'media_files', 'wordpress_articles', 'performance_metrics']
    
    for table in tables:
        try:
            result = supabase.table(table).select('*', count='exact').execute()
            count = result.count if hasattr(result, 'count') else len(result.data)
            print(f"  {table}: {count} записей")
        except Exception as e:
            print(f"  {table}: Ошибка - {str(e)[:50]}")

def main():
    """Основная функция миграции"""
    print("=" * 60)
    print("ФИНАЛЬНАЯ МИГРАЦИЯ ДАННЫХ SQLite → Supabase")
    print("=" * 60)
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Ошибка: Не настроены переменные окружения SUPABASE_URL и SUPABASE_KEY")
        print("Добавьте их в файл .env")
        return
    
    # Проверка начального статуса
    check_migration_status()
    
    # Миграция данных
    print("\nНачинаем миграцию...")
    
    # 1. Media files
    media_migrated, media_errors = migrate_media_files()
    
    # 2. WordPress articles
    wp_migrated, wp_errors = migrate_wordpress_articles()
    
    # 3. Monitoring sample
    monitoring_migrated = migrate_monitoring_sample()
    
    # Финальная проверка
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ МИГРАЦИИ:")
    print("=" * 60)
    check_migration_status()
    
    print("\n✅ Миграция завершена!")
    print(f"  media_files: {media_migrated} записей")
    print(f"  wordpress_articles: {wp_migrated} записей")
    print(f"  performance_metrics: {monitoring_migrated} записей")
    
    if media_errors > 0 or wp_errors > 0:
        print(f"\n⚠️ Обнаружены ошибки:")
        print(f"  media_files: {media_errors} ошибок")
        print(f"  wordpress_articles: {wp_errors} ошибок")

if __name__ == "__main__":
    main()