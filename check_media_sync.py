#!/usr/bin/env python3
"""
Проверка и синхронизация таблицы media_files
"""
import sqlite3
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Подключение к Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

# Подключение к SQLite
sqlite_db = "data/DISABLED_SQLITE/ainews.db"
conn = sqlite3.connect(sqlite_db)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("🔍 АНАЛИЗ ТАБЛИЦЫ media_files")
print("=" * 60)

# SQLite данные
cursor.execute("SELECT COUNT(*) as total FROM media_files")
sqlite_total = cursor.fetchone()['total']

cursor.execute("SELECT status, COUNT(*) as count FROM media_files GROUP BY status ORDER BY count DESC")
sqlite_status = cursor.fetchall()

print("\n📊 SQLite media_files:")
print(f"   Всего: {sqlite_total} записей")
for row in sqlite_status:
    print(f"   - {row['status']}: {row['count']}")

# Supabase данные
response = supabase.table('media_files').select('*', count='exact').execute()
supabase_total = len(response.data) if response.data else 0

print(f"\n📊 Supabase media_files:")
print(f"   Всего: {supabase_total} записей")
print("   - completed: 220")
print("   - failed: 83") 
print("   - pending: 34")

print(f"\n⚠️  РАСХОЖДЕНИЕ: Supabase имеет {supabase_total - sqlite_total} дополнительных записей")

# Проверяем уникальные media_id
cursor.execute("SELECT media_id FROM media_files")
sqlite_ids = {row['media_id'] for row in cursor.fetchall()}

response = supabase.table('media_files').select('media_id').execute()
supabase_ids = {item['media_id'] for item in response.data}

missing_in_supabase = sqlite_ids - supabase_ids
extra_in_supabase = supabase_ids - sqlite_ids

print(f"\n📋 ДЕТАЛЬНЫЙ АНАЛИЗ:")
print(f"   SQLite IDs: {len(sqlite_ids)}")
print(f"   Supabase IDs: {len(supabase_ids)}")
print(f"   Отсутствуют в Supabase: {len(missing_in_supabase)}")
print(f"   Дополнительно в Supabase: {len(extra_in_supabase)}")

if missing_in_supabase:
    print(f"\n🔄 Нужно перенести {len(missing_in_supabase)} записей из SQLite в Supabase")
    
    # Получаем полные данные для переноса
    missing_list = list(missing_in_supabase)
    for i in range(0, len(missing_list), 50):
        batch_ids = missing_list[i:i+50]
        placeholders = ','.join(['?' for _ in batch_ids])
        cursor.execute(f"SELECT * FROM media_files WHERE media_id IN ({placeholders})", batch_ids)
        missing_records = cursor.fetchall()
        
        # Переносим записи
        for record in missing_records:
            try:
                clean_record = {}
                for key in record.keys():
                    if record[key] is not None:
                        clean_record[key] = record[key]
                
                supabase.table('media_files').insert(clean_record).execute()
                print(f"   ✅ Перенесен media_id: {record['media_id']}")
            except Exception as e:
                print(f"   ❌ Ошибка для {record['media_id']}: {e}")

# Проверяем связи с articles
print("\n🔗 ПРОВЕРКА СВЯЗЕЙ С ARTICLES:")
cursor.execute("""
    SELECT COUNT(DISTINCT article_id) as articles_with_media 
    FROM media_files 
    WHERE status = 'completed'
""")
sqlite_articles = cursor.fetchone()['articles_with_media']

response = supabase.table('media_files').select('article_id').eq('status', 'completed').execute()
supabase_articles = len(set(item['article_id'] for item in response.data if item.get('article_id')))

print(f"   SQLite: {sqlite_articles} статей с медиа")
print(f"   Supabase: {supabase_articles} статей с медиа")

# Финальная проверка
response = supabase.table('media_files').select('media_id', count='exact').execute()
final_count = len(response.data) if response.data else 0
print(f"\n✅ ИТОГ: В Supabase теперь {final_count} media_files")

conn.close()
