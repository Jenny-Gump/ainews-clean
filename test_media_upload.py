#!/usr/bin/env python3
"""
Тест загрузки медиафайлов в Supabase
"""
import asyncio
from core.db_config import DatabaseConfig
from services.media_processor import ExtractMediaDownloaderPlaywright

async def test_media_upload():
    """Тестирует загрузку одного медиафайла"""
    print("🧪 Тестируем загрузку медиафайлов в Supabase...")
    
    # Получаем БД
    db = DatabaseConfig.get_database()
    print(f"✅ Подключено к: {type(db).__name__}")
    
    # Тестируем метод execute()
    test_media_id = "test_001"
    test_params = (
        "/test/path.jpg",  # file_path
        12345,             # file_size
        "image",           # type
        800,               # width
        600,               # height
        test_media_id      # media_id
    )
    
    try:
        # Сначала создадим тестовую запись
        from supabase import create_client
        import os
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        client = create_client(url, key)
        
        # Создаем тестовую запись
        client.table('media_files').insert({
            'media_id': test_media_id,
            'article_id': 'test_article',
            'url': 'https://example.com/test.jpg',
            'status': 'pending'
        }).execute()
        print(f"✅ Создан тестовый media_file: {test_media_id}")
        
        # Тестируем execute() метод
        with db.get_connection() as conn:
            result = conn.execute("""
                UPDATE media_files SET
                    file_path = ?,
                    file_size = ?,
                    type = ?,
                    width = ?,
                    height = ?,
                    status = 'completed'
                WHERE media_id = ?
            """, test_params)
        
        print(f"✅ Метод execute() работает: {result}")
        
        # Проверяем обновление
        updated = client.table('media_files').select('*').eq('media_id', test_media_id).execute()
        if updated.data and updated.data[0]['status'] == 'completed':
            print(f"✅ Медиафайл успешно обновлен в Supabase!")
            print(f"   Статус: {updated.data[0]['status']}")
            print(f"   Размер: {updated.data[0].get('file_size')} байт")
            print(f"   Тип: {updated.data[0].get('type')}")
        
        # Удаляем тестовую запись
        client.table('media_files').delete().eq('media_id', test_media_id).execute()
        print(f"🗑️ Тестовая запись удалена")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_media_upload())
