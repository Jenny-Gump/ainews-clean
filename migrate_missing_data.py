#!/usr/bin/env python3
"""
Скрипт для переноса недостающих данных из SQLite в Supabase
"""
import sqlite3
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

# Загружаем переменные окружения
load_dotenv()

# Подключение к Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

# Путь к SQLite базе
sqlite_db = "data/DISABLED_SQLITE/ainews.db"

print(f"🔄 Начинаем миграцию из SQLite в Supabase...")
print(f"SQLite DB: {sqlite_db}")
print(f"Supabase URL: {url}")

# Подключаемся к SQLite
conn = sqlite3.connect(sqlite_db)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. Получаем все статьи из SQLite
cursor.execute("SELECT * FROM articles ORDER BY created_at DESC")
sqlite_articles = cursor.fetchall()
print(f"\n📊 Найдено в SQLite: {len(sqlite_articles)} статей")

# Получаем существующие статьи из Supabase
response = supabase.table('articles').select('article_id').execute()
existing_ids = {item['article_id'] for item in response.data}
print(f"📊 Уже есть в Supabase: {len(existing_ids)} статей")

# Находим недостающие статьи
missing_articles = []
for row in sqlite_articles:
    if row['article_id'] not in existing_ids:
        missing_articles.append(dict(row))

print(f"❌ Недостает в Supabase: {len(missing_articles)} статей")

if missing_articles:
    print(f"\n🚀 Переносим {len(missing_articles)} недостающих статей...")
    
    # Переносим по батчам
    batch_size = 50
    for i in range(0, len(missing_articles), batch_size):
        batch = missing_articles[i:i+batch_size]
        
        # Очищаем None значения и конвертируем datetime
        clean_batch = []
        for article in batch:
            clean_article = {}
            for key, value in article.items():
                if value is not None:
                    # Конвертируем datetime в строку для JSON
                    if isinstance(value, datetime):
                        clean_article[key] = value.isoformat()
                    else:
                        clean_article[key] = value
                elif key in ['created_at', 'updated_at', 'last_checked']:
                    # Для временных полей используем текущее время если пусто
                    clean_article[key] = datetime.now().isoformat()
            clean_batch.append(clean_article)
        
        try:
            response = supabase.table('articles').insert(clean_batch).execute()
            print(f"✅ Перенесено {len(clean_batch)} статей (батч {i//batch_size + 1})")
        except Exception as e:
            print(f"❌ Ошибка при переносе батча: {e}")
            # Пробуем по одной
            for article in clean_batch:
                try:
                    supabase.table('articles').insert(article).execute()
                    print(f"  ✅ Перенесена статья {article.get('article_id')}")
                except Exception as e2:
                    print(f"  ❌ Не удалось перенести {article.get('article_id')}: {e2}")

# 2. Проверяем таблицу related_links
try:
    cursor.execute("SELECT * FROM related_links")
    related_links = cursor.fetchall()
    print(f"\n📊 Найдено в SQLite related_links: {len(related_links)} записей")
    
    if related_links:
        # Проверяем существует ли таблица в Supabase
        try:
            response = supabase.table('related_links').select('*').limit(1).execute()
            
            # Переносим данные
            for link in related_links:
                try:
                    supabase.table('related_links').insert(dict(link)).execute()
                    print(f"✅ Перенесена related_link")
                except:
                    pass  # Возможно уже существует
        except:
            print("⚠️ Таблица related_links не существует в Supabase")
except:
    print("⚠️ Таблица related_links не найдена в SQLite")

# 3. Синхронизируем tracked_articles
try:
    cursor.execute("SELECT * FROM tracked_articles")
    sqlite_tracked = cursor.fetchall()
    response = supabase.table('tracked_articles').select('article_id').execute()
    existing_tracked = {item['article_id'] for item in response.data}
    
    missing_tracked = [dict(row) for row in sqlite_tracked if row['article_id'] not in existing_tracked]
    if missing_tracked:
        print(f"\n📊 Переносим {len(missing_tracked)} tracked_articles...")
        for article in missing_tracked:
            try:
                supabase.table('tracked_articles').insert(article).execute()
            except:
                pass
except Exception as e:
    print(f"⚠️ Ошибка с tracked_articles: {e}")

# 4. Синхронизируем pipeline_operations
try:
    cursor.execute("SELECT * FROM pipeline_operations")
    sqlite_ops = cursor.fetchall()
    response = supabase.table('pipeline_operations').select('operation_id').execute()
    existing_ops = {item['operation_id'] for item in response.data}
    
    missing_ops = [dict(row) for row in sqlite_ops if row['operation_id'] not in existing_ops]
    if missing_ops:
        print(f"\n📊 Переносим {len(missing_ops)} pipeline_operations...")
        for op in missing_ops:
            try:
                supabase.table('pipeline_operations').insert(op).execute()
            except:
                pass
except Exception as e:
    print(f"⚠️ Ошибка с pipeline_operations: {e}")

# Закрываем соединение
conn.close()

# Финальная проверка
response = supabase.table('articles').select('article_id', count='exact').execute()
final_count = len(response.data) if response.data else 0
print(f"\n✅ ГОТОВО! Теперь в Supabase: {final_count} статей")
