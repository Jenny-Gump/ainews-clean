#!/usr/bin/env python3
"""
Check Meta Fields Directly
Прямая проверка мета-полей WordPress
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config

def check_meta_fields():
    """Прямая проверка мета-полей"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('📋 Проверка мета-полей Yoast')
    print('=' * 50)
    
    # Проверяем несколько категорий
    test_categories = {
        'LLM': 3,
        'Машинное обучение': 4,
        'Техника': 5,
        'Digital': 6
    }
    
    found_data = 0
    
    for cat_name, cat_id in test_categories.items():
        print(f'\n📂 {cat_name} (ID: {cat_id}):')
        
        # Получаем все данные категории
        response = requests.get(
            f'{config.wordpress_api_url}/categories/{cat_id}',
            auth=auth,
            params={'context': 'edit'}  # Полный контекст
        )
        
        if response.status_code == 200:
            data = response.json()
            meta = data.get('meta', {})
            
            if meta:
                # Ищем Yoast мета-поля
                yoast_title = meta.get('_yoast_wpseo_title')
                yoast_desc = meta.get('_yoast_wpseo_metadesc')
                yoast_keyword = meta.get('_yoast_wpseo_focuskw')
                
                if yoast_title:
                    print(f'   ✅ Title: {yoast_title}')
                    found_data += 1
                else:
                    print(f'   ❌ Title: Нет данных')
                    
                if yoast_desc:
                    print(f'   ✅ Description: {yoast_desc[:60]}...')
                else:
                    print(f'   ❌ Description: Нет данных')
                    
                if yoast_keyword:
                    print(f'   ✅ Keyword: {yoast_keyword}')
                else:
                    print(f'   ❌ Keyword: Нет данных')
                
                # Показать все Yoast поля
                yoast_fields = {k: v for k, v in meta.items() if '_yoast_wpseo_' in k and v}
                if yoast_fields:
                    print(f'   📊 Всего Yoast полей: {len(yoast_fields)}')
                else:
                    print(f'   ⚠️ Yoast поля пустые')
            else:
                print('   ❌ Мета-поля не найдены')
        else:
            print(f'   ❌ Ошибка получения данных: {response.status_code}')
    
    print(f'\n📊 Результат:')
    print(f'   ✅ Категорий с данными в мета-полях: {found_data}/{len(test_categories)}')
    
    return found_data > 0

def test_db_plugin_status():
    """Проверка статуса БД плагина"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🔧 Проверка БД плагина:')
    
    response = requests.get('https://ailynx.ru/wp-json/yoast-db/v1/check-tables', auth=auth)
    
    if response.status_code == 200:
        data = response.json()
        print('✅ БД плагин работает')
        
        yoast_tables = data.get('yoast_tables', {})
        for table, status in yoast_tables.items():
            if isinstance(status, bool):
                print(f'   {table}: {"✅" if status else "❌"}')
            elif table.endswith('_count'):
                print(f'   {table}: {status}')
        
        termmeta_yoast = data.get('termmeta_yoast', [])
        print(f'   Termmeta Yoast записей: {len(termmeta_yoast)}')
        
        for record in termmeta_yoast:
            print(f'     {record.get("meta_key")}: {record.get("count")} записей')
    else:
        print('❌ БД плагин не отвечает')

def main():
    print('🔍 Диагностика мета-полей и плагинов')
    print('=' * 60)
    
    has_meta_data = check_meta_fields()
    test_db_plugin_status()
    
    print('\n📋 Сводка:')
    if has_meta_data:
        print('✅ Данные сохранены в WordPress мета-поля')
        print('⏳ Yoast требует переиндексацию для отображения')
        print('\n🎯 Инструкции по переиндексации:')
        print('1. https://ailynx.ru/wp-admin/admin.php?page=wpseo_tools')
        print('2. Найдите раздел "SEO Data"')
        print('3. Нажмите "Start SEO data optimization" или "Reindex"')
    else:
        print('❌ Данные не найдены в мета-полях')
        print('💡 Нужно повторить обновление')

if __name__ == "__main__":
    main()