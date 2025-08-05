#!/usr/bin/env python3
"""
Restore Original Category Titles
Восстановление оригинальных названий категорий без лишних AI приставок
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config
import time

def restore_original_titles():
    """Восстановление оригинальных названий категорий"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('🔄 Восстановление оригинальных названий категорий')
    print('=' * 60)
    
    # Оригинальные простые названия категорий
    ORIGINAL_TITLES = {
        2: "Новости",
        3: "LLM", 
        4: "Машинное обучение",
        5: "Техника",
        6: "Digital",
        7: "Финансы",
        8: "Наука", 
        9: "Обучение",
        10: "Другие индустрии",
        11: "Люди"
    }
    
    success_count = 0
    
    for cat_id, original_name in ORIGINAL_TITLES.items():
        print(f'\n🔄 Восстанавливаем категорию {cat_id}: {original_name}')
        
        try:
            # Обновляем только название
            update_data = {
                'name': original_name
            }
            
            response = requests.post(
                f'{config.wordpress_api_url}/categories/{cat_id}',
                json=update_data,
                auth=auth
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f'✅ Успешно: {result.get("name")}')
                success_count += 1
            else:
                print(f'❌ Ошибка {response.status_code}: {response.text[:100]}')
                
            time.sleep(0.2)
            
        except Exception as e:
            print(f'❌ Исключение: {e}')
    
    print(f'\n📊 Результат: {success_count}/{len(ORIGINAL_TITLES)} категорий восстановлено')
    return success_count > 0

def verify_restored_titles():
    """Проверка восстановленных названий"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🔍 Проверка восстановленных названий')
    print('=' * 50)
    
    response = requests.get(f'{config.wordpress_api_url}/categories?per_page=100', auth=auth)
    
    if response.status_code == 200:
        categories = response.json()
        
        # Фильтруем только наши категории (исключаем родительскую "Новости" если она есть)
        our_categories = [cat for cat in categories if cat.get('parent') == 1 or cat.get('id') in [2,3,4,5,6,7,8,9,10,11]]
        
        print('📂 Текущие названия категорий:')
        for cat in sorted(our_categories, key=lambda x: x['id']):
            print(f'   ID {cat["id"]}: {cat["name"]} (slug: {cat["slug"]})')
        
        return True
    else:
        print(f'❌ Ошибка получения категорий: {response.status_code}')
        return False

def main():
    print('🔧 Восстановление оригинальных названий категорий')
    print('=' * 60)
    
    # Восстанавливаем оригинальные названия
    if restore_original_titles():
        print('\n✅ Названия категорий восстановлены к оригинальным')
        
        # Проверяем результат
        verify_restored_titles()
        
        print('\n💡 Что было сделано:')
        print('• Убраны лишние "AI" приставки из названий')
        print('• Восстановлены простые и понятные названия')
        print('• Yoast SEO поля остались без изменений')
        
        print('\n✅ Теперь у вас чистые названия категорий:')
        print('   • LLM')
        print('   • Машинное обучение')
        print('   • Техника')
        print('   • Digital')
        print('   • Финансы')
        print('   • Наука')
        print('   • Обучение')
        print('   • Другие индустрии')
        print('   • Люди')
        print('   • Новости')
        
    else:
        print('\n❌ Произошла ошибка при восстановлении названий')

if __name__ == "__main__":
    main()