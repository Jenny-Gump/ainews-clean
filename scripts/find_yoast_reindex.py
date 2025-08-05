#!/usr/bin/env python3
"""
Find Yoast Reindex Options
Поиск опций переиндексации Yoast
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config

def find_yoast_endpoints():
    """Поиск доступных Yoast эндпоинтов"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('🔍 Поиск Yoast эндпоинтов...')
    
    # Проверяем доступные маршруты Yoast
    yoast_endpoints = [
        '/yoast/v1',
        '/yoast/v1/indexing',
        '/yoast/v1/indexing/prepare',
        '/yoast/v1/indexing/terms',
        '/yoast/v1/indexing/posts',  
        '/yoast/v1/indexing/complete',
        '/yoast/v1/settings',
        '/yoast/v1/workouts'
    ]
    
    for endpoint in yoast_endpoints:
        try:
            response = requests.get(f'https://ailynx.ru/wp-json{endpoint}', auth=auth)
            print(f'   {endpoint}: {response.status_code}')
            if response.status_code == 200:
                print(f'      ✅ Доступен')
            time.sleep(0.2)
        except Exception as e:
            print(f'   {endpoint}: Ошибка - {e}')

def try_yoast_indexing():
    """Попытка запуска индексации Yoast"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🚀 Попытка запуска индексации Yoast...')
    
    # Последовательность для индексации
    indexing_steps = [
        ('prepare', '/yoast/v1/indexing/prepare'),
        ('terms', '/yoast/v1/indexing/terms'),
        ('complete', '/yoast/v1/indexing/complete')
    ]
    
    for step_name, endpoint in indexing_steps:
        print(f'\n🔄 Шаг: {step_name}')
        try:
            response = requests.post(f'https://ailynx.ru/wp-json{endpoint}', auth=auth)
            print(f'   Статус: {response.status_code}')
            
            if response.status_code == 200:
                data = response.json()
                print(f'   ✅ {step_name}: {data}')
            else:
                print(f'   ❌ {step_name}: {response.text[:100]}')
                
            time.sleep(1)
        except Exception as e:
            print(f'   ❌ {step_name}: Ошибка - {e}')

def show_manual_alternatives():
    """Показать альтернативные способы"""
    print('\n💡 Альтернативные способы переиндексации:')
    print()
    print('1. 📋 **Через меню категорий:**')
    print('   https://ailynx.ru/wp-admin/edit-tags.php?taxonomy=category')
    print('   - Откройте любую категорию')
    print('   - Внизу найдите блок "Yoast SEO"')
    print('   - Если поля пустые - вставьте данные вручную')
    print('   - Нажмите "Обновить"')
    print()
    print('2. 🔧 **Поиск в админке Yoast:**')
    print('   Попробуйте эти разделы:')
    print('   - https://ailynx.ru/wp-admin/admin.php?page=wpseo_dashboard')
    print('   - https://ailynx.ru/wp-admin/admin.php?page=wpseo_tools') 
    print('   - https://ailynx.ru/wp-admin/admin.php?page=wpseo_search_console')
    print('   - https://ailynx.ru/wp-admin/admin.php?page=wpseo_workouts')
    print()
    print('3. 🔄 **Принудительное обновление:**')
    print('   - Откройте: https://ailynx.ru/wp-admin/edit-tags.php?taxonomy=category&tag_ID=4')
    print('   - Найдите блок "Yoast SEO" внизу страницы')
    print('   - Заполните поля:')
    print('     SEO title: "Машинное обучение - ML новости и исследования | AI Lynx"')
    print('     Meta description: "Актуальные новости машинного обучения: алгоритмы, нейросети, исследования."')
    print('     Focus keyword: "машинное обучение"')
    print('   - Нажмите "Обновить"')

def main():
    print('🔍 Поиск опций переиндексации Yoast')
    print('=' * 60)
    
    import time
    
    find_yoast_endpoints()
    try_yoast_indexing()
    show_manual_alternatives()
    
    print('\n📋 Рекомендации:')
    print('1. Попробуйте ручное обновление одной категории')
    print('2. Если сработает - остальные подтянутся автоматически')
    print('3. Или используйте массовый ручной ввод из предыдущего скрипта')

if __name__ == "__main__":
    main()