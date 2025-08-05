#!/usr/bin/env python3
"""
Fix Categories Titles - Return to Normal
Исправление заголовков категорий - возврат к нормальным названиям
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config
import time

def restore_normal_titles():
    """Восстановление нормальных заголовков категорий"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('🔄 Восстановление нормальных заголовков категорий')
    print('=' * 60)
    
    # Нормальные названия категорий
    NORMAL_TITLES = {
        2: "AI Новости",
        3: "LLM", 
        4: "Машинное обучение",
        5: "AI Техника",
        6: "Digital AI",
        7: "AI в Финансах",
        8: "AI в Науке", 
        9: "AI Образование",
        10: "AI в Индустриях",
        11: "Люди в AI"
    }
    
    success_count = 0
    
    for cat_id, normal_name in NORMAL_TITLES.items():
        print(f'\n🔄 Восстанавливаем категорию {cat_id}: {normal_name}')
        
        try:
            # Обновляем только название, оставляем остальное
            update_data = {
                'name': normal_name
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
    
    print(f'\n📊 Результат: {success_count}/{len(NORMAL_TITLES)} категорий восстановлено')
    return success_count > 0

def check_yoast_fields_real():
    """Реальная проверка Yoast полей"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🔍 Реальная проверка Yoast полей')
    print('=' * 50)
    
    # Проверяем несколько категорий
    test_categories = [3, 4, 5, 6]  # LLM, Машинное обучение, AI Техника, Digital AI
    
    for cat_id in test_categories:
        print(f'\n📂 Категория ID {cat_id}:')
        
        try:
            response = requests.get(f'{config.wordpress_api_url}/categories/{cat_id}', auth=auth)
            
            if response.status_code == 200:
                data = response.json()
                
                print(f'   Название: {data.get("name")}')
                print(f'   Slug: {data.get("slug")}')
                
                # Проверяем Yoast поля
                yoast_title = data.get('yoast_title')
                yoast_desc = data.get('yoast_description')
                yoast_keyword = data.get('yoast_keyword')
                
                if yoast_title:
                    print(f'   ✅ Yoast Title: {yoast_title}')
                else:
                    print(f'   ❌ Yoast Title: НЕТ')
                
                if yoast_desc:
                    print(f'   ✅ Yoast Description: {yoast_desc[:60]}...')
                else:
                    print(f'   ❌ Yoast Description: НЕТ')
                
                if yoast_keyword:
                    print(f'   ✅ Yoast Keyword: {yoast_keyword}')
                else:
                    print(f'   ❌ Yoast Keyword: НЕТ')
                
                # Проверяем стандартное описание WordPress
                wp_description = data.get('description', '')
                if wp_description:
                    print(f'   📝 WP Description: {len(wp_description)} символов')
                else:
                    print(f'   📝 WP Description: НЕТ')
                    
            else:
                print(f'   ❌ Ошибка получения: {response.status_code}')
                
        except Exception as e:
            print(f'   ❌ Исключение: {e}')

def clear_yoast_fields():
    """Очистка Yoast полей для тестирования"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🧹 Очистка Yoast полей для тестирования')
    print('=' * 50)
    
    test_category = 4  # Машинное обучение
    
    clear_data = {
        'yoast_title': '',
        'yoast_description': '',
        'yoast_keyword': ''
    }
    
    try:
        response = requests.post(
            f'{config.wordpress_api_url}/categories/{test_category}',
            json=clear_data,
            auth=auth
        )
        
        if response.status_code == 200:
            print('✅ Yoast поля очищены для тестирования')
            return True
        else:
            print(f'❌ Ошибка очистки: {response.status_code}')
            return False
            
    except Exception as e:
        print(f'❌ Исключение: {e}')
        return False

def test_simple_yoast_update():
    """Простой тест обновления Yoast полей"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🧪 Простой тест обновления Yoast')
    print('=' * 40)
    
    test_category = 4  # Машинное обучение
    
    # Простые тестовые данные
    test_data = {
        'yoast_title': 'Тест заголовок ML',
        'yoast_description': 'Тест описание для машинного обучения',
        'yoast_keyword': 'ML тест'
    }
    
    print(f'📤 Отправляем тестовые данные для категории {test_category}...')
    
    try:
        response = requests.post(
            f'{config.wordpress_api_url}/categories/{test_category}',
            json=test_data,
            auth=auth
        )
        
        if response.status_code == 200:
            result = response.json()
            print('✅ Запрос успешен, проверяем результат:')
            
            # Проверяем что вернулось
            returned_title = result.get('yoast_title')
            returned_desc = result.get('yoast_description')
            returned_keyword = result.get('yoast_keyword')
            
            print(f'   Title: "{returned_title}" (ожидали: "{test_data["yoast_title"]}")')
            print(f'   Description: "{returned_desc}" (ожидали: "{test_data["yoast_description"]}")')
            print(f'   Keyword: "{returned_keyword}" (ожидали: "{test_data["yoast_keyword"]}")')
            
            # Проверяем совпадение
            title_ok = returned_title == test_data['yoast_title']
            desc_ok = returned_desc == test_data['yoast_description']
            keyword_ok = returned_keyword == test_data['yoast_keyword']
            
            if title_ok and desc_ok and keyword_ok:
                print('🎉 ВСЕ РАБОТАЕТ! Yoast поля обновляются корректно')
                return True
            else:
                print('❌ НЕ РАБОТАЕТ! Yoast поля не обновляются')
                return False
        else:
            print(f'❌ Ошибка запроса: {response.status_code}')
            print(f'   Ответ: {response.text[:200]}')
            return False
            
    except Exception as e:
        print(f'❌ Исключение: {e}')
        return False

def main():
    print('🔧 Исправление категорий и тестирование Yoast')
    print('=' * 60)
    
    # 1. Восстанавливаем нормальные заголовки
    if restore_normal_titles():
        print('\n✅ Заголовки восстановлены')
    else:
        print('\n❌ Ошибка восстановления заголовков')
    
    # 2. Проверяем текущее состояние
    check_yoast_fields_real()
    
    # 3. Тестируем работу Yoast полей
    print('\n' + '='*60)
    if test_simple_yoast_update():
        print('\n🎉 РЕЗУЛЬТАТ: Yoast REST API Extension работает корректно!')
        print('💡 Проблема была в том, что мета-описания нужно проверять:')
        print('   1. В админке WordPress: /wp-admin/edit-tags.php?taxonomy=category')
        print('   2. В исходном коде страниц (когда сайт выйдет из maintenance)')
        print('   3. Не все мета-теги видны сразу, нужна переиндексация Yoast')
    else:
        print('\n❌ РЕЗУЛЬТАТ: Yoast REST API Extension НЕ работает')
        print('💡 Нужно проверить:')
        print('   1. Активирован ли плагин yoast-rest-api-extension.php')
        print('   2. Активирован ли Yoast SEO')
        print('   3. Есть ли права на изменение категорий')

if __name__ == "__main__":
    main()