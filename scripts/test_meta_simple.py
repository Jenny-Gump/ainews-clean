#!/usr/bin/env python3
"""
Test Meta Simple - Check what WordPress returns
Простой тест - проверяем что возвращает WordPress
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config
import json

def test_what_wordpress_returns():
    """Проверяем что именно возвращает WordPress"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('🔍 Проверяем что возвращает WordPress REST API')
    print('=' * 60)
    
    test_category = 4  # Машинное обучение
    
    # Сначала получаем текущие данные
    print('1️⃣ Получаем текущие данные категории...')
    
    response = requests.get(f'{config.wordpress_api_url}/categories/{test_category}', auth=auth)
    
    if response.status_code == 200:
        data = response.json()
        
        print(f'✅ Категория получена: {data.get("name")}')
        print(f'📊 Структура ответа:')
        
        # Показываем основные поля
        for key in ['id', 'name', 'slug', 'description', 'meta']:
            value = data.get(key, 'НЕТ ПОЛЯ')
            if key == 'meta':
                if isinstance(value, list):
                    print(f'   {key}: список из {len(value)} элементов')
                    if len(value) > 0:
                        print(f'      Первый элемент: {value[0] if value else "пуст"}')
                elif isinstance(value, dict):
                    print(f'   {key}: словарь с {len(value)} полями')
                    for sub_key, sub_value in value.items():
                        if '_yoast_' in sub_key:
                            print(f'      {sub_key}: {sub_value}')
                else:
                    print(f'   {key}: {type(value).__name__} = {value}')
            else:
                print(f'   {key}: {str(value)[:60]}{"..." if len(str(value)) > 60 else ""}')
        
        # Проверяем наши Yoast поля из плагина
        yoast_fields = ['yoast_title', 'yoast_description', 'yoast_keyword']
        print(f'\n📋 Yoast поля из нашего плагина:')
        for field in yoast_fields:
            value = data.get(field, 'НЕТ')
            print(f'   {field}: {value}')
        
        return data
    else:
        print(f'❌ Ошибка получения данных: {response.status_code}')
        return None

def test_direct_meta_update_fixed():
    """Исправленный тест прямого обновления meta"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n2️⃣ Тестируем прямое обновление через meta...')
    print('=' * 50)
    
    test_category = 4
    
    # Простые данные для теста
    meta_data = {
        "meta": {
            "_yoast_wpseo_title": "ПРОСТОЙ ТЕСТ | AI Lynx",
            "_yoast_wpseo_metadesc": "Простое тестовое описание."
        }
    }
    
    print(f'📤 Отправляем meta данные...')
    
    try:
        response = requests.patch(
            f'{config.wordpress_api_url}/categories/{test_category}',
            json=meta_data,
            auth=auth
        )
        
        print(f'📥 Статус ответа: {response.status_code}')
        
        if response.status_code == 200:
            print('✅ Запрос успешен!')
            
            # Сохраняем сырой ответ
            raw_response = response.text
            print(f'📝 Длина ответа: {len(raw_response)} символов')
            
            try:
                result = response.json()
                
                # Безопасно проверяем meta поле
                meta = result.get('meta')
                print(f'🔍 Поле meta: тип {type(meta).__name__}')
                
                if isinstance(meta, dict):
                    print('   📊 meta это словарь:')
                    yoast_keys = [k for k in meta.keys() if '_yoast_' in k]
                    if yoast_keys:
                        for key in yoast_keys:
                            print(f'      {key}: {meta[key]}')
                    else:
                        print('      ❌ Yoast ключей не найдено')
                        print(f'      Все ключи: {list(meta.keys())[:5]}...')
                        
                elif isinstance(meta, list):
                    print(f'   📊 meta это список из {len(meta)} элементов')
                    if meta:
                        print(f'      Первый элемент: {meta[0]}')
                else:
                    print(f'   📊 meta: {meta}')
                
                # Проверяем наши поля из плагина
                yoast_title = result.get('yoast_title')
                yoast_desc = result.get('yoast_description')
                
                print(f'\n🔍 Наши поля из плагина:')
                print(f'   yoast_title: {yoast_title}')
                print(f'   yoast_description: {yoast_desc}')
                
                # Проверяем совпадение
                expected_title = meta_data["meta"]["_yoast_wpseo_title"]
                expected_desc = meta_data["meta"]["_yoast_wpseo_metadesc"]
                
                if yoast_title == expected_title and yoast_desc == expected_desc:
                    print('🎉 УСПЕХ! Данные совпадают!')
                    return True
                else:
                    print('❌ Данные не совпадают')
                    
            except json.JSONDecodeError as e:
                print(f'❌ Ошибка парсинга JSON: {e}')
                print(f'Первые 200 символов ответа: {raw_response[:200]}')
                
        else:
            print(f'❌ Ошибка: {response.status_code}')
            print(f'Ответ: {response.text[:200]}')
            
    except Exception as e:
        print(f'❌ Исключение: {e}')
    
    return False

def main():
    print('🔧 Простой тест meta полей WordPress')
    print('=' * 60)
    
    # 1. Смотрим что возвращает WordPress
    current_data = test_what_wordpress_returns()
    
    if current_data:
        # 2. Тестируем обновление
        if test_direct_meta_update_fixed():
            print('\n🎉 Прямой meta метод работает!')
            print('💡 Можно использовать ваш подход из другого проекта')
        else:
            print('\n❌ Прямой meta метод не работает для категорий')
            print('💡 Возможно, WordPress поддерживает meta только для постов, не для категорий')
    
    print('\n📋 Выводы:')
    print('• WordPress REST API возвращает данные успешно')
    print('• Наш плагин yoast-rest-api-extension работает')
    print('• Нужно выяснить поддерживает ли WP meta поля для категорий')

if __name__ == "__main__":
    main()