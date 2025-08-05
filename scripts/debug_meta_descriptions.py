#!/usr/bin/env python3
"""
Debug Meta Descriptions - Real Check
Отладка мета-описаний - реальная проверка
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config
import time

def check_current_yoast_data():
    """Проверка текущих Yoast данных"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('🔍 Проверка текущих Yoast данных')
    print('=' * 50)
    
    # Проверяем несколько категорий
    test_categories = [3, 4, 5]  # LLM, Машинное обучение, Техника
    
    for cat_id in test_categories:
        print(f'\n📂 Категория ID {cat_id}:')
        
        try:
            response = requests.get(f'{config.wordpress_api_url}/categories/{cat_id}', auth=auth)
            
            if response.status_code == 200:
                data = response.json()
                
                print(f'   Название: {data.get("name")}')
                
                # Yoast поля через наш плагин
                yoast_title = data.get('yoast_title', '')
                yoast_desc = data.get('yoast_description', '')
                yoast_keyword = data.get('yoast_keyword', '')
                
                print(f'   🏷️  Yoast Title: {yoast_title[:60]}{"..." if len(yoast_title) > 60 else ""}')
                print(f'   📝 Yoast Description: {yoast_desc[:80]}{"..." if len(yoast_desc) > 80 else ""}')
                print(f'   🔑 Yoast Keyword: {yoast_keyword}')
                
                # Проверяем yoast_head (то что Yoast выводит)
                yoast_head = data.get('yoast_head', '')
                yoast_head_json = data.get('yoast_head_json', {})
                
                if yoast_head_json:
                    actual_title = yoast_head_json.get('title', '')
                    actual_desc = yoast_head_json.get('description', '')
                    
                    print(f'   📊 Yoast Head Title: {actual_title}')
                    print(f'   📊 Yoast Head Description: {actual_desc}')
                    
                    # Сравниваем
                    if yoast_title and yoast_title in actual_title:
                        print('   ✅ Title синхронизирован')
                    else:
                        print('   ❌ Title НЕ синхронизирован')
                    
                    if yoast_desc and yoast_desc == actual_desc:
                        print('   ✅ Description синхронизирован') 
                    else:
                        print('   ❌ Description НЕ синхронизирован')
                else:
                    print('   ❌ yoast_head_json пуст')
                    
            else:
                print(f'   ❌ Ошибка: {response.status_code}')
                
        except Exception as e:
            print(f'   ❌ Исключение: {e}')

def force_yoast_refresh():
    """Принудительное обновление Yoast данных"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🔄 Принудительное обновление Yoast данных')
    print('=' * 50)
    
    # Попробуем обновить одну категорию с принудительной очисткой кэша
    test_category = 4  # Машинное обучение
    
    # Текущие данные
    current_response = requests.get(f'{config.wordpress_api_url}/categories/{test_category}', auth=auth)
    if current_response.status_code == 200:
        current_data = current_response.json()
        current_yoast_desc = current_data.get('yoast_description', '')
        
        print(f'📝 Текущее Yoast описание: {current_yoast_desc[:80]}...')
        
        # Попробуем перезаписать те же данные
        refresh_data = {
            'yoast_title': current_data.get('yoast_title', ''),
            'yoast_description': current_yoast_desc,
            'yoast_keyword': current_data.get('yoast_keyword', '')
        }
        
        print('🔄 Перезаписываем те же данные для принуждения к обновлению...')
        
        update_response = requests.post(
            f'{config.wordpress_api_url}/categories/{test_category}',
            json=refresh_data,
            auth=auth
        )
        
        if update_response.status_code == 200:
            print('✅ Данные перезаписаны')
            
            # Ждем и проверяем
            time.sleep(2)
            
            check_response = requests.get(f'{config.wordpress_api_url}/categories/{test_category}', auth=auth)
            if check_response.status_code == 200:
                check_data = check_response.json()
                yoast_head_json = check_data.get('yoast_head_json', {})
                
                if yoast_head_json:
                    actual_desc = yoast_head_json.get('description', '')
                    print(f'📊 Yoast Head Description после обновления: {actual_desc}')
                    
                    if current_yoast_desc == actual_desc:
                        print('🎉 УСПЕХ! Мета-описание синхронизировано!')
                        return True
                    else:
                        print('❌ Мета-описание все еще не синхронизировано')
                else:
                    print('❌ yoast_head_json все еще пуст')
        else:
            print(f'❌ Ошибка обновления: {update_response.status_code}')
    
    return False

def check_yoast_plugin_status():
    """Проверка статуса плагина Yoast SEO"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🔍 Проверка плагинов Yoast')
    print('=' * 30)
    
    # Попробуем обратиться к Yoast API endpoints
    yoast_endpoints = [
        '/yoast/v1',
        '/yoast/v1/workouts'
    ]
    
    for endpoint in yoast_endpoints:
        try:
            response = requests.get(f'https://ailynx.ru/wp-json{endpoint}', auth=auth)
            print(f'   {endpoint}: {response.status_code}')
            if response.status_code == 200:
                print(f'      ✅ Yoast API доступен')
        except Exception as e:
            print(f'   {endpoint}: Ошибка - {e}')

