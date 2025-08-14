#!/usr/bin/env python3
"""
Быстрая миграция оставшихся данных из SQLite в Supabase
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
import os
from datetime import datetime

# Настройки подключения
SQLITE_DB = "/Users/skynet/Desktop/AI DEV/ainews-clean/data/ainews.db"
SUPABASE_CONN = "postgresql://postgres.mtguynupyltlqiwhmilc:Moh1981mmm!!!@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

def migrate_media_files_batch(sqlite_conn, pg_conn, start_id, end_id):
    """Мигрирует партию записей media_files"""
    cursor_sqlite = sqlite_conn.cursor()
    cursor_pg = pg_conn.cursor()
    
    # Получаем данные из SQLite
    query = """
    SELECT id, media_id, article_id, url, type, file_path, created_at,
           source_id, file_size, mime_type, width, height, alt_text, status,
           error, source, caption, wp_media_id, wp_upload_status, wp_uploaded_at,
           alt_text_ru, caption_ru, image_order, processing_session_id, wp_source_url
    FROM media_files
    WHERE id BETWEEN ? AND ?
    ORDER BY id
    """
    
    cursor_sqlite.execute(query, (start_id, end_id))
    records = cursor_sqlite.fetchall()
    
    if not records:
        return 0
    
    # Подготавливаем данные для вставки
    insert_query = """
    INSERT INTO media_files (
        id_integer, media_id, article_id, url, type, file_path, created_at,
        source_id, file_size, mime_type, width, height, alt_text, status,
        error, source, caption, wp_media_id, wp_upload_status, wp_uploaded_at,
        alt_text_ru, caption_ru, image_order, processing_session_id, wp_source_url
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (id_integer) DO NOTHING
    """
    
    # Выполняем пакетную вставку
    execute_batch(cursor_pg, insert_query, records, page_size=50)
    pg_conn.commit()
    
    return len(records)

def migrate_wordpress_articles(sqlite_conn, pg_conn):
    """Мигрирует все записи wordpress_articles"""
    cursor_sqlite = sqlite_conn.cursor()
    cursor_pg = pg_conn.cursor()
    
    # Проверяем структуру таблицы в Supabase
    cursor_pg.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'wordpress_articles'
    """)
    columns = [row[0] for row in cursor_pg.fetchall()]
    
    if not columns:
        print("Таблица wordpress_articles не найдена в Supabase")
        return 0
    
    # Получаем все записи из SQLite
    cursor_sqlite.execute("SELECT * FROM wordpress_articles")
    records = cursor_sqlite.fetchall()
    
    if not records:
        return 0
    
    # Получаем имена колонок из SQLite
    cursor_sqlite.execute("PRAGMA table_info(wordpress_articles)")
    sqlite_columns = [row[1] for row in cursor_sqlite.fetchall()]
    
    # Формируем запрос вставки
    placeholders = ', '.join(['%s'] * len(sqlite_columns))
    columns_str = ', '.join(sqlite_columns)
    
    insert_query = f"""
    INSERT INTO wordpress_articles ({columns_str})
    VALUES ({placeholders})
    ON CONFLICT DO NOTHING
    """
    
    # Выполняем пакетную вставку
    execute_batch(cursor_pg, insert_query, records, page_size=50)
    pg_conn.commit()
    
    return len(records)

def main():
    """Основная функция миграции"""
    print("Начинаем миграцию данных из SQLite в Supabase...")
    
    # Подключаемся к базам данных
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    pg_conn = psycopg2.connect(SUPABASE_CONN)
    
    try:
        # Мигрируем media_files партиями
        print("\n1. Миграция media_files...")
        total_media = 0
        
        # Диапазоны для миграции
        ranges = [
            (3708, 3800),
            (3801, 3900),
            (3901, 4000)
        ]
        
        for start_id, end_id in ranges:
            count = migrate_media_files_batch(sqlite_conn, pg_conn, start_id, end_id)
            total_media += count
            print(f"   Мигрировано записей {start_id}-{end_id}: {count}")
        
        print(f"   Всего мигрировано media_files: {total_media}")
        
        # Мигрируем wordpress_articles
        print("\n2. Миграция wordpress_articles...")
        wp_count = migrate_wordpress_articles(sqlite_conn, pg_conn)
        print(f"   Мигрировано wordpress_articles: {wp_count}")
        
        # Проверяем финальные количества
        cursor_pg = pg_conn.cursor()
        cursor_pg.execute("SELECT COUNT(*) FROM media_files")
        media_total = cursor_pg.fetchone()[0]
        
        cursor_pg.execute("SELECT COUNT(*) FROM wordpress_articles")
        wp_total = cursor_pg.fetchone()[0]
        
        print("\n=== ИТОГИ МИГРАЦИИ ===")
        print(f"media_files в Supabase: {media_total}")
        print(f"wordpress_articles в Supabase: {wp_total}")
        
    except Exception as e:
        print(f"Ошибка при миграции: {e}")
        pg_conn.rollback()
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    main()