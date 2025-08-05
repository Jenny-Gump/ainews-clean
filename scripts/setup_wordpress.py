#!/usr/bin/env python3
"""
WordPress Setup Helper
Помощник настройки WordPress интеграции
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.config import Config
from core.database import Database
from services.wordpress_publisher import WordPressPublisher
from app_logging import get_logger

logger = get_logger('wordpress_setup')


def check_configuration():
    """Проверка конфигурации WordPress"""
    config = Config()
    
    print("\n=== Проверка конфигурации WordPress ===\n")
    
    # Check API keys
    checks = {
        "DeepSeek API Key": bool(config.openai_api_key),
        "WordPress API URL": bool(config.wordpress_api_url),
        "WordPress Username": bool(config.wordpress_username),
        "WordPress App Password": bool(config.wordpress_app_password),
    }
    
    all_ok = True
    for name, status in checks.items():
        status_text = "✅ OK" if status else "❌ Отсутствует"
        print(f"{name}: {status_text}")
        if not status:
            all_ok = False
    
    if not all_ok:
        print("\n❌ Конфигурация неполная!")
        print("\nДобавьте недостающие параметры в файл .env:")
        print("OPENAI_API_KEY=sk-...")
        print("WORDPRESS_API_URL=https://your-site.com/wp-json/wp/v2")
        print("WORDPRESS_USERNAME=your_username")
        print("WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx")
        return False
    
    print("\n✅ Конфигурация в порядке!")
    return True


def test_wordpress_connection():
    """Тест подключения к WordPress API"""
    config = Config()
    
    if not all([config.wordpress_api_url, config.wordpress_username, config.wordpress_app_password]):
        print("\n❌ WordPress API не настроен")
        return False
    
    print("\n=== Тест подключения к WordPress ===\n")
    
    try:
        import requests
        from requests.auth import HTTPBasicAuth
        
        # Test categories endpoint
        url = f"{config.wordpress_api_url}/categories"
        auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
        
        response = requests.get(url, auth=auth, timeout=10)
        
        if response.status_code == 200:
            categories = response.json()
            print(f"✅ Подключение успешно!")
            print(f"Найдено категорий: {len(categories)}")
            
            # Show existing categories
            if categories:
                print("\nСуществующие категории:")
                for cat in categories[:10]:  # Show first 10
                    print(f"  - {cat['name']} (ID: {cat['id']})")
                
                if len(categories) > 10:
                    print(f"  ... и еще {len(categories) - 10}")
            
            return True
        else:
            print(f"❌ Ошибка подключения: {response.status_code}")
            print(f"Ответ: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return False


def check_articles_status():
    """Проверка статуса статей"""
    db = Database()
    
    print("\n=== Статистика статей ===\n")
    
    with db.get_connection() as conn:
        # Total articles
        total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        print(f"Всего статей: {total}")
        
        # Completed articles
        completed = conn.execute(
            "SELECT COUNT(*) FROM articles WHERE content_status = 'completed'"
        ).fetchone()[0]
        print(f"Обработанных: {completed}")
        
        # WordPress articles
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN translation_status = 'translated' THEN 1 ELSE 0 END) as translated,
                SUM(CASE WHEN translation_status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN published_to_wp = 1 THEN 1 ELSE 0 END) as published
            FROM wordpress_articles
        """)
        wp_stats = cursor.fetchone()
        
        print(f"\nWordPress статьи:")
        print(f"  Всего: {wp_stats[0]}")
        print(f"  Переведено: {wp_stats[1]}")
        print(f"  Ошибки перевода: {wp_stats[2]}")
        print(f"  Опубликовано: {wp_stats[3]}")
        
        # Ready to translate
        ready_to_translate = completed - wp_stats[0]
        print(f"\nГотово к переводу: {ready_to_translate}")
        
        # Ready to publish
        ready_to_publish = wp_stats[1] - wp_stats[3]
        print(f"Готово к публикации: {ready_to_publish}")


def create_test_categories():
    """Создание тестовых категорий в WordPress"""
    config = Config()
    
    if not all([config.wordpress_api_url, config.wordpress_username, config.wordpress_app_password]):
        print("\n❌ WordPress API не настроен")
        return
    
    print("\n=== Создание категорий ===\n")
    
    required_categories = [
        "LLM", "Машинное обучение", "Техника", "Digital", 
        "Люди", "Финансы", "Наука", "Обучение", "Другие индустрии"
    ]
    
    try:
        import requests
        from requests.auth import HTTPBasicAuth
        
        auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
        
        # Get existing categories
        url = f"{config.wordpress_api_url}/categories"
        response = requests.get(url, auth=auth, params={'per_page': 100})
        
        if response.status_code != 200:
            print(f"❌ Не удалось получить категории: {response.status_code}")
            return
        
        existing = {cat['name']: cat['id'] for cat in response.json()}
        
        # Create missing categories
        for cat_name in required_categories:
            if cat_name in existing:
                print(f"✅ {cat_name} - уже существует (ID: {existing[cat_name]})")
            else:
                # Create category
                data = {
                    'name': cat_name,
                    'slug': cat_name.lower().replace(' ', '-')
                }
                
                response = requests.post(url, json=data, auth=auth)
                
                if response.status_code == 201:
                    new_cat = response.json()
                    print(f"✅ {cat_name} - создана (ID: {new_cat['id']})")
                else:
                    print(f"❌ {cat_name} - ошибка создания: {response.text[:100]}")
                    
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")


def main():
    """Главная функция"""
    print("🚀 WordPress Setup Helper")
    print("=" * 50)
    
    # Check configuration
    if not check_configuration():
        return
    
    # Check database status
    check_articles_status()
    
    # Test WordPress connection
    if test_wordpress_connection():
        print("\n" + "=" * 50)
        print("\nХотите создать необходимые категории? (y/n): ", end='')
        if input().lower() == 'y':
            create_test_categories()
    
    print("\n" + "=" * 50)
    print("\n✅ Проверка завершена!")
    print("\nДальнейшие шаги:")
    print("1. Подготовка статей: python core/main.py --wordpress-prepare --limit 5")
    print("2. Публикация: python core/main.py --wordpress-publish --limit 5")


if __name__ == "__main__":
    main()