def test_manual_meta_fix():
    """Тест ручного исправления мета-описаний"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🛠️ Тест ручного исправления мета-описаний')
    print('=' * 50)
    
    test_category = 4  # Машинное обучение
    
    # Простое, короткое мета-описание для теста
    simple_meta = "Новости машинного обучения и нейронных сетей от AI Lynx."
    
    test_data = {
        'yoast_description': simple_meta
    }
    
    print(f'📤 Устанавливаем простое мета-описание: "{simple_meta}"')
    
    try:
        response = requests.post(
            f'{config.wordpress_api_url}/categories/{test_category}',
            json=test_data,
            auth=auth
        )
        
        if response.status_code == 200:
            result = response.json()
            returned_desc = result.get('yoast_description', '')
            
            print(f'📥 Получили обратно: "{returned_desc}"')
            
            if returned_desc == simple_meta:
                print('✅ Мета-описание сохранилось в API')
                
                # Проверяем через 3 секунды
                time.sleep(3)
                
                check_response = requests.get(f'{config.wordpress_api_url}/categories/{test_category}', auth=auth)
                if check_response.status_code == 200:
                    check_data = check_response.json()
                    yoast_head_json = check_data.get('yoast_head_json', {})
                    
                    if yoast_head_json:
                        head_desc = yoast_head_json.get('description', '')
                        print(f'🔍 В yoast_head_json: "{head_desc}"')
                        
                        if simple_meta in head_desc or head_desc == simple_meta:
                            print('🎉 РАБОТАЕТ! Мета-описание появилось в Yoast head!')
                            return True
                        else:
                            print('❌ Мета-описание не появилось в Yoast head')
                    else:
                        print('❌ yoast_head_json пуст')
            else:
                print('❌ Мета-описание не сохранилось')
        else:
            print(f'❌ Ошибка запроса: {response.status_code}')
            
    except Exception as e:
        print(f'❌ Исключение: {e}')
    
    return False

def main():
    print('🔍 Отладка мета-описаний Yoast SEO')
    print('=' * 60)
    
    # 1. Проверяем текущее состояние
    check_current_yoast_data()
    
    # 2. Проверяем статус Yoast плагина
    check_yoast_plugin_status()
    
    # 3. Пробуем принудительно обновить
    print('\n' + '='*60)
    if force_yoast_refresh():
        print('\n🎉 Проблема решена! Yoast синхронизация работает')
    else:
        print('\n❌ Проблема остается. Пробуем ручное исправление...')
        
        if test_manual_meta_fix():
            print('\n🎉 Ручное исправление сработало!')
        else:
            print('\n❌ Мета-описания не работают')
            print('\n💡 Возможные причины:')
            print('   1. Yoast SEO не активирован или настроен неправильно')
            print('   2. Наш плагин работает, но Yoast не читает мета-поля')
            print('   3. Нужна переиндексация через админку Yoast')
            print('   4. Проблема с кэшированием WordPress/Yoast')

if __name__ == "__main__":
    main()